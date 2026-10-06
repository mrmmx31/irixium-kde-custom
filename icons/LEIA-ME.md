# IRIX icons kit — 0.1.0

Dois trabalhos separados: uma recriação independente de ícones inspirada na SGI e ferramentas para corrigir a estrutura do Irixium existente sem sobrescrevê-lo.

## Comece pelo novo tema

Na pasta deste kit, execute:

```bash
python3 tools/install_theme.py
```

Requer Python 3.10 ou superior, sem pacotes Python adicionais. O tema pronto não exige CairoSVG, Pillow ou um editor de imagens para ser instalado.

O instalador copia `themes/IrixClassic-SGI` para `${XDG_DATA_HOME:-$HOME/.local/share}/icons/IrixClassic-SGI`. Ele recusa sobrescrever uma pasta existente e não muda o tema ativo.

Abra **Configurações do Sistema**, pesquise **Ícones**, selecione **IRIX Classic — SGI** e aplique. Feche e reabra as aplicações usadas no teste. Se alguma continuar exibindo recursos antigos, encerre e entre novamente na sessão depois de salvar seu trabalho. Não é necessário apagar todos os caches do KDE.

Para voltar, selecione **Irixium** ou **Breeze** nessa mesma tela. Não há alteração de Aurorae, Kvantum, GTK, cursores, fontes, sons ou do tema global. Aplicar posteriormente um tema global que também selecione ícones pode trocar a sua seleção novamente.

Alternativa sem script: coloque a pasta que contém `index.theme` dentro de `~/.local/share/icons/`, com o nome `IrixClassic-SGI`. Respeite `XDG_DATA_HOME` quando você o tiver personalizado. O arquivo separado `IrixClassic-SGI-0.1.0.tar.gz` contém somente essa pasta pronta.

## O que foi criado

**110 composições vetoriais distintas**, organizadas em **126 ícones-base** e **292 nomes de ícones**, incluindo aliases para aplicativos. Os números não significam 292 desenhos diferentes.

Cada nome possui PNG em **16, 22, 24, 32, 48, 64, 96 e 128 px** e um SVG editável: **2.336 PNGs e 292 SVGs**. Há versões simplificadas das famílias para 16/22/24, geradas diretamente de vetores, não de um PNG maior. Não são desenhos individualmente ajustados pixel a pixel para cada resolução.

Cobertura: pastas e locais do Dolphin, documentos e tipos de arquivo, terminal, navegador, editor, ferramentas de sistema, dispositivos, ações comuns, avisos, lixeira vazia/cheia, áudio e alguns estados de bateria e rede. Exemplos de aliases incluem Dolphin, Konsole, Kate, KWrite, Ark, KCalc, Gwenview, Firefox, DBeaver e VS Code. Todos os aliases do pacote são arquivos reais, não links simbólicos.

Não é um conjunto oficial extraído do IRIX. É uma criação nova inspirada nas diretrizes do Indigo Magic: contornos escuros, perspectiva, cores contidas, sombras, documentos em pilhas e base dos aplicativos. A representação da base é estática; não reproduz o comportamento de execução do IRIX.

Ícones não cobertos usam `breeze,hicolor`, instalados separadamente no sistema. Não há dependência do tema Irixium. Nomes `-symbolic` não têm uma família adaptativa própria neste pacote: a resolução fica por conta do aplicativo/carregador e dos temas herdados. O novo tema é colorido, com fundo transparente; não é uma variante monocromática que acompanha automaticamente todas as cores de texto.

## Auditar o Irixium atual, sem alterá-lo

Aponte para a pasta que realmente contém o `index.theme`, não para o tema Plasma:

```bash
python3 tools/repair_irixium.py \
  /caminho/irixium-kde-custom/icons/Irixium \
  --report auditoria-irixium.json
```

Substitua apenas o caminho. O relatório deve ficar fora da pasta auditada. Se estiver analisando a cópia instalada, ela pode estar em `~/.local/share/icons/Irixium`, `~/.icons/Irixium` ou numa instalação do sistema. A estrutura local é verificada; não é necessário acesso à rede.

Sem `--build`, nenhuma imagem ou configuração do tema é alterada. O auditor verifica índice, dimensões físicas de PNG, CRCs, links quebrados/externos, arquivos de texto disfarçados de PNG e SVGs com problemas estruturais. Avisos de metadados não equivalem a defeitos visuais comprovados. Não detecta toda diferença de proporção óptica, alinhamento ou espaçamento interno.

## Criar uma cópia corrigida, paralela

```bash
python3 tools/repair_irixium.py \
  /caminho/irixium-kde-custom/icons/Irixium \
  --build "${XDG_DATA_HOME:-$HOME/.local/share}/icons/Irixium-Fixed"
```

O resultado aparece como **Irixium — Corrigido (local)**. Só aplique a cópia após conferir que `after.errors` é zero e revisar os arquivos eventualmente omitidos no relatório. O programa retorna código 1 quando ainda existem erros de auditoria. Uma pasta de saída parcial ou com erros não deve ser usada.

A cópia conserva os bytes da arte válida, corrige metadados e torna os links de arquivos internos portáteis. Arquivos inválidos e links quebrados/externos são omitidos com registro no relatório, permitindo que o carregador tente o fallback. Nenhum alvo de link é adivinhado. A licença da arte permanece a original; não publique a cópia sem esclarecê-la.

Somente quando o relatório identificar **dimensões reais incorretas de PNG**, a opção adicional abaixo ajusta a tela dessas imagens na cópia:

```bash
python3 tools/repair_irixium.py \
  /caminho/irixium-kde-custom/icons/Irixium \
  --build "${XDG_DATA_HOME:-$HOME/.local/share}/icons/Irixium-Fixed-Normalized" \
  --normalize-png
```

Essa opção requer **Pillow**. Ela preserva a proporção, centraliza em tela transparente e não recorta automaticamente margens internas. Reduz com Lanczos e amplia com vizinho mais próximo para não aplicar suavização arbitrária à pixel art. Ampliação não cria detalhes. Folhas de animação não são redimensionadas. É um reparo mecânico, não substitui uma revisão visual.

## Integrar no Git

Nenhum commit, push ou alteração remota foi realizado por este kit. O índice analisado pertence ao commit `3f8e299f044bd1ebeb4f46bbc2781e93e81b7708` de `mrmmx31/irixium-kde-custom`.

A correção mínima está em `patches/0001-irixium-icon-metadata.patch`. Confira em uma branch de trabalho, na raiz do seu clone:

```bash
git apply --check /caminho/irix-icons-kit-0.1.0/patches/0001-irixium-icon-metadata.patch
```

Depois de revisar o conteúdo, a aplicação é explícita:

```bash
git apply /caminho/irix-icons-kit-0.1.0/patches/0001-irixium-icon-metadata.patch
```

Se houver conflito, não force. Compare com o índice atual. O patch muda apenas `icons/Irixium/index.theme`; não altera arquivos de arte nem componentes da decoração. O novo tema pode ser adicionado separadamente em `icons/IrixClassic-SGI/`. Copiar essa pasta para o repositório não a integra automaticamente aos instaladores/empacotadores existentes: esses devem ser revisados à parte.

O patch não corrige dimensões de imagens, não aumenta a cobertura de ícones do Irixium e não é uma correção geral do painel Plasma. Consulte `docs/AUDITORIA-IRIXIUM.md`.

## Desenvolvimento e testes

O gerador completo da nova arte está em `tools/build_classic.py`. Os SVGs instalados também podem ser editados diretamente. Para gerar um destino novo:

```bash
python3 tools/build_classic.py --output ./build/IrixClassic-SGI --previews ./build/previews
python3 tools/validate_theme.py ./build/IrixClassic-SGI
```

A geração exige **CairoSVG**; as prévias exigem também **Pillow**. Instalação e auditoria comum usam apenas a biblioteca padrão do Python. O gerador recusa destinos já existentes.

Para testar o kit:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_theme.py themes/IrixClassic-SGI
```

Os testes de normalização exigem Pillow; sem ele, esse teste é marcado como não executado. Os testes do patch usam Git. Consulte `docs/TESTES.md` para separar o que foi executado do que depende de uma sessão KDE real.

## Arquivos principais

| Caminho | Função |
|---|---|
| `themes/IrixClassic-SGI/` | Tema novo, pronto para instalar |
| `previews/previa.png` | Amostra real dos ícones gerados |
| `previews/catalogo.png` | Todos os 126 ícones-base |
| `previews/tamanhos.png` | Comparação em dimensões nativas |
| `tools/repair_irixium.py` | Auditoria e cópia corrigida do Irixium |
| `tools/validate_theme.py` | Verificador de temas |
| `tools/build_classic.py` | Fonte geradora da arte e do pacote |
| `patches/0001-irixium-icon-metadata.patch` | Correção mínima do índice existente |
| `docs/` | Auditoria, proveniência e resultados dos testes |

## Limitações importantes

Esta é a versão inicial **0.1.0**. Não foi validada numa sessão real de KDE/Wayland. A inspeção do Irixium remoto foi feita no índice e em amostras selecionadas; não foi uma auditoria integral dos bytes de todos os ícones. A ferramenta fornecida permite completar essa auditoria com a sua cópia local.

As renderizações e os testes estruturais não reproduzem regras específicas de todos os applets do Plasma, Qt, Flatpak ou aplicativos com imagens embutidas. Miniaturas de imagens e vídeos no gerenciador de arquivos não são o mesmo que ícones de tema. A escala fracionária pode suavizar bordas de formas diferentes da escala de 100%.
