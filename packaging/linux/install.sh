#!/bin/sh
# Instala o CastDevices para o usuário atual (sem sudo): copia a pasta para
# ~/.local/share/castdevices, cria o atalho no menu de apps e o comando
# `castdevices` em ~/.local/bin.
#
#   ./install.sh            instala
#   ./install.sh --remove   desinstala
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
TARGET="$DATA/castdevices"
BIN="$HOME/.local/bin"

if [ "$1" = "--remove" ]; then
    rm -rf "$TARGET" "$BIN/castdevices" \
        "$DATA/applications/castdevices.desktop" \
        "$DATA/icons/hicolor/512x512/apps/castdevices.png"
    echo "CastDevices removido."
    exit 0
fi

rm -rf "$TARGET"
mkdir -p "$TARGET" "$BIN" "$DATA/applications" "$DATA/icons/hicolor/512x512/apps"
cp -R "$HERE/." "$TARGET/"
ln -sf "$TARGET/castdevices" "$BIN/castdevices"
cp "$HERE/castdevices.png" "$DATA/icons/hicolor/512x512/apps/castdevices.png"
sed "s|^Exec=.*|Exec=$TARGET/castdevices|" "$HERE/castdevices.desktop" > "$DATA/applications/castdevices.desktop"
echo "CastDevices instalado. Abra pelo menu de apps ou rode: castdevices"
