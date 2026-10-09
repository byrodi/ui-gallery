#!/bin/sh
# Rebuild and serve the UI gallery from this harness, or stop it.
#   ./serve.sh [port]     build, write gallery.html, start the preview in the background
#   ./serve.sh stop       stop the preview this script started (by its PID file, never by pattern)
# Needs node_modules (a symlink to the app's) and python3. Set APP in vite.config.mjs or the env.
set -eu
cd "$(dirname "$0")"
pidfile=.gallery.pid
if [ "${1:-}" = stop ]; then
  if [ -f "$pidfile" ] && kill "$(cat "$pidfile")" 2>/dev/null; then echo "stopped"; else echo "not running"; fi
  rm -f "$pidfile"
  exit 0
fi
port=${1:-5198}
if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
  echo "already running (PID $(cat "$pidfile")); run ./serve.sh stop first" >&2
  exit 1
fi
./node_modules/.bin/vite build --config vite.config.mjs --outDir dist --emptyOutDir --logLevel warn
python3 make_gallery.py scenarios.json --out dist/gallery.html
nohup ./node_modules/.bin/vite preview --config vite.config.mjs --outDir dist --port "$port" --strictPort --host 127.0.0.1 >.gallery.log 2>&1 &
echo $! >"$pidfile"
i=0
until curl -fsS -o /dev/null "http://127.0.0.1:$port/gallery.html" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then echo "the preview did not start; see .gallery.log" >&2; exit 1; fi
  sleep 0.5
done
echo "http://127.0.0.1:$port/gallery.html"
