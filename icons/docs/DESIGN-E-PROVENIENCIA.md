# Design e proveniência

## Novo tema: criação independente

O código `tools/build_classic.py` constrói as formas geométricas deste pacote. Os SVGs e PNGs de `themes/IrixClassic-SGI` foram gerados a partir dele. Não foram extraídos ícones de uma instalação de IRIX nem copiados os bitmaps de Irixium, Breeze ou de outro tema.

A inspiração histórica é o capítulo **Icons**, de *Indigo Magic User Interface Guidelines*, publicação SGI 007-2167-002, consultado no espelho do manual original:

https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch02.html

Foram usados os princípios gerais de contorno, perspectiva, cores de destaque restritas, sombras, pilha de documentos e base para aplicativos. A paleta e as geometrias concretas são as do gerador, não amostras alegadas como reprodução exata de valores originais. Os ícones de aplicações modernas são adaptações funcionais; não representam programas históricos da SGI.

O tema não é oficial, não é patrocinado pela SGI e não pretende reproduzir todos os ícones de nenhuma versão específica do IRIX. Não contém o logotipo proprietário da SGI. O nome identifica a inspiração visual.

A arte e as ferramentas novas são disponibilizadas sob **MIT**, com o texto em `LICENSE`. Isso não deve ser interpretado como uma nova licença para arquivos de terceiros.

## Irixium existente

O `UPSTREAMS.md` do repositório aponta o pacote de ícones para `https://www.pling.com/p/2142965/` e registra que a licença do snapshot instalado não foi declarada. O índice também se descreve como “Remixed NsCDE”. Portanto, não o apresente como uma extração autêntica de IRIX, nem trate automaticamente a licença da raiz do repositório como confirmação da proveniência de cada bitmap.

A distribuição deste kit **não inclui os bitmaps originais de Irixium**. A correção é fornecida como ferramenta local e patch textual. Uma cópia Irixium-Fixed criada pelo usuário mantém a atribuição e os direitos dos autores da arte original. A publicação dessa cópia exige esclarecer a licença/proveniência relevante.

A fixture `tests/fixtures/Irixium-index.theme` é uma cópia do arquivo de configuração funcional fornecido pelo repositório indicado pelo usuário, preservada para verificar o patch e o hash. Ela e os trechos de contexto do patch são material preexistente; não são apresentados como arte nova MIT. Consulte a origem indicada em `AUDITORIA-IRIXIUM.md` para o registro original.

## Prévias e fontes tipográficas

Os textos das folhas de prévia foram rasterizados com uma fonte disponível no ambiente de geração. Nenhum arquivo de fonte é distribuído. Os próprios SVGs de ícones não dependem de fontes externas e não contêm imagens externas, scripts ou filtros.
