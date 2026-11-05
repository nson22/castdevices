import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

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

    Connections {
        target: apkInstallViewModel
        function onFinished(message, ok) {
            toast.show(message, ok)
        }
    }

    // 1) escolhe a APK -> 2) confirma -> instala em todos os devices listados
    FileDialog {
        id: apkFileDialog
        title: "Escolher APK"
        nameFilters: ["Pacotes Android (*.apk)"]
        onAccepted: {
            apkInstallViewModel.selectApk(selectedFile)
            if (apkInstallViewModel.apkName.length > 0) {
                installDialog.open()
            }
        }
    }

    Dialog {
        id: installDialog
        objectName: "installDialog"
        anchors.centerIn: parent
        width: Math.min(root.width - Theme.spacingXl * 2, 440)
        modal: true
        padding: Theme.spacingXl
        topPadding: Theme.spacingXl

        background: Rectangle {
            radius: Theme.radiusLg
            color: Theme.surface
            border.color: Theme.border
        }

        contentItem: ColumnLayout {
            spacing: Theme.spacingLg

            Label {
                text: "Instalar APK"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontTitle
                font.weight: Font.DemiBold
            }

            // Arquivo escolhido
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: fileRow.implicitHeight + Theme.spacingMd * 2
                radius: Theme.radiusMd
                color: Theme.surfaceAlt

                RowLayout {
                    id: fileRow
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: Theme.spacingMd

                    Text {
                        text: "android"
                        font.family: Theme.iconFont
                        font.pixelSize: 28
                        color: Theme.success
                    }
                    ColumnLayout {
                        spacing: 2
                        Layout.fillWidth: true
                        Label {
                            text: apkInstallViewModel.apkName
                            color: Theme.textPrimary
                            font.pixelSize: Theme.fontBody
                            font.weight: Font.DemiBold
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                        }
                        Label {
                            text: apkInstallViewModel.apkSize
                            color: Theme.textSecondary
                            font.pixelSize: Theme.fontCaption
                        }
                    }
                }
            }

            Label {
                text: "Será instalado em " + (grid.count === 1 ? "1 device listado" : grid.count + " devices listados")
                      + ". Se o app já existir, ele é atualizado mantendo os dados."
                color: Theme.textSecondary
                font.pixelSize: Theme.fontBody
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Theme.spacingSm
                spacing: Theme.spacingSm

                Item { Layout.fillWidth: true }
                Button {
                    text: "Cancelar"
                    flat: true
                    onClicked: installDialog.reject()
                }
                Button {
                    id: confirmInstall
                    objectName: "confirmInstall"
                    text: grid.count === 1 ? "Instalar" : "Instalar em " + grid.count
                    enabled: grid.count > 0
                    leftPadding: Theme.spacingLg
                    rightPadding: Theme.spacingLg
                    onClicked: installDialog.accept()

                    contentItem: Label {
                        text: confirmInstall.text
                        color: Theme.accentText
                        font.pixelSize: Theme.fontBody
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        implicitHeight: 36
                        radius: Theme.radiusSm
                        color: confirmInstall.down ? Qt.darker(Theme.accent, 1.15)
                             : confirmInstall.hovered ? Qt.lighter(Theme.accent, 1.08)
                             : Theme.accent
                    }
                }
            }
        }

        onAccepted: apkInstallViewModel.installOnAll()
    }

    // Resultado da instalação
    Label {
        id: toast
        property bool ok: true
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: Theme.spacingXl
        width: Math.min(implicitWidth, parent.width - Theme.spacingXl * 2)
        leftPadding: Theme.spacingLg
        rightPadding: Theme.spacingLg
        topPadding: Theme.spacingSm + 2
        bottomPadding: Theme.spacingSm + 2
        background: Rectangle { color: Theme.scrim; radius: Theme.radiusMd }
        color: toast.ok ? Theme.scrimText : "#ff8a8a"
        font.pixelSize: Theme.fontBody
        elide: Text.ElideRight
        opacity: 0
        visible: opacity > 0
        z: 10

        Behavior on opacity { NumberAnimation { duration: 200 } }

        Timer {
            id: toastTimer
            interval: 4000
            onTriggered: toast.opacity = 0
        }

        function show(message, ok) {
            toast.text = message
            toast.ok = ok
            toast.opacity = 1
            toastTimer.restart()
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
                objectName: "gridApkButton"
                iconName: "apk_install"
                tip: "Instalar APK em todos os devices"
                enabled: grid.count > 0
                onClicked: apkFileDialog.open()
            }
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
                                        font.variableAxes: ({ "FILL": 1 })
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

                            InstallProgressBar {
                                Layout.fillWidth: true
                                install: apkInstallViewModel.installs[cell.serial]
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
