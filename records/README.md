# Registros locais dos contextos de IA

`ia-tema/` guarda o diretório de trabalho anteriormente em `~/tempia/ia-tema/`.
Ele contém evidências I167, fontes de apoio, backups, experimentos e estados de
instalação usados para retomar a revisão do tema. A migração foi um rename no
mesmo filesystem, sem cópia concorrente nem descarte: 94.496 arquivos regulares,
2.379 symlinks e 3.891 diretórios. Os arquivos ocupam 865.815.471 bytes em
tamanho lógico; `ia-tema/MIGRATION-MANIFEST.jsonl.gz` registra hashes SHA-256.
O diretório bruto é local e ignorado pelo Git por conter capturas, cópias de
recuperação e outros artefatos de execução; os resultados revisados e seus
limites ficam versionáveis em `docs/review/` e na fila visual.

O caminho antigo `~/tempia/ia-tema` permanece como symlink de compatibilidade
para `records/ia-tema`. Novos temporários devem ficar em
`~/tempia/domainos-theme-work/`, fora do repositório. Não remova o symlink
enquanto a sessão GTK2 Xephyr `:187` ou os leitores dos documentos migrados
continuarem abertos.
