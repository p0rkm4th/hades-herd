#!/usr/bin/env bash
# Installs ComfyUI + Z-Image Turbo INT8 + gpu-turnstile on Melinoe.
# Preserves Herd/Strata configurations and the public Ollama :11434 endpoint.
# All downloads/preflight occur before cutover; failure restores Ollama.
set -Eeuo pipefail
log() { printf '\n[melinoe] %s\n' "$*"; }
die() { printf '\n[melinoe] ABORT: %s\n' "$*" >&2; exit 1; }
[[ $EUID -eq 0 ]] || die 'Run as root: curl ... | sudo bash'
command -v systemctl >/dev/null || die 'systemd is required.'
command -v apt-get >/dev/null || die 'This installer supports Debian/Ubuntu only.'
command -v nvidia-smi >/dev/null || die 'NVIDIA driver missing.'
for c in curl ss sha256sum; do command -v "$c" >/dev/null || die "Required command missing: $c"; done

COMFY_DIR=/opt/melinoe-comfyui
DROPIN_DIR=/etc/systemd/system/ollama.service.d
DROPIN="$DROPIN_DIR/zz-melinoe-gpu-turnstile.conf"
CFG=/etc/gpu-turnstile/gpu-turnstile.yaml
VERSION=v1.6.0
ROOT_URL="https://git.rambossek.at/PUBLIC/gpu-turnstile/releases/download/$VERSION"
CUTOVER=0
COMPLETE=0
CREATED_CFG=0
TMP=$(mktemp -d)
cleanup() {
  local rc=$?
  trap - EXIT INT TERM
  if [[ "$CUTOVER" == 1 && "$COMPLETE" != 1 ]]; then
    log 'Cutover failed; restoring original Ollama endpoint.'
    systemctl disable --now gpu-turnstile >/dev/null 2>&1 || true
    rm -f -- "$DROPIN" "$CFG"
    systemctl daemon-reload || true
    systemctl restart ollama || true
    for _ in $(seq 1 20); do
      if curl -fsS --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        log 'Rollback verified: Ollama responds on :11434.'
        break
      fi
      sleep 1
    done
  elif [[ "$CREATED_CFG" == 1 && "$COMPLETE" != 1 ]]; then
    rm -f -- "$CFG"
  fi
  rm -rf -- "$TMP"
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

systemctl is-active --quiet ollama || die 'Ollama must be a running systemd service; no changes made.'
[[ ! -e "$DROPIN" ]] || die "Existing override: $DROPIN. Refusing to overwrite."
[[ ! -e "$CFG" ]] || die "Existing gpu-turnstile config: $CFG. Refusing to overwrite."
! systemctl is-active --quiet gpu-turnstile || die 'gpu-turnstile already running.'
for port in 11435 8188 8189; do
  if ss -H -ltn "sport = :$port" | grep -q .; then die "Port $port in use; no changes made."; fi
done
curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags >"$TMP/models-before.json" || die 'Ollama does not answer at :11434.'

DRIVER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1 | cut -d. -f1)
[[ $DRIVER =~ ^[0-9]+$ ]] || die 'Cannot read NVIDIA driver.'
if (( DRIVER >= 580 )); then TORCH_CUDA=cu130
elif (( DRIVER >= 570 )); then TORCH_CUDA=cu128
else die "NVIDIA driver $DRIVER is too old for automated CUDA install; Ollama unchanged."
fi
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
log "GPU: $GPU, driver: $DRIVER, CUDA wheel: $TORCH_CUDA."
FREE_KB=$(df -Pk /opt | awk 'END {print $4}')
(( FREE_KB >= 23 * 1024 * 1024 )) || die 'Need 23 GiB free on /opt.'
log 'Installing ComfyUI and models. Ollama is still serving existing clients.'
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip curl ca-certificates acl >/dev/null

if [[ ! -d "$COMFY_DIR/.git" ]]; then
  [[ ! -e "$COMFY_DIR" ]] || die "$COMFY_DIR exists but is not a git checkout."
  git clone --depth 1 https://github.com/Comfy-Org/ComfyUI.git "$COMFY_DIR"
else
  log 'Existing ComfyUI checkout detected; preserving its version.'
fi
if [[ ! -x "$COMFY_DIR/.venv/bin/python" ]]; then python3 -m venv "$COMFY_DIR/.venv"; fi
"$COMFY_DIR/.venv/bin/pip" install -q --upgrade pip
"$COMFY_DIR/.venv/bin/pip" install -q torch torchvision torchaudio --index-url "https://download.pytorch.org/whl/$TORCH_CUDA"
"$COMFY_DIR/.venv/bin/pip" install -q -r "$COMFY_DIR/requirements.txt"
"$COMFY_DIR/.venv/bin/python" -c 'import torch; assert torch.cuda.is_available(), "CUDA unavailable"; print("CUDA ready:", torch.cuda.get_device_name(0))'

# Official Comfy-Org model files; .part protects interrupted/resumable downloads.
HF=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
get_model() {
  local folder="$1" name="$2" minbytes="$3"
  local dst="$COMFY_DIR/models/$folder/$name" part="$dst.part"
  mkdir -p "$(dirname "$dst")"
  if [[ -s "$dst" && $(stat -c %s "$dst") -ge "$minbytes" ]]; then
    log "Model present: $name"
    return 0
  fi
  log "Downloading $name"
  curl -fL --retry 5 --retry-all-errors -C - --output "$part" "$HF/$folder/$name"
  [[ $(stat -c %s "$part") -ge "$minbytes" ]] || die "Incomplete download: $name"
  mv -f -- "$part" "$dst"
}
get_model diffusion_models z_image_turbo_int8_convrot.safetensors 5500000000
get_model text_encoders qwen_3_4b_fp8_mixed.safetensors 5000000000
get_model vae ae.safetensors 300000000
mkdir -p "$COMFY_DIR"/{workflows,input,output,temp,user}
curl -fLsS --retry 3 -o "$COMFY_DIR/workflows/z_image_turbo_int8.json" \
  https://raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/image_z_image_turbo_int8.json

log 'Downloading and SHA-256 verifying gpu-turnstile.'
curl -fLsS --retry 3 -o "$TMP/gpu-turnstile-linux-amd64" "$ROOT_URL/gpu-turnstile-linux-amd64"
curl -fLsS --retry 3 -o "$TMP/gpu-turnstile-linux-amd64.sha256" "$ROOT_URL/gpu-turnstile-linux-amd64.sha256"
(cd "$TMP" && sha256sum -c gpu-turnstile-linux-amd64.sha256)
chmod 755 "$TMP/gpu-turnstile-linux-amd64"

log 'Downloads complete. Beginning brief Ollama endpoint cutover.'
mkdir -p "$DROPIN_DIR" "$(dirname "$CFG")"
cat > "$CFG" <<EOF
listen:
  ollama: ":11434"
  comfy: ":8188"
engines:
  ollama:
    url: "http://127.0.0.1:11435"
    unload_timeout: 2m
  comfy:
    url: "http://127.0.0.1:8189"
    dir: "$COMFY_DIR"
    idle_timeout: 2m
    start_timeout: 4m
llm:
  busy_mode: wait
  wait_timeout: 20m
update:
  auto: false
EOF
CREATED_CFG=1
"$TMP/gpu-turnstile-linux-amd64" config check -config "$CFG" || die 'Invalid proxy config; Ollama unchanged.'
cat > "$DROPIN" <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11435"
EOF
CUTOVER=1
systemctl daemon-reload
systemctl restart ollama
for _ in $(seq 1 20); do
  if curl -fsS --max-time 3 http://127.0.0.1:11435/api/tags >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -fsS --max-time 5 http://127.0.0.1:11435/api/tags >/dev/null || die 'Ollama backend failed.'

"$TMP/gpu-turnstile-linux-amd64" --install-service
id -u gpu-turnstile >/dev/null || die 'Turnstile service user missing.'
chown -R gpu-turnstile:gpu-turnstile "$COMFY_DIR"
systemctl restart gpu-turnstile
for _ in $(seq 1 30); do
  if curl -fsS --max-time 4 http://127.0.0.1:11434/api/tags >"$TMP/models-after.json" 2>/dev/null; then break; fi
  sleep 1
done
curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags >"$TMP/models-after.json" || die 'Proxy is not passing Ollama requests.'
python3 - "$TMP/models-before.json" "$TMP/models-after.json" <<'PY'
import json, sys
with open(sys.argv[1]) as f: before = json.load(f)
with open(sys.argv[2]) as f: after = json.load(f)
names = lambda d: sorted(m.get('name') for m in d.get('models', []))
if names(before) != names(after):
    raise SystemExit('Ollama model inventory changed unexpectedly.')
print('[melinoe] Ollama models unchanged; proxy API verified.')
PY
systemctl is-active --quiet ollama || die 'Ollama is not running.'
systemctl is-active --quiet gpu-turnstile || die 'Proxy is not running.'
COMPLETE=1
log 'SUCCESS. Existing Ollama/Herd endpoint: :11434. ComfyChair/ComfyUI: :8188.'
log "Workflow saved to: $COMFY_DIR/workflows/z_image_turbo_int8.json"
log 'Any inference already streaming at Ollama restart was interrupted and must be retried.'
