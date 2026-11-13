# Plano de continuidade — IrixClassic Files

Manutenção: mrmmx31. Versão inicial de desenvolvimento: 0.1.0-alpha2.

| Marco | Entrega | Estado desta rodada |
|---|---|---|
| F1 | Reuso real de DolphinMainWindow/View/KIO; base Debian fixada | Build nativo e testes locais aprovados em 2026-10-07 |
| F2 | Identidade, bibliotecas, configuração, bookmarks e propriedades próprias | Implementado; teste nativo de isolamento incluído |
| F3 | Pathfinder, ancestrais, drop pocket, histórico e barra vertical | Implementado; fidelidade visual pendente |
| F4 | Shelf de referências locais por pasta | Implementado; persistência e remoção segura com testes incluídos |
| F5 | Content Viewer para texto/imagens locais, limites e cancelamento | Implementado; testes nativos incluídos |
| F6 | Distribuição binária privada e fonte correspondente | Gerador bloqueado até build/testes aprovados |
| F7 | Primeira prerelease para feedback | Aguardando compilação e primeira execução, sem formulário adicional |
| F8 | Refinamento da aparência e regressão completa de ações nativas | Depois da primeira execução da alpha |
| F9 | PDF, áudio/vídeo, documentos, Shelf avançada | Futuro; não bloqueia a alpha |
| F10 | Sons semânticos do IrixClassic Sounds | Futuro; nenhuma interceptação global nesta entrega |
| F11 | Promoção estável do aplicativo | Após feedback de uso; independente do Kvantum 0.7.1 |

Preservar o original: Kvantum, decorações, sons e Dolphin do sistema não são
alterados pelo kit. A lista de Locais e serviços padrão KDE continuam sendo
compartilhados quando usados explicitamente; a Shelf não é a lista de Locais.

Critério F7: C++ compilado, testes nativos aprovados, execução em paralelo ao
Dolphin e teste com dados artificiais. Não exigir identidade perfeita com todo o
IRIX. Também não publicar uma biblioteca privada não compilada como estável.

Fluxos de arquivo herdados precisam de regressão adicional: conflitos, erros,
cancelamento, desfazer, permissões, destinos remotos, associação de MIME e plugins.
A presença das ações nos menus não certifica esses fluxos ponta a ponta.
