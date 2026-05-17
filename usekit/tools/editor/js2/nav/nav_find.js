/* Path: usekit/tools/editor/js2/nav/nav_find.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * Find + Replace 통합 모달
 * ─────────────────────────────────────────────────────────── */

const NavFind = (function () {
    'use strict';

    let _active      = false;
    let _replaceMode = false;
    let _historyMode = false;
    let _gotoMode     = false;
    let _gotoCooldown = false;  // goto 직후 재열기 방지
    let _lastQuery    = '';     // 최근 검색어 (롱프레스 재활용)
    let _searchHistory = [];  // 최근 검색어 목록 (최대 20개)
    const _HISTORY_MAX = 20;
    const _HISTORY_KEY = 'findSearchHistory';
    const _GOTO_HISTORY_KEY = 'findGotoHistory';
    const _LAST_QUERY_KEY   = 'findLastQuery';
    const _GOTO_HISTORY_MAX = 10;
    let _repHistory = [];
    const _REP_HISTORY_KEY = 'findRepHistory';
    const _REP_HISTORY_MAX = 20;
    let _gotoHistory = [];

    function _loadHistory() {
        try {
            const raw = localStorage.getItem(_HISTORY_KEY);
            _searchHistory = raw ? JSON.parse(raw) : [];
        } catch(e) { _searchHistory = []; }
    }

    function _saveHistory() {
        try { localStorage.setItem(_HISTORY_KEY, JSON.stringify(_searchHistory)); } catch(e) {}
    }

    function _loadRepHistory() {
        try {
            const raw = localStorage.getItem(_REP_HISTORY_KEY);
            _repHistory = raw ? JSON.parse(raw) : [];
        } catch(e) { _repHistory = []; }
    }
    function _saveRepHistory() {
        try { localStorage.setItem(_REP_HISTORY_KEY, JSON.stringify(_repHistory)); } catch(e) {}
    }
    function _addRepHistory(val) {
        if (val === undefined || val === null) return;
        _repHistory = _repHistory.filter(h => h !== val);
        _repHistory.unshift(val);
        if (_repHistory.length > _REP_HISTORY_MAX) _repHistory.pop();
        _saveRepHistory();
        if (_el('findModalRepHistoryList')?.style.display !== 'none') _renderRepHistory();
    }
    function _renderRepHistory() {
        const list = _el('findModalRepHistoryList');
        if (!list) return;
        list.innerHTML = '';
        if (_repHistory.length === 0) {
            list.innerHTML = '<div class="modal-list-empty">No history</div>';
            return;
        }
        _repHistory.forEach((q, i) => {
            const item = document.createElement('div');
            item.className = 'modal-list-item';
            item.innerHTML = `<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${q.replace(/</g,'&lt;')}</span><button class="modal-item-del" style="background:none;border:none;color:var(--text-muted);font-size:1.1em;padding:0 4px;cursor:pointer;">×</button>`;
            item.querySelector('span').addEventListener('click', () => {
                const inp = _el('findModalReplaceTo');
                if (inp) { inp.value = q; inp.focus(); }
            });
            item.querySelector('.modal-item-del').addEventListener('click', (e) => {
                e.stopPropagation();
                _repHistory.splice(i, 1);
                _saveRepHistory();
                _renderRepHistory();
            });
            list.appendChild(item);
        });
    }

    function _saveLastQuery(q) {
        try { localStorage.setItem(_LAST_QUERY_KEY, q); } catch(e) {}
    }

    function _loadLastQuery() {
        try { _lastQuery = localStorage.getItem(_LAST_QUERY_KEY) || ''; } catch(e) {}
    }

    function _addHistory(query) {
        if (!query) return;
        _searchHistory = _searchHistory.filter(h => h !== query);
        _searchHistory.unshift(query);
        if (_searchHistory.length > _HISTORY_MAX) _searchHistory.pop();
        _saveHistory();
        if (_historyMode) _renderHistory();
        _saveLastQuery(query);
    }

    function _renderHistory() {
        const list = _el('findModalHistoryList');
        if (!list) return;
        list.innerHTML = '';
        if (_searchHistory.length === 0) {
            list.innerHTML = '<div class="modal-list-empty">No history</div>';
            return;
        }
        _searchHistory.forEach((q, i) => {
            const item = document.createElement('div');
            item.className = 'modal-list-item';
            item.innerHTML = `<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${q.replace(/</g,'&lt;')}</span><button class="modal-item-del" data-idx="${i}" style="background:none;border:none;color:var(--text-muted);font-size:1.1em;padding:0 4px;cursor:pointer;">×</button>`;
            item.querySelector('span').addEventListener('click', () => {
                const input = _el('findModalInput');
                if (input) {
                    input.value = q;
                    input.focus();
                }
            });
            item.querySelector('.modal-item-del').addEventListener('click', (e) => {
                e.stopPropagation();
                _searchHistory.splice(i, 1);
                _saveHistory();
                _renderHistory();
            });
            list.appendChild(item);
        });
        // 첫 아이템 실제 높이 기준으로 5개 max-height 설정
        requestAnimationFrame(() => {
            const first = list.querySelector('.modal-list-item');
            if (first) {
                const h = first.getBoundingClientRect().height;
                const gap = 2;
                list.style.maxHeight = (h * 5 + gap * 4) + 'px';
                list.style.overflowY = 'auto';
            }
        });
    }

    function _onHistoryModeChange() {
        const chk = _el('findModalHistoryMode');
        const list = _el('findModalHistoryList');
        _historyMode = chk ? chk.checked : false;
        if (list) list.style.display = _historyMode ? '' : 'none';
        if (_historyMode) _renderHistory();
        requestAnimationFrame(_positionFindModal);
    }

    // ===== Go to Line =====
    function _loadGotoHistory() {
        try {
            const raw = localStorage.getItem(_GOTO_HISTORY_KEY);
            _gotoHistory = raw ? JSON.parse(raw) : [];
        } catch(e) { _gotoHistory = []; }
    }

    function _saveGotoHistory() {
        try { localStorage.setItem(_GOTO_HISTORY_KEY, JSON.stringify(_gotoHistory)); } catch(e) {}
    }

    function _addGotoHistory(lineNum) {
        const s = String(lineNum);
        _gotoHistory = _gotoHistory.filter(h => h !== s);
        _gotoHistory.unshift(s);
        if (_gotoHistory.length > _GOTO_HISTORY_MAX) _gotoHistory.pop();
        _saveGotoHistory();
        _renderGotoHistory();
    }

    function _renderGotoHistory() {
        const list = _el('findModalGotoHistory');
        if (!list) return;
        list.innerHTML = '';
        if (_gotoHistory.length === 0) {
            list.innerHTML = '<div class="modal-list-empty">No history</div>';
            return;
        }
        _gotoHistory.forEach((num, i) => {
            const item = document.createElement('div');
            item.className = 'modal-list-item';
            // 라인 내용 미리보기
            const preview = _getLinePreview(Number(num));
            item.innerHTML = `<span style="flex:1;overflow:hidden;"><b style="color:var(--ac-blue)">${num}</b><span style="color:var(--text-muted);margin-left:8px;font-size:0.85em;font-family:monospace;">${preview.replace(/</g,'&lt;').substring(0,40)}</span></span><button class="modal-item-del" style="background:none;border:none;color:var(--text-muted);font-size:1.1em;padding:0 4px;cursor:pointer;">×</button>`;
            item.querySelector('span').addEventListener('click', () => {
                const inp = _el('findModalGotoInput');
                if (inp) { inp.value = num; _onGotoInputChange(); }
            });
            item.querySelector('.modal-item-del').addEventListener('click', (e) => {
                e.stopPropagation();
                _gotoHistory.splice(i, 1);
                _saveGotoHistory();
                _renderGotoHistory();
            });
            list.appendChild(item);
        });
        // 첫 아이템 실제 높이 기준으로 5개 max-height 설정
        requestAnimationFrame(() => {
            const first = list.querySelector('.modal-list-item');
            if (first) {
                const h = first.getBoundingClientRect().height;
                list.style.maxHeight = (h * 5 + 2 * 4) + 'px';
                list.style.overflowY = 'auto';
            }
        });
        // display는 Go History 체크박스가 제어
    }

    function _getLinePreview(lineNum) {
        try {
            const view = Editor?.get?.();
            if (!view) return '';
            const doc = view.state.doc;
            if (lineNum < 1 || lineNum > doc.lines) return '(out of range)';
            return doc.line(lineNum).text || '';
        } catch(e) { return ''; }
    }

    function _onGotoInputChange() {
        const inp = _el('findModalGotoInput');
        const preview = _el('findModalGotoPreview');
        if (!inp || !preview) return;
        const lineNum = parseInt(inp.value, 10);
        if (!lineNum || lineNum < 1) {
            preview.style.display = 'none';
            return;
        }
        const text = _getLinePreview(lineNum);
        if (text === '') {
            preview.style.display = 'none';
        } else {
            preview.textContent = text === '(out of range)' ? text : `L${lineNum}: ${text}`;
            preview.style.display = '';
        }
    }

    function _doGoto() {
        const inp = _el('findModalGotoInput');
        if (!inp) return;
        const lineNum = parseInt(inp.value, 10);
        if (!lineNum || lineNum < 1) return;
        try {
            const view = Editor?.get?.();
            if (!view) return;
            const doc = view.state.doc;
            const target = Math.min(lineNum, doc.lines);
            const pos = doc.line(target).from;
            view.dispatch({
                selection: { anchor: pos },
                scrollIntoView: true,
                userEvent: 'goto'
            });
            _addGotoHistory(target);
            // 모달 닫기 + 포커스를 viewport 안정화 후 실행
            _gotoCooldown = true;
            _dismissModal();
            _active      = false;
            _replaceMode = false;
            _gotoMode    = false;
            _matches     = [];
            _index       = -1;
            _setAllButtonsActive(false);
            // LK 복원
            if (window.State?.getLK?.()) window.UIViewport?.blockKeyboard?.();
            // 포커스는 레이아웃 안정 후, 쿨다운은 viewport 완전 안정 후 해제
            setTimeout(() => { Editor.focus?.(); }, 200);
            setTimeout(() => { _gotoCooldown = false; }, 600);
        } catch(e) {}
    }

    function _onGotoModeChange() {
        requestAnimationFrame(_clampFindModalHeight);
        const chk         = _el('findModalGotoMode');
        const area        = _el('findModalGotoArea');
        const btnsFind    = _el('findModalBtnsFind');
        const btnsReplace = _el('findModalBtnsReplace');
        const btnsGoto    = _el('findModalBtnsGoto');
        const repChk      = _el('findModalReplaceMode');
        const mainInput   = _el('findModalInput');

        _gotoMode = chk ? chk.checked : false;

        const gotoHistLabel = _el('findModalGotoHistoryLabel');
        const gotoHistChk   = _el('findModalGotoHistoryMode');
        const gotoHistList  = _el('findModalGotoHistory');

        if (_gotoMode) {
            // Replace 체크 해제
            if (repChk) { repChk.checked = false; _replaceMode = false; }
            _onReplaceModeChange();
            // main input 숨김, goto area 표시
            if (mainInput) mainInput.style.display = 'none';
            if (area)      area.style.display = '';
            if (btnsFind)    btnsFind.style.display    = 'none';
            if (btnsReplace) btnsReplace.style.display = 'none';
            if (btnsGoto)    btnsGoto.style.display    = 'contents';
            // Go History 라벨 표시
            if (gotoHistLabel) gotoHistLabel.style.display = '';
            _loadGotoHistory();
            // 모바일: 자동 포커스 안 줌
        } else {
            if (mainInput) mainInput.style.display = '';
            if (area)      area.style.display      = 'none';
            if (btnsFind)    btnsFind.style.display    = 'contents';
            if (btnsReplace) btnsReplace.style.display = 'none';
            if (btnsGoto)    btnsGoto.style.display    = 'none';
            // Go History 라벨/목록 숨김
            if (gotoHistLabel) gotoHistLabel.style.display = 'none';
            if (gotoHistChk)   gotoHistChk.checked = false;
            if (gotoHistList)  gotoHistList.style.display = 'none';
        }
    }

    // ===== Modal UX: PopupManager + draggable =====
    let _dragBound = false;
    let _popup = null;
    let _matches = []; // { from, to }
    let _index   = -1;

    function _setupFindModalViewportLift() {
        _clampFindModalHeight();
    }

    function _clampFindModalHeight() {
        const modal = _el('findModal');
        if (!modal) return;
        const box = modal.querySelector('.modal');
        if (!box) return;
        const kbH = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--kb-h') || '0') || 0;
        const paddingTop = 60;
        const bottomMargin = 16;
        const maxH = window.innerHeight - kbH - paddingTop - bottomMargin;
        box.style.maxHeight = maxH + 'px';
    }

    function _resetFindModalBoxPosition() {
        const modal = _el('findModal');
        if (!modal) return;
        const box = modal.querySelector('.modal');
        if (!box) return;

        box.dataset.userMoved = '0';
        box.dataset.autoPinned = '0';
        box.style.left = '';
        box.style.top = '';
        box.style.bottom = '';
        box.style.transform = '';
        box.style.position = '';
    }

    function _bindFindModalDrag() {
        if (_dragBound) return;
        const modal = _el('findModal');
        if (!modal) return;
        const box = modal.querySelector('.modal');
        if (!box) return;

        const handle = box.querySelector('.modal-title-row') || box.querySelector('.modal-header') || _el('findModalDragHandle');
        if (!handle) return;

        _dragBound = true;

        let dragging = false;
        let startX = 0, startY = 0;
        let startLeft = 0, startTop = 0;

        const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

        const onDown = (e) => {
            // Do not start drag from interactive title actions.
            if (e.target && e.target.closest('.modal-title-action, .modal-link-btn, button, input, label, a')) return;

            // Only left button / primary touch
            if (e.button != null && e.button !== 0) return;

            dragging = true;
            box.dataset.userMoved = '1';
            try { handle.setPointerCapture(e.pointerId); } catch {}

            const rect = box.getBoundingClientRect();

            // Switch to pixel positioning
            box.style.position = 'fixed';
            box.style.transform = 'none';
            box.style.left = `${rect.left}px`;
            box.style.top  = `${rect.top}px`;
            box.style.bottom = 'auto';

            startX = e.clientX;
            startY = e.clientY;
            startLeft = rect.left;
            startTop  = rect.top;

            e.preventDefault();
        };

        const onMove = (e) => {
            if (!dragging) return;

            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            const rect = box.getBoundingClientRect();
            const maxLeft = window.innerWidth - rect.width;
            const maxTop  = window.innerHeight - rect.height;
            // 브랜드/슬롯 헤더 아래로만 이동 허용
            const headerEl = document.querySelector('.header-section');
            const minTop = headerEl ? (headerEl.getBoundingClientRect().bottom + 4) : 6;

            const nextLeft = clamp(startLeft + dx, 6, maxLeft - 6);
            const nextTop  = clamp(startTop + dy, minTop, maxTop - 6);

            box.style.left = `${nextLeft}px`;
            box.style.top  = `${nextTop}px`;
        };

        const onUp = (e) => {
            dragging = false;
            try { handle.releasePointerCapture(e.pointerId); } catch {}
        };

        handle.addEventListener('pointerdown', onDown, { passive: false });
        window.addEventListener('pointermove', onMove, { passive: true });
        window.addEventListener('pointerup', onUp, { passive: true });
    }


    function _el(id) { return document.getElementById(id); }

    // ===== 버튼 점등 =====
    function _lit(id, on) {
        const b = _el(id);
        if (!b) return;
        const s = getComputedStyle(document.documentElement);
        b.style.background  = on ? s.getPropertyValue('--ac-active-bg').trim() : '';
        b.style.borderColor = on ? s.getPropertyValue('--ac-active-bd').trim() : '';
        b.style.color       = on ? s.getPropertyValue('--ac-active-tx').trim() : '';
    }

    const _NAV_BTN_IDS    = ['btnNavUp','btnNavDown','btnNavLeft','btnNavRight'];
    const _FOOTER_BTN_IDS = ['btnFooterLeft','btnFooterRight'];

    function _litPurple(id, on) {
        const b = _el(id);
        if (!b) return;
        const s = getComputedStyle(document.documentElement);
        b.style.background  = on ? s.getPropertyValue('--ac-purple-bg').trim() : '';
        b.style.borderColor = on ? s.getPropertyValue('--ac-purple-bd').trim() : '';
        b.style.color       = on ? s.getPropertyValue('--ac-purple').trim()    : '';
    }

    function _setFooterFindActive(on) {
        _litPurple('btnFooterFind', on);
        _litPurple('btnFooterLeft', on);
        _litPurple('btnFooterRight', on);
    }

    function _setAllButtonsActive(on) {
        window._setFooterFindMode?.(on);
    }

    // ===== 카운트 표시 =====
    function _updateCount() {
        const el = _el('findModalCount');
        if (!el) return;
        el.textContent = _matches.length === 0 ? '0' : `${_index + 1}/${_matches.length}`;
    }

    // ===== 위치 표시 (Ln/Col) =====
    function _updateLoc() {
        const el = _el('findModalLoc');
        const view = Editor.get();
        if (!el || !view) return;

        // show current selection head position
        const pos = view.state.selection.main.head;
        const line = view.state.doc.lineAt(pos);
        const ln = line.number;
        const col = (pos - line.from) + 1;
        const total = view.state.doc.lines;
        el.textContent = `Ln ${ln}/${total} Col ${col}`;
    }


    // ===== Replace 모드 토글 =====
    function _onReplaceModeChange() {
        requestAnimationFrame(_positionFindModal);
        const chk         = _el('findModalReplaceMode');
        const toEl        = _el('findModalReplaceTo');
        const btnsFind    = _el('findModalBtnsFind');
        const btnsReplace = _el('findModalBtnsReplace');
        const goLabel     = _el('findModalGoLabel');
        const repHistLabel= _el('findModalRepHistoryLabel');
        const repHistList = _el('findModalRepHistoryList');

        _replaceMode = chk ? chk.checked : false;

        if (toEl)        toEl.style.display        = _replaceMode ? '' : 'none';
        if (btnsFind)    btnsFind.style.display     = _replaceMode ? 'none' : 'contents';
        if (btnsReplace) btnsReplace.style.display  = _replaceMode ? 'contents' : 'none';

        // Go ↔ Rep History 레이블 스왑
        if (goLabel)      goLabel.style.display      = _replaceMode ? 'none' : '';
        if (repHistLabel) repHistLabel.style.display  = _replaceMode ? '' : 'none';
        if (!_replaceMode && repHistList) {
            repHistList.style.display = 'none';
            const repHistChk = _el('findModalRepHistoryMode');
            if (repHistChk) repHistChk.checked = false;
        }

        // Replace 모드 ON 시 검색어 있으면 자동 Search
        if (_replaceMode && _el('findModalInput')?.value) {
            doSearch({ silent: true });
        }
    }

    // ===== 옵션 읽기 =====
    function _getOptions() {
        return {
            query:         (_el('findModalInput')?.value    ?? '').toString(),
            replaceTo:     (_el('findModalReplaceTo')?.value ?? '').toString(),
            caseSensitive: !!_el('findModalCase')?.checked,
            useRegex:      !!_el('findModalRegex')?.checked,
            fromStart:     !!(_el('findModalFromStart')?.checked ?? true),
        };
    }

    // ===== 매치 빌드 =====
    function _buildMatches(text, query, useRegex, caseSensitive) {
        const out = [];
        if (!query) return out;
        try {
            const flags = caseSensitive ? 'g' : 'gi';
            const src   = useRegex
                ? query
                : query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const re = new RegExp(src, flags);
            let m;
            while ((m = re.exec(text)) !== null) {
                const from = m.index;
                const to   = m.index + m[0].length;
                if (to === from) { re.lastIndex = from + 1; continue; }
                out.push({ from, to });
            }
        } catch (e) {
            UI?.showToast?.('Invalid regex', 1000);
        }
        return out;
    }

    // ===== CM6 매치 선택 + 스크롤 =====
    function _selectMatch(idx) {
        const view = Editor.get();
        if (!view) return;
        if (_matches.length === 0) {
            _index = -1;
            _updateCount();
            const loc = _el('findModalLoc'); if (loc) loc.textContent = '';
            return;
        }
        _index = ((idx % _matches.length) + _matches.length) % _matches.length;
        const m = _matches[_index];
        // Keep caret inside viewport: put head near start of match (avoid pushing caret to far right)
        view.dispatch({
            // keep full match selected, but put caret at start (head)
            selection:      { anchor: m.to, head: m.from },
            scrollIntoView: false,   // 3라인 규칙으로 대체
        });

        // Horizontal + vertical ensure: center X around match start
        try {
            view.dispatch({
                effects: CM6.EditorView.scrollIntoView(m.from, { x: 'center', y: 'center', margin: 16 })
            });
        } catch (e) {
            // ignore
        }

        // 3라인 규칙 (vertical stability)
        requestAnimationFrame(() => {
            window.UIViewport?.ensureCursorVisible?.();
        });
        _updateCount();
        _updateLoc();
        UI?.updateStats?.();
    }

    function _selectNearest(fromStart) {
        const view = Editor.get();
        if (!view || _matches.length === 0) { _index = -1; _updateCount(); return; }
        if (fromStart) { _selectMatch(0); return; }
        const cur = view.state.selection.main.head;
        let best  = 0;
        for (let i = 0; i < _matches.length; i++) {
            if (_matches[i].from >= cur) { best = i; break; }
        }
        _selectMatch(best);
    }

    // ===== 검색 =====
    function doSearch(opts = {}) {
        const view = Editor.get();
        if (!view) return;
        const { query, useRegex, caseSensitive, fromStart } = _getOptions();
        const text = view.state.doc.toString();
        _matches = _buildMatches(text, query, useRegex, caseSensitive);
        if (!opts.silent) {
            if (_matches.length === 0) {
                UI?.showToast?.('No matches found', 1500, 'top');
            } else {
                UI?.showToast?.(`Find: ${_matches.length}`, 700);
            }
            _addHistory(query);
        }
        _selectNearest(fromStart);
    }

    function quickSearch(direction) {
        // 블럭(BS/BE) 텍스트 있으면 히스토리에 먼저 추가
        const bs = window.State?.getBS?.();
        const be = window.State?.getBE?.();
        const blockText = (bs && be) ? (window.Editor?.getRange?.(bs, be) || '') : '';
        if (blockText) _addHistory(blockText);

        const sel = window.Editor?.getSelection?.();
        const query = (sel && sel.length > 0) ? sel : (_searchHistory[0] || '');
        if (!query) { UI?.showToast?.('No search history', 1200); return; }

        const input = document.getElementById('findModalInput');
        if (input) input.value = query;

        const view = Editor.get();
        if (!view) return;
        const { useRegex, caseSensitive } = _getOptions();
        const text = view.state.doc.toString();
        _matches = _buildMatches(text, query, useRegex, caseSensitive);

        if (_matches.length === 0) {
            UI?.showToast?.('No matches found', 1500, 'top');
            return;
        }
        _addHistory(query);
        _selectNearest(false);
        if (direction === 'next') {
            _selectMatch(_index + 1);
        } else {
            _selectMatch(_index - 1);
        }
    }

    function findNext() {
        if (_matches.length === 0) { doSearch({ silent: true }); return; }
        _selectMatch(_index + 1);
    }

    function findPrev() {
        if (_matches.length === 0) { doSearch({ silent: true }); return; }
        _selectMatch(_index - 1);
    }

    // ===== Replace =====
    function replaceOne() {
        const view = Editor.get();
        if (!view || _matches.length === 0) return;
        if (_index < 0) _selectNearest(false);
        if (_index < 0) return;

        const { replaceTo } = _getOptions();
        _addRepHistory(replaceTo);
        const m = _matches[_index];
        view.dispatch({ changes: { from: m.from, to: m.to, insert: replaceTo } });

        const delta = replaceTo.length - (m.to - m.from);
        _matches.splice(_index, 1);
        for (let i = _index; i < _matches.length; i++) {
            _matches[i].from += delta;
            _matches[i].to   += delta;
        }
        if (_matches.length === 0) {
            _index = -1;
            _updateCount();
        } else {
            _selectMatch(Math.min(_index, _matches.length - 1));
        }
        UI?.updateStats?.();
    }

    function replaceAll() {
        const view = Editor.get();
        if (!view || _matches.length === 0) return;

        const { replaceTo } = _getOptions();
        _addRepHistory(replaceTo);
        const count = _matches.length;
        const changes = [];
        for (let i = _matches.length - 1; i >= 0; i--) {
            changes.push({ from: _matches[i].from, to: _matches[i].to, insert: replaceTo });
        }
        view.dispatch({ changes });

        _matches = [];
        _index   = -1;
        _updateCount();
        UI?.showToast?.(`Replaced: ${count}`, 900);
        UI?.updateStats?.();
    }

    // ===== 방향키 인터셉트 (ui_events.js의 _bindRepeat에서 호출) =====

    
    function _positionFindModal() {
        const modal = _el('findModal');
        if (!modal) return;
        const box = modal.querySelector('.modal');
        if (!box) return;
        const headerEl = document.querySelector('.header-section');
        const top = headerEl ? (headerEl.getBoundingClientRect().bottom + 6) : 6;
        const maxW = Math.min(window.innerWidth - 12, 520);
        const left = Math.max(6, (window.innerWidth - maxW) / 2);
        box.style.position  = 'fixed';
        box.style.transform = 'none';
        box.style.bottom    = 'auto';
        box.style.top       = top + 'px';
        box.style.left      = left + 'px';
        box.style.width     = maxW + 'px';
        box.style.maxHeight = (window.innerHeight - top - 16) + 'px';
    }

    function _ensureFindPopup() {
        if (_popup) return _popup;
        const modal = _el('findModal');
        if (!modal || !window.PopupManager) return null;

        _popup = window.PopupManager.register('find', {
            modal,
            useKeyboardSafe: false,
            closeOnBackdrop: true,
            onAfterOpen() {
                _bindFindModalDrag();
                _positionFindModal();
            },
            onBeforeClose(opts) {
                if (opts?.reason !== 'dismiss') {
                    _active = false;
                    _replaceMode = false;
                    _setAllButtonsActive(false);
                }
            },
            onAfterClose() {
                Editor.focus();
            },
        });
        return _popup;
    }

    // ===== 입력값 초기화 =====
    function _clearInputs() {
        const input = _el('findModalInput');
        const rep   = _el('findModalReplaceTo');
        if (input) input.value = '';
        if (rep)   rep.value   = '';
        const locEl = _el('findModalLoc'); if (locEl) locEl.textContent = '';
        _matches = [];
        _index   = -1;
        _updateCount();
        _updateLoc();
        UI?.updateStats?.();
        if (input) {
            // keep keyboard state as-is; just move caret to start
            try { input.setSelectionRange(0, 0); } catch {}
        }
    }

// ===== 팝업만 닫기 (검색 결과 유지, 버튼 점등 유지) =====
    function _dismissModal() {
        _ensureFindPopup()?.close({ reason: 'dismiss' });
    }

    // ===== 완전 종료 (버튼 복귀) =====
    function closeModal() {
        _dismissModal();
        _active      = false;
        _replaceMode = false;
        _gotoMode    = false;
        // _matches는 유지 — 롱프레스 재활용
        _index       = -1;
        _setAllButtonsActive(false);
        _setFooterFindActive(false);
        Editor.focus();
        // LK 복원 — Find 닫히면 다시 키보드 차단
        if (window.State?.getLK?.()) window.UIViewport?.blockKeyboard?.();
    }

    // ===== 열기 =====
    function openModal({ history = false } = {}) {
        const input = _el('findModalInput');
        if (!_el('findModal')) return;

        // OS 키보드 내리기
        if (window._sysKbMode) {
            window.UIViewport?.blockKeyboard?.();
            window._sysKbMode = false;
        }
        const cm = window.Editor?.get?.()?.contentDOM;
        if (cm) {
            cm.setAttribute('inputmode', 'none');
            cm.blur();
        }

        _active = true;
        _setAllButtonsActive(true);
        // 슬롯 네비 모드 중이면 끄기
        if (window._slotNavMode) window._setSlotNavActive?.(false);

        // history 옵션: 히스토리 체크 ON + 목록 표시
        if (history) {
            const hchk = _el('findModalHistoryMode');
            if (hchk && !hchk.checked) { hchk.checked = true; }
            _historyMode = true;
        }

        const popup = _ensureFindPopup();
        popup?.open({ reason: 'command' });

        // LK 모드 반영 — Find 입력창은 LK 예외 허용
        const lk = State?.getLK?.() || false;
        if (input) input.inputMode = 'text';
        const repEl = _el('findModalReplaceTo');
        if (repEl) repEl.inputMode = 'text';
        // Find 모달 input 포커스 시 키보드 허용
        if (lk) window.UIViewport?.allowKeyboard?.();

        // Replace 체크 상태 반영
        _onReplaceModeChange();

        // 이벤트 바인딩
        const c = (id, fn) => { const b = _el(id); if (b) b.onclick = fn; };
        c('findModalClose',      closeModal);
        c('findModalSearch',     () => { doSearch(); if (_matches.length > 0) _dismissModal(); });
        c('findModalSearch2',    () => { doSearch(); if (_matches.length > 0) _dismissModal(); });
        c('findModalNext',       () => { findNext(); });
        c('findModalPrev',       () => { findPrev(); });
        c('findModalReplaceOne', () => { replaceOne(); });
        c('findModalReplaceAll', () => { replaceAll(); });
        c('findModalRepPrev',    () => { findPrev(); });
        c('findModalRepNext',    () => { findNext(); });
        c('findModalRepUndo',    () => { window.Nav?.undo?.(); });
        c('findModalClear',      () => { _clearInputs(); });

        const chk = _el('findModalReplaceMode');
        if (chk) chk.onchange = _onReplaceModeChange;

        const hchk = _el('findModalHistoryMode');
        if (hchk) hchk.onchange = _onHistoryModeChange;
        _loadHistory();
        _loadLastQuery();
        _loadRepHistory();

        const repHistChk = _el('findModalRepHistoryMode');
        if (repHistChk) repHistChk.onchange = () => {
            const list = _el('findModalRepHistoryList');
            if (!list) return;
            if (repHistChk.checked) {
                _renderRepHistory();
                list.style.display = '';
            } else {
                list.style.display = 'none';
            }
            requestAnimationFrame(_positionFindModal);
        };

        const gchk = _el('findModalGotoMode');
        if (gchk) gchk.onchange = _onGotoModeChange;

        const ghchk = _el('findModalGotoHistoryMode');
        if (ghchk) ghchk.onchange = () => {
            const list = _el('findModalGotoHistory');
            if (!list) return;
            if (ghchk.checked) {
                _loadGotoHistory();
                _renderGotoHistory();
                list.style.display = '';
            } else {
                list.style.display = 'none';
            }
        };
        // Go History 라벨 초기 숨김
        const ghl = _el('findModalGotoHistoryLabel');
        if (ghl) ghl.style.display = 'none';
        c('findModalGotoGo', _doGoto);
        const gotoInp = _el('findModalGotoInput');
        if (gotoInp) {
            gotoInp.oninput   = _onGotoInputChange;
            gotoInp.onkeydown = (e) => {
                if (e.key === 'Enter')  { e.preventDefault(); _doGoto(); }
                if (e.key === 'Escape') { closeModal(); }
            };
        }
        // goto 모드 초기화 (닫혔다 다시 열릴 때 reset)
        _gotoMode = false;
        if (gchk) gchk.checked = false;
        const garea = _el('findModalGotoArea');
        if (garea) garea.style.display = 'none';
        const btnsGoto = _el('findModalBtnsGoto');
        if (btnsGoto) btnsGoto.style.display = 'none';
        const mainInput = _el('findModalInput');
        if (mainInput) mainInput.style.display = '';

        if (input) {
            input.oninput   = () => {
                _matches = [];
                _index = -1;
                _updateCount();
            };
            input.onkeydown = (e) => {
                if (e.key === 'Enter')  { e.preventDefault(); doSearch(); if (_matches.length > 0) _dismissModal(); }
                if (e.key === 'Escape') { closeModal(); }
            };
        }

        if (input?.value) doSearch({ silent: true });
        _updateLoc();
        // 모바일: 자동 포커스 안 줌 — 키보드 올라오면서 팬 발생 방지
    }

    // 모달 없이 find 활성 상태만 켜기 (풋터 롱클릭용)

    function deactivateSilent() {
        _active = false;
        _setFooterFindActive(false);
        _setAllButtonsActive(false);
    }

    function toggleModal() {
        if (_gotoCooldown) return;  // goto 직후 재열기 방지
        if (_active) {
            // 이미 활성: 모달 열려있으면 닫기, 사일런트면 비활성
            if (_popup?.isOpen?.()) { closeModal(); return; }
            deactivateSilent();
            return;
        }
        openModal();
    }

    function init() {}

    // 외부에서 쿼리를 직접 넘겨 검색 실행 (히스토리 탭용)
    function searchQuery(q) {
        if (!q) return;
        const input = _el('findModalInput');
        if (input) input.value = q;
        const view = Editor.get();
        if (!view) return;
        const { useRegex, caseSensitive } = _getOptions();
        const text = view.state.doc.toString();
        _matches = _buildMatches(text, q, useRegex, caseSensitive);
        if (_matches.length === 0) { UI?.showToast?.('No matches found', 1500, 'top'); return; }
        _addHistory(q);
        UI?.showToast?.(`Find: ${_matches.length}`, 700);
        _selectNearest(false);
        _selectMatch(_index);
    }

    return {
        init,
        toggle: toggleModal,
        toggleModal, openModal, closeModal,
        doSearch, findNext, findPrev, quickSearch, searchQuery,
        replaceOne, replaceAll,
        isActive:      () => _active,
        deactivateSilent,
        getQuery:      () => _el('findModalInput')?.value || '',
        getHistory:    () => { if (!_searchHistory.length) _loadHistory(); return [..._searchHistory]; },
    };
})();

window.NavFind = NavFind;
