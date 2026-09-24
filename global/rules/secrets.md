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
