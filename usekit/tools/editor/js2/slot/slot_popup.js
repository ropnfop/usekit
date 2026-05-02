// slot_popup.js
// Load modal: SLOT / LOCAL / USEKIT / STORAGE tabs + preview panel
// Depends on: SlotStorage, SlotUsekit, IOSlotUsekitTab, Editor
//
// UM tab removed (OPFS migration completed — no more orphan meta cleanup needed)

const SlotPopup = (function () {
    'use strict';

    // ═══════════════════════════════════════════════════════════════
    //  [1] CONFIRM / DIFF modal helpers (module scope — reused)
    // ═══════════════════════════════════════════════════════════════

    function _confirm(msg, onOk, { okLabel = 'OK', cancelHide = false } = {}) {
        const modal   = document.getElementById('confirmModal');
        const msgEl   = document.getElementById('confirmModalMessage');
        const titleEl = document.getElementById('confirmModalTitle');
        const btnOk   = document.getElementById('btnConfirmModalOk');
        const btnCncl = document.getElementById('btnConfirmModalCancel');
        const btnX    = document.getElementById('btnConfirmModalClose');
        if (!modal) { if (window.confirm(msg)) onOk(); return; }

        if (titleEl) titleEl.textContent = 'Confirm';
        if (msgEl)   msgEl.textContent   = msg;
        if (btnOk) {
            btnOk.textContent = okLabel;
            btnOk.classList.toggle('modal-btn-danger', okLabel !== 'OK');
        }
        if (btnCncl) btnCncl.style.display = cancelHide ? 'none' : '';

        const close = () => {
            modal.style.display = 'none';
            if (btnOk)   btnOk.onclick = null;
            if (btnCncl) btnCncl.style.display = '';
        };
        if (!modal.dataset.cfBound) {
            modal.dataset.cfBound = '1';
            modal.addEventListener('click', e => { if (e.target === modal) close(); });
            btnX?.addEventListener('click', close);
            btnCncl?.addEventListener('click', close);
        }
        if (btnOk) btnOk.onclick = () => { close(); onOk(); };
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
    }

    function _openDiff(name, slotText, localText, onLoadLocal, onLoadSlot, labels) {
        const modal    = document.getElementById('diffModal');
        const metaEl   = document.getElementById('diffModalMeta');
        const slotEl   = document.getElementById('diffModalSlot');
        const localEl  = document.getElementById('diffModalLocal');
        const btnOk    = document.getElementById('btnDiffModalOk');
        const btnSlot  = document.getElementById('btnDiffModalSlot');
        const btnX     = document.getElementById('btnDiffModalClose');
        const lblSlot  = document.getElementById('diffModalLabelSlot');
        const lblLocal = document.getElementById('diffModalLabelLocal');
        const titleEl  = document.getElementById('diffModalTitle');
        if (!modal) { onLoadLocal(); return; }

        const _lSlot    = labels?.[0] || 'Slot';
        const _lLocal   = labels?.[1] || 'Local';
        const _sfxSlot  = labels?.[4] ?? 'current';
        const _sfxLocal = labels?.[5] ?? 'saved';
        if (titleEl)  titleEl.textContent  = labels?.[6] || 'Load Local Version?';
        if (lblSlot)  lblSlot.textContent  = `${_lSlot.toUpperCase()} (${_sfxSlot})`;
        if (lblLocal) lblLocal.textContent = `${_lLocal.toUpperCase()} (${_sfxLocal})`;
        if (btnSlot)  btnSlot.textContent  = labels?.[2] || 'Load Slot';
        if (btnOk)    btnOk.textContent    = labels?.[3] || 'Load Local';

        const slotLines  = slotText  ? slotText.split('\n').length  : 0;
        const localLines = localText ? localText.split('\n').length : 0;
        if (metaEl)  metaEl.textContent  = `${name}  ·  ${_lSlot}: ${slotLines}ln  →  ${_lLocal}: ${localLines}ln`;
        if (slotEl)  slotEl.textContent  = slotText  || '(empty)';
        if (localEl) localEl.textContent = localText || '(empty)';

        const close = () => {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        };
        if (!modal.dataset.diffBound) {
            modal.dataset.diffBound = '1';
            modal.addEventListener('click', e => { if (e.target === modal) close(); });
        }
        btnX.onclick = close;
        if (btnOk)   btnOk.onclick   = () => { close(); onLoadLocal(); };
        if (btnSlot) btnSlot.onclick = () => { close(); if (onLoadSlot) onLoadSlot(); };
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
    }

    // ═══════════════════════════════════════════════════════════════
    //  [2] FAVORITES (module scope — in-progress, preserved as-is)
    // ═══════════════════════════════════════════════════════════════

    const FAV_KEYS = { local: 'usekit_fav_local', slot: 'usekit_fav_slot' };

    function _getFavSet(tab) {
        const key = FAV_KEYS[tab];
        if (!key) return new Set();
        try { return new Set(JSON.parse(localStorage.getItem(key) || '[]')); }
        catch { return new Set(); }
    }
    function _saveFavSet(set, tab) {
        const key = FAV_KEYS[tab];
        if (key) localStorage.setItem(key, JSON.stringify([...set]));
    }
    function _toggleFav(name, tab) {
        const s = _getFavSet(tab);
        if (s.has(name)) s.delete(name); else s.add(name);
        _saveFavSet(s, tab);
    }
    function _isFav(name, tab) { return _getFavSet(tab).has(name); }
    function _removeFavAll(name) {
        Object.values(FAV_KEYS).forEach(key => {
            try {
                const arr = JSON.parse(localStorage.getItem(key) || '[]');
                const next = arr.filter(n => n !== name);
                if (next.length !== arr.length) localStorage.setItem(key, JSON.stringify(next));
            } catch {}
        });
        try {
            const bms = JSON.parse(localStorage.getItem('usekit_bookmarks') || '[]');
            const next = bms.filter(b => b.fileName !== name);
            if (next.length !== bms.length) localStorage.setItem('usekit_bookmarks', JSON.stringify(next));
        } catch {}
    }

    function _cleanupOrphanFavs(api) {
        try {
            const slotNames  = new Set((api.getSlots?.() || []).map(s => s.fileName));
            const localNames = new Set(SlotStorage.listLocalSlotNames?.() || []);

            // fav_slot: slot에 없는 항목 제거
            try {
                const arr  = JSON.parse(localStorage.getItem('usekit_fav_slot') || '[]');
                const next = arr.filter(n => slotNames.has(n));
                if (next.length !== arr.length) localStorage.setItem('usekit_fav_slot', JSON.stringify(next));
            } catch {}
            // bookmarks: slot + local 모두에 없으면 제거
            try {
                const arr  = JSON.parse(localStorage.getItem('usekit_bookmarks') || '[]');
                const next = arr.filter(b => slotNames.has(b.fileName) || localNames.has(b.fileName));
                if (next.length !== arr.length) localStorage.setItem('usekit_bookmarks', JSON.stringify(next));
            } catch {}
        } catch(e) { console.warn('[SlotPopup] orphan cleanup failed', e); }
    }

    // ═══════════════════════════════════════════════════════════════
    //  [3] UTIL
    // ═══════════════════════════════════════════════════════════════

    function _fmtSize(bytes) {
        if (!bytes) return '';
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes/1024).toFixed(1)}K`;
        return `${(bytes/1024/1024).toFixed(1)}M`;
    }

    function _ensureStorageNav() {
        if (!window._storageNav) {
            window._storageNav = {
                rootPath:       '/storage/emulated/0/',
                currentPath:    '/storage/emulated/0/',
                usekitBase:     '',
                useAbs:         true,
                viewMode:       'folders-first',
                dirs:           [],
                files:          [],
                fileMetas:      {},
                lastError:      '',
                _skipFetchOnce: false,
            };
        }
    }

    // ── Drag mode state (module scope — shared across open() calls) ──
    let _dragMode    = false;
    let _dragDiv     = null;
    let _dragOrigIdx = -1;

    // ═══════════════════════════════════════════════════════════════
    //  [4] MAIN — open(api)
    // ═══════════════════════════════════════════════════════════════

    function open(api) {
        _cleanupOrphanFavs(api);
        _ensureStorageNav();

        // ── DOM refs ──────────────────────────────────────────────
        const modal     = document.getElementById('loadModal');
        const listEl    = document.getElementById('loadModalList');
        const searchEl  = document.getElementById('loadModalSearch');
        const pathEl    = document.getElementById('loadModalPath');
        const countEl   = document.getElementById('loadModalCount');
        const btnX      = document.getElementById('btnLoadModalClose');
        const btnCncl   = document.getElementById('btnLoadModalCancel');
        const btnCheck  = document.getElementById('btnLoadModalCheck');
        const btnDelSel = document.getElementById('btnLoadModalDeleteSelected');
        const titleEl   = document.getElementById('loadModalTitle');
        const tabSlot    = document.getElementById('loadTabSlot');
        const tabLocal   = document.getElementById('loadTabLocal');
        const tabUsekit  = document.getElementById('loadTabUsekit');
        const tabStorage = document.getElementById('loadTabStorage');
        if (!modal || !listEl) return;

        // ── State ─────────────────────────────────────────────────
        let currentTab   = 'slot';
        let _checkMode   = false;
        let _sortMode    = 'slot';
        let _filterDirty = false;
        let _filterFav   = false;
        let _previewItem = null;
        const _selected  = new Set();

        // ── Drag mode reset ──────────────────────────────────────
        _dragMode = false; _dragDiv = null; _dragOrigIdx = -1;

        function _enterDragMode(div, slotIdx) {
            _dragMode = true;
            _dragDiv = div;
            _dragOrigIdx = slotIdx;
            // 선택 아이템 시각 효과
            div.style.transition = 'transform 0.15s, opacity 0.15s, box-shadow 0.15s';
            div.style.transform = 'scale(0.95)';
            div.style.opacity = '0.7';
            div.style.zIndex = '99';
            div.style.position = 'relative';
            div.style.boxShadow = '0 4px 16px rgba(0,0,0,0.4)';
            // 좌측 아이콘 → 체크
            const leftEl = div.querySelector('.item-left');
            if (leftEl) {
                leftEl._origHTML = leftEl.innerHTML;
                leftEl.innerHTML = '<span class="item-check active-check">✓</span>';
            }
            // 타이틀 변경
            if (titleEl) titleEl.textContent = 'DRAG';
            if (countEl) countEl.style.display = 'none';
            // Close → Done
            if (btnCncl) btnCncl.textContent = 'Done';
            try { navigator.vibrate?.(15); } catch(ex) {}
        }

        function _exitDragMode(applyMove) {
            if (!_dragMode) return;
            if (applyMove && _dragDiv && listEl) {
                const allItems = [...listEl.querySelectorAll('.modal-item')];
                const finalPos = allItems.indexOf(_dragDiv);
                if (finalPos >= 0 && finalPos !== _dragOrigIdx) {
                    api.moveSlot(_dragOrigIdx, finalPos);
                }
            }
            // 스타일 복원
            if (_dragDiv) {
                _dragDiv.style.transform = '';
                _dragDiv.style.opacity = '';
                _dragDiv.style.zIndex = '';
                _dragDiv.style.position = '';
                _dragDiv.style.boxShadow = '';
                setTimeout(() => { if (_dragDiv) _dragDiv.style.transition = ''; }, 160);
            }
            _dragMode = false;
            _dragDiv = null;
            _dragOrigIdx = -1;
            // 타이틀 복원
            if (titleEl) titleEl.textContent = 'LOAD';
            if (countEl) countEl.style.display = '';
            // Done → Close
            if (btnCncl) btnCncl.textContent = 'Close';
            render(searchEl?.value || '');
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-a] CLOSE / CHECK MODE
        // ═══════════════════════════════════════════════════════════

        function closeModal() {
            _closePreview();
            _setCheckMode(false);
            _exitDragMode(false);
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        }

        function _setCheckMode(on) {
            _checkMode = on;
            _selected.clear();
            btnCheck?.classList.toggle('active', on);
            listEl.classList.toggle('check-mode', on);
            // LOCAL 탭에서만 체크모드 활성
            const canCheck = currentTab === 'local';
            if (btnDelSel) btnDelSel.style.display = (on && canCheck) ? '' : 'none';
            if (btnCheck)  btnCheck.style.display  = canCheck ? '' : 'none';
            listEl.querySelectorAll('.modal-item').forEach(el => el.classList.remove('check-selected'));
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-b] TABS
        // ═══════════════════════════════════════════════════════════

        function switchTab(tab) {
            _closePreview();
            _setCheckMode(false);
            _filterDirty = false;
            _filterFav   = false;
            const fdEl = document.getElementById('loadFilterDirty');
            if (fdEl) fdEl.checked = false;
            const ffEl = document.getElementById('loadFilterFav');
            if (ffEl) ffEl.checked = false;

            _sortMode = (tab === 'slot') ? 'slot' : 'latest';
            document.querySelectorAll('.load-sort-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.sort === _sortMode);
            });

            currentTab = tab;
            [tabSlot, tabLocal, tabUsekit, tabStorage].forEach(b => b?.classList.remove('active'));
            const map = { slot: tabSlot, local: tabLocal, usekit: tabUsekit, storage: tabStorage };
            map[tab]?.classList.add('active');

            if (searchEl) searchEl.value = '';
            render('');
        }

        function _bindTab(el, name) {
            if (el && !el.dataset.tabBound) {
                el.dataset.tabBound = '1';
                el.addEventListener('click', () => switchTab(name));
            }
        }
        _bindTab(tabSlot,    'slot');
        _bindTab(tabLocal,   'local');
        _bindTab(tabUsekit,  'usekit');
        _bindTab(tabStorage, 'storage');

        // ═══════════════════════════════════════════════════════════
        //  [4-c] MODAL EVENT BINDINGS (once per modal)
        // ═══════════════════════════════════════════════════════════

        if (!modal.dataset.spBound) {
            modal.dataset.spBound = '1';
            modal.addEventListener('click', e => { if (e.target === modal) { if (_dragMode) _exitDragMode(true); else closeModal(); } });
            btnX?.addEventListener('click', () => { if (_dragMode) _exitDragMode(false); else closeModal(); });
            btnCncl?.addEventListener('click', () => { if (_dragMode) _exitDragMode(true); else closeModal(); });
            btnCheck?.addEventListener('click', () => _setCheckMode(!_checkMode));
            btnDelSel?.addEventListener('click', () => {
                if (!_selected.size) return;
                const names = [..._selected];
                _confirm(`Delete ${names.length} item(s)?`, () => {
                    if (currentTab === 'local') {
                        names.forEach(n => { _removeFavAll(n); api.deleteLocalSlot(n); });
                    }
                    _setCheckMode(false);
                    render(searchEl?.value || '');
                }, { okLabel: 'Delete' });
            });
            // 정렬 버튼
            document.querySelectorAll('.load-sort-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    _sortMode = btn.dataset.sort;
                    document.querySelectorAll('.load-sort-btn').forEach(b => b.classList.toggle('active', b === btn));
                    render(searchEl?.value || '');
                });
            });
            document.getElementById('loadFilterDirty')?.addEventListener('change', e => {
                _filterDirty = e.target.checked;
                render(searchEl?.value || '');
            });
            document.getElementById('loadFilterFav')?.addEventListener('change', e => {
                _filterFav = e.target.checked;
                render(searchEl?.value || '');
            });
            document.addEventListener('keydown', e => {
                if (modal.style.display !== 'none' && e.key === 'Escape') closeModal();
            });
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-d] PREVIEW PANEL
        // ═══════════════════════════════════════════════════════════

        function _ensurePreview() {
            const modalEl = modal.querySelector('.modal');
            if (!modalEl) return null;
            let panel = modalEl.querySelector('.modal-preview');
            if (panel) return panel;
            panel = document.createElement('div');
            panel.className = 'modal-preview';
            panel.innerHTML = `
                <div class="modal-preview-header">
                    <span class="modal-preview-name"></span>
                    <button class="modal-preview-close" aria-label="Close">×</button>
                </div>
                <div class="modal-preview-meta"></div>
                <div class="modal-preview-content">loading...</div>
                <div class="modal-preview-actions">
                    <button class="modal-preview-btn open">OPEN</button>
                    <button class="modal-preview-btn del">DEL</button>
                </div>`;
            panel.querySelector('.modal-preview-close').addEventListener('click', _closePreview);
            modalEl.appendChild(panel);
            return panel;
        }

        function _closePreview() {
            _previewItem = null;
            const panel = modal.querySelector('.modal-preview');
            if (panel) panel.classList.remove('open');
        }

        function _fetchRemotePreview(panel, filePath, isStorage) {
            // sandbox 상대경로 → usekitBase 절대경로 변환
            const _nav2 = window._usekitNav;
            let absFilePath = filePath;
            if (!isStorage && _nav2 && !_nav2.useAbs && _nav2.usekitBase
                    && absFilePath && !absFilePath.startsWith(_nav2.usekitBase)) {
                const rel = absFilePath.startsWith('/') ? absFilePath.slice(1) : absFilePath;
                absFilePath = _nav2.usekitBase.replace(/\/+$/, '') + '/' + rel;
            }
            let url;
            if (isStorage) {
                url = `/api/read_abs?path=${encodeURIComponent(absFilePath)}`;
            } else {
                const isAbs = absFilePath.startsWith('/storage') || absFilePath.startsWith('/data');
                url = isAbs
                    ? `/api/read_abs?path=${encodeURIComponent(absFilePath)}`
                    : `/api/read?path=${encodeURIComponent(absFilePath)}`;
            }
            fetch(url)
                .then(r => r.json().catch(() => ({})))
                .then(j => {
                    const ce = panel.querySelector('.modal-preview-content');
                    if (!ce) return;
                    const text = j?.text ?? '';
                    const lines = text ? text.split('\n') : [];
                    ce.textContent = lines.length
                        ? lines.slice(0, 300).join('\n') + (lines.length > 300 ? '\n...' : '')
                        : '(no data)';
                })
                .catch(e => {
                    const ce = panel.querySelector('.modal-preview-content');
                    if (ce) ce.textContent = `(fetch error: ${e?.message || e})`;
                });
        }

        async function _fetchLocalPreview(panel, item) {
            try {
                let text = '';
                if (currentTab === 'slot') {
                    const slots = api.getSlots();
                    const s = slots[item.slotIdx];
                    if (s?.state?.text)     text = s.state.text;
                    else if (s?.data?.text) text = s.data.text;
                    else {
                        const stored = SlotStorage.readSlot(item.baseName || item.name)
                                    || await SlotStorage.readSlotAsync(item.baseName || item.name);
                        if (stored?.text) { text = stored.text; }
                        else {
                            // LOCAL fallback
                            const local = SlotStorage.readLocal(item.baseName || item.name)
                                       || await SlotStorage.readLocalAsync(item.baseName || item.name);
                            text = local?.text || '';
                        }
                    }
                } else {
                    const stored = SlotStorage.readLocal(item.name)
                                || await SlotStorage.readLocalAsync(item.name);
                    text = stored?.text || '';
                }
                const lines = text ? text.split('\n') : [];
                const display = lines.length
                    ? lines.slice(0, 300).join('\n') + (lines.length > 300 ? '\n...' : '')
                    : '(no data)';
                const ce = panel.querySelector('.modal-preview-content');
                if (ce) ce.textContent = display;
            } catch(e) {
                console.error('[Preview] error:', e);
                const ce = panel.querySelector('.modal-preview-content');
                if (ce) ce.textContent = `(error: ${e?.message || e})`;
            }
        }

        function _openPreview(item) {
            const panel = _ensurePreview();
            if (!panel) return;
            if (_previewItem === item) { _closePreview(); return; }
            _previewItem = item;

            const nameEl    = panel.querySelector('.modal-preview-name');
            const metaEl    = panel.querySelector('.modal-preview-meta');
            const contentEl = panel.querySelector('.modal-preview-content');
            const btnOpen   = panel.querySelector('.modal-preview-btn.open');
            const btnDel    = panel.querySelector('.modal-preview-btn.del');

            nameEl.textContent = item.name;

            const info = item.info || SlotStorage.getLocalOnlyMeta(item.name);
            const parts = [];
            if (info?.timestamp) parts.push(SlotStorage.formatTime(info.timestamp));
            if (info?.lines)     parts.push(`${info.lines}ln`);
            if (info?.chars)     parts.push(`${info.chars}ch`);
            metaEl.textContent = parts.join(' · ');

            btnDel.style.display = (currentTab === 'local') ? '' : 'none';

            contentEl.textContent = 'loading...';
            if ((currentTab === 'usekit' || currentTab === 'storage') && item.path) {
                _fetchRemotePreview(panel, item.path, currentTab === 'storage');
            } else {
                setTimeout(() => _fetchLocalPreview(panel, item), 50);
            }
            panel.classList.add('open');

            btnOpen.onclick = () => { _closePreview(); _activateItem(item); };
            btnDel.onclick  = () => { _closePreview(); _deleteItem(item); };
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-e] LOAD ACTIONS (activate / delete)
        // ═══════════════════════════════════════════════════════════

        async function _loadLocalWithDiff(name) {
            const localStored = SlotStorage.readLocal(name)
                             || await SlotStorage.readLocalAsync(name);
            const localText = localStored?.text || '';
            const slots = api.getSlots?.() || [];
            const activeIdx = api.getActiveIdx?.() ?? -1;
            const matchSlot = slots.find(s => s.storage === 'local' && s.fileName === name);
            if (!matchSlot) {
                api.activateLocalByName(name); closeModal(); return;
            }
            const matchIdx = slots.indexOf(matchSlot);
            let slotText;
            if (matchIdx === activeIdx) {
                slotText = window.Editor?.getText?.() ?? '';
            } else {
                const stored = SlotStorage.readSlot(name)
                            || await SlotStorage.readSlotAsync(name);
                slotText = stored?.text ?? '';
            }
            if (!slotText || slotText === localText) {
                api.activateLocalByName(name); closeModal(); return;
            }
            _openDiff(name, slotText, localText,
                () => { api.activateLocalByName(name); closeModal(); },
                () => { api.activateByIdx(matchIdx); closeModal(); }
            );
        }

        async function _activateItem(item) {
            if (currentTab === 'slot') {
                if (item.slotIdx !== api.getActiveIdx()) {
                    const stored = await SlotStorage.readSlotAsync(item.baseName);
                    api.activateByIdx(item.slotIdx, stored?.text ?? '', { keepDirty: true });
                }
                closeModal();
            } else if (currentTab === 'local') {
                await _loadLocalWithDiff(item.name);
            } else if (currentTab === 'usekit' || currentTab === 'storage') {
                _openUsekitFile(item);
            }
        }

        function _deleteItem(item) {
            if (currentTab === 'slot') {
                _confirm(`Close slot '${item.name}'?`, () => {
                    _removeFavAll(item.baseName || item.name);
                    api.closeSlotAt(item.slotIdx);
                    render(searchEl?.value || '');
                }, { okLabel: 'Close' });
            } else if (currentTab === 'local') {
                _confirm(`Delete '${item.name}'?`, () => {
                    _removeFavAll(item.baseName || item.name);
                    api.deleteLocalSlot(item.name);
                    render(searchEl?.value || '');
                }, { okLabel: 'Delete' });
            }
        }

        function _openUsekitFile(item) {
            if (!window.SlotUsekit?.openUsekitFile) {
                console.error('[popup] SlotUsekit not loaded');
                SlotStorage.toast('SlotUsekit not loaded'); return;
            }
            // sandbox 상대경로 → usekitBase 절대경로 변환
            const _nav = window._usekitNav;
            let resolvedPath = item.path || '';
            if (_nav && !_nav.useAbs && _nav.usekitBase && resolvedPath
                    && !resolvedPath.startsWith(_nav.usekitBase)) {
                const rel = resolvedPath.startsWith('/') ? resolvedPath.slice(1) : resolvedPath;
                resolvedPath = _nav.usekitBase.replace(/\/+$/, '') + '/' + rel;
            }
            SlotUsekit.openUsekitFile(resolvedPath || item.path, item.name, {
                findSlot:     (pred) => (api.getSlots?.() ?? []).findIndex(pred),
                getSlots:     () => api.getSlots?.() ?? [],
                getActiveIdx: () => api.getActiveIdx?.() ?? -1,
                activateSlot: (idx, text) => api.activateByIdx?.(idx, text),
                openDiff:     (name, slotText, serverText, onLoadServer, onLoadSlot, labels) =>
                    _openDiff(name, slotText, serverText, onLoadServer, onLoadSlot, labels),
                addSlot:      (obj) => api.addSlot(obj),
                closeModal,
            });
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-f] FILTER + SORT
        // ═══════════════════════════════════════════════════════════

        function _applyFilterSort(items, filter) {
            let result = filter ? items.filter(it => it.name.toLowerCase().includes(filter)) : items;
            if (_filterDirty) result = result.filter(it => it.isDirty);
            if (_filterFav && (currentTab === 'local' || currentTab === 'slot')) {
                const favSet = _getFavSet(currentTab);
                result = result.filter(it => favSet.has(it.baseName || it.name));
            }
            result = [...result];
            if (_sortMode === 'latest') result.sort((a, b) => (b.info?.timestamp || 0) - (a.info?.timestamp || 0));
            if (_sortMode === 'oldest') result.sort((a, b) => (a.info?.timestamp || 0) - (b.info?.timestamp || 0));
            if (_sortMode === 'az')     result.sort((a, b) => a.name.localeCompare(b.name));
            if (_sortMode === 'za')     result.sort((a, b) => b.name.localeCompare(a.name));
            return result;
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-g] BUILD ITEMS (tab-specific)
        // ═══════════════════════════════════════════════════════════

        async function _buildSlotItems(filter) {
            if (pathEl) pathEl.textContent = 'Active slots (metadata)';
            const slots     = api.getSlots();
            const activeIdx = api.getActiveIdx();
            const infos = await Promise.all(slots.map(async s => {
                const slotData = await SlotStorage.readSlotAsync(s.fileName).catch(() => null);
                if (slotData) return slotData;
                // LOCAL fallback: 슬롯 파일 없으면 로컬 저장본에서 읽기
                const local = SlotStorage.readLocal(s.fileName)
                           || await SlotStorage.readLocalAsync(s.fileName).catch(() => null);
                return local || null;
            }));
            const items = slots.map((s, idx) => {
                const extMatch = s.usekitPath?.match(/\.([a-zA-Z0-9]{1,6})$/);
                const ext = (s.storage === 'usekit' && extMatch) ? extMatch[1] : '';
                const slotData = infos[idx];
                return {
                    name:     s.fileName + (ext ? '.' + ext : ''),
                    baseName: s.fileName,
                    isActive: idx === activeIdx,
                    isDirty:  s.isDirty,
                    storage:  s.storage,
                    slotIdx:  idx,
                    info: slotData ? {
                        timestamp: slotData.timestamp || 0,
                        lines:     slotData.text ? slotData.text.split('\n').length : 0,
                        chars:     slotData.text ? slotData.text.length : 0,
                    } : null,
                };
            });
            return _applyFilterSort(items, filter);
        }

        async function _buildLocalItems(filter) {
            if (pathEl) pathEl.textContent = `${SlotStorage.getMode?.() || 'local'}://${SlotStorage.PREFIX}*`;
            const slots     = api.getSlots();
            const activeIdx = api.getActiveIdx();
            const names = SlotStorage.listLocalSlotNames();
            const infos = await Promise.all(names.map(n => SlotStorage.getLocalOnlyMetaAsync(n)));
            const items = names.map((name, i) => ({
                name,
                isActive: name === slots[activeIdx]?.fileName,
                isDirty:  false,
                storage:  'local',
                slotIdx:  -1,
                info:     infos[i],
            }));
            return _applyFilterSort(items, filter);
        }

        async function _buildUsekitItems(q) {
            if (!window.IOSlotUsekitTab?.buildItems) {
                if (pathEl) pathEl.textContent = '(USEKIT not available)';
                return [];
            }
            const result = await window.IOSlotUsekitTab.buildItems({ filterText: q || '' });
            if (pathEl) pathEl.textContent = result.pathText || '/_tmp/';
            return result.items || [];
        }

        async function _buildStorageItems(q) {
            if (!window.IOSlotUsekitTab?.buildItems) {
                if (pathEl) pathEl.textContent = '(STORAGE not available)';
                return [];
            }
            const result = await window.IOSlotUsekitTab.buildItems({
                filterText: q || '',
                nav: window._storageNav,
            });
            if (pathEl) pathEl.textContent = result.pathText || '/';
            return result.items || [];
        }

        async function buildItems(q) {
            const filter = (q || '').trim().toLowerCase();
            if (currentTab === 'slot')    return _buildSlotItems(filter);
            if (currentTab === 'local')   return _buildLocalItems(filter);
            if (currentTab === 'usekit')  return _buildUsekitItems(q);
            if (currentTab === 'storage') return _buildStorageItems(q);
            return [];
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-h] RENDER
        // ═══════════════════════════════════════════════════════════

        async function render(q) {
            listEl.innerHTML = '<div style="padding:10px;opacity:0.5;font-size:0.8rem;">loading...</div>';

            // UI 토글: 탭별 버튼/필터 가시성
            const canCheck = currentTab === 'local';
            if (btnCheck) btnCheck.style.display = canCheck ? '' : 'none';
            const favLabel   = document.getElementById('loadFilterFavLabel');
            const dirtyLabel = document.getElementById('loadFilterDirtyLabel');
            if (favLabel)   favLabel.style.display   = (currentTab === 'local' || currentTab === 'slot') ? '' : 'none';
            if (dirtyLabel) dirtyLabel.style.display = currentTab === 'local' ? 'none' : '';
            const slotSortBtn = document.querySelector('.load-sort-btn[data-sort="slot"]');
            if (slotSortBtn) slotSortBtn.style.display = currentTab === 'slot' ? '' : 'none';

            const items = await buildItems(q);

            listEl.innerHTML = '';
            if (countEl) countEl.textContent = `${items.length} files`;

            if (!items.length) {
                const empty = document.createElement('div');
                empty.className = 'modal-item';
                empty.innerHTML = '<div class="item-body"><div class="item-name">(empty)</div></div>';
                listEl.appendChild(empty);
                return;
            }

            items.forEach(item => _renderItem(item));
        }

        function _renderItem(item) {
            if (currentTab === 'usekit' || currentTab === 'storage') {
                _renderFsItem(item);
            } else {
                _renderLocalSlotItem(item);
            }
        }

        // ── SLOT / LOCAL 항목 렌더 ──────────────────────────────
        function _renderLocalSlotItem(item) {
            const div = document.createElement('div');
            div.className = 'modal-item' + (item.isActive ? ' active' : '');
            div.dataset.name = item.name;

            const metaParts = [];
            if (currentTab === 'slot') metaParts.push(`<span class="item-storage">${item.storage}</span>`);
            if (item.info?.timestamp)  metaParts.push(SlotStorage.formatTime(item.info.timestamp));
            if (item.info?.lines)      metaParts.push(`${item.info.lines}ln`);
            if (item.info?.chars)      metaParts.push(`${item.info.chars}ch`);

            const canDel      = currentTab === 'local' || currentTab === 'slot';
            const canFav      = currentTab === 'local' || currentTab === 'slot';
            const dirtyMark   = item.isDirty ? '<span class="item-dirty">*</span>' : '';
            const checkIcon   = item.isActive
                ? `<span class="item-check active-check">✓</span>`
                : `<span class="item-check"></span>`;
            const favIcon     = canFav ? (_isFav(item.baseName || item.name, currentTab) ? '★' : '☆') : '';

            div.innerHTML = `
                <div class="item-checkbox">${item.isActive ? '✓' : ''}</div>
                <button class="item-left" type="button" aria-label="Load ${item.name}">${checkIcon}</button>
                <div class="item-body">
                    <div class="item-name name-preview">${dirtyMark}${item.name}</div>
                    <div class="item-meta">${metaParts.join(' · ')}
                        ${canFav ? `<button class="modal-fav" type="button" title="Favorite">${favIcon}</button>` : ''}
                        ${canDel ? '<button class="modal-del" type="button">DEL</button>' : ''}
                    </div>
                </div>${currentTab === 'slot' && _sortMode === 'slot' ? '<div class="item-drag-handle" aria-label="Drag to reorder">≡</div>' : ''}`;

            // 체크모드 클릭 (LOCAL만)
            div.addEventListener('click', e => {
                if (!_checkMode || currentTab !== 'local') return;
                e.stopPropagation();
                if (_selected.has(item.name)) {
                    _selected.delete(item.name);
                    div.classList.remove('check-selected');
                    div.querySelector('.item-checkbox').textContent = '';
                } else {
                    _selected.add(item.name);
                    div.classList.add('check-selected');
                    div.querySelector('.item-checkbox').textContent = '✓';
                }
            });

            // Check 버튼(좌측 아이콘) → 바로 로드
            div.querySelector('.item-left').addEventListener('click', e => {
                e.stopPropagation();
                _activateItem(item);
            });
            // Name 클릭 → 프리뷰
            div.querySelector('.item-name').addEventListener('click', e => {
                e.stopPropagation(); _openPreview(item);
            });
            // Meta 클릭 → 프리뷰 (DEL / FAV 제외)
            const metaEl = div.querySelector('.item-meta');
            if (metaEl) {
                metaEl.addEventListener('click', e => {
                    if (e.target.classList.contains('modal-del')) return;
                    if (e.target.classList.contains('modal-fav')) return;
                    e.stopPropagation();
                    _openPreview(item);
                });
            }
            // FAV
            const favBtn = div.querySelector('.modal-fav');
            if (favBtn) {
                favBtn.addEventListener('click', e => {
                    e.preventDefault(); e.stopPropagation();
                    _toggleFav(item.baseName || item.name, currentTab);
                    favBtn.textContent = _isFav(item.baseName || item.name, currentTab) ? '★' : '☆';
                    if (_filterFav) render(searchEl?.value || '');
                });
            }
            // DEL
            const delBtn = div.querySelector('.modal-del');
            if (delBtn) {
                delBtn.addEventListener('click', e => {
                    e.preventDefault(); e.stopPropagation();
                    _deleteItem(item);
                });
            }

            // ── SLOT 탭 드래그 재배치 (long-press → drag mode) ──────
            if (currentTab === 'slot' && _sortMode === 'slot' && item.slotIdx >= 0) {
                const LONG_MS = 350, MOVE_PX = 8;
                let _lpTimer = null, _startX = 0, _startY = 0;
                const _getXY = e => {
                    const t = e.touches?.[0] || e.changedTouches?.[0] || e;
                    return { x: t.clientX, y: t.clientY };
                };

                div.addEventListener('touchstart', e => {
                    if (_dragMode && _dragDiv === div) return; // 이미 선택됨
                    if (_dragMode) return; // 다른 아이템 드래그 중
                    if (e.target.closest('.modal-del') || e.target.closest('.modal-fav')) return;
                    const p = _getXY(e);
                    _startX = p.x; _startY = p.y;
                    _lpTimer = setTimeout(() => {
                        _enterDragMode(div, item.slotIdx);
                    }, LONG_MS);
                }, { passive: true });

                div.addEventListener('touchmove', e => {
                    const p = _getXY(e);
                    const dx = Math.abs(p.x - _startX), dy = Math.abs(p.y - _startY);
                    // 롱프레스 전 움직이면 취소
                    if (!_dragMode && _lpTimer && (dx > MOVE_PX || dy > MOVE_PX)) {
                        clearTimeout(_lpTimer); _lpTimer = null; return;
                    }
                    // 드래그 모드에서 드래그 중 (현재 선택 아이템만)
                    if (_dragMode && _dragDiv === div) {
                        e.preventDefault();
                        const hit = document.elementFromPoint(p.x, p.y);
                        const target = hit?.closest?.('.modal-item');
                        if (target && target !== div && target.parentNode === listEl) {
                            const allItems = [...listEl.querySelectorAll('.modal-item')];
                            const fromIdx = allItems.indexOf(div);
                            const toIdx   = allItems.indexOf(target);
                            if (fromIdx >= 0 && toIdx >= 0 && fromIdx !== toIdx) {
                                if (fromIdx < toIdx) target.after(div);
                                else target.before(div);
                            }
                        }
                    }
                }, { passive: false });

                div.addEventListener('touchend', () => {
                    clearTimeout(_lpTimer); _lpTimer = null;
                    // 드래그 모드에서 손가락 떼면 → 위치 확정 (모드는 유지)
                    // _exitDragMode는 Cancel/✕ 에서만 호출
                }, { passive: true });
                div.addEventListener('touchcancel', () => {
                    clearTimeout(_lpTimer); _lpTimer = null;
                }, { passive: true });

                // 드래그 모드 중 클릭 차단
                div.addEventListener('click', e => {
                    if (_dragMode) { e.stopPropagation(); e.preventDefault(); }
                }, true);
            }

            listEl.appendChild(div);
        }

        // ── USEKIT / STORAGE 파일시스템 항목 렌더 ────────────
        function _renderFsItem(item) {
            const div = document.createElement('div');

            // nav_parent: 상위 폴더
            if (item.type === 'nav_parent') {
                div.className = 'usekit-nav-row' + (item.disabled ? ' disabled' : '');
                div.innerHTML = `<span class="usekit-nav-icon">↑</span><span class="usekit-nav-label">//</span>`;
                if (!item.disabled) {
                    div.addEventListener('click', () => {
                        const nav = currentTab === 'storage' ? window._storageNav : window._usekitNav;
                        if (nav) { nav.currentPath = item.name; nav._skipFetchOnce = false; }
                        render(searchEl?.value || '');
                    });
                }
                listEl.appendChild(div); return;
            }

            // separator
            if (item.type === 'separator') {
                div.className = 'usekit-separator';
                listEl.appendChild(div); return;
            }

            // nav_current: 현재 폴더 (각 세그먼트 클릭 → 해당 디렉토리 이동)
            if (item.type === 'nav_current') {
                div.className = 'usekit-nav-row current';
                const rawName = String(item.name || '/').replace(/\/+$/, '') || '/';
                const allParts = rawName.split('/').filter(Boolean);
                const nav = currentTab === 'storage' ? window._storageNav : window._usekitNav;
                const rootPath = (nav?.rootPath || '/').replace(/\/+$/, '') || '';
                const rootParts = rootPath.split('/').filter(Boolean);

                // rootPath 이후 세그먼트만 표시
                const displayParts = allParts.slice(rootParts.length);

                const labelSpan = document.createElement('span');
                labelSpan.className = 'usekit-nav-label';
                labelSpan.style.cssText = 'display:flex;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none;';

                if (displayParts.length === 0) {
                    labelSpan.innerHTML = '<strong>/</strong>';
                } else {
                    const last = displayParts[displayParts.length - 1];
                    for (let i = 0; i < displayParts.length - 1; i++) {
                        const targetPath = '/' + allParts.slice(0, rootParts.length + i + 1).join('/') + '/';
                        const seg = document.createElement('span');
                        seg.textContent = '/' + displayParts[i];
                        seg.style.cssText = 'opacity:0.5;cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px;flex-shrink:0;';
                        seg.addEventListener('click', ((p) => (e) => {
                            e.stopPropagation();
                            if (nav) { nav.currentPath = p; nav._skipFetchOnce = false; }
                            render(searchEl?.value || '');
                        })(targetPath));
                        labelSpan.appendChild(seg);
                    }
                    const tailSpan = document.createElement('strong');
                    tailSpan.textContent = '/' + last;
                    tailSpan.style.cssText = 'flex-shrink:0;';
                    labelSpan.appendChild(tailSpan);
                }

                div.innerHTML = `<span class="usekit-folder-icon">📁</span>`;
                div.appendChild(labelSpan);
                // 스크롤을 끝(현재 폴더)으로
                requestAnimationFrame(() => { labelSpan.scrollLeft = labelSpan.scrollWidth; });
                listEl.appendChild(div); return;
            }

            // info: 오류/빈상태
            if (item.type === 'info') {
                div.className = 'usekit-info-row';
                div.textContent = item.name;
                listEl.appendChild(div); return;
            }

            // dir: 폴더
            if (item.type === 'dir') {
                div.className = 'modal-item usekit-dir';
                div.innerHTML = `
                    <div class="item-left" style="font-size:1.1rem;">📁</div>
                    <div class="item-body">
                        <div class="item-name">${item.name}</div>
                    </div>`;
                div.addEventListener('click', () => {
                    const nav = currentTab === 'storage' ? window._storageNav : window._usekitNav;
                    if (nav) { nav.currentPath = item.path + '/'; nav._skipFetchOnce = false; }
                    render(searchEl?.value || '');
                });
                listEl.appendChild(div); return;
            }

            // file: 일반 파일
            if (item.type === 'file') {
                div.className = 'modal-item';
                const meta = item.meta || {};
                const metaParts = [];
                if (meta.timestamp) metaParts.push(SlotStorage.formatTime(meta.timestamp));
                if (meta.size)      metaParts.push(_fmtSize(meta.size));

                div.innerHTML = `
                    <div class="item-left" style="font-size:1rem;">📄</div>
                    <div class="item-body">
                        <div class="item-name">${item.name}</div>
                        <div class="item-meta">${metaParts.join(' · ')}
                            ${item.canDel ? '<button class="modal-del" type="button">DEL</button>' : ''}
                        </div>
                    </div>`;

                // 파일명 클릭 → 프리뷰
                div.querySelector('.item-name').addEventListener('click', e => {
                    e.stopPropagation(); _openPreview(item);
                });
                // 아이콘 클릭 → 바로 열기
                div.querySelector('.item-left').addEventListener('click', e => {
                    e.stopPropagation(); _openUsekitFile(item);
                });
                // DEL
                const delBtn = div.querySelector('.modal-del');
                if (delBtn) {
                    delBtn.addEventListener('click', e => {
                        e.preventDefault(); e.stopPropagation();
                        _confirm(`Delete '${item.name}'?`, async () => {
                            const ok = await api.deleteUsekitFile(item);
                            if (ok) render(searchEl?.value || '');
                            else SlotStorage.toast('Delete failed');
                        }, { okLabel: 'Delete' });
                    });
                }
                listEl.appendChild(div); return;
            }
        }

        // ═══════════════════════════════════════════════════════════
        //  [4-i] SHOW
        // ═══════════════════════════════════════════════════════════

        if (searchEl) { searchEl.value = ''; searchEl.oninput = () => render(searchEl.value); }

        switchTab('slot');
        // 드래그 모드 잔여 상태 UI 복원
        if (titleEl) titleEl.textContent = 'LOAD';
        if (countEl) countEl.style.display = '';
        if (btnCncl) btnCncl.textContent = 'Close';
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
    }

    return { open, confirm: _confirm };
})();

window.SlotPopup   = SlotPopup;
window.showConfirm = SlotPopup.confirm;
