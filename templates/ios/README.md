# iOS starter

This is the versioned Cross Native iOS template. Generation substitutes
`__APP_ID__` in the project and `__APP_NAME_XML__` in the display-name plist.
The display name must be XML escaped; application identifiers must be validated
before substitution. Project, scheme, executable, and Swift type names remain
`CrossNative` regardless of the user-facing app name.

The starter has exactly one native screen: `Hello World` centered in its safe
content area, using SwiftUI's scalable title3 style (20 points at default text
size), system foreground/background, and no title, buttons, or navigation.
Platform font rendering and system chrome can differ from Android.

## Build

On macOS with a full Xcode installation selected:

```sh
./build.sh
```

This runs `xcodebuild` against the checked-in shared `CrossNative` scheme for a
generic iOS Simulator destination, Debug configuration, and signing disabled.
Artifacts are kept under `build/`; the app is
`build/Build/Products/Debug-iphonesimulator/CrossNative.app`.
There are no external package dependencies or runtime project-generator tools.

The checked-in Xcode project was initially produced with XcodeGen and then
reviewed as a template; consumers do not need XcodeGen. Deployment target is
iOS 17.0, Swift language mode is 5.0, and Xcode project object version is 77.
Template verification uses Xcode 27.2 (27B52); other toolchain versions are not
verified by this milestone. Physical-device signing and App Store assets are outside this simulator template.


## Run on a simulator

After building, run `python3 run.py`. Use `--device <UDID>` (or `IOS_DEVICE`) to
select a simulator explicitly; a unique simulator name is accepted, but duplicate
names require a UDID. With no selection, prefer a booted available iOS simulator,
then choose deterministically by name/runtime/UDID. Every native command uses the
same selected UDID; shutdown simulators are booted before installation.

The launcher reads the built app's Info.plist and checks it against generated
identity metadata, then installs, terminates any prior instance, launches, and
captures a screenshot. It opens Device Hub or Simulator from the selected Xcode
installation, respecting DEVELOPER_DIR; no app-name registration is required.

Evidence lives in `build/evidence/launch.json` and `screenshot.png`. The report
includes timestamps, exact device/runtime, app identifier, PID, and command
outputs. Each attempt clears the previous screenshot and replaces the report
with current status; failures never leave an old success as the latest report.
A captured screenshot does not automatically prove Hello World text, foreground
app identity, visual parity, or interaction correctness: those remain unverified
until the evidence is inspected. No OCR or UI test runner is bundled.

The run script does not build or hot reload. Rebuild before running changed code.
The parent build command targets a generic simulator artifact suitable for the
selected device architecture; installation/launch uses only the resolved UDID.

Mocked launch tests: `python3 -m unittest discover -s tests -v`.
A real launch attempt in the restricted authoring session failed while listing
simulators because CoreSimulator service access was denied. It correctly wrote
failure evidence; simulator launch and screenshot capture remain unverified there.
