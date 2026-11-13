// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid
import "ConfigUtils.js" as ConfigUtils

KCM.SimpleKCM {
    id: page
    property alias cfg_tasksOnlyCurrentDesktop: desktop.checked
    property alias cfg_tasksOnlyCurrentScreen: screen.checked
    property alias cfg_tasksOnlyCurrentActivity: activity.checked
    property alias cfg_tasksGroupingMode: grouping.currentIndex
    property alias cfg_tasksOnlyGroupWhenFull: full.checked
    property alias cfg_tasksSortMode: sorting.currentIndex
    property alias cfg_middleClickAction: middleAction.currentIndex
    property alias cfg_wheelEnabled: wheel.checked
    property alias cfg_iconboxWheelActivates: wheelActivates.checked
    property alias cfg_wheelSkipMinimized: skipMinimized.checked
    property alias cfg_interactiveMute: interactiveMute.checked
    property alias cfg_highlightWindows: highlightWindows.checked
    property alias cfg_unhideOnAttention: unhideOnAttention.checked
    property bool cfg_iconboxWindowThumbnails: false
    property bool cfg_iconboxHintsEnabled: true
    property string cfg_tasksFilterMode: "normal"
    property alias cfg_tasksAutomaticThreshold: threshold.value
    property var cfg_tasksGroupingAppIdBlacklist: []
    property var cfg_tasksGroupingLauncherUrlBlacklist: []
    readonly property var filters: ["normal", "minimized", "automatic"]
    readonly property bool automaticAvailable: cfg_tasksAutomaticThreshold >= 0

    function selectFilter(index) {
        if (index < 0 || index >= filters.length || (index === 2 && !automaticAvailable)) return false;
        cfg_tasksFilterMode = filters[index];
        return true;
    }

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
    }

    Kirigami.FormLayout {
        QQC.CheckBox { id: desktop; text: qsTr("Somente área de trabalho atual"); checked: true; Kirigami.FormData.label: qsTr("Escopo de janelas:") }
        QQC.CheckBox { id: screen; text: qsTr("Somente esta tela") }
        QQC.CheckBox { id: activity; text: qsTr("Somente atividade atual"); checked: true }
        QQC.ComboBox {
            id: filter
            Layout.fillWidth: true
            objectName: "domainosIconboxFilter"
            model: [qsTr("Todas no escopo"), qsTr("Apenas minimizadas"), qsTr("Automático conforme quantidade")]
            currentIndex: Math.max(0, page.filters.indexOf(page.cfg_tasksFilterMode))
            onActivated: index => page.selectFilter(index)
            delegate: QQC.ItemDelegate {
                required property int index
                required property var modelData
                width: filter.width; text: modelData
                enabled: index !== 2 || page.automaticAvailable
            }
            Kirigami.FormData.label: qsTr("Filtro de apresentação:")
        }
        QQC.SpinBox {
            id: threshold
            objectName: "domainosIconboxThreshold"
            from: -1; to: 1000000; value: -1; editable: true
            textFromValue: (value, locale) => value < 0 ? qsTr("Não escolhido") : Number(value).toLocaleString(locale, "f", 0)
            valueFromText: (text, locale) => text === qsTr("Não escolhido") ? -1 : Number.fromLocaleString(locale, text)
            Kirigami.FormData.label: qsTr("Limiar L do filtro automático:")
        }
        QQC.Label {
            text: page.automaticAvailable ? qsTr("N > L: mostrar só minimizadas. N ≤ L: voltar ao normal. N conta janelas do escopo antes de filtrar e agrupar; não minimiza janelas nem limita o total de tarefas.") : qsTr("L ainda não foi escolhido. Escolha um número para habilitar o modo automático; nenhum limiar é definido em seu nome.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.ComboBox {
            id: grouping
            Layout.fillWidth: true
            model: [qsTr("Sem agrupamento"), qsTr("Agrupar por aplicativo")]
            currentIndex: 1
            Kirigami.FormData.label: qsTr("Agrupamento:")
        }
        QQC.CheckBox { id: full; text: qsTr("Agrupar somente quando o espaço estiver ocupado"); checked: true; enabled: grouping.currentIndex === 1 }
        QQC.ComboBox {
            id: sorting
            Layout.fillWidth: true
            model: [qsTr("Sem ordenação"), qsTr("Manual"), qsTr("Alfabética"), qsTr("Área de trabalho"), qsTr("Atividade"), qsTr("Ativação mais recente")]
            currentIndex: 1
            Kirigami.FormData.label: qsTr("Ordem:")
        }
        QQC.Label {
            text: qsTr("Na ordem Manual, arraste uma tarefa sobre outra para reordenar a lista. O gesto usa a distância de arraste do sistema e não move nem ativa as janelas.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.ComboBox {
            id: middleAction
            objectName: "domainosIconboxMiddleAction"
            Layout.fillWidth: true
            model: [qsTr("Nenhuma ação"), qsTr("Fechar"), qsTr("Nova instância"), qsTr("Minimizar/restaurar"), qsTr("Alternar agrupamento"), qsTr("Trazer para a área atual")]
            currentIndex: 2
            Kirigami.FormData.label: qsTr("Botão do meio:")
        }
        QQC.CheckBox { id: wheel; objectName: "domainosIconboxWheelEnabled"; text: qsTr("Usar a roda para percorrer os itens, como as setas laterais"); checked: true; Kirigami.FormData.label: qsTr("Roda na Iconbox:") }
        QQC.CheckBox { id: wheelActivates; objectName: "domainosIconboxWheelActivates"; text: qsTr("Alternar e ativar janelas pela roda (opcional)"); checked: false; enabled: wheel.checked }
        QQC.CheckBox { id: skipMinimized; objectName: "domainosIconboxWheelSkipMinimized"; text: qsTr("Pular janelas minimizadas ao alternar pela roda"); checked: true; enabled: wheel.checked && wheelActivates.checked }
        QQC.CheckBox { id: interactiveMute; objectName: "domainosIconboxInteractiveMute"; text: qsTr("Clicar no indicador de áudio para silenciar o aplicativo"); checked: true; Kirigami.FormData.label: qsTr("Áudio:") }
        QQC.CheckBox { id: highlightWindows; objectName: "domainosIconboxHighlightWindows"; text: qsTr("Destacar as janelas ao passar o mouse nos ícones e títulos (opcional)"); checked: false; Kirigami.FormData.label: qsTr("Destaque:") }
        QQC.CheckBox { id: unhideOnAttention; objectName: "domainosIconboxUnhideOnAttention"; text: qsTr("Mostrar o painel oculto quando uma janela solicitar atenção"); checked: true; Kirigami.FormData.label: qsTr("Atenção:") }
        QQC.ComboBox {
            id: windowPreviews
            objectName: "domainosIconboxWindowPreviewMode"
            model: [qsTr("Títulos e lista de janelas"), qsTr("Miniaturas das janelas"), qsTr("Nenhuma dica")]
            currentIndex: page.cfg_iconboxWindowThumbnails ? 1 : page.cfg_iconboxHintsEnabled ? 0 : 2
            onActivated: index => {
                page.cfg_iconboxWindowThumbnails = index === 1
                page.cfg_iconboxHintsEnabled = index === 0
            }
            Layout.fillWidth: true
            Kirigami.FormData.label: qsTr("Ao passar o mouse na Iconbox:")
        }
        QQC.Label {
            text: qsTr("Por padrão, a dica mostra o título da janela ou a lista ordenada dos membros de um grupo. Você pode desligá-la ou substituí-la por miniaturas. Na lista de um grupo e na legenda de uma miniatura, só títulos cortados recebem uma dica, após a espera do sistema. As miniaturas usam o compositor nativo e são carregadas apenas quando solicitadas. Em X11, janelas minimizadas ou sem composição podem não oferecer miniatura; em Wayland, a prévia depende do KWin e do PipeWire. A indisponibilidade será indicada na própria prévia.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("Em um grupo, fechar, minimizar/restaurar e trazer para a área atual exigem escolher uma janela individual; o botão do meio abre o seletor sem executar essas ações. Nova instância e agrupamento usam o aplicativo/grupo nativo.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.TextArea {
            text: ConfigUtils.copy(page.cfg_tasksGroupingAppIdBlacklist).join("\n")
            placeholderText: qsTr("Um App ID por linha; vazio agrupa todos")
            onTextChanged: {
                const requested = ConfigUtils.unique(ConfigUtils.lines(text));
                if (!ConfigUtils.same(requested, page.cfg_tasksGroupingAppIdBlacklist)) page.cfg_tasksGroupingAppIdBlacklist = requested;
            }
            Kirigami.FormData.label: qsTr("Não agrupar estes App IDs:")
            Layout.fillWidth: true; Layout.preferredHeight: 70
        }
        QQC.TextArea {
            text: ConfigUtils.copy(page.cfg_tasksGroupingLauncherUrlBlacklist).join("\n")
            placeholderText: qsTr("Uma URL de lançador por linha")
            onTextChanged: {
                const requested = ConfigUtils.unique(ConfigUtils.lines(text));
                if (!ConfigUtils.same(requested, page.cfg_tasksGroupingLauncherUrlBlacklist)) page.cfg_tasksGroupingLauncherUrlBlacklist = requested;
            }
            Kirigami.FormData.label: qsTr("Não agrupar estes lançadores:")
            Layout.fillWidth: true; Layout.preferredHeight: 70
        }
        QQC.Label {
            text: qsTr("Na Iconbox, clique simples seleciona e duplo clique restaura/ativa. Dentro de um grupo, o título restaura/ativa diretamente enquanto nenhuma caixa de seleção estiver marcada; com caixas marcadas, o título passa a selecionar ou desmarcar a janela. Ctrl e Shift acrescentam e selecionam intervalos. As setas percorrem todas as tarefas. Operações de janelas exigem escolher um comando; aplicar um filtro não as executa.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
