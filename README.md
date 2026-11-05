<p align="center">
  <img src="resources/icons/scrcpy-ui.png" width="128" alt="Ícone do SCRCPY UI">
</p>

<h1 align="center">SCRCPY UI</h1>

<p align="center">
  Espelhe e controle devices Android pelo computador — Windows, macOS e Linux.<br>
  <a href="https://github.com/nson22/scrcpy_ui/releases/latest"><b>Baixar a última versão</b></a>
</p>

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
- **Controle completo** pelo mouse e teclado: toque, arraste, toque longo, scroll, Voltar
  (clique direito) e Home (clique na roda) — ver [Comandos do mouse](#comandos-do-mouse)
- **Ações do device** na barra superior: girar tela, ligar/desligar a tela, expandir notificações
- **Clipboard** bidirecional (copiar do device / colar no device)
- **Screenshot** (PNG) e **gravação de tela** (vídeo + áudio num `.mkv`, sem recodificar)
- **Inspetor de hierarquia**: árvore dos elementos da tela (`uiautomator dump`) ao lado do
  espelhamento (divisão 50/50), com as propriedades do elemento selecionado e o destaque dele
  sobre o vídeo. **Atualiza sozinho quando a tela do device muda** (espera a tela parar de
  animar) e mantém o elemento selecionado se ele continuar na tela. Cada propriedade tem um
  botão de copiar (no `resource-id`, copia só o nome depois da `/`). Abre junto com o
  espelhamento por padrão (configurável)
- **Grade de devices** com preview real (screenshot) e botão de play
- **Instalação de APK**: na grade, instala em todos os devices listados ao mesmo tempo (barra de
  progresso verde por device); no espelhamento, só no device ativo (anel de progresso verde no
  botão). Se o app já existir, é atualizado mantendo os dados
- **Desinstalação de apps**: painel lateral com os apps instalados pelo usuário (nome + pacote),
  busca, seleção de um ou vários apps e confirmação com aviso. Por padrão apaga também os dados
  do app; em Configurações dá pra manter os dados. Apps do sistema não aparecem na lista
- **Estados de carregamento** com skeleton (estilo [shadcn/ui](https://ui.shadcn.com/docs/components/base/skeleton))
  na grade de devices e no inspetor
- **Abrir automaticamente** o espelhamento quando há um único device conectado (opcional,
  desligado por padrão)
- Configurações persistidas localmente (SQLite): tema claro/escuro/sistema, pasta de
  screenshots/gravações, codecs, resolução, bitrate, FPS, stay-awake, show-touches, etc.

¹ AV1 depende do device suportar encode via hardware **e** do FFmpeg empacotado no PyAV ter um
decoder AV1 funcional — pode não decodificar dependendo do ambiente.

## Uso

1. Conecte o device via USB com a **depuração USB** ativada (aceite o aviso de autorização no
   device na primeira vez).
2. Na grade de **Dispositivos**, clique no card do device para abrir o espelhamento.
3. A barra superior do espelhamento tem as ações do device, clipboard, instalação de APK,
   gravação/screenshot, o inspetor de hierarquia, as configurações e o botão de desconectar.

### Comandos do mouse

| Mouse | Ação no device |
|---|---|
| Clique esquerdo | Toque. Segure e arraste para deslizar (swipe); segurar parado é toque longo |
| Clique direito | Voltar |
| Clique na roda | Home |
| Roda do mouse | Rolar o conteúdo sob o cursor (roda horizontal/touchpad rolam para os lados) |

Essa tabela também está em **Configurações → Comandos do mouse**.

### Instalar APK

- **Em vários devices**: na grade, clique no ícone de APK na barra superior, escolha o arquivo e
  confirme — instala em todos os devices listados, cada um com sua barra de progresso.
- **No device aberto**: no espelhamento, clique no ícone de APK e escolha o arquivo — instala só
  nesse device, com o progresso num anel em volta do ícone.

## Arquitetura

Segue o padrão **MVVM**:

- `models/` — dados puros expostos ao QML (ex.: `DeviceListModel`, um `QAbstractListModel`)
- `viewmodels/` — orquestram a lógica de negócio e expõem estado/comandos pro QML
  (`MirrorViewModel`, `DeviceListViewModel`, `SettingsViewModel`, `InspectorViewModel`,
  `ApkInstallViewModel`, `AppManagerViewModel`)
- `adb/`, `protocol/`, `video/`, `audio/`, `storage/` — camada de serviços (adbutils, protocolo
  do scrcpy, decode/encode de mídia, persistência)
- `qml/` — as Views (QML puro, só faz bind nos ViewModels)

## Download

Na [página de releases](https://github.com/nson22/scrcpy_ui/releases/latest). Não precisa instalar
Python nem o Android platform-tools: o **adb oficial já vem junto**, na mesma versão usada pelo
scrcpy (platform-tools 37.0.0). O device precisa estar com a **depuração USB** ativada.

| Sistema | Arquivo | Como usar |
|---|---|---|
| Windows | `scrcpy-ui-<versão>-win64.zip` | Extraia e abra `scrcpy-ui.exe` |
| macOS (Apple Silicon) | `scrcpy-ui-<versão>-macos-arm64.dmg` | Abra o `.dmg` e arraste o **SCRCPY UI** para Aplicativos |
| Linux (x86_64) | `scrcpy-ui-<versão>-linux-x86_64.tar.gz` | Extraia e rode `./scrcpy-ui`, ou `./install.sh` para criar o atalho no menu |

**macOS:** o app ainda não é assinado pela Apple. Na primeira vez, o macOS bloqueia a abertura.
Clique com o botão direito no app → **Abrir**, ou rode
`xattr -dr com.apple.quarantine "/Applications/SCRCPY UI.app"` no Terminal.

**Linux:** precisa de uma distro com glibc 2.35 ou mais nova (Ubuntu 22.04+, Debian 12+,
Fedora 36+). Para acessar o device via USB sem root, pode ser preciso configurar as regras
`udev` do Android (pacote `android-sdk-platform-tools-common` no Debian/Ubuntu).

## Requisitos (para rodar o código)

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) para gerenciar o projeto e as dependências
- Um device Android com depuração USB habilitada

## Rodando a partir do código

```sh
uv sync
uv run python packaging/fetch_adb.py   # adb oficial fixado (uma vez; opcional no dev)
uv run python -m scrcpy_ui
```

Sem o `fetch_adb.py`, o app usa o `adb` que o [adbutils](https://pypi.org/project/adbutils/) traz
(Windows) ou o `adb` do PATH (macOS/Linux).

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

Sempre no próprio sistema (o PyInstaller não faz build cruzado):

```sh
uv run python packaging/fetch_adb.py      # adb oficial (versão fixada + SHA-256)
uv run pyinstaller scrcpy-ui.spec --noconfirm
```

A saída fica em `dist/scrcpy-ui/` no Windows/Linux e em `dist/SCRCPY UI.app` no macOS.

O ícone vem de `resources/icons/scrcpy-ui.svg`; depois de editar o SVG, gere os PNG/ICO/ICNS com
`uv run python packaging/make_icons.py`.

## Release

Os releases são gerados pelo GitHub Actions ([`release.yml`](.github/workflows/release.yml)) a partir
da `main`:

1. Atualize a versão no `pyproject.toml` (e opcionalmente escreva as notas em
   `packaging/release-notes/<tag>.md`).
2. Crie e envie a tag: `git tag -a v0.0.4-alpha -m v0.0.4-alpha && git push origin v0.0.4-alpha`.
3. O workflow builda Windows, macOS e Linux, roda um smoke test em cada pacote e publica tudo no
   release da tag.

Rodar o workflow manualmente (Actions → Release → Run workflow) sem tag só builda e testa — os
pacotes ficam como artifacts da execução.

## Estrutura do projeto

```
.github/workflows/  # release multiplataforma (GitHub Actions)
packaging/          # entry do PyInstaller, fetch do adb, ícones, smoke test, extras do Linux
resources/
  fonts/            # Roboto + Material Symbols (ícones por nome, via ligadura)
  icons/            # ícone do app (SVG fonte + PNG/ICO/ICNS gerados)
  scrcpy-server/    # scrcpy-server.jar oficial (lado Android)
src/scrcpy_ui/
  adb/              # push do server, listagem de devices, instalação de APK, apps instalados
  audio/            # decode (opus/aac/flac) e playback (QAudioSink)
  input/            # mapeamento mouse/teclado -> protocolo Android
  models/           # lista de devices, árvore de hierarquia da tela
  protocol/         # handshake, framing de pacotes, mensagens de controle
  qml/              # Views + componentes (Theme, AppBar, Skeleton, ...)
  storage/          # SQLite de configurações
  video/            # decode (h264/h265/av1), gravação (remux pra .mkv), detecção de mudança de tela
  viewmodels/
```

## Status

Em desenvolvimento ativo (alpha). O protocolo e os formatos de mídia foram validados contra um
device real; recursos como OTG, gamepad, câmera, virtual display, gerenciamento de janela e
instalador ainda não foram implementados. O uso com device real foi validado no Windows; os pacotes
de macOS e Linux passam por um smoke test automático no CI a cada release.
