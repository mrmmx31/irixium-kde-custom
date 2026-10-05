# Validação — IrixClassic 0.1.0-rc2, bloco 1

Base consultada: `#kvantum-classic-rc1`, commit
`37041b016770145e919032796ebb55c2285df528`.
Os blobs de configuração, SVG, gerador, manifesto, README, proveniência e
instalador foram conferidos contra o remoto antes de editar as cópias locais.

Compatibilidade reconferida no tip `404ac959fdce9c1e32d0a06c4dd889e877f02c15`.
As árvores Kvantum e o blob do instalador-alvo permanecem idênticos. As novas
alterações de janela/menu no remoto ficam fora deste delta e são preservadas.

## Executado nesta entrega

- 53 testes Python: 17 da candidata anterior, 29 da rolagem, seis de integração
  com o carregador/manifesto e um teste opcional de rasterização independente.
  Todos passaram neste ambiente.
- O teste de rasterização decodificou 115 elementos de rolagem do SVG usando
  CairoSVG/Pillow e comparou os pixels com os mapas. Não é o engine Qt/Kvantum.
- Preservação de 1.739 elementos SVG preexistentes fora das setas de rolagem,
  incluindo IDs, atributos e coordenadas. Novos elementos são adicionados ao
  final do atlas; não deslocam as peças dos outros controles.
- Configurações efetivas dos demais controles, após resolver herança, idênticas
  à rc1. A nova propriedade global `center_scrollbar_indicator=false` é exclusiva
  da scrollbar e explicita o padrão do engine. Versionamento/comentário atualizados.
- Triângulo superior, faixas laterais, tampas e composição das ranhuras comparados
  com amostras independentes do PNG IRIX fornecido, guardadas em JSON de teste.
- Regeneração determinística do SVG, IDs únicos, coordenadas inteiras, recursos
  explícitos e manifesto de integridade conferidos.
- Carregador aceita rc1/rc2 e rejeita versão desconhecida ou bytes corrompidos.
  Seu plano padrão só inclui arquivos em `Kvantum/IrixClassic`.

## Não executado / não anunciado como validado

A galeria Qt 6 nativa retornou **77**, pois não há PyQt6/PySide6 neste ambiente.
Logo, os testes QtTest, carregamento do plugin Kvantum, XWayland/Wayland, KWin,
arraste nativo, extremos e RTL **não estão aprovados aqui**. A galeria e oito
verificações de eventos estão incluídas para rodar na máquina de teste.

`PREVIA-ROLAGEM.png` e `ESTADOS-ROLAGEM.png` são composições técnicas. Elas não
representam uma captura de execução nativa nem demonstram um comportamento de
mouse por si só. O estado desativado do puxador modela o código de opacidade
0,7 do Kvantum; o resultado depende da superfície real por baixo.

## Continuidade

No plano mestre, bloco 1 = implementado/candidato, aceitação local pendente.
Blocos 2–7 = revisão histórica e implementação específica pendentes. O tema não
é anunciado como reconstrução integral de todos os controles/comportamentos.

Para repetir os testes:

```sh
bash kvantum/testar-rolagem.sh
bash kvantum/prever-rolagem.sh --testar --capturas /tmp/irixclassic-rolagem-qt
```

CairoSVG/Pillow são opcionais: sem eles, o teste de rasterização é marcado como
skip, não sucesso. Nenhum dos comandos instala dependências.
