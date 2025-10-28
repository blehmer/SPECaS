#!/usr/bin/env python3
# (content abbreviated in this comment to save space)
import re, sys, json
from typing import List, Tuple
from pathlib import Path

HEADER_RE = re.compile(r'^###\s(RQ-\d+):\s(.+)$', re.MULTILINE)
ID_RE = re.compile(r'^ID:\s(RQ-\d+)\s*$', re.MULTILINE)
TYPE_RE = re.compile(r'^Type:\s(Functional|Nonfunctional\s\((?:Security|Privacy|Performance|Reliability|Cost|Operability|Compliance|Other)\))\s*$', re.MULTILINE)
SCOPE_RE = re.compile(r'^Scope:\s([A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)+)\s*$', re.MULTILINE)
STATUS_RE = re.compile(r'^Status:\s(Proposed|Accepted|Deprecated)\s*$', re.MULTILINE)
DEPENDS_RE = re.compile(r'^DependsOn:\s\[(.*?)\]\s*$', re.MULTILINE)
RATIONAL_RE = re.compile(r'^Rationale:\s(.+)$', re.MULTILINE)
SECTION_RE = re.compile(r'^\*\*([A-Za-z]+)\*\*\s*$', re.MULTILINE)
PROMPT_LINE_RE = re.compile(r'^\-\s(GEN-CODE|GEN-TESTS):\s".+?"\s*$', re.MULTILINE)
VALID_SECTION_ORDER = ["Spec", "Invariants", "Acceptance", "Metrics", "TestVectors", "Prompts"]

def parse_atom_blocks(text: str) -> List[Tuple[str, int, int]]:
    blocks = []
    headers = list(HEADER_RE.finditer(text))
    for i, m in enumerate(headers):
        start = m.start()
        end = headers[i+1].start() if i+1 < len(headers) else len(text)
        blocks.append((m.group(1), start, end))
    return blocks

def extract_field(pattern: re.Pattern, block: str, name: str, required=True):
    m = pattern.search(block)
    if not m:
        if required:
            raise ValueError(f"Missing field: {name}")
        return None
    return m.group(1) if m.lastindex else m.group(0)

def list_from_depends(text: str):
    text = text.strip()
    if not text:
        return []
    items = [x.strip() for x in text.split(',') if x.strip()]
    for it in items:
        if not re.match(r'^(RQ|ALG|QAT)-\d+$', it):
            raise ValueError(f"Bad DependsOn item: {it}")
    return items

def find_section_order(block: str):
    return [m.group(1) for m in SECTION_RE.finditer(block)]

def check_sections(block: str):
    # Ensure each required section exists and has proper content
    for sect in VALID_SECTION_ORDER:
        if f"**{sect}**" not in block:
            raise ValueError(f"Missing section **{sect}**")
    # TestVectors fenced block
    tv_match = re.search(r'\*\*TestVectors\*\*.*?```json\s*(.*?)\s*```', block, re.DOTALL)
    if not tv_match:
        raise ValueError("TestVectors must contain a fenced ```json block")
    js = tv_match.group(1)
    try:
        parsed = json.loads(js)
        if not isinstance(parsed, (list, dict)):
            raise ValueError("TestVectors JSON must be object or array")
    except Exception as e:
        raise ValueError(f"Invalid JSON in TestVectors: {e}")
    # Prompts include keys
    if "GEN-CODE:" not in block or "GEN-TESTS:" not in block:
        raise ValueError("Prompts must include GEN-CODE and GEN-TESTS")

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/lint_spec.py spec.md")
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")

    errors = []
    seen_ids = set()
    all_ids = set(m.group(1) for m in HEADER_RE.finditer(text))

    for atom_id, start, end in parse_atom_blocks(text):
        block = text[start:end]
        try:
            header_id = atom_id
            field_id = extract_field(ID_RE, block, "ID")
            if field_id != header_id:
                raise ValueError(f"ID line ({field_id}) != header ID ({header_id})")
            _type = extract_field(TYPE_RE, block, "Type")
            scope = extract_field(SCOPE_RE, block, "Scope")
            status = extract_field(STATUS_RE, block, "Status")
            deps_raw = extract_field(DEPENDS_RE, block, "DependsOn")
            deps = list_from_depends(deps_raw)
            rat = extract_field(RATIONAL_RE, block, "Rationale")
            # Section order
            sect_order = find_section_order(block)
            if sect_order != VALID_SECTION_ORDER:
                raise ValueError(f"Section order invalid. Expected {VALID_SECTION_ORDER}, got {sect_order}")
            check_sections(block)
            # Duplicates
            if header_id in seen_ids:
                raise ValueError(f"Duplicate atom ID: {header_id}")
            seen_ids.add(header_id)
            # Resolve deps
            for d in deps:
                if d not in all_ids:
                    raise ValueError(f"Unresolved DependsOn: {d}")
        except Exception as e:
            errors.append(f"[{atom_id}] {e}")

    if errors:
        print("Spec lint failed:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"OK — {len(seen_ids)} atom(s) validated")

if __name__ == "__main__":
    main()
