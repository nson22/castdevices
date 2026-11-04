import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Card de uma seção de configurações (título + descrição + linhas).
Rectangle {
    id: section

    property string title
    property string description
    default property alias content: body.data

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + Theme.spacingXl * 2
    radius: Theme.radiusLg
    color: Theme.surface
    border.color: Theme.border
    border.width: 1

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Theme.spacingXl
        spacing: Theme.spacingXs

        Label {
            text: section.title
            color: Theme.textPrimary
            font.pixelSize: Theme.fontTitle
            font.weight: Font.DemiBold
            Layout.fillWidth: true
        }
        Label {
            text: section.description
            visible: text.length > 0
            color: Theme.textSecondary
            font.pixelSize: Theme.fontCaption
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        ColumnLayout {
            id: body
            spacing: 0
            Layout.fillWidth: true
            Layout.topMargin: Theme.spacingSm
        }
    }
}
