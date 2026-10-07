# Cursores SGI — validação de 06/10/2026

## Causas encontradas

O cursor `wait` apontava para `left_ptr_watch`, e os arquivos `watch` e
`left_ptr_watch` tinham bytes idênticos: uma ampulheta estática. Espera e
progresso não eram distinguidos. Faltavam nomes diretos usados por Qt/KWin e
Wayland, incluindo `default`, `grab`, `grabbing` e os aliases de redimensionamento.
Os aliases de linha/coluna também precisavam corresponder aos eixos corretos.

O pacote tinha apenas tamanho nominal 32, com seta visível 11×18 e hotspot
(5,5), enquanto a preferência local era 48. Não havia pixels próprios para 48.

Além disso, a biblioteca instalada anunciou o caminho nativo
`~/.icons:/usr/share/icons:/usr/share/pixmaps`. O instalador mantinha somente
`~/.local/share/icons/sgi`, enquanto o KDE listava a cópia antiga em `~/.icons`.
A descoberta nativa não listou as variantes novas antes da correção desse destino.

## Alteração

- Três variantes: `sgi`, `SGI-Classic` e `SGI-Irixium`, com 142 nomes/aliases
  e 51 arquivos de imagens por variante. Derivam da mesma base documentada;
  não são três distribuições oficiais distintas.
- Tamanhos 24, 32, 48, 64 e 96, com hotspots proporcionais e manifestos.
- Espera/progresso distintos em todas as variantes. Classic e Irixium usam
  relógio com oito quadros nativos de 125 ms; o indicador de progresso mantém
  a seta. A variante `sgi` preserva a ampulheta como alternativa.
- Nomes padrão cobertos, incluindo mãos aberta/fechada, texto vertical, zoom,
  DND e redimensionamento. Foram mantidos os créditos e a declaração GPL upstream.
- Perfis globais e aplicação GTK/KDE associados às respectivas variantes.
- Instalação em `XDG_DATA_HOME/icons` e cópias de compatibilidade em `~/.icons`,
  usando a transação existente com backup e restauração. São 17 componentes
  gráficos únicos e três destinos adicionais de compatibilidade.

O conteúdo original conferiu com os Git blobs upstream no commit
`b7a02161f8e13da639d2ecff5735436c9f447d67`. As fontes imutáveis, hashes e
aliases anteriores ficam em `cursors/sources/`. `.directory`, metadado do
Dolphin, foi retirado do payload de cursores.

## Evidência

Passaram **62 testes de integração/instalação** e **7 testes dos cursores**.
O carregador real libXcursor passou em **525 consultas**: 35 papéis × cinco
tamanhos × três temas. Cada consulta conferiu os pixels, hotspots, tamanho e
todos os quadros carregados, sem recorrer a outros temas.

Em perfil e barramento temporários, instalação, repetição, descoberta nativa
dos três temas, seleção de ambos os perfis no KDE/GTK e restauração passaram.
O teste preservou `cursorSize=48` e uma chave pessoal de mouse. A restauração
da instalação também retirou as três cópias de compatibilidade criadas para
o teste. Log em `/tmp/irix-cursor-profile-zmkzfy65/cycle.log`.

No perfil real, o instalador manteve backups, a ferramenta nativa
`plasma-apply-cursortheme` reconheceu os três temas e selecionou `SGI-Classic`
com tamanho 48 preservado. GTK 3/4 recebeu o mesmo nome sem alterar outras
preferências. Backup da seleção:
`~/.local/state/irixium-cursor-selection/55a97895dc3941c9868a55d323a9f330`.

A auditoria final `tools/audit_suite.py --local --exigir-sons` passou: nenhum
componente diferente, três cópias legadas idênticas, perfil Classic sem
divergências e esquema de sons existente íntegro. Relatório privado em
`/tmp/irix-cursors-user-audit.json`. Nenhuma instalação no sistema ou configuração
de outro usuário foi alterada; o auditor externo dos ícones não foi versionado.

As proporções da seta são preservadas na base nominal 32. A comparação mostra
pixels nominais e visíveis; não é prova de dimensão física igual à de hardware
SGI. A imagem de revisão foi gerada por `cursors/tools/preview.py` a partir dos
arquivos Xcursor reais, não por uma captura de todas as aplicações. Aplicações
só exibem o cursor ocupado quando solicitam o estado ao toolkit/compositor.
