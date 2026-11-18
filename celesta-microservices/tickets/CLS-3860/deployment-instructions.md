# CLS-3860 — instruções de deploy

Escritas no pai CLS-3597 (Deployment + Rollback instructions, junto com o contact #439 que o Socrates pôs lá)
e no PR #10. Manifesto: celesta-releases `releases/CLS-3597.yaml` (grupo 1 = bundle #10, grupo 2 = tag v1.7 +
repin do game).

## Por quê

- O bundle só carrega em dev e test no game (`config/bundles.php:34`, `require-dev`), então o merge não deploya nada.
- A ordem só importa para o CLS-4837: o game requer `dev-CLS-3860` até a aprovação; depois do merge do bundle,
  sem a tag v1.7 o repin para `^1.7` não resolve (tags vão até v1.6; sem workflow de release, tag manual).
- Estados intermediários: game com v1.6 e bundle mergeado = nada muda (game trava `^1.6`, que não pega 1.7? pega:
  `^1.6` aceita 1.7 — mas só no próximo `composer update`, que é dev-only). Inofensivo.
- Rollback: reverter #10 restaura `src/Promotion/`, código que nunca carregou; inofensivo em qualquer ordem.
- Sem migration, env, fila, flag.
