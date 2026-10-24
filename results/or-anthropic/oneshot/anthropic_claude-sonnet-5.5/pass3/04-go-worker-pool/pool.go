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
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	var (
		mu       sync.Mutex
		next     int
		failed   bool
		firstErr error
	)
	results := make([]any, len(tasks))

	// claim returns the next task index to run, or false if no more tasks
	// may be started (all claimed, a task failed, or the context is done).
	claim := func() (int, bool) {
		mu.Lock()
		defer mu.Unlock()
		if failed || next >= len(tasks) || runCtx.Err() != nil {
			return 0, false
		}
		i := next
		next++
		return i, true
	}

	n := workers
	if n > len(tasks) {
		n = len(tasks)
	}

	var wg sync.WaitGroup
	wg.Add(n)
	for w := 0; w < n; w++ {
		go func() {
			defer wg.Done()
			for {
				i, ok := claim()
				if !ok {
					return
				}
				res, err := tasks[i](runCtx)
				if err != nil {
					mu.Lock()
					if !failed {
						failed = true
						firstErr = err
					}
					mu.Unlock()
					cancel()
					return
				}
				results[i] = res
			}
		}()
	}
	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err != nil {
		return nil, err
	}
	if perr := ctx.Err(); perr != nil {
		return nil, perr
	}
	return results, nil
}
