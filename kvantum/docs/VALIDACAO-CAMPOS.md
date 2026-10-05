# Validação — 0.3.0-rc1

## Executado neste ambiente

- 111 testes de tema/contrato: todos passaram. Incluem regressões dos blocos
  anteriores, 385 novos elementos rasterizados por CairoSVG e comparados aos
  mapas inteiros, preservação de todos os 2.132 recursos anteriores e sua
  posição no atlas, configurações herdadas, manifesto e contrato Qt Quick.
- 29 testes do mecanismo de atualização/recuperação em arquivos temporários:
  todos passaram. Não foram executadas operações administrativas reais.
- Verificação da expressão JavaScript efetivamente inserida no QML com Node:
  pressão esquerda, outra seta, saída, soltura, botão do meio e puxador nativo.
- Testes do reparo QML em fixture sintética: cinco substituições exatas,
  idempotência, recusa de fonte ambígua/editada, prefer conhecido, fontes locais
  ausentes, symlinks, cancelamento e instalação/restauração temporária.
- Os diretórios-base IrixClassic, kvantum/tools, kvantum/tests e tools coincidem
  com os objetos Git remotos de 5f28bdc; o plano-base também coincide.
- Patch convencional: git apply --check, aplicação, bytes/permissões e reversão
  conferidos em checkout temporário. Aplicador: 10 testes passaram, incluindo dry-run, aplicação, idempotência,
  reversão, divergência, stage, commit posterior, colisão e arquivo não relacionado.

## Não executado

Qt/PyQt6/PySide6, plugin Kvantum e sessão KDE/KWin não estão disponíveis neste
ambiente. As duas galerias nativas retornaram 77. Não foram contabilizadas como
aprovadas. CairoSVG e testes da expressão não são uma renderização do Qt.

A causa da pressão foi encontrada no código KDE v6.13.0. O reparo só aceita
instalações com as âncoras e o contrato correspondentes; não prova que toda
falha visual de qualquer aplicativo tenha essa causa. Confirmar a pressão no
StyleItem real e o carregamento pelo qmldir na máquina de destino.

Os estados e mapas dos novos campos são adaptações fundamentadas nas referências,
não reprodução certificada de cada estado do IRIX. Cor separada de readonly em
todos os apps não pode ser fornecida apenas pelo SVG do Kvantum 1.1.4.

## Artefatos

PREVIA-CAMPOS.png é composição técnica dos mapas sem interpolação adicional,
não captura nativa. Dados de regressão em tests/data/entries-baseline.json
identificam o commit-base e as configurações anteriores.
