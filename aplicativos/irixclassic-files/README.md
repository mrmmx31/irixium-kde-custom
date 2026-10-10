# IrixClassic Files 0.1.0-alpha2

Manutenção: **mrmmx31**. Derivação experimental do Dolphin para Debian 13.
**Estado: alpha compilada e testada localmente no Debian 13 em 2026-10-07.**
Veja os testes, correções e limites em [VALIDACAO-LOCAL-2026-10-07.md](docs/VALIDACAO-LOCAL-2026-10-07.md).
Não é um lançamento oficial KDE ou SGI. Não é o Dolphin instalado com outro tema,
e não é um gerenciador simplificado baseado em `QFileSystemModel`.

## O que foi implementado

A preparação reaproveita `DolphinMainWindow`, `DolphinView`, `DolphinViewContainer`,
as ações de arquivos e o backend KIO. A nova composição envolve a janela nativa:
Pathfinder editável, botão para soltar uma pasta e navegar, ancestrais,
histórico de locais, barra vertical, zoom, Shelf contextual e Content Viewer.
Os botões voltar e avançar usam o histórico nativo por aba.
As abas e a vista dividida do Dolphin permanecem acessíveis. Não se presume que
cada caminho nativo esteja validado apenas porque foi reaproveitado.

A Shelf grava **referências locais por pasta**, nos dados próprios da variante.
Remover referência não exclui o arquivo. Um drop nunca é confirmado como movimento.
O Content Viewer mostra texto simples e o primeiro quadro de imagens PNG/JPEG/BMP/
GIF/WebP. Seleção não executa o conteúdo. Ativação para abrir um item segue a
semântica de clique/duplo clique configurada no KDE; teclado também seleciona.

Apenas o visualizador novo tem os limites de 16 MiB de entrada, 40 megapixels,
256 KiB para texto, imagem reduzida até 1600×1200 e 3 segundos de trabalho.
Os decodificadores rodam em um processo separado, cancelável. **Isso não é sandbox.**
Não há preview de rede, PDF, SVG, áudio/vídeo ou documentos de escritório nessa
versão. Miniaturas nativas do Dolphin, quando explicitamente habilitadas, seguem
as políticas nativas, não as do painel novo.

## Isolamento

- Executável: `irixclassic-files`; helper: `irixclassic-preview-worker`.
- Configuração gerada: `irixclassic-filesrc`; layout: `irixclassic-files-ui.ini`.
- Shelf, bookmarks e view properties sob os dados próprios do aplicativo.
- Preferências de vista não são gravadas em `.directory` nem em xattrs de pastas.
- Bibliotecas privadas com SONAMEs próprios, junto do binário; nenhuma substitui
  `libdolphinprivate` ou `libdolphinvcs` do sistema.
- Nenhum `FileManager1` ou serviço systemd é registrado. A entrada `.desktop`
  declara os tipos MIME de diretório para que o aplicativo possa ser escolhido
  como gerenciador padrão; a instalação não altera automaticamente a escolha do
  usuário nem se conecta às instâncias do Dolphin original.

Isto não isola o sistema de arquivos: operações nativas solicitadas pelo usuário
continuam reais. Lixeira, protocolos, autenticação KIO, lista de Locais do KDE
(quando aberta) e abertura por aplicativos externos são serviços compartilhados
normais do desktop. Não prometemos um perfil isolado de todos os serviços KDE.

## Construir no Debian 13

Base fixada: **Dolphin 4:25.04.3-1+deb13u1**, com a série de patches Debian aplicada.
Qt/KDE vêm do Debian; não recompilamos todo o desktop.

Habilite os índices de fonte `deb-src` nos repositórios oficiais já configurados.
Em instalações com `/etc/apt/sources.list.d/debian.sources`, a linha `Types: deb`
pode ser ajustada pelo administrador para `Types: deb deb-src`. Não adicione
repositórios aleatórios nem desative a verificação das assinaturas do APT.

```bash
sudo apt update
sudo apt install build-essential cmake ninja-build python3 dpkg-dev dbus kio6 qt6-image-formats-plugins
sudo apt build-dep dolphin
```

Na raiz do clone, **sem sudo**:

```bash
bash aplicativos/irixclassic-files/testar-fontes.sh

trabalho="$HOME/Downloads/irixclassic-files-build-$(date +%Y%m%d-%H%M%S)"
bash aplicativos/irixclassic-files/construir.sh --baixar --trabalho "$trabalho" --jobs 2
```

`--baixar` autoriza `apt-get source --download-only` com a versão exata. Depois,
`dpkg-source -x` extrai e aplica os patches Debian. Outra cópia recebe as mudanças
do projeto. A origem e o checkout não são modificados. Uma base diferente é
recusada, não forçada. Dependências não são instaladas por `construir.sh`.

Para fonte Debian já extraída, substituir `--baixar` por `--origem /pasta/dolphin`.
A fonte deve ter a versão fixada e seus patches aplicados. Não usar checkout Git
upstream sem os patches Debian.

**Não execute `cmake --install` na árvore upstream:** suas regras normais ainda
existem para referência. Nosso fluxo compila apenas os alvos privados e usa um
instalador específico. Nenhum binário distribuível é gerado se compilação,
testes nativos ou verificação de bibliotecas falharem.

## Executar primeiro com dados artificiais

Depois de um build aprovado:

```bash
python3 aplicativos/irixclassic-files/tools/create_demo.py \
    --saida "$HOME/Downloads/irixclassic-files-demo"

"$trabalho/IrixClassic-Files-0.1.0-alpha2/bin/irixclassic-files" \
    "$HOME/Downloads/irixclassic-files-demo"
```

O aplicativo usa o estilo atual do Qt. Se o Kvantum IrixClassic estiver selecionado,
esses controles serão utilizados. Não altera o tema ou a fonte global. Os quatro
fundos foram amostrados na captura fornecida. A revisão local registrou quatro
capturas Wayland com Kvantum IrixClassic: navegação, texto, imagem e vista dividida.
Isso confirma a renderização local, sem certificar uma reprodução exata do IRIX.
A biblioteca privada e o helper devem permanecer junto do executável.

## Instalar e remover a cópia privada

```bash
cd "$trabalho/IrixClassic-Files-0.1.0-alpha2"
python3 instalar.py --verificar
python3 instalar.py
```

Destino: `~/.local/lib/irixclassic-files/0.1.0-alpha2/`, launcher em
`~/.local/bin/irixclassic-files` e entrada própria no menu de aplicativos.
Nada é instalado em `/usr`. Uma versão diferente já presente é recusada. A
entrada registra `inode/directory` e `application/x-directory`, mas não muda
automaticamente o gerenciador padrão do usuário.

```bash
python3 instalar.py --remover --verificar
python3 instalar.py --remover
```

A remoção confere os arquivos antes de apagá-los e preserva Shelf/configurações.
Não modifica o Dolphin, o Kvantum estável, as decorações ou `sons/`.

## Pacote `.deb` opcional

`tools/build_deb.py` transforma um bundle que passou nos testes nativos em
`irixclassic-files_0.1.0~alpha2-1_amd64.deb` (ou a arquitetura nativa suportada).
Execute sem sudo, com o fonte correspondente gerado pela mesma construção:

```bash
python3 aplicativos/irixclassic-files/tools/build_deb.py \
    --bundle "$trabalho/IrixClassic-Files-0.1.0-alpha2" \
    --fonte "$trabalho/pacotes/IrixClassic-Files-0.1.0-alpha2-source.tar.gz" \
    --saida "$trabalho/debian"
```

São necessários `dpkg-dev` e `binutils`. Dependências de bibliotecas são obtidas
com `dpkg-shlibdeps`; KIO, plugins Qt e de imagens são declarados explicitamente.
O empacotador verifica o manifesto e compara os fontes C++ com o arquivo fonte.
O diretório de saída precisa ser novo. O código correspondente e SHA-256 são
entregues junto do binário. Não inclui ícones, fontes ou sons SGI.

A instalação normal pelo APT coloca o aplicativo em `/usr`, disponível no menu,
com bibliotecas sob `/usr/lib/irixclassic-files/`. Isso é uma instalação de
aplicativo para o sistema, distinta da instalação privada acima. A entrada
declara os tipos MIME de diretório, mas não substitui automaticamente a escolha
do usuário nem altera temas ou configurações do Dolphin. Não há scripts de
manutenção, serviços ou registro de FileManager1. Para testar sem instalação global, extraia com `dpkg-deb -x`
e execute diretamente o binário interno; veja [README.Debian](debian/README.Debian).
O workflow também gera o `.deb`, sem publicação automática. Veja a
[validação do pacote](docs/VALIDACAO-DEB-2026-10-07.md).

## Testes, CI e lançamento

`testar-fontes.sh` executa testes Python de transformação, empacotamento e
contratos. **Eles não compilam C++.** O build executa testes Qt com dados
artificiais, em sessão D-Bus privada e backend offscreen. A avaliação visual e os
gestos Wayland precisam do uso local antes de anunciar estabilidade.

O workflow `.github/workflows/irixclassic-files-alpha.yml` compila em Debian 13
no GitHub Actions quando este componente for enviado. Não publica automaticamente.
Os logs são mantidos também em caso de erro. As actions estão fixadas por SHA.

Após build/testes aprovados e verificação local, publique uma **prerelease**, não
uma versão estável: ver `docs/PUBLICAR.md`. Não há outro formulário de aceite.
As versões dos temas estáveis permanecem inalteradas.

## Licenças e escopo

Código novo: GPL-2.0-or-later. Cada arquivo upstream conserva seus avisos e
licenças. Créditos completos dos autores do Dolphin continuam em sua fonte.
O pacote de código correspondente inclui a fonte Debian preparada e este kit.
Nenhum ícone, fonte ou áudio proprietário SGI foi embutido.

Sons próprios, renderizadores adicionais, thumbwheel histórico, arranjo livre,
integração de Shelf e os detalhes restantes de interface são o backlog posterior.
O controle vertical atual é um `QSlider` ligado ao zoom real, não a reprodução
exata do thumbwheel do IRIX. O histórico atual também não replica todos os gestos
históricos. São adaptações da primeira versão, não capacidades ocultamente prontas.
