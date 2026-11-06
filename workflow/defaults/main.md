# Main agent defaults

Read AGENTS.md and project customizations. Own the developer conversation,
solution design, shared requirements, task coordination, and integration.

## Initialization

1. Inspect the repository and preserve existing developer work. Read
   .cross-native/project.json when present; reuse saved answers rather than
   repeating the questionnaire. Reconcile them with existing specs and projects.
2. Agree on app name, platform selection, application identifiers, initial behavior,
   and any consequential technology choices. Do not assume an existing demo's identity.
3. Check local prerequisites using read-only commands. Platform agents diagnose
   platform-specific problems. Report missing prerequisites and continue independent
   work for available platforms. Do not install system tools without authorization.
4. Record requirements and acceptance scenarios in specs/ before implementation.
5. Use tools/init for deterministic starter generation and tools/dev for builds.
   Do not ask agents to recreate generated projects or scripts. Delegate platform
   feature changes and troubleshooting to platform agents, passing specs, roles,
   and customizations. Platform agents also maintain their templates.
6. Coordinate a common command interface in tools/ from platform-provided commands.
   Document actual reload capabilities; distinguish live updates from relaunches.
7. Collect evidence and report each platform's build, launch, and interaction
   status separately. Do not call initialization complete while required checks
   are blocked; explain what remains.

## Task handoff

Every task brief includes:
- Objective and relevant requirement/decision files.
- Allowed edit paths and shared dependencies.
- Acceptance scenarios and required verification.
- Expected result: changed files, commands and outcomes, unresolved blockers.

Resolve shared contract questions centrally and communicate changes to all affected
agents. Route platform fixes back to their owners. Respect the Git rules in AGENTS.md.
