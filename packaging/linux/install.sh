#!/bin/sh
# Instala o SCRCPY UI para o usuário atual (sem sudo): copia a pasta para
# ~/.local/share/scrcpy-ui, cria o atalho no menu de apps e o comando
# `scrcpy-ui` em ~/.local/bin.
#
#   ./install.sh            instala
#   ./install.sh --remove   desinstala
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
TARGET="$DATA/scrcpy-ui"
BIN="$HOME/.local/bin"

if [ "$1" = "--remove" ]; then
    rm -rf "$TARGET" "$BIN/scrcpy-ui" \
        "$DATA/applications/scrcpy-ui.desktop" \
        "$DATA/icons/hicolor/512x512/apps/scrcpy-ui.png"
    echo "SCRCPY UI removido."
    exit 0
fi

rm -rf "$TARGET"
mkdir -p "$TARGET" "$BIN" "$DATA/applications" "$DATA/icons/hicolor/512x512/apps"
cp -R "$HERE/." "$TARGET/"
ln -sf "$TARGET/scrcpy-ui" "$BIN/scrcpy-ui"
cp "$HERE/scrcpy-ui.png" "$DATA/icons/hicolor/512x512/apps/scrcpy-ui.png"
sed "s|^Exec=.*|Exec=$TARGET/scrcpy-ui|" "$HERE/scrcpy-ui.desktop" > "$DATA/applications/scrcpy-ui.desktop"
echo "SCRCPY UI instalado. Abra pelo menu de apps ou rode: scrcpy-ui"
