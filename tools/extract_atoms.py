#!/usr/bin/env python3
# (content as generated previously)
import re, sys, json, argparse
from pathlib import Path

HEADER_RE = re.compile(r'^###\s((RQ|ALG|QAT)-\d+):\s(.+)$', re.MULTILINE)
ID_RE = re.compile(r'^ID:\s((RQ|ALG|QAT)-\d+)\s*$', re.MULTILINE)
TYPE_RE = re.compile(r'^Type:\s(.+)$', re.MULTILINE)
SCOPE_RE = re.compile(r'^Scope:\s([A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)+)\s*$', re.MULTILINE)
STATUS_RE = re.compile(r'^Status:\s(Proposed|Accepted|Deprecated)\s*$', re.MULTILINE)
DEPENDS_RE = re.compile(r'^DependsOn:\s\[(.*?)\]\s*$', re.MULTILINE)
RATIONAL_RE = re.compile(r'^Rationale:\s(.+)$', re.MULTILINE)

SECTION_RE = re.compile(r'^\*\*([A-Za-z]+)\*\*\s*$', re.MULTILINE)
SECTION_BLOCK_RE = re.compile(r'^\*\*{name}\*\*\s*$(.*?)(?=^\*\*[A-Za-z]+\*\*|\\Z)', re.MULTILINE | re.DOTALL)

def parse_dep_list(text: str):
    text = text.strip()
    if not text:
        return []
    items = [x.strip() for x in text.split(',') if x.strip()]
    return items

def parse_bullets(block: str):
    return [ln[2:].rstrip() for ln in block.splitlines() if ln.strip().startswith('- ')]

def parse_testvectors(block: str):
    m = re.search(r'```json\s*(.*?)\s*```', block, flags=re.DOTALL)
    if not m:
        raise ValueError("TestVectors must contain a fenced ```json block")
    js = m.group(1).strip()
    return json.loads(js)

def extract_sections(atom_text: str):
    sections = {}
    for name in ["Spec","Invariants","Acceptance","Metrics","TestVectors","Prompts"]:
        m = re.search(SECTION_BLOCK_RE.pattern.format(name=re.escape(name)), atom_text, flags=re.MULTILINE | re.DOTALL)
        if not m:
            raise ValueError(f"Missing section **{name}**")
        content = m.group(1).strip()
        if name == "TestVectors":
            sections[name] = parse_testvectors(content)
        elif name == "Prompts":
            prompts = {}
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("- "):
                    if ":" in line:
                        k, v = line[2:].split(":", 1)
                        prompts[k.strip()] = v.strip().strip('"')
            sections[name] = prompts
        else:
            sections[name] = parse_bullets(content)
    return sections

def parse_atoms(text: str):
    atoms = []
    headers = list(HEADER_RE.finditer(text))
    for i, m in enumerate(headers):
        start = m.start()
        end = headers[i+1].start() if i+1 < len(headers) else len(text)
        block = text[start:end]
        header_id = m.group(1)
        title = m.group(3).strip()

        def get(pattern, name):
            mm = pattern.search(block)
            if not mm:
                raise ValueError(f"[{header_id}] Missing field: {name}")
            return mm.group(1).strip()

        atom_id = get(ID_RE, "ID")
        if atom_id != header_id:
            raise ValueError(f"[{header_id}] ID line ({atom_id}) != header ID ({header_id})")

        atype = get(TYPE_RE, "Type")
        scope = get(SCOPE_RE, "Scope")
        status = get(STATUS_RE, "Status")
        depends = parse_dep_list(get(DEPENDS_RE, "DependsOn"))
        rationale = get(RATIONAL_RE, "Rationale")

        sections = extract_sections(block)

        atoms.append({
            "id": atom_id,
            "title": title,
            "type": atype,
            "scope": scope,
            "status": status,
            "depends_on": depends,
            "rationale": rationale,
            "spec": sections["Spec"],
            "invariants": sections["Invariants"],
            "acceptance": sections["Acceptance"],
            "metrics": sections["Metrics"],
            "testvectors": sections["TestVectors"],
            "prompts": sections["Prompts"]
        })
    return atoms

def validate_with_schema(objs, schema_path: Path):
    try:
        import jsonschema
    except ImportError:
        print("jsonschema not installed; skipping schema validation.", file=sys.stderr)
        return True
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok = True
    for obj in objs:
        try:
            jsonschema.validate(instance=obj, schema=schema)
        except Exception as e:
            print(f"Schema validation failed for {obj.get('id')}: {e}", file=sys.stderr)
            ok = False
    return ok

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_path", help="Path to spec.md")
    ap.add_argument("--out", default="tools/out/atoms.json", help="Where to write normalized atoms JSON")
    ap.add_argument("--schema", default=None, help="Path to JSON Schema for validation")
    args = ap.parse_args()

    text = Path(args.spec_path).read_text(encoding="utf-8")
    atoms = parse_atoms(text)

    if args.schema:
        ok = validate_with_schema(atoms, Path(args.schema))
        if not ok:
            print("ERROR: Schema validation failed.", file=sys.stderr)
            sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(atoms, indent=2), encoding="utf-8")
    print(f"Wrote {len(atoms)} atom(s) to {out_path}")

if __name__ == "__main__":
    main()
