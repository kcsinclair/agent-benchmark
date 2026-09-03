package main

import (
	"context"
	"errors"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// result holds the outcome of a task execution.
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
		return nil, nil
	}

	// Create a derived context that we can cancel if a task fails or the parent context is cancelled.
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)
	resChan := make(chan result, n)
	
	// semaphore limits concurrency.
	sem := make(chan struct{}, workers)
	
	// wg ensures we wait for all started goroutines to finish to prevent leaks.
	var wg sync.WaitGroup

	// We use a separate goroutine to manage the dispatching of tasks.
	// This allows us to handle the "fail fast" requirement by stopping dispatching
	// as soon as an error is detected or the context is cancelled.
	go func() {
		for i := 0; i < n; i++ {
			select {
			case <-runCtx.Done():
				// Stop dispatching if context is cancelled or an error occurred.
				return
			case sem <- struct{}{}:
				// Acquired a worker slot.
				wg.Add(1)
				go func(idx int) {
					defer wg.Done()
					defer func() { <-sem }() // Release worker slot.

					val, err := tasks[idx](runCtx)
					resChan <- result{index: idx, val: val, err: err}
					
					if err != nil {
						// If a task fails, cancel the runCtx to signal other running tasks.
						cancel()
					}
				}(i)
			}
		}
	}()

	// We'll use a separate goroutine to close the channel once all workers are done.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	// Monitor results.
	var firstErr error

	// Collect results.
	for res := range resChan {
		if res.err != nil && firstErr == nil {
			firstErr = res.err
		}
		if res.err == nil {
			results[res.index] = res.val
		}
	}

	// If the parent context was cancelled, return its error.
	// If a task failed, return that error.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
