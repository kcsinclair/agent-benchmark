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

	// Create a channel to limit concurrency
	sem := make(chan struct{}, workers)
	
	// Channel to receive results
	results := make(chan result, len(tasks))
	
	// Context for tasks
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()
	
	var wg sync.WaitGroup
	
	// Start workers
	for i, task := range tasks {
		wg.Add(1)
		go func(index int, t Task) {
			defer wg.Done()
			
			// Wait for a worker slot
			sem <- struct{}{}
			defer func() { <-sem }()
			
			// Check if context is already cancelled
			select {
			case <-taskCtx.Done():
				results <- result{index: index, err: taskCtx.Err()}
				return
			default:
			}
			
			// Execute task
			result, err := t(taskCtx)
			results <- result{index: index, value: result, err: err}
		}(i, task)
	}
	
	// Close results channel when all goroutines are done
	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Collect results
	finalResults := make([]any, len(tasks))
	
	for r := range results {
		if r.err != nil {
			// Cancel all remaining tasks
			cancel()
			// Wait for all tasks to finish
			wg.Wait()
			return nil, r.err
		}
		finalResults[r.index] = r.value
	}
	
	// Check if context was cancelled
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	
	return finalResults, nil
}

// Helper struct to hold result
type result struct {
	index int
	value any
	err   error
}

// Custom error type for validation
type workerError struct {
	msg string
}

func (e *workerError) Error() string {
	return e.msg
}
