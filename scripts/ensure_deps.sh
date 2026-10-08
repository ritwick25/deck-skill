#!/usr/bin/env bash
# Self-heal the skill's dependencies before any build: Python packages (python-pptx, lxml,
# pillow, diagrams) and the render toolchain (LibreOffice, poppler, librsvg). Safe to run on
# every invocation: each check is a fast no-op once a dependency is already present.
# Covers macOS (Homebrew) and Linux (apt/dnf — the shape of a Claude Code cloud container).
# Never blocks on a password it can't supply: where a step would need sudo and none is
# available, it routes around the need (e.g. symlinking the brew-staged LibreOffice binary
# instead of moving the app into /Applications) or reports the one manual command to run.
set -uo pipefail

PY=${DECK_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.14/bin/python3}
[ -x "$PY" ] || PY=python3

missing_py=$("$PY" - <<'EOF'
mods = {
    "pptx": "python-pptx", "lxml": "lxml", "PIL": "pillow", "diagrams": "diagrams==0.25.1",
    "fontTools": "fonttools",     # text measurement (deckkit.measure): every title/textbox call needs it
    "playwright": "playwright",   # scripts/capture.py only (product-screen/output-capture HTML exhibits)
    "defusedxml": "defusedxml",   # gates/p12_package.py's XSD validation of the built pptx package
}
missing = []
for mod, pkg in mods.items():
    try:
        __import__(mod)
    except ImportError:
        missing.append(pkg)
print(" ".join(missing))
EOF
)

if [ -n "$missing_py" ]; then
    echo "deck: installing missing Python packages: $missing_py" >&2
    "$PY" -m pip install --user --break-system-packages $missing_py \
        || "$PY" -m pip install --user $missing_py \
        || "$PY" -m pip install $missing_py \
        || echo "deck: pip install failed for: $missing_py — install manually" >&2

    # capture.py (scripts/capture.py) drives a real Chromium via Playwright for HTML exhibit
    # screenshots; the pip package alone has no browser. Best effort only: never block the rest
    # of the setup on a ~150MB browser download.
    if echo "$missing_py" | grep -q playwright; then
        echo "deck: fetching Playwright's chromium (used only by scripts/capture.py)" >&2
        "$PY" -m playwright install chromium >&2 \
            || echo "deck: chromium fetch failed — scripts/capture.py will fail until you run: $PY -m playwright install chromium" >&2
    fi
fi

OS=$(uname -s)

if [ "$OS" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
        for formula in poppler librsvg; do
            if ! brew list "$formula" >/dev/null 2>&1; then
                echo "deck: installing $formula via brew" >&2
                brew install "$formula" >&2 || echo "deck: brew install $formula failed — install manually" >&2
            fi
        done

        if ! command -v soffice >/dev/null 2>&1 && [ ! -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
            if [ -d /Applications ] && [ -w /Applications ]; then
                echo "deck: installing libreoffice via brew (cask)" >&2
                brew install --cask libreoffice >&2 \
                    || echo "deck: brew install --cask libreoffice failed — run it yourself in a terminal" >&2
            else
                # /Applications isn't writable by this account (no admin group), so the cask's
                # final "move to /Applications" step would need sudo. brew still stages the app
                # fully in the Caskroom even when that last step fails — symlink the soffice
                # binary from there into brew's own user-owned bin dir instead. No admin needed.
                echo "deck: installing libreoffice via brew (cask, staging only — no admin on this account)" >&2
                brew install --cask libreoffice >&2
                staged=$(find /opt/homebrew/Caskroom/libreoffice -maxdepth 3 -name soffice -path '*/MacOS/soffice' 2>/dev/null | sort -V | tail -1)
                if [ -n "$staged" ] && [ -x "$staged" ]; then
                    ln -sf "$staged" /opt/homebrew/bin/soffice
                    echo "deck: linked $staged -> /opt/homebrew/bin/soffice" >&2
                else
                    echo "deck: could not find a staged soffice binary — install LibreOffice manually" >&2
                fi
            fi
        fi
    else
        echo "deck: no Homebrew found — install poppler, librsvg and libreoffice manually for this platform" >&2
    fi

elif [ "$OS" = "Linux" ]; then
    # Root (the common case inside a cloud container) needs no sudo; otherwise use passwordless
    # sudo if it's there, and fall back to reporting the command when neither is available.
    if [ "$(id -u)" = "0" ]; then
        SUDO=""
    elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        SUDO="sudo"
    else
        SUDO=""
        NO_ROOT=1
    fi

    need_apt=""
    command -v pdftoppm   >/dev/null 2>&1 || need_apt="$need_apt poppler-utils"
    command -v rsvg-convert >/dev/null 2>&1 || need_apt="$need_apt librsvg2-bin"
    command -v soffice    >/dev/null 2>&1 || need_apt="$need_apt libreoffice"

    if [ -n "$need_apt" ]; then
        if command -v apt-get >/dev/null 2>&1; then
            if [ -n "${NO_ROOT:-}" ]; then
                echo "deck: missing packages ($need_apt) and no root/passwordless sudo — run yourself:" >&2
                echo "deck:   sudo apt-get update && sudo apt-get install -y$need_apt" >&2
            else
                echo "deck: installing via apt:$need_apt" >&2
                $SUDO apt-get update >&2 \
                    && $SUDO apt-get install -y $need_apt >&2 \
                    || echo "deck: apt-get install failed for:$need_apt — install manually" >&2
            fi
        elif command -v dnf >/dev/null 2>&1; then
            need_dnf=$(echo "$need_apt" | sed 's/poppler-utils/poppler-utils/; s/librsvg2-bin/librsvg2-tools/; s/libreoffice/libreoffice/')
            if [ -n "${NO_ROOT:-}" ]; then
                echo "deck: missing packages ($need_dnf) and no root/passwordless sudo — run yourself:" >&2
                echo "deck:   sudo dnf install -y$need_dnf" >&2
            else
                echo "deck: installing via dnf:$need_dnf" >&2
                $SUDO dnf install -y $need_dnf >&2 || echo "deck: dnf install failed for:$need_dnf — install manually" >&2
            fi
        else
            echo "deck: no apt-get or dnf found — install$need_apt manually for this distro" >&2
        fi
    fi
else
    echo "deck: unrecognized platform ($OS) — install poppler, librsvg and libreoffice manually" >&2
fi

exit 0
