# Roteiro de aceitação local

Marcar os itens com resultado real. Não considerar estas caixas aprovadas por
terem passado os testes Node/Python. Mantenha a pasta extraída para restauração.

- [ ] Confirmar que `--verificar` aponta para a Classic efetivamente selecionada.
- [ ] Conferir carregamento da decoração após nova sessão, sem mensagens QML de erro.
- [ ] Comparar duas janelas lado a lado em 100%, ativas e inativas, sem hover visual.
- [ ] Pressionar e segurar cada controle: relevo invertido, símbolo imóvel.
- [ ] Arrastar para fora e soltar: minimizar/maximizar não executam a ação.
- [ ] Arrastar para fora, voltar e soltar: executa uma única ação.
- [ ] Maximizar/restaurar: mesmas proporções, título sem salto vertical indevido.
- [ ] Janela sem maximização: símbolo rebaixado, sem pressão/ação/arraste do título ao clicar nele.
- [ ] Menu: abre uma única vez, não reabre na soltura.
- [ ] Menu: testar clique para deixar aberto, escolha de ação e cancelamento com Escape.
- [ ] Menu: testar pressionar–arrastar–soltar; registrar se o KWin transfere o gesto.
- [ ] Menu: testar a preferência já existente de duplo clique para fechar em uma janela descartável.
- [ ] Clique direito/central no maximizador preserva as operações nativas do KWin.
- [ ] Título comprido é elidido; janela estreita não sobrepõe alvos de clique.
- [ ] Troca de escala/tamanho/visibilidade não deixa botão preso.
- [ ] Restaurar a atualização e confirmar retorno à cópia exata anterior.

Se o menu nativo não reproduzir a seleção arrastada, não corrigir isso por um
piscar temporizado. Registre o comportamento. `menuOpensOnPress: false`, em
Settings.qml, é alternativa local explícita e não certificação histórica.

Não execute `kwin --replace` para tentar resolver carregamento. Salve o trabalho,
restaure a cópia anterior se necessário e entre novamente na sessão.
