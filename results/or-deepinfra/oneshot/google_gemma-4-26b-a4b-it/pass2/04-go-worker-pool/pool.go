package main

import (
	"context"
	"errors"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// result wraps the output of a task to maintain order and error state.
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

	// Dispatcher loop
	go func() {
		for i := 0; i < n; i++ {
			// Check if we should stop starting new tasks due to error or parent cancellation.
			select {
			case <-runCtx.Done():
				return
			case sem <- struct{}{}:
				// Acquired slot
			}

			// Double check context before launching to avoid race between sem acquisition and launch.
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
				
				// We send the result even if there's an error, 
				// but the main loop will prioritize the first error.
				resChan <- result{index: idx, val: val, err: err}
			}(i)
		}
	}()

	// Collector loop
	// We need to wait for all goroutines to finish to satisfy the "no leaks" requirement.
	// We use a separate goroutine to close the channel once all workers are done.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	// Process results as they come in.
	// We must collect all results to ensure wg.Wait() completes and no goroutines leak.
	for res := range resChan {
		if res.err != nil {
			// If we encounter an error, we don't return immediately because 
			// we must wait for all started tasks to finish (via the range loop).
			// The first error is already captured by setError.
		} else {
			// Only store result if we haven't encountered an error yet.
			// Note: even if an error happened, we continue draining resChan.
			if firstErr == nil {
				results[res.index] = res.val
			}
		}
	}

	// If the parent context was cancelled, return its error.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// If a task failed, return the first error.
	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
