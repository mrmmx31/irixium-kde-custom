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
- [ ] Menu: clique simples esquerdo abre uma única vez após a espera de duplo clique; relevo solta imediatamente.
- [ ] Menu: testar clique para deixar aberto, escolha de ação e cancelamento com Escape.
- [ ] Menu: manter pressionado até abrir e então arrastar/soltar; registrar a captura do KWin.
- [ ] Menu: duplo clique esquerdo fecha uma janela descartável sem popup intermediário.
- [ ] Menu: clique direito abre sem esperar o prazo do clique esquerdo e não fecha.
- [ ] Menu: habilitar/desabilitar a opção LOCAL; nenhuma mudança na chave global do KDE.
- [ ] Menu: sair da área após um clique simples pendente cancela a abertura.
- [ ] Menu: trocar o foco/ocultar enquanto há clique pendente não abre popup atrasado.
- [ ] Clique direito/central no maximizador preserva as operações nativas do KWin.
- [ ] Título comprido é elidido; janela estreita não sobrepõe alvos de clique.
- [ ] Troca de escala/tamanho/visibilidade não deixa botão preso.
- [ ] Restaurar a atualização e confirmar retorno à cópia exata anterior.

O perfil padrão prioriza distinguir clique simples de duplo. A abertura esquerda
não ocorre na primeira pressão: o clique simples espera, ou a pressão prolongada
solicita o menu pelo evento pressAndHold. A transferência de seleção arrastada para
o popup nativo precisa ser testada, não simulada por um piscar temporizado.
