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
