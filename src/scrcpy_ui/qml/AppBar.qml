import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Barra superior comum a todas as telas: [leading] título/subtítulo [ações]
Rectangle {
    id: bar

    property string title
    property string subtitle
    property alias leading: leadingRow.data
    default property alias actions: trailingRow.data

    implicitHeight: Theme.appBarHeight
    color: Theme.surface

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: Theme.border
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Theme.spacingSm
        anchors.rightMargin: Theme.spacingSm
        spacing: Theme.spacingSm

        Row {
            id: leadingRow
            spacing: 2
            Layout.alignment: Qt.AlignVCenter
        }

        ColumnLayout {
            spacing: 0
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: leadingRow.children.length > 0 ? 0 : Theme.spacingSm

            Label {
                text: bar.title
                visible: text.length > 0
                color: Theme.textPrimary
                font.pixelSize: Theme.fontTitle
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Label {
                text: bar.subtitle
                visible: text.length > 0
                color: Theme.textSecondary
                font.pixelSize: Theme.fontCaption
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }

        Row {
            id: trailingRow
            spacing: 2
            Layout.alignment: Qt.AlignVCenter
        }
    }
}
