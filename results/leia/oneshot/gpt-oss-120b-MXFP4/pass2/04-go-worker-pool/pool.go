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
	// validation
	if workers < 1 {
		return nil, errors.New("workers must be >= 1")
	}
	if len(tasks) == 0 {
		return nil, nil
	}

	// runCtx can be cancelled when the first error appears or when the
	// parent context is cancelled.
	runCtx, cancelAll := context.WithCancel(ctx)
	defer cancelAll()

	type job struct {
		idx int
		fn  Task
	}
	jobs := make(chan job)

	results := make([]any, len(tasks))

	var wg sync.WaitGroup
	var once sync.Once
	var firstErr error

	worker := func() {
		defer wg.Done()
		for j := range jobs {
			// Do not start a task if the run has already been cancelled.
			select {
			case <-runCtx.Done():
				continue // skip this job
			default:
			}

			val, err := j.fn(runCtx)
			if err != nil {
				once.Do(func() {
					firstErr = err
					cancelAll()
				})
				continue
			}
			results[j.idx] = val
		}
	}

	// start the fixed pool
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go worker()
	}

	// feeder goroutine
	go func() {
		defer close(jobs)
		for i, t := range tasks {
			select {
			case <-runCtx.Done():
				return // stop feeding new jobs
			case jobs <- job{idx: i, fn: t}:
			}
		}
	}()

	// wait for all workers to finish
	wg.Wait()

	// propagate the first error, if any
	if firstErr != nil {
		return nil, firstErr
	}
	// propagate parent context cancellation
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	return results, nil
}
