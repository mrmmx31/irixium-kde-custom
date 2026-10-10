# Laboratório de temas Motif

Aplicativo C99/Motif organizado em MVC. O usuário edita projetos e compara
controles reais; a ferramenta exporta propostas privadas. Não instala temas
nem modifica a configuração do desktop pessoal.

## Compilar

No Debian, dependências de compilação:

```sh
sudo apt install build-essential libmotif-dev libjson-c-dev libpng-dev libxt-dev libssl-dev
make -C tools/theme-lab
make -C tools/theme-lab check
```

Bibliotecas/bindings adicionais são necessários para as galerias; a ferramenta
mostra os disponíveis. Não afirma cobertura de GTK1/GTK5 sem runtime real.

Para testar no GTK3 um esquema diferente do desktop, compile o leitor de papéis
nativos do KDE. Ele usa um processo sem interface, sem trocar a configuração:

```sh
sudo apt install cmake qt6-base-dev libkf6colorscheme-dev libkf6config-dev
cmake -S tools/theme-lab/native-build -B tools/theme-lab/build/native-colors
cmake --build tools/theme-lab/build/native-colors --parallel 2
```

## Abrir na sessão de teste

Com uma prévia criada por `plasma/tools/prever-tema-completo.py`, execute:

```sh
python3 plasma/tools/abrir-laboratorio-temas.py --sessao CAMINHO_DA_SESSAO --raiz .
```

O lançador mantém o Xephyr existente, monta fontes e tradutores somente para
leitura e usa o HOME/DBus privados. A pipeta mede pixels dessa tela X11; não
captura o desktop Wayland externo. Fechar a prévia encerra seus processos.

Para comparar duas versões sem fechar a primeira, acrescente `--nova-instancia`.
Cada instância adicional usa uma pasta de projetos própria; a saída do lançador
mostra esse caminho. Fontes, executáveis e referência são congelados por execução.

## Ajustar e guardar

1. No painel esquerdo, escolha plataforma e esquema de teste. Cada família tem
   receita independente. O esquema altera somente os controles em teste.
2. Marque categorias e controles visíveis; escolha o estado e os valores.
   Na lista, Ctrl combina itens e Shift seleciona um intervalo.
   **Atualizar** aplica à montagem central. Com **Atualização automática**, o
   intervalo em milissegundos reúne as alterações antes de atualizar.
3. No canvas, `Ctrl+clique` seleciona e `Ctrl+arraste` posiciona. Cliques comuns
   mantêm a operação nativa. Também é possível digitar X/Y e atualizar.
   O terceiro painel contém apenas o trecho do controle/estado selecionado.
   Estados forçados são uma ferramenta de edição, não uma prova histórica.
4. A referência central usa controles **Motif reais**, com receita própria e o
   mesmo esquema de teste. Cliques nela exercitam o Motif e não editam GTK3.
   **Imagem histórica** abre o PNG atual em outra janela, em escala 1:1;
   o campo Referência PNG permite escolher outra imagem.
   **Pipeta** mede RGB16/RGB8; clique
   esquerdo captura, Esc ou botão direito cancela e 30 s libera o ponteiro.
5. **Prévia separada** abre controles nativos em outra janela. Motif e GTK3
   têm montagem central nesta etapa; as galerias GTK2/GTK4/Qt5/Qt6 usam o tema
   atual e indicam que sua receita ainda não foi traduzida. GTK1/GTK5 ausentes
   não são simulados; a galeria Qt Quick não valida SVGs do Plasma Style.
6. **Salvar** guarda um projeto JSON. **Importar** recupera um projeto validado.
7. **Exportar** gera receitas e a proposta GTK3 na pasta de trabalho, sem alterar
   o contrato histórico. As exportações registram entradas e suas origens.

Barra, seta, thumb e sombra precisam respeitar as relações da implementação
GTK3: barra = seta + 2 × sombra; thumb transversal = seta; seta ímpar;
moldura = sombra. Padding/fonte iniciais são defaults da ferramenta, não medidas
comprovadas da referência histórica.

Cor medida é evidência. O DomainOS usa papéis como
`Colors:Button/BackgroundNormal` do esquema KDE atual; a pipeta não cria cores
finais fixas nos widgets. O campo de fatores regula luz, sombra e trilho.

## Organização

`src/model.c` valida e persiste; `src/view.c` contém widgets e referência;
`src/controller.c` executa ações sem bloquear o loop Xt; `backend.py` identifica
capacidades e traduz receitas. `preview_gtk.py` contém os controles GTK3 reais;
eventos privados correlacionados pelo hash da cena passam pelo controller.
`src/native_colors.cpp` lê estados com KColorScheme e a política do GTKConfig.
A interface usa a biblioteca Motif do sistema.
O código-fonte baixado do Motif atual serve de apoio; a VM SR10.4 continua sendo
a referência histórica para o tema DomainOS.

Escopo e fila: [documento do laboratório](../../docs/DOMAINOS-LABORATORIO-TEMAS.md).
