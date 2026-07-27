# -*- coding: utf-8 -*-
# Deep data-action test: write / update / delete / read at full keydata depth.
# Run after applying the keydata patch (usekit_keydata_patch.zip).
# Expected: ALL PASS.

from usekit import u, s

_pass = 0
_fail = 0

def chk(label, got, expect):
    global _pass, _fail
    ok = got == expect
    if ok:
        _pass += 1
        print(f"[PASS] {label}")
    else:
        _fail += 1
        print(f"[FAIL] {label}\n        got={got!r}\n        exp={expect!r}")

def section(t):
    print(f"\n{'='*60}\n{t}\n{'='*60}")

# =====================================================================
section("WRITE — keydata 부분쓰기 (기존과 병합, 경로 자동생성)")
# =====================================================================
u.wjb({"app": {"name": "srs"}}, "w_kd", wrap=False)
u.wjb(100, "w_kd", keydata="user/score")          # set nested into existing
chk("write keydata into existing (merge)",
    u.rjb("w_kd"), {"app": {"name": "srs"}, "user": {"score": 100}})

u.wjb("dark", "w_kd2", keydata="a/b/c/d")          # deep auto-create from empty
chk("write keydata deep auto-create",
    u.rjb("w_kd2", keydata="a/b/c/d"), "dark")

# =====================================================================
section("WRITE — wrap 함정 (콜론/URL) 및 wrap=False")
# =====================================================================
u.wjb("name:Alice", "w_wrap")                       # default wrap splits colon
chk("wrap colon split", u.rjb("w_wrap"), {"name": "Alice"})
u.wjb("http://x.com", "w_url", wrap=False)          # wrap=False keeps raw
chk("wrap=False keeps raw", u.rjb("w_url"), "http://x.com")

# =====================================================================
section("WRITE — append 모드 (array / object / jsonl)")
# =====================================================================
# NOTE: array append requires the file to ALREADY be a top-level list.
# Start from a list (or use append_mode='auto' which detects type).
u.wjb([{"id": 1}], "w_app", wrap=False)
u.wjb({"id": 2}, "w_app", append=True, append_mode="array")
chk("append array (start as list)", u.rjb("w_app"), [{"id": 1}, {"id": 2}])

# 'auto' mode: detects existing type (list here) and appends accordingly
u.wjb([{"id": 1}], "w_auto", wrap=False)
u.wjb({"id": 2}, "w_auto", append=True, append_mode="auto")
chk("append auto (detect list)", u.rjb("w_auto"), [{"id": 1}, {"id": 2}])

u.wjb({"a": 1}, "w_obj", wrap=False)
u.wjb({"b": 2}, "w_obj", append=True, append_mode="object")
chk("append object merge", u.rjb("w_obj"), {"a": 1, "b": 2})

u.djb("w_log")  # ensure clean start (jsonl appends accumulate across reruns)
u.wjb({"e": "login"}, "w_log", append=True, append_mode="jsonl")
u.wjb({"e": "logout"}, "w_log", append=True, append_mode="jsonl")
chk("append jsonl read back", u.rjb("w_log", jsonl=True), [{"e": "login"}, {"e": "logout"}])

# =====================================================================
section("UPDATE — Big (전체 단위): merge / list / 타입불일치 / merge=False")
# =====================================================================
u.wjb({"a": 1, "b": 2}, "u_big", wrap=False)
u.ujb({"c": 3}, "u_big")
chk("update dict merge", u.rjb("u_big"), {"a": 1, "b": 2, "c": 3})

u.wjb([1, 2], "u_list", wrap=False)
u.ujb([3, 4], "u_list")
chk("update list append", u.rjb("u_list"), [1, 2, 3, 4])

u.wjb({"a": 1}, "u_rep", wrap=False)
u.ujb({"c": 3}, "u_rep", merge=False)
chk("update merge=False replace", u.rjb("u_rep"), {"c": 3})

# =====================================================================
section("UPDATE — Small (지점 단위): 부분갱신 / create_missing / recursive")
# =====================================================================
u.wjb({"app": {"v": "1", "debug": True}, "x": 9}, "u_pt", wrap=False)
u.ujb("2", "u_pt", keydata="app/v")
chk("update nested point only", u.rjb("u_pt"), {"app": {"v": "2", "debug": True}, "x": 9})

u.wjb({"app": {"v": "1"}}, "u_cm", wrap=False)
u.ujb("dark", "u_cm", keydata="app/theme/mode")     # create_missing default True
chk("update auto-create path", u.rjb("u_cm", keydata="app/theme/mode"), "dark")

u.wjb({"users": [{"role": "x"}, {"role": "x"}], "role": "x"}, "u_rec", wrap=False)
u.ujb("ADMIN", "u_rec", keydata="role", recursive=True)
chk("update recursive all keys",
    u.rjb("u_rec"), {"users": [{"role": "ADMIN"}, {"role": "ADMIN"}], "role": "ADMIN"})

# =====================================================================
section("DELETE — Big (파일 전체) vs Small (지점만)")
# =====================================================================
u.wjb({"k": "v"}, "d_big", wrap=False)
u.djb("d_big")                                       # delete whole file
chk("delete whole file -> has False", u.hjb("d_big"), False)

u.wjb({"keep": 1, "drop": 2}, "d_small", wrap=False)
u.djb("d_small", keydata="drop")                     # delete one key, keep file
chk("delete keydata point only", u.rjb("d_small"), {"keep": 1})

u.wjb({"a": {"tmp": 1, "real": 2}, "b": {"tmp": 3}}, "d_rec", wrap=False)
u.djb("d_rec", keydata="tmp", recursive=True)        # delete all 'tmp' anywhere
chk("delete recursive all keys", u.rjb("d_rec"), {"a": {"real": 2}, "b": {}})

# =====================================================================
section("READ — keydata 네비/검색 (패치 적용 확인)")
# =====================================================================
u.wjb({
    "app": {"version": "0.5", "debug": True},
    "users": [
        {"id": 1, "email": "alice@gmail.com"},
        {"id": 2, "email": "bob@naver.com"},
        {"id": 3, "email": "cara@gmail.com"},
    ],
}, "r_kd", wrap=False)
chk("read path nav", u.rjb("r_kd", keydata="app/version"), "0.5")
chk("read neg index", u.rjb("r_kd", keydata="users[-1]/email"), "cara@gmail.com")
chk("read recursive all",
    u.rjb("r_kd", keydata="email", recursive=True, find_all=True),
    ["alice@gmail.com", "bob@naver.com", "cara@gmail.com"])
chk("read search_value (PATCH)",
    u.rjb("r_kd", keydata="email", recursive=True, find_all=True, search_value="gmail"),
    ["alice@gmail.com", "cara@gmail.com"])
chk("read regex (PATCH)",
    u.rjb("r_kd", keydata="email", recursive=True, find_all=True, search_value="^a", regex=True),
    ["alice@gmail.com"])
chk("read keydata_exists True (PATCH)",
    u.rjb("r_kd", keydata="app/debug", keydata_exists=True), True)
chk("read keydata_exists False (PATCH)",
    u.rjb("r_kd", keydata="app/ghost", keydata_exists=True), False)

# =====================================================================
section("TXT — keydata = grep (정규식 노선, 구조화 아님) [2차 PATCH]")
# =====================================================================
u.wtb("INFO start\nERROR timeout\nWARN disk\nERROR oom\nINFO done\n", "t_grep")
chk("txt grep substring", u.rtb("t_grep", keydata="ERROR"), "ERROR timeout\nERROR oom")
chk("txt grep regex ^WARN", u.rtb("t_grep", keydata="^WARN", regex=True), "WARN disk")
chk("txt tail_bottom (regression)", u.rtb("t_grep", tail_bottom=2), "ERROR oom\nINFO done")
chk("txt plain read (regression)", u.rtb("t_grep")[:10], "INFO start")

# =====================================================================
section("YAML — keydata 검색 (json 과 동일 노선) [1차 PATCH 공유]")
# =====================================================================
u.wyb({"app": {"v": "9"}, "users": [{"email": "a@gmail.com"}, {"email": "b@naver.com"}]}, "y_kd")
chk("yaml path nav", u.ryb("y_kd", keydata="app/v"), "9")
chk("yaml search_value gmail",
    u.ryb("y_kd", keydata="email", recursive=True, find_all=True, search_value="gmail"),
    ["a@gmail.com"])

# =====================================================================
section("SAFE / MEM — 보조")
# =====================================================================
chk("safe missing -> None", s.rjb("nope_xyz_123"), None)
u.wjm({"k": "v"}, "m1")
chk("mem write/read", u.rjm("m1"), {"k": "v"})
chk("mem has", u.hjm("m1"), True)

# =====================================================================
print(f"\n{'='*60}")
print(f"RESULT: {_pass} passed, {_fail} failed")
print(f"{'='*60}")
import sys
sys.exit(1 if _fail else 0)
