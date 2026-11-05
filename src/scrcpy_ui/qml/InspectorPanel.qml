import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Painel lateral com a árvore de elementos da tela (uiautomator dump) e as
// propriedades do elemento selecionado.
Rectangle {
    id: panel

    color: Theme.surface

    Connections {
        target: inspectorViewModel
        function onHierarchyChanged() {
            tree.expandRecursively()
            // Recaptura automática: mantém selecionado o mesmo elemento, se ainda existir
            const index = inspectorViewModel.selectedIndex()
            if (index.valid) {
                tree.selectionModel.setCurrentIndex(index, ItemSelectionModel.NoUpdate)
            } else {
                tree.selectionModel.clearCurrentIndex()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.leftMargin: Theme.spacingLg
            Layout.rightMargin: Theme.spacingSm
            spacing: Theme.spacingSm

            Label {
                text: "Hierarquia da tela"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontTitle
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            IconButton {
                objectName: "inspectorRefresh"
                iconName: "refresh"
                tip: "Recarregar (também atualiza sozinho quando a tela muda)"
                onClicked: inspectorViewModel.refresh()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.border
        }

        Label {
            visible: inspectorViewModel.errorMessage.length > 0
            text: "Não foi possível capturar: " + inspectorViewModel.errorMessage
            color: Theme.danger
            font.pixelSize: Theme.fontCaption
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            Layout.margins: Theme.spacingLg
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            TreeView {
                id: tree
                anchors.fill: parent
                anchors.topMargin: Theme.spacingXs
                clip: true
                model: inspectorViewModel.hierarchyModel

                // Recapturando: a árvore atual pulsa (mesmo "pulse" do skeleton)
                readonly property bool refreshing: inspectorViewModel.busy && rows > 0
                onRefreshingChanged: if (!refreshing) opacity = 1
                SequentialAnimation on opacity {
                    running: tree.refreshing
                    loops: Animation.Infinite
                    NumberAnimation { from: 1; to: 0.5; duration: 1000; easing.type: Easing.Bezier; easing.bezierCurve: [0.4, 0, 0.6, 1, 1, 1] }
                    NumberAnimation { from: 0.5; to: 1; duration: 1000; easing.type: Easing.Bezier; easing.bezierCurve: [0.4, 0, 0.6, 1, 1, 1] }
                }
                // Painel criado com uma captura já existente (ex.: hot reload)
                Component.onCompleted: expandRecursively()
                selectionModel: ItemSelectionModel {
                    onCurrentChanged: (current) => inspectorViewModel.selectIndex(current)
                }

                ScrollBar.vertical: ScrollBar {}
                ScrollBar.horizontal: ScrollBar {}

                delegate: Item {
                    id: node

                    required property TreeView treeView
                    required property bool expanded
                    required property bool hasChildren
                    required property int depth
                    required property int row
                    required property int column
                    required property bool current
                    required property string display

                    readonly property int indent: Theme.spacingSm + depth * 14

                    implicitWidth: Math.max(tree.width, indent + 24 + label.implicitWidth + Theme.spacingLg)
                    implicitHeight: 28

                    Rectangle {
                        anchors.fill: parent
                        color: node.current ? Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.18)
                             : hover.hovered ? Theme.surfaceAlt
                             : "transparent"
                    }

                    Text {
                        id: arrow
                        x: node.indent
                        anchors.verticalCenter: parent.verticalCenter
                        visible: node.hasChildren
                        text: "chevron_right"
                        rotation: node.expanded ? 90 : 0
                        font.family: Theme.iconFont
                        font.pixelSize: 18
                        color: Theme.textSecondary

                        TapHandler {
                            onTapped: node.treeView.toggleExpanded(node.row)
                        }
                    }

                    Label {
                        id: label
                        x: node.indent + 22
                        anchors.verticalCenter: parent.verticalCenter
                        text: node.display
                        color: node.current ? Theme.accent : Theme.textPrimary
                        font.pixelSize: Theme.fontCaption + 1
                    }

                    HoverHandler { id: hover }
                    TapHandler {
                        onTapped: node.treeView.selectionModel.setCurrentIndex(
                            node.treeView.index(node.row, node.column), ItemSelectionModel.NoUpdate)
                        onDoubleTapped: node.treeView.toggleExpanded(node.row)
                    }
                }
            }

            // Carregando a primeira captura: skeleton de texto (estilo shadcn/ui).
            // Nas recapturas a árvore atual continua visível, pulsando igual.
            SkeletonText {
                anchors.fill: parent
                visible: inspectorViewModel.busy && tree.rows === 0
            }

            Label {
                anchors.centerIn: parent
                visible: tree.rows === 0 && !inspectorViewModel.busy && inspectorViewModel.errorMessage.length === 0
                text: "Nada capturado ainda"
                color: Theme.textSecondary
                font.pixelSize: Theme.fontBody
            }
        }

        Rectangle {
            visible: inspectorViewModel.hasSelection
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.border
        }

        ScrollView {
            id: detailsScroll
            visible: inspectorViewModel.hasSelection
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(details.implicitHeight + Theme.spacingLg * 2, panel.height * 0.4)
            contentWidth: availableWidth
            clip: true

            ColumnLayout {
                id: details
                x: Theme.spacingLg
                y: Theme.spacingLg
                width: detailsScroll.availableWidth - Theme.spacingLg * 2
                spacing: Theme.spacingSm

                Repeater {
                    model: inspectorViewModel.selectedDetails

                    RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Theme.spacingMd

                        Label {
                            text: modelData.name
                            color: Theme.textSecondary
                            font.pixelSize: Theme.fontCaption
                            Layout.preferredWidth: 96
                            Layout.alignment: Qt.AlignTop
                        }
                        // TextEdit (e não Label) pra dar pra selecionar e copiar o valor
                        TextEdit {
                            text: modelData.value
                            readOnly: true
                            selectByMouse: true
                            wrapMode: TextEdit.WrapAnywhere
                            color: Theme.textPrimary
                            selectionColor: Theme.accent
                            selectedTextColor: Theme.accentText
                            font.pixelSize: Theme.fontCaption
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
