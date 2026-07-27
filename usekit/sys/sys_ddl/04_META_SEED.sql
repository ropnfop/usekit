-- ============================================================
-- META SEED : initial dictionary + global settings (idempotent).
-- Re-runnable: ON CONFLICT DO UPDATE keeps labels/desc/color current.
-- ============================================================

-- ── TBL_META: column-level descriptions (enum_value IS NULL) ──
INSERT INTO TBL_META (table_name,column_name,enum_value,label,description,color,ord) VALUES
 ('TSK_SESSION','kind',NULL,'Kind','세션 실행 방식. live 또는 job.',NULL,0)
 ON CONFLICT(table_name,column_name) WHERE enum_value IS NULL
 DO UPDATE SET label=excluded.label,description=excluded.description,color=excluded.color,ord=excluded.ord;
INSERT INTO TBL_META (table_name,column_name,enum_value,label,description,color,ord) VALUES
 ('TSK_SESSION','mode',NULL,'Mode','컨텍스트 용도. chat/task/edit.',NULL,0)
 ON CONFLICT(table_name,column_name) WHERE enum_value IS NULL
 DO UPDATE SET label=excluded.label,description=excluded.description,color=excluded.color,ord=excluded.ord;

-- ── TBL_META: enum values (enum_value NOT NULL) ──
INSERT INTO TBL_META (table_name,column_name,enum_value,label,description,color,ord) VALUES
 ('TSK_SESSION','kind','live','Live','일반 채팅 누적(재주입 resume)',NULL,1),
 ('TSK_SESSION','kind','job','Job','CLI 작업(cli_session_id resume)',NULL,2),
 ('TSK_SESSION','mode','chat','Chat','설계 컨텍스트',NULL,1),
 ('TSK_SESSION','mode','task','Task','공정 컨텍스트',NULL,2),
 ('TSK_SESSION','mode','edit','Edit','에디터(코드)',NULL,3),
 ('TSK_SESSION','status','active','Active','진행 중',NULL,1),
 ('TSK_SESSION','status','closed','Closed','종료',NULL,2),
 ('TSK_STEP','status','pending','Pending','대기','#586069',1),
 ('TSK_STEP','status','running','Running','실행 중','#d29922',2),
 ('TSK_STEP','status','done','Done','완료','#3fb950',3),
 ('TSK_STEP','status','error','Error','실패','#f85149',4)
ON CONFLICT(table_name,column_name,enum_value)
DO UPDATE SET label=excluded.label,description=excluded.description,color=excluded.color,ord=excluded.ord;

-- ── SYS_META: global settings (app-wide status colors + api_key_ref) ──
INSERT INTO SYS_META (key,value,description) VALUES
 ('schema_version','1','usekit.db 스키마 버전'),
 ('ui.color.alive','#3fb950','provider 헬스 alive'),
 ('ui.color.idle','#586069','미설정/idle'),
 ('ui.color.dead','#f85149','dead/실패'),
 ('ui.color.busy','#d29922','busy/limit'),
 ('api_key_ref.groq','GROQ_API_KEY','groq provider 키 환경변수명'),
 ('api_key_ref.groq_api','GROQ_API_KEY','groq_api provider 키'),
 ('api_key_ref.openrouter','OPENROUTER_API_KEY','openrouter 키')
ON CONFLICT(key) DO UPDATE SET value=excluded.value,description=excluded.description;

-- ── SYS_META: telemetry 설정 (3차 감사) ──
INSERT INTO SYS_META (key,value,description) VALUES
 ('telemetry.level','summary','계측 상세도: summary(DB만) | debug(messages 마스킹) | trace(전문, 로컬전용)'),
 ('telemetry.retention_days','7','ai_calls JSONL 보존기간(일). 모바일 기본 7.'),
 ('telemetry.store_final_prompt','0','final_prompt 전문 저장. 1=trace 에서만. 기본 0(OFF).')
ON CONFLICT(key) DO UPDATE SET value=excluded.value,description=excluded.description;
