#!/usr/bin/env python3
"""Testa a promessa do repositório: global/ sobrevive sem as pastas da empresa?

Recebe a raiz de uma cópia descartável de onde celesta-* já foi apagado, e
resolve cada link markdown relativo e cada @import dentro de global/. Uma
referência que não resolve é um lugar onde o método ficou preso ao contexto.

Procurar a string 'celesta-' não serve: acusa menção ilustrativa ("para a
Celesta, ver …"), que é documentação legítima, e não pega um link quebrado
para um arquivo que só mudou de pasta.
"""
import os
import re
import sys

LINK = re.compile(r'\]\((?!https?:|#|mailto:)([^)]+)\)')   # [texto](caminho)
IMPORT = re.compile(r'^@(\S+)', re.M)                       # @caminho


def broken_refs(root: str) -> list[str]:
    out = []
    base = os.path.join(root, 'global')
    for dirpath, _, files in os.walk(base):
        for fn in files:
            if not fn.endswith('.md'):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding='utf-8', errors='replace') as fh:
                text = fh.read()
            for target in LINK.findall(text) + IMPORT.findall(text):
                t = target.split('#')[0].strip()
                # Caminho absoluto ou de home é ambiente, não estrutura do repo.
                if not t or t.startswith('~') or os.path.isabs(t):
                    continue
                if not os.path.exists(os.path.join(dirpath, t)):
                    out.append(f'{os.path.relpath(path, root)} -> {t}')
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: portable-check.py <raiz-da-copia>', file=sys.stderr)
        return 2

    broken = broken_refs(sys.argv[1])
    if broken:
        for b in broken:
            print(f'\033[31m  {b}\033[0m')
        print(f'\n  {len(broken)} referência(s) quebrada(s): '
              'global/ ainda depende do que foi apagado.')
        return 1

    print('  \033[32mnenhuma — global/ é autossuficiente\033[0m')
    return 0


if __name__ == '__main__':
    sys.exit(main())
