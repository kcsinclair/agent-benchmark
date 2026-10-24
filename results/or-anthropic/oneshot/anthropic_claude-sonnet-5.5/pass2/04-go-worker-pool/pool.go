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
	if workers > len(tasks) {
		workers = len(tasks)
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var (
		mu       sync.Mutex
		next     int
		failed   bool
		firstErr error
	)

	// claim returns the next task index to run, or false if no more tasks
	// should be started (failure, cancellation, or all tasks claimed).
	claim := func() (int, bool) {
		mu.Lock()
		defer mu.Unlock()
		if failed || runCtx.Err() != nil || next >= len(tasks) {
			return 0, false
		}
		i := next
		next++
		return i, true
	}

	fail := func(err error) {
		mu.Lock()
		if !failed {
			failed = true
			firstErr = err
		}
		mu.Unlock()
		cancel()
	}

	var wg sync.WaitGroup
	wg.Add(workers)
	for w := 0; w < workers; w++ {
		go func() {
			defer wg.Done()
			for {
				i, ok := claim()
				if !ok {
					return
				}
				res, err := tasks[i](runCtx)
				if err != nil {
					fail(err)
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
