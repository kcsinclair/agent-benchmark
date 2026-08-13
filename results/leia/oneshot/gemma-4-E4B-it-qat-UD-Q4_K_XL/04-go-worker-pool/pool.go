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
	n := len(tasks)
	if n == 0 {
		return nil, nil
	}

	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	// result holds the final values, indexed by the original task index.
	results := make([]any, n)
	// errHolder stores the first error encountered.
	var errHolder error
	// mu protects access to errHolder.
	var mu sync.Mutex

	// workerDone signals when a worker has finished its current task.
	workerDone := make(chan struct{}, workers)
	// taskDone signals when a specific task has completed (either successfully or with an error).
	taskDone := make(chan struct{}, n)

	// We use a context derived from the parent context to manage the lifecycle
	// of the pool execution, allowing us to cancel all pending/running tasks
	// if the parent context is cancelled or an error occurs.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel() // Ensure cancellation happens when Run exits

	// Semaphore to limit concurrency to 'workers'.
	// We use a buffered channel of size 'workers'. Sending to it blocks if full.
	semaphore := make(chan struct{}, workers)

	// Start a goroutine to monitor the context and the error state.
	// This goroutine handles the "Fail fast" and "Context cancellation" requirements.
	go func() {
		select {
		case <-ctx.Done():
			// Parent context cancelled or we explicitly cancelled it.
			// We must wait for all started tasks to finish before returning.
			// The main loop below handles waiting for taskDone.
			return
		case <-errHolder:
			// An error has been recorded. We must stop starting new tasks.
			// The main loop will detect this and stop dispatching.
			return
		}
	}()

	// Dispatch tasks
	for i := 0; i < n; i++ {
		// Check if we should stop dispatching due to context cancellation or error
		select {
		case <-ctx.Done():
			// Context cancelled before we could start task i.
			// We must wait for all currently running tasks to finish.
			// The main loop handles this waiting.
			return
		default:
			// Continue to start the task
		}

		// Acquire a slot in the semaphore. This blocks if 'workers' are already running.
		select {
		case semaphore <- struct{}{}:
			// Slot acquired, start the task.
			go func(taskIndex int, t Task) {
				defer func() {
					// Release the semaphore slot when the task finishes.
					<-semaphore
					// Signal that this specific task is done.
					taskDone <- struct{}{}
				}()

				// Execute the task with the derived context.
				val, err := t(ctx)

				if err != nil {
					// Record the first error encountered.
					mu.Lock()
					if errHolder == nil {
						errHolder = err
					}
					mu.Unlock()
					// Note: We don't cancel the context here immediately because
					// we must wait for all *started* tasks to finish (Requirement 4).
					// The main loop will handle the final cancellation/return.
					return
				}

				// Store the result.
				results[taskIndex] = val
			}(i, tasks[i])
		case <-ctx.Done():
			// Context cancelled while waiting for a semaphore slot.
			// Stop dispatching and let the main loop handle cleanup.
			return
		}
	}

	// Wait for all tasks to complete.
	// We wait for 'n' signals on taskDone.
	for i := 0; i < n; i++ {
		select {
		case <-taskDone:
			// Task finished.
		case <-ctx.Done():
			// Context cancelled while waiting for tasks to finish.
			// Return the context error.
			return nil, ctx.Err()
		}
	}

	// If we reached here, all tasks finished.
	// Check if any error was recorded.
	if errHolder != nil {
		// Requirement 4: Return the first error.
		return nil, errHolder
	}

	// Success.
	return results, nil
}
