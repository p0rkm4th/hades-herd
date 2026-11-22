#!/usr/bin/env bash
# Melinoe: reuse running ComfyUI (:8188) behind GPU Turnstile (:8189).
# Preserve original Ollama client port (:11434) and all Herd/Strata configuration.
# If cutover fails, remove our Ollama drop-in and restart original service.
# This does NOT install another ComfyUI or change its files/models.
set -Eeuo pipefail
log() { printf '[Melinoe] %s\n' "$*"; }
die() { printf '[Melinoe] STOP: %s\n' "$*" >&2; exit 1; }
[[ $EUID -eq 0 ]] || die 'Must run with sudo/root.'
for tool in curl ss systemctl sha256sum python3; do
  command -v "$tool" >/dev/null || die "Missing required tool: $tool"
done
[[ $(uname -m) == x86_64 ]] || die 'Installer is for Linux x86_64.'
[[ -d /run/systemd/system ]] || die 'Host must use systemd.'
systemctl is-active -q ollama || die 'Ollama is not an active systemd service. No changes made.'
systemctl is-active -q gpu-turnstile && die 'GPU Turnstile is already running; refusing to replace it.'
DROP=/etc/systemd/system/ollama.service.d/zz-melinoe-turnstile.conf
CONF=/etc/gpu-turnstile/gpu-turnstile.yaml
[[ ! -e "$DROP" && ! -e "$CONF" ]] || die 'Existing Turnstile config/drop-in found; refusing to overwrite it.'
for p in 11435 8189; do
  ! ss -H -ltn "( sport = :$p )" | grep -q . || die "Port $p already used. No changes made."
done

TEMP="$(mktemp -d)"
CUTOVER=0
COMPLETE=0
clean() {
  code=$?
  trap - EXIT INT TERM
  if [[ $CUTOVER -eq 1 && $COMPLETE -eq 0 ]]; then
    log 'Cutover failed; restoring Ollama original configuration.'
    systemctl disable --now gpu-turnstile >/dev/null 2>&1 || true
    rm -f "$DROP" "$CONF"
    systemctl daemon-reload || true
    systemctl restart ollama || true
    for i in $(seq 1 25); do
      if curl --noproxy '*' -fsS --max-time 2 "$ORIGINAL_URL/api/tags" >/dev/null 2>&1; then
        log 'Rollback verified: Ollama available again on port 11434.'
        break
      fi
      sleep 1
    done
  elif [[ $COMPLETE -eq 0 ]]; then
    # Before cutover, only our newly generated proxy configuration may need removal.
    [[ -e "$CONF" ]] && rm -f "$CONF"
  fi
  rm -rf "$TEMP"
  exit "$code"
}
trap clean EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Discover the original listen address before probing; it may be LAN-only.
# Preserve EXACTLY that bind for existing clients when proxy takes over.
ORIG_BIND="$(ss -H -ltn '( sport = :11434 )' | awk 'NR==1 {print $4}')"
case "$ORIG_BIND" in
  0.0.0.0:11434|'*:11434') LISTENER=':11434'; ORIGINAL_URL='http://127.0.0.1:11434' ;;
  127.0.0.1:11434) LISTENER="$ORIG_BIND"; ORIGINAL_URL="http://$ORIG_BIND" ;;
  *) if [[ "$ORIG_BIND" =~ ^([0-9]{1,3}\\.){3}[0-9]{1,3}:11434$ ]]; then
       LISTENER="$ORIG_BIND"
       ORIGINAL_URL="http://$ORIG_BIND"
     else
       die "Unsupported Ollama listen address '$ORIG_BIND'; no changes made."
     fi ;;
esac
log "Detected original Ollama bind: $ORIG_BIND"
curl --noproxy '*' -fsS --max-time 4 "$ORIGINAL_URL/api/tags" > "$TEMP/models-before.json" ||
  die "Ollama $ORIGINAL_URL health check failed."
curl --noproxy '*' -fsS --max-time 4 http://127.0.0.1:8188/system_stats > "$TEMP/comfy-stats.json" ||
  die 'Existing ComfyUI :8188 health check failed.'
python3 - "$TEMP/comfy-stats.json" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    info=json.load(f)
if 'system' not in info or 'comfyui_version' not in info['system']:
    raise SystemExit('Unexpected ComfyUI response.')
print('[Melinoe] Existing ComfyUI version:', info['system']['comfyui_version'])
PY


log 'Downloading verified GPU Turnstile v1.6.0. Existing inference remains online.'
BASE=https://git.rambossek.at/PUBLIC/gpu-turnstile/releases/download/v1.6.0
curl --fail --location --silent --show-error --retry 3 -o "$TEMP/gpu-turnstile-linux-amd64" "$BASE/gpu-turnstile-linux-amd64"
curl --fail --location --silent --show-error --retry 3 -o "$TEMP/gpu-turnstile-linux-amd64.sha256" "$BASE/gpu-turnstile-linux-amd64.sha256"
(cd "$TEMP" && sha256sum -c gpu-turnstile-linux-amd64.sha256)
chmod +x "$TEMP/gpu-turnstile-linux-amd64"

# Running ComfyUI is unmanaged: omit engines.comfy.dir/cmd so it is NEVER killed or replaced.
mkdir -p /etc/gpu-turnstile
cat > "$CONF" <<EOF
listen:
  ollama: "$LISTENER"
  comfy: ":8189"
engines:
  ollama:
    url: "http://127.0.0.1:11435"
    unload_timeout: 2m
  comfy:
    url: "http://127.0.0.1:8188"
    queue_interval: 2s
llm:
  busy_mode: wait
  wait_timeout: 20m
update:
  auto: false
EOF
"$TEMP/gpu-turnstile-linux-amd64" config check -config "$CONF" ||
  die 'Turnstile rejected configuration; Ollama has not been modified.'

# Never sever an active Ollama stream. An established TCP connection could also be
# an idle keep-alive socket, but aborting is safer than risking an in-flight inference.
if ss -H -tn state established '( sport = :11434 )' | grep -q .; then
  die 'Ollama has established connections. Retry during an idle period; no changes made.'
fi

# A short controlled Ollama restart is needed to return the SAME public endpoint via proxy.
log 'Cutover: existing Ollama :11434 -> backend :11435, proxy retains :11434.'
mkdir -p "$(dirname "$DROP")"
cat > "$DROP" <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11435"
EOF
CUTOVER=1
systemctl daemon-reload
systemctl restart ollama
for i in $(seq 1 25); do
  curl --noproxy '*' -fsS --max-time 2 http://127.0.0.1:11435/api/tags >/dev/null 2>&1 && break
  sleep 1
done
curl --noproxy '*' -fsS --max-time 5 http://127.0.0.1:11435/api/tags >/dev/null ||
  die 'Ollama backend not responding.'

# The upstream installer creates the sandboxed systemd service and starts it.
"$TEMP/gpu-turnstile-linux-amd64" --install-service
for i in $(seq 1 30); do
  curl --noproxy '*' -fsS --max-time 2 "$ORIGINAL_URL/api/tags" > "$TEMP/models-after.json" 2>/dev/null && break
  sleep 1
done
curl --noproxy '*' -fsS --max-time 5 "$ORIGINAL_URL/api/tags" > "$TEMP/models-after.json" ||
  die 'Ollama proxy health check failed.'
curl --noproxy '*' -fsS --max-time 5 http://127.0.0.1:8189/system_stats > /dev/null ||
  die 'Existing ComfyUI is not reachable through proxy.'
python3 - "$TEMP/models-before.json" "$TEMP/models-after.json" <<'PY'
import json, sys
def inventory(path):
    with open(path) as f:
        data=json.load(f)
    return sorted(m.get('name','') for m in data.get('models', []))
if inventory(sys.argv[1]) != inventory(sys.argv[2]):
    raise SystemExit('Ollama inventory mismatch after cutover.')
print('[Melinoe] Ollama model inventory preserved.')
PY
systemctl is-active -q ollama || die 'Ollama service inactive.'
systemctl is-active -q gpu-turnstile || die 'Turnstile service inactive.'
COMPLETE=1
log 'SUCCESS. Ollama/Herd still use :11434; existing ComfyUI :8188 unchanged.'
log 'Use Melinoe-IP:8189 for ComfyChair to get managed GPU switching.'
log 'No image-generation model was downloaded; existing ComfyUI models are retained.'
