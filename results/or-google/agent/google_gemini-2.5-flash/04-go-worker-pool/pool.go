package main

import (
	"context"
	"fmt"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, fmt.Errorf("workers must be at least 1, got %d", workers)
	}

	if len(tasks) == 0 {
		return []any{}, nil
	}

	results := make([]any, len(tasks))
	errChan := make(chan error, 1) // Buffer 1 to avoid blocking if an error occurs
	var wg sync.WaitGroup

	// Create a context that can be cancelled to signal tasks to stop
	taskCtx, cancelTasks := context.WithCancel(ctx)
	defer cancelTasks() // Ensure all task contexts are cancelled when Run exits

	// Semaphore to limit concurrent workers
	sem := make(chan struct{}, workers)

	for i, task := range tasks {
		select {
		case <-ctx.Done():
			// Parent context cancelled, stop starting new tasks
			return nil, ctx.Err()
		case err := <-errChan:
			// An error occurred in a previous task, stop starting new tasks
			return nil, err
		default:
			// Continue
		}

		wg.Add(1)
		go func(i int, task Task) {
			defer wg.Done()

			// Acquire a worker slot
			select {
			case <-ctx.Done():
				// Parent context cancelled while waiting for a slot
				return
			case err := <-errChan:
				// An error occurred while waiting for a slot
				// This case is important to prevent new tasks from starting if an error has already occurred
				// and the error channel has been written to.
				if err != nil {
					return
				}
			case sem <- struct{}{}:
				// Acquired a slot
			}
			defer func() { <-sem }() // Release the worker slot

			// Check for cancellation or error before running the task
			select {
			case <-taskCtx.Done():
				return // Task context cancelled, don't run
			case err := <-errChan:
				if err != nil {
					return // An error occurred, don't run
				}
			default:
				// Continue
			}

			result, err := task(taskCtx)
			if err != nil {
				select {
				case errChan <- err:
					// Successfully sent the error
				default:
					// Error channel is full, meaning another error was already sent.
					// We only care about the first error.
				}
				cancelTasks() // Cancel all running tasks
				return
			}
			results[i] = result
		}(i, task)
	}

	wg.Wait() // Wait for all started tasks to finish

	select {
	case err := <-errChan:
		return nil, err
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
		return results, nil
	}
}
