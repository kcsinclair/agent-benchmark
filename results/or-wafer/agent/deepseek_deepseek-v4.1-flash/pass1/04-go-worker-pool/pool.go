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
		return nil, errors.New("pool: workers must be >= 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Child context so we can cancel still-running tasks on failure/timeout.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var (
		wg       sync.WaitGroup
		firstErr error
		errOnce  sync.Once
	)

	// setErr records the first error observed and cancels the task context.
	setErr := func(err error) {
		if err == nil {
			return
		}
		errOnce.Do(func() {
			firstErr = err
			cancel()
		})
	}

	// A semaphore bounds the number of concurrently executing tasks.
	sem := make(chan struct{}, workers)

	// dispatch hands out indices; a goroutine that has not yet acquired the
	// semaphore returns immediately once the context is done, so unstarted
	// tasks never run.
dispatch:
	for i := range tasks {
		select {
		case sem <- struct{}{}:
			// Slot acquired: this task is now considered started.
		case <-taskCtx.Done():
			break dispatch
		}
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			defer func() { <-sem }()
			v, err := tasks[idx](taskCtx)
			if err != nil {
				setErr(err)
				return
			}
			results[idx] = v
		}(i)
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
