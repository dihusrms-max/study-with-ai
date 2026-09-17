# DACON Codex Autonomous Execution Policy

## Purpose

Work continuously inside the currently approved DACON task instead of stopping after routine steps to ask
"계속할까요?", "다음으로 진행할까요?", or "구현해도 될까요?".

The user wants completion of the requested bounded task, not repeated step-by-step confirmations.

## Default execution behavior

Within the current repository and the explicitly requested task:

- Read and inspect files as needed.
- Edit project code and project documentation needed to complete the task.
- Run existing unit tests, property tests, validators, linters, and dry-runs.
- Re-run tests after ordinary fixes.
- Use existing runner/evaluator/cache/gate implementations instead of duplicating them.
- Create temporary candidate files, diagnostic outputs, reports, and cache entries inside approved project paths.
- If an ordinary implementation or test fails, diagnose it, make a safe in-scope fix, and retry.
- Continue from planning -> implementation -> test -> repair -> verification without asking for "next".
- Prefer the smallest change that satisfies the current task.
- Report progress at meaningful milestones, but do not stop merely to request permission for the next routine step.

## DACON experiment policy

For experiment tasks explicitly requested by the user:

- Preserve the current baseline, Gold labels, source dataset, and evaluation metric.
- Reuse the existing evaluator and gate as the source of truth.
- Reuse the existing Gemma runner/cache/concurrency policy unless the current task explicitly changes it.
- Treat prompt/request identity as part of experiment identity.
- Do not compare repeated runs as identical experiments when request/prompt hashes differ.
- Do not promote a candidate solely because of one best observed score.
- Failed candidates may be rejected automatically according to the already-approved gate.
- Promising candidates may advance through already-approved diagnostic stages without asking for confirmation each time.
- Stay within the API/run budget explicitly established for the current task.
- Never silently increase an API budget.

## Hard stop: ask the user before any of these

Stop and request explicit user approval before:

- Merging a candidate into the Student/main production path.
- Overwriting or replacing the accepted baseline.
- Modifying Gold labels or source competition datasets.
- Changing the definition of the evaluation metric or promotion gate.
- Running an official competition submission or sending a submission.
- Increasing an agreed API/spend/run budget.
- Changing API keys, credentials, authentication, sandbox/security policy, or secret handling.
- Deleting large datasets, experiment history, caches needed for reproducibility, or other destructive bulk deletion.
- Force-pushing, rewriting shared Git history, or merging to the shared main branch.
- Publishing/pushing changes to a remote repository unless the user explicitly asked for it.

## Git behavior

- Read-only Git inspection is routine.
- Local edits and tests are routine.
- Do not `git push`, force-push, merge to shared main, or rewrite history unless explicitly requested.
- Do not discard unrelated user/team changes.
- If the working tree already contains unrelated modifications, preserve them.

## Permission failure behavior

If an action fails because of sandbox or permission boundaries:

1. Try a safe in-workspace alternative when one exists.
2. Do not weaken the global sandbox just to make the command work.
3. Request approval only when the action is necessary to complete the explicit task.
4. Explain briefly what boundary is being crossed and why.

## Completion standard

A task is complete when the requested implementation is made, relevant tests/validation are run,
ordinary in-scope failures are repaired where feasible, and the final state/results are reported.

Do not stop after only presenting a plan when implementation was requested.
