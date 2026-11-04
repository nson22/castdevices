import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "#1b1b1f"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 4
                spacing: 8

                ToolButton {
                    text: "arrow_back"
                    font.family: "Material Icons"
                    font.pixelSize: 22
                    ToolTip.text: "Voltar"
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    onClicked: root.StackView.view.pop()
                }
                Label {
                    text: "Configurações"
                    font.bold: true
                    font.pixelSize: 16
                }
            }
        }

        ScrollView {
            id: scrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            ColumnLayout {
                width: scrollView.availableWidth
                Layout.margins: 16
                spacing: 8

                Label {
                    text: "Pasta para salvar screenshots"
                    font.bold: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextField {
                        id: pathField
                        Layout.fillWidth: true
                        readOnly: true
                        text: settingsViewModel.screenshotDir
                    }
                    Button {
                        text: "Escolher..."
                        onClicked: folderDialog.open()
                    }
                }

                Label {
                    text: "Pasta para salvar gravações (.mkv)"
                    font.bold: true
                    Layout.topMargin: 16
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    TextField {
                        id: recordingPathField
                        Layout.fillWidth: true
                        readOnly: true
                        text: settingsViewModel.recordingDir
                    }
                    Button {
                        text: "Escolher..."
                        onClicked: recordingFolderDialog.open()
                    }
                }

                Label {
                    text: "Conexão"
                    font.bold: true
                    Layout.topMargin: 16
                }

                Switch {
                    text: "Manter o device sempre acordado enquanto espelhado"
                    checked: settingsViewModel.stayAwake
                    onToggled: settingsViewModel.stayAwake = checked
                }
                Switch {
                    text: "Mostrar indicador visual de toques no device"
                    checked: settingsViewModel.showTouches
                    onToggled: settingsViewModel.showTouches = checked
                }
                Label {
                    text: "Essas duas opções só têm efeito na próxima conexão."
                    font.italic: true
                    opacity: 0.7
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Label {
                    text: "Vídeo"
                    font.bold: true
                    Layout.topMargin: 16
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label { text: "Codec:" }
                    ComboBox {
                        id: videoCodecCombo
                        Layout.fillWidth: true
                        model: ["h264", "h265", "av1"]
                        currentIndex: model.indexOf(settingsViewModel.videoCodec)
                        onActivated: settingsViewModel.videoCodec = model[currentIndex]
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label { text: "Resolução máx.:" }
                    ComboBox {
                        id: maxSizeCombo
                        Layout.fillWidth: true
                        readonly property var sizeValues: [0, 1920, 1280, 1024, 800, 640]
                        model: ["Nativa (sem limite)", "1920", "1280", "1024", "800", "640"]
                        currentIndex: Math.max(0, sizeValues.indexOf(settingsViewModel.maxSize))
                        onActivated: settingsViewModel.maxSize = sizeValues[currentIndex]
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label { text: "Bitrate (Mbps):" }
                    SpinBox {
                        id: bitRateSpin
                        Layout.fillWidth: true
                        from: 1
                        to: 50
                        value: settingsViewModel.videoBitRate / 1000000
                        onValueModified: settingsViewModel.videoBitRate = value * 1000000
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label { text: "FPS máx.:" }
                    ComboBox {
                        id: maxFpsCombo
                        Layout.fillWidth: true
                        readonly property var fpsValues: [0, 30, 60]
                        model: ["Sem limite", "30", "60"]
                        currentIndex: Math.max(0, fpsValues.indexOf(settingsViewModel.maxFps))
                        onActivated: settingsViewModel.maxFps = fpsValues[currentIndex]
                    }
                }
                Label {
                    text: "h265/av1 dependem de suporte de hardware do device " +
                          "(encoder) -- se não tiver, a conexão vai falhar. Essas " +
                          "opções só têm efeito na próxima conexão."
                    font.italic: true
                    opacity: 0.7
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Label {
                    text: "Áudio"
                    font.bold: true
                    Layout.topMargin: 16
                }

                Switch {
                    text: "Transmitir áudio do device"
                    checked: settingsViewModel.audioEnabled
                    onToggled: settingsViewModel.audioEnabled = checked
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    enabled: settingsViewModel.audioEnabled

                    Label { text: "Codec:" }
                    ComboBox {
                        id: audioCodecCombo
                        Layout.fillWidth: true
                        model: ["opus", "aac", "flac", "raw"]
                        currentIndex: model.indexOf(settingsViewModel.audioCodec)
                        onActivated: settingsViewModel.audioCodec = model[currentIndex]
                    }
                }
                Label {
                    text: "Áudio só é suportado em Android 11+. \"opus\" é o mais leve; " +
                          "\"raw\" não comprime (mais qualidade, mais banda). Efeito só na próxima conexão."
                    font.italic: true
                    opacity: 0.7
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }

    FolderDialog {
        id: folderDialog
        title: "Escolher pasta para screenshots"
        onAccepted: settingsViewModel.setScreenshotDir(selectedFolder)
    }

    FolderDialog {
        id: recordingFolderDialog
        title: "Escolher pasta para gravações"
        onAccepted: settingsViewModel.setRecordingDir(selectedFolder)
    }
}
