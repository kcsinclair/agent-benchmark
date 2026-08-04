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

	n := len(tasks)
	results := make([]any, n)

	// Create a cancellable context for the tasks
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Semaphore to limit concurrency
	sem := make(chan struct{}, workers)

	var wg sync.WaitGroup

	// firstErr stores the first error encountered
	var firstErr error
	var mu sync.Mutex

	// Track which tasks have started to prevent starting new ones after failure
	// We use a flag to indicate if we should stop starting new tasks
	var stopStarting bool

	// We need to ensure that if an error occurs, we don't start new tasks.
	// We also need to wait for all started tasks to complete.

	// Start tasks
	for i := 0; i < n; i++ {
		// Check if we should stop starting new tasks
		if stopStarting {
			break
		}

		// Check if parent context is already cancelled
		if ctx.Err() != nil {
			stopStarting = true
			break
		}

		// Acquire semaphore slot
		select {
		case sem <- struct{}{}:
			// Got a slot
		case <-ctx.Done():
			// Parent context cancelled
			stopStarting = true
			break
		}

		if stopStarting {
			break
		}

		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			defer func() { <-sem }()

			// Check if we should run this task
			// If stopStarting is true, we still need to run if we already acquired the slot
			// But we should check if the task context is cancelled
			if taskCtx.Err() != nil {
				return
			}

			result, err := tasks[idx](taskCtx)
			if err != nil {
				mu.Lock()
				if firstErr == nil {
					firstErr = err
					stopStarting = true
					// Cancel task context to signal other tasks
					cancel()
				}
				mu.Unlock()
				return
			}

			mu.Lock()
			if firstErr == nil {
				results[idx] = result
			}
			mu.Unlock()
		}(i)
	}

	// Wait for all started tasks to complete
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	// Check if parent context was cancelled
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return results, nil
}
