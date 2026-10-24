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
	// Respect an already-cancelled parent context without starting anything.
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	parent := ctx
	taskCtx, cancel := context.WithCancel(parent)
	defer cancel()

	var (
		mu       sync.Mutex
		firstErr error
		wg       sync.WaitGroup
	)

	// setErr records the first error and cancels the task context.
	// If the parent has been cancelled by the time the error is observed,
	// the parent's error is reported (the task error is most likely a
	// consequence of the cancellation).
	setErr := func(err error) {
		mu.Lock()
		if firstErr == nil {
			if perr := parent.Err(); perr != nil {
				firstErr = perr
			} else {
				firstErr = err
			}
		}
		mu.Unlock()
		cancel()
	}

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)

dispatch:
	for i, t := range tasks {
		// Acquire a worker slot, or stop if cancelled / failed.
		select {
		case <-taskCtx.Done():
			break dispatch
		case sem <- struct{}{}:
		}
		// select may choose the send even if ctx is already done.
		if taskCtx.Err() != nil {
			<-sem
			break dispatch
		}

		wg.Add(1)
		go func(i int, t Task) {
			defer wg.Done()
			defer func() { <-sem }()

			// Last-moment check: never start a task after a failure/cancel.
			if taskCtx.Err() != nil {
				return
			}
			if t == nil {
				setErr(fmt.Errorf("pool: task %d is nil", i))
				return
			}
			v, err := t(taskCtx)
			if err != nil {
				setErr(err)
				return
			}
			results[i] = v // distinct index per goroutine: race-free
		}(i, t)
	}

	// Wait for every started task before returning (no leaks).
	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err != nil {
		return nil, err
	}
	if perr := parent.Err(); perr != nil {
		return nil, perr
	}
	return results, nil
}
