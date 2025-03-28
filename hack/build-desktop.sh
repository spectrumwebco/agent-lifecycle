
set -e

DESKTOP_DIR="$(realpath $(dirname $0)/../desktop)"

if [[ -z "${SKIP_INSTALL}" ]]; then
    echo "Installing dependencies..."
    cd "${DESKTOP_DIR}" && yarn install
fi

echo "Building SpacetimeDB server..."
cd "${DESKTOP_DIR}/src-tauri/server" && cargo build --release

if [[ -z "${BUILD_PLATFORMS}" ]]; then
    BUILD_PLATFORMS="darwin windows linux"
fi

for platform in ${BUILD_PLATFORMS}; do
    case "${platform}" in
        darwin)
            echo "Building for macOS (universal)..."
            cd "${DESKTOP_DIR}" && yarn tauri build --target universal-apple-darwin
            ;;
        windows)
            echo "Building for Windows..."
            cd "${DESKTOP_DIR}" && yarn tauri build --target x86_64-pc-windows-msvc
            ;;
        linux)
            echo "Building for Linux (x86_64)..."
            cd "${DESKTOP_DIR}" && yarn tauri build --target x86_64-unknown-linux-gnu
            
            echo "Building for Linux (aarch64)..."
            cd "${DESKTOP_DIR}" && yarn tauri build --target aarch64-unknown-linux-gnu
            ;;
    esac
done

echo "Desktop builds completed successfully!"
