#!/usr/bin/env python3
"""Diff estruturado de dois OpenAPI: o que mudou por operação, campo a campo.
   openapi-diff.py <master.json> <branch.json>
Saída em texto: uma seção por operação criada (+), removida (-) ou alterada (~), com os campos do
request e de cada resposta achatados (a.b[].c: tipo) e marcados + novo, - removido, ~ alterado.
Só o que mudou; $ref resolvido, allOf/oneOf juntados, recursão cortada."""
import json, sys

METHODS = {"get", "put", "post", "delete", "patch", "head", "options"}


def load(p):
    with open(p) as f:
        return json.load(f)


def make_flat(doc):
    def resolve(s):
        while isinstance(s, dict) and "$ref" in s:
            node = doc
            for part in s["$ref"].lstrip("#/").split("/"):
                node = node.get(part.replace("~1", "/").replace("~0", "~"), {})
            s = node
        return s if isinstance(s, dict) else {}

    def desc(s, req):
        t = s.get("type", "object" if "properties" in s else "?")
        if isinstance(t, list):
            nullable = "null" in t
            t = "|".join(x for x in t if x != "null") or "null"
        else:
            nullable = bool(s.get("nullable"))
        if nullable:
            t += "|null"
        if "enum" in s:
            t += " enum(" + ",".join(map(str, s["enum"])) + ")"
        if s.get("format"):
            t += f" <{s['format']}>"
        return t + ("" if req else " (optional)")

    def flat(s, prefix="", req=True, out=None, depth=0, seen=()):
        out = {} if out is None else out
        raw_ref = s.get("$ref") if isinstance(s, dict) else None
        s = resolve(s)
        if depth > 8 or (raw_ref and raw_ref in seen):
            out[prefix or "(root)"] = "…recursivo"
            return out
        seen = seen + ((raw_ref,) if raw_ref else ())
        for key in ("allOf", "oneOf", "anyOf"):
            for sub in s.get(key, []):
                flat(sub, prefix, req, out, depth + 1, seen)
        if s.get("type") == "array" or "items" in s:
            flat(s.get("items", {}), prefix + "[]", req, out, depth + 1, seen)
            if not prefix:
                out.setdefault("(root)", "array")
            return out
        props = s.get("properties")
        if props:
            required = set(s.get("required", []))
            for name, sub in props.items():
                p = f"{prefix}.{name}" if prefix else name
                rs = resolve(sub)
                if rs.get("properties") or rs.get("items") or any(k in rs for k in ("allOf", "oneOf", "anyOf")):
                    flat(sub, p, name in required, out, depth + 1, seen)
                else:
                    out[p] = desc(rs, name in required)
        elif prefix:
            out[prefix] = desc(s, req)
        return out

    return flat, resolve


def body_fields(flat, resolve, node):
    node = resolve(node or {})
    out = {}
    for mime, mt in (node.get("content") or {}).items():
        for k, v in flat(mt.get("schema", {})).items():
            out[f"[{mime}] {k}"] = v
    return out


def params(resolve, op, path_item):
    out = {}
    for p in (path_item.get("parameters", []) + op.get("parameters", [])):
        p = resolve(p)
        sch = resolve(p.get("schema", {}))
        out[f"{p.get('in')}:{p.get('name')}"] = f"{sch.get('type', '?')}" + ("" if p.get("required") else " (optional)")
    return out


def facets(doc):
    flat, resolve = make_flat(doc)
    ops = {}
    for path, item in doc.get("paths", {}).items():
        for m, op in item.items():
            if m not in METHODS:
                continue
            f = {"params": params(resolve, op, item), "request": body_fields(flat, resolve, op.get("requestBody"))}
            for code, r in (op.get("responses") or {}).items():
                r = resolve(r)
                f[f"response {code}"] = body_fields(flat, resolve, r)
                f[f"response {code} text"] = {"description": r.get("description", "")}
            ops[f"{m.upper()} {path}"] = f
    return ops


def show(title, a, b):
    lines = []
    for k in sorted(set(a) | set(b)):
        if k not in a:
            lines.append(f"    + {k}: {b[k]}")
        elif k not in b:
            lines.append(f"    - {k}: {a[k]}")
        elif a[k] != b[k]:
            lines.append(f"    ~ {k}: {a[k]}  →  {b[k]}")
    if lines:
        print(f"  {title}")
        print("\n".join(lines))
    return bool(lines)


def main():
    old, new = facets(load(sys.argv[1])), facets(load(sys.argv[2]))
    for key in sorted(set(old) | set(new)):
        if key not in old:
            kind = "CRIADO"
        elif key not in new:
            kind = "REMOVIDO"
        elif old[key] != new[key]:
            kind = "ALTERADO"
        else:
            continue
        print(f"{kind} {key}")
        a, b = old.get(key, {}), new.get(key, {})
        for facet in sorted(set(a) | set(b), key=lambda x: (x != "params", x != "request", x)):
            show(facet, a.get(facet, {}), b.get(facet, {}))
        print()


main()
