# helper_setup_task.py 패치 (메타 3계층 적재 검증)

현재 L80 은 TSK_% 만 카운트 → SYS_META/TBL_META 를 못 셈.
감사 권고: prefix 확장보다 expected_tables 명시 검증이 더 안전.

## BEFORE (L78~80 부근)
```python
tables = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' AND name LIKE 'TSK_%' ORDER BY name")]
```

## AFTER
```python
expected = [
    "TSK_TASK","TSK_STEP","TSK_SESSION","TSK_MESSAGE","TSK_CONTEXT",
    "SYS_META","TBL_META","TSK_META","TSK_CALL",
]
have = {r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table'")}
tables  = [t for t in expected if t in have]
missing = [t for t in expected if t not in have]
if missing and verbose:
    print(f"  [WARN] missing tables: {', '.join(missing)}")
```

검증 통과 조건: missing == [] (8개 전부 존재).
시드 파일은 01→02→03→04 알파벳 순 자동 적재 (코드 무수정).
