import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: root

    // Largura padrão dos controles da coluna direita (ComboBox, SpinBox...)
    readonly property int controlWidth: 220

    // "Tecla" com ícone + nome do comando do mouse (seção de ajuda)
    component MouseChip: Rectangle {
        id: chip
        property string iconName: "mouse"
        property string text

        // Largura mínima igual pra todos: alinham em coluna e, em janela
        // estreita, todos descem pra baixo do texto (ver SettingRow.stacked)
        implicitWidth: Math.max(150, chipRow.implicitWidth + Theme.spacingMd * 2)
        implicitHeight: 30
        radius: Theme.radiusSm
        color: Theme.surfaceAlt
        border.color: Theme.border

        RowLayout {
            id: chipRow
            anchors.centerIn: parent
            spacing: Theme.spacingXs

            Text {
                text: chip.iconName
                font.family: Theme.iconFont
                font.pixelSize: 18
                color: Theme.textSecondary
            }
            Label {
                text: chip.text
                color: Theme.textPrimary
                font.pixelSize: Theme.fontCaption
                font.weight: Font.DemiBold
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AppBar {
            Layout.fillWidth: true
            title: "Configurações"
            leading: IconButton {
                iconName: "arrow_back"
                tip: "Voltar"
                onClicked: root.StackView.view.pop()
            }
        }

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            // Container centralizado com max-width e padding (como um
            // `max-width: 760px; margin: 0 auto; padding: 32px 24px` no CSS)
            Item {
                width: scrollView.availableWidth
                implicitHeight: content.implicitHeight + Theme.spacingXxl * 2

                ColumnLayout {
                    id: content
                    width: Math.min(parent.width - Theme.spacingXl * 2, Theme.maxContentWidth)
                    x: (parent.width - width) / 2
                    y: Theme.spacingXxl
                    spacing: Theme.spacingLg

                    SettingsSection {
                        title: "Aparência"

                        SettingRow {
                            label: "Tema"
                            description: "\"Sistema\" acompanha o tema claro/escuro do Windows."
                            showDivider: false

                            ComboBox {
                                readonly property var values: ["system", "light", "dark"]
                                Layout.preferredWidth: root.controlWidth
                                Layout.fillWidth: true
                                model: ["Sistema", "Claro", "Escuro"]
                                currentIndex: Math.max(0, values.indexOf(settingsViewModel.themeMode))
                                onActivated: settingsViewModel.themeMode = values[currentIndex]
                            }
                        }
                    }

                    SettingsSection {
                        title: "Conexão"
                        description: "Mudanças aqui valem a partir da próxima conexão."

                        SettingRow {
                            label: "Abrir automaticamente com um único device"
                            description: "Quando só um device estiver conectado, abre o espelhamento dele direto, sem passar pela grade."
                            showDivider: false

                            Switch {
                                checked: settingsViewModel.autoConnectSingleDevice
                                onToggled: settingsViewModel.autoConnectSingleDevice = checked
                            }
                        }
                        SettingRow {
                            label: "Manter o device acordado"
                            description: "Impede que a tela do device apague enquanto espelhado."

                            Switch {
                                checked: settingsViewModel.stayAwake
                                onToggled: settingsViewModel.stayAwake = checked
                            }
                        }
                        SettingRow {
                            label: "Mostrar toques"
                            description: "Exibe um indicador visual onde você toca no device."

                            Switch {
                                checked: settingsViewModel.showTouches
                                onToggled: settingsViewModel.showTouches = checked
                            }
                        }
                    }

                    SettingsSection {
                        title: "Vídeo"
                        description: "h265 e av1 dependem de encoder de hardware no device; se não houver, a conexão falha."

                        SettingRow {
                            label: "Codec"
                            showDivider: false

                            ComboBox {
                                Layout.preferredWidth: root.controlWidth
                                Layout.fillWidth: true
                                model: ["h264", "h265", "av1"]
                                currentIndex: Math.max(0, model.indexOf(settingsViewModel.videoCodec))
                                onActivated: settingsViewModel.videoCodec = model[currentIndex]
                            }
                        }
                        SettingRow {
                            label: "Resolução máxima"
                            description: "Limita o maior lado da imagem. Valores menores reduzem latência."

                            ComboBox {
                                readonly property var values: [0, 1920, 1280, 1024, 800, 640]
                                Layout.preferredWidth: root.controlWidth
                                Layout.fillWidth: true
                                model: ["Nativa", "1920 px", "1280 px", "1024 px", "800 px", "640 px"]
                                currentIndex: Math.max(0, values.indexOf(settingsViewModel.maxSize))
                                onActivated: settingsViewModel.maxSize = values[currentIndex]
                            }
                        }
                        SettingRow {
                            label: "Bitrate (Mbps)"

                            SpinBox {
                                Layout.preferredWidth: root.controlWidth
                                Layout.fillWidth: true
                                from: 1
                                to: 50
                                editable: true
                                value: settingsViewModel.videoBitRate / 1000000
                                onValueModified: settingsViewModel.videoBitRate = value * 1000000
                            }
                        }
                        SettingRow {
                            label: "FPS máximo"

                            ComboBox {
                                readonly property var values: [0, 30, 60]
                                Layout.preferredWidth: root.controlWidth
                                Layout.fillWidth: true
                                model: ["Sem limite", "30", "60"]
                                currentIndex: Math.max(0, values.indexOf(settingsViewModel.maxFps))
                                onActivated: settingsViewModel.maxFps = values[currentIndex]
                            }
                        }
                    }

                    SettingsSection {
                        title: "Áudio"
                        description: "Requer Android 11 ou superior."

                        SettingRow {
                            label: "Transmitir áudio do device"
                            showDivider: false

                            Switch {
                                checked: settingsViewModel.audioEnabled
                                onToggled: settingsViewModel.audioEnabled = checked
                            }
                        }
                        SettingRow {
                            label: "Codec"
                            description: "opus é o mais leve; raw não comprime (mais qualidade, mais banda)."
                            enabled: settingsViewModel.audioEnabled
                            opacity: enabled ? 1 : 0.5

                            ComboBox {
                                Layout.preferredWidth: root.controlWidth
                                Layout.fillWidth: true
                                model: ["opus", "aac", "flac", "raw"]
                                currentIndex: Math.max(0, model.indexOf(settingsViewModel.audioCodec))
                                onActivated: settingsViewModel.audioCodec = model[currentIndex]
                            }
                        }
                    }

                    SettingsSection {
                        title: "Armazenamento"

                        SettingRow {
                            label: "Pasta de screenshots"
                            description: settingsViewModel.screenshotDir
                            showDivider: false

                            Button {
                                text: "Alterar…"
                                flat: true
                                onClicked: screenshotFolderDialog.open()
                            }
                        }
                        SettingRow {
                            label: "Pasta de gravações (.mkv)"
                            description: settingsViewModel.recordingDir

                            Button {
                                text: "Alterar…"
                                flat: true
                                onClicked: recordingFolderDialog.open()
                            }
                        }
                    }

                    SettingsSection {
                        title: "Comandos do mouse"
                        description: "Como o mouse controla o device na tela de espelhamento."

                        SettingRow {
                            label: "Tocar e arrastar"
                            description: "Um clique é um toque na tela. Segure e arraste para deslizar (swipe), rolar listas ou arrastar itens; segurar parado faz um toque longo."
                            showDivider: false

                            MouseChip { text: "Clique esquerdo" }
                        }
                        SettingRow {
                            label: "Voltar"
                            description: "Mesmo que o botão Voltar do Android."

                            MouseChip { text: "Clique direito" }
                        }
                        SettingRow {
                            label: "Tela inicial (Home)"
                            description: "Mesmo que o botão Home do Android."

                            MouseChip { text: "Clique na roda" }
                        }
                        SettingRow {
                            label: "Rolar"
                            description: "Rola o conteúdo sob o cursor. Roda horizontal ou touchpad rolam para os lados."

                            MouseChip { iconName: "swap_vert"; text: "Roda do mouse" }
                        }
                    }
                }
            }
        }
    }

    FolderDialog {
        id: screenshotFolderDialog
        title: "Escolher pasta para screenshots"
        onAccepted: settingsViewModel.setScreenshotDir(selectedFolder)
    }

    FolderDialog {
        id: recordingFolderDialog
        title: "Escolher pasta para gravações"
        onAccepted: settingsViewModel.setRecordingDir(selectedFolder)
    }
}
