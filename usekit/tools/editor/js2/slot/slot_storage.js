// slot_storage.js
// OPFS R/W (slot data) + localStorage (metadata), sync-compatible via memory cache
// Lazy load: 초기화 시 파일 목록만 스캔, 내용은 readLocal 호출 시 로드
// Fallback: OPFS → IDB → LS
// Depends on: UI (showToast)

const SlotStorage = (function () {
    'use strict';

    const PREFIX    = 'usekit_scratch_editor_'; // IDB/LS 마이그레이션 호환용
    const META_KEY  = 'usekit_editor_slots_v2';
    const UM_PREFIX = PREFIX + 'usekitmeta_';
    const OPFS_DIR  = 'usekit_editor';
    const IDB_NAME  = 'usekit_editor';
    const IDB_VER   = 1;
    const IDB_STORE = 'slot_data';

    // ── Memory cache ──────────────────────────────────────────────
    // key: fileName, value: JSON string (null = 존재는 하지만 아직 미로드)
    const _cache    = new Map(); // fileName → JSON string | null
    const _handles  = new Map(); // fileName → FileSystemFileHandle (OPFS)

    let _opfsDir = null;
    let _idb     = null;
    let _mode    = null; // 'opfs' | 'idb' | 'ls'
    let _ready   = false;
    let _pendingFlush = null;

    // ── Toast / Format ────────────────────────────────────────────
    function toast(msg, ms = 1200, position) {
        try { UI.showToast(String(msg), ms, position || 'bottom'); } catch(e) {}
    }
    function formatTime(ts) {
        try {
            const d = new Date(ts), p = n => String(n).padStart(2, '0');
            return `${String(d.getFullYear()).slice(-2)}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
        } catch(e) { return ''; }
    }

    // ── OPFS ──────────────────────────────────────────────────────
    // swap/temp 파일 정리 상태 — 실패 시 재시도 큐
    const _swapRetryQueue = new Set(); // fileName → 다음 sweep 때 재시도

    function _isSwapFile(name) {
        // OPFS createWritable()이 생성하는 임시 파일
        return name.endsWith('.crswap');
    }

    async function _initOPFS() {
        const root = await navigator.storage.getDirectory();
        _opfsDir = await root.getDirectoryHandle(OPFS_DIR, { create: true });
        // 파일 목록만 스캔 — 내용은 읽지 않음 (lazy)
        let swapFound = 0, swapCleaned = 0, swapFailed = 0;
        for await (const [name, handle] of _opfsDir.entries()) {
            if (handle.kind !== 'file') continue;
            // .crswap은 슬롯 관리 대상 아님 — 즉시 정리 시도, 실패 시 재시도 큐
            if (_isSwapFile(name)) {
                swapFound++;
                try {
                    await _opfsDir.removeEntry(name);
                    swapCleaned++;
                } catch(e) {
                    swapFailed++;
                    _swapRetryQueue.add(name);
                    console.warn('[SlotStorage] swap cleanup failed (queued for retry):',
                        name, e.name || '', e.message || '');
                }
                continue; // _cache/_handles에 넣지 않음
            }
            _handles.set(name, handle);
            _cache.set(name, null); // null = 존재하지만 미로드
        }
        if (swapFound > 0) {
            console.log('[SlotStorage] OPFS swap files:', swapFound,
                '(cleaned:', swapCleaned, ', pending retry:', swapFailed, ')');
        }
        console.log('[SlotStorage] OPFS scanned: ' + _cache.size + ' files (lazy)');
    }

    // 재시도 큐 sweep — 실패했던 swap 파일 재삭제 시도
    async function _sweepSwapRetryQueue() {
        if (!_opfsDir || _swapRetryQueue.size === 0) return;
        const names = [..._swapRetryQueue];
        let cleaned = 0, stillFailed = 0;
        for (const name of names) {
            try {
                await _opfsDir.removeEntry(name);
                _swapRetryQueue.delete(name);
                cleaned++;
            } catch(e) {
                stillFailed++;
            }
        }
        if (cleaned > 0 || stillFailed > 0) {
            console.log('[SlotStorage] swap retry sweep — cleaned:', cleaned,
                ', still failed:', stillFailed);
        }
    }

    // OPFS 파일 읽기 (lazy load 핵심)
    async function _opfsRead(name) {
        try {
            let handle = _handles.get(name);
            if (!handle && _opfsDir) {
                handle = await _opfsDir.getFileHandle(name);
                _handles.set(name, handle);
            }
            if (!handle) return null;
            const file = await handle.getFile();
            return await file.text();
        } catch(e) { return null; }
    }

    async function _opfsPut(name, json) {
        if (!_opfsDir) return;
        try {
            let handle = _handles.get(name);
            if (!handle) {
                handle = await _opfsDir.getFileHandle(name, { create: true });
                _handles.set(name, handle);
            }
            const w = await handle.createWritable();
            await w.write(json);
            await w.close();
        } catch(e) { console.warn('[SlotStorage] OPFS write error:', name, e); }
    }

    async function _opfsDelete(name) {
        if (!_opfsDir) return;
        try {
            await _opfsDir.removeEntry(name);
            _handles.delete(name);
        } catch(e) {
            // NotFoundError는 이미 없는 파일 → 무시, 그 외는 경고
            if (e.name !== 'NotFoundError') {
                console.warn('[SlotStorage] OPFS delete failed:',
                    name, e.name || '', e.message || '');
            } else {
                _handles.delete(name); // 핸들만 정리
            }
        }
    }

    // ── IDB fallback ──────────────────────────────────────────────
    function _initIDB() {
        return new Promise((resolve) => {
            if (!window.indexedDB) { resolve(false); return; }
            const req = indexedDB.open(IDB_NAME, IDB_VER);
            req.onupgradeneeded = (e) => {
                if (!e.target.result.objectStoreNames.contains(IDB_STORE))
                    e.target.result.createObjectStore(IDB_STORE);
            };
            req.onerror = () => resolve(false);
            req.onsuccess = (e) => {
                _idb = e.target.result;
                // IDB도 키 목록만 먼저 스캔
                const tx = _idb.transaction(IDB_STORE, 'readonly');
                const rk = tx.objectStore(IDB_STORE).getAllKeys();
                rk.onsuccess = (ev) => {
                    for (const k of ev.target.result) {
                        const name = String(k).startsWith(PREFIX) ? String(k).slice(PREFIX.length) : String(k);
                        _cache.set(name, null); // lazy
                    }
                    resolve(_cache.size > 0);
                };
                rk.onerror = () => resolve(false);
            };
        });
    }

    // IDB lazy read
    function _idbRead(name) {
        return new Promise((resolve) => {
            if (!_idb) { resolve(null); return; }
            const tx = _idb.transaction(IDB_STORE, 'readonly');
            const req = tx.objectStore(IDB_STORE).get(PREFIX + name);
            req.onsuccess = (e) => resolve(e.target.result ?? null);
            req.onerror   = () => resolve(null);
        });
    }

    function _idbPut(name, json) {
        if (!_idb) return;
        try {
            const tx = _idb.transaction(IDB_STORE, 'readwrite');
            tx.objectStore(IDB_STORE).put(json, PREFIX + name);
        } catch(e) {}
    }

    function _idbDelete(name) {
        if (!_idb) return;
        try {
            const tx = _idb.transaction(IDB_STORE, 'readwrite');
            tx.objectStore(IDB_STORE).delete(PREFIX + name);
        } catch(e) {}
    }

    // ── LS fallback ───────────────────────────────────────────────
    function _loadLSKeysIntoCache() {
        // LS도 키 목록만 캐시에 등록 (lazy)
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                if (!k || k === META_KEY) continue;
                if (k.startsWith(PREFIX) && !k.startsWith(UM_PREFIX)) {
                    const name = k.slice(PREFIX.length);
                    _cache.set(name, null); // lazy
                }
            }
        } catch(e) {}
    }

    function _lsRead(name) {
        try { return localStorage.getItem(PREFIX + name); } catch(e) { return null; }
    }

    // ── 마이그레이션 (IDB/LS → OPFS) — 백그라운드 ────────────────
    async function _migrateToOPFS(srcMode) {
        let count = 0;
        for (const name of _cache.keys()) {
            // 이미 로드된 게 있으면 재사용, 없으면 소스에서 읽기
            let json = _cache.get(name);
            if (!json) {
                json = srcMode === 'idb' ? await _idbRead(name) : _lsRead(name);
                if (json) _cache.set(name, json);
            }
            if (json) { await _opfsPut(name, json); count++; }
        }
        // 소스 정리
        if (srcMode === 'idb' && _idb) {
            try {
                const tx = _idb.transaction(IDB_STORE, 'readwrite');
                tx.objectStore(IDB_STORE).clear();
                tx.oncomplete = () => console.log('[SlotStorage] IDB cleared after OPFS migration');
            } catch(e) {}
        } else if (srcMode === 'ls') {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const k = localStorage.key(i);
                if (k && k.startsWith(PREFIX) && !k.startsWith(UM_PREFIX) && k !== META_KEY)
                    try { localStorage.removeItem(k); } catch(e) {}
            }
        }
        console.log('[SlotStorage] ' + srcMode + '→OPFS migrated ' + count + ' files');
    }

    // ── 메인 초기화 ───────────────────────────────────────────────
    async function initStorage() {
        try {
            if (navigator.storage?.getDirectory) {
                await _initOPFS();
                _mode = 'opfs';

                if (_cache.size === 0) {
                    // OPFS 비어있음 → IDB 확인
                    const idbHas = await _initIDB();
                    if (idbHas) {
                        // IDB → OPFS 백그라운드 마이그레이션
                        setTimeout(() => _migrateToOPFS('idb'), 500);
                        console.log('[SlotStorage] mode: opfs (migrating from IDB)');
                    } else {
                        // LS 확인
                        _loadLSKeysIntoCache();
                        if (_cache.size > 0) {
                            setTimeout(() => _migrateToOPFS('ls'), 500);
                            console.log('[SlotStorage] mode: opfs (migrating from LS)');
                        } else {
                            console.log('[SlotStorage] mode: opfs (fresh)');
                        }
                    }
                } else {
                    console.log('[SlotStorage] mode: opfs (' + _cache.size + ' files, lazy)');
                }
                _ready = true;
                _flushPending();
                return;
            }
        } catch(e) {
            console.warn('[SlotStorage] OPFS failed, trying IDB:', e);
        }

        // IDB fallback
        try {
            const idbOk = await _initIDB();
            if (idbOk || window.indexedDB) {
                _mode = 'idb';
                if (_cache.size === 0) {
                    _loadLSKeysIntoCache();
                    // LS → IDB 마이그레이션
                    if (_cache.size > 0 && _idb) {
                        setTimeout(async () => {
                            for (const name of _cache.keys()) {
                                const json = _lsRead(name);
                                if (json) { _cache.set(name, json); _idbPut(name, json); }
                            }
                            for (let i = localStorage.length - 1; i >= 0; i--) {
                                const k = localStorage.key(i);
                                if (k && k.startsWith(PREFIX) && !k.startsWith(UM_PREFIX) && k !== META_KEY)
                                    try { localStorage.removeItem(k); } catch(e2) {}
                            }
                        }, 500);
                    }
                }
                console.log('[SlotStorage] mode: idb (' + _cache.size + ' keys, lazy)');
                _ready = true;
                _flushPending();
                return;
            }
        } catch(e) {
            console.warn('[SlotStorage] IDB failed, using LS:', e);
        }

        // LS 최후 fallback
        _loadLSKeysIntoCache();
        _mode = 'ls';
        console.log('[SlotStorage] mode: ls (' + _cache.size + ' items)');
        _ready = true;
        _flushPending();
    }


    function _flushPending() {
        if (!_pendingFlush) return;
        const entries = Object.entries(_pendingFlush);
        _pendingFlush = null;
        for (const [name, json] of entries) {
            console.log('[SlotStorage] flushing pending write:', name);
            _backendPut(name, json);
        }
    }

    function initIDB() { return initStorage(); }

    // ── Backend write/delete ──────────────────────────────────────
    function _backendPut(name, json) {
        if (_mode === 'opfs')     _opfsPut(name, json);
        else if (_mode === 'idb') _idbPut(name, json);
        else { try { localStorage.setItem(PREFIX + name, json); } catch(e) {} }
    }

    function _backendDelete(name) {
        if (_mode === 'opfs')     _opfsDelete(name);
        else if (_mode === 'idb') _idbDelete(name);
        else { try { localStorage.removeItem(PREFIX + name); } catch(e) {} }
    }

    // ── LS saveMetadata QuotaExceeded 대응 ───────────────────────
    function _purgeLSSlotData() {
        // 슬롯 데이터 제거 — tmp 백업은 튕김 복구용이므로 제외
        try {
            const toRemove = [];
            for (let i = 0; i < localStorage.length; i++) {
                const k = localStorage.key(i);
                if (!k || k === META_KEY) continue;
                // PREFIX 슬롯 데이터 (UM_PREFIX, tmp 제외)
                if (k.startsWith(PREFIX) && !k.startsWith(UM_PREFIX)) { toRemove.push(k); continue; }
                // usekit_tmp_ 는 튕김 복구용 — purge 제외
            }
            toRemove.forEach(k => { try { localStorage.removeItem(k); } catch(e) {} });
            if (toRemove.length) console.log('[SlotStorage] purged ' + toRemove.length + ' LS keys (slot data)');
        } catch(e) {}
    }

    // tmp 백업만 제거 (saveMetadata 최후 수단 — tmp 희생 후 meta 저장)
    function _purgeLSTmp() {
        try {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const k = localStorage.key(i);
                if (k && k.startsWith('usekit_tmp_')) {
                    try { localStorage.removeItem(k); } catch(e) {}
                }
            }
            console.log('[SlotStorage] purged tmp backups (last resort)');
        } catch(e) {}
    }

    // ── Metadata R/W (localStorage 유지) ──────────────────────────
    function _stripStateText(state) {
        // state.text (전체 파일 내용) 는 별도 storage에 저장 — 메타에 포함 시 Quota 초과
        if (!state) return null;
        const { text: _omit, ...rest } = state;
        return rest;
    }

    function saveMetadata(slots, activeIdx, winStart, uiState) {
        const payload = JSON.stringify({
            slots: slots.map(s => ({
                slotIndex:  s.slotIndex,
                storage:    s.storage,
                fileName:   s.fileName,
                isDirty:    s.isDirty,
                usekitPath: s.usekitPath || '',
                state:      _stripStateText(s.state),
            })),
            activeSlotIndex: activeIdx,
            windowStart:     winStart,
            uiState:         uiState || null,
            lastModified:    Date.now(),
        });
        try {
            localStorage.setItem(META_KEY, payload);
        } catch(e) {
            _purgeLSSlotData();
            try { localStorage.setItem(META_KEY, payload); }
            catch(e2) {
                // 여전히 실패 — uiState 제외 후 최소 페이로드로 재시도
                try {
                    const minimal = JSON.stringify({
                        slots: slots.map(s => ({
                            slotIndex: s.slotIndex, storage: s.storage,
                            fileName: s.fileName, isDirty: s.isDirty,
                            usekitPath: s.usekitPath || '', state: null,
                        })),
                        activeSlotIndex: activeIdx,
                        windowStart: winStart,
                        uiState: null,
                        lastModified: Date.now(),
                    });
                    localStorage.setItem(META_KEY, minimal);
                    console.warn('[SlotStorage.saveMetadata] saved minimal (no state/uiState)');
                } catch(e3) {
                    // 최후 수단: tmp 백업 희생 후 최소 메타 저장
                    _purgeLSTmp();
                    try { localStorage.setItem(META_KEY, minimal); }
                    catch(e4) { console.warn('[SlotStorage.saveMetadata] all retries failed', e4); }
                }
            }
        }
    }

    function loadMetadata() {
        try {
            const raw = localStorage.getItem(META_KEY);
            if (!raw) return { slots: [], activeSlotIndex: 0, windowStart: 0 };
            const d = JSON.parse(raw);
            return {
                slots:           Array.isArray(d.slots) ? d.slots : [],
                activeSlotIndex: d.activeSlotIndex || 0,
                windowStart:     d.windowStart     || 0,
                uiState:         d.uiState         || null,
            };
        } catch(e) { return { slots: [], activeSlotIndex: 0, windowStart: 0 }; }
    }

    // ── Local slot data API ───────────────────────────────────────

    // readLocal: 동기 우선, 캐시 미스 시 null 반환 (비동기 필요 시 readLocalAsync)
    function readLocal(name) {
        try {
            const cached = _cache.get(name);
            if (cached) return JSON.parse(cached); // 캐시 히트
            if (!_cache.has(name)) return null;    // 존재하지 않음
            // null = 존재하지만 미로드 → 동기로는 LS만 가능
            if (_mode === 'ls') {
                const raw = _lsRead(name);
                if (raw) { _cache.set(name, raw); return JSON.parse(raw); }
            }
            // OPFS/IDB: 동기 불가 → null 반환 (caller가 readLocalAsync 써야 함)
            return null;
        } catch(e) { return null; }
    }

    // readLocalAsync: OPFS/IDB lazy load
    async function readLocalAsync(name) {
        try {
            const cached = _cache.get(name);
            if (cached) return JSON.parse(cached);
            if (!_cache.has(name)) return null;

            let raw = null;
            if (_mode === 'opfs')     raw = await _opfsRead(name);
            else if (_mode === 'idb') raw = await _idbRead(name);
            else                      raw = _lsRead(name);

            if (raw) { _cache.set(name, raw); return JSON.parse(raw); }
            return null;
        } catch(e) { return null; }
    }

    function writeLocal(name, data) {
        try {
            const json = JSON.stringify(data);
            _cache.set(name, json);
            if (!_ready || !_mode) {
                _pendingFlush = _pendingFlush || {};
                _pendingFlush[name] = json;
                console.warn('[SlotStorage] writeLocal before ready, queued:', name);
            } else {
                _backendPut(name, json);
            }
            return true;
        } catch(e) {
            window.UI?.showToast?.('Write failed: ' + (e.message || e.name || 'unknown'), 3000);
            return false;
        }
    }

    function removeLocal(name) {
        _cache.delete(name);
        _handles.delete(name);
        _backendDelete(name);
    }

    function localKeyExists(name) { return _cache.has(name); }

    function migrateLocalKey(oldName, newName, { allowOverwrite = false } = {}) {
        try {
            if (oldName === newName) return true;
            const oldVal = _cache.get(oldName);
            if (_cache.has(newName) && !allowOverwrite) return false;
            if (oldVal !== undefined) {
                _cache.set(newName, oldVal);
                _cache.delete(oldName);
                if (_handles.has(oldName)) {
                    _handles.delete(oldName); // 새 handle은 write 시 생성
                }
                if (oldVal) _backendPut(newName, oldVal);
                _backendDelete(oldName);
            }
            return true;
        } catch(e) { return false; }
    }

    // ── Listing ───────────────────────────────────────────────────
    // 로컬파일만 (slot_ prefix 제외)
    function listLocalSlotNames() {
        return [..._cache.keys()].filter(k => !k.startsWith('slot_'));
    }

    // ── Slot-file API (슬롯 전용 작업본, prefix: "slot_") ─────────
    // 사용자에게는 같은 이름으로 보이나, 내부 저장 key는 "slot_" + name
    const SLOT_PREFIX = 'slot_';

    function _slotKey(name) { return SLOT_PREFIX + name; }

    function writeSlot(name, data) {
        return writeLocal(_slotKey(name), data);
    }

    function readSlot(name) {
        return readLocal(_slotKey(name));
    }

    async function readSlotAsync(name) {
        return readLocalAsync(_slotKey(name));
    }

    function removeSlot(name) {
        removeLocal(_slotKey(name));
    }

    function migrateSlotKey(oldName, newName) {
        return migrateLocalKey(_slotKey(oldName), _slotKey(newName), { allowOverwrite: true });
    }

    // 슬롯파일 목록 — "slot_" prefix 제거해서 반환
    function listSlotFileNames() {
        return [..._cache.keys()]
            .filter(k => k.startsWith(SLOT_PREFIX))
            .map(k => k.slice(SLOT_PREFIX.length));
    }

    // ── Chat-file API (챗 기록 저장, prefix: "chat_") ─────────────
    const CHAT_PREFIX = 'chat_';

    function _chatKey(name) { return CHAT_PREFIX + name; }

    function writeChat(name, data) {
        return writeLocal(_chatKey(name), data);
    }

    function readChat(name) {
        return readLocal(_chatKey(name));
    }

    async function readChatAsync(name) {
        return readLocalAsync(_chatKey(name));
    }

    function removeChat(name) {
        removeLocal(_chatKey(name));
    }

    function migrateChatKey(oldName, newName) {
        return migrateLocalKey(_chatKey(oldName), _chatKey(newName), { allowOverwrite: true });
    }

    // 챗파일 목록 — "chat_" prefix 제거해서 반환
    function listChatFileNames() {
        return [..._cache.keys()]
            .filter(k => k.startsWith(CHAT_PREFIX))
            .map(k => k.slice(CHAT_PREFIX.length));
    }

    // ── Meta helpers ──────────────────────────────────────────────
    function getLocalOnlyMeta(name) {
        try {
            const d = readLocal(name);
            if (!d) return { timestamp: 0, chars: 0, lines: 0 };
            const text = d.text || '';
            return { timestamp: Number(d.timestamp || 0), chars: text.length, lines: text ? text.split('\n').length : 0 };
        } catch(e) { return { timestamp: 0, chars: 0, lines: 0 }; }
    }

    async function getLocalOnlyMetaAsync(name) {
        try {
            const d = (readLocal(name)) || (await readLocalAsync(name));
            if (!d) return { timestamp: 0, chars: 0, lines: 0 };
            const text = d.text || '';
            return { timestamp: Number(d.timestamp || 0), chars: text.length, lines: text ? text.split('\n').length : 0 };
        } catch(e) { return { timestamp: 0, chars: 0, lines: 0 }; }
    }

    // ── Sanitize filename ─────────────────────────────────────────
    function sanitizeFileName(name) {
        return String(name || '').trim()
            .replace(/\s+/g, '_')
            .replace(/[^\p{L}\p{N}._-]/gu, '_')
            .replace(/_+/g, '_')
            .replace(/^_+|_+$/g, '');
    }

    function getMode() { return _mode; }

    return {
        PREFIX, META_KEY,
        toast, formatTime,
        initIDB,
        getMode,
        saveMetadata, loadMetadata,
        readLocal, readLocalAsync, writeLocal, removeLocal, localKeyExists, migrateLocalKey,
        listLocalSlotNames,
        writeSlot, readSlot, readSlotAsync, removeSlot, migrateSlotKey, listSlotFileNames,
        writeChat, readChat, readChatAsync, removeChat, migrateChatKey, listChatFileNames,
        getLocalOnlyMeta, getLocalOnlyMetaAsync,
        sanitizeFileName,
        sweepSwapFiles: _sweepSwapRetryQueue,
    };
})();

window.SlotStorage = SlotStorage;
