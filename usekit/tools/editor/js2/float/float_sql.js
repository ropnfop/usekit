// float_sql.js — SQL pill logic (extracted from index.html)
(function() {
  const body       = document.body;
  const btnSqlView = document.getElementById('btnSqlView');
  const sqlPill    = document.getElementById('floatSqlTool');
  const btnSql     = document.getElementById('floatBtnSql');
  const btnGrid    = document.getElementById('floatBtnGrid');
  const btnSqlTool = document.getElementById('floatBtnSqlTool');
  const overlay    = document.getElementById('sqlGridOverlay');
  const btnClose   = document.getElementById('sgpBtnClose');
  if (!btnSqlView || !sqlPill) return;

  // ── SQL pill 독립 표시/숨김 ──
  //   Python pill(#floatRunTool)과 완전히 독립적으로 동작.
  //   풋터 SQL VIEW 버튼으로만 켜고 끔. 그리드는 사용자가 GRID 버튼으로 직접 오픈.
  //   숨김 시 pointer-events: none 처리 → 숨겨진 상태에서 터치 히트테스트 완전 차단
  //   (복붙 등 에디터 동작과의 간섭 방지)
  //   가시성은 localStorage에 저장 → 재시작 시 이전 상태 복원
  function showSqlFloat() {
    sqlPill.style.display = 'flex';
    sqlPill.style.pointerEvents = '';       // 히트테스트 복원
    // TOOL 팝업은 초기에 닫힌 상태로
    const stp = document.getElementById('floatSqlToolPanel');
    if (stp) stp.style.display = 'none';
    try { localStorage.setItem('usekit_sql_float_visible', '1'); } catch (e) {}
  }
  function hideSqlFloat() {
    sqlPill.style.display = 'none';
    sqlPill.style.pointerEvents = 'none';   // 숨김 중 이벤트 히트테스트 차단
    // pill 숨길 때 관련 팝업/오버레이도 정리
    const stp = document.getElementById('floatSqlToolPanel');
    if (stp) stp.style.display = 'none';
    closeGrid();
    try { localStorage.removeItem('usekit_sql_float_visible'); } catch (e) {}
  }
  function toggleSqlFloat() {
    const isOpen = sqlPill.style.display === 'flex';
    if (isOpen) hideSqlFloat();
    else showSqlFloat();
  }

  // 초기 상태 — 이전 가시성 복원
  //   pointer-events는 가시성에 연동
  try {
    if (localStorage.getItem('usekit_sql_float_visible') === '1') {
      sqlPill.style.display = 'flex';
      sqlPill.style.pointerEvents = '';
    } else {
      sqlPill.style.pointerEvents = 'none';
    }
  } catch (e) {
    sqlPill.style.pointerEvents = 'none';
  }

  // 풋터 SQL VIEW 버튼 — 기존 _bind('btnSqlView')의 toast를 덮어쓰지 않도록
  // touchend / mouseup만 직접 바인딩 (run tool 패턴과 동일)
  let _tc = false;
  btnSqlView.addEventListener('touchstart', e => { e.preventDefault(); _tc = true; }, { passive: false });
  btnSqlView.addEventListener('touchend',   e => { e.preventDefault(); if (_tc) { _tc = false; toggleSqlFloat(); } }, { passive: false });
  btnSqlView.addEventListener('mouseup',    e => { if (!_tc) toggleSqlFloat(); });

  // ── 그리드 열기/닫기 ──
  function openGrid() {
    overlay.classList.add('is-open');
    sqlPill.classList.add('is-grid-open');
    btnGrid.classList.add('is-active');
    _syncGridLabel();
  }
  function closeGrid() {
    overlay.classList.remove('is-open');
    _exitEditMode();
    sqlPill.classList.remove('is-grid-open');
    btnGrid.classList.remove('is-active');
    _syncGridLabel();
  }
  function toggleGrid() {
    if (overlay.classList.contains('is-open')) closeGrid();
    else openGrid();
  }

  // TOOL 메뉴의 "Show/Hide Grid" 라벨 갱신 (팝업 마크업이 DOM에 있을 때만)
  function _syncGridLabel() {
    const label = document.getElementById('floatStpGridLabel');
    if (!label) return;
    const isOpen = overlay.classList.contains('is-open');
    label.textContent = isOpen ? 'Hide Grid' : 'Show Grid';
  }

  // ═══════════════════════════════════════════════
  // SQL 실제 실행 — 자동 래퍼 + /api/exec + 그리드 렌더링
  // ═══════════════════════════════════════════════

  const sgpBody   = document.getElementById('sgpBody');
  const sgpQuery  = document.getElementById('sgpQuery');
  const sgpStats  = document.getElementById('sgpStats');
  const sgpVerb   = document.getElementById('sgpVerb');
  const sgpDimens = document.getElementById('sgpDimens');

  // ═══════════════════════════════════════════════════════════
  // copy / csv export — 마지막 SELECT 결과를 보관하고 직렬화
  // ═══════════════════════════════════════════════════════════
  // 마지막으로 그리드에 렌더된 query 결과
  // shape: { columns: [...], rows: [[...], ...], sql: "..." }
  // SELECT 외 (DML/DDL/error/empty) 상태에서는 null
  let _lastResult = null;
  let _lastError  = null;

  // ── 셀 값 → 문자열 변환 (null/undefined → 빈 문자열) ──
  function _cellToStr(v) {
    if (v === null || v === undefined) return '';
    return String(v);
  }

  // ── TSV 직렬화 (clipboard용) ──
  // 탭 구분, 셀 내부 탭/개행은 공백으로 치환 (엑셀 호환)
  function _toTSV(cols, rows) {
    const escCell = (v) => _cellToStr(v).replace(/[\t\r\n]+/g, ' ');
    const lines = [];
    lines.push(cols.map(escCell).join('\t'));
    for (const r of rows) {
      lines.push(r.map(escCell).join('\t'));
    }
    return lines.join('\n');
  }

  // ── CSV 직렬화 (RFC 4180 준수) ──
  // 쉼표/따옴표/개행 포함된 셀은 ""로 감싸고 내부 "는 ""로 escape
  function _toCSV(cols, rows) {
    const escCell = (v) => {
      const s = _cellToStr(v);
      if (s === '') return '';
      if (/[",\r\n]/.test(s)) {
        return '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    };
    const lines = [];
    lines.push(cols.map(escCell).join(','));
    for (const r of rows) {
      lines.push(r.map(escCell).join(','));
    }
    return lines.join('\r\n');  // CSV는 CRLF가 표준
  }

  // ── 토스트 (그리드 헤더 영역에 잠깐 표시) ──
  let _toastTimer = null;
  function _sgpToast(msg, kind) {
    const existing = document.getElementById('sgpToast');
    if (existing) existing.remove();
    if (_toastTimer) { clearTimeout(_toastTimer); _toastTimer = null; }
    const t = document.createElement('div');
    t.id = 'sgpToast';
    t.className = 'sgp-toast' + (kind ? ' sgp-toast-' + kind : '');
    t.textContent = msg;
    // 그리드 패널 안에 띄우기 (overlay 안)
    const panel = document.getElementById('sqlGridPanel');
    if (panel) panel.appendChild(t);
    _toastTimer = setTimeout(() => {
      t.classList.add('sgp-toast-fade');
      setTimeout(() => t.remove(), 250);
    }, 1500);
  }

  // ── 클립보드 복사 (모바일 호환) ──
  async function _copyToClipboard(text) {
    // 1차: execCommand (동기 — user gesture 컨텍스트에서 즉시 실행, Samsung Browser 호환)
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
      document.body.appendChild(ta);
      ta.focus();
      ta.setSelectionRange(0, ta.value.length);
      const ok = document.execCommand('copy');
      ta.remove();
      if (ok) return true;
    } catch (e) { /* fall through */ }
    // 2차: Clipboard API (async — gesture 만료 시 실패 가능)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (e) { /* fall through */ }
    }
    return false;
  }

  // ── 파일 다운로드 ──
  function _downloadFile(filename, content, mimeType) {
    const BOM = '\uFEFF';  // 엑셀에서 한글 안 깨지게
    const blob = new Blob([BOM + content], { type: mimeType + ';charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }

  // ── 파일명 생성 (sql_result_YYYYMMDD_HHMMSS.csv) ──
  function _makeFilename(ext) {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
    return `sql_result_${ts}.${ext}`;
  }

  // ── copy 버튼 동작 ──
  async function _doCopy() {
    // 정상 결과: TSV 복사
    if (_lastResult && _lastResult.columns && _lastResult.rows) {
      const tsv = _toTSV(_lastResult.columns, _lastResult.rows);
      // 내부 클립보드 동기화 — CTRL+PASTE / LIST 모달에서 사용
      try { window.NavBlock?.setClipData?.(tsv); } catch(e){}
      try { window.NavClipboard?.push?.(tsv); } catch(e){}
      const ok = await _copyToClipboard(tsv);
      const n = _lastResult.rows.length;
      _sgpToast(ok ? `Copied ${n} row${n===1?'':'s'} (TSV)` : 'Copy failed — try selecting manually', ok ? 'ok' : 'warn');
      return;
    }
    // 에러 상태: 에러 메시지 + traceback 복사
    if (_lastError) {
      const parts = [];
      parts.push('[SQL ERROR]');
      if (_lastError.error) parts.push(_lastError.error);
      if (_lastError.traceback) parts.push('', _lastError.traceback);
      if (_lastError.sql) parts.push('', '[SQL]', _lastError.sql);
      const text = parts.join('\n');
      try { window.NavBlock?.setClipData?.(text); } catch(e){}
      try { window.NavClipboard?.push?.(text); } catch(e){}
      const ok = await _copyToClipboard(text);
      _sgpToast(ok ? 'Error copied' : 'Copy failed — try selecting manually', ok ? 'ok' : 'warn');
      return;
    }
    _sgpToast('No data to copy', 'warn');
  }

  // ── csv 버튼 동작 ──
  function _doCsv() {
    if (!_lastResult || !_lastResult.columns || !_lastResult.rows) {
      _sgpToast('No data to export', 'warn');
      return;
    }
    const csv = _toCSV(_lastResult.columns, _lastResult.rows);
    const filename = _makeFilename('csv');
    try {
      _downloadFile(filename, csv, 'text/csv');
      const n = _lastResult.rows.length;
      _sgpToast(`Exported ${n} row${n === 1 ? '' : 's'} → ${filename}`, 'ok');
    } catch (e) {
      _sgpToast('Export failed: ' + e.message, 'warn');
    }
  }

  // ── HTML escape ──
  function _esc(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ── 첫 키워드 추출 (SELECT/INSERT/...) ──
  function _firstVerb(sql) {
    const m = String(sql || '').trim().match(/^(--[^\n]*\n|\/\*[\s\S]*?\*\/|\s)*([A-Za-z]+)/);
    return m ? m[2].toUpperCase() : '';
  }

  // ── Python 자동 래퍼 빌드 ──
  // 사용자 SQL을 Python 코드로 감싸서 /api/exec에 보냄
  // 결과는 stdout에 __SQL_RESULT__{json} / __SQL_ERROR__{json} 마커로 출력
  function _buildSqlWrapper(sqlText, paramStr) {
    // SQL을 base64로 안전하게 임베드 (어떤 따옴표/특수문자도 절대 안 깨짐)
    // - btoa는 ASCII만 받으므로 TextEncoder로 UTF-8 바이트화 후 base64
    const _utf8  = new TextEncoder().encode(String(sqlText));
    let _bin = '';
    for (let i = 0; i < _utf8.length; i++) _bin += String.fromCharCode(_utf8[i]);
    const sqlB64 = btoa(_bin);
    return `import json as _json, time as _time, traceback as _tb, base64 as _b64
try:
    from usekit import u as _u
except Exception as _e:
    print("__SQL_ERROR__" + _json.dumps({
        "error": "usekit not available: " + str(_e),
        "traceback": ""
    }))
else:
    _SQL = _b64.b64decode("${sqlB64}").decode("utf-8")
    _stripped = _SQL.strip()
    # 첫 키워드 (DDL vs DML/Query 판별)
    _kw = ""
    for _tok in _stripped.split(None, 1):
        _kw = _tok.upper().strip(';')
        break
    _is_ddl = _kw in ("CREATE", "DROP", "ALTER", "TRUNCATE")

    _t0 = _time.time()
    try:
        if _is_ddl:
            _u.xdb(_stripped)
            _ms = int((_time.time() - _t0) * 1000)
            print("__SQL_RESULT__" + _json.dumps({
                "kind": "ddl", "verb": _kw,
                "elapsed_ms": _ms, "sql": _SQL
            }))
        else:
            _KWARGS = ${paramStr || "{}"}
            _result = _u.xsb(_stripped, **_KWARGS)
            _ms = int((_time.time() - _t0) * 1000)

            # 결과 형태 판별: list of rows (SELECT) / None or int (DML)
            if isinstance(_result, list) and _result:
                _first = _result[0]
                # namedtuple 우선 (sql_variable_demo.py 기반)
                if hasattr(_first, '_fields'):
                    _cols = list(_first._fields)
                    _rows = [list(r) for r in _result]
                elif isinstance(_first, dict):
                    _cols = list(_first.keys())
                    _rows = [[r.get(c) for c in _cols] for r in _result]
                elif hasattr(_first, '__dict__'):
                    _cols = [k for k in vars(_first).keys() if not k.startswith('_')]
                    _rows = [[getattr(r, c, None) for c in _cols] for r in _result]
                else:
                    # 튜플/리스트만 — 컬럼명 없음
                    _cols = ["col" + str(i+1) for i in range(len(_first))]
                    _rows = [list(r) for r in _result]
                print("__SQL_RESULT__" + _json.dumps({
                    "kind": "query", "verb": _kw,
                    "columns": _cols, "rows": _rows,
                    "elapsed_ms": _ms, "sql": _SQL
                }, default=str))
            elif isinstance(_result, list):
                # 빈 리스트 = 0 rows
                print("__SQL_RESULT__" + _json.dumps({
                    "kind": "query", "verb": _kw,
                    "columns": [], "rows": [],
                    "elapsed_ms": _ms, "sql": _SQL
                }))
            else:
                # DML (INSERT/UPDATE/DELETE) — affected rows 추정
                _affected = _result if isinstance(_result, int) else None
                print("__SQL_RESULT__" + _json.dumps({
                    "kind": "dml", "verb": _kw,
                    "affected": _affected,
                    "elapsed_ms": _ms, "sql": _SQL
                }))
    except Exception as _e:
        print("__SQL_ERROR__" + _json.dumps({
            "error": str(_e),
            "traceback": _tb.format_exc()
        }))
`;
  }

  // ═════════════════════════════════════════════════════════════
  // 메타 테이블 wrapper — 테이블 목록 + 통계 + 행수 한방
  // ═════════════════════════════════════════════════════════════
  function _buildMetaTablesWrapper() {
    return `import json as _json, time as _time, traceback as _tb
try:
    from usekit import u as _u
except Exception as _e:
    print("__SQL_ERROR__" + _json.dumps({
        "error": "usekit not available: " + str(_e),
        "traceback": ""
    }))
else:
    _t0 = _time.time()
    try:
        # 1단계: 테이블 메타 (한방 SQL)
        _meta_sql = """
            SELECT
              m.name AS name,
              (SELECT COUNT(*) FROM pragma_table_info(m.name))                        AS cols,
              (SELECT COUNT(*) FROM pragma_table_info(m.name) WHERE pk > 0)           AS pk,
              (SELECT COUNT(*) FROM pragma_table_info(m.name) WHERE "notnull" = 1)    AS nn,
              (SELECT COUNT(*) FROM pragma_foreign_key_list(m.name))                  AS fk,
              (SELECT COUNT(*) FROM sqlite_master
                 WHERE type='index' AND tbl_name=m.name
                   AND name NOT LIKE 'sqlite_autoindex%')                             AS idx
            FROM sqlite_master m
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY m.name
        """
        _meta = _u.xsb(_meta_sql)

        # 2단계: 각 테이블 행수 (Python 루프 — 동적 SQL 한계 회피)
        _cols  = ["name", "cols", "rows", "pk", "nn", "fk", "idx"]
        _rows  = []
        for _r in (_meta or []):
            # row가 namedtuple/dict 어느 쪽이든 안전하게 꺼냄
            if hasattr(_r, '_fields'):
                _name = _r.name
                _c    = _r.cols
                _pk   = _r.pk
                _nn   = _r.nn
                _fk   = _r.fk
                _ix   = _r.idx
            elif isinstance(_r, dict):
                _name = _r.get('name')
                _c    = _r.get('cols')
                _pk   = _r.get('pk')
                _nn   = _r.get('nn')
                _fk   = _r.get('fk')
                _ix   = _r.get('idx')
            else:
                _name, _c, _pk, _nn, _fk, _ix = _r[0], _r[1], _r[2], _r[3], _r[4], _r[5]

            # 행수 — 실패해도 전체는 진행 (None 표시)
            try:
                _safe = str(_name).replace('"', '""')
                _cnt  = _u.xsb('SELECT COUNT(*) AS c FROM "' + _safe + '"')
                if _cnt and hasattr(_cnt[0], '_fields'):
                    _n = _cnt[0].c
                elif _cnt and isinstance(_cnt[0], dict):
                    _n = _cnt[0].get('c')
                elif _cnt:
                    _n = _cnt[0][0]
                else:
                    _n = None
            except Exception:
                _n = None

            _rows.append([_name, _c, _n, _pk, _nn, _fk, _ix])

        _ms = int((_time.time() - _t0) * 1000)
        print("__SQL_RESULT__" + _json.dumps({
            "kind": "query", "verb": "META",
            "columns": _cols, "rows": _rows,
            "elapsed_ms": _ms,
            "sql": "META: tables (cols/rows/pk/nn/fk/idx)"
        }, default=str))
    except Exception as _e:
        print("__SQL_ERROR__" + _json.dumps({
            "error": str(_e),
            "traceback": _tb.format_exc()
        }))
`;
  }

  // 메타 테이블 실행 — 신규 wrapper 사용
  async function _executeMetaTables() {
    openGrid();
    _renderLoading("META: tables (cols/rows/pk/nn/fk/idx)", { kind: 'meta', metaKind: 'tables' });

    const code = _buildMetaTablesWrapper();
    try {
      const res = await fetch('/api/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, inputs: [], timeout: 30 }),
      });
      const json = await res.json();

      if (!json.ok && !json.stdout) {
        _renderError({
          error: json.error || 'Server error',
          traceback: json.stderr || ''
        }, '');
        return;
      }

      const parsed = _parseSqlOutput(json.stdout);
      if (!parsed) {
        _renderError({
          error: 'No SQL result marker found in output',
          traceback: 'stdout:\n' + (json.stdout || '(empty)') + '\n\nstderr:\n' + (json.stderr || '(empty)')
        }, '');
        return;
      }
      if (!parsed.ok) {
        if (parsed.parseError) {
          _renderError({
            error: 'Failed to parse meta result: ' + parsed.parseError,
            traceback: parsed.raw || ''
          }, '');
        } else {
          _renderError(parsed.data, '');
        }
        return;
      }

      const data = parsed.data;
      data._context = { kind: 'meta', metaKind: 'tables' };
      _renderQuery(data);
    } catch (e) {
      _renderError({
        error: 'Network/fetch failed: ' + e.message,
        traceback: 'The dev server may be down.'
      }, '');
    }
  }

  // ═════════════════════════════════════════════════════════════
  // 배치 래퍼 — 여러 statement를 하나씩 u.xsb/xdb에 넘김
  // (u.xsb는 "one statement at a time"만 지원)
  // ═════════════════════════════════════════════════════════════
  function _buildSqlBatchWrapper(statementsArray) {
    // statements 배열을 base64로 안전하게 전달
    const stmtsJson = JSON.stringify(statementsArray);
    const _utf8 = new TextEncoder().encode(stmtsJson);
    let _bin = '';
    for (let i = 0; i < _utf8.length; i++) _bin += String.fromCharCode(_utf8[i]);
    const stmtsB64 = btoa(_bin);
    return `import json as _json, time as _time, traceback as _tb, base64 as _b64
try:
    from usekit import u as _u
except Exception as _e:
    print("__SQL_ERROR__" + _json.dumps({"error":"usekit not available: "+str(_e),"traceback":""}))
else:
    _STATEMENTS = _json.loads(_b64.b64decode("${stmtsB64}").decode("utf-8"))
    _results = []
    _t0 = _time.time()
    _last_query_data = None

    for _idx, _sql_raw in enumerate(_STATEMENTS):
        _sql = _sql_raw.strip()
        if not _sql:
            continue
        _kw = ""
        for _tok in _sql.split(None, 1):
            _kw = _tok.upper().strip(";")
            break
        _is_ddl = _kw in ("CREATE", "DROP", "ALTER", "TRUNCATE")
        _stmt_t0 = _time.time()
        try:
            if _is_ddl:
                _u.xdb(_sql)
                _ms_s = int((_time.time() - _stmt_t0) * 1000)
                _results.append({"kind":"ddl","verb":_kw,"elapsed_ms":_ms_s,"sql":_sql,"stmt_index":_idx})
            else:
                _result = _u.xsb(_sql)
                _ms_s = int((_time.time() - _stmt_t0) * 1000)
                if isinstance(_result, list) and _result:
                    _first = _result[0]
                    if hasattr(_first, "_fields"):
                        _cols = list(_first._fields)
                        _rows = [list(r) for r in _result]
                    elif isinstance(_first, dict):
                        _cols = list(_first.keys())
                        _rows = [[r.get(c) for c in _cols] for r in _result]
                    elif hasattr(_first, "__dict__"):
                        _cols = [k for k in vars(_first).keys() if not k.startswith("_")]
                        _rows = [[getattr(r, c, None) for c in _cols] for r in _result]
                    else:
                        _cols = ["col" + str(i+1) for i in range(len(_first))]
                        _rows = [list(r) for r in _result]
                    _data = {"kind":"query","verb":_kw,"columns":_cols,"rows":_rows,
                             "elapsed_ms":_ms_s,"sql":_sql,"stmt_index":_idx}
                    _results.append(_data)
                    _last_query_data = _data
                elif isinstance(_result, list):
                    _data = {"kind":"query","verb":_kw,"columns":[],"rows":[],
                             "elapsed_ms":_ms_s,"sql":_sql,"stmt_index":_idx}
                    _results.append(_data)
                    _last_query_data = _data
                else:
                    _affected = _result if isinstance(_result, int) else None
                    _results.append({"kind":"dml","verb":_kw,"affected":_affected,
                                     "elapsed_ms":_ms_s,"sql":_sql,"stmt_index":_idx})
        except Exception as _e:
            _results.append({"kind":"error","verb":_kw,"error":str(_e),
                             "traceback":_tb.format_exc(),"sql":_sql,"stmt_index":_idx})
            break

    _total_ms = int((_time.time() - _t0) * 1000)
    _last_kind = _results[-1]["kind"] if _results else None
    print("__SQL_BATCH_RESULT__" + _json.dumps({
        "results": _results,
        "total_elapsed_ms": _total_ms,
        "total_requested": len(_STATEMENTS),
        "total_executed": len(_results),
        "last_kind": _last_kind,
        "last_query": _last_query_data,
    }, default=str))
`;
  }

  // ── stdout에서 마커 파싱 (단일 + 배치 둘 다 지원) ──
  function _parseSqlOutput(stdout) {
    if (!stdout) return null;
    const lines = stdout.split('\n');
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i];
      if (line.startsWith('__SQL_BATCH_RESULT__')) {
        try { return { ok: true, batch: true, data: JSON.parse(line.slice(20)) }; }
        catch (e) { return { ok: false, parseError: e.message, raw: line }; }
      }
      if (line.startsWith('__SQL_RESULT__')) {
        try { return { ok: true, data: JSON.parse(line.slice(14)) }; }
        catch (e) { return { ok: false, parseError: e.message, raw: line }; }
      }
      if (line.startsWith('__SQL_ERROR__')) {
        try { return { ok: false, data: JSON.parse(line.slice(13)) }; }
        catch (e) { return { ok: false, parseError: e.message, raw: line }; }
      }
    }
    return null;
  }

  // ── 메타/푸터 업데이트 ──
  function _updateMeta(query, statsText, verb, dimText) {
    if (sgpQuery)  sgpQuery.textContent  = query  || '—';
    if (sgpStats)  sgpStats.textContent  = statsText || '—';
    if (sgpVerb) {
      sgpVerb.textContent = verb || '—';
      if (verb) sgpVerb.setAttribute('data-verb', verb);
      else      sgpVerb.removeAttribute('data-verb');
    }
    if (sgpDimens) sgpDimens.textContent = dimText || '—';
  }

  // ── 렌더: 로딩 ──
  function _renderLoading(sql, context) {
    _lastResult = null;  // 새 실행 시작 → 이전 결과 무효화
    _lastError  = null;
    sgpBody.innerHTML = `
      <div class="sgp-loading">
        <div class="sgp-spinner"></div>
        <div class="sgp-loading-text">Executing...</div>
      </div>`;
    const queryOneLine = sql.trim().split('\n')[0].slice(0, 200);
    let statsLine = 'running...';
    if (context && context.kind === 'current' && context.stmtTotal > 1) {
      statsLine = `running stmt ${context.stmtIndex + 1}/${context.stmtTotal}...`;
    } else if (context && context.kind === 'batch' && context.total > 1) {
      statsLine = `running ${context.total} statements...`;
    }
    _updateMeta(queryOneLine, statsLine, _firstVerb(sql), '—');
  }

  // ── 렌더: 빈 상태 ──
  function _renderEmpty() {
    _lastResult = null;
    sgpBody.innerHTML = `
      <div class="sgp-empty">
        <div class="sgp-empty-icon">▦</div>
        <div class="sgp-empty-text">No result yet</div>
        <div class="sgp-empty-hint">Tap <b>◆ SQL</b> to execute the editor content</div>
      </div>`;
    _updateMeta('(no query yet)', '—', '', '—');
  }

  // ═══════════════════════════════════════════════
  // 그리드 셀 액션 메뉴 (Cell / Row / Meta Tables)
  // ═══════════════════════════════════════════════

  // 공통 액션 메뉴 팝업 (anchor 근처에 표시)
  function _showCellActionMenu(title, items, anchorEl) {
    let overlay = document.getElementById('_cellActionMenu');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = '_cellActionMenu';
      overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;' +
        'z-index:9998;display:flex;align-items:flex-start;justify-content:flex-start;';
      document.body.appendChild(overlay);
    }
    const closeMenu = () => { overlay.style.display = 'none'; };
    overlay.onclick = (e) => { if (e.target === overlay) closeMenu(); };

    const itemHtml = items.map((it, i) =>
      `<button data-i="${i}" style="display:block;width:100%;text-align:left;padding:0.55rem 0.9rem;
        background:transparent;border:none;border-top:${i === 0 ? 'none' : '1px solid rgba(0,0,0,0.06)'};
        color:#2a2010;font-size:0.88rem;cursor:pointer;">${_esc(it.label)}</button>`
    ).join('');

    overlay.innerHTML = `
      <div id="_camBox" style="position:absolute;background:#fffaf0;border:1px solid rgba(180,140,60,0.3);
           border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.25);min-width:180px;max-width:260px;
           overflow:hidden;">
        <div style="padding:0.4rem 0.9rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;
             color:#8b6f2f;background:rgba(220,170,90,0.12);border-bottom:1px solid rgba(180,140,60,0.15);
             white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${_esc(title)}</div>
        ${itemHtml}
      </div>`;
    overlay.style.display = 'flex';

    // anchor 근처에 위치
    const box = overlay.querySelector('#_camBox');
    const r = anchorEl.getBoundingClientRect();
    const vw = window.innerWidth, vh = window.innerHeight;
    let left = r.left, top = r.bottom + 4;
    const bw = box.offsetWidth || 200;
    const bh = box.offsetHeight || 160;
    if (left + bw > vw - 8) left = vw - bw - 8;
    if (left < 8) left = 8;
    if (top + bh > vh - 8) top = r.top - bh - 4;  // 위로 뒤집기
    if (top < 8) top = 8;
    box.style.left = left + 'px';
    box.style.top  = top + 'px';

    overlay.querySelectorAll('[data-i]').forEach(btn => {
      btn.onclick = () => {
        const i = parseInt(btn.dataset.i);
        closeMenu();
        try { items[i].onClick?.(); } catch (e) { console.error(e); }
      };
    });
  }

  // 셀 클릭 → 액션 메뉴
  function _bindGridCellActions(body, cols, rows, ctx) {
    const table = body.querySelector('table.sgp-grid');
    if (!table) return;
    const isMeta = ctx && ctx.kind === 'meta';
    const metaKind = ctx && ctx.metaKind;

    table.addEventListener('click', (e) => {
      // 컬럼 헤더(th) 클릭 — 모든 결과(쿼리 + 메타) 공통
      const th = e.target.closest('th');
      if (th && th.dataset.ci !== undefined) {
        const ci = parseInt(th.dataset.ci);
        if (ci < 0 || ci >= cols.length) return;
        const colName = cols[ci] || '';
        // 세로 연결: 각 행의 ci 컬럼 값 (NULL/undefined는 빈 문자열, 탭/개행은 공백 치환)
        const colValues = rows.map(r => {
          const v = r[ci];
          if (v === null || v === undefined) return '';
          return String(v).replace(/\t/g, ' ').replace(/\n/g, ' ');
        }).join('\n');
        _showCellActionMenu(`Column: ${colName}`, [
          { label: 'Copy column values', onClick: () => _copyText(colValues, `Column copied (${rows.length} values)`) },
          { label: 'Copy column name',   onClick: () => _copyText(colName, 'Column name copied') },
          { label: 'Write column name',  onClick: () => _writeToEditor(colName, `Written: ${colName}`) },
        ], th);
        return;
      }

      const td = e.target.closest('td');
      if (!td) return;

      // 행번호 클릭
      if (td.dataset.rownum) {
        const tr = td.closest('tr');
        const ri = parseInt(tr?.dataset.r ?? '-1');
        if (ri < 0) return;
        const row = rows[ri];
        if (!row) return;
        _showCellActionMenu(`Row #${ri + 1}`, [
          { label: 'Copy row (TSV)',  onClick: () => _copyRowTSV(cols, row) },
          { label: 'Copy row (JSON)', onClick: () => _copyRowJSON(cols, row) },
        ], td);
        return;
      }

      // 일반 셀 클릭
      const ri = parseInt(td.dataset.r ?? '-1');
      const ci = parseInt(td.dataset.c ?? '-1');
      if (ri < 0 || ci < 0) return;
      const val = rows[ri]?.[ci];
      const colName = cols[ci] || '';

      // Meta Tables 결과의 NAME 컬럼: Columns view / Drop table + 일반 Copy 메뉴 병합
      if (isMeta && metaKind === 'tables' && colName === 'name') {
        const tableName = String(val);
        _showCellActionMenu(`Table: ${tableName}`, [
          { label: 'Columns view',     onClick: () => _metaShowColumns(tableName) },
          { label: 'Drop table',       onClick: () => _metaDropTable(tableName) },
          { label: 'Copy value',       onClick: () => _copyText(val === null || val === undefined ? '' : String(val), 'Value copied') },
          { label: 'Write value',      onClick: () => _writeToEditor(val === null || val === undefined ? '' : String(val), `Written: ${tableName}`) },
          { label: 'Copy column name', onClick: () => _copyText(colName, 'Column name copied') },
          { label: 'Write column name', onClick: () => _writeToEditor(colName, `Written: ${colName}`) },
          { label: 'Copy row (TSV)',   onClick: () => _copyRowTSV(cols, rows[ri]) },
        ], td);
        return;
      }

      // 일반 셀: Copy value / Write value / Copy column / Copy row
      const preview = val === null || val === undefined ? 'NULL' : String(val).slice(0, 40);
      const valStr = val === null || val === undefined ? '' : String(val);
      _showCellActionMenu(`${colName}: ${preview}`, [
        { label: 'Copy value',       onClick: () => _copyText(valStr, 'Value copied') },
        { label: 'Write value',      onClick: () => _writeToEditor(valStr, `Written: ${preview.length > 25 ? preview.slice(0,25) + '…' : preview}`) },
        { label: 'Copy column name', onClick: () => _copyText(colName, 'Column name copied') },
        { label: 'Write column name', onClick: () => _writeToEditor(colName, `Written: ${colName}`) },
        { label: 'Copy row (TSV)',   onClick: () => _copyRowTSV(cols, rows[ri]) },
      ], td);
    });
  }

  // 복사 헬퍼
  async function _copyText(text, toastMsg) {
    const t = String(text ?? '');
    try { window.NavBlock?.setClipData?.(t); } catch(e){}
    try { window.NavClipboard?.push?.(t); } catch(e){}
    const ok = await _copyToClipboard(t);
    _sgpToast(ok ? (toastMsg || 'Copied') : 'Copy failed', ok ? 'ok' : 'warn');
  }
  async function _copyRowTSV(cols, row) {
    const line = row.map(v => (v === null || v === undefined) ? '' : String(v).replace(/\t/g, ' ').replace(/\n/g, ' ')).join('\t');
    try { window.NavBlock?.setClipData?.(line); } catch(e){}
    try { window.NavClipboard?.push?.(line); } catch(e){}
    const ok = await _copyToClipboard(line);
    _sgpToast(ok ? 'Row copied (TSV)' : 'Copy failed', ok ? 'ok' : 'warn');
  }
  async function _copyRowJSON(cols, row) {
    const obj = {};
    cols.forEach((c, i) => { obj[c] = row[i] ?? null; });
    const json = JSON.stringify(obj, null, 2);
    try { window.NavBlock?.setClipData?.(json); } catch(e){}
    try { window.NavClipboard?.push?.(json); } catch(e){}
    const ok = await _copyToClipboard(json);
    _sgpToast(ok ? 'Row copied (JSON)' : 'Copy failed', ok ? 'ok' : 'warn');
  }

  // ── Write to Editor ──
  function _writeToEditor(text, toastMsg) {
    const s = String(text ?? '');
    let inserted = false;
    try {
      // 멀티커서(블록) 모드 → editAll
      if (window._uiIsBlockMode?.() && window.NavBlockV2?.editAll) {
        window.NavBlockV2.editAll('insert', s);
        inserted = true;
      }
    } catch (e) { console.warn('[Write] editAll failed', e); }
    if (!inserted) {
      // 단일커서 → replaceSelection (scrollIntoView 내장)
      try {
        if (window.Editor?.replaceSelection) {
          window.Editor.replaceSelection(s);
          inserted = true;
        }
      } catch (e) { console.warn('[Write] replaceSelection failed', e); }
    }
    _sgpToast(inserted ? (toastMsg || 'Written') : 'Write failed', inserted ? 'ok' : 'warn');
  }

  // Meta 액션 핸들러 (stub — Columns/Drop 구현)
  function _metaShowColumns(tableName) {
    const safeName = String(tableName).replace(/"/g, '""');
    _executeSql(`PRAGMA table_info("${safeName}")`,
      { kind: 'meta', metaKind: 'columns', tableName });
  }
  function _metaDropTable(tableName) {
    // 2차 확인 팝업 (간이)
    if (!window.confirm) return;
    const ok = window.confirm(`Drop table "${tableName}"?\n\nThis cannot be undone.`);
    if (!ok) return;
    const safeName = String(tableName).replace(/"/g, '""');
    _executeSql(`DROP TABLE "${safeName}"`, { kind: 'meta', metaKind: 'drop', tableName });
  }

  // ── 렌더: SELECT 결과 (그리드) ──
  function _renderQuery(data) {
    const cols = data.columns || [];
    const rows = data.rows || [];
    const sql  = (data.sql || '').replace(/\s+/g, ' ').trim();

    // ★ copy/csv용 결과 보관 (0행이어도 컬럼 헤더는 export 가능)
    _lastResult = { columns: cols, rows: rows, sql: data.sql || '' };
    _lastError = null;

    if (cols.length === 0 && rows.length === 0) {
      sgpBody.innerHTML = `
        <div class="sgp-empty">
          <div class="sgp-empty-icon">⊘</div>
          <div class="sgp-empty-text">0 rows returned</div>
          <div class="sgp-empty-hint">Query executed successfully but returned no rows</div>
        </div>`;
      const ctx0 = data._context;
      const ctxHint0 = (ctx0 && ctx0.kind === 'current' && ctx0.stmtTotal > 1)
        ? ` · stmt ${ctx0.stmtIndex + 1}/${ctx0.stmtTotal}` : '';
      _updateMeta(sql, `0 rows · ${data.elapsed_ms || 0}ms${ctxHint0}`, data.verb || 'SELECT', `0 ROWS × ${cols.length} COLS`);
      return;
    }

    // 숫자 컬럼 자동 감지 (모든 비-null 값이 number이면 num 클래스)
    const isNumCol = cols.map((_, ci) => {
      let allNum = true, sawAny = false;
      for (const r of rows) {
        const v = r[ci];
        if (v === null || v === undefined) continue;
        sawAny = true;
        if (typeof v !== 'number') { allNum = false; break; }
      }
      return sawAny && allNum;
    });

    let html = '<table class="sgp-grid"><thead><tr>';
    html += '<th class="rownum">#</th>';
    cols.forEach((c, i) => {
      const cls = isNumCol[i] ? ' class="num-col"' : '';
      html += `<th${cls} data-ci="${i}">${_esc(c)}</th>`;
    });
    html += '</tr></thead><tbody>';
    rows.forEach((r, ri) => {
      html += `<tr data-r="${ri}"><td class="rownum" data-rownum="1">${ri + 1}</td>`;
      r.forEach((v, ci) => {
        if (v === null || v === undefined) {
          html += `<td class="is-null" data-r="${ri}" data-c="${ci}">NULL</td>`;
        } else if (isNumCol[ci]) {
          html += `<td class="num" data-r="${ri}" data-c="${ci}">${_esc(v)}</td>`;
        } else {
          html += `<td data-r="${ri}" data-c="${ci}">${_esc(v)}</td>`;
        }
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    sgpBody.innerHTML = html;

    // 셀/행번호 클릭 → 액션 메뉴
    const ctxCurrent = data._context;
    _bindGridCellActions(sgpBody, cols, rows, ctxCurrent);

    const ctx = data._context;
    const ctxHint = (ctx && ctx.kind === 'current' && ctx.stmtTotal > 1)
      ? ` · stmt ${ctx.stmtIndex + 1}/${ctx.stmtTotal}` : '';
    _updateMeta(
      sql,
      `${rows.length} rows · ${data.elapsed_ms || 0}ms${ctxHint}`,
      data.verb || 'SELECT',
      `${rows.length} ROWS × ${cols.length} COLS`
    );
  }

  // ── 렌더: DML/DDL 성공 ──
  function _renderDml(data) {
    _lastResult = null;
    const sql = (data.sql || '').replace(/\s+/g, ' ').trim();
    const verb = data.verb || (data.kind === 'ddl' ? 'DDL' : 'DML');
    let mainText, subText;
    if (data.kind === 'ddl') {
      mainText = `${verb} executed`;
      // 메타 유지보수 명령은 스키마 변경이 아니므로 전용 문구 사용
      if      (verb === 'VACUUM')  subText = 'Database optimized';
      else if (verb === 'ANALYZE') subText = 'Statistics updated';
      else {
        subText = 'Schema changed successfully';
        // DDL 성공 → SQL 자동완성 스키마 갱신
        if (window.SqlComplete) window.SqlComplete.reloadSchema();
      }
    } else {
      mainText = `${verb} executed`;
      subText = data.affected != null
        ? `${data.affected} row${data.affected === 1 ? '' : 's'} affected`
        : 'No rows returned';
    }
    sgpBody.innerHTML = `
      <div class="sgp-dml-ok">
        <div class="sgp-dml-icon">✓</div>
        <div class="sgp-dml-text">${_esc(mainText)}</div>
        <div class="sgp-dml-sub">${_esc(subText)}</div>
      </div>`;
    const ctxD = data._context;
    const ctxHintD = (ctxD && ctxD.kind === 'current' && ctxD.stmtTotal > 1)
      ? ` · stmt ${ctxD.stmtIndex + 1}/${ctxD.stmtTotal}` : '';
    _updateMeta(
      sql,
      `${data.elapsed_ms || 0}ms${ctxHintD}`,
      verb,
      data.affected != null ? `${data.affected} affected` : '—'
    );
  }

  // ── 렌더: 에러 ──
  // ── 실행문 범위 플래시 하이라이트 ──
  let _flashMark = null;
  function _flashStatementRange(from, to) {
    try {
      const view = window.Editor?.get?.();
      if (!view) return;
      // CSS 클래스 기반 mark decoration
      const { Decoration, ViewPlugin, StateEffect } = CM6 || {};
      if (!Decoration) return;

      // 간단한 방식: selection으로 범위 표시 후 복귀
      const savedSel = view.state.selection;
      view.dispatch({
        selection: { anchor: from, head: to },
        scrollIntoView: true,
      });
      // 800ms 후 원래 selection 복귀
      clearTimeout(_flashMark);
      _flashMark = setTimeout(() => {
        try {
          view.dispatch({ selection: savedSel });
        } catch (e) { /* 편집 중 변경되었을 수 있음 */ }
      }, 800);
    } catch (e) {
      console.warn('[SqlView] flash range failed:', e);
    }
  }

  function _renderError(errData, sqlText) {
    _lastResult = null;
    const errMsg = errData?.error || 'Unknown error';
    const trace  = errData?.traceback || '';
    _lastError = { error: errMsg, traceback: trace, sql: sqlText || '' };

    // 에러 토큰에서 위치 찾기 — near "XXX" 패턴
    let jumpHtml = '';
    const nearMatch = errMsg.match(/near\s+"([^"]+)"/i);
    const noTableMatch = errMsg.match(/no such table:\s*(\S+)/i);
    const noColMatch = errMsg.match(/no such column:\s*(\S+)/i);
    const token = nearMatch?.[1] || noTableMatch?.[1] || noColMatch?.[1];

    if (token && window.Editor) {
      const editorText = window.Editor.getText?.() || '';
      const tokenIdx = editorText.indexOf(token);
      if (tokenIdx >= 0) {
        const before = editorText.slice(0, tokenIdx);
        const line = (before.match(/\n/g) || []).length + 1;
        const lastNl = before.lastIndexOf('\n');
        const col = tokenIdx - lastNl;
        jumpHtml = `<div class="sgp-error-jump" style="margin-top:0.5rem;">
          <span style="opacity:0.7;font-size:0.82rem;">Line ${line}, Col ${col} — "<b>${_esc(token)}</b>"</span>
          <button id="sgpErrorJump" class="sgp-error-jump-btn" style="margin-left:0.5rem;padding:0.2rem 0.7rem;border-radius:4px;border:1px solid var(--ac-red-bd,#c44);background:var(--ac-red-bg,rgba(255,80,80,0.1));color:var(--ac-red,#e55);font-size:0.8rem;cursor:pointer;">Jump</button>
        </div>`;
        // Jump 이벤트 — 약간 딜레이 후 바인딩 (innerHTML 후)
        setTimeout(() => {
          document.getElementById('sgpErrorJump')?.addEventListener('click', () => {
            window.Editor.setCursor?.({ line: line - 1, ch: col - 1 });
            window.Editor.focus?.();
            // edit mode이면 grid 축소
            if (_editModeActive) _updateEditPanelHeight();
          });
        }, 50);
      }
    }

    sgpBody.innerHTML = `
      <div class="sgp-error">
        <div class="sgp-error-title">⚠ SQL Error</div>
        <div class="sgp-error-msg">${_esc(errMsg)}</div>
        ${jumpHtml}
        ${trace ? `<div class="sgp-error-trace">${_esc(trace)}</div>` : ''}
      </div>`;
    // Jump 버튼 이벤트 재바인딩 (innerHTML 이후)
    if (token && window.Editor) {
      const editorText = window.Editor.getText?.() || '';
      const tokenIdx = editorText.indexOf(token);
      if (tokenIdx >= 0) {
        const before = editorText.slice(0, tokenIdx);
        const line = (before.match(/\n/g) || []).length + 1;
        const lastNl = before.lastIndexOf('\n');
        const col = tokenIdx - lastNl;
        document.getElementById('sgpErrorJump')?.addEventListener('click', () => {
          window.Editor.setCursor?.({ line: line - 1, ch: col - 1 });
          window.Editor.focus?.();
        });
      }
    }

    const sql = (sqlText || '').replace(/\s+/g, ' ').trim();
    _updateMeta(sql || '—', 'error', 'ERROR', '—');
  }

  // ── 실행 메인 함수 ──
  async function _runSql() {
    // 기존 API 호환 — 전체 에디터 실행
    return _runEntireEditor();
  }

  // ═════════════════════════════════════════════════════════════
  // SQL statement 파서 (; 기반 상태 머신)
  // text: SQL 본체만 (앞쪽 주석/공백 제거 — 실행용)
  // start/end: 원본 offset (에디터 매칭용)
  // ═════════════════════════════════════════════════════════════
  function _parseSqlStatements(text) {
    const stmts = [];
    const s = String(text || '');
    const n = s.length;
    let i = 0, stmtStart = 0;

    // 앞쪽 공백 + 주석 건너뛴 실제 SQL 본체 시작 offset
    function _findSqlStart(start, end) {
      let j = start;
      while (j < end) {
        if (s[j] === ' ' || s[j] === '\t' || s[j] === '\r' || s[j] === '\n') { j++; continue; }
        if (s[j] === '-' && s[j + 1] === '-') {
          while (j < end && s[j] !== '\n') j++;
          continue;
        }
        if (s[j] === '/' && s[j + 1] === '*') {
          j += 2;
          while (j < end && !(s[j] === '*' && s[j + 1] === '/')) j++;
          if (j < end) j += 2;
          continue;
        }
        break;
      }
      return j;
    }

    function _pushStmt(start, end) {
      const sqlStart = _findSqlStart(start, end);
      const body = s.slice(sqlStart, end);
      if (!body.trim()) return;  // 주석/공백만이면 skip
      stmts.push({
        start,               // 원본 offset (에디터 매칭용)
        end,
        textStart: sqlStart, // SQL 본체 시작
        text: body,          // 실행용 — 앞주석 제거됨
      });
    }

    while (i < n) {
      const c = s[i], c2 = s[i + 1];
      // -- line comment
      if (c === '-' && c2 === '-') {
        while (i < n && s[i] !== '\n') i++;
        continue;
      }
      // /* block comment */
      if (c === '/' && c2 === '*') {
        i += 2;
        while (i < n && !(s[i] === '*' && s[i + 1] === '/')) i++;
        if (i < n) i += 2;
        continue;
      }
      // 'single-quoted' (SQL '' escape)
      if (c === "'") {
        i++;
        while (i < n) {
          if (s[i] === "'") {
            if (s[i + 1] === "'") { i += 2; continue; }
            i++; break;
          }
          i++;
        }
        continue;
      }
      // "double-quoted"
      if (c === '"') {
        i++;
        while (i < n) {
          if (s[i] === '"') {
            if (s[i + 1] === '"') { i += 2; continue; }
            i++; break;
          }
          i++;
        }
        continue;
      }
      // statement boundary
      if (c === ';') {
        _pushStmt(stmtStart, i + 1);
        i++;
        stmtStart = i;
        continue;
      }
      i++;
    }
    // 마지막 (세미콜론 없이 끝)
    if (stmtStart < n) {
      _pushStmt(stmtStart, n);
    }
    return stmts;
  }

  function _findStatementAt(text, cursorOffset) {
    const stmts = _parseSqlStatements(text);
    if (stmts.length === 0) return null;
    // 정확히 속한 statement (end는 exclusive)
    for (let i = 0; i < stmts.length; i++) {
      const st = stmts[i];
      if (cursorOffset >= st.start && cursorOffset < st.end) {
        return { index: i, total: stmts.length, ...st };
      }
    }
    // 모든 statement 뒤에 있으면 마지막
    const last = stmts[stmts.length - 1];
    if (cursorOffset >= last.end) {
      return { index: stmts.length - 1, total: stmts.length, ...last };
    }
    // statement 사이 공백 → 다음 statement
    for (let i = 0; i < stmts.length; i++) {
      if (cursorOffset < stmts[i].start) {
        return { index: i, total: stmts.length, ...stmts[i] };
      }
    }
    return { index: 0, total: stmts.length, ...stmts[0] };
  }

  // ═════════════════════════════════════════════════════════════
  // ping 선체크 후 실제 fetch (서버 죽어있을 때 빠른 감지용, 1500ms timeout)
  // — 실패 시 catch로 흘러가도록 throw
  // ═════════════════════════════════════════════════════════════
  async function _sqlFetchWithPing(url, opts) {
    const pr = await fetch('/api/ping', { signal: AbortSignal.timeout(1500) });
    if (!pr.ok) throw new Error('ping_not_ok_' + pr.status);
    return fetch(url, opts);
  }

  // ═════════════════════════════════════════════════════════════
  // 코어 실행 로직 (DRY) — sqlText 주어지면 fetch → 파싱 → 렌더
  // context = { kind: 'all'|'current', stmtIndex, stmtTotal }
  // ═════════════════════════════════════════════════════════════
  async function _executeSql(sqlText, context, paramStr) {
    sqlText = String(sqlText || '').trim();
    if (!sqlText) {
      _renderError({ error: 'Empty SQL — nothing to execute', traceback: '' }, '');
      return;
    }

    openGrid();
    _renderLoading(sqlText, context);

    const code = _buildSqlWrapper(sqlText, paramStr);
    try {
      const res = await _sqlFetchWithPing('/api/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, inputs: [], timeout: 20 }),
      });
      const json = await res.json();

      if (!json.ok && !json.stdout) {
        _renderError({
          error: json.error || 'Server error',
          traceback: json.stderr || ''
        }, sqlText);
        return;
      }

      const parsed = _parseSqlOutput(json.stdout);
      if (!parsed) {
        _renderError({
          error: 'No SQL result marker found in output',
          traceback: 'stdout:\n' + (json.stdout || '(empty)') + '\n\nstderr:\n' + (json.stderr || '(empty)')
        }, sqlText);
        return;
      }

      if (!parsed.ok) {
        if (parsed.parseError) {
          _renderError({
            error: 'Failed to parse SQL result: ' + parsed.parseError,
            traceback: parsed.raw || ''
          }, sqlText);
        } else {
          _renderError(parsed.data, sqlText);
        }
        return;
      }

      // context 정보를 data에 주입해서 렌더 시 활용
      const data = parsed.data;
      if (context) {
        data._context = context;
      }
      // VACUUM/ANALYZE: 메타 명령이므로 빈 쿼리 그리드 대신 DDL 스타일 성공 화면으로
      if (context?.metaKind === 'vacuum' || context?.metaKind === 'analyze') {
        data.kind = 'ddl';
        data.verb = context.metaKind.toUpperCase();
      }
      if (data.kind === 'query') _renderQuery(data);
      else                       _renderDml(data);
    } catch (e) {
      _renderError({
        error: 'Network/fetch failed: ' + e.message,
        traceback: 'The dev server may be down.'
      }, sqlText);
    }
  }

  // ═════════════════════════════════════════════════════════════
  // 배치 실행 — 여러 statement를 하나씩 순차 실행
  // (u.xsb 제약: "one statement at a time")
  // ═════════════════════════════════════════════════════════════
  async function _executeBatch(statementsArray, sourceText) {
    if (!statementsArray || statementsArray.length === 0) {
      _renderError({ error: 'No SQL statements to execute', traceback: '' }, sourceText || '');
      return;
    }

    openGrid();
    // 로딩 표시 — N개 실행 중
    const previewSql = (sourceText || statementsArray[0]).trim().split('\n')[0].slice(0, 200);
    _renderLoading(previewSql, { kind: 'batch', total: statementsArray.length });

    const code = _buildSqlBatchWrapper(statementsArray);
    try {
      const res = await _sqlFetchWithPing('/api/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, inputs: [], timeout: 30 }),
      });
      const json = await res.json();

      if (!json.ok && !json.stdout) {
        _renderError({
          error: json.error || 'Server error',
          traceback: json.stderr || ''
        }, sourceText || '');
        return;
      }

      const parsed = _parseSqlOutput(json.stdout);
      if (!parsed) {
        _renderError({
          error: 'No SQL batch result marker found in output',
          traceback: 'stdout:\n' + (json.stdout || '(empty)') + '\n\nstderr:\n' + (json.stderr || '(empty)')
        }, sourceText || '');
        return;
      }

      if (!parsed.ok) {
        if (parsed.parseError) {
          _renderError({
            error: 'Failed to parse batch result: ' + parsed.parseError,
            traceback: parsed.raw || ''
          }, sourceText || '');
        } else {
          _renderError(parsed.data, sourceText || '');
        }
        return;
      }

      // 배치 결과 렌더링
      if (parsed.batch) {
        _renderBatchResult(parsed.data);
      } else {
        // 혹시 단일 결과가 왔으면 (fallback)
        const data = parsed.data;
        if (data.kind === 'query') _renderQuery(data);
        else                       _renderDml(data);
      }
    } catch (e) {
      _renderError({
        error: 'Network/fetch failed: ' + e.message,
        traceback: 'The dev server may be down.'
      }, sourceText || '');
    }
  }

  // ── 배치 결과 렌더 ──
  // 전략: 마지막 SELECT 결과가 있으면 그리드에 + 메타에 "N/M executed"
  //       에러로 중단됐으면 에러 박스 + 이전 성공 개수
  //       SELECT 없이 DML/DDL만이면 요약 화면
  function _renderBatchResult(batch) {
    const results = batch.results || [];
    const requested = batch.total_requested || 0;
    const executed  = batch.total_executed  || 0;
    const totalMs   = batch.total_elapsed_ms || 0;
    const last      = results[results.length - 1];

    // 에러로 중단
    if (last && last.kind === 'error') {
      _lastResult = null;
      const errStmtIdx = (last.stmt_index ?? 0) + 1;
      const ok = executed - 1;  // 에러 제외하고 성공한 개수
      // 에러 박스 렌더
      sgpBody.innerHTML = `
        <div class="sgp-error">
          <div class="sgp-error-title">⚠ SQL Error (stmt ${errStmtIdx}/${requested})</div>
          <div class="sgp-error-msg">${_esc(last.error || 'Unknown')}</div>
          ${ok > 0 ? `<div style="margin-top:10px;padding:8px 10px;background:#fff5e6;border-radius:4px;font-size:11px;color:#7a5a18;">✓ ${ok} statement${ok === 1 ? '' : 's'} executed successfully before the error.</div>` : ''}
          ${last.sql ? `<div class="sgp-error-trace" style="margin-top:10px;">${_esc(last.sql.slice(0, 400))}</div>` : ''}
          ${last.traceback ? `<div class="sgp-error-trace">${_esc(last.traceback)}</div>` : ''}
        </div>`;
      const firstLine = (last.sql || '').split('\n')[0].slice(0, 200);
      _updateMeta(firstLine, `${ok}/${requested} executed · ${totalMs}ms · error`, 'ERROR', `stopped at stmt ${errStmtIdx}`);
      return;
    }

    // 마지막이 SELECT 결과 — 그 결과를 그리드에
    if (batch.last_query) {
      const q = batch.last_query;
      // 배치 컨텍스트 주입
      q._context = { kind: 'batch', batchExecuted: executed, batchRequested: requested };
      _renderQuery(q);
      // 메타 통계 덧붙이기 (_renderQuery가 한 번 덮어쓰므로 이후 재갱신)
      const sqlPreview = (q.sql || '').replace(/\s+/g, ' ').trim();
      const rowsCount  = (q.rows || []).length;
      const colsCount  = (q.columns || []).length;
      _updateMeta(
        sqlPreview,
        `${rowsCount} rows · last of ${executed}/${requested} stmts · ${totalMs}ms`,
        q.verb || 'SELECT',
        `${rowsCount} ROWS × ${colsCount} COLS`
      );
      return;
    }

    // SELECT 없음 — DML/DDL만 있었음. 요약 화면.
    _lastResult = null;
    const counts = {};
    results.forEach(r => { counts[r.verb || r.kind] = (counts[r.verb || r.kind] || 0) + 1; });
    const countsText = Object.entries(counts).map(([k, v]) => `${v} ${k}`).join(', ');
    const lastVerb = last ? (last.verb || last.kind.toUpperCase()) : 'BATCH';
    sgpBody.innerHTML = `
      <div class="sgp-dml-ok">
        <div class="sgp-dml-icon">✓</div>
        <div class="sgp-dml-text">Batch executed</div>
        <div class="sgp-dml-sub">${_esc(executed)} statement${executed === 1 ? '' : 's'} — ${_esc(countsText)}</div>
      </div>`;
    _updateMeta(`${executed} statements`, `${totalMs}ms`, lastVerb, `${executed}/${requested} done`);
  }

  // ── 전체 에디터 실행 (Run All) ──
  // 파서로 statement 배열 뽑아서 배치 실행
  async function _runEntireEditor() {
    const Editor = window.Editor;
    if (!Editor || typeof Editor.getText !== 'function') {
      _renderError({ error: 'Editor not available', traceback: '' }, '');
      return;
    }
    const sqlText = Editor.getText();
    if (!sqlText.trim()) {
      _renderError({ error: 'Editor is empty — write some SQL first', traceback: '' }, '');
      return;
    }
    const stmts = _parseSqlStatements(sqlText);
    if (stmts.length === 0) {
      _renderError({ error: 'No SQL statements found (only comments/whitespace?)', traceback: '' }, sqlText);
      return;
    }
    // 각 statement의 text(앞주석 trim된)만 배열로 추출
    const stmtTexts = stmts.map(s => s.text);
    await _executeBatch(stmtTexts, sqlText);
  }


  // ═══════════════════════════════════════════════
  // SQL 바인딩 변수 감지 + 팝업
  // ═══════════════════════════════════════════════

  const _BIND_STYLE_KEY = 'usekit_sql_bind_style';
  const _BIND_VALS_PREFIX = 'usekit_sql_bind_vals__';

  // 선택된 스타일로 변수 이름 추출 (중복 제거, 순서 유지)
  function _extractBindVars(sql, style) {
    const code_only = _sqlCodeOnly(sql);
    const patterns = {
      '$': /\$(\w+)/g,
      ':': /(?<!:):(\w+)/g,
      '@': /@(\w+)/g,
      '%': /%\((\w+)\)s/g,
    };
    const re = patterns[style];
    if (!re) return [];
    const seen = new Set(), vars = [];
    let m;
    re.lastIndex = 0;
    while ((m = re.exec(code_only)) !== null) {
      if (!seen.has(m[1])) { seen.add(m[1]); vars.push(m[1]); }
    }
    return vars;
  }

  // code 구간만 추출 (문자열/주석 제외 — 간단 JS 버전)
  function _sqlCodeOnly(sql) {
    let out = '', i = 0, n = sql.length;
    while (i < n) {
      // line comment
      if (sql[i] === '-' && sql[i+1] === '-') {
        while (i < n && sql[i] !== '\n') i++;
        continue;
      }
      // block comment
      if (sql[i] === '/' && sql[i+1] === '*') {
        i += 2;
        while (i < n && !(sql[i] === '*' && sql[i+1] === '/')) i++;
        i += 2; continue;
      }
      // single-quoted
      if (sql[i] === "'") {
        i++;
        while (i < n) {
          if (sql[i] === "'" && sql[i+1] === "'") { i += 2; continue; }
          if (sql[i] === "'") { i++; break; }
          i++;
        }
        continue;
      }
      // double-quoted
      if (sql[i] === '"') {
        i++;
        while (i < n) {
          if (sql[i] === '"' && sql[i+1] === '"') { i += 2; continue; }
          if (sql[i] === '"') { i++; break; }
          i++;
        }
        continue;
      }
      out += sql[i++];
    }
    return out;
  }

  // 저장된 스타일 로드 (디폴트 $)
  function _loadBindStyle() {
    try { return localStorage.getItem(_BIND_STYLE_KEY) || '$'; } catch { return '$'; }
  }
  function _saveBindStyle(style) {
    try { localStorage.setItem(_BIND_STYLE_KEY, style); } catch {}
  }

  // 슬롯명 기반 이전 값 로드/저장
  function _loadBindVals(slotKey) {
    try { return JSON.parse(localStorage.getItem(_BIND_VALS_PREFIX + slotKey) || '{}'); } catch { return {}; }
  }
  function _saveBindVals(slotKey, vals) {
    try { localStorage.setItem(_BIND_VALS_PREFIX + slotKey, JSON.stringify(vals)); } catch {}
  }

  // 바인딩 변수 팝업 — Promise<paramStr | null>
  // sqlText: SQL 전문 (스타일 바뀌면 재감지용)
  // force: true면 변수 없어도 팝업 열기 (Set Variables 용)
  function _showBindPopup(sqlText, initialStyle, slotKey, force) {
    return new Promise((resolve) => {
      const prevVals = _loadBindVals(slotKey);
      const STYLES = ['$', ':', '@', '%'];
      let style = initialStyle;
      let vars = _extractBindVars(sqlText, style);

      let overlay = document.getElementById('_sqlBindPopup');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = '_sqlBindPopup';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;' +
          'background:rgba(0,0,0,0.6);z-index:9999;display:flex;' +
          'align-items:center;justify-content:center;padding:1.2rem;';
        document.body.appendChild(overlay);
      }

      const _renderStyleButtons = () => STYLES.map(s =>
        `<button data-style="${s}" style="padding:0.3rem 0.6rem;border-radius:6px;border:1px solid;` +
        `background:${s === style ? 'var(--ac-blue-bg,rgba(110,168,254,0.15))' : 'transparent'};` +
        `border-color:${s === style ? 'var(--ac-blue,#6ea8fe)' : 'var(--bd,rgba(110,168,254,0.15))'};` +
        `color:${s === style ? 'var(--ac-blue,#6ea8fe)' : 'var(--tx-muted,#8a93a3)'};` +
        `font-size:0.82rem;cursor:pointer;">${s === '%' ? '%(…)s' : s + 'var'}</button>`
      ).join('');

      const _renderVarFields = () => {
        if (!vars.length) {
          return `<div style="padding:0.6rem;text-align:center;font-size:0.82rem;color:var(--tx-muted,#8a93a3);opacity:0.7;">No ${style}variables detected</div>`;
        }
        return vars.map(v =>
          `<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
            <span style="min-width:80px;font-size:0.82rem;color:var(--tx-muted,#8a93a3);font-family:monospace;">${style}${v}</span>
            <input data-var="${v}" type="text" value="${(prevVals[v] ?? '').toString().replace(/"/g,'&quot;')}"
              style="flex:1;padding:0.4rem 0.6rem;border-radius:7px;border:1px solid var(--bd,#333);
              background:var(--bg-raised,#1c2638);color:var(--tx-primary,#e8edf6);font-size:0.85rem;outline:none;" />
          </div>`
        ).join('');
      };

      const _render = () => {
        overlay.innerHTML = `
          <div style="background:var(--bg-surface,#111827);border-radius:14px;
               padding:1.2rem 1rem;width:100%;max-width:400px;
               box-shadow:0 4px 32px rgba(0,0,0,0.6);border:1px solid var(--bd,rgba(110,168,254,0.12));">
            <div style="font-size:0.75rem;opacity:0.5;font-weight:700;letter-spacing:0.06em;margin-bottom:0.7rem;">SQL BIND VARIABLES</div>
            <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:0.9rem;" id="_bindStyleRow">
              ${_renderStyleButtons()}
            </div>
            <div id="_bindVarFields">${_renderVarFields()}</div>
            <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:0.9rem;">
              <button id="_bindCancel" style="padding:0.45rem 1rem;border-radius:8px;border:none;
                background:var(--bg-raised,#1c2638);color:var(--tx-muted,#8a93a3);font-size:0.85rem;cursor:pointer;">Cancel</button>
              <button id="_bindOk" style="padding:0.45rem 1rem;border-radius:8px;border:none;
                background:var(--ac-blue,#6ea8fe);color:#000;font-size:0.85rem;font-weight:700;cursor:pointer;">Run</button>
            </div>
          </div>`;

        // 스타일 버튼 — 클릭 시 재렌더(재감지)
        overlay.querySelector('#_bindStyleRow').addEventListener('click', e => {
          const btn = e.target.closest('[data-style]');
          if (!btn) return;
          const newStyle = btn.dataset.style;
          if (newStyle === style) return;
          style = newStyle;
          _saveBindStyle(style);
          vars = _extractBindVars(sqlText, style);
          _render();  // 재렌더
        });

        overlay.querySelector('#_bindOk').onclick = () => _done(true);
        overlay.querySelector('#_bindCancel').onclick = () => _done(false);
      };

      const _done = (ok) => {
        if (!ok) { overlay.style.display = 'none'; resolve(null); return; }
        const vals = {};
        overlay.querySelectorAll('[data-var]').forEach(el => { vals[el.dataset.var] = el.value; });
        _saveBindVals(slotKey, vals);
        _saveBindStyle(style);
        overlay.style.display = 'none';
        // 변수 없으면 빈 dict 반환
        if (!vars.length) { resolve('{}'); return; }
        // Python dict literal 조립
        const _toPyLiteral = (s) => {
          const t = String(s).trim();
          if (/^-?\d+$/.test(t)) return t;
          if (/^-?\d+\.\d+$/.test(t)) return t;
          const esc = t.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
          return `"${esc}"`;
        };
        const entries = vars.map(v => `"${v}": ${_toPyLiteral(vals[v])}`).join(', ');
        resolve(`{${entries}}`);
      };

      overlay.style.display = 'flex';
      _render();
      setTimeout(() => { overlay.querySelector('[data-var]')?.focus(); }, 80);
    });
  }

  // 감지 → 팝업 → paramStr 반환 (없으면 null, 취소면 false)
  async function _collectBindParams(sqlText, slotKey) {
    const style = _loadBindStyle();
    const vars = _extractBindVars(sqlText, style);
    if (!vars.length) return null;  // 변수 없음 → 그냥 실행
    const result = await _showBindPopup(sqlText, style, slotKey, false);
    return result === null ? false : result;
  }

  // SQL TOOL 패널의 "Set Variables" 진입점 — 강제 팝업 오픈, Run 시 현재 statement 실행
  async function _openBindPopupForce() {
    const Editor = window.Editor;
    if (!Editor || typeof Editor.getText !== 'function') return;
    const sqlText = Editor.getText();
    if (!sqlText.trim()) return;

    const slotKey = window.SlotManager?.getCurrentSlotInfo?.()?.fileName || 'default';
    const style = _loadBindStyle();
    const paramStr = await _showBindPopup(sqlText, style, slotKey, true);
    if (paramStr === null) return;  // Cancel

    // Run 눌렀으면 현재 statement 실행
    let cursorOffset = 0;
    try { cursorOffset = Editor.get()?.state?.selection?.main?.head ?? 0; } catch {}
    const found = _findStatementAt(sqlText, cursorOffset);
    if (!found) {
      _renderError({ error: 'No SQL statement found at cursor', traceback: '' }, '');
      return;
    }
    await _executeSql(found.text, {
      kind: 'current',
      stmtIndex: found.index,
      stmtTotal: found.total,
    }, paramStr);
  }
  window._openBindPopupForce = _openBindPopupForce;

  // ── 커서 위치 statement만 실행 (Current Block) ──
  async function _runCurrentStatement() {
    const Editor = window.Editor;
    if (!Editor || typeof Editor.getText !== 'function' || typeof Editor.get !== 'function') {
      _renderError({ error: 'Editor not available', traceback: '' }, '');
      return;
    }
    const sqlText = Editor.getText();
    if (!sqlText.trim()) {
      _renderError({ error: 'Editor is empty — write some SQL first', traceback: '' }, '');
      return;
    }

    // 커서 offset 직접 읽기 (Editor.get().state.selection.main.head)
    let cursorOffset = 0;
    try {
      const view = Editor.get();
      cursorOffset = view?.state?.selection?.main?.head ?? 0;
    } catch (e) {
      cursorOffset = 0;
    }

    const found = _findStatementAt(sqlText, cursorOffset);
    if (!found) {
      _renderError({ error: 'No SQL statement found at cursor', traceback: '' }, '');
      return;
    }

    // ── 실행 범위 하이라이트 ──
    _flashStatementRange(found.start, found.end);

    // 바인딩 변수 감지 → 팝업
    const slotKey = window.SlotManager?.getCurrentSlotInfo?.()?.fileName || 'default';
    const bindResult = await _collectBindParams(found.text, slotKey);
    if (bindResult === false) return;  // 취소

    await _executeSql(found.text, {
      kind: 'current',
      stmtIndex: found.index,
      stmtTotal: found.total,
    }, bindResult || undefined);
  }

  // ═══════════════════════════════════════════════
  // 드래그 + 통합 클릭 (Python pill과 동일 패턴)
  // ═══════════════════════════════════════════════

  // TOOL 팝업
  const sqlToolPanel = document.getElementById('floatSqlToolPanel');

  // 팝업 위치 계산 (Python pill의 _positionToolPanel과 동일 로직 — 4방향 adaptive)
  function _positionSqlToolPanel() {
    if (!sqlToolPanel) return;
    const r = sqlPill.getBoundingClientRect();
    const isHorizontal = sqlPill.classList.contains('is-horizontal');
    const margin = 8;
    const panelW = sqlToolPanel.offsetWidth  || 160;
    const panelH = sqlToolPanel.offsetHeight || 260;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const pillCx = r.left + r.width / 2;
    const pillCy = r.top  + r.height / 2;

    if (isHorizontal) {
      // 가로 pill: 상/하 중 공간 있는 쪽으로 드롭, 좌우는 pill 우측끝 정렬
      const pillOnUpperHalf = pillCy < vh / 2;
      let topVal;
      if (pillOnUpperHalf) {
        topVal = r.bottom + 8;                 // pill 아래
      } else {
        topVal = r.top - panelH - 8;           // pill 위
      }
      topVal = Math.max(margin, Math.min(vh - panelH - margin, topVal));

      let leftVal = r.right - panelW;          // 우측 정렬
      leftVal = Math.max(margin, Math.min(vw - panelW - margin, leftVal));

      sqlToolPanel.style.top    = topVal  + 'px';
      sqlToolPanel.style.left   = leftVal + 'px';
      sqlToolPanel.style.right  = 'auto';
      sqlToolPanel.style.bottom = 'auto';
    } else {
      // 세로 pill: 좌/우 중 공간 많은 쪽 attach, 세로는 pill 중앙 정렬
      const pillOnLeftHalf = pillCx < vw / 2;
      if (pillOnLeftHalf) {
        let leftVal = r.right + 10;
        leftVal = Math.max(margin, Math.min(vw - panelW - margin, leftVal));
        sqlToolPanel.style.left  = leftVal + 'px';
        sqlToolPanel.style.right = 'auto';
      } else {
        let rightVal = vw - r.left + 10;
        rightVal = Math.max(margin, Math.min(vw - panelW - margin, rightVal));
        sqlToolPanel.style.right = rightVal + 'px';
        sqlToolPanel.style.left  = 'auto';
      }
      let topVal = pillCy - panelH / 2;
      topVal = Math.max(margin, Math.min(vh - panelH - margin, topVal));
      sqlToolPanel.style.top    = topVal + 'px';
      sqlToolPanel.style.bottom = 'auto';
    }
  }

  function _toggleSqlToolPanel() {
    if (!sqlToolPanel) return;
    const show = sqlToolPanel.style.display === 'none' || sqlToolPanel.style.display === '';
    if (show) _positionSqlToolPanel();
    sqlToolPanel.style.display = show ? 'flex' : 'none';
    btnSqlTool.classList.toggle('is-active', show);
    if (show) requestAnimationFrame(_positionSqlToolPanel);
  }
  function _closeSqlToolPanel() {
    if (!sqlToolPanel) return;
    sqlToolPanel.style.display = 'none';
    btnSqlTool.classList.remove('is-active');
  }

  // ── 드래그 + 통합 클릭 (Python pill의 onStart/onMove/onEnd 패턴) ──
  let _sqlDragging = false, _sqlOx = 0, _sqlOy = 0, _sqlMoved = false, _sqlTouchId = null;

  function _sqlOnStart(cx, cy) {
    _sqlDragging = true; _sqlMoved = false;
    const r = sqlPill.getBoundingClientRect();
    _sqlOx = cx - r.left; _sqlOy = cy - r.top;
  }
  function _sqlOnMove(cx, cy) {
    if (!_sqlDragging) return;
    const r = sqlPill.getBoundingClientRect();
    const dx = Math.abs(cx - (r.left + _sqlOx));
    const dy = Math.abs(cy - (r.top  + _sqlOy));
    if (dx > 8 || dy > 8) _sqlMoved = true;
    if (!_sqlMoved) return;
    const w = sqlPill.offsetWidth  || 40;
    const h = sqlPill.offsetHeight || 150;
    sqlPill.style.left   = Math.max(0, Math.min(window.innerWidth  - w, cx - _sqlOx)) + 'px';
    sqlPill.style.top    = Math.max(0, Math.min(window.innerHeight - h, cy - _sqlOy)) + 'px';
    sqlPill.style.right  = 'auto';
    sqlPill.style.bottom = 'auto';
    // 드래그 중 팝업 닫기
    _closeSqlToolPanel();
  }
  function _sqlOnEnd(target) {
    _sqlDragging = false;
    if (_sqlMoved) {
      // 드래그로 이동한 경우 — 위치 저장
      try {
        const r = sqlPill.getBoundingClientRect();
        localStorage.setItem('usekit_sql_float_pos', JSON.stringify({ left: r.left, top: r.top }));
      } catch (e) {}
      return;
    }
    // 클릭 분기
    const id = target?.id || target?.closest?.('[id]')?.id;
    if      (id === 'floatBtnSql'     || target?.closest?.('#floatBtnSql'))     _runCurrentStatement();
    else if (id === 'floatBtnGrid'    || target?.closest?.('#floatBtnGrid'))    toggleGrid();
    else if (id === 'floatBtnSqlTool' || target?.closest?.('#floatBtnSqlTool')) _toggleSqlToolPanel();
  }

  sqlPill.addEventListener('touchstart', e => {
    e.preventDefault();
    const t = e.touches[0]; _sqlTouchId = t.identifier;
    _sqlOnStart(t.clientX, t.clientY);
  }, { passive: false });
  sqlPill.addEventListener('touchmove', e => {
    e.preventDefault();
    const t = [...e.touches].find(x => x.identifier === _sqlTouchId);
    if (t) _sqlOnMove(t.clientX, t.clientY);
  }, { passive: false });
  sqlPill.addEventListener('touchend', e => {
    e.preventDefault();
    const t = [...e.changedTouches].find(x => x.identifier === _sqlTouchId);
    _sqlOnEnd(document.elementFromPoint(t?.clientX ?? 0, t?.clientY ?? 0));
  }, { passive: false });

  sqlPill.addEventListener('mousedown', e => { _sqlOnStart(e.clientX, e.clientY); });
  document.addEventListener('mousemove', e => { if (_sqlDragging) _sqlOnMove(e.clientX, e.clientY); });
  document.addEventListener('mouseup',   e => { if (_sqlDragging) _sqlOnEnd(e.target); });

  // ── SQL TOOL 메뉴 버튼 바인딩 ──
  document.getElementById('floatStpCurrent')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    _runCurrentStatement();
  });
  document.getElementById('floatStpAll')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    _runEntireEditor();
  });
  document.getElementById('floatStpBind')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    _openBindPopupForce();
  });

  // Run → Explain: 현재 커서 위치의 SQL을 EXPLAIN QUERY PLAN으로 감싸 실행
  //   _runCurrentStatement 패턴 재사용 + prefix 추가 + context.kind='explain'
  document.getElementById('floatStpExplain')?.addEventListener('click', async () => {
    _closeSqlToolPanel();
    const Editor = window.Editor;
    if (!Editor || typeof Editor.getText !== 'function' || typeof Editor.get !== 'function') {
      _renderError({ error: 'Editor not available', traceback: '' }, '');
      openGrid();
      return;
    }
    const sqlText = Editor.getText();
    if (!sqlText.trim()) {
      _renderError({ error: 'Editor is empty — write some SQL first', traceback: '' }, '');
      openGrid();
      return;
    }
    let cursorOffset = 0;
    try {
      const view = Editor.get();
      cursorOffset = view?.state?.selection?.main?.head ?? 0;
    } catch (e) { cursorOffset = 0; }

    const found = _findStatementAt(sqlText, cursorOffset);
    if (!found) {
      _renderError({ error: 'No SQL statement found at cursor', traceback: '' }, '');
      openGrid();
      return;
    }

    // 바인딩 변수 처리 (일반 Run과 동일)
    const slotKey = window.SlotManager?.getCurrentSlotInfo?.()?.fileName || 'default';
    const bindResult = await _collectBindParams(found.text, slotKey);
    if (bindResult === false) return;  // 취소

    // EXPLAIN QUERY PLAN prefix — 원본 끝 세미콜론 제거 (SQLite EXPLAIN 문법)
    const bareSql = found.text.replace(/;\s*$/, '');
    const explainSql = 'EXPLAIN QUERY PLAN ' + bareSql;
    await _executeSql(explainSql, {
      kind: 'explain',
      stmtIndex: found.index,
      stmtTotal: found.total,
    }, bindResult || undefined);
  });

  // Meta → Analyze: DB 전체 통계 수집 (SQLite: ANALYZE)
  document.getElementById('floatStpAnalyze')?.addEventListener('click', async () => {
    _closeSqlToolPanel();
    await _executeSql('ANALYZE', { kind: 'meta', metaKind: 'analyze' });
  });

  // Meta → Vacuum (stub 교체): DB 전체 VACUUM
  document.getElementById('floatStpMetaVacuum')?.addEventListener('click', async () => {
    _closeSqlToolPanel();
    await _executeSql('VACUUM', { kind: 'meta', metaKind: 'vacuum' });
  });

  // 그룹 아코디언 토글 — Run / Meta / Menu 공통 패턴
  function _bindStpGroupToggle(toggleId, sectionId, arrowId) {
    const storageKey = 'usekit_mtp_grp_' + sectionId;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) {
        const sec = document.getElementById(sectionId);
        const arrow = document.getElementById(arrowId);
        if (sec) {
          sec.style.display = saved === 'open' ? 'block' : 'none';
          if (arrow) arrow.textContent = saved === 'open' ? '▴' : '▾';
        }
      }
    } catch (e) {}
    document.getElementById(toggleId)?.addEventListener('click', () => {
      const sec = document.getElementById(sectionId);
      const arrow = document.getElementById(arrowId);
      if (!sec) return;
      const open = sec.style.display !== 'none';
      sec.style.display = open ? 'none' : 'block';
      if (arrow) arrow.textContent = open ? '▾' : '▴';
      try { localStorage.setItem(storageKey, open ? 'closed' : 'open'); } catch (e) {}
    });
  }
  _bindStpGroupToggle('floatStpRunToggle',  'floatStpRunSection',  'floatStpRunArrow');
  _bindStpGroupToggle('floatStpMetaToggle', 'floatStpMetaSection', 'floatStpMetaArrow');
  _bindStpGroupToggle('floatStpMenuToggle', 'floatStpMenuSection', 'floatStpMenuArrow');

  // Help 버튼 — 패널 닫고 SQL Help 모달 열기
  document.getElementById('floatStpHelp')?.addEventListener('click', () => {
    const panel = document.getElementById('floatSqlToolPanel');
    if (panel) panel.style.display = 'none';
    const modal = document.getElementById('sqlHelpModal');
    if (modal) { modal.style.display = 'flex'; modal.setAttribute('aria-hidden', 'false'); }
  });
  document.getElementById('btnSqlHelpClose')?.addEventListener('click', () => {
    const modal = document.getElementById('sqlHelpModal');
    if (modal) { modal.style.display = 'none'; modal.setAttribute('aria-hidden', 'true'); }
  });
  document.getElementById('btnSqlHelpOk')?.addEventListener('click', () => {
    const modal = document.getElementById('sqlHelpModal');
    if (modal) { modal.style.display = 'none'; modal.setAttribute('aria-hidden', 'true'); }
  });

  // Meta → Tables
  document.getElementById('floatStpMetaTables')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    _executeMetaTables();
  });

  // ═══════════════════════════════════════════════
  // SQL pill 가로/세로 레이아웃 토글 (Python pill과 동일 패턴)
  // ═══════════════════════════════════════════════
  function _setSqlLayout(orientation, opts) {
    // orientation: 'vertical' | 'horizontal'
    // opts.preservePosition: true면 현재 pill 중심점 유지 (토글 시), false면 기본 위치 (초기 복원)
    const isHorizontal = orientation === 'horizontal';
    const preserve = opts?.preservePosition !== false;

    // 전환 전 중심점 기록
    const preRect = sqlPill.getBoundingClientRect();
    const preCx = preRect.left + preRect.width  / 2;
    const preCy = preRect.top  + preRect.height / 2;
    const hadVisualPosition = preRect.width > 0;

    // 클래스 토글 (크기 즉시 변경)
    sqlPill.classList.toggle('is-horizontal', isHorizontal);

    if (preserve && hadVisualPosition) {
      const newW = sqlPill.offsetWidth;
      const newH = sqlPill.offsetHeight;
      let newLeft = preCx - newW / 2;
      let newTop  = preCy - newH / 2;
      const margin = 6;
      newLeft = Math.max(margin, Math.min(window.innerWidth  - newW - margin, newLeft));
      newTop  = Math.max(margin, Math.min(window.innerHeight - newH - margin, newTop));
      sqlPill.style.transform = 'none';
      sqlPill.style.right  = 'auto';
      sqlPill.style.bottom = 'auto';
      sqlPill.style.left   = newLeft + 'px';
      sqlPill.style.top    = newTop  + 'px';
    } else {
      // 초기 복원 — 기본 위치
      if (isHorizontal) {
        sqlPill.style.right  = 'auto';
        sqlPill.style.left   = '50%';
        sqlPill.style.transform = 'translateX(-50%)';
        sqlPill.style.top    = '12px';
        sqlPill.style.bottom = 'auto';
      } else {
        sqlPill.style.left   = 'auto';
        sqlPill.style.transform = 'none';
        sqlPill.style.right  = '14px';
        sqlPill.style.bottom = 'auto';
        sqlPill.style.top    = '250px';
      }
    }

    // 라벨/아이콘 갱신 — "다음 상태" 표시 (Python pill 패턴)
    const lbl = document.getElementById('floatStpLayoutLabel');
    const ico = document.getElementById('floatStpLayoutIcon');
    if (lbl) lbl.textContent = isHorizontal ? 'Vertical' : 'Horizontal';
    if (ico) ico.textContent = isHorizontal ? '▤' : '▦';
    try { localStorage.setItem('usekit_sql_float_layout', orientation); } catch (e) {}
  }
  // 초기 복원 (기본 위치 사용)
  try {
    const saved = localStorage.getItem('usekit_sql_float_layout');
    if (saved === 'horizontal') _setSqlLayout('horizontal', { preservePosition: false });
  } catch (e) {}

  // ── 위치 복원 (레이아웃 복원 직후) ──
  //   저장된 좌표가 있으면 적용하되 화면 밖이면 클램프.
  try {
    const raw = localStorage.getItem('usekit_sql_float_pos');
    if (raw) {
      const pos = JSON.parse(raw);
      if (pos && typeof pos.left === 'number' && typeof pos.top === 'number') {
        const w = sqlPill.offsetWidth  || 58;
        const h = sqlPill.offsetHeight || 150;
        const margin = 6;
        const left = Math.max(margin, Math.min(window.innerWidth  - w - margin, pos.left));
        const top  = Math.max(margin, Math.min(window.innerHeight - h - margin, pos.top));
        sqlPill.style.transform = 'none';
        sqlPill.style.right  = 'auto';
        sqlPill.style.bottom = 'auto';
        sqlPill.style.left   = left + 'px';
        sqlPill.style.top    = top  + 'px';
      }
    }
  } catch (e) {}

  // Menu → Horizontal/Vertical 토글
  document.getElementById('floatStpMenuHorizontal')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    const next = sqlPill.classList.contains('is-horizontal') ? 'vertical' : 'horizontal';
    _setSqlLayout(next);  // 기본 preserve=true
    // 레이아웃 전환 후 새 위치 저장
    try {
      const r = sqlPill.getBoundingClientRect();
      localStorage.setItem('usekit_sql_float_pos', JSON.stringify({ left: r.left, top: r.top }));
    } catch (e) {}
  });

  // Menu → Hide: SQL 플로팅 + 패널 모두 숨김 (pointer-events 차단 포함)
  document.getElementById('floatStpMenuHide')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    hideSqlFloat();
  });

  // Menu → Menu: 자기 Hide + Menu pill(허브) 표시
  document.getElementById('floatStpMenuHub')?.addEventListener('click', () => {
    _closeSqlToolPanel();
    hideSqlFloat();
    if (window.MenuView?.show) window.MenuView.show();
  });

  // Grid 상태에 따라 메뉴 라벨 갱신은 openGrid/closeGrid 본체에서 처리됨 (_syncGridLabel)

  // 팝업 외부 탭 시 닫기 (SQL pill 자체는 이미 drag 처리, 그리드 overlay는 별도)
  document.addEventListener('touchstart', (e) => {
    if (sqlToolPanel && sqlToolPanel.style.display === 'flex') {
      if (!sqlToolPanel.contains(e.target) && !sqlPill.contains(e.target)) {
        _closeSqlToolPanel();
      }
    }
  }, { passive: true, capture: true });

  // close 버튼
  btnClose.addEventListener('click', closeGrid);
  // overlay 바깥 탭 → 닫기 (edit 모드에서는 무시)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay && !overlay.classList.contains('is-edit-mode')) closeGrid();
  });

  // ── edit 모드: 패널을 editor-section 안으로 이동 (에디터 메인, 패널 미니뷰) ──
  let _editModeActive = false;
  let _vvResizeHandler = null;

  function _updateEditPanelHeight() {
    const p = document.getElementById('sqlGridPanel');
    if (!p || !_editModeActive) return;
    // visualViewport 높이 vs 전체 화면 높이 비교 → 키보드 감지
    const vv = window.visualViewport;
    const screenH = window.screen.height || window.innerHeight;
    const viewH = vv ? vv.height : window.innerHeight;
    const kbOpen = (screenH - viewH) > 150;     // 150px 이상 차이 = 키보드 열림

    if (kbOpen) {
      // 키보드 열림 → 헤더+메타만 (약 70px)
      p.style.height = '70px';
      p.style.maxHeight = '70px';
    } else {
      // 키보드 닫힘 → 넉넉하게
      p.style.height = '45vh';
      p.style.maxHeight = '400px';
    }
  }

  function _enterEditMode() {
    const p = document.getElementById('sqlGridPanel');
    const section = document.querySelector('.editor-section');
    const host = document.getElementById('editor-host');
    const btn = document.getElementById('sgpBtnEdit');
    if (!p || !section) return;

    _editModeActive = true;
    overlay.classList.add('is-edit-mode');

    // 패널을 overlay에서 떼어서 editor-section에 붙임
    overlay.classList.remove('is-open');          // CSS로 숨김 (inline 없이)
    if (host) host.style.flex = '1 1 0';
    // 패널: 고정 높이, grow 없음
    p.style.flex = '0 0 auto';
    p.style.overflow = 'hidden';
    p.style.borderRadius = '0';
    p.style.borderTop = '2px solid #d99830';
    p.style.boxShadow = '0 -4px 12px rgba(0,0,0,0.15)';
    section.appendChild(p);

    // 초기 높이 + 키보드 감시
    _updateEditPanelHeight();
    _vvResizeHandler = _updateEditPanelHeight;
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', _vvResizeHandler);
    }

    if (btn) { btn.textContent = 'edit ●'; btn.classList.add('is-active'); }
  }
  function _exitEditMode() {
    if (!_editModeActive) return;     // edit 모드 아니면 무시
    const p = document.getElementById('sqlGridPanel');
    const btn = document.getElementById('sgpBtnEdit');
    if (!p) return;

    _editModeActive = false;
    overlay.classList.remove('is-edit-mode');

    // 키보드 감시 해제
    if (_vvResizeHandler && window.visualViewport) {
      window.visualViewport.removeEventListener('resize', _vvResizeHandler);
      _vvResizeHandler = null;
    }

    // 패널을 다시 overlay 안으로 복귀
    p.style.flex = '';
    p.style.maxHeight = '';
    p.style.minHeight = '';
    p.style.height = '';
    p.style.flexShrink = '';
    p.style.overflow = '';
    p.style.borderRadius = '';
    p.style.borderTop = '';
    p.style.boxShadow = '';
    // sgp-body 스크롤 명시 복원
    const body = document.getElementById('sgpBody');
    if (body) { body.style.overflow = 'auto'; body.style.minHeight = '0'; }
    overlay.appendChild(p);
    overlay.classList.add('is-open');             // 그리드 다시 보임
    overlay.style.display = '';                   // inline 잔여 제거

    // editor-host 복원
    const host = document.getElementById('editor-host');
    if (host) { host.style.flex = ''; host.style.minHeight = ''; }

    if (btn) { btn.textContent = 'edit'; btn.classList.remove('is-active'); }
  }
  document.getElementById('sgpBtnEdit')?.addEventListener('click', () => {
    if (_editModeActive) {
      _exitEditMode();
    } else {
      _enterEditMode();
    }
  });

  // wrap 토글 — localStorage 저장
  const _WRAP_KEY = 'usekit_sql_grid_wrap';
  const _applyWrapState = (on) => {
    const panel = document.getElementById('sqlGridPanel');
    const btn = document.getElementById('sgpBtnWrap');
    if (panel) panel.classList.toggle('is-wrap', !!on);
    if (btn)   btn.classList.toggle('is-active', !!on);
  };
  // 초기 상태 복원
  try {
    const saved = localStorage.getItem(_WRAP_KEY) === '1';
    _applyWrapState(saved);
  } catch {}
  document.getElementById('sgpBtnWrap')?.addEventListener('click', () => {
    const panel = document.getElementById('sqlGridPanel');
    const nowOn = !panel?.classList.contains('is-wrap');
    _applyWrapState(nowOn);
    try { localStorage.setItem(_WRAP_KEY, nowOn ? '1' : '0'); } catch {}
  });

  // copy / csv 버튼
  document.getElementById('sgpBtnCopy')?.addEventListener('click', _doCopy);
  document.getElementById('sgpBtnCsv')?.addEventListener('click', _doCsv);

  // 외부에서 호출 가능하게 노출
  window.SqlView = {
    enter: showSqlFloat,
    exit: hideSqlFloat,
    toggle: toggleSqlFloat,
    openGrid, closeGrid, toggleGrid,
    run: _runSql,                        // 기존 호환 (전체 실행)
    runAll: _runEntireEditor,            // 명시적 전체 실행 (배치)
    runCurrent: _runCurrentStatement,    // 커서 statement만 (기본)
    openToolPanel: _toggleSqlToolPanel,
    copy: _doCopy,
    exportCsv: _doCsv,
    // 디버깅/확장용
    _parseSqlStatements, _findStatementAt,
    _renderQuery, _renderDml, _renderError, _renderEmpty, _renderBatchResult,
    _buildSqlWrapper, _buildSqlBatchWrapper, _buildMetaTablesWrapper, _parseSqlOutput,
    _executeSql, _executeBatch, _executeMetaTables,
    _toTSV, _toCSV,
    get lastResult() { return _lastResult; },
    get editModeActive() { return _editModeActive; },
  };
})();
