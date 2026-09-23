package main

import (
	"context"
	"fmt"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	// Validation: workers must be at least 1
	if workers < 1 {
		return nil, fmt.Errorf("workers must be at least 1, got %d", workers)
	}

	// Handle empty tasks
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Create a cancellable context for task execution
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Results slice to maintain order
	results := make([]any, len(tasks))

	// Semaphore to limit concurrent workers
	semaphore := make(chan struct{}, workers)

	// WaitGroup to track all goroutines
	var wg sync.WaitGroup

	// Channel to communicate the first error that occurs
	errChan := make(chan error, 1)

	// Mutex to protect error state
	var errMu sync.Mutex
	var firstErr error

	// Monitor parent context cancellation
	go func() {
		<-ctx.Done()
		errMu.Lock()
		if firstErr == nil {
			firstErr = ctx.Err()
		}
		errMu.Unlock()
		cancel()
	}()

	// Launch a goroutine for each task
	for i, task := range tasks {
		wg.Add(1)

		go func(index int, t Task) {
			defer wg.Done()

			// Check if we should even try to acquire the semaphore
			errMu.Lock()
			if firstErr != nil {
				errMu.Unlock()
				return
			}
			errMu.Unlock()

			// Try to acquire a worker slot
			select {
			case semaphore <- struct{}{}:
				// Acquired a slot
				defer func() { <-semaphore }()
			case <-taskCtx.Done():
				// Context cancelled before we could start
				errMu.Lock()
				if firstErr == nil {
					firstErr = taskCtx.Err()
				}
				errMu.Unlock()
				return
			}

			// Check again if an error occurred while waiting for semaphore
			errMu.Lock()
			if firstErr != nil {
				errMu.Unlock()
				return
			}
			errMu.Unlock()

			// Execute the task
			result, err := t(taskCtx)

			if err != nil {
				errMu.Lock()
				if firstErr == nil {
					firstErr = err
					cancel() // Cancel remaining tasks
				}
				errMu.Unlock()
				return
			}

			// Store result in order
			results[index] = result
		}(i, task)
	}

	// Wait for all goroutines to complete
	wg.Wait()

	// Check if any error occurred
	errMu.Lock()
	if firstErr != nil {
		errMu.Unlock()
		return nil, firstErr
	}
	errMu.Unlock()

	return results, nil
}
