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
	if ctx == nil {
		ctx = context.Background()
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var (
		mu       sync.Mutex
		next     int
		firstErr error
	)

	// claim returns the next task index to run, or -1 if no more should start.
	claim := func() int {
		mu.Lock()
		defer mu.Unlock()
		if firstErr != nil || runCtx.Err() != nil || next >= len(tasks) {
			return -1
		}
		i := next
		next++
		return i
	}

	fail := func(err error) {
		mu.Lock()
		if firstErr == nil {
			firstErr = err
		}
		mu.Unlock()
		cancel()
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
				i := claim()
				if i < 0 {
					return
				}
				v, err := tasks[i](runCtx)
				if err != nil {
					fail(err)
					return
				}
				results[i] = v
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
