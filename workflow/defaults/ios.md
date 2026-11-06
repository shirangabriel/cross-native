# iOS agent defaults

Read AGENTS.md, workflow/project/ instructions, and the assigned specifications.
Own ios/ and templates/ios/, including native configuration, implementation,
build scripts, and platform verification. Tools generate starters from the template;
preserve generated projects during feature work. Request shared-file changes through the main agent.

Use native Apple frameworks; default to Swift and SwiftUI unless explicitly
overridden. Use the agreed app identity and platform-appropriate navigation,
accessibility, and system appearance. Keep project setup reproducible.

Supply exact prerequisite, build, run, and supported reload commands to the main
agent for tools/ integration. Keep simulator and physical-device requirements clear.

For each task, report changed files, commands run, outcomes, and blockers. Verify
acceptance behavior on a simulator/device when possible; distinguish that from a
successful build. Do not claim checks you did not perform or silently change
shared behavior to solve a platform issue. Follow the Git rules in AGENTS.md.
