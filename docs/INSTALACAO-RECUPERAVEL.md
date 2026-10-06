# Atualização recuperável do Irixium moderno

## Problema corrigido

Antes, o script copiava `aurorae/Irixium/`, substituía o menu e gravava seleção e
fontes antes de chamar o instalador de geometria. Remover a instalação do grupo
legado resolveu uma regressão direta, mas uma falha final ainda deixava `Irixiumrc`
novo com o grupo anterior. O fluxo atual prepara um plano único e seu backup
**antes da primeira escrita no destino**.

## Sequência

1. Validar diretórios, recursos SVG/PNG, módulo Aurorae e seu código conhecido,
   manifesto de `moderno/geometria/` e configuração local. Não executar shell de
   arquivos de configuração. Recusar links simbólicos ou dimensões personalizadas
   incompatíveis com o perfil de geometria.
2. Capturar conteúdo/permissões dos arquivos afetados. Gravar recibo privado com
   cópias e SHA-256 anteriores/posteriores e estado `prepared`.
3. Atualizar arquivos do tema do usuário, mesclando somente a geometria no
   `Irixiumrc` instalado. Outras personalizações de desenho substituídas pelo
   checkout ficam no backup. Arquivos extras na pasta não são apagados.
4. Autorizar o lote administrativo: **grupo novo de moderno/geometria**, menu do
   checkout e imagem PNG. Nenhuma cópia do grupo legado da raiz. O auxiliar valida
   os hashes novamente depois da autorização, escreve por arquivo temporário/
   rename e tenta desfazer o lote se alguma escrita falhar.
5. Somente quando solicitado, gravar seleção da decoração e/ou fontes. Verificar
   hashes e concluir o recibo. Reconfigurar o KWin somente depois disso.

Sem `--ativar` e `--aplicar-fontes`, `kwinrc` e `kdeglobals` não são escritos.
A Classic e o Kvantum são intocados. O fluxo Kvantum tem recibo e seleção separados.

## O que a recuperação garante — e o que não garante

Não existe transação única entre arquivos de sistema, pasta do usuário e
compositor. Uma falha comum provoca rollback das cópias conhecidas. SIGTERM e
interrupção de teclado são tratados; SIGKILL, falta de energia ou encerramento do
processo durante uma escrita podem deixar recuperação pendente. Nesse caso,
novas instalações são bloqueadas até a conclusão explícita.

O rollback de recursos de sistema pode solicitar autorização novamente. Se ela
for negada, o backup é mantido e o instalador informa `recovery_needed`; não
anuncia restauração concluída. `reconfigure` não é executado numa instalação que
falhou. Alterações vistas antes de um encerramento de sessão não são garantidas
como atomicamente invisíveis ao compositor.

```sh
bash restaurar-irixium.sh --verificar --recuperar
bash restaurar-irixium.sh --recuperar
```

A restauração compara **todos** os destinos antes de escrever. Aceita somente os
conteúdos anteriores ou posteriores registrados; não apaga atualizações do KDE
ou edições pessoais desconhecidas. Mantém os recibos mesmo após restaurar.
Restaura arquivos, não remove diretórios vazios eventualmente criados. Não tenta
reverter mudanças feitas por outros programas na sessão.

O bloqueio do atualizador de geometria é compartilhado para evitar duas escritas
cooperantes concorrentes. Ferramentas externas não usam esse bloqueio; por isso há
a segunda comparação de hashes antes de cada substituição.

## Migração e uso

O `update-irixium.sh` atual instala o pacote `irixium_modern` somente no perfil
do usuário. Ele não usa os recibos legados, não altera componentes compartilhados
do Aurorae e não elimina backups antigos.

A ativação agora é intencional:

```sh
bash update-irixium.sh          # instalar; preservar seleção
bash update-irixium.sh --ativar # selecionar irixium_modern
```

Não usar sudo na frente. Os únicos destinos são `~/.local/share`,
`~/.config/kwinrc` quando a ativação é explícita e o estado privado do usuário.
`--aplicar-fontes` não faz parte desse instalador.

Não execute o instalador antigo a partir de outro clone, pois ele ainda poderá
reaplicar configurações antigas. Preserve o clone revisado e teste primeiro com
`--verificar`. A sessão deve ser encerrada normalmente para recarregar QML.
