# Validação — IrixClassic 0.2.0-rc1

## Resultado executado nesta entrega

- 75 testes unittest passaram: mapas, geração determinística, integridade,
  regressão de rolagem, configuração herdada e reconhecimento do manifesto.
- CairoSVG renderizou independentemente 115 elementos de rolagem e 278 elementos
  novos de botões; cada pixel foi comparado com o mapa gerador correspondente.
  São 393 comparações de elementos dentro da suíte, não 393 testes nativos Qt.
- Os 1.846 elementos preexistentes fora dos oito estados pressionado/toggled
  das setas permanecem idênticos, incluindo IDs e transformações no atlas.
- Todas as configurações efetivas fora dos dois grupos de botões e do novo
  ToolbarButton foram comparadas com a rc2 (comentário da versão excluído).
- As 462 posições da borda do botão Close da captura IRIX fornecida coincidem
  com o comando normal gerado em 52×31; não inclui texto/ícone. Não certifica
  todas as renderizações do tema nem estados não vistos no screenshot.
- Os scripts novos passaram pela análise de sintaxe Python e shell.

A cópia de base dos arquivos do tema e ferramentas foi conferida por objetos
Git contra `4e9e56617d07374723b9db6a9716b3b861b4b028`. As árvores/arquivos fora
   do escopo não são incluídos no ZIP. Sem commit, push ou instalação no desktop
   do usuário.

## Não executado

O executor da galeria detectou ausência de PyQt6/PySide6 neste ambiente e
retornou **77**. Não foi carregado o plugin Kvantum nem o KWin. Isso não é um
resultado de teste gráfico aprovado.

A validação local deve confirmar a seleção efetiva dos estados pelo plugin,
principalmente a pressão da seta, o contorno de botão padrão e autoRaise.
A galeria inclui verificações de pixels na pressão, além de ações e sinais:

```sh
bash kvantum/prever-botoes.sh --testar
bash kvantum/prever-botoes.sh --capturas /tmp/irix-botoes-qt
```

A checagem pixel a pixel específica das setas é executada na grade nativa 18×18
com DPR=1; outros tamanhos/DPR continuam exigindo comparação visual. O programa
registra DPR e Qt no resultado. Não muda escala global ou configurações da sessão.

O histórico da rolagem permanece em VALIDACAO-ROLAGEM.md. O plano completo está
em ../PLANO-IRIXCLASSIC.md. Implementação para teste não é aprovação local.
