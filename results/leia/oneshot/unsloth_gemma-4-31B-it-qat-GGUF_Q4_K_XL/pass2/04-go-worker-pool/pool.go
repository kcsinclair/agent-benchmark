package main

import (
	"context"
	"errors"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	numTasks := len(tasks)
	if numTasks == 0 {
		return []any{}, nil
	}

	// Create a cancellable context to signal all workers to stop if one fails
	// or if the parent context is cancelled.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, numTasks)
	
	// taskChan distributes indices of tasks to be processed.
	taskChan := make(chan int)
	
	// errChan captures the first error that occurs.
	// Buffered to ensure workers don't block if Run has already returned.
	errChan := make(chan error, numTasks)
	
	var wg sync.WaitGroup
	var errOnce sync.Once

	// Helper to capture the first error and trigger cancellation.
	reportError := func(err error) {
		errOnce.Do(func() {
			errChan <- err
			cancel()
		})
	}

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
					res, err := tasks[idx](ctx)
					if err != nil {
						reportError(err)
						return
					}
					results[idx] = res
				}
			}
		}()
	}

	// Feed tasks into the channel.
	go func() {
		defer close(taskChan)
		for i := 0; i < numTasks; i++ {
			select {
			case <-ctx.Done():
				return
			case taskChan <- i:
			}
		}
	}()

	// Wait for all workers to finish.
	wg.Wait()

	// Check if an error occurred.
	select {
	case err := <-errChan:
		return nil, err
	default:
		// If the parent context was cancelled but no task returned an error,
		// we must return the context error.
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		return results, nil
	}
}
