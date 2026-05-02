/* Path: usekit/tools/editor/js2/ui/ui_viewport.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * OS 키보드 상태 감지 + inputmode 제어 + 커서 가시성 보정
 *
 * 원칙:
 *   - editor 높이 = --editor-h CSS 변수 (ui.js 단일 관리)
 *   - maxAppH = window._maxAppH (ui.js가 관리, 읽기만)
 *   - KB 오픈: 빈라인+하단 위치일 때만 중앙 보정, 일반 라인은 CM6에 위임
 *   - KB 닫힘: 디바운스 200ms (삼성 브라우저 순간 오보 방지)
 *   - scrollGuard: CM6가 transactionFilter 외부에서 scrollTop을 직접 변경하는 버그 대응
 *     빈라인 Y = (lineNum-1)*lh 로 정확히 계산, passive:false로 CM6 연속 scroll 차단
 *     touchend 후 300ms / 롱클릭(touchend 없음) 폴백 1500ms 후 가드 해제
 *   - cursorActivity: 모든 커서 이동 경로에서 빈라인 도착 시 가드 활성
 * ─────────────────────────────────────────────────────────── */

const UIViewport = (function () {
    'use strict';

    const KB_THRESHOLD = 150;

    let _kbOpen       = false;
    let _allowKb      = false;
    let _initialized  = false;
    let _kbCloseTimer = null;
    let _kbOpenTimer  = null;   // 오픈 디바운스 — 삼성브라우저 순간 resize 오발 차단
    let _onKbClose    = null;

    function onKbClose(fn) { _onKbClose = fn; }

    // ── visualViewport 높이 ──────────────────────────────────
    function _currentAppH() {
        const vv = window.visualViewport;
        return Math.round(vv ? vv.height : window.innerHeight);
    }

    // ── editor 가시 영역 높이 — CSS 변수 단일 소스 ──────────
    function _editorVisibleH() {
        const val = parseFloat(
            getComputedStyle(document.documentElement).getPropertyValue('--editor-h')
        );
        if (val > 0) return val;
        const sc = _scroller();
        if (sc) { const h = sc.getBoundingClientRect().height; if (h > 0) return h; }
        return _currentAppH();
    }

    // ── KB 상태 감지 ─────────────────────────────────────────
    function _updateKbState() {
        const appH = _currentAppH();
        const maxH = window._maxAppH || appH;
        if (maxH === 0) return;

        const nowOpen = (maxH - appH) > KB_THRESHOLD;
        const wasOpen = _kbOpen;

        if (!wasOpen && nowOpen) {
            // 클로즈 타이머 취소
            clearTimeout(_kbCloseTimer);
            _kbCloseTimer = null;
            // 오픈 디바운스 60ms — 삼성브라우저 버튼 탭 시 순간적 resize 오발 차단
            if (_kbOpenTimer) return;
            _kbOpenTimer = setTimeout(() => {
                _kbOpenTimer = null;
                // 타이머 만료 시점에 실제로 열려있는지 재확인
                const appH2   = _currentAppH();
                const maxH2   = window._maxAppH || appH2;
                const stillOpen = (maxH2 - appH2) > KB_THRESHOLD;
                if (!stillOpen) return;
                _kbOpen = true;
                // OS키 오픈: 빈라인+하단 위치일 때만 중앙으로, 일반 라인은 CM6에 위임
                setTimeout(() => {
                    const view = Editor.get?.();
                    const sc   = _scroller();
                    if (!view || !sc) return;

                    const head = view.state.selection.main.head;
                    let isEmpty = false, lineNum = 1;
                    try {
                        const line = view.state.doc.lineAt(head);
                        isEmpty    = line.length === 0;
                        lineNum    = line.number;
                    } catch (e) {}

                    if (!isEmpty) { view.dispatch({ scrollIntoView: true }); return; }

                    const edH        = _editorVisibleH();
                    const lh         = _lineHeight();
                    const cursorY    = (lineNum - 1) * lh;
                    const nearBottom = cursorY >= (sc.scrollTop + edH) - lh * 2;

                    if (nearBottom) {
                        sc.scrollTop = Math.max(0, cursorY - edH / 2 + lh / 2);
                    } else {
                        view.dispatch({ scrollIntoView: true });
                    }
                }, 150);
            }, 60);

        } else if (wasOpen && !nowOpen) {
            // 오픈 타이머 취소
            clearTimeout(_kbOpenTimer);
            _kbOpenTimer = null;
            clearTimeout(_kbCloseTimer);
            _kbCloseTimer = setTimeout(() => {
                const stillOpen = ((window._maxAppH || 0) - _currentAppH()) > KB_THRESHOLD;
                if (!stillOpen) {
                    _kbOpen = false;
                    if (_allowKb) { _allowKb = false; _applyInputMode('none'); }
                    _onKbClose?.();
                }
                _kbCloseTimer = null;
            }, 200);
        }
    }

    // ── inputmode 제어 ───────────────────────────────────────
    function _applyInputMode(val) {
        const view = Editor.get?.();
        if (!view) return;
        if (val === 'none') view.contentDOM.setAttribute('inputmode', 'none');
        else                view.contentDOM.removeAttribute('inputmode');
    }

    function allowKeyboard() { _allowKb = true;  _applyInputMode('text'); }
    function blockKeyboard()  { _allowKb = false; _applyInputMode('none'); }
    function isKbOpen()       { return _kbOpen; }
    function isKbAllowed()    { return _allowKb; }

    // ── scrollDOM ────────────────────────────────────────────
    function _scroller() { return Editor.get?.()?.scrollDOM || null; }

    // ── 라인 높이 ────────────────────────────────────────────
    function _lineHeight() {
        const sc = _scroller();
        if (!sc) return 20;
        const line = sc.querySelector('.cm-line');
        return line ? (line.getBoundingClientRect().height || 20) : 20;
    }

    // ── 커서 Y 계산 (일반 라인, scrollDOM 내부 절대 Y) ───────
    function _getCursorY(view, sc, head) {
        const rect = sc.getBoundingClientRect();
        try {
            const coords = view.coordsAtPos(head, 1);
            if (coords) return coords.top - rect.top + sc.scrollTop;
        } catch (e) {}
        return null;
    }

    // ── 세로 커서 가시성 보정 ────────────────────────────────
    // emptyLineScrollGuard 이후 보조 호출용 (일반 라인 기준)
    function ensureCursorVisible() {
        try { if (window.State?.getModeS?.() && !_kbOpen) return; } catch (e) {}

        const view = Editor.get?.();
        if (!view) return;
        const sc = _scroller();
        if (!sc) return;

        const lh      = _lineHeight();
        const edH     = _editorVisibleH();
        const scrollT = sc.scrollTop;
        const head    = view.state.selection.main.head;
        const cursorY = _getCursorY(view, sc, head);
        if (cursorY === null) return;

        const cursorBot = cursorY + lh;
        if (cursorY >= scrollT && cursorBot <= scrollT + edH) return;

        sc.scrollTop = cursorY < scrollT
            ? Math.max(0, cursorY)
            : cursorBot - edH;
    }

    // ── nav/keypad 변화 후 높이 재계산 ──────────────────────
    function recalcEditorRect() {
        UI.recalcHeight();
        requestAnimationFrame(() => {
            const view = Editor.get?.();
            if (!view) return;
            if (_kbOpen) {
                // 빈라인이면 scrollIntoView 차단 — CM6 오동작 방지, 가드로 위치 유지
                let isEmpty = false;
                try { isEmpty = view.state.doc.lineAt(view.state.selection.main.head).length === 0; } catch (e) {}
                if (isEmpty) {
                    triggerScrollGuard();
                } else {
                    view.dispatch({ scrollIntoView: true });
                }
            } else {
                view.requestMeasure?.();
            }
        });
    }

    // ── editor 탭/클릭 → KB 허용 ────────────────────────────
    function _bindClickHandler() {
        const view = Editor.get?.();
        if (!view) return;
        const onTap = () => {
            if (window._sysKbMode) {
                if (window.State?.getLK?.()) return; // LK ON: OS 키보드 차단
                // LK OFF: OS 키보드 허용 → ui.js가 키패드 자동 숨김
                allowKeyboard();
                return;
            }
            if (window.SlotManager?.isSwitchingSlot?.()) return; // 슬롯 전환 중 KB 오발화 방지
            if (window._clipModalOpen) { blockKeyboard(); return; }
            try {
                if (window.State?.getLK?.())    { blockKeyboard(); return; }
                if (window.State?.getModeS?.()) { blockKeyboard(); return; }
            } catch (e) {}
            allowKeyboard();
        };
        view.contentDOM.addEventListener('mousedown',  onTap);
        view.contentDOM.addEventListener('touchstart', onTap, { passive: true });
    }

    // ── scrollGuard ──────────────────────────────────────────
    // CM6가 transactionFilter 외부에서 scrollDOM.scrollTop을 직접 변경하는 버그 대응.
    // 빈라인 Y = (lineNum-1)*lh 로 정확히 계산 (coordsAtPos 미사용).
    // passive:false로 CM6 연속 scroll을 완전 차단.
    let _guardActive   = false;
    let _savedTop      = 0;
    let _lastStableTop = 0;  // 가드 비활성 상태에서 마지막 정상 scrollTop
    let _guardTimer    = null;
    let _isTouching    = false;  // 터치 드래그 중 여부 — 드래그 scroll은 허용

    function _activateGuard(sc, scrollTop) {
        if (!_kbOpen) return;
        _savedTop    = scrollTop;
        _guardActive = true;
        clearTimeout(_guardTimer);
        _guardTimer  = setTimeout(() => { _guardActive = false; }, 1500);
    }

    // 외부(ui_events 등)에서 빈라인 가드 강제 활성용
    function triggerScrollGuard() {
        const sc = _scroller();
        if (sc) _activateGuard(sc, _lastStableTop);
    }

    function _bindScrollGuard(view, sc) {
        // 터치 드래그 추적 — 드래그 중 scroll은 사용자 의도이므로 허용
        // 롱프레스 OS 팝업 시 touchend/touchcancel이 안 오는 경우 대비:
        //   contextmenu 이벤트 + 500ms 폴백 타이머로 강제 리셋
        let _touchTimer = null;
        const _setTouching = (val) => {
            _isTouching = val;
            if (!val) { clearTimeout(_touchTimer); _touchTimer = null; }
        };
        sc.addEventListener('touchstart', () => {
            _setTouching(true);
            clearTimeout(_touchTimer);
            _touchTimer = setTimeout(() => { _setTouching(false); }, 2000);
        }, { passive: true });
        sc.addEventListener('touchend',    () => { _setTouching(false); }, { passive: true });
        sc.addEventListener('touchcancel', () => { _setTouching(false); }, { passive: true });

        // Keyboard-open scroll chain blocker.
        // When the editor has no internal scroll range, Android/Samsung can pan the
        // visual viewport even though html/body are fixed. Prevent only boundary
        // vertical moves, so normal CM6 internal scrolling still works.
        let _panLastX = 0;
        let _panLastY = 0;
        sc.addEventListener('touchstart', (e) => {
            const t = e.touches && e.touches[0];
            if (!t) return;
            _panLastX = t.clientX;
            _panLastY = t.clientY;
        }, { passive: true });

        sc.addEventListener('touchmove', (e) => {
            if (!_kbOpen) return;
            const t = e.touches && e.touches[0];
            if (!t) return;

            const dx = t.clientX - _panLastX;
            const dy = t.clientY - _panLastY;
            _panLastX = t.clientX;
            _panLastY = t.clientY;

            // Let horizontal pan and tiny jitter pass through.
            if (Math.abs(dy) < 2 || Math.abs(dx) > Math.abs(dy)) return;

            const maxTop = Math.max(0, sc.scrollHeight - sc.clientHeight);
            const top    = sc.scrollTop;
            const noRange = maxTop <= 1;
            const atTopPullingDown = dy > 0 && top <= 0;
            const atBottomPushingUp = dy < 0 && top >= maxTop - 1;

            if (noRange || atTopPullingDown || atBottomPushingUp) {
                e.preventDefault();
                e.stopPropagation();
                if (noRange && top !== 0) sc.scrollTop = 0;
            }
        }, { passive: false });
        // OS 팝업(롱프레스) → contextmenu 발생 시 즉시 리셋
        sc.addEventListener('contextmenu', () => { _setTouching(false); }, { passive: true });
        view.contentDOM.addEventListener('contextmenu', () => { _setTouching(false); }, { passive: true });

        // touchend/touchcancel 후 300ms 유지 후 가드 해제
        const release = () => {
            if (!_guardActive) return;
            clearTimeout(_guardTimer);
            _guardTimer = setTimeout(() => { _guardActive = false; }, 300);
        };
        view.contentDOM.addEventListener('touchend',    release, { passive: true });
        view.contentDOM.addEventListener('touchcancel', release, { passive: true });

        // 빈라인 탭/롱클릭 → 가드 ON
        view.contentDOM.addEventListener('touchstart', (e) => {
            if (!_kbOpen) return;
            const t = e.touches[0];
            const pos = view.posAtCoords({ x: t.clientX, y: t.clientY });
            if (pos == null) return;
            let isEmpty = false;
            try { isEmpty = view.state.doc.lineAt(pos).length === 0; } catch (e) {}
            if (!isEmpty) return;
            _activateGuard(sc, sc.scrollTop);
        }, { passive: true });

        // 가드 활성 중 CM6 settle scroll 차단 (터치 드래그 중에는 통과)
        sc.addEventListener('scroll', () => {
            if (!_guardActive) {
                _lastStableTop = sc.scrollTop;
                return;
            }
            // 사용자가 직접 드래그 중이면 차단하지 않음 — savedTop만 추적
            if (_isTouching) {
                _savedTop      = sc.scrollTop;
                _lastStableTop = sc.scrollTop;
                return;
            }
            if (!_kbOpen) { _guardActive = false; return; }

            const edH  = _editorVisibleH();
            const lh   = _lineHeight();
            const head = view.state.selection.main.head;

            let lineNum = 1;
            try { lineNum = view.state.doc.lineAt(head).number; } catch (e) {}

            const cursorY   = (lineNum - 1) * lh;
            const cursorBot = cursorY + lh;
            const inView    = cursorY >= _savedTop && cursorBot <= _savedTop + edH;

            if (inView) {
                sc.scrollTop = _savedTop;
                requestAnimationFrame(() => Editor.get?.()?.requestMeasure?.());
            } else {
                const newTop = cursorY < _savedTop
                    ? Math.max(0, cursorY)
                    : Math.max(0, cursorBot - edH + lh * 0.5);
                sc.scrollTop = newTop;
                _savedTop    = newTop;
            }
        }, { passive: false });
    }

    // ── 초기화 ───────────────────────────────────────────────
    function init() {
        if (_initialized) return;
        _initialized = true;

        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', _updateKbState);
        }
        window.addEventListener('resize', _updateKbState);

        requestAnimationFrame(() => {
            _bindClickHandler();
            _applyInputMode('none');

            const view = Editor.get?.();
            const sc   = _scroller();
            if (!view || !sc) return;

            _bindScrollGuard(view, sc);

            // 모든 커서 이동 경로에서 빈라인 도착 시 가드 활성
            // (setCursor, setSelectionDirected, Esc, Tab, Hm, End, ⌫ 등 전부 커버)
            // _lastStableTop 기준: CM6가 이미 scroll을 발생시킨 후여도 올바른 위치로 복원
            Editor.on('cursorActivity', () => {
                if (!_kbOpen) return;
                let isEmpty = false;
                try {
                    const head = view.state.selection.main.head;
                    isEmpty = view.state.doc.lineAt(head).length === 0;
                } catch (e) {}
                if (isEmpty) _activateGuard(sc, _lastStableTop);
            });
        });
    }

    return {
        init,
        allowKeyboard, blockKeyboard,
        isKbOpen, isKbAllowed,
        onKbClose,
        ensureCursorVisible,
        recalcEditorRect,
        triggerScrollGuard,
    };
})();

window.UIViewport = UIViewport;
