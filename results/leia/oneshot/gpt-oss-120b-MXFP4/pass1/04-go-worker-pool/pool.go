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
	// ---- validation ---------------------------------------------------------
	if workers < 1 {
		return nil, errors.New("workers must be >= 1")
	}
	if len(tasks) == 0 {
		// empty input – nothing to do
		return nil, nil
	}

	// ---- preparation --------------------------------------------------------
	// derived context that we can cancel when the first error appears or when
	// the parent context is done.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	type job struct {
		idx  int
		task Task
	}

	// channel that feeds jobs to workers
	jobs := make(chan job)

	// slice that will hold the results; each index is written by exactly one
	// worker, so no additional synchronization is required for the slice.
	results := make([]any, len(tasks))

	// once is used to capture the *first* error that occurs.
	var once sync.Once
	var firstErr error

	// ---- workers ------------------------------------------------------------
	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					// cancelled – stop processing further jobs
					return
				case j, ok := <-jobs:
					if !ok {
						// no more jobs
						return
					}
					// run the task
					res, err := j.task(ctx)
					if err != nil {
						once.Do(func() {
							firstErr = err
							cancel() // fail‑fast: stop everything else
						})
						// we do **not** store a result for a failed task
						continue
					}
					// successful – store result at the proper index
					results[j.idx] = res
				}
			}
		}()
	}

	// ---- job feeder ---------------------------------------------------------
	// This goroutine pushes jobs onto the channel respecting cancellation.
	go func() {
		defer close(jobs)
		for i, t := range tasks {
			select {
			case <-ctx.Done():
				// stop feeding new jobs as soon as we are cancelled
				return
			case jobs <- job{idx: i, task: t}:
				// job queued
			}
		}
	}()

	// ---- wait for everything to finish ------------------------------------
	wg.Wait()

	// ---- decide what to return ---------------------------------------------
	if firstErr != nil {
		// an error from a task – return it (the context is already cancelled)
		return nil, firstErr
	}
	if ctx.Err() != nil {
		// parent context was cancelled or timed‑out
		return nil, ctx.Err()
	}
	// success
	return results, nil
}
