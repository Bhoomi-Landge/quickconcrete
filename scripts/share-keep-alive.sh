#!/usr/bin/env bash
# Reliable share: builds app, serves on one port, keeps Mac awake, restarts Cloudflare
# if the tunnel drops. URL is written to share-url.txt whenever it changes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PYTHON="$BACKEND/venv/bin/python"
URL_FILE="$ROOT/share-url.txt"
PORT="${PORT:-5055}"
URL="http://127.0.0.1:${PORT}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing backend venv. Run: cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
  exit 1
fi
if ! command -v cloudflared >/dev/null; then
  echo "Install: brew install cloudflared"
  exit 1
fi

# Free the port
if lsof -ti:"$PORT" >/dev/null 2>&1; then
  echo "==> Freeing port ${PORT}..."
  lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

echo "==> Building frontend..."
(cd "$FRONTEND" && npm run build)

echo "==> Starting app on ${URL}..."
export SERVE_FRONTEND=1
export PORT
cd "$BACKEND"
"$PYTHON" -c "
from app import app
app.run(host='127.0.0.1', port=int('${PORT}'), debug=False, use_reloader=False, threaded=True)
" &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  pkill -f "cloudflared tunnel --protocol http2 --url ${URL}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for i in $(seq 1 40); do
  if curl -sf "${URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
if ! curl -sf "${URL}/api/health" >/dev/null 2>&1; then
  echo "App failed to start on ${URL}"
  exit 1
fi
if [[ "$(curl -s -o /dev/null -w '%{http_code}' "${URL}/")" != "200" ]]; then
  echo "App is not serving the website on ${URL}"
  exit 1
fi

echo "==> App OK. Keeping Mac awake (caffeinate) + restarting Cloudflare if it drops..."
echo "==> Current public URL will be saved to: ${URL_FILE}"
echo ""

# Prevent sleep while this script runs (needs caffeinate; ignore if missing)
if command -v caffeinate >/dev/null; then
  caffeinate -dims -w $$ &
  CAFFEINE_PID=$!
  trap 'kill $CAFFEINE_PID 2>/dev/null || true; cleanup' EXIT INT TERM
fi

LOG="$(mktemp -t qc-tunnel.XXXXXX)"
attempt=0
while true; do
  attempt=$((attempt + 1))
  : >"$LOG"
  echo "==> Tunnel attempt #${attempt}..."
  # Run cloudflared; capture URL from its log as soon as it appears
  cloudflared tunnel --protocol http2 --url "${URL}" 2>&1 | tee "$LOG" &
  CF_PID=$!

  # Wait up to 45s for a trycloudflare URL
  public=""
  for _ in $(seq 1 45); do
    public="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | tail -1 || true)"
    if [[ -n "$public" ]]; then
      echo "$public" >"$URL_FILE"
      echo ""
      echo "============================================"
      echo "  SHARE THIS LINK (only this one):"
      echo "  $public"
      echo "============================================"
      echo "  Also saved in share-url.txt"
      echo "  Leave this terminal open. Mac will stay awake."
      echo ""
      break
    fi
    if ! kill -0 "$CF_PID" 2>/dev/null; then
      break
    fi
    sleep 1
  done

  # Wait until cloudflared exits (disconnect / sleep / crash)
  wait "$CF_PID" || true
  echo "==> Tunnel dropped. Restarting in 3s..."
  sleep 3
done
