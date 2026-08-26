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
		return nil, nil
	}

	// ---- preparation --------------------------------------------------------
	// context that will be cancelled as soon as we need to stop the work
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	type job struct {
		idx  int
		task Task
	}
	jobCh := make(chan job) // unbuffered – guarantees at most `workers` tasks run

	// channel closed the first time we have to stop feeding new jobs
	stopCh := make(chan struct{})
	var stopOnce sync.Once
	stop := func() { stopOnce.Do(func() { close(stopCh) }) }

	var wg sync.WaitGroup
	var errOnce sync.Once
	var firstErr error

	// record the first error (task error or parent‑context cancellation)
	setError := func(err error) {
		errOnce.Do(func() {
			firstErr = err
			cancel() // cancel the derived context for all running tasks
			stop()   // stop feeding new jobs
		})
	}

	// ---- workers ------------------------------------------------------------
	if workers > len(tasks) {
		workers = len(tasks)
	}
	worker := func() {
		defer wg.Done()
		for j := range jobCh {
			// If the context is already cancelled we must not start the task.
			if taskCtx.Err() != nil {
				continue
			}
			res, err := j.task(taskCtx)
			if err != nil {
				setError(err)
				continue
			}
			// each index is written by exactly one worker → no race
			results[j.idx] = res
		}
	}
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go worker()
	}

	// ---- feed jobs -----------------------------------------------------------
	stopped := false
	for i, t := range tasks {
		if stopped {
			break
		}
		select {
		case <-ctx.Done():
			// parent context finished – treat as an error
			setError(ctx.Err())
			stopped = true
		case <-stopCh:
			// an earlier task already failed
			stopped = true
		case jobCh <- job{idx: i, task: t}:
			// job successfully handed to a worker
		}
	}
	close(jobCh) // no more jobs

	// ---- wait for workers ---------------------------------------------------
	wg.Wait()

	// ---- final result -------------------------------------------------------
	if firstErr != nil {
		return nil, firstErr
	}
	return results, nil
}
