# IrixClassic Kvantum 0.7.1 — primeira versão estável

**IrixClassic 0.7.1 estável** traz a linguagem visual do SGI IRIX/Indigo Magic
para os controles de aplicativos que utilizam o estilo Qt/Kvantum.
Manutenção: **mrmmx31**. Licença: **GPL-3.0-or-later**.

## Instalação

Baixe **IrixClassic-0.7.1-kvantum.zip**, extraia e instale a pasta **IrixClassic**
pelo Kvantum Manager. Escolha IrixClassic nesse gerenciador e mantenha o
Application Style do KDE em **kvantum**. Reabra os aplicativos. Sem sudo.
O plugin Kvantum deve estar instalado pela distribuição; ele não vem neste ZIP.

O pacote **IrixClassic-0.7.1-codigo.zip** inclui os geradores e a instalação de
usuário com backup/restauração. Os dois pacotes e `SHA256SUMS` correspondem ao
mesmo lançamento. Hashes verificam integridade; esta entrega não é assinada.

## Incluído

Barras de rolagem e setas; botões de comando e ferramentas; campos, combos e
spinboxes; checkboxes e radios; menus; abas; sliders, progresso, divisores,
cabeçalhos, listas/árvores e recursos complementares. O acabamento inclui o
separador fino da toolbar em ambas as orientações e indicadores numéricos
mais legíveis. A decoração externa IRIX Classic é um componente separado.

## Promoção sem redesenho

Esta versão promove explicitamente **0.7.1-rc1**, aceita localmente em
**06/10/2026**, preservando toda a arte renderizada e as configurações funcionais.
Foram alterados identificação da versão, documentação e empacotamento.
A candidata teve 445 casos nas suítes, 87 verificações nativas nas galerias e
8 verificações de instalação/restauração isolada aprovados na coleta recebida.
O ambiente de referência foi Debian 13, KDE/Wayland, Qt 6.8.2 e Kvantum 1.1.4.
Isso descreve o ambiente testado; não certifica todas as versões/distribuições.

## Limites conhecidos — não impedem este lançamento

A diferença de fundo entre campos editáveis e somente leitura não é universal.
Controles próprios de aplicativos e algumas interfaces Qt Quick podem não seguir
todo o tema. Há adaptações históricas e controles nativos: não se promete cópia
pixel a pixel de todas as interfaces e interações do IRIX. A densidade depende
também da fonte, dos ícones e do aplicativo. Fontes e ícones globais, GTK, estilo
Plasma e decoração KWin não são incluídos.

O reparo de pressão das setas do módulo KDE `org.kde.desktop` é **separado e
opcional**. Foi confirmado na instalação de referência; instalar o tema não
altera arquivos do KDE nem aplica esse reparo. Quem já o utiliza não deve
reaplicá-lo sem necessidade. Novos usuários devem consultar a documentação do
projeto antes de qualquer ajuste desse componente compartilhado.

## Feedback e próximas versões

Relate problemas nas Issues de **mrmmx31/irixium-kde-custom**, indicando versão do
tema, aplicativo, versões do Qt/KDE/Kvantum, escala da tela, comportamento esperado
e observado. Capturas devem ocultar dados pessoais. Melhorias de fidelidade,
compatibilidade e acessibilidade serão desenvolvidas em versões posteriores;
**não substituiremos os arquivos desta versão publicada por outros diferentes**.

Créditos: configuração derivada do Irixium de Mark Whittaker (Phob1an); arte
Classic e ajustes mantidos por mrmmx31. Projeto independente, não oficial da SGI.
