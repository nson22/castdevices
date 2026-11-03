import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: root
    anchors.fill: parent

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
                    text: "←"
                    font.pixelSize: 18
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
        }

        Item { Layout.fillHeight: true }
    }

    FolderDialog {
        id: folderDialog
        title: "Escolher pasta para screenshots"
        onAccepted: settingsViewModel.setScreenshotDir(selectedFolder)
    }
}
