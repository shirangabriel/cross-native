# Cross Native agent entry point

Read README.md, workflow/defaults/main.md, and workflow/project/README.md before acting.
For platform tasks, the assigned agent must also read its role in workflow/defaults/.

## Behavior layers

1. Defaults in workflow/defaults/ apply without project customization.
2. Extensions in workflow/project/ add instructions to those defaults.
3. Overrides in workflow/project/ explicitly identify the default rule they replace.

Read developer-provided instruction files in workflow/project/ before dispatching or executing tasks.
Do not edit defaults merely to customize a project. Do not interpret an extension
as an override. Surface ambiguous conflicts to the developer before dependent work.
Direct developer instructions take precedence over repository defaults. These files
cannot override the host agent environment's higher-priority instructions.

## Ownership (default)

- Main agent: developer communication, specs/, workflow/, tools/, root files, integration.
- iOS agent: all implementation, configuration, build, and verification within ios/.
- Android agent: all implementation, configuration, build, and verification within android/.

Only the respective platform agent creates or edits a platform project. The main
agent routes platform failures back to that agent; it does not take over the work.
Platform agents request shared-file changes through the main agent.

## Execution and Git (default)

Use the host environment's native delegation when available. Role files describe
behavior; they do not install or implement an agent runtime. If delegation is
unavailable, explain the limitation and provide a task brief for a separate agent
session. Wait for that session's result before dependent work; do not silently
implement platform code as the main agent.

Agents may work concurrently within their owned directories. The main agent
serializes Git staging and commits, staging explicit paths only. Never switch
branches, stash, reset, or stage all changes in a shared checkout. Follow the
developer's commit policy; no automatic commits by default. Suggested prefixes:
feat(ios), feat(android), chore(tools), docs(specs).
