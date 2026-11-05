import QtQuick

// Placeholder de carregamento no estilo do Skeleton "Text" do shadcn/ui:
// blocos de 3 linhas (h-4, gap-2; w-full, w-full, w-3/4), cantos rounded-md,
// cor neutra e animação "pulse" (opacidade 1 -> 0,5 -> 1 em 2s).
Item {
    id: root

    readonly property int lineHeight: 16      // h-4
    readonly property int lineGap: 8          // gap-2
    readonly property int blockGap: 24
    readonly property int blockHeight: lineHeight * 3 + lineGap * 2

    clip: true

    // animate-pulse do Tailwind: 50% { opacity: .5 }, cubic-bezier(.4,0,.6,1)
    SequentialAnimation on opacity {
        running: root.visible
        loops: Animation.Infinite
        NumberAnimation { from: 1; to: 0.5; duration: 1000; easing.type: Easing.Bezier; easing.bezierCurve: [0.4, 0, 0.6, 1, 1, 1] }
        NumberAnimation { from: 0.5; to: 1; duration: 1000; easing.type: Easing.Bezier; easing.bezierCurve: [0.4, 0, 0.6, 1, 1, 1] }
    }

    Column {
        id: blocks
        x: Theme.spacingLg
        y: Theme.spacingLg
        width: root.width - Theme.spacingLg * 2
        spacing: root.blockGap

        Repeater {
            model: Math.max(1, Math.ceil((root.height - Theme.spacingLg) / (root.blockHeight + root.blockGap)))

            Column {
                width: blocks.width
                spacing: root.lineGap

                Repeater {
                    model: [1, 1, 0.75]   // w-full, w-full, w-3/4

                    Rectangle {
                        required property real modelData
                        width: blocks.width * modelData
                        height: root.lineHeight
                        radius: Theme.radiusSm   // rounded-md
                        color: Theme.surfaceHover  // bg-accent
                    }
                }
            }
        }
    }
}
