---
description: Início e fim do turno de oncall — confere notificação, acesso e ferramentas item a item antes do primeiro alerta, e fecha o turno com handoff. Usar quando o usuário disser que está entrando ou saindo de oncall sem alerta colado; alerta vai para `oncall`.
argument-hint: [inicio|fim]
---

# oncall-shift

Alerta colado não é aqui: é `oncall`.

Tudo que é da empresa — canais, perfis, comandos de teste, escalonamento, incidentes conhecidos — está
**num arquivo só** do overlay (para a Celesta: `celesta-microservices/oncall-reference.md`). Ler ele uma
vez, no começo. Não abrir a policy original nem os arquivos de incidente: o índice basta até um alerta
casar com uma linha.

**Por quê:** a policy pede resposta em 15 minutos. Descobrir no primeiro alerta que o MFA, a VPN ou um
conector não funciona come esse tempo inteiro. Já aconteceu: o gap de acesso à conta da fila do
segment só apareceu no meio do alerta de 2026-08-29.

## Início

1. Ler o arquivo de referência do overlay.
2. Conectores que esta sessão não alcança (APM, plantão, chat, nuvem): listar todos **juntos, uma vez**.
   Autorizar é com ele, fora daqui.
3. Percorrer o checklist de início **um item por vez**: pedir, esperar o ok, seguir.
   - Item com comando somente-leitura: eu rodo e reporto só o resultado.
   - Item que exige humano (código de MFA, celular, VPN): eu peço, e confirmo com o comando do item
     quando houver um.
4. Item que falha não é pulado: vira pendência nomeada no estado do turno, com quem resolve.
5. Recap em uma linha por padrão do índice de incidentes que cai dentro da semana (data de calendário,
   fornecedor instável). Nada além.
6. Escrever `<memória do projeto>/oncall/shifts/<AAAA-MM-DD>.md` (data de início): janela do turno, itens
   ok, pendências.

## Durante

Cada alerta vai para `oncall`. Ao fechar um, acrescentar no estado do turno uma linha apontando o
arquivo do incidente.

Sessão nova durante o turno: ler o estado do turno antes, não refazer o checklist. Sessão de nuvem
expira; testar com o comando de identidade antes da primeira leitura, sem pedir licença.

## Fim

1. Checklist de fim, item a item.
2. Handoff para o canal de oncall, no formato de `rules/writing.md`: incidentes da semana em uma linha
   cada, o que segue aberto, gap de acesso não resolvido. Mostrar o texto; ele posta.
3. Fechar o estado do turno: resultado de cada pendência.
