# Pager DomainOS e a referência IRIX

Pesquisa RESP-C03, 08/10/2026. Os documentos originais da SGI estão preservados
nos espelhos abaixo; sua consulta não depende de executar o IRIX.

O capítulo **Using Multiple Desks** descreve Desks Overview com miniaturas de
janelas e ícones, seleção de uma janela por contorno amarelo, navegação entre
desktops e comandos para criar, renomear e remover áreas. O formato compacto de
botões é uma alternativa às miniaturas. A troca histórica usa duplo clique; o
arraste permite mover janelas entre áreas. [Desktop User’s Guide, capítulo 7](https://tech-pubs.net/SGI_EndUser/books/Desktop_UG/sgi_html/ch07.html).

O guia para desenvolvedores chama essa representação de esboço em miniatura.
Ele diferencia janelas principais, que aparecem nesse esboço, de janelas de
apoio e diálogos, que não aparecem. Também descreve rótulos das janelas ao passar
o ponteiro. Isso sustenta a referência de um mapa de janelas, mas não demonstra
captura contínua do conteúdo das aplicações. [IRIX Interactive Desktop User Interface Guidelines, capítulo 3, Desks](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-006/sgi_html/ch03.html).

Na adaptação aprovada, o modelo nativo do KDE fornece geometria, desktop e estado;
os retângulos representam esses dados e não capturam conteúdo. O clique simples
ativa a área, a roda percorre cartões por padrão e há uma luz amarela persistente.
Essas escolhas são decisões R2 da adaptação. Não se afirma equivalência integral
com Desks Overview: o gesto de ativação difere, as regras de inclusão de janelas
seguem o provedor KDE e o arraste continua adiado para a próxima versão.

O nome “snapshot” do manual histórico não é prova de uma captura de pixels ao
vivo. A equivalência confirmada aqui é a representação em miniatura e as funções
de organização descritas, dentro dos limites documentados. Não houve ensaio de
uma instalação IRIX original nesta rodada.
