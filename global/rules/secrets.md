# Credencial

Nunca entra num repositório. Carregado quando algo que autentica alguém aparece no caminho.

## A regra

Credencial vive em `~/.claude-secrets/` (`chmod 700`), **fora da árvore do git**. Não numa pasta
ignorada: fora.

**Por quê:** pasta ignorada ainda vaza por `git add -f`, por clone com `.gitignore` de uma versão
anterior, por rename, por merge mal resolvido. Fora do repositório, nenhum desses erros alcança. E a
assimetria é brutal: entrar no histórico é um comando, sair é reescrever o histórico — que numa pilha
de branches com PR aberto significa force-push.

Uma skill **referencia o caminho**, nunca o valor. O valor entra na variável de ambiente de quem
executa, em tempo de execução, e não é escrito de volta em disco.

## 1Password, em transição

Desde 2026-11-02 o destino é o 1Password; `~/.claude-secrets/` continua valendo até a migração ser
conferida, e aí sai. Durante a transição, o que já está no 1Password é lido de lá.

- O que fica em disco é a **referência** `op://cofre/item/campo`, nunca o valor.
- Execução com `op run` (ou `op inject` para um arquivo temporário que o processo consome): o valor
  vai direto para o processo e não passa por mim.
- **`op read` e `op item get` com valor, nunca.** Imprimem o segredo, que fica no transcript.
- Só referencio itens marcados com a tag combinada. Cofre de produção, nunca.

**Por quê:** a sessão do CLI destrava com Touch ID e libera **todos** os cofres do usuário, inclusive
os de produção. Criar um cofre dedicado exige admin da conta (403 em 2026-11-02). Então o limite é
por regra, não por técnica; a restrição técnica só viria de uma service account com um cofre só, o
que fica para quando algo precisar rodar sem o Lucas presente.

Cofre, tag e conta estão no overlay do projeto.

## O que conta como credencial

A fronteira é **"isto autentica alguém?"**, não "isto é interno".

Contam: senha, client secret, token, chave de API, chave privada, chave de assinatura entre serviços,
URL pré-assinada, token de sessão que não expira.

Não contam, e são versionados por decisão: id de conta de nuvem, hostname interno, nome de cluster ou
namespace, e-mail de colega, link de canal. Um scanner que barra esses dispara em todo commit — e
scanner que sempre dispara vira `--no-verify`, o que o torna pior que não ter.

## Antes de publicar qualquer coisa

`chmod 600` **não sobrevive a um `git push`**. Se a única proteção de um arquivo é a permissão dele,
ele não está protegido — está adiado. Dois arquivos de skill viveram meses assim.

Coleção de API versionada carrega o **nome** da variável com valor vazio, nunca o valor.

## Achado de segurança em produção

Análise de falha ainda aberta — a rota sem autenticação, a ausência de expiração, a query que encontra
o segredo no log — **não vai para repositório nenhum**, nem privado. Reunir a cadeia num arquivo é
escrever o roteiro de exploração.

No repositório fica o que o trabalho precisa acionar: que existe, o que bloqueia, quem é dono, e a
ordem das ações. A análise fica no vault enquanto a falha estiver aberta.

## Mover não desfaz

Extrair um segredo para o vault **para de espalhá-lo**; não desfaz a exposição de quem já o leu ou de
onde ele já esteve. Um valor que passou meses em arquivo de texto precisa ser **rotacionado**, e dizer
isso é parte do trabalho — não uma ressalva opcional no fim.
