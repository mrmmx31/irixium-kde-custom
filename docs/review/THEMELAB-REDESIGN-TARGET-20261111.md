# ThemeLab — contrato visual da proposta de 2026-11-11

Este documento traduz as seis imagens fornecidas pelo usuário em requisitos de
interface verificáveis. Ele não transforma os mockups em renderização nativa e
não registra aceite visual. As cores visíveis nas imagens são ilustrativas: a
implementação continua resolvendo os papéis atuais do KDE e as paletas próprias
das referências nativas, conforme `DOMAINOS-REGRAS-CORES.md`.

## Proveniência

As cópias privadas de trabalho estão em
`~/tempia/domainos-theme-work/themelab-redesign-proposals-20261111-r1/`.
Os anexos originais em `/tmp` foram somente lidos e não foram sobrescritos.

| ID | Uso | Dimensão | SHA-256 |
| --- | --- | --- | --- |
| 01 | Editor de pintura manual | 1536 x 1024 | `2b2be99dbb3fbfd382e21724a3659de5e509ec70594fcb66eb354bcefe10f57d` |
| 02 | Peça e geometria / Cores e relevo | 1024 x 1536 | `57bec9bde1eac6667fe02d233950b6a1263379f70b0b86379a08e7e5a236e268` |
| 03 | Catálogo / Controle e medições | 1024 x 1536 | `cce53cf0e02efd66023b054249838ca457005792f5a832ff7fe5e3ab27153bd3` |
| 04 | Estrutura principal com ferramentas à esquerda | 1672 x 941 | `fa4fb3915480b7e65b4bea0307ed5ae9612e9a095fd910d4b1687824e881c711` |
| 05 | Mapa dos menus | 1672 x 941 | `56072da18b55a57a616ca83bc18082664957a2d7604c6ee33e0a5768220451a7` |
| 06 | Modelo e referências / Código da proposta | 1368 x 1149 | `581b9c45115f6869582d61d950f57b3505bc73950d76c99c1ade37b79506ffe1` |

As pranchas formais 1:1 ficaram em:

- `~/tempia/domainos-theme-work/themelab-redesign-main-compare-20261111-r1/`;
- `~/tempia/domainos-theme-work/themelab-redesign-paint-compare-20261111-r1/`.

As dimensões atuais e propostas diferem. Por isso, os recibos registram
`pixel_diff.status = not_comparable`; a prancha lado a lado serve para inspeção
de estrutura, não para uma porcentagem de fidelidade.

## Dez grupos do redesenho

### 1. Moldura principal

- A barra de título continua pertencendo ao gerenciador de janelas.
- A barra de menus ocupa uma faixa própria, acima de todos os painéis.
- O corpo tem uma coluna de ferramentas à esquerda e a comparação ao centro.
- A área de código deixa de ser uma terceira coluna permanente.

### 2. Menus

A ordem é `Arquivo`, `Referência`, `Comparação`, `Ferramentas`, `Exibir` e
`Ajuda`. As ações existentes são reorganizadas, não duplicadas em uma nova
camada de estado. `Exibir` oferece as seis páginas da coluna esquerda. Cada item
tem dica própria e despacha a mesma ação do controller atual.

### 3. Faixa de contexto

Família, esquema usado na prévia, atualização automática e intervalo em
milissegundos ficam na faixa superior. A mudança não altera o significado:
esquema continua privado da prévia e o intervalo continua sendo debounce, não
duração de operação.

### 4. Navegação lateral

A coluna esquerda tem exatamente seis páginas mutuamente exclusivas:

1. Catálogo;
2. Controle e medições;
3. Peça e geometria;
4. Cores e relevo;
5. Modelo e referências;
6. Código da proposta.

Trocar de página não destrói widgets, não descarta texto e não aplica a receita.
O estado selecionado permanece enquanto o programa estiver aberto.

### 5. Catálogo

Mantém a árvore, categorias, controles, seleção por teclado e visibilidade já
implementadas. A página não cria uma segunda seleção de controle.

### 6. Controle, medições, peça e geometria

`Controle e medições` reúne estado, âncora, posição, tamanho, suporte e medidas
nativas. `Peça e geometria` reúne peça, estado da peça, parâmetros independentes,
geometria compartilhada e cursor de escala GTK2. Medida nativa, mínimo do
toolkit e valor personalizado continuam identificados separadamente.

### 7. Cores e relevo

Reúne fatores e papéis sem inserir RGB final. Face, texto, conteúdo e seleção
são nomes de papéis; luz, sombra e trilho são derivações da paleta corrente.
Estados normal, pressionado, desabilitado e backdrop permanecem distintos.

### 8. Modelo, referências e código

Nome, PNG de referência, notas, limites e resumo da pipeta ficam em `Modelo e
referências`. Busca e código somente leitura ficam em `Código da proposta`.
Selecionar e copiar o código continua permitido; proposta gerada não equivale a
prévia aplicada, tema instalado ou referência histórica.

### 9. Comparação central

Motif e a família-alvo ocupam colunas equivalentes e crescem proporcionalmente.
Os canvases internos mantêm coordenadas correspondentes e escala 1:1, com
rolagem independente. A referência Motif é renderização real da biblioteca
instalada; uma captura histórica permanece identificada e separada. Nenhuma
aproximação desenhada pode receber rótulo de prévia nativa.

### 10. Editor de pintura manual

O editor recebe menus `Arquivo`, `Editar`, `Exibir` e `Ajuda`; uma lateral para
alvo, ferramentas, dimensões, referência e ensaio nativo; e um canvas principal
amplo. Família da arte e fonte da referência continuam escolhas independentes.
Copiar referência ou prévia é explícito e recuperável em um passo de Undo.
Zoom da arte e zoom das amostras continuam separados. Todos os controles têm
dicas, e campos de texto preservam Undo/Redo de vários passos, recortar, copiar,
colar e selecionar tudo com menu e atalhos usuais.

## Mapeamento das ações existentes

| Menu | Ações |
| --- | --- |
| Arquivo | Salvar, Carregar, Importar delta, Exportar, Sair |
| Referência | Imagem histórica, Pipeta |
| Comparação | Atualizar, Prévia separada |
| Ferramentas | Pintura manual, Restaurar família, Reconstruir arquivos, Desfazer projeto, Refazer projeto, Guardar ponto, Voltar ao ponto, Resetar peça |
| Exibir | Seis páginas laterais |
| Ajuda | Assuntos e níveis já existentes |

## Sequência e gates

1. Separar menu, faixa de contexto e páginas laterais sem alterar o controller.
2. Colocar código na sexta página e eliminar a terceira coluna fixa.
3. Tornar Motif/alvo um par horizontal proporcional com canvases 1:1.
4. Reorganizar o editor manual sem remover seletores, peças ou ensaios atuais.
5. Compilar e executar testes de modelo, controller, view, edição e hints.
6. Inspecionar na sessão normal somente quando solicitado pelo usuário; Xephyr
   depende de escolha explícita do usuário.
7. Registrar comparação visual e pedir avaliação humana. Testes técnicos não
   preenchem o aceite visual.

## Critério de conclusão

O redesenho só pode ser declarado concluído quando as ações existentes forem
alcançáveis, as seis páginas preservarem seus estados, a comparação permanecer
1:1, a edição de texto passar o contrato completo, as paletas forem dinâmicas,
os testes técnicos passarem e o usuário avaliar a interface real. Uma captura
do mockup, uma compilação ou uma contagem de testes isolada não satisfazem esse
critério.
