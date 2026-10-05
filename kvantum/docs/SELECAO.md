# Bloco 4 — caixas de seleção e botões de opção

Revisão **0.4.0-rc1**, manutenção `mrmmx31`. Recursos novos isolados;
blocos 1–3, decoração, fontes globais e Irixium moderno preservados.

## Referência e alcance

O manual da SGI, *Indigo Magic User Interface Guidelines*, capítulo 9,
descreve checkbox independente com marca vermelha e radio exclusivo com
triângulo azul. A imagem do `gscan` no manual *IRIX Scanner Administration
Guide*, capítulo 6, também permite observar o contorno em losango dos radios.
O capítulo 3 documenta o **locate highlight**: clareamento sob o ponteiro.

Fontes primárias preservadas:
- https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch09.html
- https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/ch03.html
- https://techpubs.jurassic.nl/library/manuals/1000/007-1633-060/sgi_html/ch06.html

As figuras de controles do capítulo 9 não foram recuperadas como arquivos
brutos nesta revisão. Não existe uma comparação pixel a pixel com elas.
A forma, a cor funcional e o modelo de seleção têm base histórica; coordenadas,
cores RGB exatas e espessuras são adaptação original à célula **15×15** já usada.
O estado parcial (barra vermelha) é extensão do Qt, não certificado como IRIX.

## Implementação

`selection_art.py` acrescenta **52 recursos** ao atlas. Nenhum dos **2517**
recursos anteriores é substituído ou reposicionado. A configuração troca apenas
`interior.element` de `CheckBox` e `RadioButton` (além do comentário de versão).
`check_size=15`, margens, fontes, layout e áreas clicáveis ficam intactos.

| Estado | Desenho / responsável |
|---|---|
| Desmarcado | Caixa ou losango rebaixado, sem marca de seleção. |
| Marcado | Marca vermelha ou triângulo azul; a forma também distingue o estado. |
| Parcial | Barra horizontal vermelha, diferente do sinal de confirmação. |
| Ponteiro | Clareamento da face, sem animação, sem selecionar o controle. |
| Foco de teclado | Contorno de foco existente, separado do estado da marca. |
| Indisponível | Tratamento nativo do Kvantum; controle permanece visível e bloqueado pelo aplicativo. |
| Menu/lista | Prefixos `menu-` e `item-` próprios conforme a rota suportada pelo motor. |

Não alteramos o hover dos botões já aprovados. O clareamento desta família é
fundamentado no manual; não generalizamos a ausência de hover da decoração
externa para toda a interface de aplicativos.

## Limites reais do Kvantum 1.1.4

O código `PE_IndicatorCheckBox` / `PE_IndicatorRadioButton` seleciona os sufixos
`normal`, `focused`, `checked-normal`, `checked-focused` e, para checkboxes,
`tristate-normal` / `tristate-focused`. Ele **não consulta `State_Sunken` para
escolher um SVG pressed separado** nestes indicadores. Incluir esse desenho no
arquivo não faria o motor utilizá-lo. Não mascaramos essa limitação transformando
hover em pressão ou alterando a seleção no evento errado.

A indisponibilidade usa a variante normal correspondente à seleção, com
opacidade **0.7**; o motor não solicita um SVG `disabled` específico aqui.
A prévia simula essa composição sobre cinza, não anuncia um teste do plugin.
Menus de Qt Widgets usam `menu-`; checkboxes em itens de vistas usam `item-`.
Qt Quick pode utilizar o caminho sem esses prefixos.

Código auditado:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp

Exclusividade, mudança de estado, atalhos, bloqueio e acessibilidade são funções
do Qt e do aplicativo. Este tema não injeta eventos nem substitui esses widgets.

## Teste local

Na raiz do clone:

```sh
bash kvantum/testar-selecao.sh
bash kvantum/prever-selecao.sh
bash kvantum/prever-selecao.sh --testar
```

A galeria carrega o plugin Qt 6 real em configuração temporária. Testar mouse,
Tab/Espaço, seleção parcial, exclusividade, disabled, menus e itens de árvore.
`--tema Irixium` compara com o moderno sem selecionar outro tema no desktop.
Dependência ausente retorna **77**, nunca aprovação. A galeria limita suas
fontes ao processo de teste e não distribui fontes.

A candidata está implementada para validação; nenhum ensaio Qt/KDE foi executado
no ambiente de preparação. Próximo bloco: **5 — menus**.
