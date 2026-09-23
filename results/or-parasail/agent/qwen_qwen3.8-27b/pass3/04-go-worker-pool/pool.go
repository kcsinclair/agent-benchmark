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

	// firstErr records the first error that occurred. The mutex protects
	// firstErr; the done channel is closed exactly once when it is set.
	var (
		mu       sync.Mutex
		firstErr error
	)
	done := make(chan struct{})
	closeOnce := sync.OnceFunc(func() { close(done) })

	// recordErr stores err as firstErr if no error has been recorded yet.
	recordErr := func(err error) {
		if err == nil {
			return
		}
		mu.Lock()
		if firstErr == nil {
			firstErr = err
			closeOnce()
		}
		mu.Unlock()
	}

	// failed reports whether an error has already been recorded.
	failed := func() bool {
		select {
		case <-done:
			return true
		default:
			return false
		}
	}

	// worker pulls jobs off the channel and executes them.
	worker := func() {
		for j := range jobs {
			// If the parent context was cancelled, stop taking new work.
			if err := taskCtx.Err(); err != nil {
				recordErr(err)
				continue
			}
			// If a task already failed, do not start this one.
			if failed() {
				continue
			}
			val, err := j.task(taskCtx)
			results[j.index] = val
			recordErr(err)
		}
	}

	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			worker()
		}()
	}

	// Dispatcher: feed jobs to workers, but stop once a failure or parent
	// cancellation is observed.
	go func() {
		defer close(jobs)
		for i, t := range tasks {
			if failed() {
				return
			}
			if err := taskCtx.Err(); err != nil {
				recordErr(err)
				return
			}
			jobs <- job{index: i, task: t}
		}
	}()

	// Wait for all workers to finish.
	wg.Wait()

	// Determine the error to return.
	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err == nil {
		// No task error; check whether the parent context was cancelled.
		if cerr := taskCtx.Err(); cerr != nil {
			err = cerr
		}
	}
	if err != nil {
		return nil, err
	}
	return results, nil
}
