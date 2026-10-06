# Validação — IrixClassic Sounds 0.1.0

Manutenção: mrmmx31. Registro de 06/10/2026.

## Executado nesta entrega

- **46 testes Python** do catálogo, fonte fixada, geração, WAV, instalação e
  restauração passaram, inclusive uma execução como usuário comum.
- **13 testes do aplicador de merge** passaram como usuário comum: verificação
  sem escrita, adição exata, idempotência, reversão, proteção contra edições,
  stage, arquivos versionados, symlinks e pacote adulterado. Branch, HEAD,
  index e arquivos fora de `sons/` permaneceram intactos.
- FFmpeg e ffprobe foram usados de verdade em conversões de AIFF de teste;
  o PCM estéreo de 16 bits foi comparado com a entrada, preservando canais,
  taxa e amostras. O arquivo de teste foi criado e removido em pasta temporária.
- O tema de ensaio gerou 24 WAVs, 24 descrições `.sound`, oito `.disabled` e
  os cinco arquivos de índice, procedência, catálogo, galeria e manifesto.
  Instalação e restauração copiaram e removeram esses arquivos em diretórios
  temporários de usuário, com conferência de conteúdo.
- Uma falha de escrita injetada provocou restauração dos arquivos anteriores;
  edições posteriores desconhecidas foram recusadas. Não é uma promessa de
  atomicidade com aplicativos abertos ou de imunidade a qualquer falha de disco.

Também passaram três verificações de linha de comando com usuário comum e HOME
isolado: inventário sem criar arquivos, listagem dos 24 nomes sem tocar áudio e
recusa de instalar um tema quando faltam as fontes locais.
Sintaxe dos seis módulos Python e dos 6 scripts shell conferida.

## Limites importantes

**Os originais SGI não fazem parte do pacote público nem foram baixados pelo fluxo
versionado.**
Os tamanhos e identificadores Git blob foram consultados no espelho fixado,
mas o acesso de rede do runtime não conseguiu resolver os hosts de download.
Os testes de conversão utilizaram exclusivamente AIFFs artificiais, com um
catálogo de ensaio em memória. Isso não valida o som real de nenhuma amostra
SGI. O catálogo público e o instalador não possuem opção para aceitar substitutos.

A importação dos oito originais, a decodificação de cada um e a conferência
final de duração/PCM acontecem somente quando o usuário fornece uma pasta local
com `--origem`. Arquivo ausente, divergente, silencioso ou inválido interrompe
a instalação; não é gerado um tema fictício para fazê-la parecer concluída.

**Nenhuma sessão KDE/libcanberra foi executada aqui.** libcanberra não está
instalada neste runtime, e não foi feita uma audição. O índice e os nomes foram
conferidos contra o código do Plasma 6.3 e a especificação freedesktop; a
seleção no KCM, o lookup de áudio e a audição ainda precisam da máquina de destino.
Não é necessário repetir os testes gráficos do Kvantum para isso.

O instalador público não faz chamadas de rede. Identificadores Git blob não são
assinatura da SGI. Direitos dos áudios são separados da licença de código:
consulte CREDITOS-E-AUDIOS.md.

## Reproduzir

Na raiz do ZIP extraído, como usuário normal:

```sh
bash sons/testar.sh
python3 -B testar-merge.py
```

Os testes não acessam a rede nem reproduzem áudio. Exigem Python 3 e Git; os
ensaios de conversão usam FFmpeg/ffprobe e indicam `skipped` se ausentes, nunca
os contam como conversões aprovadas. Não instalam dependências.

O aceite de uso inicial é simples: importar, selecionar IrixClassic Sounds no
KCM e ouvir a prévia geral e seus cinco atalhos. `sons/ouvir.sh` permite separar
falha de lookup de falha de reprodução direta, sem alterar as configurações.
