# DomainOS 0.2.8 — troca efetiva do esquema KDE

Esta atualização corrige o percurso entre **Cores → Aplicar** e a arte do
painel. A paleta injetada dos ensaios anteriores não comprovava esse percurso:
Kvantum IrixClassic mantém a paleta de aplicação e o Plasma consulta os papéis
do esquema KDE separadamente. A composição aprovada continua sendo a referência.

## Falha reproduzida

No Plasma 6.3.6 instalado, `ColorsModel` usa `QFileInfo::baseName()` para o
identificador. `DomainOS-SR10.4.colors` torna-se `DomainOS-SR10`; Aplicar procura
`DomainOS-SR10.colors`, que não existe. A prévia lê o arquivo completo, portanto
pode estar correta apesar de a aplicação deixar os grupos `Colors:*` ausentes.
O CLI instalado compartilha esse caminho e chega a anunciar sucesso nesse caso.
Fontes oficiais correspondentes: [modelo de cores](https://raw.githubusercontent.com/KDE/plasma-workspace/v6.3.6/kcms/colors/colorsmodel.cpp)
e [aplicação do esquema](https://raw.githubusercontent.com/KDE/plasma-workspace/v6.3.6/kcms/colors/colors.cpp).

A prova privada do CLI analisada passou 9/9 verificações: identificador truncado,
grupos ausentes, nome seguro com conteúdo idêntico e aplicação dos esquemas
Irixium, Breeze Light e Breeze Dark. O resultado bruto conserva uma classificação
inicial incorreta: Breeze Light pode omitir `General/ColorScheme`, pois esse é seu
valor padrão. Não houve aplicação em um perfil pessoal durante essa prova.

## Correção

O destino instalado é `color-schemes/DomainOS-SR10-4.colors`; o nome visível
permanece **DomainOS SR10.4** e a fonte continua `colors/DomainOS-SR10.4.colors`.
Isso corrige o identificador sem usar referências de outra versão do Domain/OS.

`DomainOSKDEPalette` vincula a arte aos papéis nativos de `PlasmaCore.Theme`,
independentemente da paleta que Kvantum atribui à aplicação. Uma prova privada
de 33/33 verificações confirmou a atualização no mesmo engine por sinal KDE,
sem `QApplication.setPalette`, e a conservação do modo de referência.

O ensaio seguinte passou **71/71** verificações com aplicação pelo CLI instalado,
no mesmo engine/painel e com Kvantum IrixClassic. DomainOS, Irixium, Breeze Light,
Breeze Dark e um esquema amarelo privado atualizaram cores, URLs da arte SVG e
quatro FrameSvg nativos. A geometria permaneceu igual; o modo de referência e
o protótipo congelado continuaram idênticos por pixels em todas as trocas.
O amarelo privado acionou a proteção de contraste das duas luzes: 4,13 no Pager
e 3,23 na lente. Isso não é uma afirmação de contraste mínimo universal para
os demais esquemas históricos. Não ocorreram diagnósticos QML nesse ensaio;
os avisos de plataforma/sombra offscreen foram mantidos no relatório.

O arquivo legado só pode ser retirado automaticamente quando seus bytes são os
da versão canônica anterior. A migração mantém recibo e backup próprios,
preserva arquivos editados e permite restauração com guarda de alterações.
Ela não seleciona um esquema nem altera preferências do KDE. Os quatro destinos
principais do instalador continuam delimitados.

## Limites verificados

Uma prova no `plasmawindowed`/Kvantum real mostrou que usar somente
`Kirigami.Theme.inherit=false` não entrega todos os papéis Selection e efeitos
Inactive/Disabled. Outra prova confirmou que o QPalette completo do backend não
expõe seus papéis e grupos ao QML neste Qt 6.8.2. Essas alternativas não foram
adotadas como correção completa. Os estados de texto desativado nativos do Plasma
não equivalem a todos os efeitos de `QPalette::Disabled`.

Os 136 gates de papéis/arte/menus da rodada seguinte passaram, mas a inspeção
posterior de pixels passou somente 17/25 amostras: `StylePrivate.StyleItem` do
Kvantum continuava pintando as faces de Button/TextField com suas cores fixas.
Esse relatório negativo foi conservado e motivou a troca local dos componentes.

Os wrappers `DomainOSButton`/`DomainOSTextField` usam Plasma Components, sem
substituir o estilo global ou a barra aprovada. A prova dos wrappers com quatro
aplicações nativas de esquema passou 74/74 verificações analisadas; as asserções
iniciais incorretas sobre padding continuam no resultado bruto. Foram observados
80 × 26 para o botão de texto, 200 × 30 para o campo e 28 × 28 para os controles
compactos, no tamanho de fonte testado. Seis testes de entrada reais conferiram
pressão, uma ação por liberação, disabled sem ação e edição do campo.

O rodapé e a caixa de seleção de grupo tiveram 56 verificações privadas:
pintura no DomainOS e Breeze Dark, tamanhos contidos e um sinal nativo de
accepted/rejected por OK/Cancelar/Fechar, incluindo reconstrução dos botões
padrão. O ItemDelegate existente acompanha os papéis e foi conservado.
A lista agrupada completa teve 65/65 verificações em Wayland privado, com
grupos reais de três e duas janelas, seleção explícita e operações no conjunto
escolhido. Isso não equivale a cliques na sessão pessoal.

A rodada final da fonte passou **201/201** verificações no mesmo engine,
aplicando os cinco esquemas pelo CLI instalado, com Kvantum presente e sem
injetar `QApplication.setPalette`. As mesmas amostras de pintura que haviam
falhado passaram **25/25**; a caixa de seleção de produção passou **30/30**
verificações de pintura, papéis e área de clique nos dois estados. Arte,
menus QML, submenus, diálogos e dicas acompanharam as trocas. Geometria,
referência fixa e backup congelado permaneceram iguais. Os avisos offscreen
continuam preservados; não houve erro QML nessa rodada.

O percurso Gaveta → Preferências teve 16 verificações analisadas: nove
categorias próprias e duas categorias dos plugins de calendário instalados.
O resultado bruto conserva a premissa inicial incorreta de nove categorias
totais, os dois TypeError do PromptDialog upstream e o aviso de configuração.
Essa prova usa uma gaveta privada vazia; não afirma interação com favoritos
ou lançadores pessoais.

O QMenu de QWidget usado pelo menu direito das tarefas conserva o estilo de
aplicação Kvantum. A alternativa QSS local foi rejeitada porque alterou relevo e
geometria. Esta entrega não afirma recoloração universal desse menu nem dos
aplicativos externos. F31 continua com esse limite registrado.
As barras de rolagem fornecidas pelo estilo desktop também não foram substituídas
por esta atualização; sua recoloração integral não foi comprovada. A pintura
dos controles novos é uma prova separada dos papéis ativos e dos efeitos de
estado completos do QPalette.

## Instalação e recuperação

Os 58 testes dirigidos de catálogo, dependências, Bundle, ponte e migração passaram.
A migração foi ampliada para coordenar os dois recibos e recuperar também uma
retirada já concluída se ocorrer uma exceção depois do commit. Somente recibos
criados pela operação podem ser desfeitos; guardas de ambos são verificadas antes
da primeira restauração. `--recuperar` exige `--restaurar` e trata uma migração
interrompida sem desativar as guardas contra edições.

O teste público do CLI passou aplicando os quatro esquemas em HOME/XDG e D-Bus
próprios e conferindo os grupos efetivos de cores. Cinco testes de origem também
confirmaram a referência exclusiva SR10.4, os desenhos e a paleta de origem.

As provas de calendário, correio, pins e miniaturas da 0.2.7 continuam registradas
na [validação anterior](VALIDACAO-DOMAINOS-0.2.7-2026-10-09.md); não foram
reexecutadas integralmente nesta atualização. O arraste entre miniaturas do Pager
permanece adiado. Aceite nas sessões pessoais é separado das provas privadas.

O pacote final e a instalação desta atualização só são considerados verificados
após os ensaios dirigidos, conferência do arquivo e comparação dos recursos
instalados. Os relatórios privados conservam os resultados brutos e os hashes;
não são arquivos distribuídos nem pranchetas versionadas.
