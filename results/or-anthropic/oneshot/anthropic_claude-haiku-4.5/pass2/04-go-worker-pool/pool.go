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
	// Validation: workers must be at least 1
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	// Edge case: no tasks
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Create a cancellable context for task execution
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	// Results slice to maintain order
	results := make([]any, len(tasks))

	// Channel to send task indices to workers
	taskChan := make(chan int, workers)

	// WaitGroup to track all worker goroutines
	var wg sync.WaitGroup

	// Mutex to protect error state
	var mu sync.Mutex
	var firstErr error

	// Start worker goroutines
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for taskIdx := range taskChan {
				// Check if we've already encountered an error
				mu.Lock()
				if firstErr != nil {
					mu.Unlock()
					continue
				}
				mu.Unlock()

				// Execute the task
				result, err := tasks[taskIdx](taskCtx)

				mu.Lock()
				if err != nil && firstErr == nil {
					// First error encountered
					firstErr = err
					cancel() // Cancel remaining tasks
				} else if firstErr == nil {
					// No error yet, store result
					results[taskIdx] = result
				}
				mu.Unlock()
			}
		}()
	}

	// Goroutine to feed tasks to workers
	go func() {
		for i := 0; i < len(tasks); i++ {
			// Check if context is cancelled or if we've hit an error
			select {
			case <-taskCtx.Done():
				close(taskChan)
				return
			default:
			}

			mu.Lock()
			if firstErr != nil {
				mu.Unlock()
				close(taskChan)
				return
			}
			mu.Unlock()

			select {
			case taskChan <- i:
			case <-taskCtx.Done():
				close(taskChan)
				return
			}
		}
		close(taskChan)
	}()

	// Wait for all workers to finish
	wg.Wait()

	// Check for errors
	mu.Lock()
	if firstErr != nil {
		mu.Unlock()
		return nil, firstErr
	}
	mu.Unlock()

	// Check if context was cancelled
	if err := taskCtx.Err(); err != nil {
		return nil, err
	}

	return results, nil
}
