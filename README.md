# Cross Native

One conversation. Native apps.

An agent-agnostic starter for developing native iOS and Android apps through a
main agent and dedicated platform agents. You work with the main agent on product
decisions; platform agents create, maintain, and verify their own native apps.

This repository starts with workflow instructions. Native projects and development
commands are created for your app during initialization. No agent SDK or
orchestration runtime is bundled.

## 1. Clone the starter

Choose a directory for your app:

```sh
git clone https://github.com/shirangabriel/cross-native.git my-app
cd my-app
```

For your own project, change `origin` to your own repository before pushing:

```sh
git remote rename origin upstream
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-APP.git
```

Create that destination repository on GitHub first. Skip this remote change if
you are contributing to Cross Native itself.

## 2. Open your agent environment

Open the cloned directory in your preferred coding agent environment. Start a
conversation with the main agent and explicitly ask it to read `AGENTS.md` if your
environment does not load that file automatically.

An environment with subagent support can run platform agents in parallel. If
that capability is unavailable, the main agent supplies task briefs for separate
iOS and Android agent sessions. Return their results to the main agent for
integration. Instructions alone do not enable delegation in an unsupported tool.

## 3. Create your native projects

Send the main agent a request such as:

> Read AGENTS.md and initialize an app called My App for iOS and Android.
> Use dedicated iOS and Android agents for all platform work. Start with a Home
> screen showing Hello World, a Next button opening a second screen, and back
> navigation. Check prerequisites and record the agreed requirements before
> implementation.

Choose just iOS or Android if you only need one platform. The main agent will
agree on app identifiers and important choices with you, record them in `specs/`,
and dispatch project creation to the selected platform agents.

The default native stacks are Swift/SwiftUI for iOS and Kotlin/Jetpack Compose
for Android. Each platform agent owns its project directory and supplies the
commands needed to build and run it.

### Local prerequisites

- **iOS:** a Mac with Xcode, command-line tools, and an iOS simulator runtime.
- **Android:** an Android development toolchain, compatible Java and Android SDK,
  and an emulator or authorized physical device. Android Studio is the usual setup.
- **Initial dependency downloads:** network access.

Agents check the exact versions and additional requirements for the generated
projects. Missing system tools are reported before installation; available
platform work can proceed independently.

## 4. Build and run

After project creation, ask:

> Set up and document the verified build and run commands under tools/. Build
> both apps, launch them on available simulators or emulators, and check the
> Next and Back flow. Report build, launch, and interaction results separately.

For a single platform, ask “Run iOS” or “Run Android” instead. Tell the main agent
which simulator, emulator, or device to use if you have a preference.

The main agent coordinates the shared tools; platform agents perform platform
builds, launches, and troubleshooting. Use the exact terminal commands documented
in `tools/` after initialization. This starter does not ship a `tools/dev` command.
Physical-device setup may require additional signing or authorization.

A successful build is only the first check. Confirm that the app opens, Next
shows the second screen, and Back returns to Home. Blocked checks should remain
explicitly marked as unverified.

## 5. Make changes and reload

Continue through the main agent:

> Change the greeting on both platforms and add a counter to the second screen.
> Have each platform agent implement and verify its changes, then run both apps.

You can also target a single platform. Product behavior belongs in `specs/`;
platform agents implement it with native controls and conventions.

Ask the agent to use live updates where the generated project and tools support
them. Otherwise, use the documented rebuild/install/relaunch command. Automatic
hot reload is not provided by this template; the generated tooling must document
whether state survives an update.

## 6. Save your project

Once you have reviewed the generated apps and verification results, ask the main
agent to commit the completed work, or commit it yourself. Commit the native
projects to your app repository and maintain them there; they are not regenerated
for every feature. Commits are not automatic by default.

## Layout

```text
AGENTS.md             Agent entry point, ownership, and behavior precedence
workflow/defaults/    Main, iOS, and Android role instructions
workflow/project/     Optional developer extensions and explicit overrides
specs/                Shared product requirements and decisions
tools/                Shared scripts, added during initialization
ios/                  Created and owned by the iOS agent
android/              Created and owned by the Android agent
```

## Customize agent behavior

No customization is required to start. Add project instructions under
`workflow/project/` following its README:

- **Extensions** add conventions or checks while preserving defaults.
- **Overrides** explicitly name the default rule and its replacement.

For example, add a team lint requirement as an extension, or explicitly override
a default technology choice. Keep product requirements in `specs/` and leave
`workflow/defaults/` intact when customizing your app.
