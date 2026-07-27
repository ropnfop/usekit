# Path: usekit.llm.handler.ua_emo.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# ua.emo — the emotion JOURNALER (write-time, LLM-backed).
#   slice 1: judge()           sentence -> signed ERSDF + HSLVA + leaf   (output only)
#   slice 2: store()           judgement -> EMO_STATE + EMO_CAUSE        (ud, base/sub)
#            judge_and_store()  convenience: judge then store
#
# Role split (EMO Core Theory §9, the spine):
#   LLM  = journaler : reads a sentence, decides per-axis valence (signed ints).
#   code = engine    : ue.ersdf / ue.hslva ASSEMBLE codes; ud persists; this
#                      module only orchestrates. The model emits NUMBERS only.
#
# Lives under ua (LLM handler), NOT ue: ue stays a PURE namespace (no DB/LLM).
# §9 pole prompt (policy) is injectable via judge(prompt=...).
#
# DB routing: store(db="sub") -> test.db (rehearsal),  db="base" -> base.db
#   (prod). Path is RELATIVE ("data/table/db/<name>.db") and resolved by ud via
#   its own BASE (loader_env = the pj01 root). We avoid helper_path.resolve_*
#   and u.fad here: resolve reads a dev/bundle sys_const (db_sub='system.db'),
#   and u.fad does a filesystem walk + returns a list. sub (test.db) is the
#   DEFAULT so a stray store never pollutes real user data.
#
# Verify on device (backend chat / RUN):
#   from usekit import ua
#   ua.conn("groq_api")
#   ua.emo.judge_and_store("엄마랑 크게 싸웠다", ref_id=113)   # -> test.db
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import json as _json
import re as _re
import sys as _sys
import time as _time


# Default §9 pole prompt (policy seed). Injectable via judge(prompt=...).
# + / - per axis; 0 = undecidable/neutral. Valence is PER AXIS (not global) —
# one memory may mix signs (e.g. "미안" = F- negative feeling + D+ repair drive).
_FOP_PROMPT = """\
너는 감정 분개자다. 입력 문장 하나를 5개 축으로 분개한다.
각 축은 -9..9 정수다. 부호가 valence다: +는 긍정, -는 부정, 0은 판단불가/중립.
크기(절댓값)는 활성/관여 정도다. valence는 축마다 독립이다 (전역 아님).

축 폴:
- env  (환경) : + 좋은 맥락        / - 나쁜 맥락
- rel  (관계) : + 연결·회복·지지   / - 손상·갈등·단절
- self (자아) : + 자기확신·효능     / - 자기비난·자책·수치
- drive(의지) : + 접근·추진         / - 회피·저항
- feel (감정) : + 강한 긍정         / - 강한 부정

색(HSLVA)도 함께 추정한다:
- hue  : 0..360 (감정의 결: 분노=빨강계, 슬픔=파랑계, 평온=초록계 등)
- sat  : 0.0..1.0 (선명도/강도)
- light: 0.0..1.0 (밝기)

leaf : 이 기억의 핵심 주제어 한 단어 (예: 엄마, 시험, 친구).

설명 없이 아래 JSON 한 줄만 출력한다. 다른 텍스트 금지:
{"e":<int>,"r":<int>,"s":<int>,"d":<int>,"f":<int>,"hue":<int>,"sat":<float>,"light":<float>,"leaf":"<word>"}

문장:
"""

# Hue -> 8-color phase (EMO_PHASE.phase_key). Used until EMO_PHASE is seeded;
# bands are the standard 45-deg wheel (red anchored at 0/360).
_PHASE_BANDS = [(22, "red"), (67, "orange"), (112, "yellow"), (157, "green"),
                (202, "cyan"), (247, "blue"), (292, "violet"), (337, "magenta")]


def _hue_phase(h: int) -> str:
    """Map a hue (deg) to an EMO_PHASE phase_key."""
    h = int(h) % 360
    for thr, name in _PHASE_BANDS:
        if h <= thr:
            return name
    return "red"  # 337..360 wraps back to red


def _db_fail(where: str, err: Exception) -> None:
    """Surface a silent failure on stderr, never raise (P1-3 convention)."""
    print(f"[ua.emo] {where} FAILED: {type(err).__name__}: {err}", file=_sys.stderr)


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply, tolerating ```json
    fences and surrounding prose. Raises ValueError if none is parseable."""
    if not text:
        raise ValueError("empty model reply")
    cleaned = _re.sub(r"```(?:json)?", "", text).strip()
    m = _re.search(r"\{.*\}", cleaned, _re.DOTALL)
    blob = m.group(0) if m else cleaned
    return _json.loads(blob)


class EmoAIHandler:
    """ua.emo — emotion journaler. Holds a back-ref to the ua instance (DI),
    so this module never imports ua_handler -> no import cycle. Pure codecs
    come from ue (sbi_emo), which stays untouched."""

    def __init__(self, ua):
        self._ua = ua

    # ── slice 1: judge (output only) ────────────────────────────
    def judge(self, text: str, *, prompt: str = None, model: str = None,
              raw: bool = False) -> dict:
        """Decompose one sentence into a signed ERSDF + HSLVA + leaf.

        The LLM emits only signed integers (sign = valence); ue.ersdf/ue.hslva
        assemble the canonical codes. Uses ua.run (raw single call) so chat
        history is NOT touched. Never raises (P1-3): on failure -> {error, raw}.

        Returns {ersdf, hslva, leaf, axes, hsl, valid[, raw]}.
        """
        from usekit.classes.support.base.init.emo.sbi_emo import ue

        full = (prompt or _FOP_PROMPT) + (text or "")
        kw = {"model": model} if model else {}
        try:
            result = self._ua.run(full, **kw)
            reply = result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as e:
            _db_fail("judge:run", e)
            return {"error": f"llm_call: {e}", "raw": ""}

        try:
            data = _extract_json(reply)
        except Exception as e:
            _db_fail("judge:parse", e)
            return {"error": f"parse: {e}", "raw": reply}

        try:
            axes = (int(data["e"]), int(data["r"]), int(data["s"]),
                    int(data["d"]), int(data["f"]))
            hsl = (int(data["hue"]), float(data["sat"]), float(data["light"]))
            ersdf = ue.ersdf.to_code(*axes)                  # engine assembles signed code
            hslva = ue.hslva.to_code(hsl[0], hsl[1], hsl[2])
            leaf = str(data.get("leaf", "")).strip()
        except Exception as e:
            _db_fail("judge:assemble", e)
            return {"error": f"assemble: {e}", "raw": reply}

        out = {
            "ersdf": ersdf,
            "hslva": hslva,
            "leaf": leaf,
            "axes": axes,
            "hsl": hsl,                 # raw H/S/L kept for store()'s EMO_STATE cols
            "valid": ue.ersdf.is_valid(ersdf),
        }
        if raw:
            out["raw"] = reply
        return out

    # ── slice 2: store (EMO_STATE + EMO_CAUSE) ──────────────────
    def store(self, judgement: dict, *, db: str = "sub", ref_type: str = "dialogue",
              ref_id: int = 0, speaker: str = "user", ts: int = None) -> dict:
        """Persist a judge() result into EMO_STATE (+ linked EMO_CAUSE).

        db: "sub" -> test.db (default, rehearsal),  "base" -> base.db (prod).
        Routing: relative path resolved by ud's own BASE. Codes/labels from
        ue (engine); affect_vector/activation use ue.hslva.derive (DDL formula).
        Never raises (P1-3): on failure -> {error}.

        Returns {emo_state_id, ersdf, leaf, db, stored}.
        """
        from usekit import ud
        from usekit.classes.support.base.init.emo.sbi_emo import ue

        if "error" in judgement or not judgement.get("valid"):
            return {"error": "invalid judgement, not stored", "judgement": judgement}

        h, s, l = judgement["hsl"]
        v, a = ue.hslva.derive(s, l)                 # DDL: affect_vector, activation
        desc = ue.ersdf.describe(judgement["ersdf"])  # {env:{value,label,polarity}, ...}

        # DB by RELATIVE path so ud resolves it via its own BASE (loader_env,
        # verified = the pj01 project root). We deliberately do NOT use
        # helper_path.resolve_* here: that reads the dev/bundle sys_const
        # (db_sub='system.db') instead of the project's active yaml — a known
        # path bug. Relative + ud sidesteps the yaml read entirely.
        rel = "data/table/db/base.db" if db == "base" else "data/table/db/test.db"

        state_id = None
        try:
            ud.conn(rel)
            state_id = ud.insert("EMO_STATE", {
                "ref_type": ref_type,
                "ref_id": ref_id,
                "speaker": speaker,
                "timestamp": ts if ts is not None else int(_time.time()),
                "hue": int(h), "saturation": float(s), "lightness": float(l),
                "affect_vector": v, "activation": a,
                "dh": "0", "ds": "0", "dl": "0",      # no baseline yet -> neutral delta
                "hslva_code": judgement["hslva"],
                "phase": _hue_phase(h),
            })
            ud.insert("EMO_CAUSE", {
                "emo_state_id": state_id,
                "env_code": str(desc["env"]["value"]),     "env_label": desc["env"]["label"],
                "rel_code": str(desc["rel"]["value"]),     "rel_label": desc["rel"]["label"],
                "self_code": str(desc["self"]["value"]),   "self_label": desc["self"]["label"],
                "drive_code": str(desc["drive"]["value"]), "drive_label": desc["drive"]["label"],
                "feel_code": str(desc["feel"]["value"]),   "feel_label": desc["feel"]["label"],
                "ersdf_code": judgement["ersdf"],
            })
        except Exception as e:
            _db_fail("store", e)
            return {"error": f"store: {e}"}
        finally:
            try:
                ud.close()
            except Exception:
                pass

        return {"emo_state_id": state_id, "ersdf": judgement["ersdf"],
                "leaf": judgement.get("leaf"), "db": rel, "stored": True}

    def judge_and_store(self, text: str, *, db: str = "sub", prompt: str = None,
                        model: str = None, **store_kw) -> dict:
        """judge() then store() in one call. store_kw -> ref_type/ref_id/speaker/ts."""
        j = self.judge(text, prompt=prompt, model=model)
        if "error" in j:
            return j
        return self.store(j, db=db, **store_kw)

    # ── slice 3: recall (retrieve by signed-coordinate distance) ─
    def recall(self, query: str, *, db: str = "sub", top: int = 5,
               prompt: str = None, model: str = None, weights=None,
               query_ersdf: str = None) -> dict:
        """Retrieve past emotion memories nearest to `query` by ERSDF distance.

        Toy-proven logic on the real DB: the query is SIGNED by the same
        journaler (judge), then ranked against stored ersdf_code via
        ue.dhsl.diff. Signing both sides is essential — sign mismatch breaks
        the distance (EMO Core Theory §9 toy note).

        db: "sub" -> test.db (default), "base" -> base.db.
        weights: per-axis weights for diff (default = dhsl's (16,8,4,2,1)).
        query_ersdf: if the caller ALREADY has the query's signed coord (e.g.
        flow._extract just produced it), pass it to SKIP judge -> no extra LLM
        call. Must be a valid signed code; falls back to judge if invalid/None.
        Never raises (P1-3). Returns {query, query_ersdf, n, results:[...]}.
        Each result: {dist, ersdf, state_id, ref_type, ref_id}.
        """
        from usekit import ud
        from usekit.classes.support.base.init.emo.sbi_emo import ue

        if query_ersdf and ue.ersdf.is_valid(query_ersdf):
            qe = query_ersdf                 # reuse caller's coord -> no LLM
        else:
            qj = self.judge(query, prompt=prompt, model=model)
            if "error" in qj:
                return qj
            qe = qj["ersdf"]

        rel = "data/table/db/base.db" if db == "base" else "data/table/db/test.db"
        rows = []
        try:
            ud.conn(rel)
            rows = ud.fetch(
                "SELECT c.emo_state_id AS sid, c.ersdf_code AS code, "
                "s.ref_type AS rtype, s.ref_id AS rid "
                "FROM EMO_CAUSE c JOIN EMO_STATE s ON c.emo_state_id = s.id "
                "WHERE c.ersdf_code IS NOT NULL AND c.ersdf_code != ''"
            )
        except Exception as e:
            _db_fail("recall:fetch", e)
            return {"error": f"recall: {e}", "query_ersdf": qe}
        finally:
            try:
                ud.close()
            except Exception:
                pass

        w = tuple(weights) if weights else None
        scored = []
        for r in rows:
            code = r.code
            if not ue.ersdf.is_valid(code):     # skip malformed / legacy bad codes
                continue
            d = ue.dhsl.diff(qe, code, w) if w else ue.dhsl.diff(qe, code)
            scored.append({"dist": d, "ersdf": code, "state_id": r.sid,
                           "ref_type": r.rtype, "ref_id": r.rid})
        scored.sort(key=lambda x: x["dist"])
        return {"query": query, "query_ersdf": qe, "n": len(scored),
                "results": scored[:top]}

    # ── slice 4: backfill (code existing dialogues) ─────────────
    def backfill(self, *, db: str = "sub", speaker: str = "user",
                 limit: int = None, skip_existing: bool = True,
                 dry_run: bool = False, verbose: bool = True) -> dict:
        """Code existing MEM_DIALOGUE rows into EMO_STATE/EMO_CAUSE via
        judge_and_store — one LLM call per row, so a full run is slow; test with
        limit= first. Reads + writes the SAME db (sub=test.db by default).

        speaker:       only code rows from this speaker ('user' = the person).
        skip_existing: skip dialogue ids already coded (ref_type='dialogue').
        dry_run:       count only, no LLM / no insert.
        verbose:       per-row progress on stderr (a full run is long).
        Never raises (P1-3). Returns {total, stored, skipped, errors, db}.
        """
        from usekit import ud

        rel = "data/table/db/base.db" if db == "base" else "data/table/db/test.db"
        rows, existing = [], set()
        try:
            ud.conn(rel)
            sql = ("SELECT id, message FROM MEM_DIALOGUE "
                   "WHERE message IS NOT NULL AND message != ''")
            params = []
            if speaker:
                sql += " AND speaker = ?"
                params.append(speaker)
            sql += " ORDER BY id"
            # NOTE: no SQL LIMIT — `limit` caps NEWLY processed rows (see loop),
            # otherwise it would only ever re-scan the first N (already-coded) ids.
            rows = ud.fetch(sql, *params)
            if skip_existing:
                ex = ud.fetch("SELECT DISTINCT ref_id FROM EMO_STATE "
                              "WHERE ref_type = 'dialogue'")
                existing = {str(r.ref_id) for r in ex}
        except Exception as e:
            _db_fail("backfill:read", e)
            return {"error": f"read: {e}"}
        finally:
            try:
                ud.close()
            except Exception:
                pass

        summary = {"total": len(rows), "stored": 0, "skipped": 0,
                   "errors": 0, "db": rel}
        for i, r in enumerate(rows, 1):
            rid = r.id
            if (skip_existing and str(rid) in existing) or dry_run:
                summary["skipped"] += 1
                continue
            res = self.judge_and_store(r.message, db=db, ref_id=rid, speaker=speaker)
            if isinstance(res, dict) and res.get("stored"):
                summary["stored"] += 1
            else:
                summary["errors"] += 1
            if verbose:
                print(f"[ua.emo.backfill] {i}/{summary['total']} id={rid} "
                      f"stored={summary['stored']} err={summary['errors']}",
                      file=_sys.stderr)
            # `limit` caps how many NEW rows we touch this run (skips don't count)
            if limit and (summary["stored"] + summary["errors"]) >= int(limit):
                break
        return summary

    def __repr__(self):
        return "<EmoAIHandler ua.emo [judge | store | judge_and_store | recall | backfill]>"


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
