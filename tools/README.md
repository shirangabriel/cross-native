# Shared development tools

Run `./tools/init` from the repository root (Python 3.9+, macOS/Linux). It collects
app details, saves `.cross-native/project.json`, and starts the chosen interactive
coding-agent CLI in the project root with the setup task.

Supported choices: Codex (`codex`), Claude Code (`claude`), Cursor Agent (`agent`).
Install/authenticate your preferred CLI separately. No permission bypass flags are
used and no credentials are collected. Subagent availability is determined inside
the launched agent session, not guaranteed by executable detection.

- `--no-launch`: save/reuse details without starting the agent.
- `--agent codex|claude|cursor`: preselect or change the agent.
- `--help`: command usage.

Reruns reuse saved answers. Errors return nonzero; interrupted input returns 130.
The agent process exit code is returned to the terminal. Saved answers are retained
when launch fails. Existing app files are not modified by the initializer.

The platform agents supply build/run commands during setup, and the main agent
coordinates their wrappers here. No native build/run command is implemented yet.
Document prerequisites, device selection, exit behavior, and actual reload support
alongside each future command.

Run tests with `python3 -m unittest discover -s tools/tests -v`.
