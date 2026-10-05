# Setas: ação de rolagem e relevo são verificações diferentes

O relato de falha em outros Application Styles é motivo para **parar de
compensar o problema no SVG**. Não prova sozinho a origem exata: é necessário
separar Qt Widgets, Qt Quick/KDE e eventuais componentes próprios do aplicativo.
Também não confirma se o reparo opcional anterior chegou a ser instalado ou
qual cópia do módulo uma sessão já aberta carregou.

## Nesta entrega

O tema conserva todos os desenhos e parâmetros da rolagem. Nenhum reparo global
novo é instalado. O utilitário opcional anterior também não é executado ou
ampliado. Seu objetivo declarado era encaminhar o estado visual de pressão;
não foi validado na sessão do usuário e não certifica toda falha de ação.

`diagnosticar-setas.sh` separa:

1. **Movimento**: o valor/posição muda na direção esperada durante a pressão?
2. **Apresentação**: muda a célula renderizada ou chega `sunken` ao StyleItem?

Um pode falhar sem o outro. A versão 6.13 do `org.kde.desktop` recebe os cliques
na MouseArea das setas, mas o desenho consulta `controlRoot.pressed`. O mesmo
módulo utiliza o QStyle da aplicação; por isso um problema desse caminho pode
aparecer com Fusion, Breeze e Kvantum. Isso é hipótese a testar no sistema, não
a confirmação da versão, módulo carregado ou causa do relato atual.

Fontes técnicas:
- https://github.com/KDE/qqc2-desktop-style/blob/v6.13.0/org.kde.desktop/ScrollBar.qml
- https://github.com/KDE/qqc2-desktop-style/blob/v6.13.0/plugin/kquickstyleitem.cpp
- https://github.com/qt/qtbase/blob/v6.8.2/src/widgets/widgets/qscrollbar.cpp

## Somente inventário

```sh
bash kvantum/diagnosticar-setas.sh
```

Consulta versões, seleção Kvantum, variáveis de estilo/escala específicas,
SHA-256 dos `ScrollBar.qml` encontrados e as diretivas `prefer` de seus módulos.
Não lê todo o ambiente, não coleta área de transferência, capturas da área de
trabalho ou configurações inteiras de aplicativos. Caminho HOME é abreviado.

Os arquivos encontrados no disco não provam qual cópia o Qt carregou: pode
haver recurso embutido, pacote diferente, cache ou caminho de importação extra.

## Ensaio cruzado, sem trocar o tema do desktop

```sh
bash kvantum/diagnosticar-setas.sh --testar --saida "$HOME/Downloads/diagnostico-setas"
```

Use diretório novo ou vazio. São até seis processos/janelas próprios:
**Fusion / Breeze / Kvantum**, cada um em **Qt Widgets / Qt Quick**. Dependências
ou estilo ausentes retornam 77 e ficam como `skipped`, não como falha da seta.
A família Kvantum usa IrixClassic do checkout em configuração temporária.
O teste Qt Quick usa o **org.kde.desktop instalado**, não uma cópia remendada.
Não usa QProxyStyle nem reencontra o problema através de pintura própria.

O QTest envia mouseMove/Press/Release apenas para as janelas artificiais.
Em Widgets registra o valor e diferenças de pixels da própria seta; em Qt Quick,
posição, conteúdo e estados de MouseArea/StyleItem. No caso QML a propriedade
privada pode mudar de versão: ausência de região identificável vira `not_available`.
As regiões das setas são encontradas pelo `hitTest` nativo; o StyleItem 6.13
não expõe retângulos up/down de scrollbar em `subControlRect`. Não presumimos
a altura das setas a partir do tema.
Estilos sem setas também não são acusados de falha de ação.

O ensaio não lê entrada física de outro aplicativo nem reproduz automaticamente
qualquer aplicação problemática. Para conferir manualmente o mesmo teste:

```sh
python3 kvantum/tools/diagnose_arrows.py --probe quick --style Fusion --manual
python3 kvantum/tools/diagnose_arrows.py --probe widgets --style Fusion --manual
```

A ausência de mudança de pixels é uma observação, não prova automática de defeito:
um estilo pode usar um relevo menos perceptível. O teste exige variação de posição
para aprovar **ação**. Não classifica como ação correta apenas porque houve pintura.

## Interpretação

| Resultado | Investigação seguinte |
|---|---|
| Widgets move; Qt Quick não move, em vários estilos | Encaminhamento de eventos / módulo QML, não desenhos do IrixClassic. |
| Todos movem; Qt Quick não recebe sunken | Caminho de pressão visual do estilo desktop. |
| Widgets e Qt Quick falham com vários estilos | Verificar runtime, entrada e plataforma; não concluir que é apenas QML. |
| Testes movem, aplicativo não | Investigar componente, ambiente e runtime daquele aplicativo. |
| Sem retângulo/dependência/estilo | Teste não disponível; não há aprovação nem diagnóstico de falha. |

Arquivo: `DIAGNOSTICO-SETAS.json`. Ele contém somente dados do ensaio e inventário
limitado. Rever antes de compartilhar. A permissão do arquivo é 0600.
A pasta de saída é a única gravação persistente solicitada pelo diagnóstico.
Não há sudo, instalação de pacotes, alteração do módulo, reset de configuração
ou troca global de Application Style.
