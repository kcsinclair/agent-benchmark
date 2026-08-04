package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, &workerError{msg: "workers must be at least 1"}
	}
	
	if len(tasks) == 0 {
		return []any{}, nil
	}
	
	// Use a channel to limit concurrency
	sem := make(chan struct{}, workers)
	
	// Use a channel to collect results in order
	results := make([]any, len(tasks))
	errChan := make(chan error, 1)
	
	var wg sync.WaitGroup
	
	// Start a goroutine to handle context cancellation
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	
	go func() {
		<-ctx.Done()
		cancel() // Cancel all running tasks
	}()
	
	for i, task := range tasks {
		wg.Add(1)
		go func(index int, t Task) {
			defer wg.Done()
			
			// Wait for a worker slot
			select {
			case sem <- struct{}{}:
				defer func() { <-sem }() // Release the slot
			case <-ctx.Done():
				errChan <- ctx.Err()
				return
			}
			
			// Execute the task
			result, err := t(ctx)
			if err != nil {
				select {
				case errChan <- err:
				default:
				}
				return
			}
			
			results[index] = result
		}(i, task)
	}
	
	// Wait for all tasks to complete
	wg.Wait()
	
	// Check for errors
	select {
	case err := <-errChan:
		return nil, err
	default:
	}
	
	return results, nil
}

// workerError is a custom error type for worker validation
type workerError struct {
	msg string
}

func (e *workerError) Error() string {
	return e.msg
}
