# Publicar IrixClassic Kvantum 0.7.1 estável

A promoção está autorizada e registrada. **Não há novo aceite visual exigido.**
Esta etapa publica os arquivos já aceitos com a identidade estável; não é uma
nova rodada de construção do tema. Mantenedor público: `mrmmx31`.

## Antes da publicação

Faça merge da promoção no clone, revise o diff e os arquivos novos, faça commit
e envie essa branch ao `origin`. O publicador não cria commits nem envia branches.
Ele verifica que o commit remoto corresponde exatamente ao HEAD e que todos os
arquivos distribuídos estão nesse commit. A branch pode continuar se chamando
`#kvantum-classic-rc1`; **o nome da branch não determina o canal da release**.
O script não precisa da branch master e não publica a versão antiga de lá.

Use seu nick e o endereço noreply configurado no GitHub para commits públicos.
Não envie tokens, arquivos de credenciais, logs pessoais ou relatórios brutos.
A tag criada é leve (sem novo e-mail de tagger). Créditos legítimos de terceiros
permanecem nos arquivos e licenças.

Instale a GitHub CLI pela distribuição, caso não exista, e autentique-a na sua
máquina com `gh auth login`. Não compartilhe o token no chat ou no repositório.
Não use sudo para publicar.

## Publicação com um comando

Na raiz do checkout com o commit já enviado:

```sh
bash distribuicao/publicar-estavel.sh --verificar
bash distribuicao/publicar-estavel.sh --publicar \
    --saida "$HOME/Downloads/IrixClassic-0.7.1-publicacao"
```

A verificação é local, sem escrita ou rede. O comando com **--publicar**:

1. Confere promoção, manifesto, equivalência da arte/configuração, commit e origin.
2. Cria/envia somente `irixclassic-kvantum-v0.7.1`, sem mover tags existentes.
3. Cria uma release em rascunho, com título e notas explícitos.
4. Envia os dois ZIPs, SHA256SUMS e DISTRIBUICAO.json; baixa e compara os bytes.
5. Publica como release **normal, não prerelease**, e registra PUBLICACAO.json.

Há escrita externa a partir do passo 2. Um problema de upload deixa o rascunho
para repetir o mesmo comando. Assets de nomes iguais não são sobrescritos;
qualquer divergência exige revisão, não `--force` ou `--clobber`. A confirmação
final é a URL real e `published: true` no recibo. `signed: false` continua correto:
SHA-256 não é assinatura digital e a tag leve não é assinada.

A pasta de assets deve ser nova ou conter exatamente os mesmos arquivos. Se
alterar o código depois do commit, o publicador interrompe antes de publicar.
Uma release já publicada e idêntica é reconhecida por leitura; não é regravada.
Não há `git push --tags`, push de branch, exclusão de release ou force push.

## Pela interface do GitHub

A alternativa é criar a tag específica no commit revisado, enviá-la, gerar os
pacotes com `distribuicao/gerar-kvantum.sh`, abrir uma nova Release nessa tag,
colar `NOTAS-0.7.1.md` e anexar os quatro arquivos gerados. Deixe **Pre-release**
desmarcado. Não use o HEAD antigo de master como alvo e não apenas renomeie ZIPs RC.
O script automatiza e verifica esse mesmo objetivo, sem depender de CLI nesta conversa.

## Desenvolvimento depois da entrega

Preserve a tag e os assets da 0.7.1. Abra correções e melhorias a partir dessa base,
registre o problema/feedback e publique novos números de versão. Não há promessa
de perfeição visual universal; as limitações aceitas constam das notas públicas.
A 0.7.1 não promove o Irixium moderno nem a decoração externa para outra versão.

Documentação primária consultada para os comandos de publicação:
- https://cli.github.com/manual/gh_release_create
- https://cli.github.com/manual/gh_release_upload
- https://cli.github.com/manual/gh_release_download
- https://cli.github.com/manual/gh_release_edit
