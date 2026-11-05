import QtQuick

// Botão de upload de APK. Durante a instalação, um anel verde em volta do
// ícone mostra o progresso (0..1).
IconButton {
    id: control

    property real progress: 0
    property bool installing: false

    iconName: "apk_install"

    Canvas {
        id: ring
        anchors.centerIn: parent
        width: 34
        height: 34
        visible: control.installing
        // Só redesenha quando algo muda (Canvas não é reativo sozinho)
        property real value: control.progress
        property color trackColor: Theme.border
        property color fillColor: Theme.success
        onValueChanged: requestPaint()
        onTrackColorChanged: requestPaint()
        onVisibleChanged: requestPaint()

        onPaint: {
            const ctx = getContext("2d")
            const lineWidth = 3
            const r = (width - lineWidth) / 2
            const cx = width / 2
            const cy = height / 2
            ctx.reset()
            ctx.lineWidth = lineWidth
            ctx.lineCap = "round"

            ctx.strokeStyle = trackColor
            ctx.beginPath()
            ctx.arc(cx, cy, r, 0, 2 * Math.PI)
            ctx.stroke()

            if (value > 0) {
                // Começa no topo (-90°) e vai no sentido horário
                ctx.strokeStyle = fillColor
                ctx.beginPath()
                ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * Math.min(1, value))
                ctx.stroke()
            }
        }
    }
}
