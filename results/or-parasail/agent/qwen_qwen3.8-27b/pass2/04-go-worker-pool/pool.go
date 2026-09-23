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

	var (
		mu       sync.Mutex
		startErr error // first task error, if any
	)

	// recordErr stores the first error and cancels the task context so
	// in-flight tasks can abort and no new tasks start.
	recordErr := func(err error) {
		if err == nil {
			return
		}
		mu.Lock()
		if startErr == nil {
			startErr = err
		}
		mu.Unlock()
		cancel()
	}

	// runWorker executes jobs until the jobs channel is closed.
	runWorker := func() {
		for j := range jobs {
			// Gate: only start the task if no error has been recorded yet.
			// This is checked under the same mutex that recordErr uses, so
			// a task can never start after a failure has been recorded.
			mu.Lock()
			aborted := startErr != nil
			mu.Unlock()
			if aborted {
				continue
			}
			res, err := j.task(taskCtx)
			if err != nil {
				recordErr(err)
				continue
			}
			results[j.index] = res
		}
	}

	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			runWorker()
		}()
	}

	// Dispatcher: feed jobs to workers, but stop early on error or
	// parent cancellation.
	go func() {
		defer close(jobs)
		for i, t := range tasks {
			select {
			case jobs <- job{index: i, task: t}:
			case <-taskCtx.Done():
				return
			}
		}
	}()

	// Wait for all workers to finish (no goroutine leaks).
	wg.Wait()

	// Determine the error to return.
	mu.Lock()
	firstErr := startErr
	mu.Unlock()

	if firstErr != nil {
		return nil, firstErr
	}

	// No task error: check whether the parent context was cancelled.
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	return results, nil
}
