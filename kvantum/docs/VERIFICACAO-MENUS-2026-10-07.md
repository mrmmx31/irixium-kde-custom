# Verificação dos menus IrixClassic — 7 de outubro de 2026

Conclusão: o Kvantum IrixClassic 0.7.1 oferece uma adaptação funcional da
linguagem SGI, mas os menus ainda não podem ser descritos como reprodução
integral do IRIX original. Esta revisão não alterou SVG, kvconfig, seleção de
tema, fontes do usuário ou configurações de outros usuários.

O tema ativo é IrixClassic. Os arquivos locais em
`~/.config/Kvantum/IrixClassic/` coincidem por SHA-256 com os arquivos do
repositório. As galerias usam cópias temporárias para testar o mesmo tema.

| Aspecto | Evidência | Resultado |
|---|---|---|
| Fundo e barra | Cinza #c1c1c1, painel opaco, bisel de 2 px, sem blur/sombra externa | Adaptado; perfil central da barra baseado na referência Confidence Tests registrada anteriormente |
| Item apontado/selecionado | Face #dfdfdf, relevo elevado | Renderização confirmada; compatível com a ideia de locate highlight SGI |
| Item pressionado | Face #b3b3b3, relevo invertido | Renderização confirmada quando o Qt envia State_Sunken; não comprova duração histórica da pressão |
| Item indisponível | Texto dimmed; sem painel de destaque; ação não executada | Confirmado |
| Separadores e setas | Separador com duas linhas, faixa de 6 px; seta de submenu com relevo | Recursos próprios; medidas de popup não certificadas por referência histórica |
| Navegação e marcação | Mouse, teclado, Esc, submenu, checkbox e rádio exclusivo | 17 verificações nativas aprovadas |
| Tipografia do popup | text.italic=true configurado; captura mostra texto reto | Lacuna real: Kvantum não aplica essa chave aos itens de QMenu |
| Submenus | submenu_delay=250, submenu_overlap=1 | Valores da adaptação; não há comprovação de que reproduzem a temporização SGI |
| Conteúdo dos menus | Ordem, títulos, mnemônicos e posição de Ajuda vêm dos aplicativos | O tema não impõe as regras editoriais SGI aos aplicativos KDE |

A SGI associa ObliqueLabelFont e SmallObliqueLabelFont aos menus. A documentação
oficial do Kvantum declara que itens de menu, combo e view não recebem itálico
por text.italic. Portanto, a indicação no kvconfig não garante a fonte esperada.
A descrição anterior em MENUS.md foi corrigida para reconhecer essa limitação.

A documentação SGI também recomenda conteúdo específico para menus contextuais
(título, ordem, separadores e restrições de cascata). Isso depende do aplicativo,
e não pode ser validado como uma propriedade global do SVG/Kvantum.

Passaram 23 testes unitários de menus. Na galeria real, Qt 6.8.2/PyQt6/Wayland
identificou Kvantum::Style e aprovou as 17 verificações de comportamento/pixels.
Capturamos o popup e os estados selecionado, pressionado e indisponível. Esses
testes não transformam desenhos adaptados em cópias históricas comprovadas.

O capítulo 8 completo do espelho SGI permaneceu inacessível nesta revisão.
A comparação se apoia no apêndice SGI, no capítulo 3, no manual de esquemas e
na referência Confidence Tests documentada no trabalho anterior. Não foi feita
uma nova comparação de todos os pixels de popup com uma captura original IRIX.

Fontes primárias:

- [SGI: esquemas, tabela 3-1 — fontes de menus](https://techpubs.jurassic.nl/library/manuals/2000/007-2006-080/sgi_html/ch03.html)
- [SGI: visual Indigo Magic e locate highlight](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch03.html)
- [SGI: diretrizes de menus, apêndice A](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-003/sgi_html/apa.html)
- [Kvantum 1.1.4: Theme-Config, text.italic](https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/doc/Theme-Config)
