package main

import (
	"context"
	"errors"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

type result struct {
	index int
	val   any
	err   error
}

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}

	// ctx is cancelled if a task fails or the parent context is cancelled.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	resultsChan := make(chan result, n)
	semaphore := make(chan struct{}, workers)
	var wg sync.WaitGroup

	// Dispatcher goroutine
	go func() {
		for i := 0; i < n; i++ {
			select {
			case <-ctx.Done():
				return
			case semaphore <- struct{}{}:
				wg.Add(1)
				go func(idx int) {
					defer wg.Done()
					defer func() { <-semaphore }()
					val, err := tasks[idx](ctx)
					resultsChan <- result{index: idx, val: val, err: err}
				}(i)
			}
		}
	}()

	// Closer goroutine
	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	finalResults := make([]any, n)
	var firstErr error

	for res := range resultsChan {
		if res.err != nil && firstErr == nil {
			firstErr = res.err
			cancel() // Signal other tasks to stop
		}
		if res.err == nil {
			finalResults[res.index] = res.val
		}
	}

	if firstErr != nil {
		return nil, firstErr
	}

	// If the loop finished but the context was cancelled (e.g. timeout), return ctx.Err()
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	return finalResults, nil
}
