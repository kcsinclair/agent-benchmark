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
	// Validate input parameters
	if workers < 1 {
		return nil, ErrInvalidWorkers
	}
	if len(tasks) == 0 {
		return nil, nil
	}

	// Create a channel to signal when a worker is available.
	// The buffer size is workers to allow all workers to start immediately.
	workerAvailable := make(chan struct{}, workers)

	// Create a channel to collect results in order.
	// The buffer size is len(tasks) to hold all results without blocking.
	results := make(chan result, len(tasks))

	// Create a wait group to wait for all tasks to complete.
	var wg sync.WaitGroup

	// Create a context that can be cancelled to stop tasks.
	taskCtx, cancelTaskCtx := context.WithCancel(ctx)
	defer cancelTaskCtx() // Ensure cancellation is called on exit

	// Start worker goroutines.
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				// Wait for a signal that a worker is available.
				// This blocks until a task is ready or the context is cancelled.
				select {
				case <-workerAvailable:
					// Worker is available, process a task.
					task, index := <-tasksQueue
					// Execute the task with the task context.
					res, err := task(taskCtx)
					// Send the result to the results channel.
					results <- result{index: index, value: res, err: err}
				case <-taskCtx.Done():
					// Context cancelled, stop processing tasks.
					return
				}
			}
		}()
	}

	// Send tasks to the worker goroutines.
	for i, task := range tasks {
		// Send the task and its index to the tasksQueue channel.
		tasksQueue <- taskAndIndex{task: task, index: i}
	}

	// Wait for all tasks to complete.
	wg.Wait()

	// Close the results channel to signal that no more results will be sent.
	close(results)

	// Collect results from the results channel.
	var finalResults []any
	for res := range results {
		if res.err != nil {
			// Return the first error encountered.
			return nil, res.err
		}
		finalResults = append(finalResults, res.value)
	}

	return finalResults, nil
}

// result represents the result of a task execution.
type result struct {
	index int
	value any
	err   error
}

// taskAndIndex represents a task and its index.
type taskAndIndex struct {
	task  Task
	index int
}

// tasksQueue is a channel to send tasks to worker goroutines.
var tasksQueue = make(chan taskAndIndex)

// ErrInvalidWorkers is returned when the number of workers is less than 1.
var ErrInvalidWorkers = errors.New("invalid number of workers")
