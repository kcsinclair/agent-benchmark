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
		return []any{}, nil
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
	var shouldStop bool

	// We need to ensure that once an error occurs, we don't start new tasks.
	// We'll use a channel or atomic flag. Let's use a simple flag protected by mu.

	// Start tasks
	for i := 0; i < n; i++ {
		// Check if we should stop starting new tasks
		mu.Lock()
		if shouldStop {
			mu.Unlock()
			break
		}
		mu.Unlock()

		// Wait for a slot in the semaphore
		select {
		case sem <- struct{}{}:
			// Got a slot
		case <-taskCtx.Done():
			// Context cancelled, stop starting new tasks
			mu.Lock()
			shouldStop = true
			mu.Unlock()
			break
		}

		// Check again after acquiring semaphore slot
		mu.Lock()
		if shouldStop {
			mu.Unlock()
			<-sem // Release the slot we just acquired
			break
		}
		mu.Unlock()

		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			defer func() { <-sem }() // Release semaphore slot

			task := tasks[idx]
			result, err := task(taskCtx)

			mu.Lock()
			defer mu.Unlock()

			if err != nil && firstErr == nil {
				firstErr = err
				shouldStop = true
				cancel() // Cancel context to stop other tasks
			}

			if err == nil {
				results[idx] = result
			}
		}(i)
	}

	// Wait for all started tasks to complete
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	// Check if context was cancelled
	if taskCtx.Err() != nil {
		return nil, taskCtx.Err()
	}

	return results, nil
}
