/* Path: usekit/tools/editor/js2/state/active_state.js
 * --------------------------------------------------------------------------------------------
 * ActiveState — 런타임 단일 진실 (Single Source of Truth)
 *
 * v2.0 (simplified):
 *   - input/edit/키패드 모드 제거
 *   - uiMode: 'quick' | 'menu' | 'hidden' 만 관리
 * ─────────────────────────────────────────────────────────── */

const ActiveState = (function () {
    'use strict';

    // ── 글로벌 UI 상태 ────────────────────────────────────────
    const _UI_DEFAULTS = {
        uiMode:           'quick',   // 'quick' | 'menu' | 'hidden' | 'nav'
        secondRowVisible: false,
        thirdRowVisible:  true,
        thirdRowLocMode:  false,
        navVisible:       true,
    };
    let _uiState = { ..._UI_DEFAULTS };

    // ── 글로벌 편집 상태 ──────────────────────────────────────
    const _EDIT_DEFAULTS = { lkMode: false };
    let _editState = { ..._EDIT_DEFAULTS };

    // ── 슬롯별 상태 ───────────────────────────────────────────
    const _DEFAULTS = {
        slotId: null,
        text:      '',
        cursor:    { line: 0, ch: 0 },
        scrollTop: 0,
        theme:       'light',
        font:        'default',
        fontSize:    14,
        wrap:        false,
        highlight:   true,
        lineNumbers: true,
        modeS:  false,
        modeM:  false,
        bs:        null,
        be:        null,
        activeEnd: null,
        navPanelIndex:    0,
        updatedAt: 0,
    };
    let _st = { ..._DEFAULTS };

    function get(key)  { return key ? _st[key] : { ..._st }; }
    function getAll()  { return { ..._st }; }
    function set(key, value) { _st[key] = value; _st.updatedAt = Date.now(); }
    function patch(obj) { Object.assign(_st, obj); _st.updatedAt = Date.now(); }

    // ── Editor Bridge ─────────────────────────────────────────
    function captureFromEditor() {
        if (!window.Editor?.isReady?.()) return;
        _st.text        = Editor.getText();
        _st.cursor      = Editor.getCursor();
        _st.scrollTop   = Editor.getScrollTop();
        _st.wrap        = !!Editor.getOption('lineWrapping');
        _st.highlight   = Editor.getOption('highlight') !== false;
        _st.lineNumbers = !!Editor.getOption('lineNumbers');
        _st.updatedAt   = Date.now();
    }

    function applyToEditor(opts) {
        if (!window.Editor?.isReady?.()) return;
        if (opts?.text !== false) Editor.setText(_st.text ?? '');
        Editor.setOption('lineWrapping', !!_st.wrap);
        Editor.setOption('highlight', _st.highlight !== false);
        if (window.UISettings?.applyHighlight) UISettings.applyHighlight(_st.highlight !== false ? 'on' : 'off');
        Editor.setOption('lineNumbers', !!_st.lineNumbers);
        if (!opts?.deferCursor) _applyCursorScroll();
    }

    function _applyCursorScroll() {
        if (!window.Editor?.isReady?.()) return;
        const cur = _st.cursor;
        if (cur && typeof cur.line === 'number') {
            const maxLine  = Editor.lineCount() - 1;
            const safeLine = Math.min(cur.line, Math.max(0, maxLine));
            const lineText = Editor.getLine(safeLine) || '';
            const safeCh   = Math.min(cur.ch, lineText.length);
            Editor.setCursor({ line: safeLine, ch: safeCh });
        }
        if (_st.scrollTop > 0) {
            Editor.scrollTo?.(_st.scrollTop);
            requestAnimationFrame(() => { Editor.scrollTo?.(_st.scrollTop); });
        }
    }

    function applyCursorScroll() { _applyCursorScroll(); }

    // ── State Bridge ──────────────────────────────────────────
    function captureFromState() {
        if (!window.State) return;
        _editState.lkMode = State.getLK();
        _st.modeS     = State.getModeS();
        _st.modeM     = State.getModeM();
        _st.bs        = State.getBS() ? { ...State.getBS() } : null;
        _st.be        = State.getBE() ? { ...State.getBE() } : null;
        _st.activeEnd = State.getActiveEnd ? State.getActiveEnd() : null;
    }

    function applyToState() {
        if (!window.State) return;
        State.setLK(_editState.lkMode);
        State.setModeM(_st.modeM);
        State.setBS(_st.bs || null);
        State.setBE(_st.be || null);
        if (State.setActiveEnd) State.setActiveEnd(_st.activeEnd || null);
    }

    // ── UI Bridge ─────────────────────────────────────────────
    function captureUI() {
        const app       = document.querySelector('.editor-app');
        _uiState.navVisible       = app       ? !app.classList.contains('nav-hidden')      : true;
        // 편집 nav-block 제거됨 — secondRow/thirdRow 상태 캡처 불필요
    }

    function applyUI() {
        const mode = _uiState.uiMode;

        // 패널 전환
        if (mode === 'hidden') {
            document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
        } else {
            const target = mode === 'menu' ? 'panel-buttons'
                         : mode === 'nav'  ? 'panel-navigation'
                         : 'panel-quick';
            document.querySelectorAll('.swipe-panel').forEach(p =>
                p.classList.toggle('active', p.classList.contains(target))
            );
        }

        // nav-hidden
        const app = document.querySelector('.editor-app');
        if (app) {
            app.classList.toggle('nav-hidden', mode === 'hidden');
            window.UI?.recalcHeight?.();
        }

        // 편집 nav-block 제거됨 — secondRow/thirdRow/locMode 복원 불필요
    }

    function captureFromUI() { captureUI(); }
    function applyToUI() {
        applyUI();
        // ui_events 내부 _ui 변수 동기화
        window.UIEvents?.syncUiMode?.(_uiState.uiMode);
        // LK 버튼 색상
        window.UIEvents?._syncButtonColors?.();
        // LK ON → keyboard block
        if (_editState.lkMode) {
            window.UIViewport?.blockKeyboard?.();
        } else if (!window.SlotManager?.isSwitchingSlot?.()) {
            window.UIViewport?.allowKeyboard?.();
        }
        window.UIStats?.updateKUButton?.(false);
    }

    // ── 접근자 ────────────────────────────────────────────────
    function getUI(key)          { return key ? _uiState[key] : { ..._uiState }; }
    function setUI(key, value)   { _uiState[key] = value; }
    function getEdit(key)        { return key ? _editState[key] : { ..._editState }; }
    function setEdit(key, value) { _editState[key] = value; }

    // ── Snapshot ──────────────────────────────────────────────
    function toSnapshot() {
        captureFromEditor();
        captureFromState();
        captureUI();
        return {
            text:      _st.text,
            cursor:    { ..._st.cursor },
            scrollTop: _st.scrollTop,
            settings: {
                theme:       _st.theme,
                font:        _st.font,
                fontSize:    _st.fontSize,
                wrap:        _st.wrap,
                highlight:   _st.highlight,
                lineNumbers: _st.lineNumbers,
            },
            edit: {
                modeM:     _st.modeM,
                bs:        _st.bs        ? { ..._st.bs }   : null,
                be:        _st.be        ? { ..._st.be }   : null,
                activeEnd: _st.activeEnd || null,
            },
            ui: { ..._uiState },
            updatedAt: Date.now(),
        };
    }

    function fromSnapshot(snap) {
        if (!snap) return;
        const policy = SetupPolicy?.get?.() || {};

        _st.text      = snap.text      ?? '';
        _st.cursor    = snap.cursor    ? { ...snap.cursor } : { line: 0, ch: 0 };
        _st.scrollTop = snap.scrollTop ?? 0;

        const s = snap.settings || {};
        if (policy.theme    === 'slot' && s.theme    != null) _st.theme    = s.theme;
        if (policy.font     === 'slot' && s.font     != null) _st.font     = s.font;
        if (policy.fontSize === 'slot' && s.fontSize != null) _st.fontSize = Number(s.fontSize);
        if (s.wrap        !== undefined) _st.wrap        = !!s.wrap;
        if (policy.highlight === 'slot' && s.highlight !== undefined) _st.highlight = !!s.highlight;
        if (s.lineNumbers !== undefined) _st.lineNumbers = !!s.lineNumbers;

        const e = snap.edit || {};
        _st.modeM     = !!e.modeM;
        _st.bs        = e.bs        ? { ...e.bs }   : null;
        _st.be        = e.be        ? { ...e.be }   : null;
        _st.activeEnd = e.activeEnd || null;
        _st.updatedAt = Date.now();
        // ui는 글로벌 — 슬롯 복원 시 건드리지 않음
    }

    function reset(slotId) {
        _st = { ..._DEFAULTS, slotId: slotId || null };
    }

    return {
        get, getAll, set, patch,
        captureFromEditor, applyToEditor, applyCursorScroll,
        captureFromState,  applyToState,
        captureFromUI,     applyToUI,
        captureUI,         applyUI,
        getUI,             setUI,
        getEdit,           setEdit,
        toSnapshot, fromSnapshot,
        reset,
    };
})();

window.ActiveState = ActiveState;
