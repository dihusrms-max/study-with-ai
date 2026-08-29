import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

const sourceDirectory = resolve('js');

function collectJavaScriptFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name);

    if (entry.isDirectory()) {
      return collectJavaScriptFiles(path);
    }

    return entry.isFile() && entry.name.endsWith('.js') ? [path] : [];
  });
}

const files = collectJavaScriptFiles(sourceDirectory);
let hasFailure = false;

for (const file of files) {
  const result = spawnSync(process.execPath, ['--check', file], {
    stdio: 'inherit'
  });
  hasFailure ||= result.status !== 0;
}

if (hasFailure) {
  process.exitCode = 1;
} else {
  console.log(`JavaScript syntax check passed for ${files.length} file(s).`);
}
