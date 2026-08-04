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
	var shouldStop bool

	// We need to ensure that if an error occurs, we don't start new tasks.
	// We'll use a channel or atomic flag. Let's use a simple flag protected by mu.

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
			// Release the semaphore slot since we're not running the task
			<-sem
			break
		}
		mu.Unlock()

		wg.Add(1)
		go func(idx int, t Task) {
			defer wg.Done()
			defer func() { <-sem }() // Release semaphore slot

			result, err := t(taskCtx)

			mu.Lock()
			if firstErr == nil {
				if err != nil {
					firstErr = err
					shouldStop = true
					cancel() // Cancel context to stop other tasks
				}
				results[idx] = result
			}
			mu.Unlock()
		}(i, tasks[i])
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
