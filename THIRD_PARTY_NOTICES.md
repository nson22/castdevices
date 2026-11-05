# Componentes de terceiros

O CastDevices é licenciado sob a [Apache License 2.0](LICENSE). Os pacotes distribuídos nos
releases (Windows, macOS e Linux) incluem os componentes abaixo, cada um sob a sua própria
licença. Os textos completos das licenças estão na pasta [`LICENSES/`](LICENSES), que também vai
dentro de cada pacote.

| Componente | Uso no CastDevices | Licença | Texto |
|---|---|---|---|
| [scrcpy-server](https://github.com/Genymobile/scrcpy) 4.0 — © 2018 Genymobile, © 2018-2026 Romain Vimont | Servidor que roda no device (captura, encode, controle) | Apache-2.0 | [Apache-2.0](LICENSES/Apache-2.0.txt) |
| [Qt for Python (PySide6, Shiboken6)](https://www.qt.io/qt-for-python) e Qt 6 — © The Qt Company Ltd. | Interface (QML), vídeo e áudio | LGPL-3.0-only | [LGPL-3.0](LICENSES/LGPL-3.0-only.txt) + [GPL-3.0](LICENSES/GPL-3.0-only.txt) |
| [FFmpeg](https://ffmpeg.org) 9.0 (embutido no PyAV) — © os autores do FFmpeg | Decodificação de vídeo/áudio | LGPL-3.0-or-later | [LGPL-3.0](LICENSES/LGPL-3.0-only.txt) + [GPL-3.0](LICENSES/GPL-3.0-only.txt) |
| [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools) 37.0.0 (adb) — © The Android Open Source Project | Comunicação com o device | Apache-2.0 e outras (ver `NOTICE.txt` ao lado do `adb` no pacote) | [Apache-2.0](LICENSES/Apache-2.0.txt) |
| [PyAV](https://github.com/PyAV-Org/PyAV) — © os autores do PyAV | Binding Python do FFmpeg | BSD-3-Clause | [site do projeto](https://github.com/PyAV-Org/PyAV/blob/main/LICENSE.txt) |
| [adbutils](https://github.com/openatx/adbutils) — © openatx | Cliente do protocolo adb | MIT | [site do projeto](https://github.com/openatx/adbutils/blob/master/LICENSE) |
| [NumPy](https://numpy.org) — © NumPy Developers | Manipulação dos frames | BSD-3-Clause (e componentes 0BSD, MIT, Zlib, CC0) | [site do projeto](https://github.com/numpy/numpy/blob/main/LICENSE.txt) |
| [Pillow](https://python-pillow.org) — © Jeffrey A. Clark e colaboradores | Imagens (screenshots, ícones) | MIT-CMU | [site do projeto](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| [Python](https://www.python.org) 3.12 — © Python Software Foundation | Runtime | PSF-2.0 | [site do projeto](https://docs.python.org/3/license.html) |
| [Material Symbols](https://github.com/google/material-design-icons) — © Google LLC | Ícones da interface | Apache-2.0 | [Apache-2.0](LICENSES/Apache-2.0.txt) |
| [Roboto](https://github.com/googlefonts/roboto-classic) — © 2011 The Roboto Project Authors | Fonte da interface | OFL-1.1 | [OFL-1.1](LICENSES/OFL-1.1.txt) |

O executável é gerado com o [PyInstaller](https://pyinstaller.org) (GPL-2.0 com exceção de
bootloader, que permite distribuir o resultado sob qualquer licença).

## Qt e FFmpeg (LGPL-3.0)

O CastDevices usa o Qt (via PySide6) e o FFmpeg sob a GNU Lesser General Public License, versão 3.
Para cumprir a LGPL:

- **As bibliotecas são dinâmicas e substituíveis.** Os pacotes são gerados no modo "pasta" do
  PyInstaller: as bibliotecas do Qt/PySide6 e do FFmpeg ficam como arquivos separados
  (`.dll`/`.dylib`/`.so`) dentro de `_internal/` (Windows/Linux) ou de
  `CastDevices.app/Contents/Frameworks/` (macOS). Você pode trocá-las por versões compatíveis
  modificadas por você. No macOS, depois de trocar, reassine o app localmente
  (`codesign --force --deep --sign - "CastDevices.app"`).
- **Código-fonte das bibliotecas:**
  - Qt 6: https://download.qt.io/official_releases/qt/ e https://code.qt.io
  - PySide6 / Shiboken6 6.12: https://download.qt.io/official_releases/QtForPython/ e
    https://code.qt.io/cgit/pyside/pyside-setup.git
  - FFmpeg 9.0: https://ffmpeg.org/download.html — o build usado pelo PyAV é feito pelos
    scripts de https://github.com/PyAV-Org/pyav-ffmpeg
- **Código-fonte do CastDevices**, para refazer o pacote com bibliotecas modificadas:
  https://github.com/nson22/scrcpy_ui (instruções de build no README).

Se não conseguir obter algum desses códigos-fonte pelos links acima, abra uma
[issue](https://github.com/nson22/scrcpy_ui/issues) que fornecemos uma cópia.

### Módulos do Qt que não vão no pacote

Alguns módulos do Qt são licenciados só sob GPL (ou licença comercial), sem a opção LGPL, e por
isso não podem ser distribuídos junto de um app Apache-2.0. O CastDevices não usa nenhum deles, e o
build (`castdevices.spec`) os deixa de fora: Qt Quick Timeline, Qt Shader Tools, Qt Quick 3D,
Qt Virtual Keyboard, Qt Charts, Qt Data Visualization, Qt Graphs, Qt Lottie, Qt HTTP Server,
Qt Protobuf/gRPC, Qt MQTT, Qt CoAP, Qt OPC UA e Qt Wayland Compositor.

Os pacotes dos releases `v0.0.3-alpha` e `v0.0.4-alpha` foram gerados antes dessa exclusão e
ainda contêm as bibliotecas do Qt Quick Timeline e do Qt Shader Tools (não usadas pelo app). Os
próximos releases já saem sem elas.

## scrcpy

O CastDevices é um cliente independente: ele **não é** um projeto oficial do scrcpy nem da
Genymobile. Ele reutiliza o `scrcpy-server` oficial, sem modificações, sob a Apache License 2.0.
