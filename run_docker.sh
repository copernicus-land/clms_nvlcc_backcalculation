#!/usr/bin/env bash
# Build a Docker image from environment.yml and serve the notebook with JupyterLab.
#
# Usage: ./run_docker.sh [--lan] [port]      (default port: 8888)
#
#   (default)  listen on localhost only, without a token
#   --lan      listen on all network interfaces, protected by a random token
#
# The repository is mounted into the container, so notebook edits are saved
# back to this folder.
set -euo pipefail

usage() { sed -n '4,7s/^# \{0,1\}//p' "$0"; }

LAN=false
PORT=8888
for arg in "$@"; do
    case "$arg" in
        --lan)     LAN=true ;;
        -h|--help) usage; exit 0 ;;
        *[!0-9]*|'') echo "Unknown argument: $arg" >&2; usage >&2; exit 1 ;;
        *)         PORT="$arg" ;;
    esac
done

IMAGE="nvlcc-backcalculation"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NB_PATH="lab/tree/change_backcalculation.ipynb"

# Only environment.yml is copied into the image, so edits to the notebook
# or helpers don't invalidate the (slow) environment layer.
docker build -t "$IMAGE" -f - "$REPO_DIR" <<'EOF'
FROM mambaorg/micromamba:1.5.10
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && micromamba clean --all --yes
EOF

if $LAN; then
    # Anyone who can reach the port could run code as you, so require a token.
    TOKEN="$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')"
    PUBLISH="${PORT}:8888"
    echo "Serving on all interfaces (Ctrl+C to stop). Open from another machine via:"
    # Host IPv4 addresses, skipping Docker's own bridge interfaces
    for ip in $(ip -4 -o addr show scope global 2>/dev/null \
                | awk '$2 !~ /^(docker|br-|veth)/ {sub(/\/.*/, "", $4); print $4}'); do
        echo "  http://${ip}:${PORT}/${NB_PATH}?token=${TOKEN}"
    done
    echo "  (or http://localhost:${PORT}/${NB_PATH}?token=${TOKEN} on this machine)"
else
    TOKEN=""
    PUBLISH="127.0.0.1:${PORT}:8888"
    echo "Serving at http://localhost:${PORT}/${NB_PATH} (Ctrl+C to stop)"
fi

# Run as the host user so files written to the mounted repo keep your ownership.
docker run --rm -it \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -p "$PUBLISH" \
    -v "$REPO_DIR":/work \
    -w /work \
    "$IMAGE" \
    jupyter lab --ip=0.0.0.0 --port=8888 --no-browser \
        --ServerApp.token="$TOKEN" --ServerApp.password='' \
        --ServerApp.root_dir=/work
