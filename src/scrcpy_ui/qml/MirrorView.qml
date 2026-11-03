import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia

Item {
    id: root
    anchors.fill: parent

    Component {
        id: settingsComponent
        SettingsView {}
    }

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
                anchors.leftMargin: 4
                anchors.rightMargin: 4
                spacing: 0

                Item { Layout.fillWidth: true }

                ToolButton {
                    text: "photo_camera"
                    font.family: "Material Icons"
                    font.pixelSize: 22
                    ToolTip.text: "Screenshot"
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    onClicked: mirrorViewModel.takeScreenshot()
                }
                ToolButton {
                    text: "settings"
                    font.family: "Material Icons"
                    font.pixelSize: 22
                    ToolTip.text: "Configurações"
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    onClicked: root.StackView.view.push(settingsComponent)
                }
                ToolButton {
                    text: "power_settings_new"
                    font.family: "Material Icons"
                    font.pixelSize: 22
                    ToolTip.text: "Desconectar"
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    onClicked: mirrorViewModel.disconnectDevice()
                }
            }
        }

        Item {
            id: videoArea
            Layout.fillWidth: true
            Layout.fillHeight: true
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

            Keys.onPressed: function (event) {
                mirrorViewModel.sendKey(event.key, true)
                event.accepted = true
            }
            Keys.onReleased: function (event) {
                mirrorViewModel.sendKey(event.key, false)
                event.accepted = true
            }
        }
    }

    Label {
        id: toast
        anchors.top: topBar.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 8
        padding: 8
        background: Rectangle { color: "#cc000000"; radius: 6 }
        color: "white"
        opacity: 0
        visible: opacity > 0
        z: 10

        Behavior on opacity { NumberAnimation { duration: 200 } }

        Timer {
            id: hideTimer
            interval: 2200
            onTriggered: toast.opacity = 0
        }

        function show(message) {
            toast.text = message
            toast.opacity = 1
            hideTimer.restart()
        }
    }

    Connections {
        target: mirrorViewModel
        function onScreenshotSaved(path) {
            toast.show("Screenshot salvo em " + path)
        }
    }
}
