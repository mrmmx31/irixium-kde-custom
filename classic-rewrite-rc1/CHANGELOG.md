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
