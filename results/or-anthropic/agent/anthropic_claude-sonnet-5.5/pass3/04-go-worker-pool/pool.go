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
		next     int
		failed   bool
		firstErr error
		done     int
		wg       sync.WaitGroup
	)

	if workers > n {
		workers = n
	}

	worker := func() {
		defer wg.Done()
		for {
			mu.Lock()
			if failed || next >= n || runCtx.Err() != nil {
				mu.Unlock()
				return
			}
			idx := next
			next++
			mu.Unlock()

			res, err := tasks[idx](runCtx)

			mu.Lock()
			if err != nil {
				if !failed {
					failed = true
					firstErr = err
				}
				mu.Unlock()
				cancel()
				return
			}
			results[idx] = res
			done++
			mu.Unlock()
		}
	}

	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go worker()
	}
	wg.Wait()

	mu.Lock()
	defer mu.Unlock()
	if firstErr != nil {
		return nil, firstErr
	}
	if done < n {
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		return nil, context.Canceled
	}
	return results, nil
}
