#!/usr/bin/env python3
import argparse, base64, io, os, sys, zipfile, pathlib, textwrap

TEMPLATE = r"""#!/usr/bin/env bash
set -euo pipefail

APP_NAME="__APP_NAME__"
INSTALL_ROOT="${HOME}/.local/opt"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${INSTALL_ROOT}/${APP_NAME}"
VENV_DIR="${APP_DIR}/.venv"
B64_FILE="${APP_DIR}/.payload.b64"

echo "Installing $APP_NAME to $APP_DIR"

mkdir -p "$APP_DIR" "$BIN_DIR"

# Write embedded payload to file to avoid huge env/argv limits
cat > "$B64_FILE" <<'__B64__'
__PAYLOAD_B64__
__B64__

export APP_DIR

python3 - <<'PY'
import base64, sys, os, zipfile, io
app_dir = os.environ['APP_DIR']
b64_path = os.path.join(app_dir, '.payload.b64')
with open(b64_path, 'r') as f:
    b64 = f.read()
data = base64.b64decode(b64.encode('ascii'))
zf = zipfile.ZipFile(io.BytesIO(data))
zf.extractall(app_dir)
os.remove(b64_path)
PY

# If payload nested a top-level folder, use it
if [ -d "$APP_DIR/__APP_NAME__" ]; then
  APP_SRC="$APP_DIR/__APP_NAME__"
else
  APP_SRC="$APP_DIR"
fi

# Create venv and install requirements
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Please install python3-venv and re-run." >&2
  exit 1
fi

if ! python3 -Im venv -h >/dev/null 2>&1; then
  echo "Installing python3-venv is required on Ubuntu: sudo apt install -y python3-venv" >&2
  exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "$APP_SRC/requirements.txt" ]; then
  pip install -r "$APP_SRC/requirements.txt"
fi

# Create launcher
cat > "$BIN_DIR/__LAUNCHER_NAME__" <<'LAUNCH'
#!/usr/bin/env bash
APP_DIR="${HOME}/.local/opt/__APP_NAME__"
VENV_DIR="${APP_DIR}/.venv"
SRC_DIR="${APP_DIR}/__APP_NAME__"
if [ -f "${SRC_DIR}/main.py" ]; then
  MAIN="${SRC_DIR}/main.py"
else
  MAIN="${APP_DIR}/main.py"
fi
exec "${VENV_DIR}/bin/python" "$MAIN" "$@"
LAUNCH
chmod +x "$BIN_DIR/__LAUNCHER_NAME__"

echo ""
echo "✅ Installed. Add $BIN_DIR to your PATH if needed, then run: __LAUNCHER_NAME__"
echo "   PATH example: echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc"
"""

def zip_dir_to_bytes(src_dir: str) -> bytes:
    src = pathlib.Path(src_dir).resolve()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # If the directory name is not the app name, still preserve top-level folder
        root_name = src.name
        for path in src.rglob("*"):
            if path.is_file():
                rel = path.relative_to(src.parent)  # include the folder itself
                zf.write(path, rel.as_posix())
    return buf.getvalue()

def main():
    ap = argparse.ArgumentParser(description="Build a self-extracting Linux/macOS installer with embedded payload")
    ap.add_argument("--src", required=True, help="Path to your project folder (will be zipped)")
    ap.add_argument("--app-name", required=True, help="Application name (used for install dir and launcher defaults)")
    ap.add_argument("--launcher-name", default=None, help="Launcher command name (default: lowercased app name)")
    ap.add_argument("--output", required=True, help="Path to write the installer script, e.g. install_bibsteak.sh")
    args = ap.parse_args()

    app_name = args.app_name
    launcher_name = (args.launcher_name or app_name).lower()

    payload = zip_dir_to_bytes(args.src)
    payload_b64 = base64.b64encode(payload).decode("ascii")

    script = TEMPLATE.replace("__PAYLOAD_B64__", payload_b64)\
                     .replace("__APP_NAME__", app_name)\
                     .replace("__LAUNCHER_NAME__", launcher_name)

    out = pathlib.Path(args.output)
    out.write_text(script, encoding="utf-8")
    out.chmod(0o755)
    print(f"Wrote installer: {out}")

if __name__ == "__main__":
    main()
