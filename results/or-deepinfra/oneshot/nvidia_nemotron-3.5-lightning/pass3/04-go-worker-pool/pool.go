package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	// Validation: workers < 1 -> immediate error, no tasks started.
	if workers < 1 {
		return nil, errWorkers
	}

	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}

	// Shared state.
	var (
		mu         sync.Mutex
		results    = make([]any, n)
		doneCount  int32
		errResult  error // first error encountered
		errMu      sync.Mutex // protects errResult
	)

	// taskCh dispatches tasks to workers. Closing it signals "no more tasks".
	taskCh := make(chan int, n) // task index
	resultCh := make(chan result, n)

	// Start worker goroutines.
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range taskCh {
				// Each task gets a copy of the parent context that can be cancelled.
				taskCtx, cancel := context.WithCancelCause(ctx)
				val, err := tasks[idx](taskCtx)
				cancel(nil) // notify the task that we are done reading from taskCh
				resultCh <- result{
					Idx:   idx,
					Val:   val,
					Err:   err,
				}
			}
		}()
	}

	// Send task indices to workers.
	go func() {
		for i := 0; i < n; i++ {
			taskCh <- i
		}
		close(taskCh)
	}()

	// Collect results.
	go func() {
		wg.Wait() // wait for all workers to finish processing already-sent tasks
		close(resultCh)
	}()

	// Drain result channel and handle errors / context cancellation.
	// We use a select to also watch for ctx.Done().
	for r := range resultCh {
		mu.Lock()
		results[r.Idx] = r.Val
		mu.Unlock()

		if r.Err != nil {
			errMu.Lock()
			if errResult == nil {
				errResult = r.Err
			}
			errMu.Unlock()
		}
	}

	// At this point all tasks have finished (or were cancelled).
	// Check if parent context was cancelled while we were running.
	if ctx.Err() != nil {
		// If we already have an task error, wrap it; otherwise return ctx error.
		if errResult != nil {
			return nil, errResult //nolint:wrapcheck // we just return the error, wrapping is implicit via sentinel
		}
		return nil, ctx.Err()
	}

	// No ctx cancellation and no task errors.
	if errResult == nil {
		return results, nil
	}

	// Task error occurred and ctx is not cancelled.
	return nil, errResult
}

// result holds a single task's index, value, and error.
type result struct {
	Idx   int
	Val   any
	Err   error
}

// errWorkers is returned when workers < 1.
var errWorkers = errNew("workers must be >= 1")

// errNew wraps a message into an error for pool use.
func errNew(msg string) error {
	return &errNewError(msg)
}

type errNewError struct {
	msg string
}

func (e *errNewError) Error() string { return e.msg }
func (e *errNewError) Unwrap() error  { return nil }
