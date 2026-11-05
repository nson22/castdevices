import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia

Item {
    id: root

    Component {
        id: settingsComponent
        SettingsView {}
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        AppBar {
            Layout.fillWidth: true

            // Ações no device
            IconButton {
                iconName: "mobile_rotate"
                tip: "Girar tela"
                onClicked: mirrorViewModel.rotateDevice()
            }
            IconButton {
                iconName: mirrorViewModel.screenOn ? "tv_off" : "tv"
                tip: mirrorViewModel.screenOn ? "Desligar tela" : "Ligar tela"
                onClicked: mirrorViewModel.toggleScreenPower()
            }
            IconButton {
                iconName: "expand_circle_down"
                tip: "Expandir notificações"
                onClicked: mirrorViewModel.expandNotifications()
            }

            AppBarSeparator {}

            // Clipboard
            IconButton {
                iconName: "content_copy"
                tip: "Copiar clipboard do device"
                onClicked: mirrorViewModel.copyClipboardFromDevice()
            }
            IconButton {
                iconName: "content_paste"
                tip: "Colar clipboard no device"
                onClicked: mirrorViewModel.pasteClipboardToDevice()
            }

            AppBarSeparator {}

            // Captura
            IconButton {
                iconName: mirrorViewModel.isRecording ? "stop" : "fiber_manual_record"
                iconColor: mirrorViewModel.isRecording ? Theme.danger : Theme.textPrimary
                filled: true
                tip: mirrorViewModel.isRecording ? "Parar gravação" : "Gravar tela"
                onClicked: mirrorViewModel.toggleRecording()
            }
            IconButton {
                iconName: "photo_camera"
                tip: "Screenshot"
                onClicked: mirrorViewModel.takeScreenshot()
            }

            AppBarSeparator {}

            IconButton {
                id: inspectorToggle
                objectName: "inspectorToggle"
                iconName: "account_tree"
                tip: checked ? "Ocultar hierarquia da tela" : "Mostrar hierarquia da tela"
                checkable: true
                onToggled: {
                    if (checked) {
                        // Abre dividindo a área meio a meio com o vídeo
                        inspectorPanel.SplitView.preferredWidth = split.width / 2
                    }
                    // Ativo: captura agora e recaptura quando a tela do device mudar
                    inspectorViewModel.active = checked
                }
            }
            IconButton {
                iconName: "settings"
                tip: "Configurações"
                onClicked: root.StackView.view.push(settingsComponent)
            }
            IconButton {
                iconName: "power_settings_new"
                tip: "Desconectar"
                onClicked: mirrorViewModel.disconnectDevice()
            }
        }

        SplitView {
            id: split
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            handle: Rectangle {
                implicitWidth: 4
                color: SplitHandle.pressed || SplitHandle.hovered ? Theme.accent : Theme.border
            }

            Rectangle {
                id: videoArea
                SplitView.fillWidth: true
                SplitView.minimumWidth: 240
                color: Theme.videoBackground
                focus: true

                VideoOutput {
                    id: videoOutput
                    anchors.fill: parent
                    fillMode: VideoOutput.PreserveAspectFit

                    onContentRectChanged: mirrorViewModel.setContentRect(contentRect.x, contentRect.y, contentRect.width, contentRect.height)

                    Component.onCompleted: mirrorViewModel.attachVideoSink(videoOutput.videoSink)
                }

                MouseArea {
                    id: mouseArea
                    anchors.fill: videoOutput
                    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                    hoverEnabled: false

                    // Android não tem um gesto nativo de "clique direito"/"clique do meio"
                    // sobre toque -- só o botão esquerdo gera um toque de fato (down/move/up).
                    // Direito e meio disparam Voltar/Home (mesmo default do scrcpy original).
                    property bool touchActive: false

                    onPressed: function (mouse) {
                        videoArea.forceActiveFocus()
                        if (mouse.button === Qt.RightButton) {
                            mirrorViewModel.sendBack()
                        } else if (mouse.button === Qt.MiddleButton) {
                            mirrorViewModel.sendHome()
                        } else {
                            touchActive = true
                            mirrorViewModel.sendMousePress(mouse.x, mouse.y, mouse.buttons)
                        }
                    }
                    onPositionChanged: function (mouse) {
                        if (touchActive) {
                            mirrorViewModel.sendMouseMove(mouse.x, mouse.y, mouse.buttons)
                        }
                    }
                    onReleased: function (mouse) {
                        if (touchActive && mouse.button === Qt.LeftButton) {
                            touchActive = false
                            mirrorViewModel.sendMouseRelease(mouse.x, mouse.y, mouse.buttons)
                        }
                    }
                    onWheel: function (wheel) {
                        mirrorViewModel.sendWheel(wheel.x, wheel.y, wheel.angleDelta.x / 8, wheel.angleDelta.y / 8)
                    }
                }

                // Destaque do elemento selecionado na árvore. Os bounds vêm em pixels
                // físicos da tela do device; o vídeo pode estar reduzido (resolução
                // máxima), então converte pela proporção da área do vídeo.
                Rectangle {
                    readonly property rect bounds: inspectorViewModel.selectedBounds
                    readonly property real sx: videoOutput.contentRect.width / Math.max(1, inspectorViewModel.screenWidth)
                    readonly property real sy: videoOutput.contentRect.height / Math.max(1, inspectorViewModel.screenHeight)

                    visible: inspectorToggle.checked && inspectorViewModel.hasSelection
                    x: videoOutput.contentRect.x + bounds.x * sx
                    y: videoOutput.contentRect.y + bounds.y * sy
                    width: bounds.width * sx
                    height: bounds.height * sy
                    color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.2)
                    border.color: Theme.accent
                    border.width: 2
                }

                Keys.onPressed: function (event) {
                    mirrorViewModel.sendKey(event.key, true)
                    event.accepted = true
                }
                Keys.onReleased: function (event) {
                    mirrorViewModel.sendKey(event.key, false)
                    event.accepted = true
                }

                // Indicador de gravação
                Rectangle {
                    visible: mirrorViewModel.isRecording
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.margins: Theme.spacingMd
                    height: 28
                    width: recRow.implicitWidth + Theme.spacingMd * 2
                    radius: height / 2
                    color: Theme.scrim

                    RowLayout {
                        id: recRow
                        anchors.centerIn: parent
                        spacing: Theme.spacingSm

                        Rectangle {
                            width: 10
                            height: 10
                            radius: 5
                            color: Theme.danger

                            SequentialAnimation on opacity {
                                running: mirrorViewModel.isRecording
                                loops: Animation.Infinite
                                NumberAnimation { to: 0.3; duration: 700 }
                                NumberAnimation { to: 1; duration: 700 }
                            }
                        }
                        Label {
                            text: "Gravando"
                            color: Theme.scrimText
                            font.pixelSize: Theme.fontCaption
                            font.weight: Font.DemiBold
                        }
                    }
                }

                // Toast
                Label {
                    id: toast
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottomMargin: Theme.spacingXl
                    width: Math.min(implicitWidth, parent.width - Theme.spacingXl * 2)
                    leftPadding: Theme.spacingLg
                    rightPadding: Theme.spacingLg
                    topPadding: Theme.spacingSm + 2
                    bottomPadding: Theme.spacingSm + 2
                    background: Rectangle { color: Theme.scrim; radius: Theme.radiusMd }
                    color: Theme.scrimText
                    font.pixelSize: Theme.fontBody
                    elide: Text.ElideMiddle
                    opacity: 0
                    visible: opacity > 0
                    z: 10

                    Behavior on opacity { NumberAnimation { duration: 200 } }

                    Timer {
                        id: hideTimer
                        interval: 2600
                        onTriggered: toast.opacity = 0
                    }

                    function show(message) {
                        toast.text = message
                        toast.opacity = 1
                        hideTimer.restart()
                    }
                }
            }

            InspectorPanel {
                id: inspectorPanel
                visible: inspectorToggle.checked
                SplitView.preferredWidth: 380
                SplitView.minimumWidth: 280
            }
        }
    }

    // Saiu da tela (desconectou, ou engine recriada no hot reload): para a recaptura
    Component.onDestruction: inspectorViewModel.active = false

    Connections {
        target: mirrorViewModel
        function onScreenshotSaved(path) {
            toast.show("Screenshot salvo em " + path)
        }
        function onRecordingSaved(path) {
            toast.show("Gravação salva em " + path)
        }
    }
}
