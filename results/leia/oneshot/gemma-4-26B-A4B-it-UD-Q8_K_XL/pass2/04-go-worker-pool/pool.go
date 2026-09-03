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

			// Double check context before spawning to avoid starting a task 
			// if a previous one just failed.
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
				
				// Even if an error occurred, we send the result to the channel
				// so the collector knows this specific task is done.
				// However, if the context was cancelled, we must ensure we don't
				// block forever on resChan if the collector has already exited.
				select {
				case resChan <- result{index: idx, val: val, err: err}:
				case <-runCtx.Done():
					// If the context is cancelled, the collector might have stopped.
					// We don't need to send the result if the whole operation is aborting.
				}
			}(i)
		}
	}()

	// Collector loop
	// We need to wait for all tasks to finish (via wg) to ensure no leaks.
	// We use a separate goroutine to close the channel when all workers are done.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	// Process results as they come in.
	// We must continue collecting until resChan is closed to ensure wg.Wait() completes.
	for res := range resChan {
		if res.err != nil {
			// We don't return immediately here because we must wait for 
			// all started tasks to finish (handled by the range loop and wg.Wait).
			// The first error is already captured by setError.
		} else {
			results[res.index] = res.val
		}
	}

	// If the parent context was cancelled, return its error.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// If a task returned an error, return the first one.
	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
