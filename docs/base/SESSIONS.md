# SESSIONS.md

USEKIT 개발 세션 히스토리.
새 세션 시작 시 참조 — 맥락, 결정사항, 미완 과제 확인용.

---

## Session 01 — 2026-05-07

**목표:** CLAUDE.md 작성 + 라이브러리 실사용 검증

### 완료한 것

**CLAUDE.md 구축**
- 3-letter 라우팅 전체 정리 (ACTION 15 / FORMAT 10 / LOCATION 7)
- EXEC 레이어 — REPL 실행기 패턴, 스크립트/함수 두 모드, base/sub 구조
- NAVI 레이어 — gjb/sjb 역할 정정 (동적 경로 + 캐시)
- append 4모드, dir_path, 출력 보관 패턴 (wjb/wtb/wmb)
- Help 시스템, 파라미터 정의서(infra/) 위치 문서화

**버그 수정**
| 항목 | 원인 | 수정 |
|------|------|------|
| `uw.history()` ok/info 미기록 | `_log()`에 `_history.append` 누락 | 추가 |
| `use.emit.json.mem()` 미작동 | `use_base.py`에 `emit=DataIO.emit` 누락 | 추가 |
| `core/env` 누락 | `env/` gitignore 규칙 충돌 | 예외 처리 + 파일 커밋 |

**문서 오류 수정**
- `gjb` keydata 설명 잘못됨 → 경로/캐시 전용으로 정정
- LOCATION 8개 → 7개 (`mem`은 emit 전용)
- ACTION 16개 → 15개

**예제 추가**
- `src/base/` — calc, demo, main, score_app, ledger
- `src/sub/` — utils, score_parts/, ledger_parts/

### 발견한 것

- `uw.history()` `ok/info/warn` — 수정 완료
- `use.emit.json.mem()` — 수정 완료
- `gjb` keydata — 문서 정정 완료
- `uw.p()`와 `_log()` 내부 count가 이중으로 올라가는 구조 → 추후 점검 필요

### 다음 세션 과제 (2순위~)

- [ ] `ud` 사용법 문서화 (현재 import만 있음)
- [ ] `km` (keymemory) 실사용 예제
- [ ] `keydata` 심화 — 배열 인덱스, 중첩 경로 예제
- [ ] `walk=True` 패턴 예제
- [ ] `cus` loc 실사용 예제
- [ ] `uw.p()` + `_log()` count 이중 증가 점검

### 현재 라이브러리 상태

> 핵심 기능(JSON, SQL, EXEC) 실사용 가능 수준.
> CLAUDE.md 기준으로 일반적인 데이터 처리 프로젝트 즉시 투입 가능.
> 마감 완성도 약 85%.

---

## Session 02 — 2026-05-07

**목표:** 모바일 첫 연결 + 세션 연계 프로세스 수립

### 완료한 것

- 모바일(Termux + Samsung Browser)에서 Claude Code 첫 연결 확인
- CLAUDE.md / SESSIONS.md 정상 전달 확인
- 세션 연계 구조 점검 → SESSIONS.md 비자동 로드 문제 식별
- CLAUDE.md에 **세션 시작 필수 액션** 섹션 추가

### 결정사항

- 클로드의 역할: usekit 실사용 + 안정화 피드백 제공
- 세션 루틴: SESSIONS.md 먼저 읽기 → 목표 확인 → 마감 시 기록
- 스모크 테스트 등 반복 작업 금지 — CLAUDE.md 상태가 진실

---

## Session 03 — 2026-05-07

**목표:** ud 재정의 + 문서 구조 정비

### 완료한 것

**ud 재정의 (SQLite3 전용 저수준 도구)**
- `sbi_db.py` 전면 재설계 — `conn / exec / fetch / one / many / tx / close`
- `use_support.py` import 경로 버그 수정 (`init.db` → `init.dbms`)
- `conn()` 재호출 시 연결 누수 버그 수정 (자동 close 추가)
- CLAUDE.md `ud` 섹션 추가

**문서 구조 정비**
- `docs/base/manual/usekit/` — 01~05 매뉴얼 파일 분리
- `docs/base/manual/support/` — uw / ut / ud / s 매뉴얼 분리
- CLAUDE.md 슬림 인덱스로 재편
- 중복 제거, 섹션 이동, 누락 복구, 정확성 검증 (pjb/ljb/fjb 동작 확인)
- 타 Claude 세션 브랜치 4개 정리

### 현재 라이브러리 상태

> ud 정상 작동 확인.
> 문서 구조 완성 — CLAUDE.md(인덱스) + manual/ 9개 파일.
> 마감 완성도 약 90%.

### 다음 세션 과제

- [ ] `km` (keymemory) 실사용 예제
- [ ] `keydata` 심화 — 배열 인덱스, 중첩 경로 예제
- [ ] `walk=True` 패턴 예제
- [ ] `cus` loc 실사용 예제
- [ ] `uw.p()` + `_log()` count 이중 증가 점검
