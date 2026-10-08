#!/usr/bin/env bash
# Build frontend + run API + SPA on :5000, then expose via Cloudflare quick tunnel.
# Keep this terminal open. Link dies if you quit or the Mac sleeps.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PYTHON="$BACKEND/venv/bin/python"
PORT="${PORT:-5000}"
URL="http://127.0.0.1:${PORT}"

pick_port() {
  local p
  for p in 5000 5001 5050 8765; do
    if ! lsof -ti:"$p" >/dev/null 2>&1; then
      PORT="$p"
      URL="http://127.0.0.1:${PORT}"
      return 0
    fi
  done
  echo "Ports 5000, 5001, 5050, 8765 are busy. Stop other servers or set PORT=."
  exit 1
}

if lsof -ti:"$PORT" >/dev/null 2>&1; then
  echo "==> Port ${PORT} is in use; picking another port..."
  pick_port
  echo "==> Using port ${PORT}"
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing $PYTHON — create venv in backend first."
  exit 1
fi

if ! command -v cloudflared >/dev/null; then
  echo "Install cloudflared: brew install cloudflared"
  exit 1
fi

echo "==> Building frontend..."
(cd "$FRONTEND" && npm run build)

echo "==> Starting QuickConcrete on ${URL} (API + website)..."
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
}
trap cleanup EXIT INT TERM

for i in {1..30}; do
  if curl -sf "${URL}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -sf "${URL}/api/health" >/dev/null 2>&1; then
  echo "Server failed to start on ${URL}"
  exit 1
fi

SPA_CODE="$(curl -s -o /dev/null -w "%{http_code}" "${URL}/")"
if [[ "$SPA_CODE" != "200" ]]; then
  echo "Server on ${URL} is not serving the built website (got / = ${SPA_CODE})."
  echo "Stop other Flask processes and run this script again."
  exit 1
fi

echo "==> Local OK: ${URL} (website + API)"
echo "==> Starting Cloudflare tunnel (copy the https://….trycloudflare.com URL below)..."
echo ""

# http2 is often more reliable than quic on Indian Wi‑Fi / mobile networks
cloudflared tunnel --protocol http2 --url "${URL}"
