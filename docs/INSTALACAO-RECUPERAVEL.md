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

`instalar-irixium.sh` lê `components.json`, verifica os componentes e prepara
cópias temporárias antes de substituir destinos. Guarda recibos e os arquivos
anteriores em `XDG_STATE_HOME/irixium-suite`. Não grava seleção nem recursos de
sistema. Destinos compartilhados e links externos são recusados.

`aplicar-tema.sh classic|moderno` usa o aplicador nativo do Plasma sem reset de
layout e escolhe o Kvantum correspondente. Inclui GTK 3/4 na seleção, preservando
as outras preferências dos arquivos `settings.ini`. Seleciona sons SGI somente
quando o esquema está instalado e validado. `--exigir-sons` recusa a aplicação
sem os áudios; `--sem-sons` preserva a seleção. Volume e habilitação não mudam.

A aplicação captura configurações antes de escrever, inclusive GTK/Qt, e guarda
um recibo em `XDG_STATE_HOME/irixium-selection`. Falhas comuns restauram as cópias
anteriores. A restauração recusa arquivos alterados depois da aplicação.

```sh
bash instalar-irixium.sh --restaurar --verificar
bash instalar-irixium.sh --restaurar
bash aplicar-tema.sh --restaurar
```

Sons mantêm importação, verificação e backups separados em `sons/`. O download
é solicitado explicitamente por `sons/instalar.sh --baixar`; a instalação gráfica
não baixa áudios. Os antigos instaladores que substituíam QML compartilhado
foram removidos. Backups antigos no perfil não foram apagados.

O hook opcional da Classic instala seu runtime em
`XDG_DATA_HOME/irixium/hooks/classic`, sem apontar para a pasta de origem. Ele
mantém o pacote disponível e preserva a decoração selecionada. A suíte migra
somente os serviços legados reconhecidos dessa origem; serviços personalizados
são preservados. Instalar a suíte não habilita nem inicia um hook novo.

A ponte de estilos opcional também copia seu runtime para o XDG do usuário.
Seus serviços usam esses arquivos instalados, não a pasta extraída. Caminhos
com espaços, `%` e `$` são preservados nos comandos e no ambiente do serviço.

Atualizar arquivos não substitui o QML em memória. Encerre normalmente a sessão
para carregar a decoração nova. Não há atomicidade com outros programas que
alterem preferências simultaneamente, nem reinício forçado do compositor.
