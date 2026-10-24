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

	// Task context is cancelled only through our own cancel, so that the
	// recorded first error is always set before tasks observe cancellation.
	tctx, cancel := context.WithCancel(context.WithoutCancel(ctx))
	defer cancel()

	results := make([]any, n)
	var (
		mu       sync.Mutex
		next     int
		firstErr error
	)
	setErr := func(e error) {
		mu.Lock()
		if firstErr == nil {
			firstErr = e
		}
		mu.Unlock()
		cancel()
	}

	stop := make(chan struct{})
	var watcher sync.WaitGroup
	watcher.Add(1)
	go func() {
		defer watcher.Done()
		select {
		case <-ctx.Done():
			setErr(ctx.Err())
		case <-stop:
		}
	}()

	if workers > n {
		workers = n
	}
	var wg sync.WaitGroup
	wg.Add(workers)
	for w := 0; w < workers; w++ {
		go func() {
			defer wg.Done()
			for {
				mu.Lock()
				if firstErr != nil || next >= n {
					mu.Unlock()
					return
				}
				if err := ctx.Err(); err != nil {
					mu.Unlock()
					setErr(err)
					return
				}
				i := next
				next++
				mu.Unlock()

				res, err := tasks[i](tctx)
				if err != nil {
					setErr(err)
					return
				}
				results[i] = res
			}
		}()
	}
	wg.Wait()
	close(stop)
	watcher.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err != nil {
		return nil, err
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	return results, nil
}
