package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	// Validation
	if workers < 1 {
		return nil, &workerError{msg: "workers must be at least 1"}
	}
	
	if len(tasks) == 0 {
		return []any{}, nil
	}
	
	// Create a context that we can cancel to stop new tasks
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	
	// Channel to receive results
	results := make(chan result, len(tasks))
	
	// Worker pool
	var wg sync.WaitGroup
	taskChan := make(chan int, len(tasks)) // Channel to send task indices
	
	// Send all task indices to the task channel
	for i := range tasks {
		taskChan <- i
	}
	close(taskChan)
	
	// Start workers
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case taskIndex, ok := <-taskChan:
					if !ok {
						// No more tasks
						return
					}
					
					// Run the task
					task := tasks[taskIndex]
					result, err := task(ctx)
					
					// Send result back
					select {
					case results <- result{index: taskIndex, value: result, err: err}:
					case <-ctx.Done():
						// Context cancelled, but we still need to send the result
						// to avoid blocking
						return
					}
				}
			}
		}()
	}
	
	// Close results channel when all workers are done
	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Collect results in order
	finalResults := make([]any, len(tasks))
	for i := 0; i < len(tasks); i++ {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case res, ok := <-results:
			if !ok {
				// Channel closed, but we should have received all results
				return nil, &resultError{msg: "results channel closed unexpectedly"}
			}
			if res.err != nil {
				// Cancel remaining tasks and return the error
				cancel()
				// Wait for all workers to finish
				wg.Wait()
				return nil, res.err
			}
			finalResults[res.index] = res.value
		}
	}
	
	// Wait for all workers to finish
	wg.Wait()
	
	return finalResults, nil
}

// Helper types
type result struct {
	index int
	value any
	err   error
}

type workerError struct {
	msg string
}

func (e *workerError) Error() string {
	return e.msg
}

type resultError struct {
	msg string
}

func (e *resultError) Error() string {
	return e.msg
}
