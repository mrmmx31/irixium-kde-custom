# Validação do desenho Irix Classic DomainOS — 2026-10-08

O esquema de cores se chama **DomainOS SR14.4**, conforme a confirmação do
usuário. `IrixClassicDomainOS` é uma opção independente. Os 38 arquivos do
Plasma Style Classic original permanecem idênticos ao inventário registrado
antes desta adição. Os 27 componentes anteriores, os dois perfis globais e a
configuração dos sons permanecem iguais; o catálogo acrescenta três opções,
totalizando 30 componentes.

## Desenho e fontes

O painel usa a composição fornecida pelo usuário, com base de 1942×218 pixels:
quatro instrumentos, sete itens na Iconbox, dois quadros de áreas, bandeja
2×3, setas ▶/▲ e cinco atalhos na faixa inferior. Os símbolos fixos e as
texturas são novos desenhos vetoriais inspirados na referência HP nítida.
Os bitmaps da Iconbox são cópias verificadas dos ícones IRIX do repositório.
As capturas de referência não são distribuídas no pacote.

Os testes nativos confirmaram DejaVu Sans Mono e Nimbus Sans, esta última
resolvida como `Nimbus Sans [UKWN]`, sem substituição de família. O desenho
reconstrói as texturas e relevos sem copiar o borrado da imagem de projeto.
O relevo tem bandas mais simples que a referência, e os símbolos fixos são
redesenhos; a revisão visual pelo usuário continua sendo necessária.

## Verificações executadas

| Verificação | Resultado | Limite da evidência |
| --- | --- | --- |
| `tests/test_components.py` e `tests/test_user_bundle.py` | 20 testes aprovados | Catálogo, independência dos defaults e instalação/restauração dos três novos recursos, preservando preferências, layouts e esquema vizinho |
| `tests/test_domainos.py` | 4 testes aprovados | Baseline Classic, origem/hash dos SVGs, cópias SGI e nome/hash do esquema SR14.4 |
| `plasma/tools/prever-domainos.py` | 96 verificações aprovadas | QML de produção, composição, pressão/cancelamento em 28 botões, geometria preservada e escala de 50% |
| `plasma/tools/testar-domainos-package.py` | 21 verificações aprovadas | KPackage real em `plasmawindowed`, fullRepresentation visível em 1942×218, 40 imagens carregadas, fontes resolvidas e zero erros QML |
| `plasma/IrixClassicDomainOS/tools/verify_artwork.py` | 14 verificações aprovadas | Qt6 QSvgRenderer, KSvg, trama sem esticar, recursos de controles, relevo e superfícies opacas |
| Instalador completo e auditoria em XDG temporário | 30 componentes instalados e auditados, zero falhas | Instalação offline, cópias de compatibilidade de cursores/GTK e restauração, com seleção/layouts/áreas preservados |

O builder/verifier do Style também foi executado novamente sem alterações dos
hashes de saída. As ferramentas não deixam `__pycache__` no componente instalado.
O teste da galeria captura o mesmo QML que o applet carrega; não é um mockup
separado. Os testes usam diretórios privados, e a prova do KPackage utiliza
Xvfb com D-Bus sem ativação de serviços da sessão real.

## Fase e decisões pendentes

Hora/data, gráfico, janelas, miniaturas das áreas e status da bandeja são
amostras de desenho. **Nenhuma função de botão está aprovada ou implementada.**
Os botões apenas mostram pressão/cancelamento, sem timer ou animação no produto.
Os tempos de espera dos runners servem exclusivamente para capturar a imagem.

Não foram testadas ativação de janelas minimizadas, troca/criação de áreas,
ações de bandeja, lançadores, bloqueio, ajuda, coleta real de sensores ou
migração de painel. Essas funções e a seleção final permanecem registradas
como pendentes em [DOMAINOS-REQUISITOS.md](DOMAINOS-REQUISITOS.md), F01–F31.
A instalação dos arquivos não seleciona o novo Style/esquema nem modifica o
painel. `aplicar-tema.sh classic` mantém o comportamento anterior.

Os três novos recursos também foram disponibilizados no perfil **lsi**,
com recibo próprio em `~/.local/state/irixium-domainos-design`. A comparação
antes/depois confirmou as configurações protegidas e o Style Classic intactos.
A auditoria local passou para os 30 componentes e para a seleção Classic,
sem divergências. Nenhum painel DomainOS foi inserido. **p001532 não recebeu
estas novas opções nesta etapa**; não há certificação de execução nelas nesse
perfil.
