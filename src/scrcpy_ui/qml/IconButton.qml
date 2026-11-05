import QtQuick
import QtQuick.Controls

ToolButton {
    id: control

    property string iconName
    property string tip
    property color iconColor: Theme.textPrimary
    // Material Symbols é variável: FILL=1 dá a versão preenchida do ícone
    property bool filled: false

    implicitWidth: 40
    implicitHeight: 40
    padding: 0

    contentItem: Text {
        text: control.iconName
        font.family: Theme.iconFont
        font.pixelSize: 22
        font.variableAxes: ({ "FILL": control.filled ? 1 : 0 })
        color: !control.enabled ? Theme.textSecondary
             : control.checked ? Theme.accent
             : control.iconColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    // checkable: true + checked -> estado "ligado" (fundo e ícone em destaque)
    background: Rectangle {
        radius: Theme.radiusSm
        color: control.down ? Theme.surfaceHover
             : control.checked || control.hovered ? Theme.surfaceAlt
             : "transparent"
    }

    ToolTip.text: tip
    ToolTip.visible: hovered && tip.length > 0
    ToolTip.delay: 400
}
