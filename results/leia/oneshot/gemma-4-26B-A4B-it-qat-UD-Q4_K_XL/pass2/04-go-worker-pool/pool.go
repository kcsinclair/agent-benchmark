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

	// Use a WaitGroup to ensure all started goroutines finish before returning.
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
					
					// Send result. We use a select to avoid blocking if the 
					// main loop has already exited due to an error.
					select {
					case resultsChan <- result{index: idx, val: val, err: err}:
					case <-ctx.Done():
						return
					}
				}
			}
		}()
	}

	// Dispatcher goroutine: feeds task indices into the worker pool.
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

	// Collector logic.
	// We need to collect exactly 'n' results or stop early on error.
	// However, we must ensure all workers finish (wg.Wait) before returning
	// to prevent goroutine leaks.
	
	finalResults := make([]any, n)
	var firstErr error
	completedCount := 0

	// We use a separate goroutine to close resultsChan once all workers are done.
	// This allows the collection loop to terminate naturally.
	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	// Collect results.
	for res := range resultsChan {
		if res.err != nil && firstErr == nil {
			firstErr = res.err
			cancel() // Signal other tasks to stop.
		}
		
		if res.err == nil {
			finalResults[res.index] = res.val
		}
		
		completedCount++
		// If we encountered an error, we stop collecting and wait for workers.
		// The 'range resultsChan' will terminate once wg.Wait() finishes and close(resultsChan) is called.
		if firstErr != nil {
			break
		}
	}

	// Wait for all workers to finish to satisfy the "no goroutine leaks" requirement.
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	// Check if the context was cancelled (e.g., parent timeout).
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return finalResults, nil
}
