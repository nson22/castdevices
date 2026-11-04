import QtQuick
import QtQuick.Controls

ToolButton {
    id: control

    property string iconName
    property string tip
    property color iconColor: Theme.textPrimary

    implicitWidth: 40
    implicitHeight: 40
    padding: 0

    contentItem: Text {
        text: control.iconName
        font.family: Theme.iconFont
        font.pixelSize: 22
        color: control.enabled ? control.iconColor : Theme.textSecondary
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: Theme.radiusSm
        color: control.down ? Theme.surfaceHover
             : control.hovered ? Theme.surfaceAlt
             : "transparent"
    }

    ToolTip.text: tip
    ToolTip.visible: hovered && tip.length > 0
    ToolTip.delay: 400
}
