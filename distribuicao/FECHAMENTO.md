# Fechamento da candidata IrixClassic 0.7.1-rc1

Manutenção pública: **mrmmx31**. Esta etapa não cria outra aparência, não muda
versão, não publica no GitHub e não instala ou repete o reparo das setas do KDE.
A correção das setas já foi confirmada pelo usuário; ela permanece separada.

## Um comando para reunir o que falta

Depois do merge, execute **na raiz do clone, na sessão gráfica e sem sudo**:

```sh
saida="$HOME/Downloads/irixclassic-fechamento-$(date +%Y%m%d-%H%M%S)"
bash distribuicao/fechar-candidata.sh --saida "$saida"
```

O diretório deve ser novo e estar fora do clone. A coleta roda as três suítes
estáticas, os retestes de seleção/menus dos dois temas, o acabamento e a galeria
integrada nos dois temas. Captura **somente as janelas de demonstração**. Também
gera/verifica os dois ZIPs candidatos e instala/restaura o código extraído usando
um HOME temporário. Não altera a instalação em uso, fonte, escala ou tema global.

Evite interagir com as janelas de ensaio até terminarem. Nenhum software é
instalado automaticamente. As galerias precisam de PyQt6 ou PySide6 e do plugin
Kvantum compatível com esse Qt. Os testes de mapas usam CairoSVG e Pillow. No
Debian 13, estes dois últimos são `python3-cairosvg` e `python3-pil`; uma instalação
opcional e explícita é `sudo apt install python3-cairosvg python3-pil`.
Não execute os scripts de tema/coleta com sudo.

**Não define `QT_QPA_PLATFORM` nem um backend de renderização implicitamente.**
Execução com `offscreen`/`minimal` fica identificada e não aprova a evidência da
sessão de desktop. Uma ausência, erro, timeout ou relatório parcial não vira
resultado aprovado. Retornos:

| Código | Significado |
|---|---|
| 0 | Candidata aceita localmente, após avaliação explícita do aceite manual. |
| 1 | Falha de teste, integridade ou execução. |
| 2 | Ensaios concluídos; inspeção humana pendente, ou ajuste visual solicitado. |
| 77 | Evidência incompleta: dependência/ensaio ausente, teste ignorado ou plataforma sem sessão gráfica. |

A coleta normal pode terminar em **2** sem que isso seja uma falha. Leia o
relatório. O estado de candidato e `stable_approved=false` não mudam mesmo após
um aceite local: uma futura versão estável e publicação exigem decisão explícita.

## Saída única

- `FECHAMENTO.html` e `FECHAMENTO.json`: estado de cada ensaio e seus limites.
- `capturas/`: conjunto nos dois temas; divisórias das duas toolbars e spinbox
  pressionada/solta/indisponível. Não são imagens geradas nem capturas do desktop.
- `resultados/` e `logs/`: resultados parciais e finais dos processos de teste.
- `pacotes/`: tema mínimo, código-fonte, hashes e metadados da candidata.
- `ACEITE-VISUAL.json`: formulário inicialmente **pendente**, vinculado ao hash
  do relatório; só preencher depois da inspeção visual.
- `EVIDENCIAS-PARA-REVISAO.zip`: relatório, resultados, logs e imagens desta coleta,
  sem arquivos desconhecidos que estejam na pasta, sem os pacotes de código e
  sem histórico Git. Os caminhos do HOME e do clone são substituídos nos logs.

Não compartilhe um diretório pessoal inteiro: o ZIP de evidências já reúne o
necessário. É prudente revisar as observações escritas manualmente antes do envio.

## Aceite visual sem reabrir os blocos aprovados

No `ACEITE-VISUAL.json`, os três itens finais são: separadores nas duas
orientações; legibilidade/estados da spinbox; conjunto integrado e limitações
conhecidas. Utilize `pendente`, `aprovado` ou `reprovado`. Preencha a data ISO
`AAAA-MM-DD`, mantendo somente o nick público. Não há nome civil ou e-mail a
preencher. Os botões/scrollbars aprovados não foram redesenhados.

Depois:

```sh
bash distribuicao/fechar-candidata.sh --avaliar "$saida"
```

O programa verifica a correspondência entre relatório, insumos e evidências;
se algo mudou, exige uma coleta atualizada. Ele escreve `PARECER-FINAL.json` e
atualiza o ZIP de evidências, **sem transformar o teste em aprovação automática**.
SHA-256 é integridade local, não assinatura digital nem auditoria independente.
Um status `candidate_accepted_locally` permite encerrar esta candidata, não
certifica identidade pixel a pixel com todas as versões do IRIX.

## Escopo e diferenças mantidas

Os sete blocos têm implementação ou tratamento nativo descrito em
`kvantum/docs/COBERTURA-IRIXCLASSIC.md`. O mesmo SVG pode não controlar componentes
próprios de um aplicativo ou todos os componentes Qt Quick. Não há distinção
universal de superfície `readonly` no SVG do motor alvo. LEDs, thumbwheels,
comportamentos ViewKit/Motif específicos e reorganização de aplicações não foram
introduzidos como se fizessem parte de um tema de aparência.

Os pacotes não incluem fontes binárias, ícones globais, GTK, decoração KWin nem
bibliotecas SGI. Os arquivos das decorações e do Irixium moderno não são alterados.
Este não é um Global Theme KDE completo: é o Application Style Kvantum Classic.

## Inspeção sem executar e modo de desenvolvimento

```sh
bash distribuicao/fechar-candidata.sh --verificar
```

Esse modo valida os insumos e mostra o plano sem criar saída. Para ambientes sem
Qt, `--sem-nativos` junto de `--saida` executa somente a validação não gráfica;
retorna 77 e não conclui o aceite. Não use essa opção como atalho de aprovação.
As galerias podem ser reabertas individualmente sem reinstalar o tema.

## Fontes dos requisitos de execução

- Kvantum 1.1.4, instalação: https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/INSTALL.md
- Qt Test 6.8: https://doc.qt.io/qt-6.8/qtest.html
- Debian CairoSVG: https://packages.debian.org/trixie/python3-cairosvg
- Debian Pillow: https://packages.debian.org/trixie/python3-pil
