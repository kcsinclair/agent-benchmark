select {
case <-parentCtx.Done():
    recordErr(parentCtx.Err())
    cancel()
case <-stopWatcher:
}
