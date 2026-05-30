#!/usr/bin/env bash
# =============================================================================
# run.sh — Execute OpenVINS simulation and collect trajectory outputs
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENVINS_DIR="$REPO_ROOT/open_vins"
BUILD_DIR="$OPENVINS_DIR/ov_msckf/build"
CONFIG="$OPENVINS_DIR/config/rpng_sim/estimator_config.yaml"
RESULTS_DIR="$REPO_ROOT/results"
BINARY="$BUILD_DIR/run_simulation"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[run]${NC} $*"; }
warn()  { echo -e "${YELLOW}[run]${NC} $*"; }
error() { echo -e "${RED}[run]${NC} $*" >&2; exit 1; }

# ── Checks ────────────────────────────────────────────────────────────────────
[ -f "$BINARY" ]  || error "Binary not found. Run: bash setup.sh first."
[ -f "$CONFIG" ]  || error "Config not found at $CONFIG"

# ── Run simulation ────────────────────────────────────────────────────────────
info "Running OpenVINS simulation..."
info "Config: $CONFIG"
echo ""

cd "$BUILD_DIR"
"$BINARY" "$CONFIG"

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    error "Simulation exited with code $EXIT_CODE"
fi

# ── Collect outputs ───────────────────────────────────────────────────────────
mkdir -p "$RESULTS_DIR"

for f in trajectory.txt groundtruth.txt; do
    if [ -f "$BUILD_DIR/$f" ]; then
        cp "$BUILD_DIR/$f" "$RESULTS_DIR/$f"
        LINES=$(wc -l < "$RESULTS_DIR/$f")
        info "Saved $f → results/$f  ($((LINES - 1)) data points)"
    else
        warn "$f not found in build dir — patch may not have applied correctly."
    fi
done

echo ""
info "Simulation complete. Run:  python evaluate.py"
