# Método

Este arquivo não contém regra. Ele carrega o roteador, que decide o que ler.

@router.md
@rules/writing.md

`router.md` classifica o input e aponta o fluxo. `rules/writing.md` é a única regra sempre carregada,
porque vale em toda saída independente de contexto.

O resto de `rules/` entra sob demanda, pelo roteador. Cada regra existe **uma vez**, no seu arquivo,
com as exceções dela dentro — e mudar como eu trabalho passa por `rules/corpus.md` antes de qualquer
edição.

Contexto de projeto — serviços, containers, caminhos, credenciais — fica no overlay do projeto, nunca
aqui.
