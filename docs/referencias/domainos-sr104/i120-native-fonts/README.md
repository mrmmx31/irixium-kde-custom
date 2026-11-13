# Provas de fontes — I120

Capturas originais e logs ficam nesta pasta. São rótulos nativos não editáveis,
com leitura de volta de UTF-8; não são outra aplicação de edição nem uma
substituição da interface do laboratório. Motif atual não é a biblioteca da VM.

Reproduzir em uma sessão X11 própria, com Motif, GTK3/PyGObject, Xvfb e
ImageMagick instalados:

```bash
cc -std=c99 -Wall -Wextra -Werror motif-font-probe.c \
  -lXm -lXt -lX11 -o motif-font-probe
xvfb-run -a -s '-screen 0 1600x600x24 -nolisten tcp' python3 run-private.py
```

O runner consulta `kdeglobals` em XDG_CONFIG_HOME ou no diretório padrão XDG
do usuário; não altera esse arquivo. Face e texto são os papéis de janela
atuais. A execução escreve novas provas em `result/`, encerra apenas seus
processos e não envia eventos de teclado/mouse. `gtk` ou `motif` como argumento
final limita a execução à família escolhida. O backend GTK é X11 explícito;
Wayland e o endereço DBus pessoais não são herdados pelo processo de prova.

`fixed` no servidor observado não contém ISO10646. O log registra os charsets
ausentes; não interpretar leitura de texto idêntico como cobertura gráfica.
Os FontSets Helvetica incluíram uma fonte ISO10646 nesta instalação, porém
isso não certifica todos os idiomas. As candidatas GTK3 da amostra registram
o contexto/fontes efetivos e a quantidade de glyphs desconhecidos.

Não há seleção ou instalação automática da candidata com métricas próximas.
Confira o relatório principal e o recibo I120-NATIVE-FONTES-20261011.json.
