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
		return nil, &invalidWorkerCountError{workers}
	}

	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Create a context that can be cancelled to stop new tasks from starting
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Channel to receive results
	results := make([]any, len(tasks))
	errors := make([]error, len(tasks))
	var errMu sync.Mutex

	// Channel to limit concurrency
	sem := make(chan struct{}, workers)

	var wg sync.WaitGroup

	for i, task := range tasks {
		wg.Add(1)
		go func(i int, task Task) {
			defer wg.Done()
			// Acquire semaphore
			sem <- struct{}{}
			defer func() { <-sem }() // Release semaphore

			// Run task with the context
			result, err := task(ctx)
			if err != nil {
				errMu.Lock()
				errors[i] = err
				errMu.Unlock()
				cancel() // Cancel the parent context to stop new tasks
				return
			}

			// Store result
			results[i] = result
		}(i, task)
	}

	// Wait for all tasks to complete
	wg.Wait()

	// Check for any errors
	for _, err := range errors {
		if err != nil {
			return nil, err
		}
	}

	// Check if parent context was cancelled
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return results, nil
}

type invalidWorkerCountError struct {
	workers int
}

func (e *invalidWorkerCountError) Error() string {
	return "invalid worker count: " + string(rune(e.workers))
}
