import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    anchors.fill: parent

    Component.onCompleted: deviceListViewModel.refresh()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: topBar
            Layout.fillWidth: true
            height: 40
            color: "#1b1b1f"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 4

                Label {
                    text: "Devices"
                    font.pixelSize: 16
                    font.bold: true
                    Layout.fillWidth: true
                }
                ToolButton {
                    text: "refresh"
                    font.family: "Material Icons"
                    font.pixelSize: 22
                    ToolTip.text: "Atualizar"
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    onClicked: deviceListViewModel.refresh()
                }
            }
        }

        GridView {
            id: gridView
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 16
            clip: true
            cellWidth: 170
            cellHeight: 280
            model: deviceListViewModel.deviceListModel

            delegate: Item {
                id: delegateRoot
                required property string serial
                required property string deviceModel
                required property int previewRevision

                width: gridView.cellWidth
                height: gridView.cellHeight

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 8
                    radius: 8
                    color: "#1b1b1f"
                    border.color: "#333338"

                    Image {
                        id: preview
                        anchors.fill: parent
                        anchors.margins: 1
                        fillMode: Image.PreserveAspectFit
                        source: "image://devicepreviews/" + delegateRoot.serial + "/" + delegateRoot.previewRevision
                        asynchronous: true
                    }

                    Rectangle {
                        anchors.centerIn: parent
                        width: 56
                        height: 56
                        radius: width / 2
                        color: "#000000"
                        opacity: playArea.containsMouse ? 0.75 : 0.55

                        Text {
                            anchors.centerIn: parent
                            text: "play_arrow"
                            font.family: "Material Icons"
                            color: "white"
                            font.pixelSize: 28
                        }
                    }

                    MouseArea {
                        id: playArea
                        hoverEnabled: true
                        anchors.fill: parent
                        onClicked: mirrorViewModel.connectToDevice(delegateRoot.serial)
                    }

                    Label {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 6
                        elide: Text.ElideRight
                        horizontalAlignment: Text.AlignHCenter
                        text: delegateRoot.deviceModel.length > 0 ? delegateRoot.deviceModel : delegateRoot.serial
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                visible: gridView.count === 0
                horizontalAlignment: Text.AlignHCenter
                text: "Nenhum device encontrado.\nConecte via USB com depuração habilitada."
            }
        }
    }
}
