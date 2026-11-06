# Initialization contract

Status: CLI questionnaire and launch adapters implemented in tools/init. Native
project creation and verification are performed by the launched agent session.

## Entry point

Run `./tools/init` after cloning, before starting a coding agent. Requires Python
3.9+ on macOS/Linux. The final question chooses Codex, Claude Code, or Cursor Agent.
Adapters detect the CLI on PATH and start an interactive session in the resolved
project root with a shared initialization task. No CLI installation, authentication,
or permission bypass is performed. Native subagent capabilities are checked inside
the session. Desktop and slash-command entry points are not implemented.

Answers are saved atomically in `.cross-native/project.json` (schema version 1).
Reruns validate and reuse answers; `--agent` changes the saved provider and
`--no-launch` saves without starting it. The CLI prints basic prerequisite hints;
platform agents perform authoritative checks. Requirements in specs/project.md
are produced by the main agent using saved answers before implementation.

## Questions and defaults

Ask only for missing information; reuse existing recorded answers on resume.

| Question | Default |
| --- | --- |
| App display name | Required; no assumed demo name |
| Target platforms | Offer iOS and Android, or either individually |
| Application identifier | Required reverse-domain identifier; validate for each selected platform |

New projects default to a single native screen displaying Hello World; do not ask
a starting-point question. Preserve starting_experience in previously saved
configurations when resuming. Apply default role behavior plus developer
extensions and explicit overrides. Ask about consequential choices only when
requirements or conflicting instructions leave them unresolved. Do not require
developers to configure agent internals to initialize an app.

## Execution

1. Inspect the workspace without overwriting existing projects. Resolve existing
   customizations and adapter delegation capabilities.
2. Collect missing answers and record project identity and acceptance scenarios
   in specs/project.md. This file describes the app; this contract describes the
   development toolkit.
3. Run read-only prerequisite checks. Report missing tooling and keep selected
   platforms visible even if one is blocked. Do not install system software
   without authorization.
4. Dispatch separate tasks to the selected platform agents with specifications,
   role instructions, customizations, edit boundaries, and required evidence.
   Only platform agents create or modify ios/ and android/.
5. Platform agents use reproducible generation/build tools where available and
   provide exact commands and prerequisites. The main agent integrates shared
   wrappers and documents their actual capabilities under tools/.
6. Build and launch on available simulators/emulators and verify the agreed
   interactions through the respective agents. Report each outcome separately.
7. Return generated paths, usable commands, verification evidence, and any
   blockers. Do not commit or push automatically.

Use agents for decisions, implementation, and diagnosis. Use tools for repeatable
validation, generation, builds, installation, launches, and evidence collection.

## Failure and resume

Persist confirmed requirements before dispatch. Rerunning initialization must
inspect completed work, reuse prior answers, and resume unfinished steps rather
than overwrite or regenerate a working project. Ask before replacing existing
project files. A failed platform does not erase the other platform's progress.

If delegation is unavailable, report it and supply platform task briefs for
separate sessions under AGENTS.md. Do not silently let the main agent implement
platform code or claim automatic initialization is available.

## Completion criteria

- Agreed app identity, platforms, and acceptance scenarios recorded.
- Each selected platform project created by its platform agent.
- Reproducible build/run commands documented and supplied by tooling.
- Per-platform build, launch, and interaction evidence reported.
- Missing prerequisites or unavailable checks explicitly marked as blocked or
  unverified; full initialization remains incomplete until required checks pass.

Validate the eventual implementation against fresh initialization, single-platform
selection, missing prerequisites, interrupted initialization/resume, an existing
project, and unavailable delegation. CLI handoff and persistence are covered by tools/tests/test_init.py; real agent
delegation and native app verification still require an end-to-end project trial.
