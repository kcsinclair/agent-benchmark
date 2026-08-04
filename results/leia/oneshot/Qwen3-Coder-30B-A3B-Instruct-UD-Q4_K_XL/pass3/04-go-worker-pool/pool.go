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
	if workers < 1 {
		return nil, &invalidWorkerCountError{}
	}
	
	if len(tasks) == 0 {
		return []any{}, nil
	}
	
	// Use a channel to limit concurrency
	sem := make(chan struct{}, workers)
	
	// Use a channel to collect results in order
	results := make([]any, len(tasks))
	errChan := make(chan error, 1)
	
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstErr error
	
	// Start a goroutine to handle context cancellation
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	
	go func() {
		<-ctx.Done()
		cancel()
	}()
	
	for i, task := range tasks {
		wg.Add(1)
		
		go func(index int, t Task) {
			defer wg.Done()
			
			// Wait for a worker slot
			select {
			case sem <- struct{}{}:
			case <-ctx.Done():
				return
			}
			
			// Run the task
			taskCtx, taskCancel := context.WithCancel(ctx)
			defer taskCancel()
			
			result, err := t(taskCtx)
			
			// Put the slot back
			<-sem
			
			if err != nil {
				mu.Lock()
				if firstErr == nil {
					firstErr = err
					taskCancel()
				}
				mu.Unlock()
				select {
				case errChan <- err:
				default:
				}
				return
			}
			
			mu.Lock()
			results[index] = result
			mu.Unlock()
		}(i, task)
	}
	
	// Wait for all tasks to complete
	wg.Wait()
	
	// Check for errors
	select {
	case err := <-errChan:
		return nil, err
	default:
	}
	
	return results, firstErr
}

type invalidWorkerCountError struct{}

func (e *invalidWorkerCountError) Error() string {
	return "invalid worker count"
}
