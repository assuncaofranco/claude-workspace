# CLS-3540 — matriz de QA (cms #281, Rasoul)

Lucas como testador. Refactor para 100% de cobertura: o risco é regressão no que foi reescrito, não
feature nova. Critério de todas as A: mesma resposta que o master, exceto a 1a.

Classes: **A** afetada, testar · **N** não afetada / sem entrada · **E** só dá para ver fora da API.

| # | Variante | Código tocado | Classe | Como verificar |
|---|---|---|---|---|
| 1 | player lista blocos filtrando por nome de tag: vê ANY, USER sem segmento, USER com segmento dele; não vê USER com segmento alheio, COUNTRY, outra tag | `ContentBlockFilter` virou readonly com propriedades públicas; controller lê `->language`, `->visibility`, `->segments`, `->contentTagNames` | A | GW `/cms/content-blocks?contentTagNames[]=` |
| 2 | mesmo, filtrando por id de tag | `->contentTagIds` | A | GW `?contentTagIds[]=` |
| 3 | player lê no segundo idioma do domínio | `->language` + `GatewayTranslationMapper` sem os ramos mortos | A | GW `?language=<lang2>`, conteúdo de cada bloco no lang2 |
| 4 | visitante (token de aplicação): vê ANY e COUNTRY, não vê USER | `->visibility` pelo outro ramo do gateway | A | GW com token `client_credentials` |
| 5 | BO cria e edita bloco com conteúdo por idioma: todos os idiomas gravados | `GatewayTranslationMapper::mapFormsToData/mapDataToForms` | A | BO POST, PUT, GET por idioma |
| 6 | BO PUT troca o conjunto de tags `[T, T2]` → `[T]` | `ContentBlock` (tags) | A | BO GET depois do PUT |
| 7 | BO cria e edita rascunho de T&C: conteúdo de todo idioma do domínio | `TermsAndConditionsNormalizer::getLocales(int)` | A | BO POST/PUT draft (nunca publish em pp) |
| 1a | body com tipo errado em `content-blocks-api` → 400 `Invalid filter body.` (antes 500) | controller | A, DEV-ONLY | o gateway valida tipo antes (`ContentBlockVisibilityForm`), então não chega por entrada; coberto pelo teste do PR |
| 8 | job de activity do T&C (`UserActivityJobData::toArray`) | DTO readonly | E | activity do rascunho criado em 7 (BO ou banco) |
| 9 | `content_block/{id}/segment/{segmentId}` DELETE | só marcador de cobertura | N | |
| 10 | `removeContentTag` agora remove | só alcançável pelas fixtures (campo `contentTagIds` é `mapped: false`) | N | |
| 11 | `duplicate`, `__clone`, `setSegments`, `ContentBlockSegmentRepository`, `jsonSerialize` do T&C, `ContentBlockApiType` | apagados, sem chamador | N | |
| 12 | comando de expiração | só teste novo | N | |
| 13 | gate 100 no CI | `ci.yml` | N | job `tests` do PR |
