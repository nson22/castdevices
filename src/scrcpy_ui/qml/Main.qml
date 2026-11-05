import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material

ApplicationWindow {
    id: window
    width: 1100
    height: 760
    minimumWidth: 460
    minimumHeight: 480
    visible: true
    // O Qt acrescenta " - CastDevices" (applicationDisplayName); vazio = só o nome do app
    title: ""
    color: Theme.background

    // Controles nativos (Switch, ComboBox, Menu, Dialog...) herdam os tokens
    Material.theme: Theme.dark ? Material.Dark : Material.Light
    Material.accent: Theme.accent
    Material.background: Theme.surface
    Material.foreground: Theme.textPrimary

    Binding {
        target: Theme
        property: "mode"
        value: settingsViewModel.themeMode
    }

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: deviceGridComponent

        // Engine recriada com uma sessão já ativa (hot reload no modo --dev)
        Component.onCompleted: {
            if (mirrorViewModel.isConnected) {
                push(mirrorComponent, {}, StackView.Immediate)
            }
        }
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
            window.title = name
            stackView.push(mirrorComponent)
        }
        function onDisconnected() {
            window.title = ""
            stackView.pop(stackView.get(0))
        }
        function onErrorOccurred(message) {
            errorDialog.text = message
            errorDialog.open()
        }
    }

    Dialog {
        id: errorDialog
        property alias text: errorLabel.text

        anchors.centerIn: parent
        width: Math.min(parent.width - Theme.spacingXl * 2, 480)
        modal: true
        title: "Algo deu errado"
        standardButtons: Dialog.Ok

        Label {
            id: errorLabel
            width: parent.width
            color: Theme.textPrimary
            wrapMode: Text.WordWrap
        }
    }
}
