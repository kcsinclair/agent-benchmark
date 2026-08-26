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
	// Validation
	if workers < 1 {
		return nil, errors.New("workers must be >= 1")
	}
	if len(tasks) == 0 {
		return nil, nil
	}

	// Result slice
	results := make([]any, len(tasks))

	// Derived context that can be cancelled on error or parent cancellation
	ctx2, cancel := context.WithCancel(ctx)
	defer cancel()

	// Job type to keep the original index
	type job struct {
		idx int
		t   Task
	}

	// Channel for jobs – buffered to avoid blocking on send when workers are busy
	jobsCh := make(chan job, workers)

	var wg sync.WaitGroup
	var once sync.Once
	var firstErr error

	// Worker goroutine
	worker := func() {
		defer wg.Done()
		for j := range jobsCh {
			res, err := j.t(ctx2)
			if err != nil {
				once.Do(func() {
					firstErr = err
					cancel() // cancel all running tasks
				})
				continue
			}
			results[j.idx] = res
		}
	}

	// Start workers
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go worker()
	}

	// Send jobs, stop if context is cancelled or an error occurs
sendLoop:
	for i, t := range tasks {
		select {
		case <-ctx2.Done():
			break sendLoop
		case jobsCh <- job{idx: i, t: t}:
		}
	}
	close(jobsCh)

	// Wait for all workers to finish
	wg.Wait()

	// Return according to the outcome
	if firstErr != nil {
		return nil, firstErr
	}
	if ctx2.Err() != nil {
		return nil, ctx2.Err()
	}
	return results, nil
}
