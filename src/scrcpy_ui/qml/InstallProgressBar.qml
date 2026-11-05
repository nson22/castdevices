import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Progresso de instalação de APK de um device (card da grade): barra verde +
// status. `install` é a entrada de apkInstallViewModel.installs[serial]
// ({progress, phase, message}) ou undefined quando não há instalação.
ColumnLayout {
    id: root

    property var install

    readonly property string phase: install ? install.phase : ""
    readonly property real progress: install ? install.progress : 0

    visible: phase.length > 0
    spacing: Theme.spacingXs

    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 6
        radius: 3
        color: Theme.surfaceAlt

        Rectangle {
            width: parent.width * (root.phase === "error" ? 1 : Math.min(1, root.progress))
            height: parent.height
            radius: parent.radius
            color: root.phase === "error" ? Theme.danger : Theme.success

            Behavior on width { NumberAnimation { duration: 160 } }
        }
    }

    Label {
        Layout.fillWidth: true
        text: root.phase === "uploading" ? "Enviando APK… " + Math.round(root.progress * 100) + "%"
            : root.phase === "installing" ? "Instalando… " + Math.round(root.progress * 100) + "%"
            : root.phase === "done" ? "Instalado"
            : root.phase === "error" ? "Falhou: " + root.install.message
            : ""
        color: root.phase === "done" ? Theme.success
             : root.phase === "error" ? Theme.danger
             : Theme.textSecondary
        font.pixelSize: Theme.fontCaption
        font.weight: root.phase === "done" ? Font.DemiBold : Font.Normal
        elide: Text.ElideRight

        HoverHandler { id: hover }
        ToolTip.visible: root.phase === "error" && hover.hovered
        ToolTip.text: root.phase === "error" ? root.install.message : ""
        ToolTip.delay: 300
    }
}
