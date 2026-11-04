import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    Component.onCompleted: deviceListViewModel.refresh()

    Connections {
        target: deviceListViewModel
        function onSingleDeviceFound(serial) {
            if (settingsViewModel.autoConnectSingleDevice) {
                mirrorViewModel.connectToDevice(serial)
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AppBar {
            Layout.fillWidth: true
            title: "Dispositivos"
            subtitle: grid.count === 0 ? "Nenhum conectado"
                    : grid.count === 1 ? "1 conectado"
                    : grid.count + " conectados"

            IconButton {
                iconName: "refresh"
                tip: "Atualizar"
                onClicked: deviceListViewModel.refresh()
            }
        }

        Item {
            id: body
            Layout.fillWidth: true
            Layout.fillHeight: true

            GridView {
                id: grid

                // Container centralizado com max-width + colunas calculadas pela largura
                readonly property int minCellWidth: 200
                readonly property int availableWidth: Math.min(body.width - Theme.spacingXl * 2,
                                                                Theme.maxGridWidth)
                readonly property int columns: Math.max(1, Math.floor(availableWidth / minCellWidth))

                width: availableWidth
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.topMargin: Theme.spacingXl - Theme.spacingSm
                cellWidth: Math.floor(availableWidth / columns)
                cellHeight: Math.round(cellWidth * 1.25)
                clip: true
                model: deviceListViewModel.deviceListModel
                visible: count > 0

                delegate: Item {
                    id: cell
                    required property string serial
                    required property string deviceModel
                    required property int previewRevision

                    width: grid.cellWidth
                    height: grid.cellHeight

                    Rectangle {
                        id: card
                        anchors.fill: parent
                        anchors.margins: Theme.spacingSm
                        radius: Theme.radiusLg
                        color: area.containsMouse ? Theme.surfaceHover : Theme.surface
                        border.width: 1
                        border.color: area.containsMouse ? Theme.accent : Theme.border

                        Behavior on color { ColorAnimation { duration: 120 } }
                        Behavior on border.color { ColorAnimation { duration: 120 } }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: Theme.spacingMd
                            spacing: Theme.spacingMd

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: Theme.radiusMd
                                color: Theme.videoBackground

                                Image {
                                    anchors.fill: parent
                                    anchors.margins: Theme.spacingXs
                                    fillMode: Image.PreserveAspectFit
                                    asynchronous: true
                                    source: "image://devicepreviews/" + cell.serial + "/" + cell.previewRevision
                                }

                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 56
                                    height: 56
                                    radius: width / 2
                                    color: Theme.accent
                                    opacity: area.containsMouse ? 1 : 0.88
                                    scale: area.containsMouse ? 1.08 : 1

                                    Behavior on scale { NumberAnimation { duration: 120 } }

                                    Text {
                                        anchors.centerIn: parent
                                        text: "play_arrow"
                                        font.family: Theme.iconFont
                                        font.pixelSize: 32
                                        color: Theme.accentText
                                    }
                                }
                            }

                            ColumnLayout {
                                spacing: 2
                                Layout.fillWidth: true

                                Label {
                                    text: cell.deviceModel.length > 0 ? cell.deviceModel : cell.serial
                                    color: Theme.textPrimary
                                    font.pixelSize: Theme.fontBody
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: cell.deviceModel.length > 0 ? cell.serial : "Modelo desconhecido"
                                    color: Theme.textSecondary
                                    font.pixelSize: Theme.fontCaption
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        MouseArea {
                            id: area
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: mirrorViewModel.connectToDevice(cell.serial)
                        }
                    }
                }
            }

            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width - Theme.spacingXl * 2, 420)
                spacing: Theme.spacingMd
                visible: grid.count === 0

                Text {
                    text: "phonelink_off"
                    font.family: Theme.iconFont
                    font.pixelSize: 56
                    color: Theme.textSecondary
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: "Nenhum dispositivo encontrado"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontTitle
                    font.weight: Font.DemiBold
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: "Conecte um Android via USB com a depuração USB ativada e toque em Atualizar."
                    color: Theme.textSecondary
                    font.pixelSize: Theme.fontBody
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
                Button {
                    id: emptyRefresh
                    text: "Atualizar"
                    leftPadding: Theme.spacingXl
                    rightPadding: Theme.spacingXl
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: Theme.spacingSm
                    onClicked: deviceListViewModel.refresh()

                    contentItem: Label {
                        text: emptyRefresh.text
                        color: Theme.accentText
                        font.pixelSize: Theme.fontBody
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitHeight: 40
                        radius: Theme.radiusSm
                        color: emptyRefresh.down ? Qt.darker(Theme.accent, 1.15)
                             : emptyRefresh.hovered ? Qt.lighter(Theme.accent, 1.08)
                             : Theme.accent
                    }
                }
            }
        }
    }
}
