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

	// Create a context that will be cancelled when the first error occurs.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Results channel
	type result struct {
		index int
		value any
		err   error
	}
	resultsCh := make(chan result, len(tasks))

	// WaitGroup to track all started goroutines
	var wg sync.WaitGroup

	// Semaphore to limit concurrency
	sem := make(chan struct{}, workers)

	// Launch tasks
	for i, task := range tasks {
		// Check if context is already cancelled
		select {
		case <-taskCtx.Done():
			// Context cancelled, stop starting new tasks
			continue
		default:
		}

		// Try to acquire a worker slot
		select {
		case <-taskCtx.Done():
			// Context cancelled
			continue
		case sem <- struct{}{}:
			// Got a worker slot
		}

		wg.Add(1)
		go func(idx int, t Task) {
			defer wg.Done()
			defer func() { <-sem }() // Release worker slot

			// Check if we should still run (context might have been cancelled)
			select {
			case <-taskCtx.Done():
				// Context was cancelled, don't run the task
				resultsCh <- result{index: idx, err: taskCtx.Err()}
				return
			default:
			}

			value, err := t(taskCtx)
			resultsCh <- result{index: idx, value: value, err: err}

			if err != nil {
				cancel() // Cancel context to stop other running tasks
			}
		}(i, task)
	}

	// Wait for all started goroutines to finish
	wg.Wait()
	close(resultsCh)

	// Collect results in order
	results := make([]any, len(tasks))
	for r := range resultsCh {
		if r.err != nil {
			return nil, r.err
		}
		results[r.index] = r.value
	}

	return results, nil
}

type invalidWorkersError struct{}

func (e *invalidWorkersError) Error() string {
	return "workers must be at least 1"
}
