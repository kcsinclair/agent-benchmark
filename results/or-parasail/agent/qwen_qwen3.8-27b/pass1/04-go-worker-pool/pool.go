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
		return nil, errors.New("pool: workers must be at least 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Derive a cancellable context so we can abort in-flight tasks on
	// failure or parent cancellation.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	// job is a work item handed to a worker.
	type job struct {
		index int
		task  Task
	}

	jobs := make(chan job)

	// firstErr holds the first error that occurred; guarded by errMu.
	var (
		errMu    sync.Mutex
		firstErr error
	)
	recordErr := func(err error) {
		if err == nil {
			return
		}
		errMu.Lock()
		if firstErr == nil {
			firstErr = err
		}
		errMu.Unlock()
	}

	// done is closed when all workers have finished.
	done := make(chan struct{})

	// Start the worker pool.
	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				// If the context is already cancelled, stop taking work.
				if taskCtx.Err() != nil {
					continue
				}
				val, err := j.task(taskCtx)
				if err != nil {
					recordErr(err)
					// Cancel so other in-flight tasks can abort early.
					cancel()
				} else {
					results[j.index] = val
				}
			}
		}()
	}

	// Dispatcher: feed jobs to workers, but stop on first error or ctx cancel.
	go func() {
		defer close(jobs)
		for i, t := range tasks {
			// Stop dispatching if the context was cancelled.
			if taskCtx.Err() != nil {
				return
			}
			// Stop dispatching if a task already failed.
			errMu.Lock()
			failed := firstErr != nil
			errMu.Unlock()
			if failed {
				return
			}
			jobs <- job{index: i, task: t}
		}
	}()

	// Wait for all workers to finish.
	go func() {
		wg.Wait()
		close(done)
	}()

	<-done

	// Determine the final error.
	errMu.Lock()
	runErr := firstErr
	errMu.Unlock()
	if runErr == nil {
		// No task failed; check whether the parent context was cancelled.
		if err := ctx.Err(); err != nil {
			runErr = err
		}
	}

	if runErr != nil {
		return nil, runErr
	}
	return results, nil
}
