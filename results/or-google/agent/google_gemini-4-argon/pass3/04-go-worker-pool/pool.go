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
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)

	var (
		mu       sync.Mutex
		nextIdx  int
		firstErr error
	)

	numWorkers := workers
	if numWorkers > n {
		numWorkers = n
	}

	var wg sync.WaitGroup
	wg.Add(numWorkers)

	for w := 0; w < numWorkers; w++ {
		go func() {
			defer wg.Done()
			for {
				mu.Lock()
				if firstErr != nil || runCtx.Err() != nil || nextIdx >= n {
					mu.Unlock()
					return
				}
				idx := nextIdx
				nextIdx++
				mu.Unlock()

				if runCtx.Err() != nil {
					return
				}

				res, err := tasks[idx](runCtx)
				if err != nil {
					mu.Lock()
					if firstErr == nil {
						if ctx.Err() != nil && errors.Is(err, ctx.Err()) {
							firstErr = ctx.Err()
						} else {
							firstErr = err
						}
						cancel()
					}
					mu.Unlock()
					return
				}

				results[idx] = res
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
