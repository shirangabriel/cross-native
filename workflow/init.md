# Initialization contract

## Tooling first

`./tools/init` is a Python 3.9+ macOS/Linux entry point, run before a coding agent.
It asks for app name, selected platforms, and application identifier. Choices use
numbers with Enter for defaults. There is no starting-experience question.

Save answers atomically to `.cross-native/project.json` (version 1). Generate from
versioned templates without model calls. Both platforms must show exactly one
centered Hello World label, scalable 20pt/sp text and system colors, no app title,
buttons, or navigation. Platform fonts and system bars may differ.

Templates live in templates/ios and templates/android, maintained by their platform
agents. Fixed internal target/namespace names avoid fragile source renaming;
application identifiers and display names come from validated configuration.

Stage each generated directory before publication. Reruns preserve existing marked
projects, reject identity changes, and refuse to overwrite unmarked directories.
Resume missing platforms after interruptions; do not regenerate working apps.

## Build and launch

After generation, inspect prerequisites and run the selected native build scripts,
then platform-owned run.py scripts. Build/install/launch each selected platform
independently and keep device selection explicit through capture and evidence.
Persist full build logs under .build/logs/ and report concise success/failure.
Do not install toolchains automatically. Keep projects and answers when builds or launches
fail, attempt independent selected platforms, and return nonzero on any failure.
`--skip-build` permits offline generation and skips launch too; it supplies no
build evidence. `--skip-run` builds without launching. `--no-launch` skips only
the AI agent handoff, not native app launch.

After successful builds and launches (or explicit skips), offer an optional coding-agent CLI handoff. `--no-launch`
finishes without an agent; `--agent` preselects one. Support Codex, Claude Code,
and Cursor Agent using argument lists and an explicit project working directory.
Preserve CLI permission/authentication settings. Missing executables produce
instructions and retain saved state. Existing agent selections are reused.

## Agent responsibilities

The launched main agent reads roles, project customizations, configuration, and
build logs. It records/reconciles specs/project.md for subsequent feature work.
It preserves generated apps and delegates platform changes/troubleshooting to
their respective agents. If delegation is unavailable, supply separate-session
briefs rather than silently implementing platform code as the main agent.
Extensions/overrides guide feature work; they do not change the shipped generator.
Changes to the starter require a deliberate template/tooling change.

## Evidence and reload

Record the selected device identity, application identifier, time, launch outcome,
and screenshot under each platform's build/evidence. Invalidate stale success
metadata before a launch attempt. Treat screenshot capture, automated UI checks,
and visual/interaction acceptance as separate claims. A process launch does not
prove the expected screen is visible. Physical iOS deployment is outside scope.

`tools/dev run ios|android|all` rebuilds, installs, and relaunches. No live/hot reload
or navigation-state preservation is promised. End-to-end parity requires checking
both captures against the shared starter contract.

## Validation

Exercise fresh and single-platform generation, valid identity substitution,
paths with spaces, missing prerequisites, interrupted resume, existing files,
failed builds, and optional agent handoff. Real native builds are separate from
mocked process tests. Runtime parity still requires device evidence in the next milestone.
