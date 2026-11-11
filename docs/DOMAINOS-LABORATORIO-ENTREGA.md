# Preparação da entrega do laboratório

Esta é uma candidata privada funcional T07–T09, sem nova publicação ou instalação.
A validação final T10 permanece para o fim, conforme a orientação do usuário.
[Inventário e hashes](review/T10-PREPARACAO-ENTREGA-20261011.json).

## Dez grupos de acompanhamento

| Item | Grupo | Situação desta consolidação |
| --- | --- | --- |
| T01 | Medidas e spins | Entrega anterior e avaliação separadas; não reabrir conclusão por contagem de testes. |
| T02 | Catálogo e montagem | Estado técnico `done`, sem autorização atual; não consta como próximo trabalho executável. |
| T03 | Propriedades e estados | Propostas e decisões parciais na prancheta; não presumir todos os controles prontos. |
| T04 | Toolkits e adaptadores | Autorizado; GTK3 privado, GTK2 parcial, outros adaptadores pendentes. |
| T05 | Cores e pipeta | Parcial; fallback KDE e pipeta foram provados, mas papéis/fatores continuam compartilhados por família, não por controle. Consulte o recibo T05. |
| T06 | Código e busca | Concluído tecnicamente; revisão humana pendente. Busca UTF-8 nos dois sentidos, realce pela paleta escolhida, alias `_breeze` explicado e snippet limitado ao controle em edição. Consulte o recibo T06. |
| T07 | Dicas e orientação | Preparação funcional registrada; entrega coordenada pendente. |
| T08 | Projetos e exportação | Revalidação técnica registrada em `review/T08-REVALIDACAO-XEPHYR-20261016.json`; revisão visual e handoff preservando quatro arquivos pendentes. |
| T09 | Execução e recuperação | Journal, editor, crash/timeout, cancelamento e retomada explícita passaram na build privada atual; perda de display atual não foi repetida por limite do `/tmp`. Consulte os recibos T09. |
| T10 | Validação e entrega | Auditoria final iniciada; documentação ainda tem estados antigos, a GUI continua aberta e a validação completa não foi executada. Sem publicação nesta etapa. |

A tabela descreve a fila, não registra aprovação humana. A fotografia atual da
Fila Atual mostra T04, T01, T03, T05 e T07 aguardando revisão do usuário, T08
agora também aguardando sua revisão técnica/visual, e T10 como auditoria final
enfileirada. Ler a revisão salva antes de executar qualquer item. A decisão da
pessoa continua na prancheta.

## Compilação e retomada

Usar os comandos e dependências do [README](../tools/theme-lab/README.md).
O header de processos agora invalida os dois executáveis no Makefile. O alvo
`check-owned-processes` permite verificar encerramento sem iniciar interface.
A recompilação desta preparação gerou bytes iguais aos binários T09 já testados;
os hashes permitem reutilizar essas provas com o escopo original.

Na atualização privada, preservar `working.json`, `scene.json`,
`editor-journal.json` e `project-history.json` disponíveis. Saídas geradas
são regeneradas, não importadas. Manter a origem aberta; texto ainda sem
checkpoint não tem garantia de transferência. Conferir a liberação do canal
correto para o pedido e escopo atuais; autorização de outro contexto não vale.

## Limites do inventário

O probe não inicia GUI. Aqui detectou Motif2.3.8, GTK2 2.24.33, GTK3 3.24.49,
GTK4 4.18.6, Qt5 5.15.15 e Qt6 6.8.2. GTK1/GTK5 estão indisponíveis.
Kvantum e a galeria Qt Quick/KDE estão disponíveis, com adaptadores pendentes.
Disponibilidade da biblioteca não prova tradução da receita ou fidelidade.
Motif instalado não identifica a biblioteca histórica SR10.4. O Motif da
interface/referência é distinto de um adaptador de galeria externo.

Não colocar dados pessoais, journals, amostras ou backup aprovado num pacote
publicável. A release final exige inventário dos itens efetivamente entregues,
dependências portáveis, preservação de dados e avaliação com seus limites.

## Retomada da Fila Atual — 2026-10-16

T05 permanece parcial. A leitura nativa KColorScheme produziu papéis para
DomainOS, Breeze Light, Breeze Dark e amarelo de teste, com fallback por papel
para esquemas que omitem cores de Header. A prévia GTK3 foi verificada somente
com Irixium em sessão isolada; a pipeta guardou amostra como evidência e não a
converteu em papel. A suíte atual de backend passou (35 testes). A lacuna é
estrutural: `TLRecipe.palette` ainda é uma paleta da família inteira, não uma
receita de papéis por controle. Portanto T05 não está concluído nem aprovado.
Recibos e comparação: [resumo T05](review/T05-CORES-PIPETA-20261016.json),
[quatro esquemas](review/T05-QUATRO-ESQUEMAS-20261016.json),
[contraste](review/T05-CONTRASTE-20261016.json) e
[prévia GTK3](review/T05-GTK3-IRIXIUM-PREVIEW.png).

Conforme a nota autorizada de T05, o trabalho seguiu para T06 sem transformar
essa limitação em aceite. T06 está tecnicamente concluído: busca UTF-8 para
frente/trás com opções de correspondência, realce visível usando o papel
Selection da paleta da prévia, explicação do alias `_breeze` e emissão apenas do
controle em edição. Build estrito, teste unitário da busca, 35 testes do backend
e ensaio de interface em Xephyr passaram; o campo de busca também passou os
atalhos de edição exigidos. O launcher bwrap não foi usado nesta sessão de
ensaio, então sua barreira recusou gerar a prévia native; essa limitação não
alterou o perfil do desktop. A evidência técnica não marca avaliação humana.
Consulte [recibo T06](review/T06-CODIGO-BUSCA-20261016.json) e a
[captura do realce](review/T06-BUSCA-CODIGO-20261016.png). T05 continua parcial
por compartilhar a receita de cores por família, não por controle.
