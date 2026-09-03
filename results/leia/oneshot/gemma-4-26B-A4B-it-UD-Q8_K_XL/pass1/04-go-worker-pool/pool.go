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
				// Since resChan is buffered to n, this is safe.
				resChan <- result{index: idx, val: val, err: err}
			}(i)
		}
	}()

	// Collector loop
	// We need to wait for all tasks that were actually started to finish.
	// We use a separate goroutine to close the channel once all workers are done.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	// Process results as they come in.
	receivedCount := 0
	for res := range resChan {
		if res.err != nil {
			// If we encounter an error, we don't return immediately.
			// We must wait for the wg.Wait() via the channel close to ensure no leaks.
			// The loop will continue until resChan is closed.
		} else {
			results[res.index] = res.val
		}
		receivedCount++
	}

	// If an error was captured during execution, return it.
	if firstErr != nil {
		return nil, firstErr
	}

	// If the loop finished but the context was cancelled (e.g. timeout), return ctx error.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return results, nil
}
