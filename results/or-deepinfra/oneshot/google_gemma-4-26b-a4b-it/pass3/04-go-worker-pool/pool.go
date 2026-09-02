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

	// Create a derived context to signal cancellation to running tasks
	// if a task fails or the parent context is cancelled.
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)
	resChan := make(chan result, n)
	
	// semaphore limits concurrency
	sem := make(chan struct{}, workers)
	
	// wg ensures we wait for all started goroutines to finish to prevent leaks.
	var wg sync.WaitGroup

	// errOnce ensures we only capture the first error that occurs.
	var errOnce sync.Once
	var firstErr error

	// Helper to capture the first error and trigger cancellation.
	setError := func(err error) {
		if err != nil {
			errOnce.Do(func() {
				firstErr = err
				cancel()
			})
		}
	}

	// We use a separate goroutine to feed tasks into the worker pool.
	// This allows us to stop dispatching tasks immediately if an error occurs.
	go func() {
		for i := 0; i < n; i++ {
			// Check if we should stop dispatching due to error or parent cancellation.
			select {
			case <-runCtx.Done():
				return
			case sem <- struct{}{}:
				// Acquired slot in semaphore
			}

			// Double check context before spawning to avoid starting a task
			// if the context was cancelled while waiting for the semaphore.
			if runCtx.Err() != nil {
				<-sem // release slot
				return
			}

			wg.Add(1)
			go func(idx int) {
				defer wg.Done()
				defer func() { <-sem }() // release slot

				val, err := tasks[idx](runCtx)
				if err != nil {
					setError(err)
				}
				resChan <- result{index: idx, val: val, err: err}
			}(i)
		}
	}()

	// Monitor for completion or error.
	// We must wait for all started goroutines to finish to satisfy the "no leaks" requirement.
	
	// This goroutine closes the channel once all workers are done.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	// Collect results.
	// We loop until the channel is closed (which happens after wg.Wait()).
	for res := range resChan {
		if res.err != nil && firstErr == nil {
			// This case handles the error that triggered the cancellation.
			// Note: setError is called inside the task goroutine.
		}
		if res.index >= 0 && res.index < n {
			results[res.index] = res.val
		}
	}

	// If an error occurred (either from a task or context cancellation), return nil and the error.
	if firstErr != nil {
		return nil, firstErr
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return results, nil
}
