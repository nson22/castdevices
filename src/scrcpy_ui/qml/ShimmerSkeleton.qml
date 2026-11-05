import QtQuick

// Indicador de carregamento estilo "shimmer".
// skeleton: true  -> linhas-esqueleto imitando a árvore (ainda não há conteúdo)
// skeleton: false -> só a faixa de brilho varrendo por cima do conteúdo atual
Item {
    id: root

    property bool skeleton: true
    readonly property real band: 180
    // Posição horizontal da faixa de brilho, compartilhada por todas as linhas
    // pra que o brilho atravesse o esqueleto inteiro como uma onda só
    property real sweepX: -band
    // Profundidade e largura relativa de cada linha do esqueleto (parece uma árvore)
    readonly property var shape: [[0, .45], [1, .6], [1, .38], [2, .7], [3, .5], [3, .62], [2, .42],
                                  [1, .55], [2, .66], [3, .4], [4, .58], [2, .48], [1, .35], [2, .6]]

    clip: true

    NumberAnimation on sweepX {
        running: root.visible
        from: -root.band
        to: root.width + root.band
        duration: 1400
        loops: Animation.Infinite
        easing.type: Easing.InOutQuad
    }

    component Sweep: Rectangle {
        // offsetX: posição deste item em relação ao root
        property real offsetX: 0
        x: root.sweepX - offsetX - root.band / 2
        width: root.band
        height: parent.height
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: "transparent" }
            GradientStop { position: 0.5; color: Qt.rgba(Theme.textPrimary.r, Theme.textPrimary.g, Theme.textPrimary.b, root.skeleton ? 0.10 : 0.09) }
            GradientStop { position: 1; color: "transparent" }
        }
    }

    // Recaptura com árvore na tela: brilho discreto sobre o conteúdo
    Sweep {
        visible: !root.skeleton
    }

    Column {
        id: rows
        visible: root.skeleton
        x: Theme.spacingSm
        y: Theme.spacingSm + 7
        spacing: 14

        Repeater {
            model: Math.ceil(root.height / 28)

            Rectangle {
                id: bar
                required property int index
                readonly property var spec: root.shape[index % root.shape.length]

                x: 22 + spec[0] * 14
                width: Math.max(60, (root.width - rows.x - x - Theme.spacingLg) * spec[1])
                height: 14
                radius: 4
                color: Theme.surfaceAlt
                clip: true

                Sweep {
                    offsetX: rows.x + bar.x
                }
            }
        }
    }
}
