/* Path: usekit/tools/editor/js2/editor/py_complete.js
 * --------------------------------------------------------------------------------------------
 * Python Autocomplete module for USEKIT Editor
 * - Ctrl+Space  → u.xxx USEKIT 단축형 (small scale)
 * - Alt+Space   → use.xxx USEKIT 풀네임 (large scale)
 * - Shift+Space → identifier history + python keywords + builtins + modules
 * --------------------------------------------------------------------------------------------
 */

const PyComplete = (function () {
    'use strict';

    // ── State ────────────────────────────────────────────────────────────────
    let _acTriggerKind = null;   // 'ctrl' | 'alt' | 'shift' | null

    // USEKIT 자동완성 데이터 (editor.js loadAutocomplete에서 주입)
    let _uItems    = [];   // u.xxx 단축형
    let _use1Items = [];   // use.xxx 1단계
    let _use2Items = [];   // use.xxx.xxx 2단계
    let _use3Items = [];   // use.xxx.xxx.xxx 3단계
    let _usekitReady = false;

    // 런타임 모듈 목록 (lazy load)
    let _runtimeModules = [];
    let _runtimeLoaded  = false;
    let _runtimeLoading = false;

    // ── Shift+Space 데이터: Builtin 함수 ─────────────────────────────────────
    const _BUILTIN_FUNCTIONS = [
        'print', 'len', 'range', 'type', 'int', 'str', 'float', 'list', 'dict', 'tuple', 'set',
        'bool', 'bytes', 'bytearray', 'memoryview',
        'input', 'open', 'exec', 'eval', 'compile',
        'abs', 'round', 'min', 'max', 'sum', 'pow', 'divmod',
        'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
        'any', 'all', 'next', 'iter',
        'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr', 'delattr',
        'id', 'hash', 'repr', 'format', 'chr', 'ord',
        'hex', 'oct', 'bin', 'ascii',
        'dir', 'vars', 'globals', 'locals', 'help',
        'callable', 'staticmethod', 'classmethod', 'property', 'super',
        'object', 'breakpoint', '__import__',
        'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
        'AttributeError', 'FileNotFoundError', 'ImportError', 'RuntimeError',
        'StopIteration', 'GeneratorExit', 'SystemExit', 'KeyboardInterrupt',
        'OSError', 'IOError', 'NameError', 'ZeroDivisionError',
        'OverflowError', 'RecursionError', 'PermissionError',
        'NotImplementedError', 'AssertionError', 'UnicodeError',
        // 자주 쓰는 메서드
        'append', 'extend', 'insert', 'remove', 'pop', 'clear', 'copy',
        'keys', 'values', 'items', 'get', 'update', 'setdefault',
        'join', 'split', 'strip', 'lstrip', 'rstrip', 'replace', 'find', 'rfind',
        'startswith', 'endswith', 'upper', 'lower', 'title', 'capitalize',
        'encode', 'decode', 'count', 'index',
        'sort', 'reverse',
        'read', 'write', 'readline', 'readlines', 'writelines', 'close', 'flush', 'seek',
        'add', 'discard', 'union', 'intersection', 'difference',
        'isdigit', 'isalpha', 'isalnum', 'isspace',
        'splitlines', 'partition', 'rpartition',
    ];

    // ── Shift+Space 데이터: 모듈명 ──────────────────────────────────────────
    const _STATIC_MODULES = [
        'os', 'sys', 're', 'json', 'csv', 'math', 'random', 'time', 'datetime',
        'pathlib', 'shutil', 'glob', 'fnmatch',
        'collections', 'itertools', 'functools', 'operator',
        'io', 'string', 'textwrap', 'struct', 'codecs',
        'subprocess', 'threading', 'multiprocessing', 'concurrent',
        'argparse', 'logging', 'warnings',
        'hashlib', 'hmac', 'secrets',
        'sqlite3', 'dbm', 'shelve',
        'http', 'urllib', 'socket', 'ssl', 'email',
        'xml', 'html', 'configparser',
        'pickle', 'copy', 'pprint',
        'typing', 'dataclasses', 'abc', 'enum',
        'unittest', 'doctest', 'pdb', 'traceback', 'inspect',
        'contextlib', 'atexit', 'signal',
        'tempfile', 'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma',
        'base64', 'binascii',
        'statistics', 'decimal', 'fractions',
        'asyncio', 'selectors',
        'importlib', 'pkgutil', 'types',
        'platform', 'sysconfig',
        'os.path', 'collections.abc', 'concurrent.futures',
        'urllib.parse', 'urllib.request', 'http.server', 'http.client',
    ];

    const _STATIC_PIP_MODULES = [
        'numpy', 'pandas', 'requests', 'flask', 'fastapi',
        'PIL', 'cv2', 'matplotlib', 'scipy', 'sklearn',
        'torch', 'tensorflow',
        'yaml', 'toml', 'dotenv',
        'bs4', 'lxml', 'selenium',
        'pytest', 'black', 'mypy', 'ruff',
        'tqdm', 'rich', 'click', 'typer',
        'pydantic', 'httpx', 'aiohttp',
        'uvicorn', 'gunicorn', 'celery',
        'sqlalchemy', 'alembic',
        'paramiko', 'fabric',
        'jinja2', 'markupsafe',
        'cryptography', 'jwt',
        'boto3', 'google',
        'openai', 'anthropic',
        'gradio', 'streamlit',
    ];

    // ── Shift+Space 데이터: Python 키워드 ───────────────────────────────────
    const _PY_KEYWORDS = [
        'False', 'None', 'True',
        'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
        'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
        'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not',
        'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
    ];

    const _PY_COMPOUNDS = [
        "if __name__ == '__main__':",
        'def __init__(self):', 'def __repr__(self):', 'def __str__(self):',
        'def __enter__(self):', 'def __exit__(self):',
        'def __getitem__(self, key):', 'def __setitem__(self, key, val):',
        'def __len__(self):', 'def __iter__(self):', 'def __next__(self):',
        'def __call__(self):',
        "with open('', 'r') as f:",
        'for i in range():',
        'except Exception as e:',
        'raise ValueError', 'raise TypeError', 'raise NotImplementedError',
        'async def', 'async for', 'async with',
        'yield from',
        '@property', '@staticmethod', '@classmethod',
        '@dataclass', '@abstractmethod',
        '__all__', '__version__', '__name__', '__file__', '__doc__',
        'is None', 'is not None', 'not in',
    ];

    // ── Python 모드 판별 ────────────────────────────────────────────────────
    function isPyMode() {
        if (window.SqlComplete?.isSqlMode?.()) return false;
        const ext = (document.getElementById('metaExt')?.value || '').trim().toLowerCase();
        return ext === 'py' || ext === '' || ext === 'txt';
    }

    // ── USEKIT 데이터 주입 (editor.js loadAutocomplete에서 호출) ─────────────
    function setUsekitItems(uI, use1I, use2I, use3I) {
        _uItems    = uI  || [];
        _use1Items = use1I || [];
        _use2Items = use2I || [];
        _use3Items = use3I || [];
        _usekitReady = _uItems.length > 0 || _use1Items.length > 0;
        console.log('[PyAC] USEKIT items set: u=' + _uItems.length,
            'use1=' + _use1Items.length, 'use2=' + _use2Items.length, 'use3=' + _use3Items.length);
    }

    // ── 런타임 모듈 로드 ────────────────────────────────────────────────────
    async function loadRuntimeModules() {
        if (_runtimeLoaded || _runtimeLoading) return;
        _runtimeLoading = true;
        console.log('[PyAC] loadRuntimeModules: starting...');

        const code = `
import json as _json
try:
    import pkgutil as _pkgutil
    import sys as _sys
    _mods = set()
    for _name in _sys.modules:
        if not _name.startswith('_'):
            _mods.add(_name.split('.')[0])
    try:
        for _imp, _name, _ispkg in _pkgutil.iter_modules():
            if not _name.startswith('_'):
                _mods.add(_name)
    except Exception:
        pass
    print("__PY_MODULES__" + _json.dumps(sorted(_mods)))
except Exception as _e:
    print("__PY_MODULES_ERROR__" + str(_e))
`;
        try {
            const res = await fetch('/api/exec', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, inputs: [], timeout: 15 }),
            });
            const json = await res.json();
            const stdout = json.stdout || '';

            const marker = '__PY_MODULES__';
            const idx = stdout.indexOf(marker);
            if (idx >= 0) {
                const raw = stdout.slice(idx + marker.length).split('\n')[0];
                _runtimeModules = JSON.parse(raw);
                _runtimeLoaded = true;
                console.log('[PyAC] runtime modules loaded:', _runtimeModules.length);
            } else {
                console.warn('[PyAC] module marker not found');
            }
        } catch (e) {
            console.warn('[PyAC] runtime load failed:', e);
        } finally {
            _runtimeLoading = false;
        }
    }

    function reloadRuntimeModules() {
        _runtimeLoaded = false;
        _runtimeLoading = false;
        return loadRuntimeModules();
    }

    // ── 식별자 수집 ─────────────────────────────────────────────────────────
    function _collectIdentifiers(text) {
        const set = new Set();
        const re = /\b([a-zA-Z_]\w{1,})\b/g;
        let m;
        while ((m = re.exec(text)) !== null) {
            set.add(m[1]);
        }
        const exclude = new Set([
            ..._PY_KEYWORDS.map(k => k.toLowerCase()),
            'true', 'false', 'none', 'self', 'cls',
        ]);
        const result = [];
        for (const id of set) {
            if (!exclude.has(id.toLowerCase())) {
                result.push(id);
            }
        }
        return result.sort();
    }

    // ── 모듈 목록 합산 ──────────────────────────────────────────────────────
    function _getAllModules() {
        const set = new Set([..._STATIC_MODULES, ..._STATIC_PIP_MODULES]);
        if (_runtimeLoaded) {
            for (const m of _runtimeModules) set.add(m);
        }
        return [...set].sort();
    }

    // ── CM6 completion source ────────────────────────────────────────────────
    function pySource(context) {
        const kind = _acTriggerKind;
        _acTriggerKind = null;

        if (!context.explicit && !kind) return null;

        const wordMatch = context.matchBefore(/\w*/);
        const from   = wordMatch ? wordMatch.from : context.pos;
        const typing = wordMatch ? wordMatch.text : '';
        const ltyping = typing.toLowerCase();

        // ── Ctrl+Space → u.xxx USEKIT 단축형 ──
        if (kind === 'ctrl') {
            if (!_usekitReady) return null;
            const section = { name: 'u.', rank: 0 };
            const options = _uItems
                .filter(o => o.label.toLowerCase().startsWith(ltyping))
                .map(o => ({
                    label: o.label,
                    detail: o.detail,
                    type: 'function',
                    section,
                    apply: (view, completion, from, to) => {
                        const insert = 'u.' + completion.label;
                        view.dispatch({
                            changes: { from, to, insert },
                            selection: { anchor: from + insert.length },
                        });
                    },
                }));
            return options.length ? { from, options } : null;
        }

        // ── Alt+Space → use.xxx USEKIT 풀네임 ──
        if (kind === 'alt') {
            if (!_usekitReady) return null;
            const section = { name: 'use.', rank: 0 };
            const options = _use1Items
                .filter(o => o.label.toLowerCase().startsWith(ltyping))
                .map(o => ({
                    label: o.label,
                    detail: o.detail,
                    type: 'function',
                    section,
                    apply: (view, completion, from, to) => {
                        const insert = 'use.' + completion.label;
                        view.dispatch({
                            changes: { from, to, insert },
                            selection: { anchor: from + insert.length },
                        });
                    },
                }));
            return options.length ? { from, options } : null;
        }

        // ── Shift+Space → 히스토리 + 키워드 + builtin + 모듈 ──
        if (kind === 'shift' || (!kind && context.explicit)) {
            const histSection    = { name: 'HISTORY', rank: 0 };
            const kwSection      = { name: 'KEYWORD', rank: 1 };
            const builtinSection = { name: 'BUILTIN', rank: 2 };
            const moduleSection  = { name: 'MODULE', rank: 3 };
            const snippetSection = { name: 'SNIPPET', rank: 4 };

            const editorText = context.state.doc.toString();
            const ids = _collectIdentifiers(editorText);
            const options = [];

            // 1. 히스토리
            for (const id of ids) {
                if (id.toLowerCase().startsWith(ltyping)) {
                    options.push({ label: id, type: 'variable', boost: 4, section: histSection });
                }
            }
            // 2. 키워드
            for (const kw of _PY_KEYWORDS) {
                if (kw.toLowerCase().startsWith(ltyping)) {
                    options.push({ label: kw, type: 'keyword', boost: 3, section: kwSection });
                }
            }
            // 3. builtin
            for (const b of _BUILTIN_FUNCTIONS) {
                if (b.toLowerCase().startsWith(ltyping)) {
                    options.push({ label: b, type: 'function', boost: 2, section: builtinSection });
                }
            }
            // 4. 모듈
            const allModules = _getAllModules();
            for (const m of allModules) {
                if (m.toLowerCase().startsWith(ltyping)) {
                    options.push({ label: m, type: 'namespace', boost: 1, section: moduleSection });
                }
            }
            // 5. 스니펫
            for (const c of _PY_COMPOUNDS) {
                if (c.toLowerCase().startsWith(ltyping)) {
                    options.push({ label: c, type: 'text', boost: 0, section: snippetSection });
                }
            }
            return options.length ? { from, options } : null;
        }

        return null;
    }

    // ── 키 이벤트 핸들러 ────────────────────────────────────────────────────
    function handleKeyTrigger(e) {
        if (!isPyMode()) return false;

        // 런타임 모듈 lazy load
        if (!_runtimeLoaded && !_runtimeLoading) {
            loadRuntimeModules();
        }

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
        if (isPyMode()) {
            loadRuntimeModules();
        }
    }

    // ── Public API ───────────────────────────────────────────────────────────
    return {
        init,
        isPyMode,
        pySource,
        handleKeyTrigger,
        setUsekitItems,
        loadRuntimeModules,
        reloadRuntimeModules,
        setTriggerKind(kind) { _acTriggerKind = kind; },
        get runtimeLoaded() { return _runtimeLoaded; },
        get usekitReady() { return _usekitReady; },
    };
})();

window.PyComplete = PyComplete;
