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
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	var (
		wg       sync.WaitGroup
		errOnce  sync.Once
		firstErr error
	)

	setError := func(err error) {
		errOnce.Do(func() {
			firstErr = err
			cancel()
		})
	}

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)

loop:
	for i, task := range tasks {
		// Fast-path check before attempting to acquire a worker slot.
		if runCtx.Err() != nil {
			break
		}

		// Acquire a worker slot or abort if the context is cancelled.
		select {
		case <-runCtx.Done():
			break loop
		case sem <- struct{}{}:
		}

		// Re-check after acquiring the slot in case both select cases were ready
		// simultaneously and the random selection picked the semaphore.
		if runCtx.Err() != nil {
			<-sem
			break loop
		}

		wg.Add(1)
		go func(idx int, t Task) {
			defer wg.Done()
			defer func() { <-sem }()

			res, err := t(runCtx)
			if err != nil {
				setError(err)
				return
			}
			results[idx] = res
		}(i, task)
	}

	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	return results, nil
}
