"""Curriculum pack linter: regexes compile, ids resolve, demo answers are self-consistent,
emoji keys exist as frontend assets, every topic has a theme, every concept a mastery
criterion, every question >=2 transfer questions (the 2nd is used after re-teaching).
Run: uv run python scripts/check_curriculum.py"""
import re, sys, yaml
from pathlib import Path
D = str(Path(__file__).resolve().parent.parent / "curriculum" / "data") + "/"
FILES = sorted(p.name for p in Path(D).glob("*.yaml"))
EMOJI = {p.stem for p in (Path(__file__).resolve().parents[2] / "frontend" / "public" / "assets" / "emoji").glob("*.png")}
TYPES = {"FACTUAL_ERROR","CAUSAL_ERROR","CONCEPT_CONFUSION","MISSING_STEP","OVERGENERALIZATION","VOCABULARY_CONFUSION"}
STRATS = {"DIRECT_HINT","SOCRATIC_QUESTION","ANALOGY","COUNTEREXAMPLE","SIMPLER_EXPLANATION","PREREQUISITE_REVIEW","VISUAL_EXPLANATION","TRANSFER_EXAMPLE"}

def _strings_only(x, path, E):
    """Plain YAML scalars containing ': ' silently become dicts — catch that."""
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ("messages", "confirm", "key_ideas", "hints", "patterns", "resolution_patterns", "answer_patterns", "prerequisites") and isinstance(v, list):
                for i, m in enumerate(v):
                    if not isinstance(m, str):
                        E(f"{path}.{k}[{i}]: expected a string, got {type(m).__name__} (quote it — it probably contains ': ')")
            _strings_only(v, f"{path}.{k}", E)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            _strings_only(v, f"{path}[{i}]", E)


def check(fn):
    errs, warns = [], []
    d = yaml.safe_load(open(D + fn))
    E = errs.append
    _strings_only(d, fn, E)
    def comp(pats, where):
        out = []
        if not isinstance(pats, list) or not pats:
            E(f"{where}: patterns missing/empty"); return out
        for p in pats:
            if not isinstance(p, str): E(f"{where}: non-string pattern {p!r}"); continue
            try: out.append(re.compile(p, re.I))
            except re.error as e: E(f"{where}: bad regex {p!r}: {e}")
        return out
    def hit(rx, text): return any(r.search(text.lower()) for r in rx)
    def emoji(v, where):
        if v not in EMOJI: E(f"{where}: emoji {v!r} not in allowed key list")
    for k in ["topic_id","name","emoji","color","theme","concepts","misconceptions","questions"]:
        if k not in d: E(f"top-level missing {k}")
    for k in ("theme", "syllabus_ref", "level"):
        if k in d and not (isinstance(d[k], str) and d[k].strip()): E(f"top-level {k}: expected a non-empty string")
    emoji(d.get("emoji"), "topic")
    cids = [c["id"] for c in d["concepts"]]
    if len(set(cids)) != len(cids): E("duplicate concept ids")
    pos = set()
    for c in d["concepts"]:
        emoji(c.get("emoji"), f"concept {c['id']}")
        mc = c.get("mastery_criterion")
        if not (isinstance(mc, str) and mc.strip()): E(f"concept {c['id']}: missing mastery_criterion (or not a string — quote it if it contains ': ')")
        for p in c.get("prerequisites", []):
            if p not in cids: E(f"concept {c['id']}: unknown prereq {p}")
        x, y = c["position"]["x"], c["position"]["y"]
        if not (-2 <= x <= 2 and 0 <= y <= 5): E(f"concept {c['id']}: position out of range")
        if (x, y) in pos: E(f"concept {c['id']}: overlapping position {(x,y)}")
        pos.add((x, y))
    # cycle check
    g = {c["id"]: c.get("prerequisites", []) for c in d["concepts"]}
    state = {}
    def dfs(n, stack):
        if state.get(n) == 1: E(f"prereq cycle: {' -> '.join(stack+[n])}"); return
        if state.get(n) == 2: return
        state[n] = 1
        for m in g.get(n, []): dfs(m, stack + [n])
        state[n] = 2
    for n in g: dfs(n, [])
    M = {}
    for m in d["misconceptions"]:
        w = f"misconception {m['id']}"
        for k in ["label","statement","corrective_target","nudge","confirm"]:
            if not m.get(k): E(f"{w}: missing {k}")
        if m.get("concept") not in cids: E(f"{w}: bad concept {m.get('concept')}")
        if m.get("type") not in TYPES: E(f"{w}: bad type {m.get('type')}")
        t = m.get("teaching", {})
        if len(t) < 2: E(f"{w}: <2 teaching strategies")
        for s, blk in t.items():
            if s not in STRATS: E(f"{w}: bad strategy {s}")
            if not blk.get("messages"): E(f"{w}.{s}: no messages")
        M[m["id"]] = (comp(m.get("patterns"), w+".patterns"), comp(m.get("resolution_patterns"), w+".resolution_patterns"))
    if not 3 <= len(M) <= 6: E(f"misconception count {len(M)} not in 3..6")
    all_mis_rx = [r for p, _ in M.values() for r in p]
    ids = [q["id"] for q in d["questions"]] + [t["id"] for q in d["questions"] for t in q.get("transfer_questions", [])]
    for dup in sorted({i for i in ids if ids.count(i) > 1}): E(f"duplicate question/transfer id {dup}")
    for q in d["questions"]:
        w = f"question {q['id']}"
        emoji(q.get("emoji"), w)
        if not q.get("answer_praise"): E(f"{w}: missing answer_praise")
        elif not q["answer_praise"].startswith("You"): E(f"{w}: answer_praise must start with 'You'")
        if q.get("concept") not in cids: E(f"{w}: bad concept")
        for rc in q.get("related_concepts", []):
            if rc not in cids: E(f"{w}: bad related_concept {rc}")
        ap = comp(q.get("answer_patterns"), w+".answer_patterns")
        pts = {p["id"]: comp(p.get("patterns"), f"{w}.{p['id']}") for p in q["expected_reasoning"]}
        for rp in q["required_points"]:
            if rp not in pts: E(f"{w}: required point {rp} not in expected_reasoning")
        da = q["demo_answers"]
        mis = q.get("misconceptions", [])
        for mid in mis:
            if mid not in M: E(f"{w}: unknown misconception {mid}")
        mis = [m for m in mis if m in M]
        if mis:
            hits = [m for m in mis if hit(M[m][0], da["misconception"])]
            if not hits: E(f"{w}: demo misconception matches none of {mis}")
            elif not any(hit(M[m][1], da["dialogue"]) for m in hits):
                E(f"{w}: demo dialogue matches no resolution pattern of {hits}")
            if hit(ap, da["misconception"]): warns.append(f"{w}: demo misconception also matches answer_patterns (check realism)")
            for m in mis:
                if hit(M[m][0], da["correct"]): E(f"{w}: demo correct matches misconception {m}")
            # mirror harness/verifier.py: text inside a misconception match never earns a reasoning point,
            # so the misconception demo must not hit any reasoning point outside those spans.
            txt = da["misconception"].lower()
            blocked = [mt.span() for m in mis for r in M[m][0] for mt in r.finditer(txt)]
            for pid, rx in pts.items():
                if any(all(e <= bs or s0 >= be for bs, be in blocked) for r in rx for s0, e in (mt.span() for mt in r.finditer(txt))):
                    E(f"{w}: demo misconception earns reasoning point {pid} (would be praised)")
        if hit(all_mis_rx, da["correct"]): warns.append(f"{w}: demo correct matches some (unlisted) misconception pattern")
        for rp in q["required_points"]:
            if rp in pts and not hit(pts[rp], da["correct"]): E(f"{w}: demo correct misses required point {rp}")
        if not hit(ap, da["correct"]): E(f"{w}: demo correct misses answer_patterns")
        tqs = q.get("transfer_questions", [])
        if len(tqs) < 2: E(f"{w}: {len(tqs)} transfer question(s); need >=2 (the 2nd is used after re-teaching)")
        for t in tqs:
            tw = f"transfer {t['id']}"
            emoji(t.get("emoji"), tw)
            tap = comp(t.get("answer_patterns"), tw+".answer_patterns")
            tpts = {p["id"]: comp(p.get("patterns"), f"{tw}.{p['id']}") for p in t["expected_reasoning"]}
            for rp in t["required_points"]:
                if rp not in tpts: E(f"{tw}: required point {rp} missing")
                elif not hit(tpts[rp], t["demo_answer"]): E(f"{tw}: demo_answer misses {rp}")
            if not hit(tap, t["demo_answer"]): E(f"{tw}: demo_answer misses answer_patterns")
    return d, errs, warns

bad = 0
for fn in FILES:
    try: d, errs, warns = check(fn)
    except Exception as e:
        print(f"{fn}: LOAD/STRUCTURE FAIL {type(e).__name__}: {e}"); bad += 1; continue
    print(f"{fn}: concepts={len(d['concepts'])} misconceptions={len(d['misconceptions'])} questions={len(d['questions'])} transfers={sum(len(q.get('transfer_questions',[])) for q in d['questions'])} -> {'OK' if not errs else f'{len(errs)} ERROR(S)'}")
    for e in errs: print("   ERROR", e)
    for w in warns: print("   warn ", w)
    bad += bool(errs)
sys.exit(1 if bad else 0)
