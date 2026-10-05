# Validação — geometria do Irixium moderno 1.0.0-rc1

## Executado

- **38 testes Python:** alteração restrita à seção Layout, preservação de cores e
  demais chaves, CRLF, idempotência, recusa de dimensões personalizadas/duplicadas,
  instalação e restauração exatas, migração do QML original/v1/v2, código desconhecido,
  cancelamento administrativo, falha simulada de escrita, recibo interrompido,
  backup corrompido, edições posteriores, atualização do KDE, links simbólicos e
  preparação da integração local sem escrever ou modificar ações existentes.
- **21 testes JavaScript**, com **126 cenários geométricos parametrizados**: funções
  de geometria extraídas literalmente do QML novo, folgas iguais, alturas, grupos
  espelhados, cortes nos cantos e limites de janelas pequenas. A criação dos controles
  foi exercitada com objetos simulados, incluindo Help oculto, maximizador sem
  `buttonType`, espaçador, item desabilitado e destruição adiada.
- Compilação sintática dos arquivos Python; sintaxe dos wrappers shell; consistência
  do perfil de referência com a transformação aplicada pelo instalador.
- Integração CLI completa em um checkout Git temporário: verificação sem escrita,
  aplicação, repetição idempotente, sintaxe do instalador integrado e validação
  do manifesto da cópia integrada. Nenhum commit ou push foi executado.

As cópias administrativas foram simuladas em diretórios temporários. Nenhum arquivo
do KDE de um usuário foi escrito pelos testes. A execução de instalação privilegiada
real não está abrangida. O manifesto registra hashes, não uma assinatura de origem.

## Não executado

Não houve runtime Qt 6/KWin disponível neste ambiente. Os testes QML em `tests/qml/`
foram incluídos para execução local, **não contabilizados como aprovados**. Esse
harness usa o componente QML real, mas substitui os objetos KDE por simuladores;
mesmo quando passar, não certificará a renderização dos SVGs pelo KSvg nem eventos
de uma sessão KWin real.

Não foi produzida uma captura real do tema atualizado. Os cálculos referem-se ao
perfil padrão 22×22 e fator de botão 1. Efeitos, fontes e cores não foram redesenhados.

## Aceitação local

1. Mantenha a escala em 100%, instale com backup, encerre e entre novamente na sessão.
   Se estiver selecionada, a IRIX Classic deve continuar funcionando sem alteração.
2. Selecione Irixium moderno. Confira janela normal e maximizada, ativa e inativa.
   As divisórias devem ter a mesma altura útil e o título não deve encostar nelas.
3. Compare a distância do relevo à área que acende no hover, não apenas a largura do
   símbolo. O contorno do hover deve continuar tendo 22×22 no perfil padrão.
4. Confira menu, minimizar, maximizar/restaurar, fechar e qualquer ordem já escolhida.
   O pacote não pode trocar a função de um botão nem redefinir duplo clique.
5. Experimente uma janela com Help oculto, uma operação desabilitada e uma janela
   redimensionada. Não deve haver divisórias de itens invisíveis ou duplicadas.
6. Alterne para outra decoração Aurorae e volte. O perfil novo só deve atuar em
   Irixium. Valide a restauração antes de publicar como revisão aprovada.

Qualquer diferença no comportamento dos botões deve ser investigada sem alterar os
SVGs ou transportar a política de interação da IRIX Classic para o moderno.
