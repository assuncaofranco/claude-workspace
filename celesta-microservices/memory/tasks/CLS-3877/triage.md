---
name: cls3877-tnc-sign-503
description: "CLS-3877 sign T&C 503 em prod-2 — falha é no celesta-crm (validator), cms só devolve 404 correto; pendente decidir se cms deve barrar publish sem todos os idiomas"
metadata:
  node_type: memory
  type: project
  originSessionId: a033e278-e53c-47b4-80f8-2213940a769b
  modified: 2026-10-20T09:29:52.316Z
---

Expedite CLS-3877 (CSD-2694), aberto 2026-10-19, componente D-Team, assignee Francisco. Player 29, T&C 7, prod-2.

Fluxo: `POST crm /api/player/{id}/terms_and_conditions/sign` → `TermsAndConditionsSignedIdValidator` chama cms
`GET /api/{locale}/terms_and_conditions/last_published?domainId=` com o locale do request (`en`).
Cms filtra por `wat.locale` e devolve 404 quando nenhuma versão publicada tem conteúdo naquele idioma.
Crm, em domínio ANJ, converte o 404 em `Elastica\Exception\NotFoundException` (classe errada, não tratada) → 500 → gateway mascara como 503 `Unknown error`.
Em domínio sem ANJ o erro do cms é engolido e o sign passa.

**Por que importa:** o 503 é bug de tratamento do crm (time D); cms se comporta como foi escrito. A única pergunta que é nossa é de produto: cms deveria recusar publish de T&C sem conteúdo em todos os idiomas do domínio?

**Correção (2026-10-20):** o publish valida idioma sim, no manager (`isAllowedToBePublished`), mas só sobre as linhas que já existem. As linhas de tradução nascem no POST, uma por idioma de `domain.languages` naquele momento; o PUT só atualiza linhas existentes e nunca cria. Idioma adicionado ao domínio depois da criação nunca ganha linha, e o publish passa. Só um publicado por domínio (publish despublica os outros).

**Vídeo do Yannick (2026-10-20):** ele opera no BO (console.anj, domínio vibrez), edita a T&C 7 (abas fr/en), publica, e testa como player em beta.vibrez.fr (site em francês). O front do site mostra `status: 400` no corpo, mas com `code: SERVICE_UNAVAILABLE` + `Unknown error`, que é a assinatura do 503 do gateway, provavelmente reembrulhado pelo site. **O gateway não tem prefixo de locale nem setLocale, então chama o crm sempre em `en` (default do Symfony), qualquer que seja o idioma do site.** Toda T&C de domínio ANJ precisa ter `en`, senão ninguém aceita.

**Fix (2026-10-20):** sub-task CLS-3888, branch `CLS-3877-CLS-3888` no cms, não commitada. PUT cria a tradução do idioma que falta; publish confere contra `domain.languages`. Causa confirmada pelo vídeo: Yannick escreveu o `en` e clicou Publish sem Save. Testes 573 verdes, Newman em `sdd/_how_to_test/CLS-3888/` 0 falhas. Pendente: commit/PR, deploy, operador republicar com `en`, ticket do time C (crm 503, gateway sempre `en`), e BO front salvar antes de publicar.

**Como aplicar:** antes de corrigir, confirmar em prod se `en` está nos languages do domínio do player 29 e quais locales a T&C 7 tem. Se `en` está no domínio e não na T&C, é o buraco do PUT/publish do cms. Se `en` não está no domínio, o cms está certo e o problema é crm/locale do player. Achado lateral no `TermsAndConditionsRepository::getLastPublished`: `orderBy` duas vezes, a segunda sobrescreve, então ordena só por id e ignora `publishedAt`.
