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
	// Validation: workers < 1 → immediate error
	if workers < 1 {
		return nil, errors.New("pool: workers must be >= 1")
	}

	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}

	results := make([]any, n)
	var mu sync.Mutex
	var wg sync.WaitGroup

	// channel to limit concurrent execution; capacity = workers
	sem := make(chan struct{}, workers)

	// protect firstErr
	var firstErr error

	// We cancel a copy of the context so the original is not mutated prematurely.
	// The defer cancel will run when Run returns.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Start tasks respecting the workers bound and ctx cancellation
	for i, task := range tasks {
		// Before trying to start a new task, check if context was already cancelled.
		select {
		case <-ctx.Done():
			// Cancel any in‑flight tasks by closing the semaphore.
			close(sem)
			// Wait for already‑started goroutines to finish.
			wg.Wait()
			return nil, ctx.Err()
		default:
		}

		wg.Add(1)
		sem <- struct{}{} // acquire a slot (blocks if at the bound)

		go func(idx int, t Task) {
			defer wg.Done()
			// Run the task with the (possibly cancelled) context
			val, err := t(ctx)
			mu.Lock()
			results[idx] = val
			if err != nil && firstErr == nil {
				firstErr = err
			}
			mu.Unlock()
			<-sem // release the slot
		}(i, task)
	}

	// Wait for all goroutines to finish
	wg.Wait()

	// After all tasks finished, check context error (covers the case where
	// ctx was cancelled while tasks were running).
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// If any task returned an error, fail fast with the first error.
	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
