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
	if ctx == nil {
		ctx = context.Background()
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	tctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)

	var (
		wg       sync.WaitGroup
		mu       sync.Mutex
		firstErr error
	)
	record := func(err error) {
		mu.Lock()
		if firstErr == nil {
			if perr := ctx.Err(); perr != nil {
				firstErr = perr
			} else {
				firstErr = err
			}
		}
		mu.Unlock()
		cancel()
	}

loop:
	for i, t := range tasks {
		select {
		case <-tctx.Done():
			break loop
		case sem <- struct{}{}:
		}
		// Re-check: select picks randomly when both are ready.
		if tctx.Err() != nil {
			<-sem
			break loop
		}
		wg.Add(1)
		go func(i int, t Task) {
			defer wg.Done()
			defer func() { <-sem }()
			v, err := t(tctx)
			if err != nil {
				record(err)
				return
			}
			results[i] = v
		}(i, t)
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
