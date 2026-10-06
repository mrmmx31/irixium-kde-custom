# Distribuição do IrixClassic Kvantum

**Lançamento ativo: 0.7.1 estável**, promovido explicitamente da candidata aceita
em 06/10/2026. `LANCAMENTO.json` é o registro ativo. `CANDIDATA.json` e o fechamento
anterior são histórico: seus resultados não são reescritos para simular a promoção.

```sh
bash distribuicao/testar.sh
bash distribuicao/gerar-kvantum.sh --verificar
bash distribuicao/gerar-kvantum.sh --saida /caminho/novo/fora-do-clone
```

São gerados o tema mínimo, o código-fonte correspondente, `SHA256SUMS` e
`DISTRIBUICAO.json`, todos identificando canal stable e aprovação explícita.
Nenhum desses comandos instala ou publica. O novo estado não exige outra rodada
de aceite do mesmo desenho; a equivalência funcional é conferida por hash normalizado.

Para publicar o commit já revisado e enviado ao GitHub:

```sh
bash distribuicao/publicar-estavel.sh --verificar
bash distribuicao/publicar-estavel.sh --publicar
```

O segundo comando escreve no GitHub. Ele usa a tag específica
`irixclassic-kvantum-v0.7.1`, envia os artefatos a um rascunho, confere por download
e publica a release normal (não prerelease). Não sobrescreve uma release já
publicada nem move uma tag. Não usa `--force`, `--clobber` ou `git push --tags`.
Detalhes: `PUBLICAR-ESTAVEL.md`. Notas públicas: `NOTAS-0.7.1.md`.

Futuros ajustes serão novas versões. Moderno, decoração, GTK, fontes, logs privados
e correção do KDE permanecem fora dos dois pacotes Kvantum. Artefatos não assinados.
