# Cross Native

An agent-agnostic starter for developing native iOS and Android apps through a
main agent and dedicated platform agents. Product decisions are shared; each
platform agent owns its native implementation.

This template contains instructions only. There are no app projects, pinned app
names, installed dependencies, development commands, or orchestration runtime yet.

## Start a project

1. Clone this repository and open it in your preferred agent environment.
2. Direct your main agent to read AGENTS.md. If your environment does not load
   that file automatically, include it in the initial prompt explicitly.
3. Ask: “Initialize an app named <name> for <iOS, Android, or both>. Follow AGENTS.md
   and delegate platform work to the respective agents.”
4. Agree on application identifiers, initial behavior, and platform choices with
   the main agent. It records these decisions in specs/ and checks prerequisites.
5. Platform agents create and verify their projects. The main agent coordinates
   tools/ commands and reports what built, what ran, and what remains blocked.

Use an environment with delegation to run platform agents in parallel. Otherwise,
use separate platform-agent sessions with the briefs supplied by the main agent.
This repository does not make delegation available in an unsupported environment.

## Layout

```text
AGENTS.md             Entry point, ownership, behavior precedence
workflow/defaults/    Main, iOS, and Android role instructions
workflow/project/     Optional developer extensions and explicit overrides
specs/                Shared product requirements and decisions
tools/               Shared scripts, added during initialization
ios/                 Created and owned by the iOS agent
android/             Created and owned by the Android agent
```

## Customize behavior

Defaults work without customization. Add project instructions under
workflow/project/ using its documented extension/override format. Keep product
requirements in specs/. No particular model, provider, or agent SDK is required.
