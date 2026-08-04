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
		return nil, errors.New("workers must be >= 1")
	}
	if len(tasks) == 0 {
		return nil, nil
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)
	var wg sync.WaitGroup
	var firstErr error
	var firstErrOnce sync.Once

	for i, task := range tasks {
		if ctx.Err() != nil {
			break
		}

		wg.Add(1)
		go func(i int, task Task) {
			defer wg.Done()

			// Acquire semaphore to limit concurrency.
			// On context cancellation, exit without running.
			select {
			case sem <- struct{}{}:
			case <-ctx.Done():
				return
			}
			defer func() { <-sem }()

			result, err := task(ctx)

			results[i] = result
			if err != nil {
				firstErrOnce.Do(func() {
					firstErr = err
					cancel()
				})
			}
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
