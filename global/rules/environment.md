# Ambiente e stack

Quando o problema não é o código. Carregado no passo 12 (lint e testes) e no oncall.

## Quebra de stack vai para o Lucas, nunca para um contorno

Serviço que não responde, cache velho, banco limpo, container fora de sincronia: **parar e contar**.
Não inventar contorno — limpar pool de cache, recarregar fixtures, recriar container, mexer em env —
para se desbloquear.

**Por quê:** ele é dono do ambiente e com frequência já sabe a causa, ou está no meio do conserto.
Contorno silencioso mascara o problema real, pode destruir estado de que outra sessão dele depende, e
produz teste verde pelo motivo errado. Dito explicitamente em 2026-08-27, depois que rodei um load de
fixtures sem a flag `--no-bundles` que o próprio projeto usa, quebrei a resolução de domínio no
Backoffice local, e ia limpar o Redis em vez de reportar — enquanto ele já estava reinstalando outros
dois serviços.

**Como aplicar:** dizer o que quebrou, o que eu fiz logo antes, e qual acho que é a causa. Então
esperar.

**Distinguir de defeito de código do ticket**, que eu devo investigar e corrigir eu mesmo. O sinal é
onde está o problema: no código que o ticket toca, ou na máquina.

**Antes de qualquer comando de setup** (fixtures, migrations, recriar container), olhar como o
`install.sh`/`Makefile` do próprio repositório o invoca, e usar as mesmas flags.

## `make init` depois de troca grande de branch

Depois de trocar de branch — sobretudo para uma com deriva grande do master — ou de qualquer mudança
grande de código, rodar `make init` no serviço afetado **antes** de confiar em resultado de teste.

**Por quê:** o container faz bind-mount do diretório, então mudança de código é vista na hora — mas o
cache de metadata do ORM e os bancos de dev e de teste **não** acompanham o checkout. Caso concreto:
depois de um checkout 111 commits à frente, a suíte produziu 19 erros espúrios
(`ReflectionException: Property ...::$updatedAt does not exist`) que não tinham nada a ver com o
código. A entidade genuinamente não tinha a propriedade; era cache e schema de teste velhos. `make
init` resolveu — 1522/1522 e 944/944 limpos depois.

**Como aplicar:** antes de reportar falha de teste como regressão real logo após troca de branch,
merge ou rebase, descartar cache velho rodando `make init`. Se não existir ou não resolver, é
problema de stack — sobe para a regra acima, não improvisa.

**Armadilha irmã:** rodar os testes migra **só** o banco de teste, nunca o de desenvolvimento.
Escrever migration nova e rodar a suíte deixa o schema de dev velho. Isso já produziu um repro
end-to-end que falhava em silêncio depois da correção — mensagem consumida, nenhum erro logado,
nenhuma linha criada — porque a coluna ainda era `NOT NULL` no banco de dev, e a violação era lançada
dentro do handler sem linha de log visível. Depois de adicionar ou editar migration, migrar o banco de
dev explicitamente antes de qualquer verificação manual por ele.
