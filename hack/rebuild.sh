#!/usr/bin/env bash

set -e

if [[ -z "${TMPDIR}" ]]; then
    TMPDIR="/tmp"
fi

if [[ -z "${BUILD_PLATFORMS}" ]]; then
    BUILD_PLATFORMS="linux windows darwin"
fi

if [[ -z "${BUILD_ARCHS}" ]]; then
    BUILD_ARCHS="amd64 arm64"
fi

for os in $BUILD_PLATFORMS; do
    for arch in $BUILD_ARCHS; do
        # don't build for arm on windows
        if [[ "$os" == "windows" && "$arch" == "arm64" ]]; then
            continue
        fi
        echo "[INFO] Building for $os/$arch"
        if [[ $RACE == "yes" ]]; then
            echo "Building kled with race detector"
            CGO_ENABLED=1 GOOS=$os GOARCH=$arch go build -race -ldflags "-s -w" -o test/kled-cli-$os-$arch
        else
            CGO_ENABLED=0 GOOS=$os GOARCH=$arch go build -ldflags "-s -w" -o test/kled-cli-$os-$arch
        fi
    done
done
echo "[INFO] Built binaries for all platforms in test/ directory"

if [[ -z "${SKIP_INSTALL}" ]]; then
    if command -v sudo &> /dev/null; then
        go build -o test/kled && sudo mv test/kled /usr/local/bin/
    else
        go install .
    fi
fi
echo "[INFO] Built kled binary and moved to /usr/local/bin"

if [[ $BUILD_PLATFORMS == *"linux"* ]]; then
    cp test/kled-cli-linux-amd64 test/kled-linux-amd64
    if [ -f "test/kled-cli-linux-arm64" ]; then
        cp test/kled-cli-linux-arm64 test/kled-linux-arm64
    fi
fi

if [ -d "desktop/src-tauri/bin" ]; then
    if [[ $BUILD_PLATFORMS == *"linux"* ]]; then
        cp test/kled-cli-linux-amd64 desktop/src-tauri/bin/kled-cli-x86_64-unknown-linux-gnu
        if [ -f "test/kled-cli-linux-arm64" ]; then
            cp test/kled-cli-linux-arm64 desktop/src-tauri/bin/kled-cli-aarch64-unknown-linux-gnu
        fi
    fi
    if [[ $BUILD_PLATFORMS == *"windows"* ]]; then
        cp test/kled-cli-windows-amd64 desktop/src-tauri/bin/kled-cli-x86_64-pc-windows-msvc.exe
    fi
    if [[ $BUILD_PLATFORMS == *"darwin"* ]]; then
        cp test/kled-cli-darwin-amd64 desktop/src-tauri/bin/kled-cli-x86_64-apple-darwin
        cp test/kled-cli-darwin-arm64 desktop/src-tauri/bin/kled-cli-aarch64-apple-darwin
    fi
echo "[INFO] Copied binaries to desktop/src-tauri/bin"
fi

if [[ $BUILD_PLATFORMS == *"linux"* ]]; then
    rm -R $TMPDIR/kled-cache 2>/dev/null || true
    mkdir -p $TMPDIR/kled-cache
    cp test/kled-cli-linux-amd64 $TMPDIR/kled-cache/kled-linux-amd64
    if [ -f "test/kled-cli-linux-arm64" ]; then
        cp test/kled-cli-linux-arm64 $TMPDIR/kled-cache/kled-linux-arm64
    fi
    echo "[INFO] Copied binaries to $TMPDIR/kled-cache"
fi
