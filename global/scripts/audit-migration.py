#!/usr/bin/env python3
"""Compara o estado pré-git de ~/.claude com o repositório.

Existe por um motivo estreito: o git registra tudo a partir do primeiro commit,
mas as operações com perda aconteceram ANTES dele — extração de credencial,
remoção de entradas da allowlist, redação de achado de segurança, absorção dos
feedbacks em rules/. Esse intervalo não tem diff em lugar nenhum, e é exatamente
onde um equívoco se esconderia.

Uso:  audit-migration.py [<dir-pré-git>] [<repo>]

Não imprime conteúdo de arquivo — só caminho, situação e tamanho. O diretório
pré-git contém credencial viva; a saída daqui é versionada.
"""
import hashlib
import os
import sys

# Onde cada diretório do ~/.claude antigo foi parar no repositório.
MOVES = {
    'commands':                                        'global/skills',
    'shared':                                          'celesta-microservices/shared',
    'hooks':                                           'celesta-microservices/hooks',
    'postman':                                         'celesta-microservices/postman',
    'memory':                                          'global/memory',
    'projects/-Users-l-franco-Desktop-celesta-projects/memory': 'celesta-microservices/memory',
    'projects/-Users-l-franco-Desktop-infra/memory':   'celesta-infra/memory',
}

# Arquivos que deliberadamente não têm correspondente 1:1.
EXPLAINED = {
    'CLAUDE.md':          'dividido em global/CLAUDE.md + router.md + rules/ + overlay da Celesta',
    'RTK.md':             'global/RTK.md',
    'settings.json':      'celesta-microservices/settings/settings.json (26 entradas com credencial removidas)',
    'settings.local.json': 'celesta-microservices/settings/settings.local.json',
    'memory/celesta-infra.md': 'celesta-infra/memory/celesta-infra.md',
}

VAULTED = {
    'projects/-Users-l-franco-Desktop-celesta-projects/memory/project_game_nginx_body_capture.md':
        '~/.claude-secrets/celesta-prod-findings.md (ponteiro ficou no repo)',
    'projects/-Users-l-franco-Desktop-celesta-projects/memory/projects/celesta-cms-v2/preprod-1-test-admin.md':
        '~/.claude-secrets/celesta-cms-v2.md (ponteiro ficou no repo)',
    'commands/preprod-test.md':
        'credenciais -> ~/.claude-secrets/celesta-preprod.md; método reescrito genérico',
    'commands/ticket-postman.md':
        'credenciais -> ~/.claude-secrets/celesta-dev.md; referência Celesta -> postman-reference.md',
}

ABSORBED_PREFIX = 'projects/-Users-l-franco-Desktop-celesta-projects/memory/feedback_'
ABSORBED_ALSO = {'projects/-Users-l-franco-Desktop-celesta-projects/memory/preferences.md'}


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:12]


def classify(rel: str, old_root: str, repo: str):
    """-> (situação, destino, detalhe)"""
    if rel in VAULTED:
        return 'VAULT', VAULTED[rel], 'segredo fora da árvore do git'
    if rel.startswith(ABSORBED_PREFIX) or rel in ABSORBED_ALSO:
        return 'ABSORVIDO', 'global/rules/', 'reescrito por tema, original removido'
    if rel in EXPLAINED:
        return 'DIVIDIDO', EXPLAINED[rel], ''

    for src, dst in sorted(MOVES.items(), key=lambda kv: -len(kv[0])):
        if rel.startswith(src + '/'):
            new = os.path.join(dst, rel[len(src) + 1:])
            full = os.path.join(repo, new)
            if not os.path.exists(full):
                return 'SUMIU', new, 'não achado no repositório — investigar'
            if sha(os.path.join(old_root, rel)) == sha(full):
                return 'IDÊNTICO', new, ''
            o = os.path.getsize(os.path.join(old_root, rel))
            n = os.path.getsize(full)
            return 'MODIFICADO', new, f'{o} -> {n} bytes ({n - o:+d})'

    return 'NÃO MAPEADO', '', 'fora do escopo da migração (estado de runtime)'


def main() -> int:
    old = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.claude-pre-git-2026-09-22')
    repo = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()

    if not os.path.isdir(old):
        print(f'diretório pré-git não encontrado: {old}', file=sys.stderr)
        return 2

    rows = []
    for dirpath, _, files in os.walk(old):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, old)
            rows.append((rel,) + classify(rel, old, repo))

    order = ['SUMIU', 'MODIFICADO', 'VAULT', 'ABSORVIDO', 'DIVIDIDO', 'IDÊNTICO', 'NÃO MAPEADO']
    rows.sort(key=lambda r: (order.index(r[1]) if r[1] in order else 99, r[0]))

    counts = {}
    for _, status, _, _ in rows:
        counts[status] = counts.get(status, 0) + 1

    print(f'# Auditoria da migração\n')
    print(f'Origem: `{old}` ({len(rows)} arquivos)\n')
    print('| situação | n | significa |')
    print('|---|---|---|')
    meaning = {
        'IDÊNTICO': 'byte a byte igual — nada a conferir',
        'MODIFICADO': 'conteúdo mudou — **é aqui que um equívoco estaria**',
        'VAULT': 'saiu para ~/.claude-secrets, ponteiro ficou',
        'ABSORVIDO': 'conteúdo reescrito em rules/, original removido',
        'DIVIDIDO': 'virou mais de um arquivo',
        'SUMIU': 'sem correspondente — **investigar**',
        'NÃO MAPEADO': 'estado de runtime, nunca foi para o repositório',
    }
    for s in order:
        if s in counts:
            print(f'| {s} | {counts[s]} | {meaning[s]} |')

    for s in order:
        sel = [r for r in rows if r[1] == s]
        if not sel or s in ('IDÊNTICO', 'NÃO MAPEADO'):
            continue
        print(f'\n## {s}\n')
        for rel, _, dst, det in sel:
            print(f'- `{rel}`')
            if dst:
                print(f'  → `{dst}`' + (f' — {det}' if det else ''))
            elif det:
                print(f'  — {det}')

    n_id = counts.get('IDÊNTICO', 0)
    if n_id:
        print(f'\n## IDÊNTICO ({n_id})\n\nMovidos sem alteração. Para conferir:\n')
        print('```bash\npython3 global/scripts/audit-migration.py | grep MODIFICADO\n```')

    return 1 if counts.get('SUMIU') else 0


if __name__ == '__main__':
    sys.exit(main())
