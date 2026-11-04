import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Linha de formulário: rótulo/descrição à esquerda, controle à direita.
// Abaixo de Theme.compactBreakpoint, controles largos (ComboBox, SpinBox)
// descem pra linha de baixo e ocupam a largura toda (como um media query);
// controles estreitos (Switch, botão) continuam alinhados à direita.
Item {
    id: row

    property string label
    property string description
    property bool showDivider: true
    default property alias control: holder.data

    readonly property bool stacked: width < Theme.compactBreakpoint && holder.implicitWidth > 120

    Layout.fillWidth: true
    implicitHeight: grid.implicitHeight + Theme.spacingMd * 2

    Rectangle {
        visible: row.showDivider
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 1
        color: Theme.border
    }

    GridLayout {
        id: grid
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        columns: row.stacked ? 1 : 2
        columnSpacing: Theme.spacingXl
        rowSpacing: Theme.spacingSm

        ColumnLayout {
            spacing: 2
            Layout.fillWidth: true

            Label {
                text: row.label
                color: Theme.textPrimary
                font.pixelSize: Theme.fontBody
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: row.description
                visible: text.length > 0
                color: Theme.textSecondary
                font.pixelSize: Theme.fontCaption
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        RowLayout {
            id: holder
            spacing: Theme.spacingSm
            Layout.fillWidth: row.stacked
            Layout.alignment: row.stacked ? Qt.AlignLeft : (Qt.AlignRight | Qt.AlignVCenter)
        }
    }
}
