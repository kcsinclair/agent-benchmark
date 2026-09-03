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

	// Create a derived context that we can cancel internally if a task fails
	// or if the parent context is cancelled.
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
	// This allows us to stop dispatching tasks immediately upon error or cancellation.
	go func() {
		for i := 0; i < n; i++ {
			// Check if we should stop dispatching new tasks.
			select {
			case <-runCtx.Done():
				return
			case sem <- struct{}{}:
				// Acquired slot in semaphore.
			}

			// Double check context before starting the goroutine.
			select {
			case <-runCtx.Done():
				<-sem // release slot
				return
			default:
			}

			wg.Add(1)
			go func(idx int) {
				defer wg.Done()
				defer func() { <-sem }() // release slot

				val, err := tasks[idx](runCtx)
				if err != nil {
					setError(err)
				}
				
				// Even if an error occurred, we send the result to the channel
				// so the collector knows this specific task is done.
				// However, if the context was cancelled, we must ensure we don't
				// block forever on resChan if the collector has already exited.
				// Since resChan is buffered to n, this is safe.
				resChan <- result{index: idx, val: val, err: err}
			}(i)
		}
	}()

	// Collector loop: wait for all tasks to report back or for an error to occur.
	// We must wait for all goroutines to finish (wg.Wait) to satisfy the "no leaks" requirement.
	
	// We run the collection in a separate goroutine so we can wait on wg.Wait() 
	// in the main flow.
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	// Wait for either all tasks to finish or a cancellation/error to occur.
	// Note: We must wait for wg.Wait() regardless of error to prevent leaks.
	<-done

	// If an error occurred (either from a task or context cancellation), return it.
	if firstErr != nil {
		return nil, firstErr
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// If we reached here, all tasks completed successfully.
	// Collect results from the channel.
	close(resChan)
	for res := range resChan {
		// Because we waited for wg.Wait(), we know all results are in the channel.
		// We check if the result itself contains an error (though setError should have caught it).
		if res.err != nil {
			return nil, res.err
		}
		results[res.index] = res.val
	}

	return results, nil
}
