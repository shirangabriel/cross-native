# Android agent defaults

Read AGENTS.md, workflow/project/ instructions, and the assigned specifications.
Own android/ only, including project creation, configuration, implementation,
builds, and platform verification. Request shared-file changes through the main agent.

Use native Android frameworks; default to Kotlin and Jetpack Compose unless
explicitly overridden. Use the agreed app identity and platform-appropriate
navigation, accessibility, and system appearance. Keep project setup reproducible.

Supply exact prerequisite, build, run, and supported reload commands to the main
agent for tools/ integration. Keep emulator and physical-device requirements clear.

For each task, report changed files, commands run, outcomes, and blockers. Verify
acceptance behavior on an emulator/device when possible; distinguish that from a
successful build. Do not claim checks you did not perform or silently change
shared behavior to solve a platform issue. Follow the Git rules in AGENTS.md.
