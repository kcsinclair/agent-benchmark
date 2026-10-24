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
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	cctx, cancel := context.WithCancel(ctx)
	defer cancel()

	var (
		mu       sync.Mutex
		firstErr error
		wg       sync.WaitGroup
	)
	setErr := func(err error) {
		mu.Lock()
		if firstErr == nil {
			firstErr = err
		}
		mu.Unlock()
		cancel()
	}

	stop := context.AfterFunc(ctx, func() { setErr(ctx.Err()) })
	defer stop()

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)

dispatch:
	for i, t := range tasks {
		select {
		case sem <- struct{}{}:
		case <-cctx.Done():
			break dispatch
		}
		// Check failure state and launch atomically w.r.t. setErr so that no
		// task starts after an error has been recorded.
		mu.Lock()
		if firstErr != nil || cctx.Err() != nil {
			mu.Unlock()
			<-sem
			break dispatch
		}
		wg.Add(1)
		go func(i int, t Task) {
			defer wg.Done()
			defer func() { <-sem }()
			v, err := t(cctx)
			if err != nil {
				setErr(err)
				return
			}
			results[i] = v
		}(i, t)
		mu.Unlock()
	}

	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err == nil && cctx.Err() != nil && ctx.Err() != nil {
		// Parent cancelled but AfterFunc not yet recorded; honor it only if
		// dispatch was cut short (some task not run).
		err = ctx.Err()
	}
	if err != nil {
		return nil, err
	}
	return results, nil
}
