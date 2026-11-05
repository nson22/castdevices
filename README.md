# scrcpy-ui

Cliente desktop multiplataforma (Python + [PySide6](https://pypi.org/project/PySide6/)/QML) que
reimplementa, de forma independente, as funcionalidades do
[scrcpy](https://github.com/Genymobile/scrcpy): espelhar e controlar um device Android via USB
(ou Wi-Fi), direto do computador.

O projeto **reutiliza o `scrcpy-server.jar` oficial** (lado Android, pré-compilado) e implementa
do zero, em Python, o cliente que fala o protocolo de socket do scrcpy, decodifica vídeo/áudio
via [PyAV](https://pyav.org/) e renderiza numa UI em QML.

## Funcionalidades

- **Espelhamento de tela** em tempo real (H.264 / H.265 / AV1¹), com resolução, bitrate e FPS
  máximo configuráveis
- **Áudio** do device (Opus / AAC / FLAC / PCM cru), tocado via `QAudioSink`
- **Controle completo**: toque/arraste com o mouse, teclado, scroll, Voltar/Home/Recentes,
  girar tela, ligar/desligar a tela do device, expandir notificações
- **Clipboard** bidirecional (copiar do device / colar no device)
- **Screenshot** (PNG) e **gravação de tela** (vídeo + áudio num `.mkv`, sem recodificar)
- **Inspetor de hierarquia**: árvore dos elementos da tela (`uiautomator dump`) ao lado do
  espelhamento, com as propriedades do elemento selecionado e o destaque dele sobre o vídeo
- **Grade de devices** com preview real (screenshot) e botão de play
- **Instalação de APK**: na grade, instala em todos os devices listados ao mesmo tempo (barra de
  progresso por device); no espelhamento, só no device ativo (anel de progresso no botão)
- Configurações persistidas localmente (SQLite): pasta de screenshots/gravações, codecs,
  stay-awake, show-touches, etc.

¹ AV1 depende do device suportar encode via hardware **e** do FFmpeg empacotado no PyAV ter um
decoder AV1 funcional — pode não decodificar dependendo do ambiente.

## Arquitetura

Segue o padrão **MVVM**:

- `models/` — dados puros expostos ao QML (ex.: `DeviceListModel`, um `QAbstractListModel`)
- `viewmodels/` — orquestram a lógica de negócio e expõem estado/comandos pro QML
  (`MirrorViewModel`, `DeviceListViewModel`, `SettingsViewModel`)
- `adb/`, `protocol/`, `video/`, `audio/`, `storage/` — camada de serviços (adbutils, protocolo
  do scrcpy, decode/encode de mídia, persistência)
- `qml/` — as Views (QML puro, só faz bind nos ViewModels)

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) para gerenciar o projeto e as dependências
- Um device Android com depuração USB habilitada (não precisa instalar o Android platform-tools
  separadamente — o [adbutils](https://pypi.org/project/adbutils/) já lida com o protocolo adb)
- Windows (ambiente testado até agora; Linux/macOS ainda não validados)

## Download (Windows)

Baixe o `.zip` da [página de releases](https://github.com/nson22/scrcpy_ui/releases), extraia
e abra `scrcpy-ui.exe`. Não precisa instalar Python nem o Android platform-tools.

## Rodando a partir do código

```sh
uv sync
uv run python -m scrcpy_ui
```

### Modo desenvolvimento (hot reload)

```sh
uv run scrcpy-ui-dev
```

- Salvar um `.qml` recarrega a interface na hora, sem fechar o app — mantém posição/tamanho da
  janela e, se houver um device espelhando, a sessão continua (a tela de espelhamento é reaberta).
  A navegação volta pra tela inicial a cada reload.
- Salvar um `.py` reinicia o app.
- Se o QML tiver erro, o erro aparece no terminal (arquivo:linha) e a versão anterior continua
  na tela.

## Gerando o executável

```sh
uv run pyinstaller scrcpy-ui.spec --noconfirm
```

A saída fica em `dist/scrcpy-ui/` (o `scrcpy-ui.exe` precisa das DLLs da mesma pasta).

## Estrutura do projeto

```
resources/
  fonts/            # Roboto + Material Symbols (ícones por nome, via ligadura)
  scrcpy-server/    # scrcpy-server.jar oficial (lado Android)
src/scrcpy_ui/
  adb/              # push do server, listagem de devices
  audio/            # decode (opus/aac/flac) e playback (QAudioSink)
  input/            # mapeamento mouse/teclado -> protocolo Android
  models/
  protocol/         # handshake, framing de pacotes, mensagens de controle
  qml/
  storage/          # SQLite de configurações
  video/            # decode (h264/h265/av1) e gravação (remux pra .mkv)
  viewmodels/
```

## Status

Em desenvolvimento ativo. O protocolo e os formatos de mídia foram validados contra um device
real; recursos como OTG, gamepad, câmera, virtual display e empacotamento (instalador) ainda não
foram implementados.
