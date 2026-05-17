/* Path: usekit/tools/editor/js2/nav/nav_clipboard.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * Clipboard history — R button popup, localStorage (max 20 items)
 * ─────────────────────────────────────────────────────────── */

const NavClipboard = (function () {
    'use strict';

    const STORAGE_KEY = 'usekit_clipboard_history';
    const MAX_ITEMS   = 20;

    // ── Storage ───────────────────────────────────────────────
    function _load() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
    }
    function _save(items) {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(items)); } catch {}
    }

    // ── API ───────────────────────────────────────────────────
    function push(text) {
        if (!text || typeof text !== 'string') return;
        const items = _load();
        if (items.length > 0 && items[0] === text) return;
        items.unshift(text);
        if (items.length > MAX_ITEMS) items.length = MAX_ITEMS;
        _save(items);
    }
    function getAll()    { return _load(); }
    function remove(idx) { const items = _load(); items.splice(idx, 1); _save(items); }
    function clear()     { _save([]); }

    // ── Render ────────────────────────────────────────────────
    let _expandedIdx = null;
    let _selectedIdx  = null;  // 현재 paste 대상 인덱스
    function _el(id) { return document.getElementById(id); }

    function _render() {
        const listEl = _el('clipModalList');
        if (!listEl) return;
        const items = _load();

        listEl.innerHTML = '';

        if (items.length === 0) {
            listEl.innerHTML = '<div class="modal-list-empty">No clipboard history</div>';
            return;
        }

        items.forEach((text, idx) => {
            const lines     = text.split('\n');
            const lineCount = lines.length;
            const charCount = text.length;
            const firstLine = lines[0] || '';
            const isOpen    = _expandedIdx === idx;

            // ── wrapper ──
            const wrap = document.createElement('div');
            wrap.className = 'clip-wrap' + (isOpen ? ' clip-open' : '');

            // ── header row ──
            const row = document.createElement('div');
            row.className = 'clip-row';

            // [✓] paste button
            const chk = document.createElement('button');
            chk.className = 'clip-btn-paste';
            chk.title = 'Paste';
            chk.innerHTML = '✓';
            if (_selectedIdx === idx) chk.classList.add('clip-btn-selected');
            chk.addEventListener('click', (e) => { e.stopPropagation(); _pasteItem(text); });

            // [N] number
            const num = document.createElement('span');
            num.className = 'clip-num';
            num.textContent = idx + 1;

            // title (first line preview)
            const title = document.createElement('span');
            title.className = 'clip-title';
            title.textContent = firstLine.length > 80 ? firstLine.slice(0, 80) + '…' : firstLine;

            // meta
            const meta = document.createElement('span');
            meta.className = 'clip-meta';
            meta.textContent = lineCount > 1 ? `${lineCount}L·${charCount}C` : `${charCount}C`;

            // [▼/▲] expand toggle (only if multi-line or long)
            const toggle = document.createElement('button');
            toggle.className = 'clip-btn-toggle';
            toggle.title = isOpen ? 'Collapse' : 'Expand';
            toggle.innerHTML = isOpen ? '▲' : '▼';
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                if (isOpen) {
                    _expandedIdx = null;
                } else {
                    _expandedIdx = idx;
                    // 펼친 항목을 paste 대상으로 선택
                    _selectedIdx = idx;
                    NavBlock?.setClipData?.(text);
                }
                _render();
            });

            // [🗑] delete
            const del = document.createElement('button');
            del.className = 'clip-btn-del';
            del.title = 'Delete';
            del.innerHTML = '✕';
            del.addEventListener('click', (e) => {
                e.stopPropagation();
                remove(idx);
                if (_expandedIdx === idx) _expandedIdx = null;
                else if (_expandedIdx > idx) _expandedIdx--;
                _render();
                UI?.showToast?.('Deleted', 500);
            });

            row.appendChild(chk);
            row.appendChild(num);
            row.appendChild(title);
            row.appendChild(meta);
            row.appendChild(toggle);
            row.appendChild(del);

            // ── detail panel ──
            const detail = document.createElement('div');
            detail.className = 'clip-detail';
            detail.style.display = isOpen ? '' : 'none';

            const content = document.createElement('pre');
            content.className = 'clip-content';
            content.textContent = text;
            content.title = 'Tap to paste';
            content.addEventListener('click', () => _pasteItem(text));

            const collapseBtn = document.createElement('button');
            collapseBtn.className = 'clip-btn-collapse';
            collapseBtn.textContent = 'Collapse';
            collapseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                _expandedIdx = null;
                _render();
            });

            detail.appendChild(content);
            detail.appendChild(collapseBtn);

            wrap.appendChild(row);
            wrap.appendChild(detail);
            listEl.appendChild(wrap);
        });
    }

    function _pasteItem(text) {
        // sel을 closeModal() 전에 캡처 — focus 이벤트로 selection 리셋되기 전
        const view = Editor.get?.();
        if (!view) return;
        const sel = view.state.selection.main;
        const from = sel.from, to = sel.to;
        closeModal();  // 내부 Editor.focus() 호출 있음 — 이후 dispatch로 덮어씀
        view.dispatch({
            changes:   { from, to, insert: text },
            selection: { anchor: from + text.length },
            userEvent: 'input',
        });
        Editor.focus?.();
        if (window.UI) UI.updateStats();
    }

    // ── Modal ─────────────────────────────────────────────────
    let _isOpen = false;

    function openModal() {
        const modal = _el('clipModal');
        if (!modal) return;
        _isOpen = true;
        _expandedIdx = null;
        modal.style.display = '';
        modal.setAttribute('aria-hidden', 'false');
        // 시스템 키보드 강제 다운 + 잠금
        window._clipModalOpen = true;
        UIViewport?.blockKeyboard?.();
        const kpWasOpen = window.UIKeypad?.isOpen?.() ?? false;
        modal._kpWasOpen = kpWasOpen;
        if (kpWasOpen) window.UIKeypad.hide();
        _switchTab(_activeTab);

        if (!modal.dataset.clipBound) {
            modal.dataset.clipBound = '1';
            modal.addEventListener('click', e => { if (e.target === modal) _closeModalWithFocus(); });
            _el('btnClipModalClose')?.addEventListener('click', _closeModalWithFocus);
            _el('btnClipModalClear')?.addEventListener('click', () => {
                clear();
                _expandedIdx = null;
                _render();
                UI?.showToast?.('Cleared', 600);
                UI?.notifyClipCleared?.();
            });
            _el('btnClipTab')?.addEventListener('click', () => _switchTab('clip'));
            _el('btnBookmarkTab')?.addEventListener('click', () => _switchTab('bm'));
            _el('btnFindHistTab')?.addEventListener('click', () => _switchTab('find'));
            document.addEventListener('keydown', _onKey);
        }
    }

    function _onKey(e) { if (!_isOpen) return; if (e.key === 'Escape') _closeModalWithFocus(); }

    function closeModal() {
        const modal = _el('clipModal');
        if (!modal) return;
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        _isOpen = false;
        // 키보드 잠금 해제
        window._clipModalOpen = false;
        // 키패드 복원
        if (modal._kpWasOpen) window.UIKeypad?.show?.();
        // focus는 호출자(_pasteItem 또는 직접 닫기)가 담당
    }

    function _closeModalWithFocus() {
        closeModal();
        Editor.focus?.();
    }

    function toggleModal() { _isOpen ? closeModal() : openModal(); }
    function isOpen()      { return _isOpen; }

    // ── Bookmark ──────────────────────────────────────────────
    const BM_KEY     = 'usekit_bookmarks';
    const BM_MAX     = 100;
    let _activeTab   = 'clip'; // 'clip' | 'bm'
    let _bmFilter    = 'current'; // 'current' | 'all'

    function _bmLoad() {
        try { return JSON.parse(localStorage.getItem(BM_KEY) || '[]'); } catch { return []; }
    }
    function _bmSave(items) {
        try { localStorage.setItem(BM_KEY, JSON.stringify(items)); } catch {}
    }
    function _bmCurrentFile() {
        return window.SlotManager?.getCurrentSlot?.() || '_default';
    }
    function _updateMarkBtn() {
        const btn = document.getElementById('btnFooterMark');
        if (!btn || btn.style.display === 'none') return;
        if (!window._bookmarkMode) return;
        const view = Editor.get?.();
        if (!view) return;
        const ln = view.state.doc.lineAt(view.state.selection.main.head).number;
        const file = _bmCurrentFile();
        const items = _bmLoad();
        const isMarked = items.some(b => b.fileName === file && b.ln === ln);
        if (isMarked) {
            btn.style.background  = 'var(--bg-surface)';
            btn.style.borderColor = 'var(--ac-green-bd, rgba(40,200,80,0.5))';
            btn.style.color       = 'var(--ac-green, #4caf50)';
        } else {
            btn.style.background  = 'var(--bg-surface)';
            btn.style.borderColor = 'var(--ac-red-bd)';
            btn.style.color       = 'var(--ac-red)';
        }
    }

    function addBookmark() {
        const view = Editor.get?.();
        if (!view) return;
        const pos  = view.state.selection.main.head;
        const line = view.state.doc.lineAt(pos);
        const ln   = line.number;
        const file = _bmCurrentFile();
        const items = _bmLoad();
        const alreadyMarked = items.some(b => b.fileName === file && b.ln === ln);
        if (alreadyMarked) {
            const filtered = items.filter(b => !(b.fileName === file && b.ln === ln));
            _bmSave(filtered);
            UI?.showToast?.(`Bookmark removed Ln ${ln}`, 900);
        } else {
            const preview = line.text.trim().substring(0, 40) || '(empty)';
            const filtered = items.filter(b => !(b.fileName === file && b.ln === ln));
            filtered.unshift({ fileName: file, ln, preview });
            if (filtered.length > BM_MAX) filtered.length = BM_MAX;
            _bmSave(filtered);
            UI?.showToast?.(`Bookmarked Ln ${ln}`, 900);
        }
        _updateMarkBtn();
    }
    function _bmRender() {
        const listEl = _el('bookmarkModalList');
        if (!listEl) return;
        const allItems = _bmLoad();
        const file = _bmCurrentFile();
        const items = _bmFilter === 'current'
            ? allItems.filter(b => b.fileName === file)
            : allItems;
        listEl.innerHTML = '';
        if (items.length === 0) {
            listEl.innerHTML = '<div class="modal-list-empty">No bookmarks</div>';
            return;
        }
        items.forEach((bm, i) => {
            const row = document.createElement('div');
            row.className = 'modal-list-item';
            const isCurrent = bm.fileName === file;
            row.innerHTML = `
                <span style="flex:1;overflow:hidden;min-width:0;">
                  ${!isCurrent ? `<span style="color:var(--tx-dim);font-size:0.75em;margin-right:6px;">${bm.fileName || ''}</span>` : ''}
                  <b style="color:${isCurrent ? 'var(--ac-blue)' : 'var(--tx-muted)'};margin-right:6px;">Ln ${bm.ln}</b>
                  <span style="color:var(--tx-muted);font-size:0.82em;font-family:monospace;">${(bm.preview||'').replace(/</g,'&lt;')}</span>
                </span>
                <button class="modal-item-del" style="background:none;border:none;color:var(--tx-muted);font-size:1.1em;padding:0 4px;">×</button>`;
            row.querySelector('span').addEventListener('click', () => {
                closeModal();
                if (!isCurrent) {
                    // 다른 파일 → 슬롯 전환 후 이동
                    window.SlotManager?.switchToFileName?.(bm.fileName, () => {
                        const view = Editor.get?.();
                        if (!view) return;
                        const ln = Math.min(bm.ln, view.state.doc.lines);
                        const line = view.state.doc.line(ln);
                        view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
                        Editor.focus?.();
                    });
                } else {
                    const view = Editor.get?.();
                    if (!view) return;
                    const ln = Math.min(bm.ln, view.state.doc.lines);
                    const line = view.state.doc.line(ln);
                    view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
                    Editor.focus?.();
                }
            });
            // 삭제는 allItems 기준 인덱스 필요
            row.querySelector('.modal-item-del').addEventListener('click', e => {
                e.stopPropagation();
                const arr = _bmLoad();
                const idx = arr.findIndex(b => b.fileName === bm.fileName && b.ln === bm.ln);
                if (idx !== -1) { arr.splice(idx, 1); _bmSave(arr); }
                _bmRender();
            });
            listEl.appendChild(row);
        });
    }

    function _findHistRender() {
        const listEl = _el('findHistModalList');
        if (!listEl) return;
        const history = window.NavFind?.getHistory?.() || [];
        listEl.innerHTML = '';
        if (history.length === 0) {
            listEl.innerHTML = '<div class="modal-list-empty">No find history</div>';
            return;
        }
        history.forEach((q) => {
            const row = document.createElement('div');
            row.className = 'modal-list-item';
            row.innerHTML = `
                <span style="flex:1;overflow:hidden;min-width:0;font-family:monospace;font-size:0.88em;color:var(--tx-main);">${q.replace(/</g,'&lt;')}</span>`;
            row.addEventListener('click', () => {
                closeModal();
                window.NavFind?.searchQuery?.(q);
            });
            listEl.appendChild(row);
        });
    }

    function _switchTab(tab) {
        _activeTab = tab;
        const clipList     = _el('clipModalList');
        const bmList       = _el('bookmarkModalList');
        const bmFilter     = _el('bookmarkFilter');
        const findHistList = _el('findHistModalList');
        const clipBtn      = _el('btnClipTab');
        const bmBtn        = _el('btnBookmarkTab');
        const findBtn      = _el('btnFindHistTab');
        const clearBtn     = _el('btnClipModalClear');

        // 전체 숨김
        if (clipList)     clipList.style.display     = 'none';
        if (bmList)       bmList.style.display       = 'none';
        if (bmFilter)     bmFilter.style.display     = 'none';
        if (findHistList) findHistList.style.display = 'none';
        clipBtn?.classList.remove('active');
        bmBtn?.classList.remove('active');
        findBtn?.classList.remove('active');
        if (clearBtn) clearBtn.style.display = 'none';

        if (tab === 'clip') {
            if (clipList) clipList.style.display = '';
            clipBtn?.classList.add('active');
            if (clearBtn) clearBtn.style.display = '';
            _render();
        } else if (tab === 'bm') {
            if (bmList)   bmList.style.display   = '';
            if (bmFilter) bmFilter.style.display = '';
            bmBtn?.classList.add('active');
            // 필터 버튼 바인딩 (최초 1회)
            const curBtn = _el('btnBmFilterCurrent');
            const allBtn = _el('btnBmFilterAll');
            if (curBtn && !curBtn.dataset.bmBound) {
                curBtn.dataset.bmBound = '1';
                curBtn.addEventListener('click', () => {
                    _bmFilter = 'current';
                    curBtn.classList.add('active');
                    allBtn?.classList.remove('active');
                    _bmRender();
                });
                allBtn?.addEventListener('click', () => {
                    _bmFilter = 'all';
                    allBtn.classList.add('active');
                    curBtn.classList.remove('active');
                    _bmRender();
                });
            }
            _bmRender();
        } else if (tab === 'find') {
            if (findHistList) findHistList.style.display = '';
            findBtn?.classList.add('active');
            _findHistRender();
        }
    }

    function _goBookmark(dir) {
        const view = Editor.get?.();
        if (!view) return;
        const file  = _bmCurrentFile();
        const items = _bmLoad().filter(b => b.fileName === file);
        if (items.length === 0) { UI?.showToast?.('No bookmarks', 800); return; }
        const curLine = view.state.doc.lineAt(view.state.selection.main.head).number;
        const sorted = [...items].sort((a, b) => a.ln - b.ln);
        let target;
        if (dir === 'next') {
            target = sorted.find(b => b.ln > curLine) || sorted[0];
        } else {
            const before = sorted.filter(b => b.ln < curLine);
            target = before.length > 0 ? before[before.length - 1] : sorted[sorted.length - 1];
        }
        const lineCount = view.state.doc.lines;
        const ln = Math.min(target.ln, lineCount);
        const line = view.state.doc.line(ln);
        view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
        Editor.focus?.();
        UI?.showToast?.(`Ln ${ln}`, 600);
    }

    return { push, getAll, remove, clear, openModal, closeModal, toggleModal, isOpen, addBookmark, goBookmark: _goBookmark, updateMarkBtn: _updateMarkBtn, switchTab: _switchTab };
})();

window.NavClipboard    = NavClipboard;
window._addBookmark    = () => NavClipboard.addBookmark();
window._goPrevBookmark = () => NavClipboard.goBookmark('prev');
window._goNextBookmark = () => NavClipboard.goBookmark('next');
window._updateMarkBtn  = () => NavClipboard.updateMarkBtn();
