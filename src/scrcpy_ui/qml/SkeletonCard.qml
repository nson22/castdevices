import QtQuick
import QtQuick.Layouts

// Card de device "carregando": mesmo formato do card da grade (preview +
// nome + serial), com blocos de Skeleton no lugar do conteúdo.
Rectangle {
    id: card

    // Largura útil (descontadas as margens) pras linhas de texto
    readonly property real contentWidth: width - Theme.spacingMd * 2

    radius: Theme.radiusLg
    color: Theme.surface
    border.width: 1
    border.color: Theme.border

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingMd

        Skeleton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: Theme.radiusMd
        }

        ColumnLayout {
            spacing: 6
            Layout.fillWidth: true

            Skeleton {
                Layout.preferredWidth: card.contentWidth * 0.6
                Layout.preferredHeight: 14
            }
            Skeleton {
                Layout.preferredWidth: card.contentWidth * 0.4
                Layout.preferredHeight: 10
            }
        }
    }
}
