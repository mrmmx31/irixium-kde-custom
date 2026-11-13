# IRIX Classic Shortcuts

O layout novo usa `applications:<arquivo.desktop>` para os atalhos. O navegador
é o preferido do próprio usuário, informado pelo Plasma; Dolphin e Konsole usam
seus identificadores desktop. O Qt resolve os arquivos em `XDG_DATA_HOME` e
`XDG_DATA_DIRS`, incluindo instalações locais e diretórios de exportação de apps.
Identificadores com espaços ou `%` usam codificação de URL; caminhos relativos
de arquivos desktop também são aceitos. Arquivos ausentes não lançam outro app.

O modelo e a configuração mantêm os tokens originais. Somente os argumentos
do backend nativo de metadados, lançamento, edição e exportação por arrastar
recebem a URL local resolvida. URLs `file:` existentes passam sem alteração,
inclusive durante a migração de painéis. Nenhum navegador é imposto, nenhuma
preferência é escrita, e os handlers nativos de clique, popup e arrastar continuam
em uso.

Para organizar os atalhos, clique com o botão direito em um deles e abra
**Organizar atalhos (Organize Launchers…) → Atalhos (Launchers)**. A lista oferece **Adicionar**,
**Substituir**, **Remover**, **Subir** e **Descer**. Substituir mantém a posição do
item e usa o seletor nativo de aplicações, sem editar o arquivo `.desktop` do
aplicativo. Por exemplo, selecione Dolphin e substitua por IRIX Classic Files.
As alterações da lista entram em vigor com **Aplicar** ou **OK**; **Cancelar**
mantém os atalhos anteriores. Cancelar o seletor de aplicações também não muda
a lista. Se a lista mudar enquanto o seletor de substituição estiver aberto, a
escolha é recusada para evitar substituir outro item.

Também é possível reordenar arrastando no modo de edição do Plasma, ou focando
um atalho e usando **Ctrl+Shift+setas**. A lista de configuração permite organizar
os atalhos sem depender desses gestos.

A prova nativa pode ser executada com
`python3 plasma/tools/testar-atalhos.py --saida /tmp/irix-atalhos-teste` a partir
do repositório. Ela usa a página real em um host Plasma privado e exercita o
seletor de aplicações do KDE, incluindo cancelamento e substituição. O teste
modela a transferência de `cfg_launcherUrls` ao aplicar ou descartar a página;
o diálogo completo de configuração do Plasma não faz parte desse host.
