# Acabamento localizado — 0.7.1-rc1

Manutenção: `mrmmx31`. Base revista: `#kvantum-classic-rc1`, commit
`24802858c12ce71ffe75d3bd4f563622833fe70f`. Tema: **IrixClassic**.

## Evidência e escopo

Esta entrega responde às capturas e resultados fornecidos no aceite visual de
2026-10-05: seleção Classic 11/11; menus Classic 17/17; divisão da toolbar
visualmente incorreta; indicadores da spinbox pequenos. As capturas comparáveis
foram feitas em Qt 6.8.2, Kvantum, fonte 14 px e DPR 1, plataforma offscreen.
Não são capturas de todos os componentes Qt Quick nem comprovação histórica de
cada estado. Nenhum dado pessoal ou screenshot do usuário é distribuído aqui.

O problema das setas da scrollbar foi confirmado como resolvido pelo usuário.
O SVG da scrollbar e o reparo opcional do módulo KDE ficam **intocados**. Não
reinstale o reparo para testar esta revisão. Não se altera Irixium, Aurorae,
IRIX Classic da decoração, GTK, fontes, paleta global ou escala da sessão.

## Divisória da barra de ferramentas

O recurso anterior `ic-toolbar-separator` tinha 10×2 pixels com duas faixas
horizontais; a área de destino da barra horizontal é alta e estreita. O novo
`ic-finish-toolbar-separator` tem célula 10×12, com duas colunas pintadas no
centro e quatro colunas transparentes de cada lado. A alocação do separador
continua com 10 unidades; não se muda `indicator.size`, espaçamento ou botões.

A orientação canônica é vertical. O Kvantum 1.1.4 reorienta o recurso quando
precisa desenhá-lo numa toolbar vertical. O ensaio novo cobre as duas orientações.
O handle é copiado sem mudanças para a nova família de recursos; o separador de
menu `ic-arrow-separator` não é redirecionado nem modificado.

Fonte técnica primária: Kvantum V1.1.4, `Kvantum/style/Kvantum.cpp`, casos
`PE_IndicatorToolBarSeparator` e `PM_ToolBarSeparatorExtent`:
https://github.com/tsujan/Kvantum/blob/V1.1.4/Kvantum/style/Kvantum.cpp

## Setas do campo numérico

`IndicatorSpinBox.indicator.element` passa para `ic-finish-spinmark`. A máscara
escura ocupa 7×6 pixels, antes 5×4, dentro da mesma célula 12×12. Não são as setas
da scrollbar. `spin_button_width=16`, margens, bordas e comportamento continuam
inalterados. A pressão acrescenta o relevo claro inferior/direito sem mover a
máscara escura. Hover mantém o desenho normal; indisponível tem menor contraste.
Direções opostas derivam da mesma máscara. Cores e estados são adaptações de
legibilidade; não se anuncia equivalência histórica pixel a pixel.

As coordenadas do SVG são medidas da fonte. O tamanho final depende da alocação
e do caminho do motor. O teste nativo informa as métricas e exercita a spinbox
real; a prancha técnica não substitui esse teste.

## O que foi examinado e deliberadamente preservado

A barra de menus tinha 30 px na captura Classic, com a fonte de teste de 14 px.
Os 24 px de uma captura antiga do IRIX não definem uma regra universal para
outras fontes e aplicativos. Nesta candidata **não se muda qualquer margem,
altura mínima, fonte ou recurso de menu**. O ensaio mede novamente a altura,
em vez de forçá-la e introduzir cortes. O ajuste de densidade continua sujeito
a aceite visual, não é declarado concluído por esta entrega.

Campos editáveis e somente leitura continuam usando a mesma superfície da
0.7.0-rc1. A distinção histórica desejada permanece documentada em CAMPOS.md e
COBERTURA-IRIXCLASSIC.md; não há uma promessa de cor readonly universal. Não
foram introduzidos filtros de aplicação, folhas de estilo ou patches no motor.

## Testes dos dois temas

A galeria `prever-selecao.sh --testar --tema Irixium` agora usa as dimensões
reais do indicador e compara os estados marcado e desmarcado do próprio tema.
Não exige o vermelho/azul exatos do Classic. Para IrixClassic, as verificações
exatas de suas cores foram mantidas. O moderno não foi alterado para satisfazer
um teste de outro tema.

Menus agora registram a etapa, o progresso, a tentativa de entrada, os eventos
e o erro antes de encerrar um ensaio interrompido. `--resultado` salva JSON
parcial incrementalmente, em arquivo novo, com permissão 0600. Um menu invisível
continua reprovando a execução; não se chama `trigger()` nem se reabre um menu
silenciosamente para fazer o teste passar. A falha anterior do moderno não foi
atribuída a uma causa ainda não demonstrada.

## Uso local (na raiz do clone)

```sh
bash kvantum/testar-acabamento.sh
bash kvantum/prever-acabamento.sh
bash kvantum/prever-acabamento.sh --testar \
    --resultado "$HOME/Downloads/resultado-acabamento-071.json"
bash kvantum/prever-selecao.sh --testar --tema Irixium
bash kvantum/prever-menus.sh --testar --tema Irixium \
    --resultado "$HOME/Downloads/resultado-menus-irixium-071.json"
```

Escolha nomes novos de saída. As galerias usam configuração temporária, sem
instalar ou selecionar o tema global. PyQt6 **ou** PySide6 e o plugin Kvantum
precisam estar disponíveis para o mesmo Python/Qt. Dependência ausente retorna
77; não equivale a aprovação. Não há download/instalação automática.

A revisão integrada com `--nativos` também inclui a galeria de acabamento.
O runtime da sessão é preservado. `--offscreen` na galeria de acabamento é opção
explícita, não prova de interação com o compositor Wayland.

## Instalação e restauração

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
# Para retornar à instalação anterior:
bash kvantum/restaurar-classic.sh
```

Sem sudo. O instalador conserva a seleção atual. Reabra os aplicativos; não é
necessário reinstalar a decoração nem modificar o componente KDE de rolagem.

## Preservação e limites da validação

Há 44 recursos novos. Os 5.147 anteriores, suas coordenadas e os mapas antigos
permanecem no SVG. Apenas dois encaminhamentos efetivos do kvconfig mudam:
Toolbar.indicator.element e IndicatorSpinBox.indicator.element. O handle da
toolbar permanece igual. A célula dos símbolos e todas as métricas continuam.

As suítes dos blocos anteriores projetam somente esses dois encaminhamentos
explicitamente reconhecidos para conferir os contratos anteriores. Uma nova
suíte compara **a configuração efetiva real completa** com a baseline 0.7.0-rc1
mais as duas mudanças autorizadas. Valor inesperado não é normalizado. As
baselines históricas não foram sobrescritas; o reparo KDE atual também é
verificado separadamente. As asserções antigas que exigiam a persistência do
bug das setas foram atualizadas para a confirmação recebida do usuário.

`PREVIA-ACABAMENTO.png` é uma composição de mapas; não uma captura do Qt.
Rasterização em CairoSVG, checks de código e simulações de relatórios não
substituem o teste local Qt/Kvantum. A aprovação de seleção/menus na versão
anterior não é estendida automaticamente a este executor novo.
