# NAVI Layer

NAVI는 ACTION의 한 분류 — **파일 탐색 + 경로/값 저장** 전용.

| 코드 | 이름 | 역할 |
|------|------|------|
| `p` | path | 디렉토리 경로 반환 |
| `f` | find | 파일 탐색 → PosixPath 리스트 |
| `l` | list | 파일 목록 → 파일명 문자열 리스트 |
| `g` | get | 저장된 경로/값 조회 |
| `s` | set | 경로/값 저장 |

---

## p — path (디렉토리 경로)

```python
u.pjb()               # data/json/base/ 의 절대경로
u.pjb("sub/dir")      # data/json/base/sub/dir/ 의 절대경로
u.ptb()               # data/tmp/ 의 절대경로
```

> 반환값: `PosixPath` — `str()` 변환 또는 `/` 연산 가능

---

## f — find (패턴 탐색)

```python
u.fjb("user_*")       # data/json/base/ 에서 user_*.json 매칭 → PosixPath 리스트
u.fjb("*.json")       # 모든 JSON 파일
u.fjb("log_*", walk=True)   # 하위 디렉토리 포함 재귀 탐색
```

> 반환값: `List[PosixPath]`

---

## l — list (파일 목록)

```python
u.ljb()               # data/json/base/ 의 파일명 리스트 (확장자 포함)
u.ljb("sub/dir")      # 서브 경로 지정
```

> 반환값: `List[str]` — 파일명 문자열

---

## g / s — get / set (경로·값 캐시)

`s`(set) 로 저장, `g`(get) 으로 조회. 주 용도는 **동적 경로 전환**과 **캐시성 값 보관**.

```python
# 경로 저장 → 동적 전환
u.sjb("data/prod", "env_path")
u.sjb("data/dev",  "env_path")    # 덮어쓰기
env = u.gjb("env_path")           # → "data/dev"

# 꺼낸 경로를 dir_path로 활용
u.rjb("config", dir_path=env)

# 캐시성 값 보관
u.sjb("session_abc123", "current_session")
u.gjb("current_session")          # → "session_abc123"
```

> `keydata` 를 이용한 데이터 접근은 `u.rjb("name", keydata="user/email")` — NAVI가 아닌 DATA 액션.

---

## f vs l 비교

| | `u.fjb()` | `u.ljb()` |
|---|---|---|
| 반환값 | `List[PosixPath]` | `List[str]` |
| 패턴 지정 | `u.fjb("user_*")` | 없음 |
| 재귀 | `walk=True` 지원 | — |
| 용도 | 파일 경로가 필요할 때 | 파일 이름 목록만 필요할 때 |
