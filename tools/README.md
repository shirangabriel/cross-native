# Development tools

Python 3.9+, macOS/Linux. No Python packages or AI calls are needed for generation.

## Initialize

`./tools/init` collects name, platforms, and application identifier with numbered
choices. It saves `.cross-native/project.json`, copies the selected templates into
`ios/` and/or `android/`, substitutes validated identity values, then builds and launches on simulators/emulators.
On success it offers an optional agent CLI session in the resolved project root.
Enter accepts defaults; option names are also accepted.

- `--no-launch`: generate/build/run without selecting or launching an AI agent.
- `--skip-build`: generate without building or launching apps, useful offline.
- `--skip-run`: build without launching apps.
- `--ios-device` / `--android-device`: explicit device selection (also accepted by tools/dev).
- `--agent codex|claude|cursor`: select/change the agent for the final handoff.

Generated directories have a `.cross-native-template.json` identity marker.
Reruns preserve files byte-for-byte. Existing unmarked directories or changed
identity values stop generation rather than overwrite work. Each platform is
staged before publication; after interruption rerun to generate missing platforms.
Existing custom starting_experience values are retained for compatibility but do
not alter the deterministic starter; discuss custom behavior with the agent later.

Agent executables: `codex`, `claude`, `agent` (Cursor). Install and sign in separately.
CLI trust/permission settings remain unchanged. The main agent handles feature
work and delegates platform changes; it must not regenerate the starter. CLI
availability does not establish subagent capability. Desktop adapters are not included.

## Build and inspect

```sh
./tools/dev doctor
./tools/dev doctor ios
./tools/dev build ios
./tools/dev build android
./tools/dev build all
./tools/dev run ios
./tools/dev run android
./tools/dev run all
./tools/dev run ios --ios-device SIMULATOR_UDID
./tools/dev run android --android-device SERIAL_OR_AVD
```

Doctor checks presence, not full compatibility. Builds run the platform-maintained
`build.sh` scripts; detailed logs go to `.build/logs/<platform>-build.log`.
`all` uses configured platforms (both if no configuration exists), attempts each,
and fails if any fails. Build/launch failures block automatic agent
handoff; configuration and generated projects remain available for retry.
Exit codes: 0 success, 1 setup/build failure, 130 interrupted input; an agent's
exit status is propagated. Toolchain setup is never installed automatically.

Template READMEs document pinned versions, native prerequisites, and artifacts.
`run` rebuilds before running the platform-owned `run.py`. Run logs go to
`.build/logs/<platform>-run.log`. Each runner selects an explicit device for install,
launch, and evidence. See template READMEs for selection and timeout rules.
Screenshots and launch metadata live under `<platform>/build/evidence/`. A screenshot
alone does not prove Hello World is visible; consult the recorded verification
status and manually inspect captures when automated UI checks are unavailable.
Physical iOS devices are not supported. Existing generated projects without run.py
are preserved and receive an actionable error rather than an automatic overwrite.

Reload is rebuild/install/relaunch. No automatic hot reload or state-preservation
guarantee is provided.

## Tests

`python3 -m unittest discover -s tools/tests -v`

Process tests use temporary projects and fake agents/build scripts without model
calls. Generation tests exercise the shipped templates. Real native build evidence
is separate, recorded by the platform agents; Android downloads may be blocked by
the execution environment.

Platform runner tests: `python3 -m unittest discover -s templates/ios/tests -v`
and `python3 -m unittest discover -s templates/android/tests -v`.
