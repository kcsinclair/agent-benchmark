package main

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
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
		nextIdx  atomic.Int64
		wg       sync.WaitGroup
		errOnce  sync.Once
		firstErr error
	)

	 recordErr := func(err error) {
		errOnce.Do(func() {
			firstErr = err
			cancel()
		})
	}

	numWorkers := workers
	if numWorkers > n {
		numWorkers = n
	}

	wg.Add(numWorkers)
	for w := 0; w < numWorkers; w++ {
		go func() {
			defer wg.Done()
			for {
				if err := runCtx.Err(); err != nil {
					recordErr(ctx.Err())
					return
				}

				i := int(nextIdx.Add(1) - 1)
				if i >= n {
					return
				}

				if err := runCtx.Err(); err != nil {
					recordErr(ctx.Err())
					return
				}

				res, err := tasks[i](runCtx)
				if err != nil {
					recordErr(err)
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
