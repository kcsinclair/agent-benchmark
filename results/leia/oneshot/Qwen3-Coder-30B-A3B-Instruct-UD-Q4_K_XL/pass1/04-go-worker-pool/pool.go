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
		return nil, &workerError{msg: "workers must be >= 1"}
	}
	
	if len(tasks) == 0 {
		return []any{}, nil
	}
	
	// Create a context that can be cancelled to stop new tasks
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	
	// Channels for communication
	taskChan := make(chan taskWithIndex, len(tasks))
	resultChan := make(chan resultWithIndex, len(tasks))
	
	// Start workers
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case taskInfo, ok := <-taskChan:
					if !ok {
						return
					}
					result, err := taskInfo.task(ctx)
					select {
					case resultChan <- resultWithIndex{index: taskInfo.index, result: result, err: err}:
					case <-ctx.Done():
						return
					}
				}
			}
		}()
	}
	
	// Send tasks to the channel
	go func() {
		defer close(taskChan)
		for i, task := range tasks {
			select {
			case taskChan <- taskWithIndex{index: i, task: task}:
			case <-ctx.Done():
				return
			}
		}
	}()
	
	// Collect results
	results := make([]any, len(tasks))
	var firstErr error
	
	for i := 0; i < len(tasks); i++ {
		select {
		case resultInfo := <-resultChan:
			if resultInfo.err != nil {
				if firstErr == nil {
					firstErr = resultInfo.err
				}
				cancel() // Cancel remaining tasks
			} else {
				results[resultInfo.index] = resultInfo.result
			}
		case <-ctx.Done():
			firstErr = ctx.Err()
			cancel() // Ensure cancellation
		}
	}
	
	// Wait for all workers to finish
	cancel()
	wg.Wait()
	
	if firstErr != nil {
		return nil, firstErr
	}
	
	return results, nil
}

// Helper types
type taskWithIndex struct {
	index int
	task  Task
}

type resultWithIndex struct {
	index int
	result any
	err   error
}

// Custom error type for validation
type workerError struct {
	msg string
}

func (e *workerError) Error() string {
	return e.msg
}
