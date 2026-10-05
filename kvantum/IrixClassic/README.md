# IrixClassic — Application Style Kvantum

**0.2.0-rc1 — pressão das setas e bloco 2: botões. Manutenção: `mrmmx31`.**
Não é uma decoração de janela. O nome no Kvantum permanece **IrixClassic**.

## Nesta revisão

A barra de rolagem da 0.1.0-rc2 foi preservada: puxador, trilho, ranhuras,
largura 18 e comprimento mínimo 34. Corrigido o detalhe de pressão das setas:
o contorno escuro do triângulo não muda de lugar, mas ganha o realce inferior/
direito que faltava, além da inversão da célula já existente.

O bloco 2 fornece recursos separados para comando, ferramenta/paleta e toolbar.
A pressão rebaixa o bisel interno sem mover o texto/ícone. O marcador do botão
padrão não oculta mais a faixa clara do bisel pressionado. Hover, seleção
persistente, foco de teclado e indisponibilidade têm papéis separados.
Não há temporizador ou animação prolongando artificialmente a pressão.

O perfil normal do botão de comando preserva os três tons de borda do Help
Viewer IRIX fornecido. Estados sem referência visual direta e equivalências
Qt continuam sendo adaptações documentadas, não cópias históricas certificadas.
A paleta geral, os tamanhos de fontes e as métricas dos outros blocos não mudam.

## Testar antes de instalar

Na raiz do checkout:

```sh
bash kvantum/testar-botoes.sh
bash kvantum/prever-botoes.sh
```

A galeria usa configuração temporária e Qt 6/Kvantum real quando disponível;
não troca a seleção da sessão. Exige PyQt6 ou PySide6 e o plugin Kvantum Qt 6.
Dependência ausente retorna código 77 e não é instalada automaticamente.
A fonte de 14 pixels é local à galeria; `--fonte-px 16` permite comparar.

Para testes de eventos e PNGs offscreen:

```sh
bash kvantum/prever-botoes.sh --testar
bash kvantum/prever-botoes.sh --capturas /tmp/irix-botoes-qt
```

A imagem `PRESSAO-E-BOTOES.png` é uma prancha técnica dos mapas, não um screenshot
Qt. `PREVIA.png` é a prévia inicial rc1; `PREVIA-ROLAGEM.png` e
`ESTADOS-ROLAGEM.png` documentam a rc2. Para o novo estado pressionado, use a
prancha nova e a galeria nativa, não as prévias históricas.

## Instalar / restaurar

Como usuário normal, sem sudo, na raiz do checkout:

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

Instala no diretório de configuração do usuário sem mudar a seleção. Se o tema
já estava selecionado, reabra os aplicativos. Caso contrário, escolha
IrixClassic no Kvantum Manager com Application Style definido como kvantum.
`--ativar` é opcional e altera só a seleção interna do Kvantum.

```sh
bash kvantum/restaurar-classic.sh
```

Restaura o último recibo desse instalador; depois reabra os aplicativos.
Não execute o atualizador da decoração moderna para testar este tema.
Nenhum recurso de /usr, Aurorae, decoração Classic, GTK, fontes globais,
esquema KDE, escala de tela ou base `kvantum/Irixium/` é alterado.

## Continuidade e limites

O plano completo está em `../PLANO-IRIXCLASSIC.md` e deve acompanhar cada merge.
Bloco 1: desenho aprovado pelo usuário, pressão corrigida aguardando reteste.
Bloco 2: implementado para teste local. Próximo: bloco 3, campos e entradas.
Blocos 4–7 mantêm a base anterior e ainda exigem revisão histórica específica.

Kvantum tematiza Qt Widgets e integrações que usem o estilo; não reimplementa
widgets exclusivos da SGI nem reorganiza a interface dos aplicativos. AutoRaise,
popup, tamanhos forçados e política de ações continuam pertencendo ao Qt/app.
Estados desativados podem ser desenhados pelo motor com normal/toggled e
opacidade adicional. Ausência de intervalo, Escape no arraste e impressão da
posição inicial da scrollbar SGI continuam limites documentados em
`../docs/ROLAGEM.md`.

Detalhes e aceitação: `../docs/BOTOES.md`.
Validação realizada: `../docs/VALIDACAO-BOTOES.md`.
Configuração derivada de Irixium por Mark Whittaker/Phob1an; SVG e utilitários
novos sob GPL-3.0-or-later. Créditos/licenças preservados. Nenhuma fonte tipográfica,
código privado ou binário IRIX é incluído.
