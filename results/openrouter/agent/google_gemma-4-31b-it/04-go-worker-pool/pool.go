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

	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Create a cancellable context to stop all tasks if one fails or parent is cancelled.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	
	// taskIdx is the index of the next task to be picked up by a worker.
	taskIdx := 0
	
	// errOnce ensures we only capture the first error that occurs.
	var errOnce sync.Once
	var firstErr error
	
	// wg ensures we wait for all started goroutines to finish before returning.
	var wg sync.WaitGroup

	// We use a channel to signal workers to start. 
	// However, a simpler approach is to have workers pull from a task queue.
	taskChan := make(chan int)

	// Start workers
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case idx, ok := <-taskChan:
					if !ok {
						return
					}
					
					// Execute the task
					res, err := tasks[idx](ctx)
					if err != nil {
						errOnce.Do(func() {
							firstErr = err
							cancel() // Cancel other tasks
						})
						return
					}
					results[idx] = res
				}
			}
		}()
	}

	// Feed tasks into the channel
	go func() {
		defer close(taskChan)
		for i := 0; i < len(tasks); i++ {
			select {
			case <-ctx.Done():
				return
			case taskChan <- i:
			}
		}
	}()

	// Wait for all workers to finish
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return results, nil
}
