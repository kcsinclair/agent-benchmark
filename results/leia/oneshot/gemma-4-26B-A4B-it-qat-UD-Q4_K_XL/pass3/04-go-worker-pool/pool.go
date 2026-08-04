package main

import (
	"context"
	"errors"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// result wraps the output of a task to be sent over a channel.
type result struct {
	index int
	val   any
	err   error
}

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}

	// Create a derived context that we can cancel if a task fails
	// or if the parent context is cancelled.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// resultsChan collects results from workers.
	// taskChan distributes indices of tasks to be processed.
	resultsChan := make(chan result, n)
	taskChan := make(chan int)

	// wg ensures we wait for all started goroutines to finish to prevent leaks.
	var wg sync.WaitGroup

	// Start the worker pool.
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case idx, ok := <-taskChan:
					if !ok {
						return
					}
					// Execute the task.
					val, err := tasks[idx](ctx)
					resultsChan <- result{index: idx, val: val, err: err}
					
					// If the task failed, cancel the context to stop other tasks.
					if err != nil {
						cancel()
						return
					}
				}
			}
		}()
	}

	// Dispatcher goroutine: feeds task indices to the workers.
	go func() {
		defer close(taskChan)
		for i := 0; i < n; i++ {
			select {
			case <-ctx.Done():
				return
			case taskChan <- i:
			}
		}
	}()

	// Wait for all workers to finish in a separate goroutine to avoid blocking the main thread.
	// This allows us to collect results while workers are still running.
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	// Collect results.
	finalResults := make([]any, n)
	var firstErr error

	// We loop until all workers are done.
	// Note: resultsChan might receive up to 'n' results.
	// We must consume resultsChan to prevent workers from blocking.
	receivedCount := 0
	for receivedCount < n {
		select {
		case res := <-resultsChan:
			receivedCount++
			if res.err != nil && firstErr == nil {
				firstErr = res.err
				// We don't return immediately; we must wait for wg.Wait() 
				// to ensure no goroutine leaks.
			} else if res.err == nil {
				finalResults[res.index] = res.val
			}
		case <-done:
			// If workers finished but we haven't received all results, 
			// it means some tasks were cancelled or failed.
			// We must drain the channel to ensure workers aren't blocked.
			for len(resultsChan) > 0 {
				res := <-resultsChan
				if res.err != nil && firstErr == nil {
					firstErr = res.err
				} else if res.err == nil {
					finalResults[res.index] = res.val
				}
				receivedCount++
			}
			goto collectionDone
		}
	}

collectionDone:
	// If the parent context was cancelled, prioritize that error.
	if ctx.Err() != nil && firstErr == nil {
		return nil, ctx.Err()
	}

	if firstErr != nil {
		return nil, firstErr
	}

	return finalResults, nil
}
