> Atualização 0.4.0-rc1: há relato de falha em outros Application Styles.
> O reparo descrito abaixo continua opcional e experimental, sem confirmação
> de aplicação/carregamento na sessão. Não equivale a solução universal de ação.
> Antes de novas alterações de sistema, execute o diagnóstico cruzado em
> `DIAGNOSTICO-SETAS.md`; separe movimento real de ausência de relevo.

# Setas que rolam, mas não afundam: integração Qt Quick

**Correção opcional de compatibilidade; não é um novo desenho.** Manutenção:
`mrmmx31`. Os SVGs de setas, puxador e ranhuras já aprovados são preservados.

## Causa encontrada no código

No KDE qqc2-desktop-style v6.13.0, o MouseArea do fundo do ScrollBar aceita o
clique nas setas e executa increase/decrease por timer. Entretanto, o StyleItem
usa somente `sunken: controlRoot.pressed`. Quando a pressão fica no MouseArea,
o controle Templates não precisa entrar em pressed. O aplicativo rola, mas não
encaminha Sunken ao QStyle. Por isso trocar o SVG pressed não corrige esse caso.
O QScrollBar de Qt Widgets faz outro caminho e define State_Sunken no paintEvent.

A correção mantém o estado nativo do puxador e acrescenta a pressão esquerda da
seta realmente aceita pelo MouseArea. Registra a seta inicial, verifica que o
ponteiro continua nesse controle e limpa o registro na soltura/cancelamento.
O hit-test é recalculado na pressão, sem depender de um movimento anterior.
Não adiciona timer visual, não altera o timer de repetição, cores ou métricas.

Isso identifica um defeito no componente revisto, mas não prova, sem diagnóstico
local, que toda ausência de relevo em qualquer aplicativo tenha essa causa.
O teste nativo de botões é Qt Widgets; a galeria nova testa Qt Quick/KDE.

## Escopo e instalação opt-in

**Afeta todos os temas/aplicativos que carregam o módulo Qt Quick org.kde.desktop**,
não apenas o IrixClassic. Não é aplicado por `instalar-classic.sh` ou pelos
instaladores das decorações. Não modifica o plugin Kvantum, KWin, SVGs ou seleção.

Na raiz do checkout, usuário normal, sem sudo na frente:

```sh
# Verifica o contrato do arquivo existente e exibe o diff sem escrever:
bash kvantum/corrigir-pressao-qtquick.sh --verificar --diff
# Aplicação opcional. O próprio script pede autorização administrativa:
bash kvantum/corrigir-pressao-qtquick.sh
```

Caminho típico Debian amd64:
`/usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/desktop/ScrollBar.qml`.
O script aceita também as variantes Qt 6 lib/ e lib64/ previstas no código.
Uma âncora ausente, ambígua ou uma modificação local na correção é recusada,
sem opção de forçar. O arquivo inteiro não é substituído por uma cópia do projeto.

### Por que o qmldir também pode precisar mudar

Qt 6 pode usar a diretiva `prefer :/qt/qml/org/kde/desktop/` para carregar a fonte
embutida no plugin em vez do arquivo editado no disco. Quando esse destino exato
está presente, o reparo remove **somente essa diretiva** e preserva módulos/plugins.
Antes disso, exige todos os arquivos QML registrados no qmldir presentes em disco;
sem eles a operação é recusada antes da primeira escrita. Sem prefer, o qmldir
permanece byte a byte igual. Nenhuma biblioteca é recompilada ou substituída.

Os dois arquivos são verificados novamente após autorização; há backup dos
bytes/permissões e tentativa de rollback em caso de falha. Interrupção abrupta
ou autorização de restauração negada pode exigir recuperação explícita. Não
há uma transação atômica com os aplicativos que já estão executando.

Reabra completamente Configurações do Sistema e outros aplicativos Qt Quick.
Uma nova sessão recarrega componentes residentes. O script não encerra processos.
Não apaga caches nem muda variáveis globais de ambiente. Atualizações de pacote
KDE podem repor os arquivos originais: reverificar, não reaplicar às cegas.

### Restauração

```sh
bash kvantum/corrigir-pressao-qtquick.sh --restaurar --verificar
bash kvantum/corrigir-pressao-qtquick.sh --restaurar
# Somente caso o recibo indique recuperação pendente:
bash kvantum/corrigir-pressao-qtquick.sh --restaurar --recuperar
```

Recibos em `${XDG_STATE_HOME:-$HOME/.local/state}/irixclassic-qtquick-press/`.
Edições posteriores desconhecidas bloqueiam rollback; não se apagam mudanças
novas. Reabra os apps depois de restaurar. O reparo é independente do tema.

## Teste nativo sem instalar

```sh
bash kvantum/prever-pressao-qtquick.sh
bash kvantum/prever-pressao-qtquick.sh --testar --capturas /caminho/temporario/qtquick
```

A galeria copia o componente instalado para uma pasta temporária, aplica as
mesmas alterações e carrega uma URL local explícita. A seleção Kvantum também
é temporária. O ensaio verifica a propriedade sunken do **StyleItem real**
durante mousePress e após mouseRelease. `--original` usa a fonte sem aplicar o
reparo: o ensaio pode falhar justamente por reproduzir o defeito. Não é um
mock de Qt, e uma dependência Qt/KDE ausente não conta como teste aprovado.

Carregar a cópia temporária prova esse caminho; confirmar a resolução do módulo
instalado via qmldir continua sendo parte da aceitação na sessão real.

## Fontes

- KDE: https://github.com/KDE/qqc2-desktop-style/blob/v6.13.0/org.kde.desktop/ScrollBar.qml
- Qt: https://github.com/qt/qtbase/blob/v6.8.2/src/widgets/widgets/qscrollbar.cpp
- Kvantum: https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp
- Qt qmldir/prefer: https://doc.qt.io/qt-6.8/qtqml-modules-qmldir.html
