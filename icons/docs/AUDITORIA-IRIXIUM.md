# Auditoria inicial do Irixium

Data: 6 de outubro de 2026. Repositório: `mrmmx31/irixium-kde-custom`, branch `master`, commit `3f8e299f044bd1ebeb4f46bbc2781e93e81b7708`.

Escopo efetivo: metadados do repositório, `UPSTREAMS.md`, árvore e índice de `icons/Irixium`, amostras de PNG e listagem de `plasma/Irixium/icons`. Não houve execução numa sessão KDE nem análise integral dos pixels de todas as imagens remotas. Não houve modificação no GitHub.

## 1. Padrões de 24 px ausentes das listas

O índice declara `DesktopDefault=24`, `ToolbarDefault=24` e `MainToolbarDefault=24`, mas as três listas correspondentes são `16,22,32,48`.

Isso é uma inconsistência verificável do arquivo, mas não prova por si só que todo componente atual do KDE esteja usando essas chaves. O patch inclui 24 nas listas pertinentes sem mudar os valores padrão. Inclui também o tamanho disponível nas listas de painel e diálogo. Não força tamanho de painel ou de botão.

## 2. Ordem de herança

O original usa `Inherits=hicolor,breeze`; a proposta usa `Inherits=breeze,hicolor`. A especificação descreve hicolor como a reserva final. Antecipá-lo pode favorecer a arte distribuída por aplicações antes de um fallback visualmente mais uniforme.

A mudança afeta apenas os nomes ausentes do tema. Não garante que ícones embutidos ou caminhos absolutos sejam substituídos. Também não faz o carregador preferir automaticamente a versão de um tema herdado só porque ela possui uma resolução melhor.

## 3. Raster de 256 px anunciado como escalável

`[256x256/places]` está marcado como `Type=Scalable`, `MinSize=56`, `MaxSize=512`. A árvore amostrada dessa pasta contém PNGs. O arquivo `folder.png` foi decodificado e possui realmente 256×256 pixels.

Marcar um PNG como escalável NÃO é, por si só, uma violação universal de formato. O problema prático é a política de seleção: aquele raster torna-se candidato dentro de toda a faixa declarada, sem ganhar detalhe vetorial. A proposta `Type=Fixed` o descreve como fonte raster de tamanho nominal 256; o carregador ainda pode redimensioná-lo quando necessário.

**Trade-off:** com essa alteração, uma solicitação de 64 px pode passar a escolher uma fonte nativa de 48 em vez da imagem de 256 declarada escalável. Isso pode melhorar ou piorar um desenho específico; deve ser comparado visualmente. A alteração não pode ser apresentada como solução garantida para a qualidade de todos os ícones grandes.

## 4. Cobertura de tamanhos desigual

No índice, as famílias de ações, aplicativos, dispositivos etc. terminam em 48 px; apenas locais têm a pasta adicional de 256 px. Não há uma família SVG escalável equivalente no índice desse snapshot.

Isso favorece ampliação de bitmaps em usos maiores, mas não é automaticamente um erro: pixel art pode deliberadamente trabalhar com resoluções fixas. Resolver de forma visualmente consistente requer novas versões da arte, não apenas renomear pastas ou alterar `Size=`. O tema novo resolve esse problema de distribuição para os nomes que cobre; não converte o Irixium existente em vetores.

## 5. Amostras com dimensões corretas

Foram conferidos, entre outros, estes arquivos:

| Arquivo | Dimensão física observada |
|---|---|
| `16x16/actions/go-up.png` | 16×16 |
| `24x24/actions/go-next.png` | 24×24 |
| `24x24/apps/accessories-text-editor.png` | 24×24 |
| `48x48/places/folder.png` | 48×48 |
| `256x256/places/folder.png` | 256×256 |

Portanto, não há base para afirmar que esses arquivos estejam com a dimensão física errada. Peso alto de um PNG pequeno também não prova dimensão errada: metadados embutidos podem aumentar o arquivo.

Há links simbólicos reais na árvore. A auditoria remota amostral não confirmou um conjunto geral de links quebrados. O verificador local os procura, inclusive links transformados em pequenos arquivos de texto durante transporte/descompactação. Ele não presume que estejam quebrados.

## 6. Ícones do tema Plasma são outra camada

Há `audio.svg`, `klipper.svg`, `media.svg` e `start.svg` em `plasma/Irixium/icons/`. Esses arquivos são distintos dos ícones distribuídos pelo `index.theme` de `icons/Irixium/`.

Logo, um defeito de áudio/clipboard/menu no painel pode continuar mesmo que os ícones de pastas do Dolphin estejam corretos. É necessário identificar qual recurso o componente realmente carrega antes de modificá-lo. Este kit não reescreve aqueles SVGs compostos do Plasma, nem os botões da decoração Aurorae.

## 7. O que a correção faz e o que não faz

O patch mínimo corrige listas e herança e propõe uma política fixa para o raster de 256. A ferramenta opcional cria uma cópia separada, preserva bytes válidos por padrão, reconstrói declarações de diretórios presentes e registra problemas de links/arquivos. A normalização de PNGs exige solicitação explícita e só atua na cópia.

Não são corrigidos automaticamente: margens internas excessivas, proporção visual entre desenhos, semântica de aliases, ícones faltantes de todos os aplicativos, regras dos applets, miniaturas ou defeitos de Qt/KDE. Sprite sheets de animação não são tratadas como ícones quadrados malformados.

## Referências verificadas

- Índice: https://github.com/mrmmx31/irixium-kde-custom/blob/3f8e299f044bd1ebeb4f46bbc2781e93e81b7708/icons/Irixium/index.theme
- Blob do índice: `b4ad6335a7fa38dc8d832838aced0635ebf2ac78`. A fixture dos testes corresponde byte a byte a esse blob.
- Origens: https://github.com/mrmmx31/irixium-kde-custom/blob/3f8e299f044bd1ebeb4f46bbc2781e93e81b7708/UPSTREAMS.md
- Recursos do Plasma: https://github.com/mrmmx31/irixium-kde-custom/tree/3f8e299f044bd1ebeb4f46bbc2781e93e81b7708/plasma/Irixium/icons
- Especificação: https://specifications.freedesktop.org/icon-theme/latest/
- Documentação KDE: https://develop.kde.org/docs/features/additional-features/icons/
