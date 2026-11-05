import QtQuick
import QtQuick.Controls

ToolButton {
    id: control

    property string iconName
    property string tip
    property color iconColor: Theme.textPrimary
    // Material Symbols é variável: FILL=1 dá a versão preenchida do ícone
    property bool filled: false
    // Operação em andamento: o próprio ícone gira em destaque (quem usa o botão
    // ignora cliques enquanto isso; não usa enabled pra não apagar o ícone)
    property bool busy: false

    implicitWidth: 40
    implicitHeight: 40
    padding: 0

    contentItem: Text {
        id: glyph
        text: control.iconName
        font.family: Theme.iconFont
        font.pixelSize: 22
        font.variableAxes: ({ "FILL": control.filled ? 1 : 0 })
        color: control.busy ? Theme.accent
             : !control.enabled ? Theme.textSecondary
             : control.checked ? Theme.accent
             : control.iconColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter

        RotationAnimator on rotation {
            running: control.busy
            from: 0
            to: 360
            duration: 900
            loops: Animation.Infinite
            // Ao parar, volta pra posição normal em vez de ficar torto
            onRunningChanged: if (!running) glyph.rotation = 0
        }
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
