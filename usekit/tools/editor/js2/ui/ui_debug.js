/* Path: usekit/tools/editor/js2/ui/ui_debug.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 실시간 높이/상태 디버그 오버레이
 *
 * 표시 항목:
 *   - vv.h / win.h / maxH / kbH (키보드 높이)
 *   - --app-height / --editor-h / --vv-offset-top
 *   - header / nav / footer offsetHeight
 *   - scrollDOM.h (cm-scroller 실측)
 *   - uiMode / kbOpen / kbAllowed / sysKbMode
 *   - nav 열 가시 상태 (1열/2열/3열/kp)
 *
 * 오버레이는 화면 우상단 반투명 패널
 * 탭하면 최소화/확장 토글
 * ─────────────────────────────────────────────────────────── */

const UIDebug = (function () {
    'use strict';

    let _el      = null;   // 오버레이 div
    let _mini    = false;  // 최소화 상태
    let _raf     = null;
    let _lastStr = '';

    // ── 로그 (콘솔) ─────────────────────────────────────────
    function log(tag, msg) {
        const t  = new Date();
        const ts = `${t.getMinutes().toString().padStart(2,'0')}:${t.getSeconds().toString().padStart(2,'0')}.${t.getMilliseconds().toString().padStart(3,'0')}`;
        console.log(`[DBG ${ts}] ${tag}: ${msg}`);
    }

    // ── 데이터 수집 ──────────────────────────────────────────
    function _collect() {
        const vv      = window.visualViewport;
        const root    = document.documentElement;
        const cs      = getComputedStyle(root);
        const sc      = window.Editor?.get?.()?.scrollDOM;

        const vvH     = vv  ? Math.round(vv.height)    : '–';
        const vvPan   = vv  ? Math.round(vv.offsetTop) : '–';
        const winH    = Math.round(window.innerHeight);

        const appH    = cs.getPropertyValue('--app-height').trim()    || '–';
        const edH     = cs.getPropertyValue('--editor-h').trim()      || '–';
        const offsetY = cs.getPropertyValue('--vv-offset-top').trim() || '–';

        const hdrEl   = document.querySelector('.header-section');
        const navEl   = document.querySelector('.action-nav-wrapper');
        const ftrEl   = document.querySelector('.footer-section');
        const edEl    = document.querySelector('.editor-section');

        const hdrH    = hdrEl ? hdrEl.offsetHeight : '–';
        const navH    = navEl ? (navEl.offsetParent !== null ? navEl.offsetHeight : '(hidden)') : '–';
        const ftrH    = ftrEl ? ftrEl.offsetHeight : '–';
        const edElH   = edEl  ? Math.round(edEl.getBoundingClientRect().height) : '–';
        const scH     = sc    ? Math.round(sc.getBoundingClientRect().height)   : '–';

        // uiMode — window._uiMode 또는 ActiveState
        const uiMode  = window.ActiveState?.getUI?.('uiMode') || '–';
        const kbOpen  = window.UIViewport?.isKbOpen?.()  ? 'Y' : 'N';
        const kbAllow = window.UIViewport?.isKbAllowed?.() ? 'Y' : 'N';
        const sysKb   = window._sysKbMode ? 'Y' : 'N';

        // nav 열 가시 상태
        const isVisible = id => {
            const el = typeof id === 'string' ? document.getElementById(id) : id;
            return el && !el.classList.contains('is-hidden') ? '●' : '○';
        };
        const navHidden  = document.querySelector('.editor-app')?.classList.contains('nav-hidden') ? 'Y' : 'N';
        const r1 = isVisible(document.querySelector('.block-cursor'));
        const r2 = isVisible(document.querySelector('.block-numbers'));
        const r3 = isVisible('navThirdRow');
        const kp = isVisible('kpRow5');  // 6열 대표

        const maxH = window._maxAppH || winH;

        return {
            vvH, vvPan, winH, maxH,
            kbHidden: (maxH - vvH) > 0 ? `${maxH - vvH}px` : '0',
            appH, edH, offsetY,
            hdrH, navH, ftrH, edElH, scH,
            uiMode, kbOpen, kbAllow, sysKb,
            navHidden, r1, r2, r3, kp,
        };
    }

    // ── 렌더 ─────────────────────────────────────────────────
    let _body  = null;
    let _label = null;

    function _render() {
        if (!_el || !_body) return;
        const d = _collect();

        if (_mini) {
            const str = `${d.edH} | ui:${d.uiMode} kb:${d.kbOpen}`;
            if (str !== _lastStr) { _body.textContent = str; _lastStr = str; }
            return;
        }

        const str = [
            `vv:${d.vvH}  win:${d.winH}  kb↑:${d.kbHidden}`,
            `--app-h:${d.appH}  --ed-h:${d.edH}`,
            `--offset:${d.offsetY}  pan:${d.vvPan}`,
            `hdr:${d.hdrH}  nav:${d.navH}  ftr:${d.ftrH}`,
            `editor.rect:${d.edElH}  scroller:${d.scH}`,
            `ui:${d.uiMode}  navHide:${d.navHidden}`,
            `kbOpen:${d.kbOpen}  allow:${d.kbAllow}  sys:${d.sysKb}`,
            `R1:${d.r1} R2:${d.r2} R3:${d.r3} KP:${d.kp}`,
        ].join('\n');

        if (str !== _lastStr) {
            _body.textContent = str;
            _lastStr = str;
            const edHpx = parseFloat(d.edH);
            const scHpx = typeof d.scH === 'number' ? d.scH : parseFloat(d.scH);
            _el.style.borderColor = (!isNaN(edHpx) && !isNaN(scHpx) && Math.abs(edHpx - scHpx) > 10)
                ? '#f87171'
                : '#4ade80';
        }
    }

    function _loop() {
        _render();
        _raf = requestAnimationFrame(_loop);
    }

    // ── 오버레이 생성 ────────────────────────────────────────
    function _createOverlay() {
        // 컨테이너
        _el = document.createElement('div');
        Object.assign(_el.style, {
            position:      'fixed',
            top:           '6px',
            right:         '6px',
            zIndex:        '99999',
            background:    'rgba(0,0,0,0.78)',
            color:         '#e2e8f0',
            fontSize:      '10px',
            fontFamily:    'monospace',
            lineHeight:    '1.55',
            whiteSpace:    'pre',
            borderRadius:  '6px',
            border:        '1.5px solid #4ade80',
            minWidth:      '190px',
            maxWidth:      '240px',
            pointerEvents: 'auto',
            touchAction:   'none',
        });

        // 헤더 바 (최소화 탭 + 복사 버튼)
        const bar = document.createElement('div');
        Object.assign(bar.style, {
            display:        'flex',
            justifyContent: 'space-between',
            alignItems:     'center',
            padding:        '4px 8px 2px',
            borderBottom:   '1px solid rgba(255,255,255,0.15)',
            cursor:         'pointer',
            userSelect:     'none',
        });

        const label = document.createElement('span');
        label.textContent = '▼ DBG';
        label.style.opacity = '0.6';
        label.style.fontSize = '9px';

        const copyBtn = document.createElement('button');
        copyBtn.textContent = '📋 copy';
        Object.assign(copyBtn.style, {
            background:   'rgba(255,255,255,0.12)',
            border:       '1px solid rgba(255,255,255,0.25)',
            borderRadius: '3px',
            color:        '#e2e8f0',
            fontSize:     '9px',
            padding:      '1px 5px',
            cursor:       'pointer',
            userSelect:   'none',
        });

        copyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const text = _lastStr;
            if (navigator.clipboard?.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    copyBtn.textContent = '✓ done';
                    setTimeout(() => { copyBtn.textContent = '📋 copy'; }, 1200);
                }).catch(() => _fallbackCopy(text, copyBtn));
            } else {
                _fallbackCopy(text, copyBtn);
            }
        });

        bar.appendChild(label);
        bar.appendChild(copyBtn);
        bar.addEventListener('click', () => {
            _mini = !_mini;
            label.textContent = _mini ? '▶ DBG' : '▼ DBG';
            _lastStr = '';
            _body.style.display = _mini ? 'none' : 'block';
        });

        // 본문 텍스트 영역
        const body = document.createElement('div');
        Object.assign(body.style, {
            padding:    '4px 8px 6px',
            whiteSpace: 'pre',
        });

        _el.appendChild(bar);
        _el.appendChild(body);
        _el._body  = body;
        _el._label = label;
        _body  = body;
        _label = label;

        document.body.appendChild(_el);
    }

    function _fallbackCopy(text, btn) {
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;opacity:0;top:-9999px;left:-9999px;';
            document.body.appendChild(ta);
            ta.focus();
            ta.setSelectionRange(0, ta.value.length);
            document.execCommand('copy');
            document.body.removeChild(ta);
            btn.textContent = '✓ done';
            setTimeout(() => { btn.textContent = '📋 copy'; }, 1200);
        } catch(e) {
            btn.textContent = '✗ fail';
            setTimeout(() => { btn.textContent = '📋 copy'; }, 1200);
        }
    }
    // ── visualViewport 이벤트 콘솔 로그 ─────────────────────
    function _bindVPLog() {
        const vv = window.visualViewport;
        if (!vv) return;
        vv.addEventListener('resize', () => {
            log('VP.resize', `h=${Math.round(vv.height)} pan=${Math.round(vv.offsetTop)}`);
        });
        vv.addEventListener('scroll', () => {
            log('VP.pan', `pageTop=${Math.round(vv.pageTop)} offsetTop=${Math.round(vv.offsetTop)}`);
        });
        window.addEventListener('scroll', () => {
            log('WIN.scroll!!', `scrollY=${Math.round(window.scrollY)}`);
        }, { passive: true });
    }

    // ── 초기화 ───────────────────────────────────────────────
    function init() {
        _createOverlay();
        _bindVPLog();
        _loop();

        // 초기 스냅샷 로그
        const cs  = getComputedStyle(document.documentElement);
        log('INIT', `--app-height=${cs.getPropertyValue('--app-height').trim()}`);
        log('INIT', `--editor-h=${cs.getPropertyValue('--editor-h').trim()}`);
        log('INIT', `vv.h=${window.visualViewport ? Math.round(window.visualViewport.height) : '?'}`);
    }

    return { init, log };
})();

window.UIDebug = UIDebug;
