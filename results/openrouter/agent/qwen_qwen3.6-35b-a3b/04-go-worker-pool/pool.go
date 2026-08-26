package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, &invalidWorkersError{}
	}
	if len(tasks) == 0 {
		return nil, nil
	}

	// Create a context for tasks. When we detect an error or parent ctx is done,
	// we cancel this to notify running tasks.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Results channel
	type result struct {
		index int
		value any
		err   error
	}
	resultsCh := make(chan result, len(tasks))

	// WaitGroup to track started tasks
	var wg sync.WaitGroup

	// Semaphore to limit concurrency
	sem := make(chan struct{}, workers)

	// Track if we've already failed
	var failOnce sync.Once
	var firstErr error

	// Use a done channel to signal that we should stop
	done := make(chan struct{})

	// Use a sync.Once to ensure the channel is only closed once
	var closeOnce sync.Once

	for i, task := range tasks {
		// Check if we should stop starting new tasks
		select {
		case <-done:
			// Another task failed, don't start new tasks
			// Wait for started tasks
			wg.Wait()
			closeOnce.Do(func() {
				close(resultsCh)
			})
			return nil, firstErr
		case <-ctx.Done():
			// Parent context cancelled, don't start new tasks
			cancel()
			wg.Wait()
			closeOnce.Do(func() {
				close(resultsCh)
			})
			return nil, ctx.Err()
		default:
		}

		// Try to acquire a worker slot
		select {
		case <-done:
			// Another task failed, don't start new tasks
			wg.Wait()
			closeOnce.Do(func() {
				close(resultsCh)
			})
			return nil, firstErr
		case <-ctx.Done():
			// Parent context cancelled, don't start new tasks
			cancel()
			wg.Wait()
			closeOnce.Do(func() {
				close(resultsCh)
			})
			return nil, ctx.Err()
		case sem <- struct{}{}:
			// Acquired a slot
		}

		wg.Add(1)
		go func(idx int, t Task) {
			defer wg.Done()
			defer func() { <-sem }() // Release the slot

			// Execute the task
			value, err := t(taskCtx)

			// If there's an error, record it (only the first one matters)
			if err != nil {
				failOnce.Do(func() {
					firstErr = err
				})
				// Signal to stop starting new tasks
				select {
				case done <- struct{}{}:
				default:
				}
				// Cancel the task context to notify other running tasks
				cancel()
			}

			resultsCh <- result{index: idx, value: value, err: err}
		}(i, task)
	}

	// Close the results channel when all tasks are done
	go func() {
		wg.Wait()
		closeOnce.Do(func() {
			close(resultsCh)
		})
	}()

	// Collect results
	results := make([]any, len(tasks))
	for r := range resultsCh {
		if r.err != nil {
			// Cancel context to stop other running tasks
			cancel()
			// Wait for all started tasks to finish
			wg.Wait()
			return nil, r.err
		}
		results[r.index] = r.value
	}

	return results, nil
}

type invalidWorkersError struct{}

func (e *invalidWorkersError) Error() string {
	return "workers must be >= 1"
}
