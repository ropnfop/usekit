/* Path: usekit/tools/editor/js2/editor/sql_complete.js
 * --------------------------------------------------------------------------------------------
 * SQL Autocomplete module for USEKIT Editor
 * - Ctrl+Space  → table names
 * - Alt+Space   → column names (priority: last selected table > FROM/JOIN context)
 * - Shift+Space → input history (identifiers from editor text)
 * - alias.      → auto-popup columns for that alias/table
 * --------------------------------------------------------------------------------------------
 */

const SqlComplete = (function () {
    'use strict';

    // ── State ────────────────────────────────────────────────────────────────
    let _sqlSchema     = {};      // { tableName: ['col1','col2',...] }
    let _sqlTables     = [];      // ['orders_sample', 'users', ...]
    let _schemaLoaded  = false;
    let _schemaLoading = false;

    let _lastSelectedTable = null;   // Ctrl+Space에서 탭으로 선택한 테이블
    let _acTriggerKind     = null;   // 'ctrl' | 'alt' | 'shift' | null

    // SQL 키워드 (Shift+Space용)
    const _SQL_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL',
        'AS', 'ON', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
        'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
        'CREATE', 'DROP', 'ALTER', 'TABLE', 'INDEX', 'VIEW',
        'IF', 'EXISTS', 'NOT EXISTS',
        'BETWEEN', 'LIKE', 'GLOB', 'IN',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'DISTINCT', 'ALL', 'UNION', 'EXCEPT', 'INTERSECT',
        'ASC', 'DESC', 'NULLS FIRST', 'NULLS LAST',
        'PRIMARY KEY', 'FOREIGN KEY', 'REFERENCES', 'DEFAULT', 'CHECK', 'UNIQUE',
        'INTEGER', 'TEXT', 'REAL', 'BLOB', 'BOOLEAN', 'VARCHAR',
        'PRAGMA', 'EXPLAIN', 'EXPLAIN QUERY PLAN',
        'ANALYZE', 'VACUUM', 'REINDEX',
        'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
        'TRIGGER', 'REPLACE', 'UPSERT',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
        'COALESCE', 'IFNULL', 'NULLIF', 'CAST',
        'SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'TRIM', 'REPLACE',
        'ROUND', 'ABS', 'RANDOM',
        'DATE', 'TIME', 'DATETIME', 'STRFTIME',
        'GROUP_CONCAT', 'TOTAL', 'TYPEOF',
        'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'OVER', 'PARTITION BY',
        'WITH', 'RECURSIVE',
        'SELECT *', 'SELECT COUNT(*)', 'ORDER BY', 'GROUP BY',
        'LEFT JOIN', 'INNER JOIN', 'CROSS JOIN',
        'INSERT INTO', 'DELETE FROM', 'UPDATE SET',
        'CREATE TABLE', 'CREATE INDEX', 'CREATE VIEW',
        'DROP TABLE', 'DROP INDEX', 'DROP VIEW',
        'ALTER TABLE', 'ADD COLUMN', 'RENAME TO',
    ];

    // ── SQL 모드 판별 ────────────────────────────────────────────────────────
    function isSqlMode() {
        const ext = (document.getElementById('metaExt')?.value || '').trim().toLowerCase();
        const editMode = window.SqlView?.editModeActive || false;
        const result = ext === 'sql' || editMode;
        console.log('[SqlAC] isSqlMode:', result, '(ext=' + ext + ', editMode=' + editMode + ')');
        return result;
    }

    // ── 스키마 로드 ──────────────────────────────────────────────────────────
    // /api/exec 로 pragma 조회 → _sqlSchema 캐시
    async function loadSchema() {
        if (_schemaLoaded || _schemaLoading) return;
        _schemaLoading = true;
        console.log('[SqlAC] loadSchema: starting...');

        const code = `
import json as _json
try:
    from usekit import u as _u
except Exception as _e:
    print("__SQL_SCHEMA_ERROR__" + str(_e))
else:
    _tables = _u.xsb(\"\"\"
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    \"\"\")
    _schema = {}
    for _t in (_tables or []):
        _tname = _t[0] if isinstance(_t, (list,tuple)) else (_t.name if hasattr(_t,'name') else _t.get('name',''))
        try:
            _cols = _u.xsb('PRAGMA table_info("' + str(_tname).replace('"','""') + '")')
            _cnames = []
            for _c in (_cols or []):
                if hasattr(_c, 'name'):
                    _cnames.append(_c.name)
                elif isinstance(_c, dict):
                    _cnames.append(_c.get('name',''))
                elif isinstance(_c, (list,tuple)):
                    _cnames.append(_c[1])
            _schema[str(_tname)] = _cnames
        except Exception:
            _schema[str(_tname)] = []
    print("__SQL_SCHEMA__" + _json.dumps(_schema))
`;
        try {
            const res  = await fetch('/api/exec', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, inputs: [], timeout: 15 }),
            });
            const json = await res.json();
            const stdout = json.stdout || '';
            console.log('[SqlAC] loadSchema response ok:', json.ok, 'stdout length:', stdout.length);
            if (!json.ok) console.warn('[SqlAC] loadSchema error:', json.error, json.stderr);

            const marker = '__SQL_SCHEMA__';
            const idx = stdout.indexOf(marker);
            if (idx >= 0) {
                const raw = stdout.slice(idx + marker.length).split('\n')[0];
                _sqlSchema = JSON.parse(raw);
                _sqlTables = Object.keys(_sqlSchema).sort();
                _schemaLoaded = true;
                console.log('[SqlComplete] schema loaded:', _sqlTables.length, 'tables');
            } else {
                console.warn('[SqlComplete] schema marker not found in output');
            }
        } catch (e) {
            console.warn('[SqlComplete] schema load failed:', e);
        } finally {
            _schemaLoading = false;
        }
    }

    function reloadSchema() {
        _schemaLoaded = false;
        _schemaLoading = false;
        return loadSchema();
    }

    // ── alias 파싱 ───────────────────────────────────────────────────────────
    // FROM tableName alias / FROM tableName AS alias / JOIN tableName alias
    // 반환: { alias: tableName, tableName: tableName }
    function _parseAliases(sqlText) {
        const map = {};
        // 패턴: FROM/JOIN 뒤에 테이블명 (옵션 AS) alias
        const re = /\b(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?\b/gi;
        let m;
        while ((m = re.exec(sqlText)) !== null) {
            const tableName = m[1];
            const alias     = m[2] || null;
            // 테이블명 자체도 등록
            const lower = tableName.toLowerCase();
            if (_sqlSchema[tableName] || _sqlTables.includes(tableName)) {
                map[tableName] = tableName;
                if (alias) {
                    // alias가 SQL 키워드가 아닌지 간단 체크
                    const kw = ['WHERE','ON','SET','AND','OR','LEFT','RIGHT','INNER','OUTER',
                                'CROSS','NATURAL','ORDER','GROUP','HAVING','LIMIT','UNION',
                                'INTO','VALUES','SELECT','INSERT','UPDATE','DELETE'];
                    if (!kw.includes(alias.toUpperCase())) {
                        map[alias] = tableName;
                    }
                }
            }
        }
        return map;
    }

    // ── 입력 히스토리 (Shift+Space) ─────────────────────────────────────────
    // 에디터 텍스트에서 식별자 수집 (중복 제거, 알파벳순)
    function _collectIdentifiers(text) {
        const set = new Set();
        const re = /\b([a-zA-Z_]\w{1,})\b/g;
        let m;
        while ((m = re.exec(text)) !== null) {
            set.add(m[1]);
        }
        // SQL 키워드 제외
        const kw = new Set(['SELECT','FROM','WHERE','AND','OR','NOT','IN','IS','NULL',
            'AS','ON','JOIN','LEFT','RIGHT','INNER','OUTER','CROSS','NATURAL',
            'ORDER','BY','GROUP','HAVING','LIMIT','OFFSET','INSERT','INTO',
            'VALUES','UPDATE','SET','DELETE','CREATE','DROP','ALTER','TABLE',
            'INDEX','VIEW','IF','EXISTS','BETWEEN','LIKE','CASE','WHEN','THEN',
            'ELSE','END','DISTINCT','ALL','UNION','EXCEPT','INTERSECT','ASC','DESC',
            'PRIMARY','KEY','FOREIGN','REFERENCES','CONSTRAINT','DEFAULT','CHECK',
            'UNIQUE','INTEGER','TEXT','REAL','BLOB','BOOLEAN','VARCHAR','CHAR',
            'PRAGMA','EXPLAIN','ANALYZE','VACUUM','BEGIN','COMMIT','ROLLBACK',
            'TRANSACTION','TRIGGER','AFTER','BEFORE','FOR','EACH','ROW','REPLACE']);
        const result = [];
        for (const id of set) {
            if (!kw.has(id.toUpperCase())) {
                result.push(id);
            }
        }
        return result.sort();
    }

    // ── CM6 completion source ────────────────────────────────────────────────
    function sqlSource(context) {
        if (!_schemaLoaded) return null;

        const editorText = context.state.doc.toString();

        // ── 1. dot completion: alias. 또는 tableName. ──
        const dotMatch = context.matchBefore(/\w+\.\w*/);
        if (dotMatch) {
            const parts  = dotMatch.text.split('.');
            const prefix = parts[0];
            const typing = parts[1] || '';
            const aliases = _parseAliases(editorText);
            const tableName = aliases[prefix] || (_sqlSchema[prefix] ? prefix : null);
            if (tableName && _sqlSchema[tableName]) {
                const cols = _sqlSchema[tableName];
                return {
                    from: dotMatch.from + prefix.length + 1,
                    options: cols
                        .filter(c => c.toLowerCase().startsWith(typing.toLowerCase()))
                        .map(c => ({ label: c, type: 'property', detail: tableName })),
                };
            }
            return null;
        }

        // ── 2. explicit triggers (Ctrl/Alt/Shift + Space) ──
        const kind = _acTriggerKind;
        _acTriggerKind = null;   // 소비 후 리셋

        if (!context.explicit && !kind) return null;

        // 커서 앞 단어 (필터용)
        const wordMatch = context.matchBefore(/\w*/);
        const from   = wordMatch ? wordMatch.from : context.pos;
        const typing = wordMatch ? wordMatch.text : '';

        // ── Ctrl+Space → 컬럼명 ──
        if (kind === 'ctrl' || (!kind && context.explicit)) {
            let columns = [];
            let sourceTable = '';

            // 우선순위 1: 마지막 선택 테이블
            if (_lastSelectedTable && _sqlSchema[_lastSelectedTable]) {
                columns = _sqlSchema[_lastSelectedTable];
                sourceTable = _lastSelectedTable;
            }

            // 우선순위 2: FROM/JOIN 파싱
            if (columns.length === 0) {
                const aliases = _parseAliases(editorText);
                const tables = [...new Set(Object.values(aliases))];
                if (tables.length === 1) {
                    sourceTable = tables[0];
                    columns = _sqlSchema[sourceTable] || [];
                } else if (tables.length > 1) {
                    // 여러 테이블 → 전부 합치되 출처 표시
                    const colSection = { name: 'COLUMN', rank: 0 };
                    for (const t of tables) {
                        for (const c of (_sqlSchema[t] || [])) {
                            columns.push({ col: c, table: t });
                        }
                    }
                    return {
                        from,
                        options: columns
                            .filter(item => item.col.toLowerCase().startsWith(typing.toLowerCase()))
                            .map(item => ({
                                label: item.col,
                                type: 'property',
                                detail: item.table,
                                section: colSection,
                            })),
                    };
                }
            }

            if (columns.length > 0 && typeof columns[0] === 'string') {
                const colSection = { name: `COLUMN · ${sourceTable}`, rank: 0 };
                return {
                    from,
                    options: columns
                        .filter(c => c.toLowerCase().startsWith(typing.toLowerCase()))
                        .map(c => ({ label: c, type: 'property', detail: sourceTable, section: colSection })),
                };
            }
            return null;
        }

        // ── Alt+Space → 테이블명 ──
        if (kind === 'alt') {
            const tableSection = { name: 'TABLE', rank: 0 };
            return {
                from,
                options: _sqlTables
                    .filter(t => t.toLowerCase().startsWith(typing.toLowerCase()))
                    .map(t => ({
                        label: t,
                        type: 'class',
                        detail: `${(_sqlSchema[t]||[]).length} cols`,
                        section: tableSection,
                        apply: (view, completion, from, to) => {
                            view.dispatch({
                                changes: { from, to, insert: completion.label },
                                selection: { anchor: from + completion.label.length },
                            });
                            _lastSelectedTable = completion.label;
                        },
                    })),
            };
        }

        // ── Shift+Space → 입력 히스토리 + SQL 키워드 ──
        if (kind === 'shift') {
            const histSection = { name: 'HISTORY', rank: 0 };
            const kwSection   = { name: 'SQL KEYWORD', rank: 1 };
            const ids = _collectIdentifiers(editorText);
            const options = ids
                .filter(id => id.toLowerCase().startsWith(typing.toLowerCase()))
                .map(id => ({ label: id, type: 'variable', boost: 1, section: histSection }));
            // SQL 키워드 추가
            for (const kw of _SQL_KEYWORDS) {
                if (kw.toLowerCase().startsWith(typing.toLowerCase())) {
                    options.push({ label: kw, type: 'keyword', boost: 0, section: kwSection });
                }
            }
            return { from, options };
        }

        return null;
    }

    // ── 키 이벤트 핸들러 (editor.js keydown에서 호출) ────────────────────────
    // 반환: true면 completion 트리거 필요, false면 무시
    function handleKeyTrigger(e) {
        if (!isSqlMode()) return false;

        // lazy load: SQL 모드인데 스키마 아직 없으면 로드 시작
        if (!_schemaLoaded && !_schemaLoading) {
            console.log('[SqlAC] handleKeyTrigger: lazy loading schema...');
            loadSchema();
            return false;
        }
        if (!_schemaLoaded) {
            console.log('[SqlAC] handleKeyTrigger: schema still loading, skip');
            return false;
        }

        console.log('[SqlAC] handleKeyTrigger: key=' + e.key, 'ctrl=' + e.ctrlKey, 'alt=' + e.altKey, 'shift=' + e.shiftKey);

        if (e.key === ' ' || e.code === 'Space') {
            if (e.ctrlKey && !e.altKey && !e.shiftKey) {
                _acTriggerKind = 'ctrl';
                e.preventDefault();
                return true;
            }
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                _acTriggerKind = 'alt';
                e.preventDefault();
                return true;
            }
            if (e.shiftKey && !e.ctrlKey && !e.altKey) {
                _acTriggerKind = 'shift';
                e.preventDefault();
                return true;
            }
        }
        return false;
    }

    // ── 초기화 ───────────────────────────────────────────────────────────────
    function init() {
        // SQL 모드면 스키마 로드
        if (isSqlMode()) {
            loadSchema();
        }
    }

    // ── Public API ───────────────────────────────────────────────────────────
    return {
        init,
        loadSchema,
        reloadSchema,
        isSqlMode,
        sqlSource,
        handleKeyTrigger,
        setTriggerKind(kind) { _acTriggerKind = kind; },
        get lastSelectedTable() { return _lastSelectedTable; },
        set lastSelectedTable(v) { _lastSelectedTable = v; },
        get schemaLoaded() { return _schemaLoaded; },
        get tables() { return _sqlTables; },
        get schema() { return _sqlSchema; },
    };
})();

// window에 노출
window.SqlComplete = SqlComplete;
