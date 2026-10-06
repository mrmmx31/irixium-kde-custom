# Procedência e termos dos áudios

**IRIX desktop sounds courtesy the SGI desktop.**

O esquema Indigo Magic foi organizado por **R. C. Underwood** para IRIX 5.3,
em colaboração com **Roger Powell**; **Jeff Essex** criou o conjunto de sons
utilizado na seleção. Esta atribuição se baseia na página do organizador,
revisada em 24/08/1998 e arquivada em 11/09/2001:

https://ftp.jurassic.nl/mirrors/ftp.sgi.com/sgi/desktop/sounds/sounds.html

A página incentiva uso com atribuição na Web e em computadores pessoais.
Isso não equivale a uma proibição absoluta de versionar os sons; tampouco
esclarece redistribuição de um pacote convertido ou relicenciamento.
**Os áudios não são criação de mrmmx31 e não foram relicenciados.**

## Verificação em 06/10/2026

A [página histórica do organizador](https://ftp.jurassic.nl/mirrors/ftp.sgi.com/sgi/desktop/sounds/sounds.html)
foi consultada novamente. Não possuir uma licença GPL/CC, por si só, não invalida
uma autorização específica. A dúvida é o alcance do texto e a autoridade para
autorizar distribuição pública dos originais e WAVs. Não encontramos nesses
materiais uma autorização inequívoca para esse pacote.

O README e a árvore do [espelho no commit fixado](https://github.com/theodric/IRIX-noises-macOS/tree/08ffcbcb16787d60a33ff881e4a3169a98d428a0)
não acrescentam licença de redistribuição. A política abaixo é uma decisão
conservadora do projeto, não uma conclusão de que qualquer versionamento seria
ilegal. Para alterá-la, precisamos esclarecer essa permissão com o titular ou
representante autorizado, incluindo conversão e distribuição no GitHub/releases.
Em caso de dúvida, o [U.S. Copyright Office](https://www.copyright.gov/help/faq/faq-fairuse.html)
orienta obter permissão; essa orientação não decide o caso específico.

## Política desta distribuição

O ZIP público contém somente código, catálogo, configuração e documentação.
Os áudios são importados separadamente, pelo usuário, de fonte identificada ou de
uma cópia local com os mesmos bytes. Não se inclui material sonoro em commit,
release ou pacote público gerado por estas ferramentas. A possibilidade técnica
de obter um arquivo não é uma licença. Examine os termos aplicáveis antes de
redistribuir o tema gerado com os áudios.

A licença `LICENSE-CODE` (GPL-3.0-or-later) cobre nosso código de integração,
não concede direitos sobre áudios de terceiros. Não incluímos músicas de boot,
amostras Prosonus, ROMs, imagens de mídia IRIX ou fontes tipográficas.

## Espelho usado para identidade dos arquivos

https://github.com/theodric/IRIX-noises-macOS

Commit fixado: `08ffcbcb16787d60a33ff881e4a3169a98d428a0`.
Diretório: `irix-sounds-all/`, sem usar as versões renomeadas/conversões macOS.
Somente os áudios são lidos; nenhum script desse repositório é executado.

O arquivo `data/catalogo.json` registra tamanho e identificador Git blob de
cada original. A listagem preservada de ftp.sgi.com naquele repositório confirma
os nomes e tamanhos. O catálogo HTML arredonda os tamanhos e rotula ss1 como 10K;
a listagem preservada registra 95.724 bytes. Usamos o tamanho do arquivo, não
esse rótulo aproximado, para a verificação.

A conferência de Git blob SHA-1 identifica a cópia fixada no espelho; **não é
assinatura da SGI nem prova criptográfica de cadeia de custódia desde o IRIX**.
A importação registra também SHA-256 dos bytes obtidos e dos WAVs resultantes.
URLs HTTPS são verificadas com a confiança TLS padrão; não há opção insegura.

## Conversão

FFmpeg decodifica para WAV/PCM assinado de 16 bits little-endian. A taxa de
amostragem e os canais são preservados dentro do perfil aceito (8–48 kHz,
mono ou estéreo). Não há normalização de volume, ganho, corte, fade, repetição
artificial ou remixagem. A intenção é conservar as relações de volume do esquema
original, cuja edição de amplitudes é descrita pelo organizador. Metadados de
contêiner são removidos; isso não é preservação binária do arquivo AIFF original.

Os 19 nomes são catalogados. Somente oito arquivos necessários aos eventos
sistêmicos desta versão são importados. Sons específicos de arquivos/pastas,
lançamento e desktop não recebem integração nesta entrega. DropIgnore e
DeskSwitch constam do catálogo como nunca implementados; PutAway consta como
obsoleto no IRIX 6.3/6.4.
