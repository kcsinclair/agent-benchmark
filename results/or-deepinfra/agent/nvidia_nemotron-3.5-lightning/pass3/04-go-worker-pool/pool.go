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
	// Validation: workers < 1 → immediate error, no tasks run.
	if workers < 1 {
		return nil, errors.New("pool: workers must be >= 1")
	}

	// Empty tasks → empty result, nil error.
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// If the parent context is already cancelled, return ctx.Err()
	// without starting any task.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// Channel to limit concurrency to `workers`.
	sem := make(chan struct{}, workers)

	// Results and errors collected from tasks.
	results := make([]any, len(tasks))
	var errs sync.Mutex // protects firstErr
	var firstErr error

	// wg waits for all started tasks to finish.
	var wg sync.WaitGroup

	// launchTasks starts up to `workers` tasks at a time, respecting
	// cancellation and the error-fast semantics.
	launchTasks := func() {
		for i := 0; i < len(tasks); i++ {
			// Check for cancellation or parent error before starting next task.
			select {
			case <-ctx.Done():
				// Cancel any in-progress task contexts and stop.
				// We'll drain the semaphore below.
				return
			default:
			}

			// If we already have a first error and we are about to start a
			// new task, we must not start it (fail fast: tasks not yet started
			// must never start). However, we still need to wait for already-
			// started tasks to finish.
			errs.Lock()
			hasErr := firstErr != nil
			errs.Unlock()
			if hasErr {
				// Drain: don't start new tasks, but still wait for existing.
				// We still need to consume from sem to allow in-flight tasks
				// to finish. So we break out of the loop entirely.
				return
			}

			wg.Add(1)
			idx := i // capture loop variable
			go func() {
				defer wg.Done()
				// Create a sub-context that can be cancelled if the parent
				// is cancelled while this task runs.
				subCtx, cancel := context.WithCancelCause(ctx)
				sem <- struct{}{} // acquire semaphore
				// Release semaphore in a deferred call so it always happens.
				defer func() { <-sem }()

				val, err := tasks[idx](subCtx)
				if err != nil {
					errs.Lock()
					if firstErr == nil {
						firstErr = err
					}
					errs.Unlock()
				}
				results[idx] = val
			}()
		}
	}

	// Start launching goroutine. It will respect the semaphore and the
	// loop condition.
	go launchTasks()

	// Wait for all started tasks to complete.
	wg.Wait()

	// After all tasks have finished (or were cancelled), check context error.
	if ctx.Err() != nil && firstErr == nil {
		return nil, ctx.Err()
	}
	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
