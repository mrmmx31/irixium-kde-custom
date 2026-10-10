# Cursores SGI para KDE

| ID instalado | Aparência / espera | Perfil |
|---|---|---|
| `SGI-Classic` | Vermelho/branco, relógio de pulso animado | IRIX Classic |
| `SGI-Irixium` | Vermelho/branco, relógio circular animado | Irixium moderno |
| `sgi` | Vermelho/branco, ampulheta estática original | Alternativa manual |

São três variantes mantidas neste projeto, derivadas da mesma recriação;
não são três pacotes oficiais diferentes da SGI. Nas duas variantes novas,
`wait`/`watch` mostram somente o relógio e `progress`/`left_ptr_watch` mantêm
a seta com o indicador. A animação é descrita no arquivo Xcursor: oito quadros
de 125 ms, consumidos pelo compositor/toolkit. Nenhum serviço, hook de aplicação
ou timer próprio é instalado.

## Instalação e seleção

```sh
bash instalar-irixium.sh
bash aplicar-tema.sh classic   # SGI-Classic; moderno seleciona SGI-Irixium
```

Os três temas são instalados somente em `XDG_DATA_HOME/icons` do usuário e
em `~/.icons` para compatibilidade com libXcursor/KCM. Aqui, a busca nativa
era `~/.icons:/usr/share/icons:/usr/share/pixmaps`, sem o diretório XDG.
O instalador anterior deixava o KDE lendo a cópia legada desatualizada. Agora
ambos os destinos são mantidos e auditados, com backup/rollback, sem alterar
os demais temas ou qualquer pasta do sistema.
O KCM Tema Global também declara o cursor correspondente. O script de aplicação
mantém KDE e GTK 3/4 coerentes, sem modificar o tamanho personalizado.
Para escolher apenas o cursor, use o painel Cursores ou, por exemplo:

```sh
plasma-apply-cursortheme --size 32 SGI-Classic
```

## Tamanhos e proporção

Cada estado contém tamanhos nominais **24, 32, 48, 64 e 96**. Os pixels e hotspots
são dimensionados juntos; os cinco tamanhos são distribuídos prontos e não
precisam de Pillow para instalar. A base preservada tem seta em tela transparente
32×32, desenho visível **11×18** e hotspot **(5,5)**. A variante Classic preserva
esses pixels na opção nominal 32. A dimensão nominal não é a altura visível.

Classic nos demais tamanhos reconstrói os contornos com bordas opacas;
Irixium renderiza contornos em todos os tamanhos com antialiasing. A seta é
desenhada com polígonos contínuos ajustados à silhueta de referência; os outros
estados recuperam contornos simplificados da base, preservando furos e detalhes.
Os relógios são desenhados diretamente por tamanho. Não ampliamos o bitmap
pequeno para obter essas duas variantes nem aplicamos desfoque sobre ele.
A alternativa `sgi` mantém a ampliação antiga para comparação. O código converte
as bordas suaves para alpha premultiplicado exigido pelo Xcursor.

Antes desta correção havia somente tamanho nominal 32; a sessão examinada pedia
48. Isso não assegurava uma variante de tamanho correspondente e podia levar
a escolhas diferentes de escala conforme o carregador. Agora 48 tem seus próprios
pixels. O script não reduz automaticamente essa preferência do usuário.

O [guia de interface SGI, capítulo User Feedback](https://pixelbart.net/SGI/IRIX/i/65/29/doc/usr/share/Insight/library/SGI_bookshelves/SGI_Developer/books/UI_Glines/sgi_html/ch11.html)
descreve seta vermelha com contorno branco e recomenda relógio para espera.
Essa é a referência de forma/cor; não especifica um único tamanho físico para
todos os monitores SGI. Não afirmamos equivalência física exata entre um monitor
antigo e uma tela moderna. A proporção em pixels da recriação foi preservada.
32 é o ponto de comparação da base; 48/64/96 acomodam preferências e HiDPI.

## Outros conjuntos analisados e procedência

- [BEHRZ — SGI Irix cursor](https://www.gnome-look.org/p/999497/): recriação
  apontada nos créditos upstream; precursor da família usada aqui.
- [jujum4n — sgi-enhanced](https://github.com/jujum4n/sgi-enhanced): origem dos
  binários de base, conferidos por Git blob contra o commit
  `b7a02161f8e13da639d2ecff5735436c9f447d67`.
- [MaXX — redSGI](https://docs.maxxinteractive.com/books/maxxdesktop-variables/page/maxxdesktop-shell-variables):
  documenta outra opção SGI, padrão desse desktop. Não importamos sua distribuição.
- [DaftiPunki — port Windows](https://www.rw-designer.com/cursor-set/sgi-irix-red):
  variante dessa família, com estados adicionais para Windows. Não foi convertida
  nem incluída aqui.

Os binários de base e seus hashes ficam em `sources/`, incluindo os aliases
anteriores para comparação. Removemos somente `.directory`, metadado do Dolphin
que não fazia parte de um cursor. `ORIGEM.json` e `LICENSE-NOTICE.md` identificam
os créditos e a declaração GPL sem versão encontrada upstream. Não atribuímos
uma licença presumida aos assets; o código de integração declara GPL-3.0-or-later.

## Reconstruir e verificar

```sh
python3 cursors/tools/build.py              # requer Pillow; não instala nada
python3 cursors/tools/cursor_audit.py        # valida aliases, tamanhos e manifestos
python3 -m unittest discover -s cursors/tests
python3 cursors/tools/preview.py --saida /tmp/cursores.png
```

O teste nativo consulta libXcursor para todos os 35 papéis padronizados nos cinco
tamanhos e nos três temas: **525 consultas**. Confere os pixels, hotspots e todos
os quadros efetivamente carregados, sem servidor X ou alteração da sessão.
Isso valida lookup e formato; uma aplicação só mostrará ocupado se solicitar
esse estado. Cursores privados de aplicações/sandboxes não são substituídos
por esta ferramenta.

Para testes isolados, `instalar-irixium.sh --cursor-compat-root PASTA` e
`tools/audit_suite.py --local --cursor-compat-root PASTA` evitam usar o
`~/.icons` real. O relatório distingue 17 componentes de seus três destinos
adicionais de compatibilidade.
