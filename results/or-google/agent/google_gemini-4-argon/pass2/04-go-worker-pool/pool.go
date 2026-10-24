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

	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	n := len(tasks)
	numWorkers := workers
	if numWorkers > n {
		numWorkers = n
	}

	results := make([]any, n)

	var (
		mu       sync.Mutex
		nextIdx  int
		firstErr error
		wg       sync.WaitGroup
	)

	wg.Add(numWorkers)
	for w := 0; w < numWorkers; w++ {
		go func() {
			defer wg.Done()
			for {
				mu.Lock()
				if firstErr != nil || taskCtx.Err() != nil || nextIdx >= n {
					if firstErr == nil && ctx.Err() != nil {
						firstErr = ctx.Err()
					}
					mu.Unlock()
					return
				}
				i := nextIdx
				nextIdx++
				mu.Unlock()

				res, err := tasks[i](taskCtx)
				if err != nil {
					mu.Lock()
					if firstErr == nil {
						if ctx.Err() != nil {
							firstErr = ctx.Err()
						} else {
							firstErr = err
						}
						cancel()
					}
					mu.Unlock()
					return
				}

				results[i] = res
			}
		}()
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
