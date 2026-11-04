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

        ColumnLayout {
            Layout.fillWidth: true
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
        }

        Item { Layout.fillHeight: true }
    }

    FolderDialog {
        id: folderDialog
        title: "Escolher pasta para screenshots"
        onAccepted: settingsViewModel.setScreenshotDir(selectedFolder)
    }
}
