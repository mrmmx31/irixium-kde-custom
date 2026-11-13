# Distribuição do conjunto completo

O checkout contém os 17 componentes gráficos declarados em `components.json`,
mais o código/catálogo do esquema de sons. Os três cursores também recebem
cópias de compatibilidade em `~/.icons`, com backup, para KDE/libXcursor. Use o fluxo do [README](README.md):

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash sons/instalar.sh --baixar
bash aplicar-tema.sh classic --exigir-sons   # ou: moderno
```

O terceiro comando baixa os oito originais e instala os sons para seu usuário,
com atribuição e verificação de identidade. Com cache preparado,
`sons/instalar.sh` funciona sem rede; `--origem` importa arquivos locais. Áudios e `sons/local/`
não entram em distribuição pública. Não gere arquivos de release a partir de
um diretório inteiro incluindo arquivos ignorados; use os arquivos versionados.

A aplicação faz a seleção coerente de Plasma, decoração, Kvantum, GTK, ícones,
cursores e sons já instalados. Para preservar os sons, use `--sem-sons`. O KCM
Tema Global sozinho não escolhe a seleção interna do Kvantum nem importa sons.
Não há alteração de recursos compartilhados de Aurorae ou instalação de SDDM.

Plasma 6, Aurorae/KSvg, Kvantum Qt 6 e, para importar sons, FFmpeg/ffprobe são
dependências da distribuição. Após instalar, encerre e entre na sessão para
recarregar o QML. As versões dos componentes são independentes; a distribuição
estável do Kvantum 0.7.1 permanece em `distribuicao/`, com seus registros de
aceite e empacotamento preservados.
