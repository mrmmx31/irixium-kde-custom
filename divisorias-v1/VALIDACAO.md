# Validação do pacote v1

## Executado neste ambiente

**23 testes automatizados passaram.** O registro completo está em
`tests/resultado.txt`. São testes Python em diretórios temporários, com a cópia
administrativa simulada por uma cópia local. Nenhum deles escreve no KDE real.

Cobertura principal:

- Instalação, verificação sem escrita, backup, restauração exata e reinstalação
  sem criar um backup redundante; manutenção das permissões do arquivo do usuário.
- Recusa de componente QML diferente da base, backup adulterado, link simbólico
  no arquivo do tema e alterações posteriores à instalação.
- Cancelamento da autorização, falha simulada de cópia parcial e recuperação
  do arquivo anterior; preservação das demais configurações locais.
- Comparação do componente original com a parte não modificada; comparação
  integral da seção `[Layout]` antes/depois; filtro do caminho Irixium e ausência
  de novos capturadores de entrada.
- Cálculos de coordenadas: separadores dentro da barra e oito marcas dentro
  das faixas da moldura, para uma matriz de tamanhos de janela.

A sintaxe Python foi verificada com `py_compile`; os dois scripts de entrada
foram verificados com `sh -n`.

Comandos para repetir os testes, dentro da pasta do pacote:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile irixium_install.py
sh -n instalar-divisorias.sh
sh -n restaurar-divisorias.sh
```

## Preservação do alinhamento

Os valores de altura, largura, espaçamento e margens do `Irixiumrc` de referência
não foram alterados. A sobreposição não modifica `Row.spacing`, o tamanho dos
botões ou a expressão original `anchors.topMargin` do grupo.

Com os valores do repositório, o centro da caixa de botão continua em 20
unidades lógicas a partir do topo da decoração normal (`3 + 6 + 22/2`) e em 17
na maximizada (`0 + 6 + 22/2`). Essas são verificações aritméticas de preservação
da geometria, não medições de uma captura renderizada pelo KWin.

## Não executado

**Não foi possível carregar/compilar o QML em Qt 6 nem testá-lo numa sessão
KWin/Plasma 6 neste ambiente.** Não foram validados graficamente X11, Wayland,
escala fracionária, comportamento de hover/pressionado ou a apresentação final
sobre o tema instalado do usuário.

Os testes de geometria são um modelo aritmético das coordenadas do arquivo,
não uma simulação completa do Qt Quick. As verificações do instalador não
substituem esse teste gráfico. É por isso que o pacote inclui backup,
restauração e recusa de uma base de componente diferente.

A primeira aplicação deve ser tratada como teste local: confirmar a renderização
nas janelas normal/maximizada e ativa/inativa antes de integrar ao repositório.
