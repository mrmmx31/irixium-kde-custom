# IrixClassic 0.7.1-rc1 — notas para publicação da candidata

**Mantenedor: mrmmx31. Canal: candidata de teste.**
Tema de aplicativos para Kvantum, inspirado no IRIX/Indigo Magic. Não é software
oficial da SGI, não contém código ou bibliotecas SGI e não pretende certificar
identidade de todos os controles históricos pixel a pixel.

## Conteúdo

Estilo compacto para botões, campos, opções, menus, abas, barras de rolagem,
sliders, progresso, divisores, cabeçalhos, listas, árvores e outros controles
suportados pelo QStyle. Estados e diferenças nativas estão no mapa de cobertura.
A candidata 0.7.1 corrige as divisórias das toolbars e melhora os indicadores dos
campos numéricos. O SVG e as dimensões desta entrega não mudam na revisão de
fechamento; os acréscimos são ensaios, evidências e documentação.

## Instalar

O ZIP `IrixClassic-0.7.1-rc1-kvantum.zip` contém a pasta IrixClassic para o
Kvantum Manager. O ZIP `IrixClassic-0.7.1-rc1-codigo.zip` contém o mesmo tema,
fontes de seus desenhos e instalação/restauração de usuário com backup.
Nenhum plugin Kvantum, fonte binária, tema GTK ou decoração KWin é incluído.

O pacote mínimo não executa código. O instalador do pacote de fontes é opcional,
não usa privilégios administrativos e, por padrão, não muda o tema selecionado.
SHA256SUMS verifica os ZIPs; não é assinatura de autoria.

## Limitações conhecidas

A cor específica de campos somente leitura não é universalmente suportada
pelo SVG do motor alvo. Densidade depende de fontes/aplicativos. Algumas formas
ou comportamentos são nativos de Qt/Kvantum ou adaptações documentadas; widgets
próprios e interfaces Qt Quick podem não empregar todos os desenhos do tema.

O reparo das setas do componente Qt Quick do KDE, validado separadamente na
sessão do usuário, não é instalado pelos ZIPs de tema. Não reaplicá-lo sem
necessidade e não confundi-lo com a aparência Kvantum.

## Estado de validação

A reconstrução e verificação dos arquivos não substituem a inspeção gráfica na
máquina de destino. Publicar resultados da rodada final junto das notas, sem
substituir resultados ausentes por aprovações. Até o registro do aceite final,
o canal continua candidata; nenhuma tag ou publicação é executada pelos scripts.
