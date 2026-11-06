# Cross Native

One conversation. Native apps.

Create native iOS and Android starters from reusable templates, then develop
through a main agent and dedicated platform agents. Tools handle setup and builds;
agents handle product decisions and implementation.

## Quick start

Requires Python 3.9+. iOS builds require macOS and Xcode; Android builds require
Java and Android SDK tooling. Initial dependency downloads need network access.

```sh
git clone https://github.com/shirangabriel/cross-native.git my-app
cd my-app
./tools/init
```

Enter your app name, platforms, and application identifier. Cross Native generates
one centered Hello World screen per platform, builds, and launches without AI. After success,
optionally start an installed, authenticated Codex, Claude Code, or Cursor Agent CLI.

```sh
./tools/init --no-launch       # Generate, build, and run without an agent
./tools/init --skip-build      # Generate only; skip native builds
./tools/dev doctor            # Check tool presence
./tools/dev run all           # Rebuild and launch selected platforms
./tools/dev run ios           # Run one platform
```

Reruns preserve generated projects. Use `--skip-run` for build-only initialization.
Device evidence is saved under each platform’s `build/evidence/`. Point `origin` at your own repository before pushing your app.

## Documentation

- [Agent roles and ownership](AGENTS.md)
- [Initialization workflow](workflow/init.md)
- [Tools and tests](tools/README.md)
- [Project customization](workflow/project/README.md)
