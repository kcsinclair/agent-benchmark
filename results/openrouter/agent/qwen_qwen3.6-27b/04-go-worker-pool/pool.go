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
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	results := make([]any, len(tasks))
	var firstErr error
	var mu sync.Mutex
	sem := make(chan struct{}, workers)
	var wg sync.WaitGroup
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	for i, task := range tasks {
		wg.Add(1)
		go func(idx int, t Task) {
			defer wg.Done()

			// Try to acquire semaphore or wait for cancellation
			select {
			case <-taskCtx.Done():
				return
			case sem <- struct{}{}:
				// Acquired semaphore, check if we should abort
				mu.Lock()
				shouldAbort := firstErr != nil || taskCtx.Err() != nil
				mu.Unlock()
				if shouldAbort {
					<-sem // release semaphore
					return
				}

				// Run the task
				result, err := t(taskCtx)

				mu.Lock()
				if firstErr == nil {
					if err != nil {
						firstErr = err
						cancel() // cancel other tasks
					} else {
						results[idx] = result
					}
				}
				mu.Unlock()

				<-sem // release semaphore
			}
		}(i, task)
	}

	wg.Wait()

	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if firstErr != nil {
		return nil, firstErr
	}
	return results, nil
}
