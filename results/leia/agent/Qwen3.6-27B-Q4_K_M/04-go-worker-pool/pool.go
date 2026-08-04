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

	// Create a cancellable context for tasks
	taskCtx, cancel := context.WithCancel(ctx)

	// Results slice to maintain order
	results := make([]any, len(tasks))

	// Semaphore to limit concurrency
	sem := make(chan struct{}, workers)

	// WaitGroup to wait for all started tasks to complete
	var wg sync.WaitGroup

	// Track the first error that occurred
	var firstErr error
	var errMu sync.Mutex

	// Function to run a single task
	runTask := func(i int, task Task) {
		defer wg.Done()
		defer func() { <-sem }() // Release semaphore slot

		// Execute the task
		result, err := task(taskCtx)

		// Store result or error
		errMu.Lock()
		if firstErr == nil {
			if err != nil {
				firstErr = err
			} else {
				results[i] = result
			}
		}
		errMu.Unlock()
	}

	// Start tasks respecting the worker limit
	for i, task := range tasks {
		// Check if we should stop starting new tasks
		errMu.Lock()
		if firstErr != nil {
			errMu.Unlock()
			break
		}
		errMu.Unlock()

		// Check if parent context is cancelled
		select {
		case <-ctx.Done():
			errMu.Lock()
			if firstErr == nil {
				firstErr = ctx.Err()
			}
			errMu.Unlock()
			break
		default:
		}

		if firstErr != nil {
			break
		}

		// Wait for a semaphore slot
		select {
		case sem <- struct{}{}:
			// Got a slot, start the task
			wg.Add(1)
			go runTask(i, task)
		case <-ctx.Done():
			// Parent context cancelled while waiting for slot
			errMu.Lock()
			if firstErr == nil {
				firstErr = ctx.Err()
			}
			errMu.Unlock()
			break
		}
	}

	// Cancel task context if there was an error or parent context was cancelled
	if firstErr != nil {
		cancel()
	}

	// Wait for all started tasks to complete
	wg.Wait()

	// Return results or error
	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
