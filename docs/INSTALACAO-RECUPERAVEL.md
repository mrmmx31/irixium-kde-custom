# Instalação e recuperação no perfil do usuário

## DomainOS independente

`tools/install_domainos.py` disponibiliza exatamente quatro componentes:
`plasma/plasmoids/org.irixclassic.domainos.panel`,
`plasma/plasmoids/org.irixclassic.grosview`,
`plasma/desktoptheme/IrixClassicDomainOS` e
`color-schemes/DomainOS-SR10-4.colors`, sob `XDG_DATA_HOME`.
Requer Plasma 6 com Qt 6.8 ou superior e verifica os módulos/serviços KDE/Qt pertinentes e o PyQt6 QtCore/QtDBus da
distribuição. Não exige os temas/dependências extras da suite completa.
O ZIP pré-compilado inclui o módulo nativo do painel. No checkout somente de
fontes, sua preparação também requer compilador C++, `pkg-config` e os SDKs
Qt6Widgets/Qt6Qml compatíveis com o Qt em execução; isso é verificado antes de
instalar. Nenhuma dependência de sistema é instalada automaticamente.

```sh
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
python3 tools/install_domainos.py --restaurar --verificar
python3 tools/install_domainos.py --restaurar
```

Execute como o próprio usuário, sem `sudo`. Raízes XDG estrangeiras, destinos
compartilhados e links de destino são recusados. Não há aplicação de perfil,
inserção de painel, escrita de preferências, refresh de caches/sinais ou hooks.
O widget fica disponível para adição explícita pelo usuário. Atualizar seus arquivos
não recarrega uma instância que já mantém QML em memória.

O estado próprio é `XDG_STATE_HOME/irixium-domainos`. O mesmo `Bundle` da suite
prepara/stageia cópias, confere hashes e mantém recibos/backups. Repetir com os mesmos
bytes não cria backup novo. Restaurar recupera os destinos anteriores e remove os
que a instalação criou; recusa uma edição posterior em um destino ou no backup.
Cada recibo inclui somente os destinos alterados naquela execução. Restaurar uma
atualização do applet recupera sua versão anterior; não desfaz instalações mais
antigas dos componentes que aquela atualização deixou iguais.
Os dois instaladores compartilham esses quatro caminhos, mas não seus recibos:
uma instalação posterior por outro fluxo pode impedir a restauração antiga se
alterar seus bytes. A restauração não apaga preferências/layouts criados pelo uso.

## Suite completa e aplicação

`instalar-irixium.sh` lê `components.json`, verifica os 40 componentes e prepara
cópias temporárias antes de substituir os destinos dos três temas globais:
IRIX Classic, Irixium Moderno e IrixClassicDomainOS. Guarda recibos e os arquivos
anteriores em `XDG_STATE_HOME/irixium-suite`. Não grava seleção nem recursos de
sistema. Destinos compartilhados e links externos são recusados.

### Distribuição completa pré-compilada

`tools/package_suite.py` reúne o catálogo dos 40 componentes, os auxiliares de
instalação e o módulo nativo de um ZIP DomainOS previamente validado. O módulo
só é reutilizado quando seus sete arquivos de entrada coincidem com as fontes;
a instalação também verifica arquitetura e ABI Qt. O pacote não exige o SDK
privado usado para compilar, nem contém caminhos de perfis pessoais.

Para produzir uma distribuição, indique o ZIP compatível e uma saída nova:

```sh
python3 tools/package_suite.py --pacote-nativo /caminho/irixclassic-domainos-0.2.11.zip --saida /caminho/irix-suite-0.2.11.tar.gz
```

Depois de extrair, entre em `irix-suite-0.2.11` e execute, como o próprio usuário:

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
```

Essa distribuição gráfica contém os três temas como opções. Os áudios SGI são
opcionais e não acompanham esse arquivo; a seleção de sons é preservada quando
eles não estão instalados. Fontes somente leitura são copiadas para uma área
privada gravável antes de preparar recursos; seus bytes e permissões permanecem
intactos. Instalar opções não equivale a aplicar um tema.

`aplicar-tema.sh classic|moderno|domainos` usa o aplicador nativo do Plasma sem
`--resetLayout` e escolhe o Kvantum correspondente. Inclui GTK 2/3/4 na seleção, preservando
as outras preferências dos arquivos `settings.ini`. Seleciona sons SGI somente
quando o esquema está instalado e validado. `--exigir-sons` recusa a aplicação
sem os áudios; `--sem-sons` preserva a seleção. Volume e habilitação não mudam.

A aplicação captura configurações antes de escrever, inclusive GTK/Qt, e guarda
um recibo em `XDG_STATE_HOME/irixium-selection`. Falhas comuns restauram as cópias
anteriores. A restauração recusa arquivos alterados depois da aplicação.

### Pontes e painel do tema global DomainOS

A instalação normal copia os runtimes GTK/Kvantum e Global para o XDG do usuário,
sem depender do checkout. Dentro da própria sessão KDE, também inicia suas
unidades de usuário. `--sem-integracao` dispensa esse fluxo; `--sem-cache` permite
instalar em testes sem gerenciar serviços ou atualizar caches. Se a instalação
ocorreu fora da sessão nativa, inicie depois no terminal dessa sessão:

```sh
python3 tools/theme_companion_bridge.py --instalar --iniciar
python3 tools/domainos_style_bridge.py --temas-globais --iniciar
```

A ponte GTK/Kvantum registra o Tema Global efetivo ao iniciar. A reconciliação
inicial e alterações apenas de cores preservam seleções independentes; uma
mudança posterior da identidade do Tema Global seleciona seus componentes.
Reaplicar a mesma identidade não é uma transição para esse observador; use os
comandos explícitos de aplicação ou sincronização nesse caso.

Instalar a ponte Global registra a seleção atual e não insere nem substitui
painéis. Escolher explicitamente **IrixClassicDomainOS** pelo Tema global ou por
`aplicar-tema.sh domainos` autoriza substituir um painel e registrar seu estado
anterior em `XDG_STATE_HOME/irixium-domainos-panel`. A migração confere geometria,
preferências e bandeja antes de remover o original. Um layout inicial que já
contenha o applet DomainOS não recebe outra instância nem backup fictício.

Escolher o Global Classic ou Moderno restaura o painel anterior somente quando
essa ativação foi feita pelo Global. Voltar ao Global DomainOS usa as preferências
da sua instância salva. O processo mantém as áreas de trabalho e usa o KDE nativo,
sem reset geral. Uma ativação manual anterior continua independente.

Com múltiplos painéis, a ponte recusa adivinhar a primeira migração. Consulte os
IDs na própria sessão e substitua `ID` pelo painel escolhido:

```sh
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print(JSON.stringify(panels().map(p => ({id:p.id,screen:p.screen,location:p.location}))))'
python3 tools/domainos_style_bridge.py --temas-globais --painel ID --iniciar
```

Se o Global DomainOS já estiver selecionado antes de instalar sua ponte, a
ativação explícita continua disponível:

```sh
python3 tools/activate_domainos.py --global --painel ID --verificar
python3 tools/activate_domainos.py --global --painel ID
```

O controle da ponte fica em `XDG_STATE_HOME/irixium-domainos-style-bridge`; seu
runtime fica em `XDG_DATA_HOME/irixclassic/domainos-style-bridge`. A mesma unidade
`irix-domainos-style-bridge.service` atende a integração Global e a associação
opcional entre Plasma Style e painel. Esta última exige opt-in anterior, iniciado
com `domainos_style_bridge.py --instalar --iniciar` depois de uma ativação manual.
As duas associações usam um único observador. Falhas de ativação interrompem a tentativa;
mudanças internas de recibos não causam repetição automática da falha.

### Restauração da suíte e limite do painel

Se a barra DomainOS estiver ativa e também quiser retirar seu painel, primeiro
selecione o Global Classic ou Moderno para restaurar o layout autorizado, ou use
`python3 tools/activate_domainos.py --restaurar` para sua ativação manual. A
restauração de arquivos abaixo não substitui esse procedimento de layout.

```sh
bash instalar-irixium.sh --restaurar --verificar
bash instalar-irixium.sh --restaurar
bash aplicar-tema.sh --restaurar
```

A restauração da suíte valida o controle/runtime da ponte antes de remover
componentes. Edições posteriores são recusadas. Na execução normal, para sua
unidade antes da remoção e desativa a observação Global, com backup do controle.
Se a ponte era somente Global, fica desabilitada; um Style opt-in anterior mantém
sua habilitação e retoma depois da restauração. `--sem-cache` dispensa o
gerenciamento de serviços, mas também desativa a observação Global no controle.

Helpers, unidades e backups dessa ponte são conservados para recuperação; não
há remoção de seus históricos. Os helpers somente Global permanecem inativos.
Essa restauração não modifica painéis, áreas de trabalho nem preferências Plasma.
A [validação do fluxo](../tests/test_install_suite_global_restore.py) cobre parada
antes da remoção, dry-run, preservação do Style opt-in e bloqueio de edições.

No checkout completo, sons mantêm importação, verificação e backups separados
em `sons/`. Seus scripts não acompanham a distribuição gráfica pré-compilada.
No checkout, o download é solicitado explicitamente por
`sons/instalar.sh --baixar`; a instalação gráfica não baixa áudios. Os antigos
instaladores que substituíam QML compartilhado
foram removidos. Backups antigos no perfil não foram apagados.

O hook opcional da Classic instala seu runtime em
`XDG_DATA_HOME/irixium/hooks/classic`, sem apontar para a pasta de origem. Ele
mantém o pacote disponível e preserva a decoração selecionada. A suíte migra
somente os serviços legados reconhecidos dessa origem; serviços personalizados
são preservados. Instalar a suíte não habilita nem inicia um hook novo.

A ponte de estilos opcional usa a mesma instalação local descrita acima.
Os serviços usam esses arquivos instalados, não a pasta extraída. Caminhos
com espaços, `%` e `$` são preservados nos comandos e no ambiente do serviço.

### Cores, GTK e Kvantum

Os perfis selecionam `IrixClassic-KDE`, `Irixium-KDE` ou
`DomainOS-SR10-4-KDE` no GTK. As cópias GTK 2 são instaladas também em `~/.themes`;
as três famílias adaptáveis e suas variantes `-Reload` têm recursos próprios.
A ponte lê as cores exportadas pelo GtkConfig do KDE, gera bundles GTK 2
recuperáveis e recarrega o CSS GTK 3/4. As fontes standalone continuam preservadas.

Depois de aplicar somente um esquema em Configurações do Sistema → Cores,
atualize também os aplicativos Qt pelo script manual:

```sh
python3 tools/apply_kvantum_colors.py
```

O script consulta a paleta real do KDE e a família do Global atual. Gera aliases
locais `-KDE`/`-KDE-Reload`, preserva as fontes Kvantum e notifica os aplicativos
Qt. Edições posteriores nos recursos ou na seleção independente são respeitadas
ou recusadas conforme seus recibos. Consulte [GTK](../gtk/README.md) e
[Kvantum](../kvantum/README.md) para os limites de engines, estados desativados e
aplicativos que controlam sua própria aparência.

Atualizar arquivos não substitui o QML em memória. Encerre normalmente a sessão
para carregar a decoração nova. Não há atomicidade com outros programas que
alterem preferências simultaneamente, nem reinício forçado do compositor.
