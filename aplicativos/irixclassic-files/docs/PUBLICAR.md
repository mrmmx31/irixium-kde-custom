# Publicação explícita da alpha

A numeração do aplicativo é independente da versão estável Kvantum. Publicar como
`irixclassic-files-v0.1.0-alpha1`, sempre **prerelease**. Nenhum script de build
publica, altera tags ou modifica branches.

Depois de incorporar o kit ao novo branch, revisar e fazer commit/push, execute
o build. A árvore deve estar limpa para publicar. O recibo precisa corresponder
exatamente aos arquivos atuais da integração e aos pacotes gerados.

```bash
bash aplicativos/irixclassic-files/publicar-alpha.sh --trabalho "$trabalho"
```

A chamada acima é apenas a verificação local. Com `gh` autenticado, o comando
abaixo cria a tag/release no repositório e envia os arquivos:

```bash
bash aplicativos/irixclassic-files/publicar-alpha.sh \
    --trabalho "$trabalho" --publicar
```

O script confirma o origin e a presença do commit no remoto, recusa tag existente,
cria rascunho, envia binário/fonte/checksums, baixa os assets e compara seus bytes.
Só depois publica a prerelease e salva `PUBLICACAO.json`. Não substitui tags/arquivos
nem usa `--force`. Uma falha após criar o rascunho deixa a publicação incompleta
visível no GitHub; examine esse rascunho, não force uma segunda tag sobre ele.

O workflow de CI oferece artefatos após o build. Para publicar pela interface web,
escolha explicitamente o commit do branch, inclua o binário e a fonte correspondente,
marque prerelease e não use o rótulo stable/latest. Não se exige nova aprovação do
Kvantum, que é outro componente e continua intocado.

Depois do lançamento, correções recebem alpha2 ou nova versão. Não substituir os
arquivos da alpha1 publicados com conteúdo diferente.
