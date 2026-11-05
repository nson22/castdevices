import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Painel lateral "Desinstalar apps" (mesmo formato do painel da hierarquia):
// lista os apps instalados pelo usuário no device ativo (nome + pacote),
// seleção múltipla, busca e confirmação antes de desinstalar.
Rectangle {
    id: panel

    color: Theme.surface

    // Botão de perigo (vermelho), usado no rodapé e no diálogo
    component DangerButton: Button {
        id: danger
        leftPadding: Theme.spacingLg
        rightPadding: Theme.spacingLg

        contentItem: Label {
            text: danger.text
            color: danger.enabled ? Theme.dangerText : Theme.textSecondary
            font.pixelSize: Theme.fontBody
            font.weight: Font.DemiBold
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            implicitHeight: 36
            radius: Theme.radiusSm
            color: !danger.enabled ? Theme.surfaceAlt
                 : danger.down ? Qt.darker(Theme.danger, 1.15)
                 : danger.hovered ? Qt.lighter(Theme.danger, 1.06)
                 : Theme.danger
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
                text: "Desinstalar apps"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontTitle
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            IconButton {
                iconName: "refresh"
                tip: "Recarregar lista"
                enabled: !appManagerViewModel.uninstalling
                onClicked: appManagerViewModel.refresh()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.border
        }

        TextField {
            id: search
            objectName: "appsSearch"
            Layout.fillWidth: true
            Layout.margins: Theme.spacingMd
            placeholderText: "Buscar por nome ou pacote"
            selectByMouse: true
            onTextChanged: appManagerViewModel.setFilter(text)
        }

        Label {
            visible: appManagerViewModel.errorMessage.length > 0
            text: "Não foi possível listar os apps: " + appManagerViewModel.errorMessage
            color: Theme.danger
            font.pixelSize: Theme.fontCaption
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            Layout.leftMargin: Theme.spacingLg
            Layout.rightMargin: Theme.spacingLg
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: list
                anchors.fill: parent
                clip: true
                visible: !appManagerViewModel.loading
                model: appManagerViewModel.appsModel
                ScrollBar.vertical: ScrollBar {}

                delegate: Rectangle {
                    id: row
                    required property string appName
                    required property string packageName
                    required property bool selected
                    required property string status
                    required property string message

                    width: list.width
                    implicitHeight: 52
                    color: row.selected ? Qt.rgba(Theme.danger.r, Theme.danger.g, Theme.danger.b, 0.10)
                         : rowHover.hovered ? Theme.surfaceAlt
                         : "transparent"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: Theme.spacingSm
                        anchors.rightMargin: Theme.spacingLg
                        spacing: Theme.spacingSm

                        CheckBox {
                            checked: row.selected
                            enabled: !appManagerViewModel.uninstalling
                            onToggled: appManagerViewModel.toggle(row.packageName)
                        }

                        ColumnLayout {
                            spacing: 1
                            Layout.fillWidth: true

                            Label {
                                text: row.appName
                                color: Theme.textPrimary
                                font.pixelSize: Theme.fontBody
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            // App sem nome (sem ícone no launcher): o nome já é o pacote
                            Label {
                                visible: row.appName !== row.packageName
                                text: row.packageName
                                color: Theme.textSecondary
                                font.pixelSize: Theme.fontCaption
                                elide: Text.ElideMiddle
                                Layout.fillWidth: true
                            }
                        }

                        Label {
                            visible: row.status.length > 0
                            text: row.status === "uninstalling" ? "Removendo…"
                                : row.status === "done" ? "Removido"
                                : row.status === "error" ? "Falhou"
                                : ""
                            color: row.status === "done" ? Theme.success
                                 : row.status === "error" ? Theme.danger
                                 : Theme.textSecondary
                            font.pixelSize: Theme.fontCaption
                            font.weight: Font.DemiBold

                            HoverHandler { id: statusHover }
                            ToolTip.visible: row.status === "error" && statusHover.hovered
                            ToolTip.text: row.message
                        }
                    }

                    HoverHandler { id: rowHover }
                    TapHandler {
                        enabled: !appManagerViewModel.uninstalling
                        onTapped: appManagerViewModel.toggle(row.packageName)
                    }
                }
            }

            SkeletonText {
                anchors.fill: parent
                visible: appManagerViewModel.loading
            }

            Label {
                anchors.centerIn: parent
                width: parent.width - Theme.spacingXl * 2
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                visible: !appManagerViewModel.loading && list.count === 0
                         && appManagerViewModel.errorMessage.length === 0
                text: search.text.length > 0 ? "Nenhum app encontrado para \"" + search.text + "\""
                                             : "Nenhum app instalado pelo usuário"
                color: Theme.textSecondary
                font.pixelSize: Theme.fontBody
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.border
        }

        // Rodapé: seleção + ação
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Theme.spacingMd
            spacing: Theme.spacingSm

            Label {
                text: appManagerViewModel.selectedCount === 0 ? "Nenhum app selecionado"
                    : appManagerViewModel.selectedCount === 1 ? "1 app selecionado"
                    : appManagerViewModel.selectedCount + " apps selecionados"
                color: Theme.textSecondary
                font.pixelSize: Theme.fontCaption
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Button {
                text: "Limpar"
                flat: true
                visible: appManagerViewModel.selectedCount > 0
                enabled: !appManagerViewModel.uninstalling
                onClicked: appManagerViewModel.clearSelection()
            }
            DangerButton {
                objectName: "uninstallButton"
                text: appManagerViewModel.uninstalling ? "Desinstalando…" : "Desinstalar"
                enabled: appManagerViewModel.selectedCount > 0 && !appManagerViewModel.uninstalling
                onClicked: confirmDialog.open()
            }
        }
    }

    // Confirmação com o aviso do perigo
    Dialog {
        id: confirmDialog
        objectName: "uninstallConfirm"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(parent.width - Theme.spacingXl * 2, 460)
        modal: true
        padding: Theme.spacingXl

        readonly property bool keepData: settingsViewModel.keepAppDataOnUninstall
        readonly property int count: appManagerViewModel.selectedCount

        background: Rectangle {
            radius: Theme.radiusLg
            color: Theme.surface
            border.color: Theme.border
        }

        contentItem: ColumnLayout {
            spacing: Theme.spacingLg

            Label {
                text: confirmDialog.count === 1 ? "Desinstalar 1 app?" : "Desinstalar " + confirmDialog.count + " apps?"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontTitle
                font.weight: Font.DemiBold
            }

            // Aviso
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: warningRow.implicitHeight + Theme.spacingMd * 2
                radius: Theme.radiusMd
                color: Qt.rgba(Theme.danger.r, Theme.danger.g, Theme.danger.b, 0.12)
                border.color: Qt.rgba(Theme.danger.r, Theme.danger.g, Theme.danger.b, 0.45)

                RowLayout {
                    id: warningRow
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: Theme.spacingMd

                    Text {
                        text: "warning"
                        font.family: Theme.iconFont
                        font.variableAxes: ({ "FILL": 1 })
                        font.pixelSize: 22
                        color: Theme.danger
                        Layout.alignment: Qt.AlignTop
                    }
                    Label {
                        text: confirmDialog.keepData
                              ? "Esta ação não pode ser desfeita. Os apps serão removidos do device; "
                                + "os dados e o cache deles ficam guardados no device (opção nas Configurações)."
                              : "Esta ação não pode ser desfeita. Os apps e TODOS os dados deles (arquivos, "
                                + "contas, configurações e cache) serão apagados do device permanentemente."
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontBody
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }

            // O que vai ser removido
            ListView {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(contentHeight, 200)
                clip: true
                interactive: contentHeight > height
                model: appManagerViewModel.selectedApps
                spacing: Theme.spacingSm
                ScrollBar.vertical: ScrollBar {}

                delegate: ColumnLayout {
                    required property var modelData
                    width: ListView.view.width
                    spacing: 0

                    Label {
                        text: modelData.name
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontBody
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    Label {
                        visible: modelData.name !== modelData.package
                        text: modelData.package
                        color: Theme.textSecondary
                        font.pixelSize: Theme.fontCaption
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: Theme.spacingSm
                spacing: Theme.spacingSm

                Item { Layout.fillWidth: true }
                Button {
                    text: "Cancelar"
                    flat: true
                    onClicked: confirmDialog.reject()
                }
                DangerButton {
                    objectName: "confirmUninstall"
                    text: confirmDialog.count === 1 ? "Desinstalar" : "Desinstalar " + confirmDialog.count
                    onClicked: confirmDialog.accept()
                }
            }
        }

        onAccepted: appManagerViewModel.uninstallSelected()
    }
}
