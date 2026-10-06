# Mapeamento IrixClassic Sounds 0.1.0

Este é um mapeamento novo para o KDE, não um arquivo `.ss` original do IRIX.
Nenhum evento é criado: o tema fornece o áudio **quando a aplicação solicita o nome**.
A ordem/volume de notificações e suas regras continuam sendo do KDE/aplicativo.

| Som original | Nomes fornecidos no tema | Relação com IRIX |
|---|---|---|
| Erro (`01.african.thumb.inst.aifc`) | `dialog-error`, `dialog-warning`, `battery-low`, `power-unplug-battery-low` | Erro mantém a finalidade; advertência e bateria baixa são adaptações KDE, não o Warning histórico (chegada de arquivo). |
| Erro fatal (`ss1.aifc`) | `dialog-error-serious`, `dialog-error-fatal`, `battery-caution` | Erro fatal é histórico; severidade moderna e o aviso battery-caution são adaptações. O limiar de bateria pertence ao aplicativo. |
| Chegada de arquivo (Warning no IRIX) (`13.high.chink.aifc`) | `message-new`, `message-new-email`, `message-new-instant`, `message-new-sms` | Adaptação de chegada de arquivo para chegada de mensagens. Não toca em operações do Dolphin. |
| Pergunta (`01.buzz.kerchick.aifc`) | `dialog-question` | Correspondência de finalidade. |
| Informação (`08.ting.aifc`) | `dialog-information`, `device-removed`, `power-plug` | Informação é histórica; remoção de dispositivo e energia conectada são adaptações. |
| Conclusão (`20.zikik.aifc`) | `complete`, `complete-download`, `complete-copy`, `complete-media-burn`, `theme-demo` | Conclusão é histórica; os tipos de tarefa e a prévia do tema são adaptações. Não intercepta transferências. |
| Campainha (`ss7.aifc`) | `bell-window-system`, `bell-terminal`, `audio-volume-change` | Campainha é histórica; terminal e ajuste de volume são adaptações. |
| Montar volume (`24.muted.bong.aifc`) | `device-added` | Adaptação de montar volume para dispositivo adicionado; não instala observador de montagem. |

## Eventos sem associação nesta versão

Oito nomes têm `.disabled` vazio para não herdar um login, logout ou tune de
firmware de outro tema: `desktop-login`, `desktop-logout`, `system-bootup`, `system-ready`, `system-shutdown`, `service-login`, `service-logout`, `desktop-switch`.
Não há `.disabled` para erro/bateria ou outros avisos importantes desconhecidos.
O fallback `freedesktop` permanece explícito para eventos fora da cobertura.

Os nomes `complete-*` correspondem à conclusão de operações. Não foram usados
`completion-*`, que se referem à completação de texto. Os oito sons importados
são reproduzidos sem alterações de ganho; vários nomes referenciam o mesmo PCM.

## Reservados para depois

Sons de mover/copiar/recolher ícones, excluir, enviar à lixeira, abrir pasta local
ou remota e lançar aplicações constam somente do catálogo. Não recebem aliases
`file-*`, `item-*`, `trash-*` ou `window-*` nesta versão. Não há integração Dolphin.
O mapeamento genérico `complete-copy` apenas disponibiliza um arquivo para um
nome padronizado; não instrumenta a cópia de arquivos.

## Base técnica verificada

- Catálogo SGI: https://ftp.jurassic.nl/mirrors/ftp.sgi.com/sgi/desktop/sounds/sounds.html
- Nomes freedesktop: https://specifications.freedesktop.org/sound-naming/0.2/
- Formato: https://specifications.freedesktop.org/sound-theme/latest-single/
- Prévia do Plasma 6.3: https://github.com/KDE/plasma-workspace/blob/Plasma/6.3/kcms/soundtheme/ui/main.qml
- Configuração KDE: https://github.com/KDE/plasma-workspace/blob/Plasma/6.3/kcms/soundtheme/soundthemesettings.kcfg
- Reprodução KNotifications 6.13: https://github.com/KDE/knotifications/blob/v6.13.0/src/notifybyaudio.cpp

O Plasma grava `Theme` e `Enable` em `[Sounds]` de `kdeglobals`.
Este instalador **não edita esse arquivo**: a seleção é feita pelo painel nativo.
KNotifications utiliza libcanberra com o nome do evento e o tema selecionado;
configurações legadas por caminho de arquivo podem ter resultado diferente.
As cinco prévias do KCM são cobertas por campainha, advertência, mensagem,
advertência de bateria e dispositivo. A prévia principal usa `Example=theme-demo`.
