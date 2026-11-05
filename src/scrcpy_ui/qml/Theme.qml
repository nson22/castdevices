pragma Singleton
import QtQuick

// Design tokens do app (equivalente às CSS custom properties de um design
// system web). Toda cor/espaçamento/tipografia das Views sai daqui.
QtObject {
    // "system" | "light" | "dark" -- ligado a settingsViewModel.themeMode no Main.qml
    property string mode: "system"
    readonly property bool dark: mode === "dark"
        || (mode === "system" && Qt.styleHints.colorScheme === Qt.ColorScheme.Dark)

    // Cores -- pares escolhidos com contraste >= 4.5:1 entre texto e superfície
    readonly property color background: dark ? "#0f1115" : "#f3f4f6"
    readonly property color surface: dark ? "#181b22" : "#ffffff"
    readonly property color surfaceAlt: dark ? "#20242d" : "#eceef2"
    readonly property color surfaceHover: dark ? "#272c37" : "#e3e6ec"
    readonly property color border: dark ? "#2d323d" : "#d8dce3"
    readonly property color textPrimary: dark ? "#eceef1" : "#15171c"
    readonly property color textSecondary: dark ? "#a0a7b3" : "#596070"
    readonly property color accent: dark ? "#6b9dff" : "#2563eb"
    // (sem prefixo "on": em QML "onXxx" é reservado pra handler de sinal)
    readonly property color accentText: dark ? "#0b1220" : "#ffffff"
    readonly property color danger: dark ? "#ff6b6b" : "#d12f2f"
    readonly property color dangerText: dark ? "#1f0a0a" : "#ffffff"
    // Progresso/conclusão (ex.: instalação de APK)
    readonly property color success: dark ? "#4ade80" : "#16a34a"
    readonly property color videoBackground: "#000000"
    readonly property color scrim: "#d9101318"
    readonly property color scrimText: "#f4f5f7"

    // Escala de espaçamento (4px base)
    readonly property int spacingXs: 4
    readonly property int spacingSm: 8
    readonly property int spacingMd: 12
    readonly property int spacingLg: 16
    readonly property int spacingXl: 24
    readonly property int spacingXxl: 32

    readonly property int radiusSm: 6
    readonly property int radiusMd: 10
    readonly property int radiusLg: 14

    // Tipografia
    readonly property int fontCaption: 12
    readonly property int fontBody: 14
    readonly property int fontTitle: 16
    readonly property int fontHeadline: 22
    // Material Symbols (mesmo catálogo do fonts.google.com/icons) -- os ícones
    // são escritos pelo nome, via ligadura: text: "tv_off"
    readonly property string iconFont: "Material Symbols Outlined"

    // Layout
    readonly property int appBarHeight: 52
    readonly property int maxContentWidth: 760
    readonly property int maxGridWidth: 1200
    readonly property int compactBreakpoint: 560
}
