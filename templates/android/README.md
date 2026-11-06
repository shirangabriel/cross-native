# Android starter

Generated from Cross Native's versioned template. One centered `Hello World`
label at 20sp, in a single activity, using system light/dark appearance and safe
content insets. No title, buttons, or navigation are added.

## Build

```sh
./build.sh
```

Requires Java 17, Android SDK platform 35 and build tools 35.0.0, plus network
access for first-time Gradle and Maven downloads. The build script honors
JAVA_HOME, ANDROID_HOME / ANDROID_SDK_ROOT, and GRADLE_USER_HOME. On macOS it can
use Android Studio's bundled JDK if JAVA_HOME is absent; it discovers the usual
macOS/Linux SDK directories. It does not install or update system software.

Gradle caches default to `../.build/gradle` so files remain in the app repository.
Set GRADLE_USER_HOME explicitly to reuse an existing cache. The APK is written to
`app/build/outputs/apk/debug/app-debug.apk`. Arguments after `./build.sh` are passed
to Gradle (for example, `--offline` for a fully cached toolchain).

## Pinned baseline

- Android Gradle Plugin 8.7.3; Gradle 8.11.1.
- Kotlin and Compose compiler plugin 2.0.21.
- Compose BOM 2024.10.01; Activity Compose 1.9.3.
- Compile/target SDK 35; minimum SDK 26; Java bytecode target 17.

This is a reproducible starter baseline, not a claim that these are the newest
versions or sufficient for future store submission rules. Toolchain upgrades
should be tested in the template before adoption by new apps.
[Android's AGP compatibility notes](https://developer.android.com/build/releases/agp-8-7-0-release-notes)
document the API 35 toolchain family.

Namespace and Kotlin package remain `dev.crossnative.app`; the application's
installation identifier comes from generated Gradle configuration. Changing the
identifier does not require renaming source directories.

## Verification and provenance

Gradle wrapper scripts and JAR were reused from the locally installed standard
Gradle wrapper in an existing project. Scripts retain their Apache 2.0 header.
Wrapper JAR SHA-256:
`b3a875ddc1f044746e1b1a55f645584505f4a10438c1afea9f15e92a7c42ec13`.

Template generation and build invocation were exercised in a temporary project.
The restricted authoring session could not resolve services.gradle.org. With a
locally cached Gradle distribution, Gradle started but the sandbox denied its
local daemon socket. Compilation and emulator rendering remain unverified in
that session. Device launch is implemented below; real launch remains unverified
in the restricted authoring session because ADB could not bind its daemon socket.


## Install and launch

After building the generated project:

```sh
python3 run.py
python3 run.py --device emulator-5554
python3 run.py --device Pixel_9
```

The launcher discovers adb/emulator from ANDROID_HOME or ANDROID_SDK_ROOT, standard
SDK locations, or PATH. It automatically selects a single running emulator. Multiple
running emulators require a serial. When none is running, a single installed AVD
can be started automatically; otherwise choose an AVD by name. New emulator boot
is pinned to an available port and awaited with a bounded timeout (default 180s).
Boot-property queries retry transient ADB timeouts/offline responses within that
deadline; each query is capped at 10 seconds or the remaining time. Timed-out
commands are retained in launch evidence. An exhausted deadline fails with the
selected serial and recovery guidance; no global ADB restart is performed.
Physical devices require an explicit serial via --device or ANDROID_SERIAL and
must already be authorized. Every install, launch, and capture targets the same serial.

`run.py` does not build. It installs the existing APK, force-stops the app, launches
its explicit activity, checks launch status and foreground package, then captures
`build/evidence/screenshot.png`, `ui.xml`, and `launch.json`. The JSON records UTC
time, target identity, command results, launch status, and whether an exact Hello
World node from the app package was found. That text check does not establish
layout, font size, full screen parity, or feature interaction correctness. Missing
Hello World is reported as unverified text, not a failed launch; failure to install,
launch, focus, or capture evidence returns nonzero. Old evidence is cleared at the
start of every attempt so a failure cannot leave an old successful report.

Run focused tests with `python3 -m unittest discover -s tests -v` from this folder.
These use mocks; no emulator or model session is started. Hot reload is not
implemented: rebuild, install, and relaunch resets the app process.

Foreground verification reads the full window dump and matches both application
ID and activity class exactly. If window focus fields are unavailable, it checks
the top resumed activity; another focused window or a lock screen is not treated
as success. `launch.json` records which source verified foreground identity.

Activity launch uses one `am start -W` request with up to 30 seconds for its
response, then requires exact foreground package/activity evidence within a
shared 60-second readiness budget. If the wait command times out, the runner
checks the device instead of resending the launch intent or assuming success.
Foreground queries retry transient timeouts, capped to the remaining budget;
explicit activity-start errors still fail immediately. A persistently stalled
emulator fails with recovery guidance and command evidence in launch.json.
