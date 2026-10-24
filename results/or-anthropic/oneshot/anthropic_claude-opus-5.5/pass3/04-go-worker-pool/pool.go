package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, fmt.Errorf("pool: workers must be >= 1, got %d", workers)
	}
	if ctx == nil {
		return nil, errors.New("pool: nil context")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	cctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)

	var (
		wg       sync.WaitGroup
		mu       sync.Mutex
		firstErr error
	)

	// fail records the first error and cancels the shared task context.
	fail := func(err error) {
		mu.Lock()
		if firstErr == nil {
			// If the parent was cancelled, report the parent's error,
			// since that is the root cause of the abort.
			if perr := ctx.Err(); perr != nil {
				firstErr = perr
			} else {
				firstErr = err
			}
		}
		mu.Unlock()
		cancel()
	}

dispatch:
	for i, t := range tasks {
		// Acquire a worker slot, or stop if cancelled.
		select {
		case sem <- struct{}{}:
		case <-cctx.Done():
			break dispatch
		}
		// select picks randomly among ready cases; re-check cancellation
		// so that no task starts after a failure/cancellation.
		if cctx.Err() != nil {
			<-sem
			break dispatch
		}

		wg.Add(1)
		go func(i int, t Task) {
			defer wg.Done()
			v, err := t(cctx)
			if err != nil {
				// Cancel before releasing the slot so the dispatcher
				// observes cancellation before it can reuse this slot.
				fail(err)
			} else {
				results[i] = v
			}
			<-sem
		}(i, t)
	}

	// Wait for all started tasks to finish (no goroutine leaks).
	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()

	if err == nil {
		if perr := ctx.Err(); perr != nil {
			err = perr
		}
	}
	if err != nil {
		return nil, err
	}
	return results, nil
}
