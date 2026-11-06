# Cross Native

One conversation. Native apps.

Build native iOS and Android apps with a main agent coordinating dedicated
platform agents. Agents handle decisions and implementation; tools handle
repeatable tasks.

## Quick start

Requires Python 3.9+ and an installed, authenticated coding-agent CLI:
**Codex**, **Claude Code**, or **Cursor Agent**.

```sh
git clone https://github.com/shirangabriel/cross-native.git my-app
cd my-app
./tools/init
```

Answer questions about your app name, platforms, and application identifier.
New projects start with a single native screen displaying Hello World.
Choose an agent; Cross Native saves your answers and launches it in the project
directory to coordinate native setup. Delegation depends on your agent environment.

```sh
./tools/init --no-launch       # Save answers without launching
./tools/init --agent claude    # Resume setup with a different agent
```

Native projects and build/run commands are created during agent-led setup.
iOS requires macOS and Xcode; Android requires Java and Android SDK tooling.
Point `origin` at your own repository before pushing your app.

## Documentation

- [Agent roles and ownership](AGENTS.md)
- [Initialization workflow](workflow/init.md)
- [Tools and tests](tools/README.md)
- [Project customization](workflow/project/README.md)
- [Product specifications](specs/README.md)
