#!/usr/bin/env python3
import json, argparse, sys

def grade_atom(atom: dict) -> dict:
    reasons = []
    # Acceptance should have a Given/When/Then example
    acc_ok = False
    for line in atom.get("acceptance", []):
        lw = line.lower()
        if all(k in lw for k in ("given", "when", "then")):
            acc_ok = True
            break
    if not acc_ok:
        reasons.append("Acceptance lacks a concrete Given/When/Then example")
    # TestVectors must exist
    tv = atom.get("testvectors")
    if not tv or (isinstance(tv, list) and len(tv) == 0):
        reasons.append("Missing or empty TestVectors")
    # Invariants must exist
    if not atom.get("invariants"):
        reasons.append("Missing Invariants")
    # Prompts must include keys
    p = atom.get("prompts", {})
    if not isinstance(p, dict) or "GEN-CODE" not in p or "GEN-TESTS" not in p:
        reasons.append("Prompts must include GEN-CODE and GEN-TESTS")
    return {"id": atom.get("id"), "pass": len(reasons)==0, "reasons": reasons}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", required=True)
    args = ap.parse_args()
    atoms = json.loads(open(args.atoms, "r", encoding="utf-8").read())
    fails = 0
    for atom in atoms:
        res = grade_atom(atom)
        print(f"[{'PASS' if res['pass'] else 'FAIL'}] {res['id']}")
        for r in res["reasons"]:
            print(f"  - {r}")
        if not res["pass"]:
            fails += 1
    if fails:
        print(f"Grader: {fails} atom(s) failed")
        sys.exit(1)
    print(f"Grader: All {len(atoms)} atom(s) passed")
    sys.exit(0)

if __name__ == "__main__":
    main()
