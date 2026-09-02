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

	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	taskChan := make(chan int)
	resChan := make(chan result)
	var wg sync.WaitGroup

	var errOnce sync.Once
	var firstErr error
	setError := func(err error) {
		if err != nil {
			errOnce.Do(func() {
				firstErr = err
				cancel()
			})
		}
	}

	// Start workers
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range taskChan {
				select {
				case <-runCtx.Done():
					return
				default:
				}

				val, err := tasks[idx](runCtx)

				select {
				case resChan <- result{index: idx, val: val, err: err}:
					if err != nil {
						setError(err)
					}
				case <-runCtx.Done():
					return
				}
			}
		}()
	}

	// Dispatcher
	go func() {
		defer close(taskChan)
		for i := 0; i < n; i++ {
			select {
			case <-runCtx.Done():
				return
			case taskChan <- i:
			}
		}
	}()

	// Closer: ensures resChan is closed after all workers exit.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	results := make([]any, n)
	completed := 0

	// Collector
	for completed < n {
		select {
		case res, ok := <-resChan:
			if !ok {
				goto finished
			}
			if res.err != nil {
				// This is handled by setError, but we catch it here to exit loop.
				goto finished
			}
			results[res.index] = res.val
			completed++
		case <-runCtx.Done():
			goto finished
		}
	}

finished:
	// Wait for all workers to finish to prevent leaks.
	wg.Wait()

	if firstErr != nil {
		// If the error is context cancellation, check if it was the parent or internal.
		if errors.Is(firstErr, context.Canceled) && ctx.Err() != nil {
			return nil, ctx.Err()
		}
		return nil, firstErr
	}

	if runCtx.Err() != nil {
		return nil, runCtx.Err()
	}

	return results, nil
}

type result struct {
	index int
	val   any
	err   error
}
