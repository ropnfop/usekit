# uk setup 적용 가이드 — 시드 배치 후 셋업 실행

## 1) 패키지 소스에 시드 배치 (editable 이라 복사 즉시 반영)
다음 5개를 패키지 소스 `usekit/sys/sys_ddl/` 에 둔다 (01/02 는 교체, 03~05 신규):
```
01_TSK.sql        ← 본 패키지본으로 교체 (확장 컬럼 포함: SESSION provider/model/kind/
                     cli_session_id/turn_count, MESSAGE importance/keywords/meta, mode 주석 정정)
02_TSK_IDX.sql    ← 기존 유지
03_META.sql       ← 신규 (SYS/TBL/TSK_META + 부분유니크인덱스)
04_META_SEED.sql  ← 신규 (enum 해설 + telemetry SYS_META, 멱등)
05_TSK_CALL.sql   ← 신규 (계측 테이블 + 인덱스 4)
```

## 2) 코드 수정 (uk setup 이 usekit.db 로 만들게)
```
helper_setup_task.py:39   "task.db"  → "usekit.db"
helper_setup_task.py      주석/print 의 task.db 표기 → usekit.db
helper_setup_config.py:54 안내문 "(task.db + ...)"  → "(usekit.db + ...)"
helper_setup_task.py:80   TSK_% 검증 → expected_tables 9개 (SETUP_PATCH.md)
sbi_util.py:44            _TASK_DB_REL .../task.db → usekit.db
(STEP1) get_sys_db_path() 신설 → 위 모듈들이 호출하도록 수렴
```
⚠ task_manager.py 는 건드리지 않음 (별개 nohup DB, 2차 트랙).

## 3) uk setup 실행
```
uk setup
  → ... → "Enable task manager (usekit.db + Claude Code task tracking)? [y/N]: y"
  → helper_setup_task 가 01~05 적재 → .usekit/sys/sys_db/usekit.db 생성
```

## 4) 검증 (이게 나와야 정상 — uk setup 시뮬로 확인됨)
```bash
sqlite3 /storage/emulated/0/projects/pj01/.usekit/sys/sys_db/usekit.db "
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
SELECT 'TBL_META='||COUNT(*) FROM TBL_META;
SELECT 'SYS_META='||COUNT(*) FROM SYS_META;
"
```
기대 결과:
```
테이블 9개: SYS_META TBL_META TSK_CALL TSK_CONTEXT TSK_MESSAGE TSK_META TSK_SESSION TSK_STEP TSK_TASK
TBL_META=13
SYS_META=11        (메타 8 + telemetry 3)
TSK_SESSION 확장컬럼: provider/model/kind/cli_session_id/turn_count
TSK_MESSAGE 확장컬럼: importance/keywords/meta
```
데이터 행은 0 (빈 스키마 = 정상. 가비지 task_6a62cc 제거됨, 재생성 로직 없음).

## 참고 — 그냥 개발이라 수동 적재도 가능
editable 설치라 sqlite3 로 직접 01~05 적재해도 동일. 단 uk setup 경로로 가면
셋업 로직(이름통합/expected_tables 검증)까지 같이 검증되므로 권장.
