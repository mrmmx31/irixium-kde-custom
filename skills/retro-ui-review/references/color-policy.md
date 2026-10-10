# Cores dinâmicas em adaptações temáticas

Antes de desenhar, identifique a fonte atual da paleta e registre o mapeamento
dos papéis de cor. Quando o projeto deve acompanhar um esquema selecionável,
não substitua esses papéis por cores finais literais do screenshot histórico.

1. Derive face, texto, luz, sombra, trilho e seleção da paleta atual. Valores
   fixos de geometria e fatores de iluminação são permitidos; o RGB final
   deve variar com seu papel de origem. Preto/branco não são exceções gerais.
2. Registre também pressionado, desabilitado, sem foco, selecionado e hover.
   Comparar apenas normal não comprova a harmonia dos demais estados.
3. Preserve atualização ao trocar o esquema, pelo toolkit ou por uma ponte
   necessária à integração. Não resolver uma fonte ausente com azul fixo.
4. Mantenha RGB históricos em evidências. Arquivos que definem esquemas e
   amostras de referência não autorizam fixar esses RGB nos consumidores.
5. Documente somente as exceções explicitamente autorizadas. Confira contraste;
   não ampliar uma exceção de sinal para seus textos, bordas ou fundo.
6. Após uma alteração, confira o consumidor e estados afetados em paletas de
   contraste distintas. Reuse provas válidas; não repita a suíte inteira.

## Perfil do projeto DomainOS

Na adaptação KDE de Domain/OS SR10.4 / HP VUE 2.01, todas as famílias GTK,
Qt, Kvantum, Plasma, decorações, painel, menus, dicas e notificações devem
acompanhar os papéis atuais do KDE. A reprodução histórica preserva geometria
e iluminação; não prende o usuário à cor azul da VM.

As únicas cores de sinal estáveis autorizadas são **LED de atividade** e
**luz de seleção do Pager**, com amarelo como referência ao acender e alternativa
quando o fundo prejudicar contraste. A luz do Pager não deve ser modificada
durante a revisão atual de rolagem.

Esse perfil aplica-se ao projeto correspondente. Em outro projeto, consulte
suas instruções; não imponha KDE, esta versão histórica ou essas exceções.
A documentação da regra não comprova que todas as implementações já a seguem.
