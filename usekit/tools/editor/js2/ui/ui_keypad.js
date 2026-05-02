/**
 * ui_keypad.js — LK 임시 키패드
 * Cap OFF: 소문자 / 숫자 / =/+ _/- ,/× ./÷
 * Cap ON : 대문자 / !@#$%^&*() / + - × ÷
 * 리피트: 350ms 후 80ms 간격 반복
 */
const UIKeypad = (function () {
    'use strict';

    let _cap = false;
    let _shift = false; // 단발 Shift
    let _shiftHeld = false; // 홀드 Shift
    let _ctrl = false;  // 단발 Ctrl
    let _ctrlHeld = false; // 홀드 Ctrl
    let _alt = false;   // 단발 Alt
    let _altHeld = false; // 홀드 Alt
    let _kpRow1Mode = 'default';
    let _spMode = ''; // 특수기호 모드 '' | 'sp1' | 'sp2' | 'sp3'
    const _KP1_DEFAULT = [
        { k: '1', s: '!' }, { k: '2', s: '@' }, { k: '3', s: '#' },
        { k: '4', s: '$' }, { k: '5', s: '%' }, { k: '6', s: '^' },
        { k: '7', s: '&' }, { k: '8', s: '*' }, { k: '9', s: '(' },
        { k: '0', s: ')' },
    ];
    const _KP1_ALT = ['`', '\\', '|', '※', '《', '》', '/*', '*/', '<!', '//'];

    function _applyKp1Mode(mode) {
        _kpRow1Mode = mode;
        const btns = document.querySelectorAll('#kpRow1 .cbtn:not(#kbDel):not(#kbSlash)');
        const isAlt = mode === 'alt';
        const more = document.getElementById('kpRow1More');
        if (more) more.style.color = isAlt ? 'var(--ac-blue)' : '';
        btns.forEach((btn, i) => {
            if (isAlt) {
                btn.textContent = _KP1_ALT[i] ?? '';
                btn.dataset.k = _KP1_ALT[i] ?? '';
                btn.dataset.s = _KP1_ALT[i] ?? '';
            } else {
                btn.textContent = (_cap || _shift)
                    ? _KP1_DEFAULT[i].s
                    : _KP1_DEFAULT[i].k + '/' + _KP1_DEFAULT[i].s;
                btn.dataset.k = _KP1_DEFAULT[i].k;
                btn.dataset.s = _KP1_DEFAULT[i].s;
            }
        });
    }
    const KP_IDS = ['kpRow0','kpRow1','kpRow2','kpRow3','kpRow4','kpRow5'];

    // kpRow0 모드 토글 (1번 기본 ↔ 2번)
    let _kpRow0Mode = 'a'; // 'a' | 'b'
    const _kp0Handlers = {};

    // 토글 대상 버튼 id 목록 (btn1, btn2, btn8~11)
    const _KP0_A = [
        { id: 'kpBtn0a', get lbl() { return (_cap||_shift) ? '[' : '_/['; }, fn: () => _insert((_cap||_shift) ? '[' : '_') },
        { id: 'kpBtn0b', get lbl() { return (_cap||_shift) ? ']' : '~/]'; }, fn: () => _insert((_cap||_shift) ? ']' : '~') },
        { id: 'kpBtn1',  get lbl() { return (_shift||_cap) ? '{' : "'/{"  ; }, fn: () => _insert((_shift||_cap) ? '{' : "'") },
        { id: 'kpBtn2',  get lbl() { return (_shift||_cap) ? '}' : '"/}' ; }, fn: () => _insert((_shift||_cap) ? '}' : '"') },
        { id: 'kpBtn0c', get lbl() { return (_cap||_shift) ? '<' : ':/<'; }, fn: () => _insert((_cap||_shift) ? '<' : ':') },
        { id: 'kpBtn0d', get lbl() { return (_cap||_shift) ? '>' : ';/>'; }, fn: () => _insert((_cap||_shift) ? '>' : ';') },
        { id: 'kpBtn8',  get lbl() { return (_cap||_shift) ? '+' : '=/+'; }, fn: () => _insert((_cap||_shift) ? '+' : '=') },
        { id: 'kpBtn9',  get lbl() { return (_cap||_shift) ? '-' : '?/-'; }, fn: () => _insert((_cap||_shift) ? '-' : '?') },
        { id: 'kpBtn10', get lbl() { return (_cap||_shift) ? '×' : ',/×'; }, fn: () => _insert((_cap||_shift) ? '×' : ',') },
        { id: 'kpBtn11', get lbl() { return (_cap||_shift) ? '÷' : './÷'; }, fn: () => _insert((_cap||_shift) ? '÷' : '.') },
    ];
    const _KP0_B = [
        { id: 'kpBtn0a', lbl: '`', fn: () => _insert('`') },
        { id: 'kpBtn0b', lbl: '~', fn: () => _insert('~') },
        { id: 'kpBtn1',  lbl: '<', fn: () => _insert('<') },
        { id: 'kpBtn2',  lbl: '>', fn: () => _insert('>') },
        { id: 'kpBtn0c', lbl: '[', fn: () => _insert('[') },
        { id: 'kpBtn0d', lbl: ']', fn: () => _insert(']') },
        { id: 'kpBtn8',  lbl: ':'    , fn: () => _insert(':') },
        { id: 'kpBtn9',  lbl: ';'    , fn: () => _insert(';') },
        { id: 'kpBtn10', lbl: '/'    , fn: () => _insert('/') },
        { id: 'kpBtn11', lbl: '|'    , fn: () => _insert('|') },
    ];

    const _KP0_F = [
        { id: 'kpBtn0a', lbl: 'F1',  fn: () => window.KpFn?.[1]?.() },
        { id: 'kpBtn0b', lbl: 'F2',  fn: () => window.KpFn?.[2]?.() },
        { id: 'kpBtn1',  lbl: 'F3',  fn: () => window.KpFn?.[3]?.() },
        { id: 'kpBtn2',  lbl: 'F4',  fn: () => window.KpFn?.[4]?.() },
        { id: 'kpBtn0c', lbl: 'F5',  fn: () => window.KpFn?.[5]?.() },
        { id: 'kpBtn0d', lbl: 'F6',  fn: () => window.KpFn?.[6]?.() },
        { id: 'kpBtn8',  lbl: 'F7',  fn: () => window.KpFn?.[7]?.() },
        { id: 'kpBtn9',  lbl: 'F8',  fn: () => window.KpFn?.[8]?.() },
        { id: 'kpBtn10', lbl: 'F9',  fn: () => window.KpFn?.[9]?.() },
        { id: 'kpBtn11', lbl: 'F10', fn: () => window.KpFn?.[10]?.() },
    ];

    // F키 기본 동작 정의 (향후 사용자 정의로 교체 가능)
    // confirmModal 헬퍼
    function _confirm(msg, onOk) {
        const m   = document.getElementById('confirmModal');
        const txt = document.getElementById('confirmModalMessage');
        const ok  = document.getElementById('btnConfirmModalOk');
        const cancel = document.getElementById('btnConfirmModalCancel');
        const close  = document.getElementById('btnConfirmModalClose');
        if (!m || !ok) { if (confirm(msg)) onOk(); return; }
        txt.textContent = msg;
        ok.textContent  = 'OK';
        ok.classList.remove('modal-btn-danger');
        m.style.display = '';
        m.setAttribute('aria-hidden', 'false');
        const hide = () => { m.style.display = 'none'; m.setAttribute('aria-hidden', 'true'); };
        const onY  = () => { hide(); onOk(); };
        ok.addEventListener('click',     onY,  { once: true });
        cancel.addEventListener('click', hide, { once: true });
        close.addEventListener('click',  hide, { once: true });
        m.addEventListener('click', e => { if (e.target === m) hide(); }, { once: true });
    }

    window.KpFn = {
        1:  () => {                                                       // F1: Help
                const m = document.getElementById('helpModal');
                if (!m) return;
                m.style.display = '';
                m.setAttribute('aria-hidden', 'false');
                const close = () => { m.style.display = 'none'; m.setAttribute('aria-hidden', 'true'); };
                document.getElementById('btnHelpModalClose')?.addEventListener('click', close, { once: true });
                document.getElementById('btnHelpModalOk')   ?.addEventListener('click', close, { once: true });
                m.addEventListener('click', e => { if (e.target === m) close(); }, { once: true });
            },
        2:  () => {                                                       // F2: Find Prev
                const q = window.NavFind?.getQuery?.();
                if (!q) { window.NavFind?.openModal?.(); return; }
                window.NavFind?.findPrev?.();
            },
        3:  () => {                                                       // F3: Find Next
                const q = window.NavFind?.getQuery?.();
                if (!q) { window.NavFind?.openModal?.(); return; }
                window.NavFind?.findNext?.();
            },
        4:  () => _confirm('Close the current slot?',                    // F4: Close
                    () => window.SlotManager?.closeCurrentSlot?.()),
        5:  () => {                                                       // F5: Save
                window.SlotManager?.save?.({ silent: true });
                window.UI?.showToast?.('💾 Saved', 1000, 'top');
            },
        6:  () => _confirm('Create a new slot?',                         // F6: New
                    () => window.SlotManager?.newFile?.()),
        7:  () => window.SlotManager?.openSavePopup?.(),                 // F7: Save As
        8:  () => window.SlotManager?.openLoadPopup?.(),                 // F8: Load
        9:  () => window.Nav?.goToLine?.(),                              // F9: Go to Line
        10: () => window.NavClipboard?.openModal?.(),                    // F10: Clipboard
    };

    let _kp0AbortController = null;
    function _applyKp0Mode(items) {
        // 기존 핸들러 전체 제거
        if (_kp0AbortController) _kp0AbortController.abort();
        _kp0AbortController = new AbortController();
        const signal = _kp0AbortController.signal;

        items.forEach(({ id, lbl, fn }) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.innerHTML = lbl;
            el.addEventListener('pointerdown', e => { e.preventDefault(); UIFeedback?.special(); fn(); }, { signal });
            el.addEventListener('touchstart', e => e.preventDefault(), { passive: false, signal });
        });
        const more = document.getElementById('kpRow0More');
        if (more) more.style.color = _kpRow0Mode === 'b' ? 'var(--ac-blue)' : '';
    }


    function _navBlocks() {
        return Array.from(document.querySelectorAll('.panel-navigation .nav-block:not(.kp-block)'));
    }

    function show() {
        _navBlocks().forEach(el => {
            el._kpWasVisible = !el.classList.contains('is-hidden');
            el.classList.add('is-hidden');
        });
        KP_IDS.forEach(id => document.getElementById(id)?.classList.remove('is-hidden'));
        if (window.UIViewport?.recalcEditorRect) UIViewport.recalcEditorRect();
        window.UIStats?.updateKUButton?.(false);
        window.ActiveState?.captureUI?.();
        window.SlotManager?.saveUIState?.();
    }

    function hide() {
        KP_IDS.forEach(id => document.getElementById(id)?.classList.add('is-hidden'));
        _navBlocks().forEach(el => {
            if (!window._sysKbMode && el._kpWasVisible) el.classList.remove('is-hidden');
            el._kpWasVisible = undefined;
        });
        if (window.UIViewport?.recalcEditorRect) UIViewport.recalcEditorRect();
        window.UIStats?.updateKUButton?.(false);
        if (!window._sysKbMode) {
            window.ActiveState?.captureUI?.();
            window.SlotManager?.saveUIState?.();
        }
    }

    function isOpen() {
        return !(document.getElementById('kpRow5')?.classList.contains('is-hidden') ?? true);
    }

    function toggle() { isOpen() ? hide() : show(); }

    // Ctrl 커맨드 실행
    const _CTRL_CMD = {
        z: () => window.Nav?.undo?.(),
        y: () => window.Nav?.redo?.(),
        x: () => { const t = window.NavBlock?.copyBlock?.(); if (t) { window.NavClipboard?.push?.(t); window.Nav?.cutLine?.(); } },
        c: () => { const t = window.NavBlock?.copyBlock?.() || window.Editor?.getSelection?.(); if (t) window.NavClipboard?.push?.(t); },
        v: () => window.Nav?.pasteAtCursor?.(),
        s: () => window.SlotManager?.save?.({ silent: false }),
        f: () => window.NavFind?.openModal?.(),
        a: () => window.Nav?.selectAllModeA?.(),
        g: () => window.Nav?.goToLine?.(),
        n: () => window.SlotManager?.newFile?.(),
        d: () => {
            // 라인 복제
            const view = window.Editor?.get?.();
            if (!view) return;
            const { state } = view;
            const line = state.doc.lineAt(state.selection.main.head);
            const insert = '\n' + line.text;
            view.dispatch({ changes: { from: line.to, insert } });
        },
        w: () => window.SlotManager?.closeCurrentSlot?.(),              // 탭 닫기
        '/': () => window.Nav?.toggleComment?.(),                       // 주석 토글
        l: () => window.Nav?.selectCurrentLine?.(),                     // 현재 라인 선택
        // Ctrl+Home/End → 방향키 조합으로 처리 (별도)
    };

    function _ctrlExec(ch) {
        const cmd = _CTRL_CMD[ch.toLowerCase()];
        if (!cmd) return false;
        UIFeedback?.special();
        cmd();
        if (_ctrl && !_ctrlHeld) _setCtrl(false);
        return true;
    }

    // 문자 입력 후 BS/BE를 현재 커서로 동기화 (Shift 대문자 입력 시 블럭 없이 커서 추적)
    function _syncBlockToCursor() {
        const cur = window.Editor?.getCursor?.();
        if (!cur) return;
        window.State?.setBS?.(cur);
        window.State?.setBE?.(cur);
    }

    function _insert(ch) {
        // Ctrl 조합 체크
        if ((_ctrl || _ctrlHeld) && ch.length === 1 && _CTRL_KEYS.has(ch.toLowerCase())) {
            _ctrlExec(ch);
            return;
        }
        if (_shift && !_shiftHeld) _setShift(false);
        // 문자 종류별 피드백
        if (ch === '\n') UIFeedback?.enter();
        else if (ch === '\t' || ch === ' ') UIFeedback?.space();
        else if (ch.length === 1 && /[a-zA-Z0-9]/.test(ch)) UIFeedback?.key();
        else UIFeedback?.special();
        // 블럭모드 인터셉트
        if (window._uiIsBlockMode?.()) {
            if (window.BlockState?.isActive?.()) {
                const _isCheck = window.BlockState.isCheckMode();
                if (_isCheck) window.NavBlockV2?.checkEdit?.('insert', ch);
                else          window.NavBlockV2?.editAll?.('insert', ch);
            } else {
                window.NavBlock?.insertAtColumnBlock?.(ch);
            }
            return;
        }
        Editor.replaceSelection(ch);
        Editor.focus();
        if (_shift || _shiftHeld) _syncBlockToCursor();
    }

    function _insertLang(btn) {
        let ch;
        const _spKey = _spMode === 'sp1' ? 'sp' : _spMode;
        if (_spMode && btn.dataset[_spKey]) {
            ch = btn.dataset[_spKey];
        } else {
            const upper = _cap || _shift;
            ch = upper ? btn.dataset.s : btn.dataset.k;
        }
        // Ctrl 조합 체크
        if ((_ctrl || _ctrlHeld) && ch && ch.length === 1 && _CTRL_KEYS.has(ch.toLowerCase())) {
            _ctrlExec(ch);
            return;
        }
        if (_shift && !_shiftHeld) _setShift(false);
        // 문자 종류별 피드백
        if (ch === '\n') UIFeedback?.enter();
        else if (ch === '\t' || ch === ' ') UIFeedback?.space();
        else if (ch && ch.length === 1 && /[a-zA-Z0-9]/.test(ch)) UIFeedback?.key();
        else UIFeedback?.special();
        // 블럭모드 인터셉트
        if (window._uiIsBlockMode?.() && ch) {
            if (window.BlockState?.isActive?.()) {
                const _isCheck = window.BlockState.isCheckMode();
                if (_isCheck) window.NavBlockV2?.checkEdit?.('insert', ch);
                else          window.NavBlockV2?.editAll?.('insert', ch);
            } else {
                window.NavBlock?.insertAtColumnBlock?.(ch);
            }
            return;
        }
        Editor.replaceSelection(ch);
        Editor.focus();
        if (_shift || _shiftHeld) _syncBlockToCursor();
    }

    function _applySpMode(mode) {
        _spMode = mode;
        // 점등 상태
        ['kpRow2More','kpRow3More','kpRow4More'].forEach((id, i) => {
            const m = document.getElementById(id);
            if (m) m.style.color = (mode === ['sp1','sp2','sp3'][i]) ? 'var(--ac-blue)' : '';
        });
        document.querySelectorAll('.kp-block [data-sp]').forEach(btn => {
            const spKey = mode === 'sp1' ? 'sp' : mode;
            if (mode && btn.dataset[spKey]) {
                const val = btn.dataset[spKey];
                btn.textContent = val === '\n' ? '\\n' : val === '\t' ? '\\t' : val;
            } else {
                btn.textContent = (_cap || _shift) ? btn.dataset.s : btn.dataset.k;
            }
        });
    }

    function _setCap(on) {
        _cap = on;
        const capBtn = document.getElementById('kbCap');
        capBtn?.classList.toggle('cap-active', _cap);

        // 알파벳 행 라벨 업데이트
        document.querySelectorAll('.kp-block [data-k]').forEach(b => {
            b.textContent = _cap ? b.dataset.s : b.dataset.k;
        });

        // kpRow0 A모드 라벨 업데이트 (Cap 상태 반영)
        if (_kpRow0Mode === 'a') _applyKp0Mode(_KP0_A);

        // kpRow1 토글 모드 라벨 재적용
        _applyKp1Mode(_kpRow1Mode);
    }

    // 리피트 바인딩
    function _setShift(on) {
        _shift = on;
        document.getElementById('kpShift')?.classList.toggle('cap-active', on);
        document.getElementById('kpShift2')?.classList.toggle('cap-active', on);
        if (on) {
            // Shift 켜질 때 — 현재 커서를 즉시 BS로 고정
            const cur = window.Editor?.getCursor?.();
            if (cur) { window.State?.setBS?.(cur); window.State?.setBE?.(cur); }
        } else {
            // Shift 꺼질 때 — Alt 해제, BS/BE null 초기화 (CM6 선택은 유지)
            if (_alt || _altHeld) { _altHeld = false; _setAlt(false); }
            window.NavCursor?.clearSelectAnchor?.();
            window.State?.setBS?.(null);
            window.State?.setBE?.(null);
        }
        // 알파벳/숫자 라벨 — shift 또는 cap 기준
        const upper = on || _cap;
        document.querySelectorAll('.kp-block [data-k]').forEach(b => {
            b.textContent = upper ? b.dataset.s : b.dataset.k;
        });
        if (_kpRow0Mode === 'a') _applyKp0Mode(_KP0_A);
        _applyKp1Mode(_kpRow1Mode);
    }

    // Ctrl 조합 가능한 키 목록
    const _CTRL_KEYS = new Set(['z','y','x','c','v','s','f','a','g','n','d','w','l','/']);
    let _ctrlKeyBtns = null;  // 초기화 후 캐싱
    let _ctrlOtherBtns = null;

    function _setCtrl(on) {
        _ctrl = on;
        document.getElementById('kpCtl')?.classList.toggle('cap-active', on);
        // 최초 1회만 DOM 캐싱
        if (!_ctrlKeyBtns) {
            const all = Array.from(document.querySelectorAll('.kp-block [data-k]'));
            _ctrlKeyBtns  = all.filter(b => _CTRL_KEYS.has((b.dataset.k || '').toLowerCase()));
            _ctrlOtherBtns = all.filter(b => !_CTRL_KEYS.has((b.dataset.k || '').toLowerCase()));
        }
        if (on) {
            _ctrlKeyBtns.forEach(b => { b.style.background = 'var(--ac-blue-bg)'; b.style.borderColor = 'var(--ac-blue-bd)'; b.style.color = 'var(--ac-blue)'; });
        } else {
            _ctrlKeyBtns.forEach(b => { b.style.background = ''; b.style.borderColor = ''; b.style.color = ''; });
        }
    }

    function _setAlt(on) {
        _alt = on;
        document.getElementById('kpAlt')?.classList.toggle('cap-active', on);
    }

    function _bindRepeat(el, fn, initDelay = 350, repeatDelay = 80) {
        if (!el) return;
        let _timer = null, _interval = null;
        const stop = () => {
            if (_timer)    { clearTimeout(_timer);     _timer    = null; }
            if (_interval) { clearInterval(_interval); _interval = null; }
        };
        el.addEventListener('pointerdown', e => {
            e.preventDefault();
            stop();
            fn(true);   // first press only
            _timer = setTimeout(() => {
                _interval = setInterval(() => fn(false), repeatDelay);
            }, initDelay);
        });
        el.addEventListener('pointerup',     stop);
        el.addEventListener('pointercancel', stop);
        el.addEventListener('pointerleave',  stop);
        el.addEventListener('touchstart', e => e.preventDefault(), { passive: false });
    }

    function init() {
        // 첫 터치에서 AudioContext unlock (모바일 autoplay 제한 우회)
        document.addEventListener('pointerdown', () => UIFeedback?.unlock(), { once: true });

        // 저장된 키패드 모드 복원
        const saved = window.ActiveState?.getUI?.();
        if (saved) {
            if (saved.kpRow0Mode && saved.kpRow0Mode !== 'a') {
                _kpRow0Mode = saved.kpRow0Mode;
            }
            if (saved.kpRow1Mode && saved.kpRow1Mode !== 'default') {
                _kpRow1Mode = saved.kpRow1Mode;
            }
            if (saved.spMode) {
                _spMode = saved.spMode;
            }
        }

        // ── kpRow0: cursor 행 (단순 클릭) ──
        document.querySelector('#kpRow0 .kp-modeS')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            if (State.getModeA?.()) Nav.resetModeA?.();
            Nav.toggleModeS?.();
            UI.updateStats?.();
        });
        document.querySelector('#kpRow0 .kp-modeM')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            Nav.toggleModeM?.();
            UI.updateStats?.();
        });
        document.querySelector('#kpRow0 .kp-selAll')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            Nav.progressiveSelect?.();
            UI.updateStats?.();
        });

        // 방향키 리피트 (kpRow5)
        _bindRepeat(document.querySelector('#kpRow5 .kp-left'),  () => { UIFeedback?.special(); if (window.NavFocus?.isOn?.()) { NavFocus.scrollH(-3); return; } if ((_shift||_shiftHeld) && (_alt||_altHeld)) { Nav.shiftIndent?.(-1); return; } if ((_shift||_shiftHeld) && (_ctrl||_ctrlHeld)) { Nav.selectWordLeft?.();  return; } if (_shift || _shiftHeld) { Nav.selectLeft?.();  return; } if (_ctrl || _ctrlHeld) { Nav.wordLeft?.(); return; } if (_alt || _altHeld) { Nav.indent?.(-1); return; } if (State.getModeA?.()) { Nav.modeAMoveLeft?.();  return; } Nav.moveLeft?.(); });
        _bindRepeat(document.querySelector('#kpRow5 .kp-up'),    () => { UIFeedback?.special(); if (window.NavFocus?.isOn?.()) { NavFocus.scrollV(-1); return; } if ((_shift||_shiftHeld) && (_alt||_altHeld)) { Nav.shiftMoveBlock?.(-1); return; } if ((_shift||_shiftHeld) && (_ctrl||_ctrlHeld)) { Nav.selectDocStart?.(); return; } if (_shift || _shiftHeld) { Nav.selectUp?.();    return; } if (_ctrl || _ctrlHeld) { Nav.pageUp?.();       return; } if (_alt || _altHeld) { Nav.moveLineAlt?.(-1); return; } if (State.getModeA?.()) { Nav.modeAMoveUp?.();    return; } Nav.moveUp?.(); });
        _bindRepeat(document.querySelector('#kpRow5 .kp-down'),  () => { UIFeedback?.special(); if (window.NavFocus?.isOn?.()) { NavFocus.scrollV( 1); return; } if ((_shift||_shiftHeld) && (_alt||_altHeld)) { Nav.shiftMoveBlock?.(1);  return; } if ((_shift||_shiftHeld) && (_ctrl||_ctrlHeld)) { Nav.selectDocEnd?.();   return; } if (_shift || _shiftHeld) { Nav.selectDown?.();  return; } if (_ctrl || _ctrlHeld) { Nav.pageDown?.();     return; } if (_alt || _altHeld) { Nav.moveLineAlt?.(1);  return; } if (State.getModeA?.()) { Nav.modeAMoveDown?.();  return; } Nav.moveDown?.(); });
        _bindRepeat(document.querySelector('#kpRow5 .kp-right'), () => { UIFeedback?.special(); if (window.NavFocus?.isOn?.()) { NavFocus.scrollH( 3); return; } if ((_shift||_shiftHeld) && (_alt||_altHeld)) { Nav.shiftIndent?.(1);  return; } if ((_shift||_shiftHeld) && (_ctrl||_ctrlHeld)) { Nav.selectWordRight?.(); return; } if (_shift || _shiftHeld) { Nav.selectRight?.(); return; } if (_ctrl || _ctrlHeld) { Nav.wordRight?.(); return; } if (_alt || _altHeld) { Nav.indent?.(1);  return; } if (State.getModeA?.()) { Nav.modeAMoveRight?.(); return; } Nav.moveRight?.(); });

        // kpBtn0a/0b/0c/0d — _applyKp0Mode에서 처리

        // Esc — 자판 상태 전체 초기화 (모든 토글 → 기본값)
        document.getElementById('kpEsc')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            UIFeedback?.toggle();
            // Cap / Shift / Ctrl / Alt 해제
            _shiftHeld = false;
            _setShift(false);
            _setCap(false);
            _ctrlHeld = false;
            _setCtrl(false);
            _altHeld = false;
            _setAlt(false);
            // 블록/선택 초기화
            if (window.State?.getModeS?.()) window.State?.setModeS?.(false);
            window.State?.clearBlock?.();
            window.Editor?.clearSelection?.();
            // Row0: A모드 복원
            _kpRow0Mode = 'a';
            _applyKp0Mode(_KP0_A);
            // Row1: default 복원
            _applyKp1Mode('default');
            // sp모드 해제
            _applySpMode('');
            Editor.focus?.();
        });

        // Ctl / Alt (예비 — 향후 단축키 연동)
        // kpCtl: _bindCtrl()에서 처리 / kpAlt: _bindAlt()에서 처리

        _bindRepeat(document.getElementById('kbSpace'), () => _insert(' '));

        // / (슬래시)
        _bindRepeat(document.getElementById('kbSlash'), () => _insert('/'));

        _bindShift('kpShift2');

        // ── 6열 기어: Space 위치 토글 (kpRow5More) ──
        document.getElementById('kpRow5More')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            const row5 = document.getElementById('kpRow5');
            if (!row5) return;
            UIFeedback?.toggle();
            row5.classList.toggle('kp-row5-alt');
            const alt = row5.classList.contains('kp-row5-alt');
            window.ActiveState?.setUI?.('kpRow5Alt', alt);
            window.SlotManager?.saveUIState?.();
        });

        // ── 2열 토글 바인딩 ──
        document.getElementById('kpRow1More')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            UIFeedback?.toggle();
            _applyKp1Mode(_kpRow1Mode === 'default' ? 'alt' : 'default');
            window.ActiveState?.setUI?.('kpRow1Mode', _kpRow1Mode);
            window.SlotManager?.saveUIState?.();
        });

        [['kpRow2More','sp1'],['kpRow3More','sp2'],['kpRow4More','sp3']].forEach(([id, mode]) => {
            document.getElementById(id)?.addEventListener('pointerdown', e => {
                e.preventDefault();
                UIFeedback?.toggle();
                _applySpMode(_spMode === mode ? '' : mode);
                window.ActiveState?.setUI?.('spMode', _spMode);
                window.SlotManager?.saveUIState?.();
            });
        });

        // =/+ _/- ,/× ./÷ → Cap 상태에 따라 값 결정, 리피트
        // kpBtn8~11 은 _applyKp0Mode에서 처리

        // ── kpRow1~4: data-k/data-s 버튼 리피트 ──
        document.querySelectorAll('.kp-block [data-k]').forEach(btn => {
            _bindRepeat(btn, () => _insertLang(btn));
        });

        // Del / Bs2 (리피트)
        _bindRepeat(document.getElementById('kbDel'),  (isFirst) => {
            if (isFirst) UIFeedback?.del();
            else UIFeedback?.delRepeat?.();
            if (_ctrl || _ctrlHeld) { Nav.deleteWordAfter?.(); Editor.focus?.(); return; }
            if (window._uiIsBlockMode?.()) {
                const view = window.Editor?.get?.();
                if (view) {
                    const pos = view.state.selection.main.head;
                    const ch  = view.state.doc.sliceString(pos, pos + 1);
                    if (ch === '\n') { Editor.focus?.(); return; }
                }
            }
            Editor.execCommand?.('delCharAfter');
            Editor.focus?.();
        });
        _bindRepeat(document.getElementById('kbBs2'),  (isFirst) => {
            if (isFirst) UIFeedback?.del();
            else UIFeedback?.delRepeat?.();
            if (_ctrl || _ctrlHeld) { Nav.deleteWordBefore?.(); Editor.focus?.(); return; }
            if (window._uiIsBlockMode?.()) {
                const view = window.Editor?.get?.();
                if (view) {
                    const pos = view.state.selection.main.head;
                    const ch  = view.state.doc.sliceString(pos - 1, pos);
                    if (ch === '\n') { Editor.focus?.(); return; }
                }
            }
            Editor.execCommand?.('delCharBefore');
            if (window._uiIsBlockMode?.()) {
                const bs = window.State?.getBS?.();
                if (bs && bs.ch > 0) {
                    const newCh = bs.ch - 1;
                    window.State?.setBS?.({ line: bs.line, ch: newCh });
                    const be = window.State?.getBE?.();
                    if (be) window.State?.setBE?.({ line: be.line, ch: newCh });
                    window.NavBlock?.syncColumnAfterInput?.(window.Editor?.get?.());
                }
            }
            Editor.focus?.();
        });

        // Tab / Space / Enter (리피트)
        _bindRepeat(document.getElementById('kbTab'), () => {
            if (_ctrl || _ctrlHeld) {
                const sh  = _shift || _shiftHeld;
                const alt = _alt   || _altHeld;
                if      (sh && alt) window.SlotManager?.slotLast?.();   // Shift+Alt+Ctrl+Tab → 마지막
                else if (alt)       window.SlotManager?.slotFirst?.();  // Alt+Ctrl+Tab       → 첫 슬롯
                else if (sh)        window.SlotManager?.slotPrev?.();   // Shift+Ctrl+Tab     → 이전
                else                window.SlotManager?.slotNext?.();   // Ctrl+Tab           → 다음
                if (_ctrl  && !_ctrlHeld)  _setCtrl(false);
                if (_shift && !_shiftHeld) _setShift(false);
                if (_alt   && !_altHeld)   _setAlt(false);
                return;
            }
            _insert('\t');
        });
        // kbSpace — kpRow5 바인딩에서 처리
        _bindRepeat(document.getElementById('kbEnter2'), () => {
            if (_ctrl || _ctrlHeld) {
                Nav.insertLineBelow();
                if (_ctrl && !_ctrlHeld) _setCtrl(false);
                return;
            }
            if (window._uiIsBlockMode?.()) { Editor.focus?.(); return; }
            _insert('\n');
        });

        // Home / End — 짧게: 줄 홈/끝, 길게: 문서 처음/끝
        function _bindHomeEnd(id, shortFn, longFn) {
            const el = document.getElementById(id);
            if (!el) return;
            let _t = null, _fired = false;
            el.addEventListener('touchstart', e => e.preventDefault(), { passive: false });
            el.addEventListener('pointerdown', e => {
                e.preventDefault();
                _fired = false;
                _t = setTimeout(() => {
                    _fired = true;
                    UIFeedback?.longPress();
                    longFn();
                }, 400);
            });
            el.addEventListener('pointerup', () => {
                clearTimeout(_t);
                if (!_fired) { UIFeedback?.special(); shortFn(); }
                _fired = false;
            });
            el.addEventListener('pointercancel', () => { clearTimeout(_t); _fired = false; });
        }
        _bindHomeEnd('kbHm',  () => {
            if (window._uiIsBlockMode?.()) { window.NavBlock?.columnHomeAll?.(); return; }
            const sh = _shift || _shiftHeld;
            const ct = _ctrl  || _ctrlHeld;
            if (sh && ct) { Nav.selectDocStart?.(); }
            else if (ct)  { Nav.jumpDocStart?.(); if (_ctrl && !_ctrlHeld) _setCtrl(false); }
            else if (sh)  { Nav.selectLineStart?.(); }
            else          { NavCursor.jumpH?.(); }
        }, () => NavCursor.jumpDocStart?.());
        _bindHomeEnd('kbEnd', () => {
            if (window._uiIsBlockMode?.()) { window.NavBlock?.columnEndAll?.(); return; }
            const sh = _shift || _shiftHeld;
            const ct = _ctrl  || _ctrlHeld;
            if (sh && ct) { Nav.selectDocEnd?.(); }
            else if (ct)  { Nav.jumpDocEnd?.(); if (_ctrl && !_ctrlHeld) _setCtrl(false); }
            else if (sh)  { Nav.selectLineEnd?.(); }
            else          { NavCursor.jumpE?.(); }
        }, () => NavCursor.jumpDocEnd?.());

        // ── kpShift: 홀드 or 단발 ──
        function _bindShift(id) {
            const el = document.getElementById(id);
            if (!el) return;
            let _holdTimer = null, _held = false, _active = false;
            el.addEventListener('touchstart', e => { e.preventDefault(); }, { passive: false });
            el.addEventListener('pointerdown', e => {
                e.preventDefault();
                _held = false;
                _active = true;
                _holdTimer = setTimeout(() => {
                    _held = true;
                    _shiftHeld = true;
                    UIFeedback?.longPress();
                    _setShift(true); // 홀드 시작
                }, 80);
            });
            el.addEventListener('pointerup', e => {
                if (!_active) return;
                _active = false;
                clearTimeout(_holdTimer);
                _holdTimer = null;
                if (_held) {
                    _held = false;
                    _shiftHeld = false;
                    _setShift(false); // 홀드 끝 → 해제
                } else {
                    UIFeedback?.toggle();
                    _setShift(!_shift); // 단발 토글
                }
            });
            el.addEventListener('pointercancel', () => {
                if (!_active) return;
                _active = false;
                clearTimeout(_holdTimer);
                _holdTimer = null;
                if (_held) {
                    _held = false;
                    _shiftHeld = false;
                    _setShift(false);
                } else {
                    // 단발 터치가 pointercancel로 끝난 경우도 토글 처리
                    UIFeedback?.toggle();
                    _setShift(!_shift);
                }
            });
        }
        _bindShift('kpShift');

        // ── kpCtl: 홀드 or 단발 (Shift와 동일 메커니즘) ──
        (function _bindCtrl() {
            const el = document.getElementById('kpCtl');
            if (!el) return;
            let _holdTimer = null, _held = false;
            el.addEventListener('touchstart', e => { e.preventDefault(); }, { passive: false });
            el.addEventListener('pointerdown', e => {
                e.preventDefault();
                _held = false;
                _holdTimer = setTimeout(() => {
                    _held = true;
                    _ctrlHeld = true;
                    UIFeedback?.longPress();
                    _setCtrl(true);
                }, 400);
            });
            el.addEventListener('pointerup', e => {
                clearTimeout(_holdTimer);
                if (_held) {
                    _ctrlHeld = false;
                    _setCtrl(false);
                } else {
                    UIFeedback?.toggle();
                    _setCtrl(!_ctrl);
                }
                _held = false;
            });
            el.addEventListener('pointercancel', () => {
                clearTimeout(_holdTimer);
                if (_held) { _ctrlHeld = false; _setCtrl(false); }
                _held = false;
            });
        })();

        // ── kpAlt: 홀드 or 단발 ──
        (function _bindAlt() {
            const el = document.getElementById('kpAlt');
            if (!el) return;
            let _holdTimer = null, _held = false;
            el.addEventListener('touchstart', e => { e.preventDefault(); }, { passive: false });
            el.addEventListener('pointerdown', e => {
                e.preventDefault();
                _held = false;
                _holdTimer = setTimeout(() => {
                    _held = true;
                    _altHeld = true;
                    UIFeedback?.longPress();
                    _setAlt(true);
                }, 400);
            });
            el.addEventListener('pointerup', e => {
                clearTimeout(_holdTimer);
                if (_held) {
                    _altHeld = false;
                    _setAlt(false);
                } else {
                    UIFeedback?.toggle();
                    _setAlt(!_alt);
                }
                _held = false;
            });
            el.addEventListener('pointercancel', () => {
                clearTimeout(_holdTimer);
                if (_held) { _altHeld = false; _setAlt(false); }
                _held = false;
            });
        })();

        // ── kpRow0 A/F 토글 ──
        _applyKp0Mode(_KP0_A);
        document.getElementById('kpRow0More')?.addEventListener('pointerdown', e => {
            e.preventDefault();
            UIFeedback?.toggle();
            if (_kpRow0Mode === 'a') { _kpRow0Mode = 'f'; _applyKp0Mode(_KP0_F); }
            else                     { _kpRow0Mode = 'a'; _applyKp0Mode(_cap || _shift ? _KP0_A : _KP0_A); }
            window.ActiveState?.setUI?.('kpRow0Mode', _kpRow0Mode);
            window.SlotManager?.saveUIState?.();
        });

        // Cap: 짧게=토글, 길게=대문자 고정
        const capBtn = document.getElementById('kbCap');
        if (capBtn) {
            let _t = null;
            capBtn.addEventListener('pointerdown', e => {
                e.preventDefault();
                _t = setTimeout(() => { _t = null; UIFeedback?.longPress(); _setCap(true); }, 400);
            });
            capBtn.addEventListener('pointerup', () => {
                if (_t) { clearTimeout(_t); _t = null; UIFeedback?.toggle(); _setCap(!_cap); }
            });
            capBtn.addEventListener('pointercancel', () => { if (_t) { clearTimeout(_t); _t = null; } });
        }
    }

    // 외부에서 Shift 강제 ON (S→보라 연계용), bs=블록 시작점
    function forceShiftOn(bs) {
        _shiftHeld = true;
        _setShift(true);
        // BS를 S모드 시작점으로 덮어쓰기
        if (bs) { window.State?.setBS?.(bs); window.State?.setBE?.(bs); }
    }

    // 외부에서 Shift 점등만 끄기 (보라→파란 전환용)
    function forceShiftOff() {
        _shift = false;
        _shiftHeld = false;
        document.getElementById('kpShift')?.classList.remove('cap-active');
        document.getElementById('kpShift2')?.classList.remove('cap-active');
    }

    return { init, show, hide, toggle, isOpen, isShift: () => _shift || _shiftHeld, isAlt: () => _alt || _altHeld, _forceShiftOn: forceShiftOn, _forceShiftOff: forceShiftOff, toggleCtrl: () => _setCtrl(!_ctrl), toggleAlt: () => _setAlt(!_alt), _forceCtrlOff: () => _setCtrl(false), _forceAltOff: () => _setAlt(false) };
})();

window.UIKeypad = UIKeypad;
