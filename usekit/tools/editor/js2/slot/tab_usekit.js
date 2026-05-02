/* Path: usekit/tools/editor/js/io/slot/tab_usekit.js
 * USEKIT 탭 - 아코디언 폴더 트리
 * buildItems() → slot_popup.js의 render()에서 호출
 */
(function () {
    'use strict';

    function _ensureNav() {
        if (!window._usekitNav) {
            window._usekitNav = {
                rootPath:            '/',
                currentPath:         '/_tmp/',
                usekitBase:          '',
                viewMode:            'folders-first',
                dirs:                [],
                files:               [],
                fileMetas:           {},
                lastError:           '',
                _skipFetchOnce:      false,
                _initialDirApplied:  false,
            };
        }
        return window._usekitNav;
    }

    // usekitBase + rootPath 최신화 (buildItems 시점에 호출)
    function _syncUsekitBase(nav) {
        try {
            const ping = window._usekitPing;
            if (ping?.usekit_base) {
                nav.usekitBase = ping.usekit_base.replace(/\/+$/, '');
            }
            if (nav.useAbs) return;
            // rootPath: 항상 USEKIT_BASE 루트 (빈 문자열 or "/" → "/_root/")
            // default_usekit_rel_dir은 "" なので rootPath は "/" に固定
            const rootRel = ping?.default_usekit_rel_dir ?? '';
            const root = rootRel
                ? '/' + rootRel.replace(/^\//, '').replace(/\/?$/, '/')
                : '/';
            if (nav.rootPath !== root) {
                nav.rootPath = root;
            }
            // initial_dir: 로드 팝업이 처음 열릴 때 이동할 폴더 (한 번만 적용)
            if (!nav._initialDirApplied && ping?.initial_dir) {
                const initRel = ping.initial_dir.replace(/^\//, '').replace(/\/?$/, '/');
                const initPath = '/' + initRel;
                // rootPath 하위인지 확인 후 적용
                if (initPath.startsWith(nav.rootPath)) {
                    nav.currentPath = initPath;
                }
                nav._initialDirApplied = true;
            }
        } catch (e) {}
    }

    // sandbox path → 절대경로
    function toAbsPath(nav, sandboxPath) {
        if (nav.useAbs) return sandboxPath || '';
        if (!nav.usekitBase || !sandboxPath) return sandboxPath || '';
        const rel = sandboxPath.startsWith('/') ? sandboxPath.slice(1) : sandboxPath;
        const base = nav.usekitBase.replace(/\/+$/, '');
        return rel ? base + '/' + rel : base + '/';
    }

    // usekitBase 루트인지 판단 → ↑ 버튼 상한
    function isAtUsekitBase(nav, dir) {
        if (!nav.usekitBase || !dir) return false;
        const absDir = toAbsPath(nav, dir).replace(/\/+$/, '');
        const base   = nav.usekitBase.replace(/\/+$/, '');
        return absDir === base;
    }

    // ===== PATH HELPERS =====

    function normDir(nav, p) {
        let x = String(p || '').replace(/\\/g, '/').trim();
        if (!x) x = nav.rootPath;
        if (!x.startsWith('/')) x = '/' + x;
        x = x.replace(/\/{2,}/g, '/');
        if (x.includes('..')) return null;
        // rootPath가 "/" 면 모든 절대경로 허용, 아니면 하위 경로만 허용
        if (nav.rootPath !== '/' && !x.startsWith(nav.rootPath)) return null;
        if (!x.endsWith('/')) x += '/';
        return x;
    }

    function parentDir(nav, dir) {
        const d = normDir(nav, dir);
        if (!d || d === nav.rootPath || d === '/') return nav.rootPath;
        if (isAtUsekitBase(nav, d)) return nav.rootPath;
        const parts = d.split('/').filter(Boolean);
        parts.pop();
        if (!parts.length) return nav.rootPath;
        const parent = normDir(nav, '/' + parts.join('/') + '/') || nav.rootPath;
        if (isAtUsekitBase(nav, parent) || !normDir(nav, parent)) return nav.rootPath;
        return parent;
    }

    function joinPath(nav, baseDir, name) {
        const b = normDir(nav, baseDir);
        if (!b) return null;
        const n = String(name || '').replace(/\\/g, '/').replace(/^\/+/, '');
        if (!n) return b;
        return b + n;
    }

    // ===== FETCH =====

    async function fetchList(nav) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 1500);
        try {
            const endpoint = nav.useAbs ? '/api/list_abs' : '/api/list';
            const url = `${endpoint}?path=${encodeURIComponent(nav.currentPath)}`;
            const resp = await fetch(url, { signal: controller.signal });
            const data = await resp.json();
            if (data && data.ok) {
                nav.dirs      = Array.isArray(data.dirs)  ? data.dirs  : [];
                nav.files     = Array.isArray(data.files) ? data.files : [];
                // file_metas: [{name, size, mtime}] → map
                nav.fileMetas = {};
                if (Array.isArray(data.file_metas)) {
                    data.file_metas.forEach(m => { nav.fileMetas[m.name] = m; });
                }
                nav.lastError = '';
                // useAbs nav(STORAGE)는 서버 응답 path로 currentPath 덮어쓰지 않음
                if (!nav.useAbs && typeof data.path === 'string') {
                    const np = normDir(nav, data.path);
                    if (np) nav.currentPath = np;
                }
                return true;
            }
            nav.dirs = []; nav.files = []; nav.fileMetas = {};
            nav.lastError = (data && data.error) ? String(data.error) : 'LIST_FAILED';
            return false;
        } catch (e) {
            nav.dirs = []; nav.files = []; nav.fileMetas = {};
            nav.lastError = (e && e.name === 'AbortError') ? 'TIMEOUT' : 'SERVER_DOWN';
            return false;
        } finally {
            clearTimeout(timer);
        }
    }

    // ===== DELETE FILE via /api/delete =====

    async function deleteUsekitFile(absClientPath) {
        try {
            const resp = await fetch(`/api/delete?path=${encodeURIComponent(absClientPath)}`, { method: 'DELETE' });
            const data = await resp.json().catch(() => ({}));
            return !!(data && data.ok);
        } catch (e) {
            return false;
        }
    }

    // expose for slot_popup
    window.IOSlotUsekitTab = window.IOSlotUsekitTab || {};
    window.IOSlotUsekitTab.deleteFile = deleteUsekitFile;

    // ===== BUILD ITEMS =====

    async function buildItems(opts) {
        opts = opts || {};
        const q   = String(opts.filterText || '').trim().toLowerCase();
        const nav = opts.nav || _ensureNav();

        _syncUsekitBase(nav);  // 매번 최신 usekit_base 반영
        nav.currentPath = normDir(nav, nav.currentPath) || nav.rootPath;

        if (nav._skipFetchOnce) {
            nav._skipFetchOnce = false;
        } else {
            await fetchList(nav);
        }

        const atRoot     = nav.currentPath === nav.rootPath || isAtUsekitBase(nav, nav.currentPath);
        const parentPath = parentDir(nav, nav.currentPath);

        const items = [];

        // ── 상위폴더 행 ──────────────────────────────────────────────────
        items.push({
            type:     'nav_parent',
            name:     atRoot ? '/' : parentPath,
            _isEntry: false,
            noFilter: true,
            disabled: atRoot,
            meta:     {},
        });

        // ── 현재폴더 행 + 토글 ───────────────────────────────────────────
        items.push({
            type:     'nav_current',
            name:     nav.currentPath,
            _isEntry: false,
            noFilter: true,
            viewMode: nav.viewMode,
            meta:     {},
        });

        // ── 구분선 ────────────────────────────────────────────────────────
        items.push({ type: 'separator', name: '', noFilter: true, _isEntry: false, meta: {} });

        // ── 폴더/파일 목록 ────────────────────────────────────────────────
        const sortAZ = (a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });

        const dirs  = (nav.dirs  || []).map(String).filter(Boolean).sort(sortAZ);
        const files = (nav.files || []).map(String).filter(Boolean).sort(sortAZ);

        const dirItems = dirs.map(dn => ({
            type:     'dir',
            name:     dn.replace(/\/$/, ''),   // 표시는 슬래시 없이
            _rawName: dn.replace(/\/$/, ''),
            path:     joinPath(nav, nav.currentPath, dn),
            _isEntry: true,
            meta:     {},
        })).filter(x => x.path);

        const fileItems = files.map(fn => {
            const fm   = nav.fileMetas[fn] || {};
            const size = Number(fm.size  || 0);
            const mtime = Number(fm.mtime || 0);
            // 줄수는 서버가 안 주므로 생략, chars 대신 size(bytes) 표시
            return {
                type:     'file',
                name:     fn,
                _rawName: fn,
                path:     joinPath(nav, nav.currentPath, fn),
                _isEntry: true,
                canDel:   true,
                meta: {
                    timestamp: mtime,
                    size,
                    // lines 생략 (서버가 안 줌)
                },
            };
        }).filter(x => x.path);

        const ordered = nav.viewMode === 'files-first'
            ? [...fileItems, ...dirItems]
            : [...dirItems, ...fileItems];

        const filtered = q
            ? ordered.filter(it => String(it._rawName || '').toLowerCase().includes(q))
            : ordered;

        items.push(...filtered);

        // ── 오류/빈 상태 ──────────────────────────────────────────────────
        if (!filtered.length) {
            items.push({
                type:     'info',
                name:     nav.lastError ? `(${nav.lastError})` : '(empty folder)',
                noFilter: true,
                _isEntry: false,
                meta:     {},
            });
        }

        const absPathText = toAbsPath(nav, nav.currentPath) || nav.currentPath;
        return { items, pathText: absPathText };
    }

    window.IOSlotUsekitTab.buildItems = buildItems;
})();
