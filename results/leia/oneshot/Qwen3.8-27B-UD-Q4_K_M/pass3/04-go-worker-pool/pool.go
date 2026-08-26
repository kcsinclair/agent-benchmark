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
		return nil, context.Canceled // or a custom error; spec says non-nil error
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Create a derived context that we can cancel when we need to stop.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	var firstErr error
	var errOnce sync.Once

	// We need to track which tasks have started so we can wait for them.
	// Use a semaphore channel to limit concurrency.
	sem := make(chan struct{}, workers)

	var wg sync.WaitGroup

	// We need to ensure that once an error occurs, no new tasks start.
	// We'll use a channel to signal that we should stop dispatching.
	// Actually, we can just check if taskCtx is done before starting a new task.

	// Dispatch tasks. We'll use a separate goroutine to dispatch, or we can
	// dispatch from the main goroutine. Let's dispatch from the main goroutine
	// to keep it simple, but we need to be careful about blocking.
	//
	// Actually, the standard pattern is:
	// 1. For each task, acquire a semaphore slot.
	// 2. If the context is cancelled or an error has occurred, release the slot and stop.
	// 3. Otherwise, start the task in a goroutine.
	//
	// But we need to wait for all started tasks to finish. So we use a WaitGroup.

	for i, task := range tasks {
		// Check if we should stop dispatching.
		select {
		case <-taskCtx.Done():
			// Context was cancelled (either by parent or by us due to an error).
			// We need to wait for already-started tasks to finish.
			wg.Wait()
			if firstErr != nil {
				return nil, firstErr
			}
			return nil, taskCtx.Err()
		default:
		}

		// Acquire a semaphore slot. This blocks if all workers are busy.
		// But we need to be able to unblock if the context is cancelled.
		// So we use a select with the context done channel.
		select {
		case sem <- struct{}{}:
			// Got a slot.
		case <-taskCtx.Done():
			// Context cancelled while waiting for a slot.
			wg.Wait()
			if firstErr != nil {
				return nil, firstErr
			}
			return nil, taskCtx.Err()
		}

		// Double-check that we should still start this task.
		select {
		case <-taskCtx.Done():
			// Context was cancelled between acquiring the slot and now.
			<-sem // Release the slot.
			wg.Wait()
			if firstErr != nil {
				return nil, firstErr
			}
			return nil, taskCtx.Err()
		default:
		}

		wg.Add(1)
		go func(idx int, t Task) {
			defer wg.Done()
			defer func() { <-sem }() // Release the semaphore slot.

			result, err := t(taskCtx)
			if err != nil {
				errOnce.Do(func() {
					firstErr = err
					cancel() // Cancel the task context to stop other tasks.
				})
			} else {
				results[idx] = result
			}
		}(i, task)
	}

	// Wait for all started tasks to finish.
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}
	if err := taskCtx.Err(); err != nil {
		return nil, err
	}
	return results, nil
}
