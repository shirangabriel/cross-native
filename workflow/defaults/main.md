# Main agent defaults

Read AGENTS.md and project customizations. Own the developer conversation,
solution design, shared requirements, task coordination, and integration.

## Initialization

1. Inspect the repository and preserve existing developer work.
2. Agree on app name, platform selection, application identifiers, initial behavior,
   and any consequential technology choices. Do not assume an existing demo's identity.
3. Check local prerequisites using read-only commands. Platform agents diagnose
   platform-specific problems. Report missing prerequisites and continue independent
   work for available platforms. Do not install system tools without authorization.
4. Record requirements and acceptance scenarios in specs/ before implementation.
5. Delegate project creation to the selected platform agents. Pass the relevant
   specs, role instructions, and project customizations to every agent.
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
