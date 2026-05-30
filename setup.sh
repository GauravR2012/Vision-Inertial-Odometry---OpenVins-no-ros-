#!/usr/bin/env bash
# =============================================================================
# setup.sh — Clone OpenVINS, apply trajectory-export patch, and build
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENVINS_DIR="$REPO_ROOT/open_vins"
BUILD_DIR="$OPENVINS_DIR/ov_msckf/build"
PATCH_FILE="$REPO_ROOT/patches/run_simulation.patch"
CONFIG_SRC="$REPO_ROOT/config/estimator_config.yaml"

# ── colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn()  { echo -e "${YELLOW}[setup]${NC} $*"; }
error() { echo -e "${RED}[setup]${NC} $*" >&2; exit 1; }

# ── 1. System dependencies ────────────────────────────────────────────────────
info "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential \
    cmake \
    libeigen3-dev \
    libopencv-dev \
    libboost-all-dev \
    libceres-dev \
    git

# ── 2. Clone OpenVINS ─────────────────────────────────────────────────────────
if [ -d "$OPENVINS_DIR" ]; then
    warn "open_vins/ already exists — skipping clone"
else
    info "Cloning OpenVINS..."
    git clone https://github.com/rpng/open_vins.git "$OPENVINS_DIR"
fi

# ── 3. Apply patch ────────────────────────────────────────────────────────────
TARGET_CPP="$OPENVINS_DIR/ov_msckf/src/run_simulation.cpp"

info "Applying trajectory-export patch..."
cd "$OPENVINS_DIR"
if git apply --check "$PATCH_FILE" 2>/dev/null; then
    git apply "$PATCH_FILE"
    info "Patch applied cleanly."
else
    warn "git apply failed — trying patch(1) fallback..."
    patch -p1 < "$PATCH_FILE" || error "Patch failed. Check patches/run_simulation.patch against your OpenVINS version."
fi

# ── 4. Copy config ────────────────────────────────────────────────────────────
info "Copying estimator config..."
CONFIG_DEST="$OPENVINS_DIR/config/rpng_sim/estimator_config.yaml"
cp "$CONFIG_SRC" "$CONFIG_DEST"

# Fix sim_traj_path to use absolute path in this repo
sed -i "s|src/open_vins/ov_data/sim/tum_corridor1_512_16_okvis.txt|$OPENVINS_DIR/ov_data/sim/tum_corridor1_512_16_okvis.txt|g" "$CONFIG_DEST"
info "Config path updated."

# ── 5. CMake build ────────────────────────────────────────────────────────────
info "Building OpenVINS (ENABLE_ROS=OFF)..."
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
cmake .. -DENABLE_ROS=OFF -DCMAKE_BUILD_TYPE=Release
make -j"$(nproc)"

# ── 6. Verify ─────────────────────────────────────────────────────────────────
BINARY="$BUILD_DIR/run_simulation"
if [ -f "$BINARY" ]; then
    info "Build successful → $BINARY"
else
    error "Build finished but run_simulation binary not found."
fi

echo ""
info "Setup complete. Run:  bash run.sh"
