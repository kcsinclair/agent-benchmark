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

	if len(tasks) == 0 {
		return nil, nil
	}

	// Create a cancellable context to stop all tasks if one fails or parent is cancelled.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	
	// taskIdx is the index of the next task to be picked up by a worker.
	taskIdx := 0
	// mu protects taskIdx and the firstError.
	var mu sync.Mutex
	var firstError error

	// wg ensures we wait for all started goroutines to finish before returning.
	var wg sync.WaitGroup

	// We use a semaphore-like pattern to limit concurrency.
	// However, since we need to distribute tasks, a simple loop starting 
	// workers that pull from a shared index is more idiomatic.
	
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				var currentTask Task
				var idx int

				mu.Lock()
				// Check if an error has already occurred or context is cancelled.
				if firstError != nil || ctx.Err() != nil {
					mu.Unlock()
					return
				}
				// Check if all tasks are dispatched.
				if taskIdx >= len(tasks) {
					mu.Unlock()
					return
				}
				
				idx = taskIdx
				currentTask = tasks[idx]
				taskIdx++
				mu.Unlock()

				// Execute the task.
				res, err := currentTask(ctx)

				if err != nil {
					mu.Lock()
					// Only capture the first error that occurred.
					if firstError == nil {
						firstError = err
						cancel() // Signal other tasks to stop.
					}
					mu.Unlock()
					return
				}

				// Store result in the correct position.
				mu.Lock()
				results[idx] = res
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	// Check if the parent context was cancelled or a task failed.
	if firstError != nil {
		return nil, firstError
	}
	if ctx.Err() != nil {
		// If the context was cancelled but no task returned an error, 
		// return the context error.
		return nil, ctx.Err()
	}

	return results, nil
}
