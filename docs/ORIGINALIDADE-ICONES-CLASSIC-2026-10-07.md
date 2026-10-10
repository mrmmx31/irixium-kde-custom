# Originalidade e menus do IRIX Classic — 7 de outubro de 2026

Revisão 0.4.0: foram redesenhadas 214 identidades de aplicativos e categorias
selecionadas por repetição, ausência ou afastamento do padrão SGI. VS Code usa
uma fita dobrada; IntelliJ conserva o motivo IJ. Chrome Apps usa uma esfera
com as três cores do navegador, distinguindo-se da categoria Internet. Games, Education, Science e
System usam objetos em perspectiva, contorno escuro, cores contidas, sombra e
base de aplicação. Aplicativos gráficos, editores, terminais, ferramentas de
escritório, jogos e educação receberam motivos próprios.

As figuras foram desenhadas no repositório em SVG, usando os ícones originais
instalados como referência de identidade. Não incluímos os arquivos originais
de terceiros. Nomes e marcas pertencem aos respectivos titulares.

O catálogo editável é `icons/sources/classic-identities.json`; a geometria está
nos módulos `icons/tools/classic_*_art.py` e `classic_identity.py`. O gerador
`build_classic.py` produz todos os SVG e PNG, sem depender de fontes instaladas.
O pacote tem 951 ícones canônicos, 479 composições detalhadas, 2.378 nomes e
nove tamanhos nativos: 16, 22, 24, 32, 44, 48, 64, 96 e 128. Nomes de uma mesma
aplicação ou ação continuam compartilhando sua identidade deliberadamente.

A comparação SHA-256 com o pacote anterior encontrou 21.160 imagens idênticas
e 1.800 imagens alteradas. Todas as alterações pertencem às identidades
selecionadas. Acrescentamos também 19 nomes simbólicos de categorias KDE,
usando os desenhos já existentes, sem alterar seus equivalentes regulares.

TeXdoctk tinha Icon vazio; SNX referenciava um caminho inexistente e repetia
cinco seções Desktop Entry idênticas. O helper `adapt_classic_launchers.py`
corrige somente a cópia do usuário, conserva os comandos de execução e recusa
seções conflitantes. Também separa aplicativos cujos atalhos upstream fixam o
mesmo nome genérico. Substitui apenas valores antigos conhecidos; respeita
outras escolhas pessoais e oferece backup/restauração.

Instalação em outro computador, somente no perfil corrente:

```sh
python3 icons/tools/install_theme.py --atualizar
python3 tools/adapt_classic_launchers.py
```

A integração opcional do PIA permanece separada em `integrations/pia/README.md`.
O auditor externo não integra o repositório.

A validação inclui comparação de pixels distintos das 214 identidades em
16/22/32/64 px, cobertura dos nomes simbólicos KDE, geração reproduzível,
consultas Qt sem fallback e capturas reais do PCManFM-Qt após quatro etapas.
As capturas permitem conferir categorias, VS Code/IntelliJ, TeXdoctk, SNX e
submenus de jogos/educação. Arquivos locais de resultado ficam em Downloads;
não fazem parte dos assets do tema.

Referências de desenho: [SGI Indigo Magic, capítulo 2](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch02.html),
[VS Code](https://code.visualstudio.com/brand/) e
[JetBrains](https://www.jetbrains.com/company/brand/).

Resultados automatizados: 35 testes de ícones e 78 testes gerais aprovados;
21.402 consultas Qt retornaram exatamente os PNG próprios, sem fallback.
As 39 entradas de categorias KDE instaladas resolveram ícones próprios.
A reconstrução completa reproduziu as 23.780 imagens byte a byte.
A validação estrutural terminou com zero erros e zero avisos.

O auditor externo local encontrou 769 lançadores, 3.863 referências e 1.589
nomes não vazios: todos os nomes consultados vieram do próprio Classic nas
12 combinações de tamanho/escala. Valores Icon vazios são registrados
separadamente; eles não representam nomes de ícones ausentes. A auditoria da
suíte instalada, incluindo sons e seleção Classic, terminou sem divergências.
