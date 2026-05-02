/* Path: usekit/tools/editor/js2/ui/ui.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 앱 초기화 + visualViewport 높이 관리
 *
 * 원칙:
 *   - --app-height : visualViewport.height (usekit-wrapper 크기)
 *   - --editor-h   : appH - headerH - navH - footerH (editor-section 고정 높이)
 *   - --vv-offset-top : pan 보정 (usekit-wrapper transform 용)
 *   - editor-section 높이는 CSS height: var(--editor-h) 로만 결정
 *     → JS에서 editorEl.style.height 직접 설정 금지
 *   - pan 버스트 RAF: CM 포커스 중 panOffset 진동 억제용
 * ─────────────────────────────────────────────────────────── */

const UI = (function () {
    'use strict';

    let _maxAppH    = 0;
    let _lastPan    = 0;
    let _stillCount = 0;
    let _rafLock    = null;
    let _lastKbOpen = false;

    let _elHeader  = null;
    let _elNav     = null;
    let _elFooter  = null;
    let _elWrapper = null;

    const _H_HEADER_FB = 52;
    const _H_FOOTER_FB = 32;

    function _readVV() {
        const vv = window.visualViewport;
        if (vv) return { appH: Math.round(vv.height), pan: Math.round(vv.offsetTop) };
        return { appH: window.innerHeight, pan: 0 };
    }

    function _applyVars(appH, offsetY) {
        const root = document.documentElement.style;
        root.setProperty('--app-height',    `${appH}px`);
        root.setProperty('--vv-offset-top', `${offsetY}px`);

        const headerH = _elHeader ? _elHeader.offsetHeight : _H_HEADER_FB;
        const navH    = (_elNav && _elNav.offsetParent !== null) ? _elNav.offsetHeight : 0;
        const footerH = _elFooter ? _elFooter.offsetHeight : _H_FOOTER_FB;
        const editorH = Math.max(0, appH - headerH - navH - footerH);
        root.setProperty('--editor-h', `${editorH}px`);
    }

    function _applyWrapper(appH, offsetY) {
        if (!_elWrapper) return;
        _elWrapper.style.height    = `${appH}px`;
        _elWrapper.style.transform = offsetY
            ? `translate3d(0, ${-offsetY}px, 0)`
            : '';
    }

    function _panBurst() {
        if (window._sysKbMode) { _rafLock = null; return; }
        _applyHeight();
        _rafLock = requestAnimationFrame(_panBurst);
    }

    function _applyHeight() {
        const { appH, pan } = _readVV();
        const innerH = Math.round(window.innerHeight);

        // maxAppH = vv.height와 innerHeight 중 큰 값
        // → 브라우저 주소창/네비바 show/hide로 vv가 fluctuate해도 안정적인 최대값 유지
        const candidateH = Math.max(appH, innerH);
        if (_maxAppH === 0 && candidateH > 0) _maxAppH = candidateH;
        if (candidateH > _maxAppH)            _maxAppH = candidateH;

        const kbOpen = (_maxAppH - appH) > 150;
        window._maxAppH = _maxAppH;   // UIViewport와 공유

        // kbOpen=false 상태에서는 매 tick마다 maxAppH를 현재값으로 내림
        // → OS키 닫힌 후 네비바 복귀로 innerH가 줄어들어도 즉시 재기준
        // → 상태변화(nav 토글 등) 후 OS키 내려도 kb↑:0 보장
        if (!kbOpen) {
            _maxAppH = candidateH;
            window._maxAppH = _maxAppH;
        }

        if (kbOpen !== _lastKbOpen) {
            _lastKbOpen = kbOpen;
            window.UIStats?.updateKUButton?.(kbOpen);
            if (kbOpen) {
                // OS 키보드 올라감 — 현재 active 패널 기억
                const activeP = document.querySelector('.swipe-panel.active');
                if (activeP) {
                    window._kbPrevPanel = activeP.classList.contains('panel-buttons') ? 'menu'
                                        : activeP.classList.contains('panel-navigation') ? 'nav'
                                        : 'quick';
                }
                // 인풋도구가 보이고 있으면 숨김
                if (window.UIKeypad?.isOpen?.()) {
                    window.UIKeypad?.hide?.();
                    const np = document.querySelector('.swipe-panel.panel-navigation');
                    if (np) np.classList.remove('active');
                    UI.recalcHeight();
                }
            }
            if (!kbOpen && window._kbPrevPanel) {
                // OS 키보드 내려감 — 이전 패널 복원
                const prev = window._kbPrevPanel;
                window._kbPrevPanel = null;
                if (prev === 'nav') {
                    // 인풋도구였으면 키패드까지 복원
                    document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
                    const np = document.querySelector('.swipe-panel.panel-navigation');
                    if (np) np.classList.add('active');
                    window.UIKeypad?.show?.();
                }
                // quick, menu는 숨긴 적 없으니 복원 불필요
            }
        }

        const diff = Math.abs(pan - _lastPan);
        if (diff <= 2) {
            _stillCount++;
            if (_stillCount >= 3 && _rafLock) {
                cancelAnimationFrame(_rafLock);
                _rafLock = null;
            }
        } else {
            _lastPan = pan;
            _stillCount = 0;
            if (!_rafLock) _panBurst();
        }

        const modalOpen = !!document.querySelector('.modal-overlay[aria-hidden="false"]');
        const offsetY   = (!window._sysKbMode && !modalOpen && kbOpen) ? pan : 0;

        _applyVars(appH, offsetY);
        _applyWrapper(appH, offsetY);
    }

    function recalcHeight() { _applyHeight(); window.NavFocus?.resyncPos?.(); }

    async function init() {
        _elHeader  = document.querySelector('.header-section');
        _elNav     = document.querySelector('.action-nav-wrapper');
        _elFooter  = document.querySelector('.footer-section');
        _elWrapper = document.querySelector('.usekit-wrapper');

        const app = document.querySelector('.editor-app');
        if (app) app.classList.add('no-transition');

        _applyHeight();

        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', _applyHeight);
            window.visualViewport.addEventListener('scroll', _applyHeight);
        }
        window.addEventListener('resize', _applyHeight);
        window.addEventListener('orientationchange', _applyHeight);

        if (window.SetupPolicy) SetupPolicy.init();

        const host = document.getElementById('editor-host');
        if (!host) { console.error('[UI] #editor-host not found'); return; }
        Editor.init(host);
        Editor.loadAutocomplete();  // USEKIT u.xxx 자동완성 비동기 로드

        State.reset();
        if (window.ActiveState) ActiveState.reset();

        UIStats.init();
        if (window.UISettings) UISettings.init();
        if (window.UIFooter)   UIFooter.init();
        if (window.UIViewport) UIViewport.init();
        if (window.UIEvents)   UIEvents.init();
        if (window.UIKeypad)   UIKeypad.init();

        if (window.NavNum)    NavNum.init();
        if (window.NavFind)   NavFind.init();
        if (window.NavCursor) NavCursor.init();

        if (window.SlotStorage?.initIDB) await SlotStorage.initIDB();
        SlotManager.init();

        UIStats.updateStatsNow();
        UIStats.updateUndoRedo();
        if (window.UIStats?._syncModeMBtn) UIStats._syncModeMBtn();

        Editor.on('focus', () => { if (!_rafLock) _panBurst(); });
        Editor.on('blur',  () => { if (_rafLock) { cancelAnimationFrame(_rafLock); _rafLock = null; } });

        requestAnimationFrame(() => requestAnimationFrame(() => {
            if (app) app.classList.remove('no-transition');
        }));

        // if (window.UIDebug) UIDebug.init();
    }

    function updateStats()       { UIStats.updateStats(); }
    function updateFooter()      { if (window.UIFooter) UIFooter.update(); }
    function updateUndoRedo()    { UIStats.updateUndoRedo(); }
    function notifyCopied()      { UIStats.notifyCopied(); }
    function notifyClipCleared() { UIStats.notifyClipCleared(); }

    let _toastTimer = null;
    function showToast(msg, duration = 1500, position = 'bottom') {
        let el = document.getElementById('toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'toast'; el.className = 'toast';
            document.body.appendChild(el);
        }
        el.textContent = msg;
        el.classList.toggle('toast-top', position === 'top');
        el.classList.add('show');
        clearTimeout(_toastTimer);
        _toastTimer = setTimeout(() => el.classList.remove('show'), duration);
    }

    return {
        init, recalcHeight,
        updateStats, updateFooter, updateUndoRedo,
        notifyCopied, notifyClipCleared,
        showToast,
    };
})();

window.UI = UI;
document.addEventListener('DOMContentLoaded', () => UI.init());
