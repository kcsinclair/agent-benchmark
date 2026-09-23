package main

import (
	"context"
	"errors"
	"sync"
	"time"
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

	n := len(tasks)
	results := make([]any, n)

	// If the parent context is already cancelled, return immediately.
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	// sem limits concurrent executing tasks to `workers`.
	sem := make(chan struct{}, workers)

	// taskCtx/taskCancel is a child context that we cancel when any task errors
	// or the parent context cancels. All running tasks receive this same context.
	taskCtx, taskCancel := context.WithCancelCause(context.Background())

	// ch is used to collect completion signals from goroutines.
	// We send a struct{} for each completed task; we need n signals.
	ch := make(chan struct{}, n)

	var mu sync.Mutex // protects firstError and results fills
	var firstError error

	for i := 0; i < n; i++ {
		// If the parent context is cancelled, stop starting new tasks.
		select {
		case <-ctx.Done():
			taskCancel(ctx.Err())
			// Drain ch to unblock waiters, then wait for started tasks to finish.
			for range ch {
			}
			return nil, ctx.Err()
		default:
		}

		// Acquire a slot in the semaphore.
		sem <- struct{}{}

		// Launch the task in a goroutine.
		go func(idx int) {
			// Run the task on the child context.
			val, err := tasks[idx](taskCtx)

			// Release the semaphore slot.
			<-sem

			if err != nil {
				mu.Lock()
				if firstError == nil {
					firstError = err
				}
				mu.Unlock()
			}

			results[idx] = val
			ch <- struct{}{}
		}(i)
	}

	// Wait for all n tasks to finish.
	for range ch {
	}

	// If there was a first error, return (nil, err).
	if firstError != nil {
		return nil, firstError
	}

	return results, nil
}
