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
	taskChan := make(chan taskWithIndex, len(tasks))
	var wg sync.WaitGroup

	// Create a cancellable context for tasks
	taskCtx, cancelTasks := context.WithCancel(ctx)
	defer cancelTasks() // Ensure all task contexts are cancelled when Run exits

	// Start worker goroutines
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for task := range taskChan {
				select {
				case <-taskCtx.Done():
					// If the task context is cancelled, stop processing new tasks
					// and return. The main goroutine will handle the error.
					return
				default:
					// Execute the task
					result, err := task.fn(taskCtx)
					if err != nil {
						// If an error occurs, try to send it to errChan.
						// If errChan is already closed or has an error, this send will block
						// or panic if not handled. We only want the first error.
						select {
						case errChan <- err:
							// Successfully sent the first error.
							// Cancel all other tasks.
							cancelTasks()
						default:
							// Another error was already sent, or errChan is full.
							// Do nothing, we only care about the first error.
						}
						return // Stop processing tasks for this worker
					}
					results[task.index] = result
				}
			}
		}()
	}

	// Send tasks to workers
	go func() {
		for i, task := range tasks {
			select {
			case <-taskCtx.Done():
				// If the task context is cancelled (due to parent ctx or an error),
				// stop sending new tasks.
				return
			default:
				taskChan <- taskWithIndex{fn: task, index: i}
			}
		}
		close(taskChan) // No more tasks to send
	}()

	// Wait for all workers to finish
	wg.Wait()

	// Check for context cancellation from the parent
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// Check for any task errors
	select {
	case err := <-errChan:
		return nil, err
	default:
		// No error received
	}

	return results, nil
}

// taskWithIndex bundles a Task with its original index to maintain order.
type taskWithIndex struct {
	fn    Task
	index int
}
