# 1.0.0-rc2 — correção do duplo clique no menu

- Impede publicar o menu na primeira pressão/soltura esquerda quando é necessário
  distinguir clique simples de duplo clique.
- Clique simples pendente usa o intervalo nativo do Qt; o temporizador nunca
  prolonga a aparência pressionada.
- Evento nativo de duplo clique cancela a abertura pendente e solicita Fechar uma
  única vez. Eventos sem primeiro clique válido não fecham a janela.
- `menuDoubleClickClosesWindow: true` habilita o comportamento apenas na IRIX
  Classic; nenhuma preferência global do KDE é escrita.
- Clique direito permanece imediato no perfil padrão; manter o esquerdo
  pressionado permite solicitar o menu pelo evento pressAndHold do Qt.
- Cancela pedidos pendentes em perda de foco, ocultação, geometria e política.
- Mantém o mesmo destino/ID, autoria pública mrmmx31, backup e restauração.
- Arte e geometria preservadas byte a byte em relação à rc1.
- Amplia testes de regressão, incluindo a sequência real Press-Release-Press-
  DoubleClick-Release em QtTest (fornecida para execução local).

# 1.0.0-rc1 — base consolidada

- Nome constante IRIX Classic. Atualizador reutiliza o ID selecionado da v4/v5.
- Mapas gráficos aprovados preservados byte a byte; nenhuma fonte é distribuída.
- Geometria, composição, estado de entrada e adaptação KWin em módulos separados.
- Um Canvas gráfico para moldura e controles; sem Canvas por botão.
- Controlador de gesto explícito, sem timers visuais; cancelamento e capacidade.
- Cliques em controles indisponíveis não passam para a área de título subjacente.
- Segundo clique não-menu deixa de ser suprimido por um handler genérico de duplo clique.
- Estado indisponível independente do foco da janela; ação revalidada no adaptador.
- Geometria de alvos pequenos evita a colisão existente no limiar estreito da v5.
- Migração de ajustes literais, backup verificado, troca por staging/rename,
  lock de instalação, recibos e recuperação após interrupção.
- Testes QtTest incluídos para execução local, sem registrar sucesso inexistente.

Esta revisão candidata não declara resolvida a transferência de captura para o
menu nativo. O ensaio Wayland/KWin continua sendo o critério de aprovação.
