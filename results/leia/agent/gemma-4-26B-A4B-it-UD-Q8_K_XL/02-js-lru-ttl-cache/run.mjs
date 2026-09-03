import { LruTtlCache } from './cache.mjs';
import assert from 'node:assert';

// Run the test file
import('./test.mjs').then(() => {
  console.log("Test execution finished.");
}).catch(err => {
  console.error("Test execution failed.");
  console.error(err);
  process.exit(1);
});
