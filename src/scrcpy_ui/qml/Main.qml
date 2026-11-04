import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: window
    width: 480
    height: 860
    minimumWidth: 320
    visible: true
    title: "scrcpy-ui"
    color: "#121214"

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: deviceGridComponent
    }

    Component {
        id: deviceGridComponent
        DeviceGridView {}
    }

    Component {
        id: mirrorComponent
        MirrorView {}
    }

    Connections {
        target: mirrorViewModel
        function onConnected(name, w, h) {
            window.title = "scrcpy-ui — " + name
            stackView.push(mirrorComponent)
        }
        function onDisconnected() {
            window.title = "scrcpy-ui"
            stackView.pop(stackView.get(0))
        }
        function onErrorOccurred(message) {
            errorDialog.text = message
            errorDialog.open()
        }
    }

    Dialog {
        id: errorDialog
        anchors.centerIn: parent
        title: "Erro ao conectar"
        standardButtons: Dialog.Ok
        property alias text: errorLabel.text
        Label {
            id: errorLabel
            wrapMode: Text.WordWrap
        }
    }
}
