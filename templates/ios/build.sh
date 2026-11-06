#!/bin/sh
# Compile the checked-in project without signing or project-generation dependencies.
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec xcodebuild \
    -project "$PROJECT_DIR/CrossNative.xcodeproj" \
    -scheme CrossNative \
    -configuration Debug \
    -sdk iphonesimulator \
    -destination 'generic/platform=iOS Simulator' \
    -derivedDataPath "$PROJECT_DIR/build" \
    CODE_SIGNING_ALLOWED=NO \
    build
