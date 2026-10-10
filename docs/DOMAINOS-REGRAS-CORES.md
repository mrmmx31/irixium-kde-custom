# Regra de cores — todas as adaptações DomainOS

Regra reafirmada pelo usuário em 2026-10-10: **o desenho acompanha o esquema
de cores selecionado no KDE. Não corrigir controles com cores finais estáticas.**

Aplica-se a GTK1/2/3/4, Qt Widgets, Qt Quick, Kvantum, Plasma Style, decorações,
painel, menus, dicas e notificações. A existência desta regra não declara todas
essas implementações auditadas ou concluídas; a [fila visual](DOMAINOS-FILA-REVISAO-VISUAL.md)
registra o estado de cada família.

## Fonte e tradução

- Obter os papéis atuais de janela, botão, área de conteúdo, seleção e seus
  textos correspondentes. Registrar o mapeamento usado pela família ativa.
- Derivar face, texto, luz, sombra e trilho desses papéis. Parâmetros fixos de
  geometria ou cálculo de iluminação são permitidos; a cor final deve continuar
  dependendo da paleta atual. Não criar uma exceção para preto/branco.
- Aplicar a política a normal, pressionado, desabilitado, sem foco, selecionado
  e hover. Cada estado tem uma regra explícita; um ensaio normal não os valida.
- Ao trocar o esquema, usar a atualização própria do toolkit ou a ponte/script
  de paleta do projeto quando necessária. Não depender de caminhos pessoais.
- Se um papel não estiver disponível, usar a paleta válida do toolkit e registrar
  a limitação. Não encobrir a ausência com azul ou outra paleta histórica fixa.

Os RGB da VM e dos arquivos de evidência servem para comparação histórica.
Os arquivos `.colors` definem esquemas selecionáveis; não autorizam inserir
seus valores diretamente nos controles que devem seguir outro esquema.
Máscaras de geometria não devem impor uma paleta final ao desenho.

## Exceções autorizadas

Somente **LED de atividade** e **luz de seleção do Pager** podem manter uma cor
de sinal estável, com amarelo como referência de sinal aceso. Se o fundo tornar
essa indicação ambígua, a alternativa deve preservar contraste. A autorização
não se estende ao entorno, bordas, setas, texto ou fundo desses componentes.
Não alterar a luz do Pager durante a correção atual das barras de rolagem.

## Verificação e distribuição

Após mudar um consumidor, conferir cores efetivas e seus estados no esquema
DomainOS, em um neutro, em um escuro e em um amarelo. Reutilizar provas ainda
válidas; executar novamente somente o escopo alterado ou ainda sem evidência.
Não converter essa regra em uma declaração de que toda a suíte já passou.

Entrada do projeto: [índice de regras](DOMAINOS-INDICE-REGRAS.md).
Protocolo portável: [retro-ui-review](../skills/retro-ui-review/SKILL.md) e sua
[política de cores](../skills/retro-ui-review/references/color-policy.md).
O controle da VM preserva sua paleta nativa; esta regra é da adaptação KDE.
