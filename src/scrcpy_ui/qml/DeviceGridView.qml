import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    anchors.fill: parent

    Component.onCompleted: deviceListViewModel.refresh()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Label {
                text: "Devices"
                font.pixelSize: 20
                font.bold: true
                Layout.fillWidth: true
            }
            Button {
                text: "Atualizar"
                onClicked: deviceListViewModel.refresh()
            }
        }

        GridView {
            id: gridView
            Layout.fillWidth: true
            Layout.fillHeight: true
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
                            anchors.horizontalCenterOffset: 2
                            text: "▶"
                            color: "white"
                            font.pixelSize: 22
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
