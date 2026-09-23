package main

import (
	"context"
	"errors"
	"sync"
)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("workers must be >= 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// result holds the output values in order.
	results := make([]any, len(tasks))
	// errMu protects the first error that is returned.
	var errMu struct {
		sync.Mutex
		err error
	}
	// errMu.err will store the first non-nil error encountered.

	// sem limits the number of concurrently running tasks.
	sem := make(chan struct{}, workers)

	// wg waits for all started tasks to finish.
	var wg sync.WaitGroup

	// start launches a single task and returns a cancel function.
	start := func(i int, task Task) {
		// If we already have an error, skip starting new tasks.
		errMu.Lock()
		if errMu.err != nil {
			errMu.Unlock()
			return
		}
		errMu.Unlock()

		sem <- struct{}{}
		wg.Add(1)

		// Run the task with a derived context that can be cancelled when the first error occurs.
		taskCtx, cancel := context.WithCancel(ctx)
		go func() {
			defer wg.Done()
			defer cancel() // ensure the derived context is cancelled when the goroutine exits
			// If the parent context is already done, skip execution.
			if <-taskCtx.Done() {
				// No need to run the task.
				<-sem // release the slot
				return
			}

			val, err := task(taskCtx)

			// Record the first error.
			errMu.Lock()
			if errMu.err == nil && err != nil {
				errMu.err = err
			}
			// If an error has been recorded, we still need to store the result
			// for ordering, but the final return will be an error.
			results[i] = val
			// Signal that we have an error; this will prevent further task starts.
			if errMu.err != nil {
				// Drain the semaphore to stop new tasks from being started.
				// Note: we may have already released the slot above, but we need to
				// ensure that any future attempts to acquire it are blocked.
				// The simplest way is to replace the sem channel with a buffered channel
				// that we close when an error occurs, but to keep it simple we just
				// continue to acquire/release as normal; the start function checks errMu.err
				// before proceeding.
			}
			<-sem // release the slot
			errMu.Unlock()
		}()
	}

	// Launch all tasks in order.
	for i, task := range tasks {
		start(i, task)
	}

	// Wait for all launched goroutines to finish.
	wg.Wait()

	// If we have an error, return nil slice and the error.
	if errMu.err != nil {
		return nil, errMu.err
	}
	return results, nil
}
