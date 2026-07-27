# Post-patch: deep options must now work via u.rjb directly. Regression must hold.
from usekit import u
u.wjb({
    "app":{"version":"0.5","debug":True},
    "users":[
        {"id":1,"name":"Alice","email":"alice@gmail.com"},
        {"id":2,"name":"Bob","email":"bob@naver.com"},
        {"id":3,"name":"Cara","email":"cara@gmail.com"},
    ],
    "decks":{"math":{"cards":42},"eng":{"cards":17}},
}, "pp", wrap=False)

def chk(label, got, expect):
    ok = got == expect
    print(f"[{'PASS' if ok else 'FAIL'}] {label}\n        got={got!r}\n        exp={expect!r}")

print("=== REGRESSION (기존 동작 유지돼야) ===")
chk("path nav",        u.rjb("pp", keydata="app/version"), "0.5")
chk("neg index",       u.rjb("pp", keydata="users[-1]/name"), "Cara")
chk("recursive first", u.rjb("pp", keydata="email", recursive=True), "alice@gmail.com")
chk("recursive all",   u.rjb("pp", keydata="email", recursive=True, find_all=True),
    ["alice@gmail.com","bob@naver.com","cara@gmail.com"])
chk("missing+default", u.rjb("pp", keydata="app/ghost", default="N/A"), "N/A")

print("\n=== NEW (패치로 이제 u.rjb 로 돼야) ===")
chk("search_value gmail", u.rjb("pp", keydata="email", recursive=True, find_all=True, search_value="gmail"),
    ["alice@gmail.com","cara@gmail.com"])
chk("regex ^a",           u.rjb("pp", keydata="email", recursive=True, find_all=True, search_value="^a", regex=True),
    ["alice@gmail.com"])
chk("keydata_exists T",   u.rjb("pp", keydata="app/debug", keydata_exists=True), True)
chk("keydata_exists F",   u.rjb("pp", keydata="app/ghost", keydata_exists=True), False)
chk("exists+value match", u.rjb("pp", keydata="email", recursive=True, find_all=True, search_value="gmail", keydata_exists=True), True)
