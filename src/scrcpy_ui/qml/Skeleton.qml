import QtQuick

// Bloco de carregamento no estilo do Skeleton do shadcn/ui: cor neutra
// (bg-accent), cantos rounded-md e animação "pulse" (opacidade 1 -> 0,5 -> 1
// em 2s, cubic-bezier(.4,0,.6,1)).
Rectangle {
    id: root

    property bool running: visible

    radius: Theme.radiusSm
    color: Theme.surfaceHover

    SequentialAnimation on opacity {
        running: root.running
        loops: Animation.Infinite
        NumberAnimation { from: 1; to: 0.5; duration: 1000; easing.type: Easing.Bezier; easing.bezierCurve: [0.4, 0, 0.6, 1, 1, 1] }
        NumberAnimation { from: 0.5; to: 1; duration: 1000; easing.type: Easing.Bezier; easing.bezierCurve: [0.4, 0, 0.6, 1, 1, 1] }
    }
}
