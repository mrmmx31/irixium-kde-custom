# Revisão integrada r1 — IrixClassic

Manutenção: `mrmmx31`. Esta revisão não é uma nova pintura do tema: os arquivos
instaláveis continuam exatamente os da **0.7.0-rc1**. O pacote de merge inclui o
bloco 7 para quem ainda está na 0.6.0-rc1 e reconhece os mesmos arquivos já
aplicados localmente. Não reaplica automaticamente correções em `/usr`.

## O que o comparativo efetivamente mostrou

O relatório recebido, `four_path_arrow_comparison`, foi gerado com Kvantum,
Qt 6.8.2/PyQt6 em Wayland. Em Qt Widgets, os quatro casos mostraram movimento
na direção esperada e mudança nos pixels da seta. Isso é evidência daqueles
controles de teste, não de todo aplicativo possível.

No Qt Quick instalado, os três primeiros casos rolaram, mas a área de mouse
estava pressionada enquanto o StyleItem continuava com `sunken=false`.
O quarto caso não pode ser contado como uma falha da seta horizontal direita:
a cena anterior sobrepunha as barras. Os retângulos registrados foram:

| Barra | x | y | largura | altura |
|---|---:|---:|---:|---:|
| Vertical | 590 | 64 | 18 | 282 |
| Horizontal | 12 | 328 | 596 | 18 |

A interseção calculada é **(590, 328, 18, 18)**. O ponto destinado à seta direita
fica nessa interseção, que também contém a seta inferior vertical. O valor
vertical mudou durante o ensaio horizontal. Isso identifica um defeito de
isolamento **da cena de teste**, não uma conclusão sobre a geometria de todas
as aplicações KDE.

Nos caminhos de arquivo direto e cópia corrigida, os casos identificados como
`down` registraram `activeControl=upPage`. A sonda reutilizava geometria sem
validar o alvo vivo antes de pressionar. Esses casos não comprovam falha de
pressão da seta esperada. A causa exata de cada desencontro anterior não está
estabelecida apenas pelo JSON.

Na cópia temporária corrigida, os dois casos de decremento tiveram movimento,
`sunken=true` durante a pressão e `sunken=false` depois de soltar. É evidência
favorável ao reparo nesses dois casos, **não certificação das quatro direções**.
Não houve registro dos pixels da seta nesses testes Quick antigos.

O inventário permaneceu sem marcador do reparo e com `prefer` para o recurso
embutido. O comando de comparação não instala essa correção. O JSON não
comprova qual cópia um aplicativo alheio à sonda já aberto carregou.

## Correções no ensaio

Os três caminhos Qt Quick passam agora pela mesma cena e pelo mesmo executor:

* Importação instalada de `org.kde.desktop`.
* Arquivo QML do disco, copiado byte a byte.
* O mesmo arquivo com o reparo opcional apenas na cópia temporária.

A cena reserva o canto das duas barras; elas não se sobrepõem. O alvo é medido
novamente após o layout e antes de cada pressão, incluindo transformação para
coordenadas da janela. O observador registra a área que recebeu o evento, a
classificação nativa de hit-test e a alteração do outro eixo. Ele não altera
`mouse.accepted`, `activeControl` ou `sunken` do componente.

Uma pressão que atinja `upPage`, outra barra ou um alvo que não estabilizou é
**inconclusiva**, nunca uma reprovação inventada da seta. Os quatro pares
orientação/direção precisam estar presentes, distintos e válidos para aprovar
o conjunto. As mudanças de valor, estado de pressão, soltura e pixels são
registradas separadamente.

## Executar a revisão integrada

Na raiz do clone atualizado, como usuário comum:

```sh
bash kvantum/revisar-integracao.sh --saida "$HOME/Downloads/revisao-irix-r1"
```

Esse modo confere a integridade, executa as suítes estáticas e de transação em
ambientes temporários e verifica que os arquivos de aparência não mudaram.
Produz `REVISAO-INTEGRADA.json`, `REVISAO-INTEGRADA.html` e logs individuais.
A pasta deve ser nova ou vazia; o relatório anterior não é sobrescrito.

Para acrescentar os testes nativos dos sete blocos e da galeria integrada:

```sh
bash kvantum/revisar-integracao.sh --nativos \
    --saida "$HOME/Downloads/revisao-irix-r1-nativa"
```

Os ensaios legados de Widgets dos blocos 1, 2 e 3 usam `offscreen` explicitamente;
isso aparece na categoria do relatório. Não certificam o compositor Wayland.
Os demais ensaios e a galeria integrada mantêm a plataforma da sessão.
Ausência de dependência retorna 77, nunca aprovação. O relatório não reduz
aceitação histórica ou visual a uma contagem de testes.

## Conferir a aparência em conjunto

```sh
bash kvantum/prever-integracao.sh
bash kvantum/prever-integracao.sh --tema Irixium
```

A mesma galeria, fonte local de 14 pixels e conteúdo artificial são usados nos
dois temas. A fonte da sessão não muda. `--fonte-px 16` permite comparar outra
densidade sem forçar essa opção no desktop. Não se trata de simulação de SVG:
as janelas usam os controles reais Qt Widgets e o plugin Kvantum.

```sh
bash kvantum/prever-integracao.sh --testar \
    --capturas "$HOME/Downloads/galeria-irix-r1"
```

A opção de captura salva somente a janela artificial e suas métricas, não o
desktop, aplicativos alheios, área de transferência ou documentos pessoais.
Não é selecionado `offscreen` silenciosamente; essa alternativa exige a opção
`--offscreen`. O código da galeria precisa ser executado na máquina com Qt.

## Conferir a correção das setas sem instalar

```sh
bash kvantum/comparar-setas.sh --estilo kvantum \
    --saida "$HOME/Downloads/setas-validado-r1"
```

A classificação `collected` só significa que observações foram guardadas.
Leia `assessment` de cada caminho: os códigos são 0 para aprovação de todos
os alvos válidos, 1 para falha de interação observada, 2 para alvo inconclusivo
e 77 para dependência ou controle indisponível. Nenhum arquivo KDE é alterado.
O inventário de Widgets preserva seus códigos legados; cada sonda tem seu
próprio detalhamento.

## Aplicar ao KDE é uma etapa separada

O tema e a comparação não instalam o reparo. O utilitário já existente é:

```sh
bash kvantum/corrigir-pressao-qtquick.sh --verificar --diff
bash kvantum/corrigir-pressao-qtquick.sh
```

Execute **sem sudo na frente**; a autorização ocorre no utilitário. Ele trata
`ScrollBar.qml` e a preferência conhecida do `qmldir` somente quando o contrato
de origem é reconhecido e as fontes locais estão disponíveis. É uma alteração
do módulo compartilhado do KDE, não só do IrixClassic. Não foi modificado nesta
revisão. O teste temporário primeiro permite conferir a candidata sem instalá-la.
Reabra completamente as Configurações do Sistema depois de aplicar; processos
residentes requerem nova sessão. O utilitário não encerra processos.

```sh
bash kvantum/corrigir-pressao-qtquick.sh --restaurar
```

A restauração da aparência é independente, com `restaurar-classic.sh`.
Atualizações do pacote KDE podem substituir arquivos de sistema alterados;
não reaplicar às cegas sobre uma fonte desconhecida. Consulte `PRESSAO-QTQUICK.md`.

## Aceitação final dos sete blocos

O plano mestre continua em `../PLANO-IRIXCLASSIC.md`. A barra e os botões têm
aprovação visual anterior registrada. Campos, seleção, menus, abas e os demais
controles não recebem aprovação implícita por terem sido entregues. Na revisão
integrada, conferir: repouso, apontamento, pressão, soltura, foco de teclado,
indisponibilidade, seleção persistente, RTL, orientações e textos longos, onde
cada componente e o motor realmente suportam esses estados.

A correção do estado Quick e sua instalação permanecem separadas dessa aceitação.

## Fontes técnicas

Dados: relatório fornecido pelo usuário nesta revisão; seu JSON não é publicado
no repositório. Código anterior da sonda: branch #kvantum-classic-rc1 no commit
baaacfdbadbed333757c3d638ae461ace13ca8ef.

Qt 6.8, eventos e coordenadas de MouseArea:
https://doc.qt.io/qt-6.8/qml-qtquick-mousearea.html

Qt 6.8, QTest (eventos sintéticos):
https://doc.qt.io/qt-6.8/qtest.html

KDE qqc2-desktop-style 6.13.0, ScrollBar:
https://github.com/KDE/qqc2-desktop-style/blob/v6.13.0/org.kde.desktop/ScrollBar.qml
