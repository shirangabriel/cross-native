# Optional project behavior

No extensions or overrides are active in this template.

Add Markdown instruction files in this directory. State their role scope
(main, ios, android, or all), then use these sections:

## Extensions

Add conventions or checks. Defaults remain in force. Example:
“Scope: android. Run our project lint command before reporting completion.”

## Overrides

Explicitly identify the default file, rule, replacement behavior, and affected
roles. Example: “Replace the default ‘no automatic commits’ rule in AGENTS.md for
the main agent with: commit completed, verified changes when requested as part
of a feature task.”

Examples above are explanatory, not active instructions. Keep requirements and
feature decisions in specs/. If customizations conflict or cannot be combined,
the main agent asks the developer to resolve the conflict before dependent work.
