# Cobertura do estilo e revisão integrada

**0.7.0-rc1 · `mrmmx31`.** O roteiro tem sete blocos implementados para ensaio,
mas implementação não equivale a aceitação em KDE nem a identidade histórica.
A referência mestre de continuidade é `../PLANO-IRIXCLASSIC.md`.

| Família | Entrega | Referência/limite | Situação de aceitação |
|---|---|---|---|
| Scrollbar: setas, trilho, puxador, ranhuras, duas orientações | Bloco 1 | Partes comparadas com prints fornecidos; estados derivados documentados | Desenho aprovado; problema de ação/pressão em Qt Quick **aberto** |
| Comando, padrão, ferramenta e toolbar | Bloco 2 | Perfil de borda amostrado; estados de interação adaptados | Aprovado pelo usuário |
| LineEdit, combo, spinbox e molduras | Bloco 3 | Referência SGI de entradas/opções; readonly não possui recurso SVG exclusivo | Entregue; conferir em aplicativos |
| Checkbox, parcial, radio, marcas em menu/vista | Bloco 4 | Marca vermelha e triângulo azul documentados; parcial adaptado | Entregue; pressão separada limitada pelo motor |
| MenuBar, popup, contexto, itens, separação, submenu, tear-off | Bloco 5 | Perfil de barra amostrado; estados derivados; tear-off requer suporte do aplicativo | Entregue; navegação e Qt Quick em revisão |
| Abas ligadas à página e de documentos, foco, fechar, excesso | Bloco 6 | Princípio ViewKit documentado; medidas/adaptação Qt próprias | Entregue; quatro orientações em revisão |
| Sliders/scales e progresso | Bloco 7 | Princípio SGI; aparência exata adaptada ao QStyle | Implementado para teste |
| Cabeçalhos, linhas de dados, listas e árvores | Bloco 7 | Relevo/paleta de família; medidas exatas adaptadas | Implementado para teste |
| Divisores, group boxes, tooltips, docks e size grip | Bloco 7 | Primitivas dedicadas; layouts continuam nativos | Implementado para teste |
| Dial | Bloco 7 | Recurso Qt com desenho próprio; não reproduz um dial específico SGI | Implementado; marcas decorativas, não escala calibrada |
| Toolbox | Nativo | Forma calculada pelo motor; texto e paleta integrados | Não substituído por uma falsa moldura SVG |
| MDI | Bloco 7 + Qt | Subjanela interna, não KWin; alguns ícones/casos continuam Qt | Implementado parcialmente no alcance do QStyle |
| Labels, caret, seleção de texto e ícones do aplicativo | Nativo | Fontes/conteúdo/validações pertencem ao aplicativo; paleta preservada | Não prometer controle de conteúdo por SVG |
| LED, thumbwheel, File Finder e painéis específicos da SGI | Fora do QStyle genérico | Exigem widgets/componentes e lógica próprios; não têm correspondência universal | Não implementados como funcionalidades novas |
| Interfaces HTML/GTK/controles Qt Quick que não passam pelo estilo desktop | Outro mecanismo | Um tema Kvantum não cobre automaticamente essas interfaces | Fora do escopo deste pacote |

## Critérios antes de declarar uma versão estável

1. Conferir cada bloco na escala 100%, preservando a fonte de uso real e também
   comparando a galeria com fonte local de 14 pixels. Nenhuma fonte global muda.
2. Validar mouse, teclado, foco, seleção, indisponibilidade, limites, RTL e pelo
   menos duas aplicações reais. Separar Qt Widgets e Qt Quick nos resultados.
3. Registrar os componentes com referências históricas de cor/geometria e os
   componentes apenas adaptados. Não usar testes de mapa como prova histórica.
4. Resolver ou documentar com reprodução mínima a pendência compartilhada das
   setas. Não marcar o bloco como aprovado porque uma galeria Widgets funciona.
5. Auditar instalação/restauração sem tocar decoração externa, fontes, GTK ou
   Kvantum moderno. Manter código opcional de sistema fora do instalador do tema.
6. Consolidar a galeria e os relatórios após a aceitação local; não substituir
   automaticamente controles já aprovados durante ajustes de outra família.

Nenhum teste nativo não executado deve entrar na contagem de aprovação.
Os números de recursos SVG são números de peças/estados, não de controles
independentes nem de cenários de interface que tenham sido executados.
