# CLS-3865 — decisões

## Respostas de 2026-11-17 (coordenação, Lucas)

"Provisória" = decisão tomada para o plano seguir; pode mudar depois da reunião com o Francisco. No plano,
entra em Decisions como "Lucas Franco, 2026-11-17", com a frase "pending product owner confirmation" nas
provisórias. Nada disso vai para o Jira, e a spec do pai não é editada: mudança de AC é proposta depois.

| # | Pergunta | Decisão | Tipo |
|---|---|---|---|
| 1 | Gift registrado antes do release | **Sem regra especial** (Lucas, 2026-11-17): não há gift em produção, e contar duas vezes não é problema. Alinhado ao CLS-4938. O AC "Gift recorded before release" sai: propor a mudança ao Francisco | final |
| 2 | Status `offered` | Não existe no backend; o plano ignora | final |
| 3 | Editar para o mesmo valor (#16) | 200, sem evento `gift_value_edited` | final |
| 4 | "Created by" de gift de scenario (#22) | Mostra a origem (scenario), não "—" | final |
| 5 | Mais de 100 gifts (#29) | Gift checkout pagina, com o `limit`/`offset` que a lista já aceita (Francisco, 2026-11-17: "está previsto paginação") | final |
| 6 | Só `PS_GIFT_REQUEST_VALIDATE` (#55) | Não vê o Gift checkout; é intencional | final |
| 7 | Duas ações ao mesmo tempo (#32) | Padrão do gift: transação com trava de linha (`GiftService::changeStatus`, `findPlayerGiftForUpdate`, CLS-4434). Editar × editar: as duas passam em série, cada editor recebe de volta o valor que ele editou, e fica gravado o último (Lucas, 2026-11-17). Transição × qualquer ação: a segunda falha pela máquina de estados. Cada ação bem-sucedida grava o seu evento na activity. O AC "the second gets an error" e a CLS-4941 ("first change wins") ficam para ajuste com o PO | final |
| 8 | Página Gift checkout já feita pelo Dimitris na branch `CLS-3865` do backoffice-front (`87dc6f3c9`, 2026-11-16, PR #2307; não é a CLS-4545, como a matriz dizia) | **Adjustment não existe** (Lucas, 2026-11-17; o Francisco não reconhece). É diferente do Edit value: o Adjustment credita valor no saldo real do jogador (`POST /gift/{id}/adjustment`, permissão `ROLE_PLAYERS_ACTIONS_MAKE_ADJUSTMENT`); o Edit value muda o valor do gift (`EditGiftValueModal`, `PATCH /gift/{id}`). Sai da página, com o order reference e o delivery (8b). O contrato segue as rotas que o 4942 define, não as que a página chama (`POST /gift/{id}/complete`, `PATCH /gift/{id}`, `POST /gift/{id}/adjustment`, `GET /gifts/count`) | final |
| 8b | Order reference e dados de entrega | Fora: não existe conceito de encomenda no gift (Lucas, 2026-11-17). Saem da página do Dimitris o campo "Supplier order reference", o card Delivery (nome, morada, código postal, cidade, país, telefone) e o texto "marked as ordered" do Complete. Continua aberto só o Adjustment (item 8), com o Francisco | final |
| 9 | Statistics descarta o segundo evento do gift | O 4938 troca a chave de `event_promotion` (hoje `PRIMARY KEY (gift_id)`, `ON DUPLICATE KEY UPDATE` sem efeito), e a statistics sobe antes do Complete da promotion | final |
