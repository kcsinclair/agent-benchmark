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
		return nil, errors.New("workers must be at least 1")
	}

	n := len(tasks)
	if n == 0 {
		return nil, nil
	}

	// Create a derived context that we can cancel if a task fails
	// or if the parent context is cancelled.
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)
	
	// errOnce ensures we only capture the first error.
	var errOnce sync.Once
	var firstErr error

	// taskChan distributes indices of tasks to be processed.
	taskChan := make(chan int)

	// wg tracks all active worker goroutines to ensure no leaks.
	var wg sync.WaitGroup

	// Start the worker pool.
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-runCtx.Done():
					return
				case idx, ok := <-taskChan:
					if !ok {
						return
					}

					// Execute the task.
					res, err := tasks[idx](runCtx)

					if err != nil {
						errOnce.Do(func() {
							firstErr = err
							cancel() // Stop other tasks and prevent new ones from starting.
						})
						return
					}

					results[idx] = res
				}
			}
		}()
	}

	// Dispatcher goroutine: feeds tasks to the workers.
	go func() {
		defer close(taskChan)
		for i := 0; i < n; i++ {
			select {
			case <-runCtx.Done():
				return
			case taskChan <- i:
			}
		}
	}()

	// Wait for all workers to finish.
	wg.Wait()

	// Check if an error occurred during execution.
	if firstErr != nil {
		return nil, firstErr
	}

	// Check if the context was cancelled (e.g., parent context timeout).
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	return results, nil
}
