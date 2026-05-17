/* Path: usekit/tools/editor/js2/ui/ui_events.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 버튼 바인딩 — 모든 nav/edit/file 버튼 이벤트
 * K.M.S. Lock 임시 막음
 * ─────────────────────────────────────────────────────────── */

// ── NavFocus: 가상 포커스 스크롤 모드 (inline) ───────────────
const NavFocus = (function () {
    'use strict';

    function scrollV(lines) { Editor.scrollByLines?.(lines, _fixH); }
    function scrollH(chars)  { Editor.scrollByChars?.(chars); }

    function _updateOverlayPos() {
        const el = document.getElementById('focusOverlay');
        if (!el) return;
        const sc = document.querySelector('.cm-scroller');
        if (!sc) return;
        const r = sc.getBoundingClientRect();
        const centerY = r.top + r.height * 0.5;
        const pct = (centerY / window.innerHeight * 100).toFixed(2);
        const hLine = el.querySelector('.focus-h');
        const vLine = el.querySelector('.focus-v');
        if (hLine) hLine.style.top = pct + '%';
        if (vLine) vLine.style.top = 'calc(' + pct + '% - 12px)';
    }

    function showOverlay() {
        let el = document.getElementById('focusOverlay');
        if (!el) {
            el = document.createElement('div');
            el.id = 'focusOverlay';
            el.innerHTML = '<span class="focus-h"></span><span class="focus-v"></span>';
            document.body.appendChild(el);
        }
        el.classList.add('active');
        _updateOverlayPos();
    }

    function hideOverlay() {
        const el = document.getElementById('focusOverlay');
        if (el) el.classList.remove('active');
    }

    let _fixH = true;  // true=x고정(짧은/파란), false=x보정(긴/amber)

    function toggle(fixH) {
        const wasOn = State.getModeF();
        if (fixH === false) {
            // 길게: 어디서든 x보정 ON (꺼져있으면 켜고, 켜져있으면 전환)
            _fixH = false;
            if (!wasOn) State.toggleModeF();
            State.getModeF() ? showOverlay() : hideOverlay();
            _updateBtn(State.getModeF());
            return;
        }
        // 짧게(fixH=true): 토글
        _fixH = true;
        State.toggleModeF();
        const on = State.getModeF();
        on ? showOverlay() : hideOverlay();
        _updateBtn(on);
    }
    function _updateBtn(on) {
        const btn = document.getElementById('btnFooterFocus');
        if (!btn) return;
        btn.classList.remove('active');
        btn.style.background = btn.style.borderColor = btn.style.color = '';
        if (!on) return;
        if (_fixH) {
            // 짧은: 파란색 (x고정)
            btn.classList.add('active');
        } else {
            // 긴: purple (x보정)
            const s = getComputedStyle(document.documentElement);
            btn.style.background  = s.getPropertyValue('--ac-purple-bg').trim();
            btn.style.borderColor = s.getPropertyValue('--ac-purple-bd').trim();
            btn.style.color       = s.getPropertyValue('--ac-purple').trim();
        }
    }

    function isOn() { return State.getModeF(); }
    function _resyncColor() { _updateBtn(State.getModeF()); }

    return { toggle, isOn, scrollV, scrollH, showOverlay, hideOverlay, _resyncColor, resyncPos: _updateOverlayPos };
})();
window.NavFocus = NavFocus;

const UIEvents = (function () {
    'use strict';

    function _escHtml(s) {
        return String(s)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    function _escHtmlPretty(s) {
        return _escHtml(s)
            .replace(/\\n/g,'\n')
            .replace(/\n/g,'<br>');
    }

    // ── stdout pretty-format (Python list/dict 출력 정리) ──
    function _fmtStdout(raw) {
        if (!raw || !raw.trim()) return raw;
        return raw.split('\n').map(line => {
            const t = line.trim();
            if (!t) return line;
            // JSON 시도
            if ((t[0] === '[' || t[0] === '{') && (t[t.length-1] === ']' || t[t.length-1] === '}')) {
                try { return JSON.stringify(JSON.parse(t), null, 2); } catch(_) {}
            }
            // Python repr: 길면 포맷팅
            if (t.length > 80 && /^[\[({]/.test(t)) return _fmtPythonRepr(t);
            return line;
        }).join('\n');
    }
    function _fmtPythonRepr(s) {
        let out = '', indent = 0, inStr = false, strCh = '';
        for (let i = 0; i < s.length; i++) {
            const c = s[i];
            if (inStr) {
                out += c;
                if (c === '\\') { out += s[++i] || ''; continue; }
                if (c === strCh) inStr = false;
                continue;
            }
            if (c === "'" || c === '"') { inStr = true; strCh = c; out += c; continue; }
            if (c === '{' || c === '[' || c === '(') {
                indent++;
                out += c + '\n' + '  '.repeat(indent);
            } else if (c === '}' || c === ']' || c === ')') {
                indent = Math.max(0, indent - 1);
                out += '\n' + '  '.repeat(indent) + c;
            } else if (c === ',') {
                out += ',\n' + '  '.repeat(indent);
                if (s[i+1] === ' ') i++;
            } else {
                out += c;
            }
        }
        return out;
    }

    // 기본: touchend + mouseup (300ms 딜레이 없음)
    function _bind(id, fn) {
        const el = document.getElementById(id);
        if (!el) return;
        let _touched = false;
        const run = (e) => {
            e.preventDefault();
            try { fn(); } catch(e) { console.warn('[UIEvents]', id, e); }
        };
        el.addEventListener('touchstart', (e) => { e.preventDefault(); _touched = true; }, { passive: false });
        el.addEventListener('touchend', run, { passive: false });
        el.addEventListener('mouseup', (e) => { if (_touched) { _touched = false; return; } run(e); });
    }

    // 롱프레스 지원
    function _bindLong(id, onSingle, onLong) {
        const el = document.getElementById(id);
        if (!el) return;
        let _timer = null, _fired = false, _locked = false;

        const start = (e) => {
            e.preventDefault();
            _fired = false;
            _timer = setTimeout(() => {
                _fired = true;
                if (onLong) try { onLong(); } catch(e) {}
            }, 400);
        };
        const end = (e) => {
            e.preventDefault();
            clearTimeout(_timer);
            if (!_fired && !_locked) {
                _locked = true;
                setTimeout(() => { _locked = false; }, 280);
                try { onSingle(); } catch(e) { console.warn('[UIEvents]', id, e); }
            }
        };
        const cancel = () => { clearTimeout(_timer); };

        el.addEventListener('touchstart', start, { passive: false });
        el.addEventListener('touchend',   end,   { passive: false });
        el.addEventListener('touchcancel', cancel);
        el.addEventListener('mousedown',  start);
        el.addEventListener('mouseup',    end);
        el.addEventListener('mouseleave', cancel);
    }

    // 더블탭 + 롱프레스
    function _bindDoubleLong(id, onSingle, onDouble, onLong) {
        const el = document.getElementById(id);
        if (!el) return;
        let _timer = null, _longTimer = null, _tapCount = 0, _longFired = false;

        const start = (e) => {
            e.preventDefault();
            _longFired = false;
            _longTimer = setTimeout(() => {
                _longFired = true;
                clearTimeout(_timer);
                _tapCount = 0;
                try { onLong(); } catch(e) {}
            }, 500);
        };
        const end = (e) => {
            e.preventDefault();
            clearTimeout(_longTimer);
            if (_longFired) return;
            _tapCount++;
            if (_tapCount === 1) {
                _timer = setTimeout(() => {
                    _tapCount = 0;
                    try { onSingle(); } catch(e) {}
                }, 120);
            } else {
                clearTimeout(_timer);
                _tapCount = 0;
                try { onDouble(); } catch(e) {}
            }
        };
        const cancel = () => { clearTimeout(_longTimer); clearTimeout(_timer); _tapCount = 0; };

        el.addEventListener('touchstart', start, { passive: false });
        el.addEventListener('touchend',   end,   { passive: false });
        el.addEventListener('touchcancel', cancel);
        el.addEventListener('mousedown',  start);
        el.addEventListener('mouseup',    end);
        el.addEventListener('mouseleave', cancel);
    }

    // 누르는 동안 반복
    // CHECK IME ghost — 방향키 이동 후 snap 기준점 재계산

    function _bindRepeat(id, fn, delay = 80, initialDelay = 350, options = {}) {
        const el = document.getElementById(id);
        if (!el) return;
        let _timer = null, _interval = null;
        let _active = false;
        let _repeatEnabled = false;
        let _firedOnce = false;

        const shouldRepeat = typeof options.shouldRepeat === 'function'
            ? options.shouldRepeat
            : () => true;

        const run = () => {
            try { fn(!_firedOnce); } catch(_) {}
            _firedOnce = true;
        };

        const start = (e) => {
            e.preventDefault();
            if (!window.UIViewport?.isKbOpen?.()) window.UIViewport?.blockKeyboard?.();
            if (_active) return;
            _active = true;
            _firedOnce = false;
            _repeatEnabled = !!shouldRepeat();

            if (_repeatEnabled) {
                run();
                _timer = setTimeout(() => {
                    _interval = setInterval(() => {
                        if (!_active) { clearInterval(_interval); _interval = null; return; }
                        run();
                    }, delay);
                }, initialDelay);
            }
        };

        const stop = (e) => {
            if (e?.preventDefault) e.preventDefault();
            const shouldRunSingle = _active && !_repeatEnabled && !_firedOnce;
            _active = false;
            clearTimeout(_timer);
            clearInterval(_interval);
            _timer = _interval = null;
            if (shouldRunSingle) run();
        };

        el.addEventListener('touchstart',  start, { passive: false });
        el.addEventListener('touchend',    stop,  { passive: false });
        el.addEventListener('touchcancel', stop,  { passive: true });

        // pointer 이벤트 — 터치 슬립/멀티터치 누락 방지
        el.addEventListener('pointerup',     stop, { passive: true });
        el.addEventListener('pointercancel', stop, { passive: true });
        el.addEventListener('pointerleave',  stop, { passive: true });

        el.addEventListener('mousedown',  start);
        el.addEventListener('mouseup',    stop);
        el.addEventListener('mouseleave', stop);
    }
    function init() {
        // slotContainer 인라인 스타일 초기화 (이전 세션 잔여 방지)
        const _sc = document.getElementById('slotContainer');
        const _ml = document.getElementById('metaLoc');
        if (_sc) _sc.style.display = 'flex';
        if (_ml) _ml.style.display = 'none';
        _showingSlots = true;
        _bindNavButtons();
        _bindEditButtons();
        _bindFileButtons();
        _bindFooterButtons();
        _bindHeaderButtons();
        _bindCMEvents();
        _bindKeyboard();
        _bindSwipeGesture();
        requestAnimationFrame(_updateMore2Indicator);

        // slotNavMode 복원
        try {
            if (localStorage.getItem('usekit_slot_nav') === '1') {
                _setSlotNavActive(true);
            }
        } catch(e) {}

        // Focus 복원
        try {
            if (localStorage.getItem('usekit_focus') === '1') {
                window.NavFocus?.toggle?.(true);
            }
        } catch(e) {}

        // LK 복원 — SlotManager._apply() 완료 후 적용
        try {
            if (localStorage.getItem('usekit_lk') === '1') {
                requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() => {
                    State.setLK(true);
                    UIViewport?.blockKeyboard?.();
                    _updateLKBtn(true);
                    window.ActiveState?.setEdit?.('lkMode', true);
                })));
            }
        } catch(e) {}
        // uiMode 복원은 slot_manager → applyToUI → syncUiMode 경로로 처리
    }
    function _bindNavButtons() {
        // KB 오픈 + 빈라인 커서 상태에서 scrollGuard 활성
        // Ctrl/Alt 토글 시 가드 타이머 갱신용
        function _guardIfEmptyLine() {
            if (!UIViewport.isKbOpen()) return;
            const view = Editor.get();
            if (!view) return;
            let isEmpty = false;
            try { isEmpty = view.state.doc.lineAt(view.state.selection.main.head).length === 0; } catch (e) {}
            if (isEmpty) UIViewport.triggerScrollGuard();
        }

        // 방향키: 반복 지원
        _bindRepeat('btnNavUp',    () => { if (window._imeSnap) { window.imeSnapRestore?.(); return; } if (State.getModeF())  { NavFocus.scrollV(-1); } else if (State.getModeA()) { Nav.modeAMoveUp();    } else if (_navCtrl) { Nav.pageUp();     } else if (_navAlt) { Nav.moveLineAlt(-1); } else { Nav.moveUp();    } });
        _bindRepeat('btnNavDown',  () => { if (window._imeSnap) { window.imeSnapRestore?.(); return; } if (State.getModeF())  { NavFocus.scrollV( 1); } else if (State.getModeA()) { Nav.modeAMoveDown();  } else if (_navCtrl) { Nav.pageDown();    } else if (_navAlt) { Nav.moveLineAlt(1);  } else { Nav.moveDown();  } });
        _bindRepeat('btnNavLeft',  () => { if (window._imeSnap) { window.imeSnapRestore?.(); return; } if (State.getModeF())  { NavFocus.scrollH(-3); } else if (State.getModeA()) { Nav.modeAMoveLeft();  } else if (_navCtrl) { Nav.wordLeft();    } else if (_navAlt) { Nav.indent(-1);     } else { Nav.moveLeft();  } });
        _bindRepeat('btnNavRight', () => { if (window._imeSnap) { window.imeSnapRestore?.(); return; } if (State.getModeF())  { NavFocus.scrollH( 3); } else if (State.getModeA()) { Nav.modeAMoveRight(); } else if (_navCtrl) { Nav.wordRight();   } else if (_navAlt) { Nav.indent(1);      } else { Nav.moveRight(); } });

        // H: 단일=줄시작, 더블=col0, 롱=문서시작
        _bindDoubleLong('btnNavH',
            () => {                                                      // 짧게
                if (_multiMode && _checkMode) {
                    if (_qnShift && !_dbgCur) {
                        const bs = window.State?.getBS?.();
                        if (bs) {
                            const off = window.Editor?.posToOffset?.(bs);
                            if (off != null) {
                                const ranges = window.BlockState?.getRanges?.() ?? [];
                                const mIdx = window.BlockState?.getMainIdx?.() ?? 0;
                                const specs = ranges.map((r, i) =>
                                    i === mIdx ? { anchor: off, head: off } : { anchor: r.anchor, head: r.head }
                                );
                                const v = window.Editor?.get?.();
                                const newMIdx = v ? specs.findIndex(s => {
                                    try { return v.state.doc.lineAt(s.head).number - 1 === bs.line; } catch(e) { return false; }
                                }) : mIdx;
                                window.BlockState?.dispatch?.(specs, newMIdx >= 0 ? newMIdx : mIdx);
                                window.BlockState?.render?.();
                            }
                        }
                    } else {
                        window.NavBlockV2?.homeEnd?.('home', { checkOnly: true });
                    }
                    return;
                }
                if (_navCtrl) { Nav.jumpDocStart(); _setNavCtrl(false); _guardIfEmptyLine(); return; }
                if (State.getModeA()) { Nav.modeAH('short'); _guardIfEmptyLine(); return; }
                if (State.getModeS()) {
                    if (!NavBlock.trySwapByKey('H')) Nav.jumpH();
                } else {
                    State.clearBlock();
                    Nav.jumpH();
                }
                _guardIfEmptyLine();
            },
            () => {                                                      // 더블: 라인 처음(col 0)
                if (State.getModeA()) { Nav.modeAH('double'); _guardIfEmptyLine(); return; }
                if (State.getModeS()) NavBlock.trySwapByKey('H');
                State.clearBlock();
                Nav.jumpLineStart();
                _guardIfEmptyLine();
            },
            () => {                                                      // 롱: 문서 처음
                if (State.getModeA()) { Nav.modeAH('long'); _guardIfEmptyLine(); return; }
                Nav.jumpDocStart();
                _guardIfEmptyLine();
            }
        );

        _bindDoubleLong('btnNavE',
            () => {                                                      // 짧게
                if (_multiMode && _checkMode) {
                    if (_qnShift && !_dbgCur) {
                        const be = window.State?.getBE?.();
                        if (be) {
                            const off = window.Editor?.posToOffset?.(be);
                            if (off != null) {
                                const ranges = window.BlockState?.getRanges?.() ?? [];
                                const mIdx = window.BlockState?.getMainIdx?.() ?? 0;
                                const specs = ranges.map((r, i) =>
                                    i === mIdx ? { anchor: off, head: off } : { anchor: r.anchor, head: r.head }
                                );
                                const v = window.Editor?.get?.();
                                const newMIdx = v ? specs.findIndex(s => {
                                    try { return v.state.doc.lineAt(s.head).number - 1 === be.line; } catch(e) { return false; }
                                }) : mIdx;
                                window.BlockState?.dispatch?.(specs, newMIdx >= 0 ? newMIdx : mIdx);
                                window.BlockState?.render?.();
                            }
                        }
                    } else {
                        window.NavBlockV2?.homeEnd?.('end', { checkOnly: true });
                    }
                    return;
                }
                if (_navCtrl) { Nav.jumpDocEnd(); _setNavCtrl(false); _guardIfEmptyLine(); return; }
                if (State.getModeA()) { Nav.modeAE('short'); _guardIfEmptyLine(); return; }
                if (State.getModeS()) {
                    if (!NavBlock.trySwapByKey('E')) Nav.jumpE();
                } else {
                    State.clearBlock();
                    Nav.jumpE();
                }
                _guardIfEmptyLine();
            },
            () => {                                                      // 더블: 라인 끝
                if (State.getModeA()) { Nav.modeAE('double'); _guardIfEmptyLine(); return; }
                if (State.getModeS()) {
                    if (!NavBlock.trySwapByKey('E')) Nav.jumpE();
                } else {
                    State.clearBlock();
                    Nav.jumpE();
                }
                _guardIfEmptyLine();
            },
            () => {                                                      // 롱: 문서 끝
                if (State.getModeA()) { Nav.modeAE('long'); _guardIfEmptyLine(); return; }
                Nav.jumpDocEnd();
                _guardIfEmptyLine();
            }
        );

        // S 모드
        _bind('btnModeS',    () => { if (State.getModeA()) Nav.resetModeA(); Nav.toggleModeS(); _guardIfEmptyLine(); });
        _bind('checkS',      () => { if (State.getModeA()) Nav.resetModeA(); Nav.toggleModeS(); _guardIfEmptyLine(); });

        // M 모드
        _bind('btnModeM',    () => { Nav.toggleModeM(); _guardIfEmptyLine(); });
        _bind('checkM',      () => { Nav.toggleModeM(); _guardIfEmptyLine(); });

        // a/A: progressive select — 단일=단어, 더블=줄, 롱=전체
        _bindDoubleLong('btnSelectAll',
            () => { Nav.progressiveSelect(); _guardIfEmptyLine(); },
            () => { State.getModeAStep() >= 3 ? Nav.resetModeA() : Nav.selectAllModeA(); _guardIfEmptyLine(); },
            () => { State.getModeAStep() >= 3 ? Nav.resetModeA() : Nav.selectAllModeA(); _guardIfEmptyLine(); }
        );

        // 숫자패드
        ['btnLineMinus10','btnLineMinus4','btnLineMinus1',
         'btnLine1','btnLine4','btnLine10'].forEach(id => {
            _bindRepeat(id, () => window.NavNum?.trigger(id));
        });

        // Row 2 axis/pattern
        _bind('btnAxis',          () => { window.NavNum?.toggleAxis('row2');    _guardIfEmptyLine(); });
        _bind('btnToggle',        () => { window.NavNum?.toggleAxis('row2');    _guardIfEmptyLine(); });
        _bind('btnPatternToggle', () => { window.NavNum?.togglePattern('row2'); _guardIfEmptyLine(); });

        // Row 3 axis/pattern
        _bind('btnAxisV',              () => { window.NavNum?.toggleAxis('row3');    _guardIfEmptyLine(); });
        _bind('btnThirdPatternToggle', () => { window.NavNum?.togglePattern('row3'); _guardIfEmptyLine(); });

        // Row 1 more button (H/E행 기어): 2열+3열 동시 보이기/숨기기
        // 1열 기어: touchcancel 무시하는 전용 바인딩 (삼성 브라우저 롱프레스 touchcancel 방지)
        (function() {
            const el = document.getElementById('btnNavMore1');
            if (!el) return;
            let _t = null, _fired = false;
            const _doShort = () => {
                const row2 = document.querySelector('.block-numbers');
                if (!row2) return;
                const hidden = row2.classList.contains('is-hidden');
                row2.classList.toggle('is-hidden', !hidden);
                _updateMore2Indicator();
                if (!UIViewport.isKbOpen()) UIViewport.blockKeyboard();
                if (window.UIViewport?.recalcEditorRect) UIViewport.recalcEditorRect();
                window.SlotManager?.saveUIState?.();
                _guardIfEmptyLine();
            };
            const _doLong = () => {
                const row2 = document.querySelector('.block-numbers');
                const row3 = document.getElementById('navThirdRow');
                if (!row2) return;
                const hidden = row2.classList.contains('is-hidden');
                row2.classList.toggle('is-hidden', !hidden);
                if (row3) row3.classList.toggle('is-hidden', !hidden);
                _updateMore2Indicator();
                if (!UIViewport.isKbOpen()) UIViewport.blockKeyboard();
                if (window.UIViewport?.recalcEditorRect) UIViewport.recalcEditorRect();
                window.SlotManager?.saveUIState?.();
                _guardIfEmptyLine();
            };
            el.addEventListener('touchstart', (e) => {
                e.preventDefault();
                _fired = false;
                _t = setTimeout(() => { _fired = true; _doLong(); }, 300);
            }, { passive: false });
            el.addEventListener('touchend', (e) => {
                e.preventDefault();
                clearTimeout(_t);
                if (!_fired) _doShort();
            }, { passive: false });
            // touchcancel 무시 — 삼성 브라우저에서 롱프레스 도중 cancel 발생해도 타이머 유지
        })();

        // Row 2 more button (S/M행 기어): 3열 보이기/숨기기 (기존 유지)
        _bind('btnNavMore2', () => {
            const row = document.getElementById('navThirdRow');
            if (row) row.classList.toggle('is-hidden');
            _updateMore2Indicator();
            if (window.UIViewport?.recalcEditorRect) UIViewport.recalcEditorRect();
            window.SlotManager?.saveUIState?.();
            _guardIfEmptyLine();
        });

        // Row 3 more button (GO/New행 기어): 기본모드 ↔ LOC모드 전환
        let _thirdRowLocMode = false;
        function _toggleThirdRowMode() {
            _thirdRowLocMode = !_thirdRowLocMode;
            document.querySelectorAll('.thirdrow-default').forEach(el =>
                el.classList.toggle('is-hidden', _thirdRowLocMode));
            document.querySelectorAll('.thirdrow-loc').forEach(el =>
                el.classList.toggle('is-hidden', !_thirdRowLocMode));
            const gear = document.getElementById('btnNavMore3');
            if (gear) gear.style.color = _thirdRowLocMode ? 'var(--ac-blue)' : '';
            if (window.UIViewport?.recalcEditorRect) UIViewport.recalcEditorRect();
            window.SlotManager?.saveUIState?.();
        }
        _bind('btnNavMore3', () => { _toggleThirdRowMode(); _guardIfEmptyLine(); });

        // 편집툴 Ctrl 상태 (방향키 단어이동, 자동초기화 없음)
        let _navCtrl = false;
        function _setNavCtrl(on) {
            _navCtrl = on;
            const btn = document.getElementById('btnNavCtrl');
            if (!btn) return;
            btn.style.background  = on ? 'var(--ac-blue-bg)' : '';
            btn.style.borderColor = on ? 'var(--ac-blue-bd)' : '';
            btn.style.color       = on ? 'var(--ac-blue)'    : '';
            _guardIfEmptyLine();
        }
        _bind('btnNavCtrl', () => { _setNavCtrl(!_navCtrl); });
        // 편집툴 Alt 상태 (방향키 들여쓰기/줄이동, 자동초기화 없음)
        let _navAlt = false;
        function _setNavAlt(on) {
            _navAlt = on;
            const btn = document.getElementById('btnThirdLAlt');
            if (!btn) return;
            btn.style.background  = on ? 'var(--ac-blue-bg)' : '';
            btn.style.borderColor = on ? 'var(--ac-blue-bd)' : '';
            btn.style.color       = on ? 'var(--ac-blue)'    : '';
            _guardIfEmptyLine();
        }
        _bind('btnThirdLAlt', () => { _setNavAlt(!_navAlt); });
        // Tab/Find/Prev/Next 셋트 — Ctrl+Tab으로 슬롯모드↔Find모드 토글
        // 키패드 Find / 풋터 Find — 독립 상태
        let _findMode = false;        // 키패드용
        let _footerFindMode = false;  // 풋터용
        window._findMode = false;
        window._footerFindMode = false;

        function _setFindMode(on) {           // 키패드 Find
            _findMode = on;
            window._findMode = on;
            ['btnThirdLFind','btnThirdSP','btnThirdSN'].forEach(id => {
                const b = document.getElementById(id);
                if (!b) return;
                b.style.background  = '';
                b.style.borderColor = on ? 'var(--ac-purple)' : '';
                b.style.color       = on ? 'var(--ac-purple)' : '';
            });
            const findBtn = document.getElementById('btnThirdLFind');
            if (findBtn) findBtn.textContent = on ? 'Find' : 'New';
        }
        function _setFooterFindMode(on) {     // 풋터 Find
            _footerFindMode = on;
            window._footerFindMode = on;
            if (on) { window._setSlotNavActive?.(false); window._setBookmarkMode?.(false); }
            const btn = document.getElementById('btnFooterFind');
            if (btn) {
                btn.style.background  = '';
                btn.style.borderColor = on ? 'var(--ac-purple)' : '';
                btn.style.color       = on ? 'var(--ac-purple)' : '';
            }
            // Find List 버튼 표시/숨김
            const listBtn = document.getElementById('btnFooterFindList');
            if (listBtn) listBtn.style.display = on ? '' : 'none';
            _updateMarkOverlay();
            _updateFooterArrowFindColor();
        }
        function _updateFooterArrowFindColor() {
            const on = _footerFindMode;
            ['btnFooterLeft','btnFooterRight'].forEach(id => {
                const b = document.getElementById(id);
                if (!b) return;
                b.style.background  = '';
                b.style.borderColor = on ? 'var(--ac-purple)' : '';
                b.style.color       = on ? 'var(--ac-purple)' : '';
            });
        }
        window._setFindMode = _setFindMode;
        window._setFooterFindMode = _setFooterFindMode;
        _bind('btnThirdLTab', () => {
            if (_navCtrl) {
                _setFindMode(!_findMode);
                _setNavCtrl(false);
                return;
            }
            Editor.replaceSelection('	'); Editor.focus();
        });
        _bind('btnThirdLFind', () => {
            if (_findMode) { window.NavFind?.toggle?.(); return; }
            window.SlotManager?.newFile?.();
        });
        _bind('btnThirdSP', () => {
            if (_findMode) { window.NavFind?.quickSearch?.('prev'); return; }
            if (_navCtrl) {
                _setNavCtrl(false);
                const active = window.SlotManager?.getActiveIndex?.() ?? -1;
                if (active <= 0) { UI.showToast('First slot', 800); return; }
                window.SlotManager?.slotFirst?.();
                return;
            }
            const active = window.SlotManager?.getActiveIndex?.() ?? -1;
            if (active <= 0) { UI.showToast('First slot', 800); return; }
            window.SlotManager?.slotPrev?.();
        });
        _bind('btnThirdSN', () => {
            if (_findMode) { window.NavFind?.quickSearch?.('next'); return; }
            if (_navCtrl) {
                _setNavCtrl(false);
                const active = window.SlotManager?.getActiveIndex?.() ?? -1;
                const total  = window.SlotManager?.getSlotCount?.()  ?? 0;
                if (active >= total - 1) { UI.showToast('New slot ready', 800); window.KpFn?.[6]?.(); return; }
                window.SlotManager?.slotLast?.();
                return;
            }
            const active = window.SlotManager?.getActiveIndex?.() ?? -1;
            const total  = window.SlotManager?.getSlotCount?.()  ?? 0;
            if (active >= total - 1) {
                UI.showToast('New slot ready', 800);
                window.KpFn?.[6]?.();
                return;
            }
            window.SlotManager?.slotNext?.();
        });
        // ⌫ □ ⏎ ⌦
        _bindRepeat('btnThirdLBs', (isFirst) => {
            if (_navCtrl && Editor.get()?.state.selection.main.empty) { Nav.deleteWordBefore(); return; }
            if (isFirst) UIFeedback.del();
            else         UIFeedback.delRepeat();
            Editor.execCommand('delCharBefore');
        });
        _bindRepeat('btnThirdLSel', () => {
            UIFeedback.space();
            Editor.replaceSelection(' ');
        });
        _bindRepeat('btnThirdLEnt', () => {
            if (_navCtrl && Editor.get()?.state.selection.main.empty) { Nav.insertLineBelow(); return; }
            UIFeedback.enter();
            Editor.replaceSelection('\n');
        });
        _bindRepeat('btnThirdLDel', (isFirst) => {
            if (_navCtrl && Editor.get()?.state.selection.main.empty) { Nav.deleteWordAfter(); return; }
            if (isFirst) UIFeedback.del();
            else         UIFeedback.delRepeat();
            Editor.execCommand('delCharAfter');
        });

        _bind('btnNavEsc', () => {
            // ESC: 모든 활성 상태 초기화
            if (State.getModeS()) State.setModeS(false);
            if (State.getModeA()) Nav.resetModeA();
            if (State.getModeM()) State.setModeM(false);
            State.clearBlock();
            Editor.clearSelection();
            _setNavCtrl(false);
            _setNavAlt(false);
            if (_findMode) _setFindMode(false);
            window.NavNum?.resetAll?.();
            _guardIfEmptyLine();
        });
        // Row 3 numpad
        ['btnThirdMinus10','btnThirdMinus4','btnThirdMinus1',
         'btnThird1','btnThird4','btnThird10'].forEach(id => {
            _bindRepeat(id, () => { window.NavNum?.trigger(id); _guardIfEmptyLine(); });
        });

        // ×2/÷2 toggle (row 2 scale)
        _bind('btnNavScale2',  () => { window.NavNum?.toggleScale2();  _guardIfEmptyLine(); });

        // ×10/÷10 toggle (row 3 scale)
        _bind('btnNavScale10', () => { window.NavNum?.toggleScale10(); _guardIfEmptyLine(); });

        // L 버튼: 단일=라인번호 토글, 롱=디버그 정보
        _bindLong('btnLineInfo',
            () => {
                const on = !Editor.getOption('lineNumbers');
                Editor.setOption('lineNumbers', on);
                Editor.refresh();
                UI.showToast(on ? 'Line# ON' : 'Line# OFF', 800);
                UIStats.updateStatsNow();
                _updateLineNumBtn(on);
                window.SlotManager?.saveUIState?.();
            },
            () => UIStats.updateStatsNow()
        );
    }
    function _bindEditButtons() {
        // Undo/Redo
        _bind('btnUndo', () => Nav.undo());
        _bind('btnRedo', () => Nav.redo());

        // Copy: 단일=선택복사, 롱=전체복사
        _bindLong('btnCopy',
            () => {
                const text = Editor.getSelection() || Editor.getText();
                window._usekitClipCopy?.(text) || navigator.clipboard?.writeText(text);
                UI.showToast('Copied', 800); UI.notifyCopied();
            },
            () => {
                window._usekitClipCopy?.(Editor.getText()) || navigator.clipboard?.writeText(Editor.getText());
                UI.showToast('All copied', 800); UI.notifyCopied();
            }
        );

        // Paste
        _bind('btnPaste', () => Nav.pasteAtCursor());

        // RUN TOOL / SQL VIEW — 플로팅 버튼으로 연결 (index.html 인라인 스크립트)
        // _bind('btnRunTool', ...) 은 플로팅 버튼이 직접 처리
        // _bind('btnSqlView', ...) 도 인라인 스크립트(SqlView)가 직접 처리

        _bindRepeat('btnCopyQuick', () => {
            const text = Nav.copyBlock();
            if (text) { UI.showToast('Copied', 600); UI.notifyCopied(); }
            if (State.getModeA()) { Nav.resetModeA(); }
        });
        _bindRepeat('btnPasteQuick', () => Nav.pasteAtCursor());
        _bindRepeat('btnClearLine',  () => { Nav.cutLine(); UI.showToast('Cut', 600); UI.notifyCopied(); });
        _bind('btnNavR', () => window.NavClipboard?.toggleModal());
    }
    function _bindFileButtons() {
        _bind('btnSave',  () => SlotManager.openSavePopup());
        _bind('btnLoad',  () => SlotManager.openLoadPopup());
        _bind('btnNew',   () => SlotManager.newFile());
        _bind('btnClose', () => SlotManager.closeCurrentSlot());
    }

    // Bind an element with short-tap and long-tap (500ms) handlers
    function _bindLongShort(id, onShort, onLong) {
        const el = document.getElementById(id);
        if (!el) return;
        let _timer = null, _fired = false;
        const LONG_MS = 500;
        function start(e) { e.preventDefault(); _fired = false; _timer = setTimeout(() => { _fired = true; onLong?.(); }, LONG_MS); }
        function end(e) { if (e) e.preventDefault(); clearTimeout(_timer); if (!_fired) onShort?.(); }
        function cancel() { clearTimeout(_timer); }
        el.addEventListener('touchstart', start, { passive: false });
        el.addEventListener('touchend',   end,   { passive: false });
        el.addEventListener('touchcancel', cancel, { passive: true });
        el.addEventListener('mousedown',  start);
        el.addEventListener('mouseup',    end);
        el.addEventListener('mouseleave', cancel);
    }

    // Toggle between LOC address view and slot container
    let _showingSlots = true;
    function _toggleLocView() {
        _showingSlots = !_showingSlots;
        const locInput     = document.getElementById('metaLoc');
        const slotContainer= document.getElementById('slotContainer');
        if (locInput)      locInput.style.display      = _showingSlots ? 'none' : 'block';
        if (slotContainer) slotContainer.style.display = _showingSlots ? 'flex' : 'none';
    }
    // ── 북마크 모드 (모듈 스코프) ───────────────────────────────
    let _bookmarkMode = false;
    // ── 열 기어 인디케이터 ────────────────────────────────────
    function _updateMore2Indicator() {
        const row2 = document.querySelector('.block-numbers');
        const row3 = document.getElementById('navThirdRow');
        const r2hidden = row2?.classList.contains('is-hidden') ?? false;
        const r3hidden = row3?.classList.contains('is-hidden') ?? false;
        const btn1 = document.getElementById('btnNavMore1');
        const btn2 = document.getElementById('btnNavMore2');

        // 1열 기어
        if (btn1) {
            btn1.classList.remove('ind-down', 'ind-up');
            if (!r2hidden) {
                btn1.classList.add('ind-down');   // 1+2(+3) → 아래점 (접힌다)
            } else {
                btn1.classList.add('ind-up');     // 1+3, 1열만 → 위점 (펼쳐진다)
            }
        }

        // 2열 기어
        if (btn2) {
            btn2.classList.remove('ind-down', 'ind-up');
            if (!r2hidden && !r3hidden) btn2.classList.add('ind-down'); // 1+2+3 → 아래점
            else if (!r2hidden && r3hidden) btn2.classList.add('ind-up'); // 1+2 → 위점
            // 2열 숨김 → 없음
        }
    }

    function _updateWrapBtnState() {
        const btn = document.getElementById('btnFooterWrap');
        if (!btn) return;
        const wrap = !!Editor.getOption('lineWrapping');
        const bm   = _bookmarkMode;
        if (!bm && !wrap) {
            btn.style.background  = '';
            btn.style.borderColor = '';
            btn.style.color       = '';
        } else if (!bm && wrap) {
            btn.style.background  = 'var(--ac-blue-bg)';
            btn.style.borderColor = 'var(--ac-blue-bd)';
            btn.style.color       = 'var(--ac-blue)';
        } else if (bm && !wrap) {
            btn.style.background  = '';
            btn.style.borderColor = 'var(--ac-red-bd)';
            btn.style.color       = 'var(--ac-red)';
        } else {
            btn.style.background  = 'var(--ac-red-bg)';
            btn.style.borderColor = 'var(--ac-red-bd)';
            btn.style.color       = 'var(--ac-red)';
        }
    }
    function _updateMarkOverlay() {
        const overlay = document.getElementById('footerMarkOverlay');
        if (!overlay) return;
        // 표시할 버튼이 하나라도 있으면 overlay 표시
        const hasVisible = ['btnFooterMark','btnFooterClose','btnFooterFindList']
            .some(id => {
                const el = document.getElementById(id);
                return el && el.style.display !== 'none';
            });
        if (!hasVisible) {
            overlay.style.display = 'none';
            return;
        }
        overlay.style.display = 'flex';
        // btnFooterFav 오른쪽 끝 기준으로 left 계산 (없으면 btnFooterLock 기준)
        const anchorBtn = document.getElementById('btnFooterFav') || document.getElementById('btnFooterLock');
        const statusbar = overlay.closest('.statusbar');
        if (anchorBtn && statusbar) {
            const sbRect = statusbar.getBoundingClientRect();
            const lkRect = anchorBtn.getBoundingClientRect();
            const left = lkRect.right - sbRect.left + 4;
            overlay.style.left = left + 'px';
        }
    }
    window._updateMarkOverlay = _updateMarkOverlay;

    function _setBookmarkMode(on) {
        _bookmarkMode = on;
        window._bookmarkMode = on;
        if (on) { window._setSlotNavActive?.(false); window._setFooterFindMode?.(false); }
        _updateWrapBtnState();
        ['btnFooterLeft','btnFooterRight'].forEach(id => {
            const b = document.getElementById(id);
            if (!b) return;
            b.style.background  = '';
            b.style.borderColor = on ? 'var(--ac-red-bd)' : '';
            b.style.color       = on ? 'var(--ac-red)'    : '';
        });
        const markBtn = document.getElementById('btnFooterMark');
        if (markBtn) markBtn.style.display = on ? '' : 'none';
        if (on) {
            window._updateMarkBtn?.();
            Editor.on('cursorActivity', window._updateMarkBtn);
        } else {
            Editor.off('cursorActivity', window._updateMarkBtn);
        }
        _updateMarkOverlay();
    }
    window._setBookmarkMode = _setBookmarkMode;

    function _bindFooterButtons() {
        // 풋터 전체: OS키 내려진 상태에서 버튼 터치 시 OS키 올라오기 차단
        const _footerEl = document.querySelector('.footer-section');
        if (_footerEl) {
            _footerEl.addEventListener('touchstart', () => {
                if (!window.UIViewport?.isKbOpen?.()) window.UIViewport?.blockKeyboard?.();
            }, { passive: true });
        }
        _bind('btnFooterMark', () => {
            window._addBookmark?.();
        });
        _bind('btnFooterClose', () => {
            window.SlotManager?.closeCurrentSlot?.((remaining) => {
                if (remaining === 0) _setSlotNavActive(false);
            });
        });
        _bind('btnFooterMenu', () => {
            if (!window.UISettings) return;
            // Settings가 열려있으면 닫기 (close가 _persistSettings 호출)
            // 닫힌 상태면 열기
            UISettings.toggle();
            // 닫힐 때: 현재 UI 상태 ActiveState에 반영 + autosave 트리거
            if (!UISettings.isOpen?.()) {
                if (window.ActiveState) ActiveState.captureFromUI();
                window.SlotManager?.saveUIState?.();
            }
        });

        // ── 슬롯 네비 모드 (붙여넣기 롱클릭) ──────────────────

        _bindRepeat('btnFooterLeft',  () => {
            if (_slotNavMode) {
                const active = window.SlotManager?.getActiveIndex?.() ?? -1;
                if (active <= 0) { UI.showToast('First slot', 800); return; }
                window.SlotManager?.slotPrev?.();
                return;
            }
            if (_footerFindMode) { window.NavFind?.quickSearch?.('prev'); return; }
            if (_bookmarkMode) { window._goPrevBookmark?.(); return; }
            Nav.moveLeft();
        });
        _bindRepeat('btnFooterRight', () => {
            if (_slotNavMode) {
                const active  = window.SlotManager?.getActiveIndex?.() ?? -1;
                const total   = window.SlotManager?.getSlotCount?.()  ?? 0;
                if (active >= total - 1) {
                    UI.showToast('New slot ready', 800);
                    window.KpFn?.[6]?.();
                    return;
                }
                window.SlotManager?.slotNext?.();
                return;
            }
            if (_footerFindMode) { window.NavFind?.quickSearch?.('next'); return; }
            if (_bookmarkMode) { window._goNextBookmark?.(); return; }
            Nav.moveRight();
        }, 80, 350, { shouldRepeat: () => !_slotNavMode });
        // 풋터 Find: 단클릭 → 모달 토글, 롱클릭 → 검색 결과 있을 때 사일런트 활성(보라)

        _bind('btnFooterUndo',  () => Nav.undo());
        _bind('btnFooterRedo',  () => Nav.redo());
        _bindLong('btnFooterPaste',
            () => { if (_slotNavMode) { _setSlotNavActive(false); return; } Nav.pasteAtCursor(); },
            () => _setSlotNavActive(!_slotNavMode)
        );

        // Save 버튼 — 단클릭: 슬롯 네비 토글, 롱클릭: Save
        _bindLong('btnFooterSave',
            () => _setSlotNavActive(!_slotNavMode),
            () => window.SlotManager?.save?.()
        );
        _bindLong('btnFooterFind',
            () => _setFooterFindMode(!_footerFindMode),
            () => window.NavFind?.toggle?.()
        );
        _bind('btnFooterFindList', () => {
            window.NavClipboard?.openModal?.();
            // Find 탭으로 전환
            setTimeout(() => window.NavClipboard?.switchTab?.('find'), 50);
        });

        // Wrap / 북마크 토글
        // 상태 4가지:
        //   북마크OFF 랩OFF → 기본 (투명)
        //   북마크OFF 랩ON  → 파랑 보더+배경+텍스트
        //   북마크ON  랩OFF → 빨강 보더+텍스트, 투명 배경
        //   북마크ON  랩ON  → 빨강 보더+배경+텍스트
        _bindLong('btnFooterWrap',
            // 짧게: 북마크 토글 (방향키 연결/해지)
            () => {
                _setBookmarkMode(!_bookmarkMode);
                UI.showToast(_bookmarkMode ? 'Bookmark ON' : 'Bookmark OFF', 800);
            },
            // 길게: 랩 토글
            () => {
                const wrap = !Editor.getOption('lineWrapping');
                UIViewport.blockKeyboard();
                Editor.setOption('lineWrapping', wrap);
                Editor.refresh();
                UI.showToast(wrap ? 'Wrap ON' : 'Wrap OFF', 800);
                _updateWrapBtnState();
                window.SlotManager?.saveUIState?.();
            }
        );

        // LK 토글
        _bind('btnFooterLock', () => {
            State.toggleLK();
            const lk = State.getLK();
            if (lk) {
                UIViewport.blockKeyboard();
            } else if (window._sysKbMode) {
                // LK 해제 + sysKbMode: OS 키보드 허용 (자동 숨김/복원 모드)
                UIViewport.allowKeyboard();
            }
            UI.showToast(lk ? '🔒 LK ON' : '🔓 LK OFF', 800);
            _syncButtonColors();
            UIStats.updateKUButton(false);
            window.ActiveState?.setEdit?.('lkMode', lk);
            window.SlotManager?.saveUIState?.();
            try { localStorage.setItem('usekit_lk', lk ? '1' : '0'); } catch(e) {}
        });

        // Favorite 슬롯 토글
        _bind('btnFooterFav', () => {
            const slot = window.SlotManager?.getCurrentSlot?.();
            if (!slot) return;
            const FAV_KEY = 'usekit_fav_slot';
            let favSet;
            try { favSet = new Set(JSON.parse(localStorage.getItem(FAV_KEY) || '[]')); }
            catch { favSet = new Set(); }
            if (favSet.has(slot)) favSet.delete(slot); else favSet.add(slot);
            try { localStorage.setItem(FAV_KEY, JSON.stringify([...favSet])); } catch(e) {}
            const isFav = favSet.has(slot);
            const btn = document.getElementById('btnFooterFav');
            if (btn) btn.textContent = isFav ? '★' : '☆';
            UI.showToast(isFav ? '★ Favorite' : '☆ Removed', 800);
        });

        // ── RUN 버튼 ────────────────────────────────────────────────

        // input() 호출 패턴 추출
        function _extractInputCalls(code) {
            const re = /input\s*\(([^)]*)\)/g;
            const prompts = [];
            let m;
            while ((m = re.exec(code)) !== null) {
                // 프롬프트 문자열 추출 (있으면), 없으면 빈 문자열
                let p = m[1].trim();
                if ((p.startsWith('"') && p.endsWith('"')) ||
                    (p.startsWith("'") && p.endsWith("'"))) {
                    p = p.slice(1, -1);
                } else if (p) {
                    p = 'Input:';  // 변수 등 복잡한 경우
                } else {
                    p = 'Input:';
                }
                prompts.push(p);
            }
            return prompts;
        }

        // 커스텀 input 팝업 (Samsung Browser prompt() 대체)
        function _showInputPopup(promptText) {
            return new Promise((resolve) => {
                let overlay = document.getElementById('_inputPopup');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = '_inputPopup';
                    overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;' +
                        'background:rgba(0,0,0,0.6);z-index:9999;display:flex;' +
                        'align-items:center;justify-content:center;padding:1.5rem;';
                    document.body.appendChild(overlay);
                }
                overlay.innerHTML = `
                    <div style="background:var(--bg-base,#1e1e1e);border-radius:14px;
                         padding:1.2rem 1rem;width:100%;max-width:380px;
                         box-shadow:0 4px 24px rgba(0,0,0,0.5);">
                      <div style="font-size:0.8rem;opacity:0.6;margin-bottom:0.5rem;">INPUT</div>
                      <div id="_inputPromptText" style="font-size:0.9rem;margin-bottom:0.8rem;
                           word-break:break-all;"></div>
                      <input id="_inputPopupField" type="text" style="width:100%;box-sizing:border-box;
                             padding:0.5rem 0.7rem;border-radius:8px;border:1px solid #444;
                             background:#2a2a2a;color:#eee;font-size:0.9rem;outline:none;" />
                      <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:0.8rem;">
                        <button id="_inputPopupCancel" style="padding:0.45rem 1rem;border-radius:8px;
                            border:none;background:#444;color:#eee;font-size:0.85rem;cursor:pointer;">Cancel</button>
                        <button id="_inputPopupOk" style="padding:0.45rem 1rem;border-radius:8px;
                            border:none;background:#007aff;color:#fff;font-size:0.85rem;
                            font-weight:600;cursor:pointer;">OK</button>
                      </div>
                    </div>`;
                overlay.style.display = 'flex';
                document.getElementById('_inputPromptText').textContent = promptText || 'Input:';
                const field = document.getElementById('_inputPopupField');
                field.value = '';
                setTimeout(() => field.focus(), 100);

                const _done = (val) => {
                    overlay.style.display = 'none';
                    resolve(val);
                };
                document.getElementById('_inputPopupOk').onclick     = () => _done(field.value);
                document.getElementById('_inputPopupCancel').onclick  = () => _done(null);
                field.onkeydown = (e) => { if (e.key === 'Enter') _done(field.value); };
            });
        }

        async function _collectInputs(prompts) {
            const values = [];
            for (const p of prompts) {
                const val = await _showInputPopup(p);
                if (val === null) return null;  // 취소
                values.push(val);
            }
            return values;
        }

        function _openTermux() {
            console.log('[_openTermux] intent 실행');
            window.location.href = 'intent:///#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;package=com.termux;end';
        }

        // 출력 누적 — running 상태 body 반환 (응답 오면 innerHTML 교체)
        function _appendBlock(mode) {
            const output = document.getElementById('runOutput');
            if (!output) return null;
            const ts = (() => {
                const d = new Date();
                return [d.getHours(), d.getMinutes(), d.getSeconds()]
                    .map(n => String(n).padStart(2,'0')).join(':');
            })();
            const header = document.createElement('div');
            header.style.cssText = 'margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;color:#7a8a9a;';
            header.textContent = `[USEKIT - ${ts}] [${mode}]`;
            const body = document.createElement('div');
            body.style.cssText = 'margin-bottom:0.2rem;';
            body.innerHTML = '<span style="opacity:0.4;">running...</span>';
            output.appendChild(header);
            output.appendChild(body);
            output.scrollTop = output.scrollHeight;
            return body;
        }

        function _doRun(code, inputs, mode, execMode) {
            const _isEditMode = window.RunView?.editModeActive;
            // 실행 시 키보드 자동 내림 — edit 모드에서는 편집 유지를 위해 스킵
            if (!_isEditMode) {
                try { window.UIViewport?.blockKeyboard?.(); } catch (e) {}
            }

            const panel  = document.getElementById('runPanel');
            const output = document.getElementById('runOutput');
            console.log('[_doRun] start, panel:', !!panel, 'output:', !!output, 'code len:', code?.length);
            if (!panel || !output) return;

            // edit 모드에서는 overlay 열지 않음 (inline 패널이 이미 보이는 상태)
            if (!_isEditMode) panel.classList.add('is-open');
            const btnOut = document.getElementById('floatBtnOutput');
            if (btnOut) btnOut.classList.add('is-active');

            const bodyEl = _appendBlock(mode || 'RUN');

            // 서버 죽음 감지 시 실행할 공통 로직 (ping 실패 / exec fetch 실패 모두 여기로)
            const _handleServerDown = (reason) => {
                console.log('[_doRun] server down:', reason);
                if (bodyEl) bodyEl.innerHTML = '<span style="color:#ff7b72;">Server is down.<br>Opening Termux to start the server...</span>';
                setTimeout(_openTermux, 800);
                let tries = 0;
                const poll = setInterval(async () => {
                    tries++;
                    console.log('[poll] ping 시도:', tries);
                    try {
                        const r = await fetch('/api/ping', { signal: AbortSignal.timeout(1500) });
                        if (r.ok) {
                            clearInterval(poll);
                            console.log('[poll] 서버 떴음! 자동 실행');
                            if (bodyEl) bodyEl.innerHTML = '<span style="opacity:0.4;">Server connected. Running...</span>';
                            _doRun(code, inputs, mode, execMode);
                        }
                    } catch (_) {}
                    if (tries >= 15) {
                        clearInterval(poll);
                        if (bodyEl) bodyEl.innerHTML += '<br><span style="opacity:0.4;">Waiting for server... Tap Run again.</span>';
                    }
                }, 1000);
            };

            // ping 선체크 (1.5초 timeout) — 서버 죽으면 exec 호출 전에 빠르게 감지
            console.log('[_doRun] /api/ping 선체크 시작');
            fetch('/api/ping', { signal: AbortSignal.timeout(1500) })
            .then(r => {
                if (!r.ok) throw new Error('ping_not_ok_' + r.status);
                console.log('[_doRun] ping OK → /api/exec 시작');
                return fetch('/api/exec', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code, inputs: inputs || [], timeout: 15, mode: execMode || 'exec' }),
                });
            })
            .then(r => { console.log('[_doRun] fetch 응답:', r.status); return r.json(); })
            .catch(e => {
                _handleServerDown(e?.message || String(e));
                return { ok: false, error: 'network_error', stdout: '', stderr: '', _handled: true };
            })
            .then(d => {
                if (!d || d._handled) return;
                const stdout = d.stdout || '';
                const stderr = d.stderr || '';
                const err    = d.error  || '';

                // ANSI 이스케이프 제거 후 escape
                const clean = s => (s || '').replace(/\x1b\[[0-9;]*m/g, '');
                const esc = mode === 'EVAL' ? _escHtmlPretty : _escHtml;
                let html = '';
                const fmtOut = s => mode === 'EVAL' ? _fmtStdout(s) : s;
                if (stdout) html += `<span style="color:#c9d1d9;">${esc(clean(fmtOut(stdout)))}</span>`;
                if (stderr) html += `<span style="color:#f97583;">${esc(clean(stderr))}</span>`;
                if (err && !d.ok) html += `<span style="color:#ff7b72;">\n[ERROR]\n${esc(clean(err))}</span>`;
                // exec 모드에서 출력 없으면 block_echo로 자동 재시도
                if (!html && d.ok && (!execMode || execMode === 'exec')) {
                    console.log('[_doRun] no output → block_echo 자동 재시도');
                    fetch('/api/exec', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ code, inputs: inputs || [], timeout: 15, mode: 'block_echo' }),
                    })
                    .then(r2 => r2.json())
                    .catch(() => null)
                    .then(d2 => {
                        if (!d2 || !bodyEl) return;
                        const out2 = d2.stdout || '';
                        if (out2) {
                            bodyEl.innerHTML = `<span style="color:#c9d1d9;">${esc(clean(out2))}</span>`;
                        } else {
                            bodyEl.innerHTML = '<span style="opacity:0.4;">(no output)</span>';
                        }
                        output.scrollTop = output.scrollHeight;
                    });
                    return;
                }
                if (!html)  html  = '<span style="opacity:0.4;">(no output)</span>';

                if (bodyEl) bodyEl.innerHTML = html;
                output.scrollTop = output.scrollHeight;
            });
        }

        window.runExec = async () => {
            const code = window.Editor?.getText?.() || '';
            console.log('[runExec] code len:', code.length, 'Editor:', !!window.Editor);
            if (!code.trim()) { console.warn('[runExec] empty code'); return; }

            const prompts = _extractInputCalls(code);
            let inputs = [];
            if (prompts.length > 0) {
                const collected = await _collectInputs(prompts);
                if (collected === null) return;
                inputs = collected;
            }

            _doRun(code, inputs, 'RUN:CLEAN');
        };

        window.runLive = async () => {
            const code = window.Editor?.getText?.() || '';
            console.log('[runLive] code len:', code.length, 'Editor:', !!window.Editor);
            if (!code.trim()) { console.warn('[runLive] empty code'); return; }

            const prompts = _extractInputCalls(code);
            let inputs = [];
            if (prompts.length > 0) {
                const collected = await _collectInputs(prompts);
                if (collected === null) return;
                inputs = collected;
            }

            _doRun(code, inputs, 'LIVE', 'live');
        };

        window.runPrint = async () => {
            const code = window.Editor?.getText?.() || '';
            console.log('[runPrint] code len:', code.length, 'Editor:', !!window.Editor);
            if (!code.trim()) { console.warn('[runPrint] empty code'); return; }

            const prompts = _extractInputCalls(code);
            let inputs = [];
            if (prompts.length > 0) {
                const collected = await _collectInputs(prompts);
                if (collected === null) return;
                inputs = collected;
            }

            _doRun(code, inputs, 'EVAL', 'block_echo');
        };

        // ── Output 패널에 한 줄짜리 정보 블록 (안내/경고용) ──
        function _appendInfo(mode, text, color) {
            const panel = document.getElementById('runPanel');
            const output = document.getElementById('runOutput');
            if (!panel || !output) return;
            // edit 모드에서는 overlay 열지 않음
            if (!window.RunView?.editModeActive) panel.classList.add('is-open');
            const btnOut = document.getElementById('floatBtnOutput');
            if (btnOut) btnOut.classList.add('is-active');
            const ts = (() => {
                const d = new Date();
                return [d.getHours(), d.getMinutes(), d.getSeconds()]
                    .map(n => String(n).padStart(2, '0')).join(':');
            })();
            const header = document.createElement('div');
            header.style.cssText = 'margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;color:#7a8a9a;';
            header.textContent = `[USEKIT - ${ts}] [${mode}]`;
            const body = document.createElement('div');
            body.style.cssText = 'margin-bottom:0.2rem;';
            body.innerHTML = `<span style="color:${color || '#e0c97a'};">${_escHtml(text)}</span>`;
            output.appendChild(header);
            output.appendChild(body);
            output.scrollTop = output.scrollHeight;
        }

        // ── 블록 시작 줄 판정 (콜론으로 끝나는 if/for/while/def/class/try/with/elif/else/except/finally/async) ──
        function _isBlockHeader(line) {
            const s = line.replace(/#.*$/, '').trimEnd();  // 주석 제거 후 우측 공백 제거
            if (!s.endsWith(':')) return false;
            // 키워드 시작이 아닐 수도 있으나(예: `x = 1 if y else 2:` 같은 비정상 케이스 무시),
            // 들여쓰기 무시하고 첫 단어만 검사
            const m = s.trimStart().match(/^(if|elif|else|for|while|def|class|try|except|finally|with|async)\b/);
            return !!m;
        }

        // ── 현재 커서 줄 추출 (1-based 라인을 보고 0-based로 도큐먼트 분할) ──
        function _getCurrentLine() {
            const code = window.Editor?.getText?.() || '';
            const cur  = window.Editor?.getCursor?.() || { line: 0, ch: 0 };
            const lines = code.split('\n');
            const idx = Math.max(0, Math.min(cur.line, lines.length - 1));
            return { line: lines[idx] || '', index: idx, total: lines.length };
        }

        // ── 빈줄 기준 현재 블록 추출 ──
        // 정의: 커서가 있는 줄을 포함해서, 위로 빈줄(또는 BOF)까지, 아래로 빈줄(또는 EOF)까지의 연속된 비빈줄 묶음
        // 빈줄 = trim 후 길이 0
        function _getCurrentBlock() {
            const code = window.Editor?.getText?.() || '';
            const cur  = window.Editor?.getCursor?.() || { line: 0, ch: 0 };
            const lines = code.split('\n');
            if (lines.length === 0) return { text: '', start: 0, end: 0 };
            const idx = Math.max(0, Math.min(cur.line, lines.length - 1));
            // 커서가 빈줄에 있으면, 인접한 비빈줄을 찾아 거기로 이동(아래 우선, 없으면 위)
            let pivot = idx;
            const isBlank = i => !lines[i] || !lines[i].trim();
            if (isBlank(pivot)) {
                let down = pivot, up = pivot;
                while (down < lines.length && isBlank(down)) down++;
                while (up >= 0 && isBlank(up)) up--;
                if (down < lines.length) pivot = down;
                else if (up >= 0) pivot = up;
                else return { text: '', start: 0, end: 0, empty: true };
            }
            // 위/아래로 빈줄 만날 때까지 확장
            let start = pivot, end = pivot;
            while (start > 0 && !isBlank(start - 1)) start--;
            while (end < lines.length - 1 && !isBlank(end + 1)) end++;
            const text = lines.slice(start, end + 1).join('\n');
            return { text, start, end, empty: false };
        }

        // ── 다음 실행 가능한 줄 찾기 (빈줄·주석·블록 시작줄·들여쓰기 본문 스킵) ──
        // fromIdx 다음(미포함)부터 검색. 못 찾으면 -1.
        // 들여쓰기된 줄은 단독 실행 시 의미가 없거나 SyntaxError(예: return)이므로 제외.
        function _findNextRunnableLine(fromIdx) {
            const code = window.Editor?.getText?.() || '';
            const lines = code.split('\n');
            for (let i = fromIdx + 1; i < lines.length; i++) {
                const raw = lines[i];
                const t = raw.trim();
                if (!t) continue;                       // 빈줄
                if (t.startsWith('#')) continue;        // 주석
                if (raw[0] === ' ' || raw[0] === '\t') continue;  // 들여쓰기 본문
                if (_isBlockHeader(raw)) continue;      // 블록 시작줄 (단독 실행 불가)
                return i;
            }
            return -1;
        }

        // ── 다음 블록의 첫 줄 찾기 (현재 블록 end 이후 첫 비빈줄) ──
        function _findNextBlockStart(afterEndIdx) {
            const code = window.Editor?.getText?.() || '';
            const lines = code.split('\n');
            for (let i = afterEndIdx + 1; i < lines.length; i++) {
                if (lines[i].trim()) return i;
            }
            return -1;
        }

        // ── 커서를 특정 줄의 첫 비공백 위치로 이동 (없으면 EOF 안내) ──
        // mode: 안내 메시지에 쓸 라벨
        function _advanceCursor(targetIdx, mode) {
            if (targetIdx < 0) {
                _appendInfo(mode, '(end of file)', '#7a8a9a');
                return;
            }
            const code = window.Editor?.getText?.() || '';
            const lines = code.split('\n');
            const line = lines[targetIdx] || '';
            const ch = line.match(/^[\t ]*/)[0].length;  // 들여쓰기 끝 위치
            window.Editor?.setCursor?.({ line: targetIdx, ch });
        }

        // ── Line Run ──
        window.runLine = async () => {
            const { line, index } = _getCurrentLine();
            const trimmed = line.trim();
            console.log('[runLine] line', index + 1, 'len:', trimmed.length);

            // 빈줄/주석/블록 시작줄 → 안내 + 다음 실행 가능 줄로 이동
            if (!trimmed) {
                _appendInfo('LINE', `(line ${index + 1}: blank — moving to next)`, '#7a8a9a');
                _advanceCursor(_findNextRunnableLine(index), 'LINE');
                return;
            }
            if (trimmed.startsWith('#')) {
                _appendInfo('LINE', `(line ${index + 1}: comment — moving to next)`, '#7a8a9a');
                _advanceCursor(_findNextRunnableLine(index), 'LINE');
                return;
            }
            if (_isBlockHeader(line)) {
                _appendInfo('LINE',
                    `line ${index + 1} is a block header.\nUse Current Block instead. (cursor moved to next runnable)`,
                    '#e0c97a');
                _advanceCursor(_findNextRunnableLine(index), 'LINE');
                return;
            }
            // 들여쓰기 줄(블록 본문 일부)도 단독 실행 시 IndentationError 발생.
            // 들여쓰기를 제거해서 단독 statement로 실행 시도
            const dedented = line.replace(/^\s+/, '');

            const prompts = _extractInputCalls(dedented);
            let inputs = [];
            if (prompts.length > 0) {
                const collected = await _collectInputs(prompts);
                if (collected === null) return;
                inputs = collected;
            }
            _doRun(dedented, inputs, `LINE ${index + 1}`, 'single');
            // 실행 후 다음 실행 가능 줄로 이동
            _advanceCursor(_findNextRunnableLine(index), 'LINE');
        };

        // ── 현재 선택영역 정보 (text + 시작/끝 라인 1-based 표시용) ──
        function _getCurrentSelection() {
            const text = window.Editor?.getSelection?.() || '';
            if (!text) return { text: '', startLine: 0, endLine: 0, has: false };
            try {
                const v = window.Editor?.get?.();
                if (v) {
                    const { from, to } = v.state.selection.main;
                    const a = Math.min(from, to), b = Math.max(from, to);
                    const startLine = v.state.doc.lineAt(a).number;  // 1-based
                    const endLine   = v.state.doc.lineAt(b).number;
                    return { text, startLine, endLine, has: true };
                }
            } catch (e) { console.warn('[selection] view access failed:', e); }
            return { text, startLine: 0, endLine: 0, has: true };
        }

        // ── Current Block (선택영역 우선, 없으면 빈줄 기준 블록) ──
        window.runBlock = async () => {
            // 1) 선택영역 우선
            const sel = _getCurrentSelection();
            if (sel.has && sel.text.trim()) {
                console.log('[runBlock] selection L', sel.startLine, '~', sel.endLine, 'len:', sel.text.length);
                // 공통 들여쓰기 제거
                const lines = sel.text.split('\n');
                const nonBlank = lines.filter(l => l.trim());
                const minIndent = nonBlank.length
                    ? Math.min(...nonBlank.map(l => l.match(/^[\t ]*/)[0].length))
                    : 0;
                const dedented = minIndent > 0
                    ? lines.map(l => l.slice(minIndent)).join('\n')
                    : sel.text;

                const prompts = _extractInputCalls(dedented);
                let inputs = [];
                if (prompts.length > 0) {
                    const collected = await _collectInputs(prompts);
                    if (collected === null) return;
                    inputs = collected;
                }
                const label = (sel.startLine && sel.endLine)
                    ? (sel.startLine === sel.endLine
                        ? `SELECTION L${sel.startLine}`
                        : `SELECTION L${sel.startLine}-${sel.endLine}`)
                    : 'SELECTION';
                _doRun(dedented, inputs, label, 'block_echo');
                // 선택 끝(1-based) 다음 비빈줄로 이동, 선택은 자동 해제됨(setCursor가 anchor만 설정)
                if (sel.endLine > 0) {
                    _advanceCursor(_findNextBlockStart(sel.endLine - 1), 'SELECTION');
                }
                return;
            }

            // 2) 선택 없음 → 빈줄 기준 블록
            const { text, start, end, empty } = _getCurrentBlock();
            console.log('[runBlock] block lines', start + 1, '~', end + 1, 'len:', text.length);

            if (empty || !text.trim()) {
                _appendInfo('BLOCK', '(no block to run)', '#7a8a9a');
                return;
            }
            const lines = text.split('\n');
            const nonBlank = lines.filter(l => l.trim());
            const minIndent = Math.min(...nonBlank.map(l => l.match(/^[\t ]*/)[0].length));
            const dedented = minIndent > 0
                ? lines.map(l => l.slice(minIndent)).join('\n')
                : text;

            const prompts = _extractInputCalls(dedented);
            let inputs = [];
            if (prompts.length > 0) {
                const collected = await _collectInputs(prompts);
                if (collected === null) return;
                inputs = collected;
            }
            const label = (start === end) ? `BLOCK L${start + 1}` : `BLOCK L${start + 1}-${end + 1}`;
            _doRun(dedented, inputs, label, 'block_echo');
            // 다음 블록의 첫 줄로 이동
            _advanceCursor(_findNextBlockStart(end), 'BLOCK');
        };

        document.getElementById('btnRunCopy')?.addEventListener('click', async () => {
            const output = document.getElementById('runOutput');
            if (!output) return;
            const text = output.innerText || output.textContent || '';
            const btn = document.getElementById('btnRunCopy');
            const restore = (msg, color) => {
                if (!btn) return;
                const old = btn.textContent;
                const oldColor = btn.style.color;
                btn.textContent = msg;
                if (color) btn.style.color = color;
                setTimeout(() => { btn.textContent = old; btn.style.color = oldColor; }, 1100);
            };
            try {
                // execCommand 우선 (Samsung Browser user-gesture 호환)
                let copied = false;
                try {
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
                    document.body.appendChild(ta);
                    ta.focus();
                    ta.setSelectionRange(0, ta.value.length);
                    copied = document.execCommand('copy');
                    ta.remove();
                } catch (e) { /* fall through */ }
                if (!copied && navigator.clipboard?.writeText) {
                    await navigator.clipboard.writeText(text);
                }
                restore('copied', '#4caf50');
            } catch (e) {
                console.warn('[copy] failed:', e);
                restore('failed', '#f97583');
            }
        });
        document.getElementById('btnRunClear')?.addEventListener('click', () => {
            const output = document.getElementById('runOutput');
            if (output) output.innerHTML = '';
        });
        // btnRunClose: float_run.js에서 통합 관리
        // btnRunEdit: float_run.js에서 통합 관리
        // runPanel overlay-click: float_run.js에서 통합 관리

        // Fixed Focus 토글
        // 짧은=x고정(blue), 긴=x보정(amber) / 켜진상태 길게=모드전환
        _bindLongShort('btnFooterFocus',
            () => {
                if (window.NavFocus) {
                    NavFocus.toggle(true);
                    UIViewport.blockKeyboard();
                    const on = State.getModeF();
                    UI.showToast(on ? '🔍 Focus Lock ON' : '🔍 Focus Lock OFF', 800);
                    try { localStorage.setItem('usekit_focus', on ? '1' : '0'); } catch(e) {}
                }
            },
            () => {
                if (window.NavFocus) {
                    NavFocus.toggle(false);
                    UIViewport.blockKeyboard();
                    const on = State.getModeF();
                    UI.showToast(on ? '🔍 Focus Lock ON' : '🔍 Focus Lock OFF', 800);
                    try { localStorage.setItem('usekit_focus', on ? '1' : '0'); } catch(e) {}
                }
            }
        );

        // KU 버튼 — OS 키보드 토글 (단발: 올리기/내리기)
        _bind('btnFooterKeyboard', () => {
            if (UIViewport.isKbOpen()) {
                UIViewport.blockKeyboard();
            } else {
                UIViewport.allowKeyboard();
                setTimeout(() => { Editor.focus(); }, 80);
            }
            _syncButtonColors();
        });

        // 멀티커서 List 오버레이
        _bind('btnFooterMultiList', () => _toggleMultiListOverlay());
    }

    // ── 멀티커서 List 오버레이 ──────────────────────────────────
    let _multiListOpen = false;

    function _closeMultiListOverlay() {
        _multiListOpen = false;
        const el = document.getElementById('multiListOverlay');
        if (el) el.remove();
    }

    function _toggleMultiListOverlay() {
        if (_multiListOpen) { _closeMultiListOverlay(); return; }
        _multiListOpen = true;

        const ranges  = window.BlockState?.getRanges?.() || [];
        const mainIdx = window.BlockState?.getMainIdx?.() ?? 0;
        const view    = window.Editor?.get?.();

        const overlay = document.createElement('div');
        overlay.id = 'multiListOverlay';
        overlay.style.cssText = `
            position: fixed;
            bottom: calc(var(--footer-h, 2.8rem) + 4px);
            right: 8px;
            min-width: 220px;
            max-width: 90vw;
            max-height: 50vh;
            overflow-y: auto;
            background: var(--bg-surface);
            border: 1px solid var(--ac-purple);
            border-radius: var(--r-md);
            z-index: 500;
            box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        `;

        if (ranges.length === 0) {
            overlay.innerHTML = '<div style="padding:12px;color:var(--tx-dim);font-size:0.85rem;">No cursors</div>';
        } else {
            ranges.forEach((r, i) => {
                const row = document.createElement('div');
                const isMain = i === mainIdx;
                const ln = view ? view.state.doc.lineAt(r.head).number : '?';
                const preview = view ? view.state.doc.lineAt(r.head).text.slice(0, 30) : '';
                row.style.cssText = `
                    display:flex; align-items:center; gap:8px;
                    padding: 8px 12px;
                    cursor:pointer;
                    border-bottom: 1px solid var(--bd);
                    background: ${isMain ? 'var(--ac-purple-bg)' : 'transparent'};
                `;
                row.innerHTML = `
                    <span style="color:var(--ac-purple);font-size:0.75rem;min-width:1.2rem;">C${i+1}</span>
                    <b style="color:${isMain ? 'var(--ac-purple)' : 'var(--tx-dim)'};font-size:0.8rem;min-width:2.5rem;">L${ln}</b>
                    <span style="color:var(--tx-muted);font-size:0.8rem;font-family:monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${preview.replace(/</g,'&lt;')}</span>
                `;
                row.addEventListener('click', () => {
                    window.BlockState?.setMainIdx?.(i);
                    window.BlockState?.render?.();
                    if (view) {
                        view.dispatch({ scrollIntoView: true, selection: { anchor: r.head } });
                        view.focus();
                    }
                    _closeMultiListOverlay();
                });
                overlay.appendChild(row);
            });
        }

        // 바깥 터치로 닫기
        setTimeout(() => {
            document.addEventListener('touchstart', function _onOutside(e) {
                if (!overlay.contains(e.target) && e.target.id !== 'btnFooterMultiList') {
                    _closeMultiListOverlay();
                    document.removeEventListener('touchstart', _onOutside);
                }
            }, { passive: true });
        }, 100);

        document.body.appendChild(overlay);
    }

    function resyncEditorButtons() {
        _updateWrapBtnState();
        _updateLineNumBtn(Editor.getOption('lineNumbers') !== false);
        _updateMore2Indicator();
    }

    function _updateLineNumBtn(on) {
        const btn = document.getElementById('btnLineInfo');
        if (!btn) return;
        const s = getComputedStyle(document.documentElement);
        btn.style.background  = on ? s.getPropertyValue('--ac-active-bg').trim() : '';
        btn.style.borderColor = on ? s.getPropertyValue('--ac-active-bd').trim() : '';
        btn.style.color       = on ? s.getPropertyValue('--ac-active-tx').trim() : '';
    }

    function _updateLKBtn(on) {
        const btn = document.getElementById('btnFooterLock');
        if (!btn) return;
        const s = getComputedStyle(document.documentElement);
        btn.style.background  = on ? s.getPropertyValue('--ac-purple-bg').trim() : '';
        btn.style.borderColor = on ? s.getPropertyValue('--ac-purple-bd').trim() : '';
        btn.style.color       = on ? s.getPropertyValue('--ac-purple').trim()    : '';
    }

    // 블럭모드에서 OS 키보드만 토글 (블럭 상태 유지) — 좌쉬프트 전용

    // 두 버튼 색상+캡션 일괄 동기화 — 항상 이 함수로 처리
    function _syncButtonColors() {
        const lkBtn = document.getElementById('btnFooterLock');
        const kuBtn = document.getElementById('btnFooterKeyboard');
        if (!lkBtn || !kuBtn) return;
        const s = getComputedStyle(document.documentElement);
        // LK 상태만 반영 (input/edit 없음)
        const lkOn = State.getLK() ?? false;
        lkBtn.textContent = '⌨';
        kuBtn.textContent = '⌨';
        lkBtn.style.background  = lkOn ? s.getPropertyValue('--ac-purple-bg').trim() : '';
        lkBtn.style.borderColor = lkOn ? s.getPropertyValue('--ac-purple-bd').trim() : '';
        lkBtn.style.color       = lkOn ? s.getPropertyValue('--ac-purple').trim()    : '';
        kuBtn.style.background = kuBtn.style.borderColor = kuBtn.style.color = '';
        UIStats.updateKUButton(false);
        // Fav 버튼 동기화
        const favBtn = document.getElementById('btnFooterFav');
        if (favBtn) {
            const slot = window.SlotManager?.getCurrentSlot?.();
            if (slot) {
                try {
                    const favSet = new Set(JSON.parse(localStorage.getItem('usekit_fav_slot') || '[]'));
                    favBtn.textContent = favSet.has(slot) ? '★' : '☆';
                } catch { favBtn.textContent = '☆'; }
            } else {
                favBtn.textContent = '☆';
            }
        }
    }
    function _bindHeaderButtons() {
        // SAVE label: short tap → save, long tap → save-as popup
        _bindLongShort('saveLabel',
            () => SlotManager.save({ silent: false }),   // short
            () => SlotManager.openSavePopup()            // long
        );
        _bind('metaFileDisplay', () => SlotManager.openSavePopup());

        // LOC label: short tap → toggle loc/slot view, long tap → load popup
        _bindLongShort('locLabel',
            () => _toggleLocView(),                      // short
            () => SlotManager.openLoadPopup()            // long
        );

        // metaLoc: tap → 전체 경로 팝업
        (function () {
            const el = document.getElementById('metaLoc');
            if (!el || el.dataset.locBound) return;
            el.dataset.locBound = '1';
            el.addEventListener('click', () => {
                const fullPath = el.dataset.fullpath || el.value;
                if (!fullPath) return;
                // 경로 전용 팝업 오버레이
                let overlay = document.getElementById('_locPathPopup');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = '_locPathPopup';
                    overlay.style.cssText = [
                        'position:fixed','top:0','left:0','right:0','bottom:0',
                        'background:rgba(0,0,0,0.55)','z-index:9999',
                        'display:flex','align-items:center','justify-content:center',
                        'padding:1.5rem',
                    ].join(';');
                    overlay.innerHTML = `
                        <div id="_locPathBox" style="background:var(--bg-base,#fff);border-radius:14px;
                             padding:1.2rem 1rem 0.8rem;max-width:92vw;min-width:60vw;
                             word-break:break-all;font-size:0.85rem;
                             color:var(--tx-primary,#111);line-height:1.6;
                             box-shadow:0 4px 24px rgba(0,0,0,0.35);">
                          <div style="opacity:0.5;font-size:0.7rem;margin-bottom:0.5rem;font-weight:600;letter-spacing:0.05em;">FULL PATH</div>
                          <div id="_locPathText" style="user-select:all;-webkit-user-select:all;
                               word-break:break-all;margin-bottom:0.9rem;"></div>
                          <div style="display:flex;gap:0.5rem;justify-content:flex-end;">
                            <button id="_locPathCopy" style="padding:0.45rem 1.1rem;border-radius:8px;
                              border:none;background:#007aff;color:#fff;font-size:0.85rem;
                              font-weight:600;cursor:pointer;">Copy</button>
                            <button id="_locPathOk" style="padding:0.45rem 1.1rem;border-radius:8px;
                              border:none;background:#e5e5ea;color:#111;font-size:0.85rem;
                              font-weight:600;cursor:pointer;">OK</button>
                          </div>
                        </div>`;
                    overlay.addEventListener('click', (e) => {
                        if (!document.getElementById('_locPathBox')?.contains(e.target))
                            overlay.style.display = 'none';
                    });
                    document.getElementById('_locPathOk')?.addEventListener('click', () => {
                        overlay.style.display = 'none';
                    });
                    document.getElementById('_locPathCopy')?.addEventListener('click', () => {
                        const txt = document.getElementById('_locPathText')?.textContent || '';
                        window._usekitClipCopy?.(txt);
                        const btn = document.getElementById('_locPathCopy');
                        if (btn) { btn.textContent = 'Copied!'; setTimeout(() => { btn.textContent = 'Copy'; }, 1500); }
                    });
                    document.body.appendChild(overlay);
                }
                document.getElementById('_locPathText').textContent = fullPath;
                overlay.style.display = 'flex';
                // 3초 후 자동 닫힘
                clearTimeout(overlay._timer);
                overlay._timer = setTimeout(() => { overlay.style.display = 'none'; }, 3000);
            });
        })();

        // metaFile: blur/Enter → rename
        (function () {
            const el = document.getElementById('metaFile');
            if (!el || el.dataset.hdrBound) return;
            el.dataset.hdrBound = '1';
            const _doRename = () => {
                const name = el.value.trim();
                if (name) SlotManager.renameCurrentSlot(name, { silent: false });
            };
            el.addEventListener('blur',    _doRename);
            el.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); _doRename(); Editor.focus(); } });
        })();

        // metaFunc: tap → toggle local ↔ usekit (ping으로 termux 확인)
        (function () {
            const el = document.getElementById('metaFunc');
            if (!el || el.dataset.hdrBound) return;
            el.dataset.hdrBound = '1';
            el.addEventListener('click', async () => {
                const cur = el.textContent.trim().toLowerCase();

                // usekit → local: 무조건 허용
                if (cur === 'usekit') {
                    SlotManager.setActiveStorage('local');
                    return;
                }

                // local → usekit: ping으로 termux 확인
                el.textContent = '...';
                el.disabled = true;
                try {
                    const r = await fetch('/api/ping', { signal: AbortSignal.timeout(2000) });
                    const j = await r.json();
                    if (!j?.ok) throw new Error('no server');

                    // ping 응답 전체 캐시 → tab_usekit.js가 rootPath/usekitBase 읽어감
                    window._usekitPing = j;
                    SlotManager.setUsekitBase(j.usekit_base || '');

                    // usekitPath가 없으면 기본 경로 자동 설정 (ping의 rel_dir 기준)
                    const info = SlotManager.getCurrentSlotInfo() || {};
                    if (!info.usekitPath) {
                        const relDir = (j.default_usekit_rel_dir || '_tmp').replace(/\/?$/, '');
                        const fname  = info.fileName || 'scratch';
                        const ext    = document.getElementById('metaExt')?.value?.trim() || 'txt';
                        SlotManager.setUsekitPathForActive(`/${relDir}/${fname}.${ext}`);
                    }
                    SlotManager.setActiveStorage('usekit');
                } catch(e) {
                    SlotStorage.toast('Termux not connected');
                    el.textContent = 'local';
                } finally {
                    el.disabled = false;
                }
            });
        })();

        // Brand toggle → 메뉴 토글 (열면 panel-buttons 노출, 다시 누르면 nav-hidden)
        // 좌상단 브랜드 → 메뉴 토글
        _bind('brand-toggle', () => {
            const next = (_ui === 'menu') ? 'hidden' : 'menu';
            _uiGo(next);
            window.UIStats?.updateKUButton?.(false);
            window.SlotManager?.saveUIState?.();
        });

        // 우하단 기어 → nav-hidden 토글 (도구 숨기기/펼치기)
        _bind('btnFooterSettings', () => {
            const app = document.querySelector('.editor-app');
            if (!app) return;
            const next = app.classList.contains('nav-hidden') ? 'quick' : 'hidden';
            _uiGo(next);
            window.SlotManager?.saveUIState?.();
            UIStats.updateKUButton(false);
        });

        // 우상단 기어 → 퀵 토글
        _bind('btnHeaderSettings', () => {
            const next = (_ui === 'quick') ? 'hidden' : 'quick';
            _uiGo(next);
            window.UIStats?.updateKUButton?.(false);
            window.SlotManager?.saveUIState?.();
        });

        // 약식 패널 전체: OS키 내려진 상태에서 버튼 터치 시 OS키 올라오기 차단
        const _qnPanel = document.querySelector('.swipe-panel.panel-quick');
        if (_qnPanel) {
            _qnPanel.addEventListener('touchstart', () => {
                if (!window.UIViewport?.isKbOpen?.()) window.UIViewport?.blockKeyboard?.();
            }, { passive: true });
        }

        // 약식 패널 — 뒤 4개 셋트 정의
        const _qnSets = () => ({
            default: ['NEW',   'LOAD',  'SAVE AS', 'CLOSE'],
            ctrl:    ['ALL',   'COPY',  'PASTE','LIST'],
            alt:     ['FIRST', 'LAST',  'BACK', 'NEXT'],
            shiftr:  ['⌫',    'SPACE', 'ENTER','DEL' ],
        });

        // 모디파이어별 컬러 클래스
        const _qnColors = {
            default: { mod: '',              set: '' },
            ctrl:    { mod: 'qn-mod-active', set: 'qn-set-ctrl'   },
            alt:     { mod: 'qn-mod-alt',    set: 'qn-set-alt'    },
            shiftr:  { mod: 'qn-mod-shiftr', set: 'qn-set-shiftr' },
        };
        const _qnModIds = { ctrl:'qnCTRL', alt:'qnALT' };
        // ────────────────────────────────────────────────────────────
        // 상태 변수 (퀵패널 셋트 체계)
        // ────────────────────────────────────────────────────────────
        // _qnSet: 잠금된 셋트. 가능 값: 'default' | 'shiftr'
        //   - 'default': 뒤 4버튼 = NEW/LOAD/SAVE AS/CLOSE (또는 SHIFT_L ON 시 슬롯 네비)
        //   - 'shiftr':  뒤 4버튼 = ⌫/SPACE/ENTER/DEL (SHIFT_R ■로 토글)
        //   (참고) 과거엔 'ctrl'/'alt' 잠금도 있었으나 TAB 잠금 기능 제거로 폐기됨.
        //          ctrl/alt는 이제 _modCtrl/_modAlt pending으로만 존재.
        //
        // _modCtrl / _modAlt: 모디파이어 pending 플래그 (토글식)
        //   SHIFT_L OFF: 상호배타 (나중 누른 쪽이 이김)
        //   SHIFT_L ON:  독립 토글 (둘 다 true면 멀티 진입 트리거)
        //
        // _qnShift: SHIFT_L ON/OFF 플래그 (SHIFT_R = _qnSet==='shiftr'와 별개)
        // ────────────────────────────────────────────────────────────
        let _qnSet   = 'default';

        let _modCtrl = false;
        let _modAlt  = false;
        let _qnShift = false;
        window._qnShift = false;
        let _qnShiftLocked = false;    // 롱클릭 고정 모드
        let _cursorMode = false;       // true=CUR(커서모드/쉬프트OFF), false=BLK(블럭모드/쉬프트ON)
        // 멀티블럭 모드. 진입 경로:
        //   1. SHIFT_L + TAB         (_bind qnTAB)
        //   2. SHIFT_L + CTRL + ALT  (_qnMod — SHIFT ON 상태에서 둘 다 켜지는 순간)
        //   3. 기타 내부 재진입 (ESC 단계적 초기화 경로 등)
        let _multiMode = false;
        let _mLock = false;             // M-LOCK 온오프
        let _mLockPending = false;      // ESC 후 다음 클릭에서 M-LOCK ON 대기
        let _checkedHeads = new Set(); // CHECK된 커서 head 위치들
        let _colOffsets   = new Map(); // line → delta  (BE 오프셋)
        let _colBsOffsets = new Map(); // line → gamma  (BS 오프셋, CUR모드에서만 업데이트)
        let _checkMode = false;        // CHECK ON/OFF
        // _qnPending: 현재 활성화된 모디파이어 셋 반환 (ctrl / alt / null)
        // 역할:
        //   1. S1~S4 뒤 4버튼 동작 분기 (_qnExec): pending에 따라 ctrl(ALL/COPY/...), alt(FIRST/LAST/...) 실행
        //   2. 방향키/HOME/END 네비게이션 수정자: wordLeft, jumpParagraph, shiftIndent 등
        //   3. 뒤 4버튼 라벨 + 컬러 (_qnApplyLabels): pending 셋트로 렌더
        //
        // 주의:
        //   - 셋트 "잠금"(TAB 눌러 고정) 기능은 제거됨. CTRL+TAB=Copy pill, ALT+TAB=Menu pill.
        //   - SHIFT_L OFF: ctrl/alt 상호배타 (_qnMod 참조). 나중 누른 쪽이 이김.
        //   - SHIFT_L ON:  ctrl/alt 독립 토글 가능. 둘 다 true면 멀티 진입 트리거.
        //   - ctrl 우선 반환은 SHIFT_L ON에서 둘 다 켜진 순간(멀티 진입 직전)에만 의미 있음.
        //   - 멀티모드에선 _modCtrl/_modAlt가 M-LOCK/CHECK 버튼으로 재사용되므로 항상 null.
        function _qnPending() {
            if (_multiMode) return null;
            if (_modCtrl) return 'ctrl';
            if (_modAlt)  return 'alt';
            return null;
        }

        // Copy pill이 열려있을 때 CTRL pending의 라벨/S1~S4 동작을 default로 중화.
        //   의도: Copy pill이 ALL/COPY/PASTE/LIST 기능을 대체하므로 퀵에 중복 표시 방지.
        //   영향 범위: 라벨(_qnApplyLabels), S1~S4 액션(_qnExec) 두 경로만.
        //   네비게이션 수정자(_qnPending 직접 참조: wordLeft/HOME/END mod 등)는 영향 없음.
        //   결과: Copy pill 열린 채 CTRL 누르면 네비게이션은 ctrl 동작, 퀵 라벨은 default(NEW/LOAD/...).
        function _isClipPillOpen() {
            const el = document.getElementById('floatClipTool');
            return !!(el && el.style.display === 'flex');
        }
        function _qnSetForLabel(name) {
            if (name === 'ctrl' && !_multiMode && _isClipPillOpen()) return 'default';
            return name;
        }

        // 모디파이어 버튼(qnCTRL/qnALT)과 qnTAB에 붙은 mod 컬러 클래스 일괄 제거.
        //   _modCtrl/_modAlt를 false로 만든 직후 호출 (TAB 트리거 분기 등).
        //   이후 _qnApplyLabels를 호출하면 현재 플래그 기준으로 다시 정확히 렌더됨.
        function _qnClearModClasses() {
            const cls = ['qn-mod-active','qn-mod-alt','qn-mod-shiftr'];
            Object.values(_qnModIds).forEach(id => {
                const btn = document.getElementById(id);
                if (btn) cls.forEach(c => btn.classList.remove(c));
            });
            const tabBtn = document.getElementById('qnTAB');
            if (tabBtn) cls.forEach(c => tabBtn.classList.remove(c));
        }

        function _qnApplyLabels(name) {
            // shiftr 모드 중엔 어떤 name이 들어와도 캡션/스타일은 shiftr 기준 유지
            if (_qnSet === 'shiftr') name = 'shiftr';
            // Copy pill 열려있으면 ctrl 라벨/셋트 → default로 중화 (네비는 영향 없음)
            name = _qnSetForLabel(name);
            const sets = _qnSets();
            const labels = sets[name] || sets.default;
            const allModCls = ['qn-mod-active','qn-mod-alt','qn-mod-shiftr'];
            const allSetCls = ['qn-set-ctrl','qn-set-alt','qn-set-shiftr'];
            const color = _qnColors[name] || _qnColors.default;
            const homeBtn = document.getElementById('qnHOME');
            const endBtn  = document.getElementById('qnEND');
            if (homeBtn) homeBtn.classList.remove('qn-mod-active');
            if (endBtn)  endBtn.classList.remove('qn-mod-active');

            // 뒤 4개 캡션 + 셋트 컬러
            ['qnS1','qnS2','qnS3','qnS4'].forEach((id, i) => {
                const btn = document.getElementById(id);
                if (!btn) return;
                let label = labels[i];
                if (_qnSet === 'shiftr') label = ['⌫','SPACE','ENTER','DEL'][i];
                else if (!_multiMode && name === 'default' && _qnShift && _qnSet !== 'shiftr') label = ['PREV','NEXT','T-SLOT','E-SLOT'][i];
                btn.textContent = label;
                allSetCls.forEach(c => btn.classList.remove(c));
                if (_qnSet === 'shiftr') btn.classList.add('qn-set-shiftr');
                else if (color.set) btn.classList.add(color.set);
            });

            // 모디파이어 키 컬러 — 각 플래그 독립적으로 표시
            Object.entries(_qnModIds).forEach(([key, id]) => {
                const btn = document.getElementById(id);
                if (!btn) return;
                allModCls.forEach(c => btn.classList.remove(c));
                if (_multiMode) {
                    // ALT(CHECK)는 초록 유지, CTRL(M-LOCK)은 아래에서 별도 처리
                    if (key === 'alt') btn.classList.add(_qnColors.alt.mod);
                    return;
                }
                if (key === 'ctrl' && _modCtrl) btn.classList.add(_qnColors.ctrl.mod);
                if (key === 'alt'  && _modAlt)  btn.classList.add(_qnColors.alt.mod);
            });

            // MULTI 상태: CTRL→M-LOCK, ALT→CHECK 캡션 + 클래스
            const ctrlBtn = document.getElementById('qnCTRL');
            const altBtn  = document.getElementById('qnALT');
            if (_multiMode) {
                if (ctrlBtn) {
                    ctrlBtn.textContent = 'M-LOCK';
                    ctrlBtn.classList.remove('qn-mlock-on', 'qn-mlock-off');
                    ctrlBtn.classList.add(_mLock ? 'qn-mlock-on' : 'qn-mlock-off');
                }
                if (altBtn) {
                    altBtn.textContent = 'CHECK';
                    altBtn.classList.remove('qn-check-on', 'qn-check-off');
                    altBtn.classList.add(_checkMode ? 'qn-check-on' : 'qn-check-off');
                }
            } else {
                if (ctrlBtn) {
                    ctrlBtn.textContent = 'CTRL';
                    ctrlBtn.classList.remove('qn-mlock-on', 'qn-mlock-off');
                }
                if (altBtn) {
                    altBtn.textContent = 'ALT';
                    altBtn.classList.remove('qn-check-on', 'qn-check-off');
                }
            }

            // SHIFT_L: multiMode면 _cursorMode, 아니면 _qnShift 기준
            const shiftLBtn = document.getElementById('qnSHIFT_L');
            if (shiftLBtn) {
                shiftLBtn.classList.toggle('qn-mod-active',
                    _multiMode ? !_cursorMode : _qnShift);
            }

            // TAB — multiMode면 BLK/CUR. 퀵일반에서는 pending 컬러 힌트 없음 (잠금 기능 제거).
            const tabBtn = document.getElementById('qnTAB');
            if (tabBtn) {
                if (_multiMode) {
                    // CHECK ON이면 A/D, 아니면 MULTI/CUR
                    if (_checkMode) {
                        // CHECK 모드: ON/OFF 고정 — 건드리지 않음
                    } else {
                        tabBtn.textContent = _cursorMode ? 'CUR' : 'BLK';
                    }
                } else {
                    allModCls.forEach(c => tabBtn.classList.remove(c));
                    // pending 컬러 힌트 제거 — ALT/CTRL+TAB으로 셋트 잠금하는 기능이 사라졌으므로
                    // 녹색/파랑 힌트가 오히려 잘못된 기대를 유발. 기본 스타일만 사용.
                    tabBtn.textContent = (_qnShift && !_qnPending()) ? 'MULTI' : 'TAB';
                }
            }
            // HOME / END 방향 힌트 — V2: _mainIdx 위치 기준 (CUR/CHECK 제외)
            if (_multiMode && !_checkMode && !_cursorMode) {
                const BS = window.BlockState;
                if (BS) {
                    const ranges = BS.getRanges();
                    const doc = window.Editor?.get?.()?.state.doc;
                    if (ranges.length > 1 && doc) {
                        const headLines = ranges.map(r => doc.lineAt(r.head).number - 1);
                        const topLine   = Math.min(...headLines);
                        const botLine   = Math.max(...headLines);
                        const mainLine  = headLines[Math.min(BS.getMainIdx(), headLines.length - 1)];
                        if (mainLine === topLine) homeBtn?.classList.add('qn-mod-active');
                        else if (mainLine === botLine) endBtn?.classList.add('qn-mod-active');
                    }
                }
            }

            // ■ 버튼: _qnSet=shiftr이면 항상 ON 표시
            document.getElementById('qnSHIFT_R')?.classList.toggle('qn-mod-shiftr', _qnSet === 'shiftr');
            // CHECK/M-LOCK 모드: cm-editor에 클래스 토글 (물방울 핸들 억제)
            document.querySelector('.cm-editor')?.classList.toggle('check-mode', !!(_multiMode && _checkMode));
            document.querySelector('.cm-editor')?.classList.toggle('mlock-mode', !!(_multiMode && _mLock));
        }

        // 방향키 이동 후 HOME/END 힌트만 갱신 (캡션 건드리지 않음)
        function _qnUpdateDirHint() {
            const homeBtn = document.getElementById('qnHOME');
            const endBtn  = document.getElementById('qnEND');
            if (homeBtn) homeBtn.classList.remove('qn-mod-active');
            if (endBtn)  endBtn.classList.remove('qn-mod-active');
            if (_multiMode && !_checkMode && !_cursorMode) {
                // V2: _mainIdx 위치 기준 — 탑이면 HOME, 바텀이면 END 점등
                const BS = window.BlockState;
                if (!BS) return;
                const ranges = BS.getRanges();
                if (ranges.length <= 1) return;
                const doc = window.Editor?.get?.()?.state.doc;
                if (!doc) return;
                const headLines = ranges.map(r => doc.lineAt(r.head).number - 1);
                const topLine   = Math.min(...headLines);
                const botLine   = Math.max(...headLines);
                const mainLine  = headLines[Math.min(BS.getMainIdx(), headLines.length - 1)];
                if (mainLine === topLine) homeBtn?.classList.add('qn-mod-active');
                else if (mainLine === botLine) endBtn?.classList.add('qn-mod-active');
            }
        }

        // 뒤 4개 버튼 실행 후 — 1회성이면 기본 셋트로 복귀
        function _qnGuardScroll() {
            if (!window.UIViewport?.isKbOpen?.()) return;
            const view = window.Editor?.get?.();
            if (!view) return;
            let isEmpty = false;
            try { isEmpty = view.state.doc.lineAt(view.state.selection.main.head).length === 0; } catch(e) {}
            if (isEmpty) window.UIViewport?.triggerScrollGuard?.();
        }

        function _qnAfterAction() {
            if (_qnPending() === 'ctrl' && _qnSet !== 'shiftr') {
                _modCtrl = false;
                // CTRL 액션 후 1회용 Shift도 자동 해제 (locked 제외)
                if (_qnShift && !_qnShiftLocked && !_multiMode) _qnSetShift(false);
                _qnApplyLabels(_qnSet);
            }
            _qnGuardScroll();
        }

        // 모디파이어 탭
        // 쉬프트 OFF: 상호배타 (나중 누른 게 이김)
        // 쉬프트 ON:  독립 토글 (CTRL/ALT 동시 가능 → 멀티블럭모드)
        function _isBlockMode() { return _multiMode; }
        window._uiIsBlockMode = _isBlockMode;
        window._uiIsMLock = () => _mLock;
        window._uiIsMLockPending = () => _mLockPending;
        window._uiMLockOff = () => { _mLock = false; _mLockPending = false; window._uiDetachMLockBlock?.(); _qnApplyLabels(_qnSet); };
        window._uiMLockOn  = () => { _mLock = true; _mLockPending = false; window._uiAttachMLockBlock?.(); _qnApplyLabels(_qnSet); };
        window._uiIsCheckMode = () => _checkMode;
        window._uiGetCheckedHeads = () => _checkedHeads;
        window._uiGetColOffsets   = () => _colOffsets;
        window._uiGetColBsOffsets = () => _colBsOffsets;
        window._uiIsCurMode = () => _cursorMode;
        window._uiIsShiftMode = () => _qnShift;
        // Copy pill 등 외부에서 pill open/close 후 퀵 라벨 재갱신 트리거
        window._uiRefreshQnLabels = () => _qnApplyLabels(_qnSet);

        // OS 엔터 — 가상 ENTER(idx=2)와 동일
        window._osEnter = function() {
            const _isCheck = window.BlockState?.isCheckMode?.() ?? false;
            const _isSingle = !_multiMode || (window.BlockState?.getRanges?.()?.length ?? 1) === 1;

            if (_isSingle) {
                window.Editor?.replaceSelection?.('\n'); // 단일: Shift ON/OFF 무관 항상 엔터
                return;
            }
            const ch = _cursorMode ? '\n' : ' ';
            if (_isCheck) {
                window.NavBlockV2?.checkEdit?.('insert', ch);
                return;
            }
            // 멀티: 가상 ENTER BLK와 동일 — replaceSelection으로 CM6 위임
            window.Editor?.replaceSelection?.(ch);
            window.BlockState?.render?.();
        };

        // OS 백스페이스 — 가상 백스(idx=0)와 동일 분기
        window._osBackspace = function() {
            const _isCheck = window.BlockState?.isCheckMode?.() ?? false;
            const _isSingle = !_multiMode || (window.BlockState?.getRanges?.()?.length ?? 1) === 1;

            // 단일: 무조건 CM6 위임 (Shift ON/OFF 무관)
            if (_isSingle) {
                window.Editor?.execCommand?.('delCharBefore');
                return;
            }
            if (_isCheck) {
                window.NavBlockV2?.checkEdit?.('delBefore');
                return;
            }
            // 멀티 직접 구현: CUR=엔터 허용(라인합치기), BLK=엔터 보호
            {
                const v = window.Editor?.get?.();
                if (!v) return;
                const doc = v.state.doc;
                const ranges = Array.from(v.state.selection.ranges);
                const changes = [];
                for (const r of [...ranges].reverse()) {
                    const lineFrom = doc.lineAt(r.head).from;
                    if (r.head < r.anchor) {
                        // 역방향: head 앞 1글자
                        if (r.head > lineFrom) changes.push({ from: r.head - 1, to: r.head });
                        else if (_cursorMode && r.head > 0) changes.push({ from: r.head - 1, to: r.head });
                    } else if (r.anchor < r.head) {
                        // 정방향 음영: 음영 삭제
                        changes.push({ from: r.anchor, to: r.head });
                    } else {
                        // 커서: head 앞 1글자
                        if (r.head > lineFrom) changes.push({ from: r.head - 1, to: r.head });
                        else if (_cursorMode && r.head > 0) changes.push({ from: r.head - 1, to: r.head });
                    }
                }
                if (changes.length) {
                    v.dispatch({ changes });
                    requestAnimationFrame(() => {
                        const v2 = window.Editor?.get?.();
                        if (!v2) return;
                        const seen = new Set();
                        const specs = [];
                        for (const r of Array.from(v2.state.selection.ranges)) {
                            const lineNum = v2.state.doc.lineAt(r.head).number;
                            if (seen.has(lineNum)) continue;
                            seen.add(lineNum);
                            specs.push({ anchor: r.anchor, head: r.head });
                        }
                        window.BlockState?.dispatch?.(specs, 0);
                        window.BlockState?.render?.();
                        window.Editor?.focus?.();
                    });
                }
            }
        };

        function _clearMultiLineState() {
            _checkedHeads.clear();
            _colOffsets.clear();
            _colBsOffsets.clear();
            window.NavBlock?._resetCheckPointer?.();
            window.NavBlock?._setCheckAnchorTemplate?.(null);
            window.NavBlock?.clearBlockSnapshots?.(); // 멀티모드 위치 히스토리 초기화
        }
        window._uiClearColOffsets = () => { _clearMultiLineState(); }; // 전체 multiLineState 초기화 (colOffsets/BsOffsets/checkedHeads/checkPointer)

        function _resetMultiAnchorTo(pos) {
            if (!pos) return;
            window.State?.setBS?.(pos);
            window.State?.setBE?.(pos);
            window.Editor?.clearSelection?.();
            window.Editor?.setCursor?.(pos);
        }

        function _resetMultiForReanchor() {
            _checkMode = false;
            window.BlockState?.setCheckMode?.(false);
            // BS 라인의 colBsOffsets(gamma) 기준으로 한 점 결정
            const bsSnap = window.State?.getBS?.();
            const bsCh   = (bsSnap && _colBsOffsets.has(bsSnap.line))
                           ? _colBsOffsets.get(bsSnap.line)
                           : bsSnap?.ch;
            const cur    = bsSnap ? { line: bsSnap.line, ch: bsCh ?? bsSnap.ch }
                                  : window.Editor?.getCursor?.();
            _clearMultiLineState();
            window._uiDetachMLockBlock?.();
            window.NavBlock?.clearColumnOverlay?.();
            _resetMultiAnchorTo(cur);
            return cur;
        }
        // BS/BE 범위 밖 라인을 checkedHeads + colOffsets + colBsOffsets 에서 모두 정리
        function _trimMultiLineState() {
            const bs = window.State?.getBS?.();
            const be = window.State?.getBE?.();
            if (!bs || !be) return;
            const fromLine = Math.min(bs.line, be.line);
            const toLine   = Math.max(bs.line, be.line);
            for (const l of [..._checkedHeads]) {
                if (l < fromLine || l > toLine) _checkedHeads.delete(l);
            }
            for (const l of [..._colOffsets.keys()]) {
                if (l < fromLine || l > toLine) _colOffsets.delete(l);
            }
            for (const l of [..._colBsOffsets.keys()]) {
                if (l < fromLine || l > toLine) _colBsOffsets.delete(l);
            }
        }

        // CHECK OFF: 유효 라인 범위만 남기고 BS/BE를 실제 주소로 동기화
        function _trimCheckoutToLastEffective() {
            const bs = window.State?.getBS?.();
            const be = window.State?.getBE?.();
            if (!bs || !be) return null;

            const forward = be.line >= bs.line;
            const fromLine = Math.min(bs.line, be.line);
            const toLine   = Math.max(bs.line, be.line);
            const validLines = [];

            for (let l = fromLine; l <= toLine; l++) {
                if (_checkedHeads.has(l)) continue;
                if (_colOffsets.has(l) || _colBsOffsets.has(l) || l === bs.line || l === be.line) {
                    validLines.push(l);
                }
            }
            if (!validLines.length) return null;

            const startLine = Math.min(...validLines);
            const endLine   = Math.max(...validLines);

            for (const l of [..._checkedHeads]) {
                if (l < startLine || l > endLine) _checkedHeads.delete(l);
            }
            for (const l of [..._colOffsets.keys()]) {
                if (l < startLine || l > endLine) _colOffsets.delete(l);
            }
            for (const l of [..._colBsOffsets.keys()]) {
                if (l < startLine || l > endLine) _colBsOffsets.delete(l);
            }

            const nextBSLine = forward ? startLine : endLine;
            const nextBELine = forward ? endLine : startLine;
            const nextBS = {
                line: nextBSLine,
                ch: _colBsOffsets.get(nextBSLine) ?? bs.ch,
            };
            const nextBE = {
                line: nextBELine,
                ch: _colOffsets.get(nextBELine) ?? be.ch,
            };

            window.State?.setBS?.(nextBS);
            window.State?.setBE?.(nextBE);
            return { bs: nextBS, be: nextBE };
        }
        window._uiTrimCheckedHeads   = _trimMultiLineState;
        window._uiTrimCheckoutToLastEffective = _trimCheckoutToLastEffective;

        function _enterMultiMode() {
            _multiMode = true;
            _modCtrl = true;
            _modAlt  = true;
            _qnSet = 'shiftr';
            // _cursorMode 항상 리셋 — ESC/재진입 시 BLK 상태로 복귀
            _cursorMode = false;
            window.BlockState?.setCursorMode?.(false);
            // 가상 오프셋 초기화 — 이전 M-LOCK 상태 잔류 방지
            window.NavBlockV2?.mlockClear?.();
            const tabBtn = document.getElementById('qnTAB');
            if (tabBtn) {
                tabBtn.textContent = 'RESET';
                tabBtn.classList.add('qn-multi');
            }
            const shiftBtn = document.getElementById('qnSHIFT_L');
            if (shiftBtn) shiftBtn.classList.add('qn-mod-active');
            // V2: BlockState 초기화 (CM6 커서 기준)
            window.BlockState?.enterMulti?.();
            // BLK OFF 오버레이 표시 (body 직속 floatBlkTool pill 제어)
            document.body.classList.add('qn-multi-on-active');
            _qnApplyLabels(_qnSet);
            _updateMarkOverlay();
            // 멀티 진입 직후 물방울(OS 커서 핸들) 즉시 해제 — 커서 위치는 유지
            // touchend 후 남아있던 물방울이 멀티 진행 중 계속 따라다니는 문제 방지
            try {
                const _v = window.Editor?.get?.();
                if (_v && _v.hasFocus && _v.state.selection.ranges.length === 1) {
                    const _sel = _v.state.selection.main;
                    if (_sel.anchor === _sel.head) {
                        const _docLen = _v.state.doc.length;
                        if (_docLen === 0) return;
                        const _delta = _sel.head > 0 ? -1 : 1;
                        _v.dispatch({ selection: { anchor: _sel.head + _delta, head: _sel.head + _delta } });
                        requestAnimationFrame(() => {
                            _v.dispatch({ selection: { anchor: _sel.head, head: _sel.head } });
                        });
                    }
                }
            } catch (e) {}
        }

        function _exitMultiMode() {
            _multiMode = false;
            _cursorMode = false;
            _mLock        = false;
            _mLockPending = false;
            window._uiDetachMLockBlock?.();
            _checkMode = false;
            _clearMultiLineState();
            // V2: BlockState 종료 + ghost + mlock 초기화
            window.BlockState?.exitMulti?.();
            window.NavBlockV2?.clearGhost?.();
            window.NavBlockV2?.mlockClear?.();
            window._imeSnap = null; // IME 백업 초기화
            _modCtrl = false;
            _modAlt  = false;
            _qnSet   = 'default';
            const tabBtn = document.getElementById('qnTAB');
            if (tabBtn) {
                tabBtn.textContent = 'TAB';
                tabBtn.classList.remove('qn-multi');
            }
            const shiftBtn = document.getElementById('qnSHIFT_L');
            if (shiftBtn) shiftBtn.classList.remove('qn-mod-active');
            // Find List 복원은 _updateMarkOverlay가 처리
            _updateMarkOverlay();
            // 멀티 List 오버레이 닫기
            _closeMultiListOverlay();
            // BLK OFF 오버레이 숨김
            document.body.classList.remove('qn-multi-on-active');
        }

        function _qnMod(name) {
            // Shift ON/OFF 무관하게 CTRL↔ALT 상호 배타 (나중 누른 쪽이 이김)
            if (name === 'ctrl') { _modCtrl = !_modCtrl; _modAlt = false; }
            else if (name === 'alt') { _modAlt = !_modAlt; _modCtrl = false; }
            _qnApplyLabels(_qnPending() || _qnSet);
        }

        _bind('qnCTRL', () => {
            if (_multiMode) {
                _mLock = !_mLock;
                if (_mLock) {
                    window._uiAttachMLockBlock?.();
                    window.BlockState?.setMLock?.(true);
                    window.NavBlockV2?.mlockInit?.();
                } else {
                    window._uiDetachMLockBlock?.();
                    window.BlockState?.setMLock?.(false);
                    window.NavBlockV2?.mlockClear?.();
                    // M-LOCK OFF 후 bases 동기화 — stale baseCh/baseHdCh 방지
                    window.NavBlockV2?._syncBasesFromMainIdx?.();
                }
                _qnApplyLabels(_qnSet);
            } else {
                _qnMod('ctrl');
            }
            _qnGuardScroll();
        });
        _bind('qnALT',  () => {
            if (_multiMode) {
                // CHECK ON 진입 전 역배열(bs.line > be.line) 정렬
                // state.js setBS()는 checkMode ON 중 변경 무시하므로 반드시 _checkMode 토글 전에 실행
                if (!_checkMode) {
                    const _bs0 = window.State?.getBS?.();
                    const _be0 = window.State?.getBE?.();
                    if (_bs0 && _be0 && _bs0.line > _be0.line) {
                        window.State?.setBS?.(_be0);
                        window.State?.setBE?.(_bs0);
                    }
                }
                _checkMode = !_checkMode;
                window.BlockState?.setCheckMode?.(_checkMode);
                if (_checkMode) {
                    // CHECK 진입: 현재 cursorMode 저장
                    window._uiIsCheckCurMode = _cursorMode;
                    const cur = window.Editor?.getCursor?.();
                    const bs  = window.State?.getBS?.();
                    const be  = window.State?.getBE?.();
                    // 포인터 초기화
                    // 재진입 시 대표 커서(main head)가 마지막 렌더 위치에 남아 있어도,
                    // CHECK 기준점: 정배열 보장 후이므로 bs.line이 항상 위쪽
                    if (bs && be) {
                        const _ptrFromLine = Math.min(bs.line, be.line);
                        window.NavBlock?._setCheckPointer?.({ line: _ptrFromLine, ch: bs.ch });
                    } else if (cur) {
                        window.NavBlock?._setCheckPointer?.(cur);
                    }
                    // CHECK ON 진입: BlockState 동기화
                    window.BlockState?.enterCheck?.();
                    if (bs && be) {
                        const colOffsets   = window._uiGetColOffsets?.();
                        const colBsOffsets = window._uiGetColBsOffsets?.();
                        const fromLine = Math.min(bs.line, be.line);
                        const toLine   = Math.max(bs.line, be.line);
                        const excluded = window._uiGetCheckedHeads?.() || new Set();
                        // 고정 컬럼 넓이: BS~BE의 anchor/head 차이
                        const colWidth = Math.abs(be.ch - bs.ch);
                        const anchorIsLeft = bs.ch <= be.ch; // gamma가 왼쪽
                        // CM6 ranges → line:실제커서ch 맵
                        const view = window.Editor?.get?.();
                        const rangeMap = new Map();
                        if (view) {
                            for (const r of view.state.selection.ranges) {
                                const hPos = window.Editor?.offsetToPos(r.head);
                                if (hPos) rangeMap.set(hPos.line, hPos.ch);
                            }
                        }
                        for (let l = fromLine; l <= toLine; l++) {
                            if (excluded.has(l)) continue;
                            // 각 라인의 실제 커서 ch (없으면 대표값)
                            const cursorCh = rangeMap.has(l) ? rangeMap.get(l) : Math.min(bs.ch, be.ch);
                            // gamma=cursorCh, delta=cursorCh+colWidth (방향 유지)
                            const gamma = anchorIsLeft ? cursorCh : cursorCh + colWidth;
                            const delta = anchorIsLeft ? cursorCh + colWidth : cursorCh;
                            if (!colOffsets?.has(l))   colOffsets?.set(l, delta);
                            if (!colBsOffsets?.has(l)) colBsOffsets?.set(l, gamma);
                        }
                        // tpl: fromLine 기준 (정배열 보장 후)
                        const tpl = {
                            anchor: colBsOffsets?.get(fromLine) ?? bs.ch,
                            head:   colOffsets?.get(fromLine)   ?? be.ch,
                        };
                        window.NavBlock?._setCheckAnchorTemplate?.(tpl);
                    }
                    requestAnimationFrame(() => {
                        const ptr = window.NavBlock?.getCheckPointer?.();
                        if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                        window.NavBlock?.applyColumnSelection?.();
                    });
                } else {
                    window._uiIsCheckCurMode = undefined;
                    window._imeSnap = null; // 체크 OFF 시 IME 백업 초기화
                    window.BlockState?.exitCheck?.();
                    // CHECK OFF:
                    // 1) 실제 유효 라인의 끝까지만 배열 꼬리를 자르고
                    // 2) BE를 그 유효 라인의 실제 주소(line,ch)로 동기화한 뒤
                    // 3) 포인터/하이라이트만 정리한다.
                    window._uiTrimCheckoutToLastEffective?.();
                    window.NavBlock?._resetCheckPointer?.();
                    window.NavBlock?._setCheckAnchorTemplate?.(null);
                    requestAnimationFrame(() => {
                        window.Editor?.setCheckLines?.([]);
                        window.NavBlock?.applyColumnSelection?.();
                    });
                }
                const tabBtn = document.getElementById('qnTAB');
                if (tabBtn) tabBtn.textContent = _checkMode ? 'ON/OFF' : (_cursorMode ? 'CUR' : 'BLK');
                _qnApplyLabels(_qnSet);
            } else {
                _qnMod('alt');
            }
            _qnGuardScroll();
        });

        // qnTAB 동작 표 (우선순위 순):
        //   1. 멀티모드 + CHECK ON  → NavBlockV2.checkTabToggle
        //   2. 멀티모드 + CHECK OFF → BLK ↔ CUR 스왑 (한 점 초기화, Shift 초기화)
        //   3. 퀵일반 + CTRL pending → Copy pill 토글 (ClipView) + CTRL 소비
        //   4. 퀵일반 + ALT  pending → Menu pill 토글 (MenuView) + ALT  소비
        //   5. 퀵일반 + SHIFT_L ON   → 멀티블럭 모드 진입 (_enterMultiMode)
        //   6. 퀵일반 기본           → 탭 문자 삽입
        // 주의: "ALT+TAB으로 alt 셋트 잠금" / "CTRL+TAB으로 ctrl 셋트 잠금" 기능은 제거됨.
        //       CTRL/ALT pending은 S1~S4 직접 클릭, 방향키 네비 수정자로는 여전히 유효.
        _bind('qnTAB', () => {
            if (_multiMode) {
                if (_checkMode) {
                    window.NavBlockV2?.checkTabToggle?.();
                    _qnApplyLabels(_qnSet);
                    return;
                }
                // BLK↔CUR 스왑 — 한 점 초기화 + Shift 초기화
                _cursorMode = !_cursorMode;
                window._imeSnap = null; // IME 백업 초기화
                // 가상 오프셋 초기화 — 모드 전환 시 이전 M-LOCK 오프셋 잔류 방지
                window.NavBlockV2?.mlockClear?.();

                // 한 점 초기화
                const _reanchorCur = _resetMultiForReanchor();
                if (_reanchorCur) {
                    const _reanchorOffset = window.Editor?.posToOffset?.(_reanchorCur);
                    if (_reanchorOffset != null) {
                        const v = window.Editor?.get?.();
                        if (v) v.dispatch({ selection: { anchor: _reanchorOffset } });
                        window.BlockState?.dispatch?.([{ anchor: _reanchorOffset, head: _reanchorOffset }], 0);
                    }
                }
                window.State?.clearBlock?.();

                // Shift 초기화 (CUR/BLK가 메인, Shift는 종속)
                _qnSetShift(false);

                // BlockState 갱신 (inputmode는 건드리지 않음 — OS 키보드 상태 존중)
                window.BlockState?.setCursorMode?.(_cursorMode);

                // tabBtn 텍스트 갱신
                const tabBtn = document.getElementById('qnTAB');
                if (tabBtn) tabBtn.textContent = _cursorMode ? 'CUR' : 'BLK';

                _qnApplyLabels(_qnSet);
                return;
            }
            // CTRL+TAB → Copy pill 토글 (CTRL pending 소비)
            //   Shift+CTRL+TAB → Run pill 토글
            if (_modCtrl) {
                if (_qnShift) {
                    // Shift+CTRL → Run pill
                    _modCtrl = false;
                    if (!_qnShiftLocked) _qnSetShift(false);
                    _qnClearModClasses();
                    window.RunView?.toggle?.();
                    _qnApplyLabels(_qnSet);
                    return;
                }
                _modCtrl = false;
                _qnClearModClasses();
                // pill 먼저 토글 → _qnApplyLabels가 pill open 상태를 _qnSetForLabel에 반영
                window.ClipView?.toggle?.();
                _qnApplyLabels(_qnSet);
                return;
            }
            // ALT+TAB → Menu pill 토글 (ALT pending 소비) — CTRL+TAB과 대칭
            //   Shift+ALT+TAB → SQL pill 토글
            if (_modAlt) {
                if (_qnShift) {
                    // Shift+ALT → SQL pill
                    _modAlt = false;
                    if (!_qnShiftLocked) _qnSetShift(false);
                    _qnClearModClasses();
                    window.SqlView?.toggle?.();
                    _qnApplyLabels(_qnSet);
                    return;
                }
                _modAlt = false;
                _qnClearModClasses();
                window.MenuView?.toggle?.();
                _qnApplyLabels(_qnSet);
                return;
            }
            if (_qnShift) {
                // SHIFT+TAB → 멀티블럭 진입
                _enterMultiMode();
            } else {
                window.Editor?.replaceSelection?.('\t');
                window.Editor?.focus?.();
            }
            _qnGuardScroll();
        });

        // ESC 동작 (단계적 초기화):
        //   멀티 모드:
        //     M-LOCK ON  → M-LOCK 해제 + 한 점 초기화 (멀티 유지)
        //     CHECK ON   → CHECK 해제 + 한 점 초기화 (멀티 유지)
        //     일반 멀티  → 한 점 초기화만 (멀티 유지) ★ BLK/CUR 클릭과 동등
        //   퀵일반:
        //     CTRL/ALT pending + SHIFT_L 초기화, _qnSet(shiftr 등)은 보존
        //     + 에디터에 Escape 키 전달 (IME 취소 등)
        // 멀티 완전 탈출은 BLK OFF 전담 (floatBlkTool).
        _bind('qnESC', () => {
            // M-LOCK ON: M-LOCK 해제 + 한 점으로 모으고 멀티 초기 상태 유지
            if (_mLock) {
                _mLock = false;
                _mLockPending = false;
                window._uiDetachMLockBlock?.();
                _resetMultiForReanchor();
                _qnSetShift(true); // SHIFT_L 버튼 active 표시용
                _enterMultiMode();
                _qnApplyLabels(_qnSet);
                return;
            }
            // CHECK ON: 한 점으로 모으고 CHECK만 해제한 채 멀티 초기 상태 유지
            if (_multiMode && _checkMode) {
                window._imeSnap = null;
                _resetMultiForReanchor();
                _qnSetShift(true);
                _enterMultiMode();
                _mLockPending = false;
                _qnApplyLabels(_qnSet);
                return;
            }
            // 일반 멀티: 한 점 초기화만 (BLK/CUR 스왑 없이 현재 모드 유지)
            // 완전 탈출은 BLK OFF 플로팅 버튼으로만 가능
            if (_multiMode) {
                window._imeSnap = null;
                _resetMultiForReanchor();
                // 멀티 재진입으로 내부 상태 깨끗이 초기화. 다만 _enterMultiMode가
                // _cursorMode를 false로 리셋하므로, 현재 CUR 상태였다면 보존하려면 우회 필요
                const _preservedCursorMode = _cursorMode;
                _enterMultiMode();
                if (_preservedCursorMode) {
                    _cursorMode = true;
                    window.BlockState?.setCursorMode?.(true);
                    const tabBtn = document.getElementById('qnTAB');
                    if (tabBtn) tabBtn.textContent = 'CUR';
                }
                _qnApplyLabels(_qnSet);
                return;
            }
            // 퀵일반: pending 모디파이어(CTRL/ALT) + SHIFT_L(_qnShift) 초기화 + 에디터 Escape 전달
            //   _qnSet(shiftr 등 SHIFT_R 셋트)만 보존 — 멀티 ESC와 같은 원칙
            //   SHIFT_L은 'MULTI' 캡션 잔존 방지를 위해 초기화
            //   완전 초기화 경로는 없음 (필요 시 CLOSE/LOGO 등 다른 경로로).
            _modCtrl = false; _modAlt = false;
            _qnSetShift(false);
            _qnApplyLabels(_qnSet);
            window.NavBlock?.clearColumnOverlay?.();
            window.State?.clearBlock?.();
            window.Editor?.clearSelection?.();
            const view = window.Editor?.get?.();
            if (view) {
                view.focus();
                view.contentDOM?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
            }
            _qnGuardScroll();
        });

        // BLK OFF → 퀵멀티 → 퀵일반 복귀 전용 (ESC 3번째 분기 - 에디터 Escape 키 전달 제외)
        // ESC와 달리 M-LOCK/CHECK 해제 분기를 거치지 않고 곧장 멀티 탈출
        // 에디터 자체의 Escape 동작(IME 취소 등)은 트리거하지 않음 — 순수 모드 전환만
        // 호출 주체는 index.html의 floatBlkTool 드래그 스크립트 (탭 판정 시)
        function _blkOffExec() {
            if (!_multiMode) return;  // 가드: 퀵일반에서 노출될 일 없지만 방어
            _qnSet     = 'default';
            _modCtrl = false; _modAlt = false;
            _qnSetShift(false);
            _exitMultiMode();
            _qnApplyLabels('default');
            window.NavBlock?.clearColumnOverlay?.();
            window.State?.clearBlock?.();
            window.Editor?.clearSelection?.();
            window.Editor?.get?.()?.focus();
            _qnGuardScroll();
        }
        window._blkOffExec = _blkOffExec;

        // ── 커서 히스토리 (BACK / NEXT용) ──
        const _qnCursorHistory = [];
        let   _qnCursorIdx     = -1;
        let   _qnHistoryLock   = false;

        function _qnPushHistory() {
            if (_qnHistoryLock) return;
            const view = window.Editor?.get?.();
            if (!view) return;
            const pos  = view.state.selection.main.head;
            const line = view.state.doc.lineAt(pos).from;
            // 같은 라인이면 무시
            if (_qnCursorHistory[_qnCursorIdx] === line) return;
            // 앞으로 이동 후 새 위치 추가 → 앞쪽 히스토리 버림
            if (_qnCursorIdx < _qnCursorHistory.length - 1) {
                _qnCursorHistory.splice(_qnCursorIdx + 1);
            }
            _qnCursorHistory.push(line);
            if (_qnCursorHistory.length > 50) _qnCursorHistory.shift();
            _qnCursorIdx = _qnCursorHistory.length - 1;
        }

        function _qnHistoryBack() {
            if (_qnCursorIdx <= 0) return;
            _qnCursorIdx--;
            const pos = _qnCursorHistory[_qnCursorIdx];
            if (pos == null) return;
            const view = window.Editor?.get?.();
            if (!view) return;
            _qnHistoryLock = true;
            view.dispatch({ selection: { anchor: pos }, scrollIntoView: true });
            view.focus();
            _qnHistoryLock = false;
        }

        function _qnHistoryNext() {
            if (_qnCursorIdx >= _qnCursorHistory.length - 1) return;
            _qnCursorIdx++;
            const pos = _qnCursorHistory[_qnCursorIdx];
            if (pos == null) return;
            const view = window.Editor?.get?.();
            if (!view) return;
            _qnHistoryLock = true;
            view.dispatch({ selection: { anchor: pos }, scrollIntoView: true });
            view.focus();
            _qnHistoryLock = false;
        }

        // 약식 패널이 열려 있을 때 커서 위치 추적
        document.addEventListener('pointerup', () => {
            const quickPanel = document.querySelector('.swipe-panel.panel-quick');
            if (quickPanel?.classList.contains('active')) _qnPushHistory();
        });

        // ── 뒤 4개 버튼 실제 기능 연결 ──
        // set 결정 매트릭스:
        //   _qnSet='default' + pending=null  → 'default'  (NEW/LOAD/SAVE AS/CLOSE)
        //   _qnSet='default' + pending=ctrl  → 'ctrl'     (ALL/COPY/PASTE/LIST)
        //       ※ Copy pill 열림 상태면 _qnSetForLabel이 'default'로 중화
        //   _qnSet='default' + pending=alt   → 'alt'      (FIRST/LAST/BACK/NEXT — 커서 히스토리)
        //   _qnSet='shiftr'  + pending=null  → 'shiftr'   (⌫/SPACE/ENTER/DEL)
        //   _qnSet='shiftr'  + pending=ctrl  → 'ctrl_shiftr'  (단어 단위 편집)
        //   _qnSet='shiftr'  + pending=alt   → 'alt_shiftr'   (라인 단위 편집)
        //   default + SHIFT_L ON             → 슬롯 네비 (case 'default' 내부에서 _qnShift 분기)
        function _qnExec(idx, isFirst) {
            let set = (_qnSet === 'shiftr' && _qnPending() === 'ctrl') ? 'ctrl_shiftr'
                      : (_qnSet === 'shiftr' && _qnPending() === 'alt')  ? 'alt_shiftr'
                      : _qnSet === 'shiftr' ? 'shiftr'
                      : (_qnPending() || _qnSet);
            // Copy pill 열려있으면 ctrl 셋트 동작 → default로 중화 (라벨과 일치)
            set = _qnSetForLabel(set);
            const _flashBtn = document.getElementById(['qnS1','qnS2','qnS3','qnS4'][idx]);
            if (_flashBtn) {
                _flashBtn.classList.add('qn-btn-flash');
                setTimeout(() => _flashBtn.classList.remove('qn-btn-flash'), 300);
            }
            _qnPushHistory();
            // ── SQL Autocomplete: shiftr SPACE(idx=1) + modifier → completion 트리거 ──
            if (idx === 1 && _qnSet === 'shiftr') {
                console.log('[SqlAC] _qnExec: SPACE pressed, sqlMode=' + window.SqlComplete?.isSqlMode?.(),
                    'schemaLoaded=' + window.SqlComplete?.schemaLoaded,
                    'pending=' + _qnPending(), 'shift=' + _qnShift);
            }
            if (idx === 1 && _qnSet === 'shiftr' && window.SqlComplete?.isSqlMode?.() && window.SqlComplete.schemaLoaded) {
                const pending = _qnPending();
                if (pending === 'ctrl' || pending === 'alt' || _qnShift) {
                    const kind = pending === 'ctrl' ? 'ctrl' : pending === 'alt' ? 'alt' : 'shift';
                    console.log('[SqlAC] _qnExec: triggering SQL completion, kind=' + kind);
                    window.SqlComplete.setTriggerKind(kind);
                    // CM6 completion 트리거
                    const cmds = CM6?.completionKeymap || [];
                    const startCmd = cmds.find(k => k.key === 'Ctrl-Space');
                    const v = window.Editor?.get?.();
                    console.log('[SqlAC] _qnExec: startCmd found=' + !!startCmd, 'view=' + !!v);
                    if (startCmd && startCmd.run && v) {
                        startCmd.run(v);
                    }
                    if (pending) { _modCtrl = false; _modAlt = false; _qnApplyLabels(_qnSet); }
                    if (_qnShift && !_qnShiftLocked) _qnSetShift(false);
                    return;
                }
            }
            // ── Python Autocomplete: shiftr SPACE(idx=1) + modifier → completion 트리거 ──
            if (idx === 1 && _qnSet === 'shiftr' && window.PyComplete?.isPyMode?.()) {
                const pending = _qnPending();
                if (pending === 'ctrl' || pending === 'alt' || _qnShift) {
                    const kind = pending === 'ctrl' ? 'ctrl' : pending === 'alt' ? 'alt' : 'shift';
                    console.log('[PyAC] _qnExec: triggering Python completion, kind=' + kind);
                    window.PyComplete.setTriggerKind(kind);
                    const cmds = CM6?.completionKeymap || [];
                    const startCmd = cmds.find(k => k.key === 'Ctrl-Space');
                    const v = window.Editor?.get?.();
                    if (startCmd && startCmd.run && v) {
                        startCmd.run(v);
                    }
                    if (pending) { _modCtrl = false; _modAlt = false; _qnApplyLabels(_qnSet); }
                    if (_qnShift && !_qnShiftLocked) _qnSetShift(false);
                    return;
                }
            }
            switch (set) {
                case 'default':
                    if (_qnShift) {
                        if (idx === 0) window.SlotManager?.slotPrev?.();
                        else if (idx === 1) window.SlotManager?.slotNext?.();
                        else if (idx === 2) window.SlotManager?.slotFirst?.();
                        else if (idx === 3) window.SlotManager?.slotLast?.();
                        // 1회용: locked 아니면 실행 후 shift 해제
                        if (!_qnShiftLocked) _qnSetShift(false);
                    } else {
                        if (idx === 0) window.SlotManager?.newFile?.();
                        else if (idx === 1) window.SlotManager?.openLoadPopup?.();
                        else if (idx === 2) window.SlotManager?.openSavePopup?.();
                        else if (idx === 3) window.SlotManager?.closeCurrentSlot?.();
                    }
                    break;
                case 'ctrl':
                    if (idx === 0) window.Nav?.selectAll?.();
                    else if (idx === 1) {
                        if (_isBlockMode()) {
                            // V2: copyAll — 빈 range 제외, 같은 라인 중복 제거
                            const text = window.NavBlockV2?.copyAll?.();
                            if (text) window.NavClipboard?.push?.(text);
                            else window.NavBlock?.copyColumnBlock?.(); // V1 폴백
                        } else {
                            // CM6 selection 있으면 우선 (selectAll 후 등), 없으면 copyBlock(커서 라인)
                            const sel = window.Editor?.getSelection?.();
                            const t = sel || window.NavBlock?.copyBlock?.();
                            if (t) {
                                window.NavBlock?.setClipData?.(t);
                                window.NavClipboard?.push?.(t);
                                window._usekitClipCopy?.(t);
                            }
                        }
                    }
                    else if (idx === 2) {
                        if (_isBlockMode()) {
                            if (_cursorMode) {
                                // CUR 멀티: \n → 공백 치환 후 모든 커서에 동일 삽입
                                const v = window.Editor?.get?.();
                                const ranges = window.BlockState?.getRanges?.();
                                const clipText = window.NavBlock?.getClipData?.();
                                if (v && ranges?.length > 1 && clipText) {
                                    const flat = clipText.replace(/\n/g, ' ');
                                    const sorted = [...ranges].sort((a, b) => b.head - a.head);
                                    const changes = sorted.map(r => ({
                                        from:   Math.min(r.anchor, r.head),
                                        to:     Math.max(r.anchor, r.head),
                                        insert: flat
                                    }));
                                    v.dispatch({ changes, userEvent: 'input' });
                                    window.BlockState?.render?.();
                                } else {
                                    window.Nav?.pasteAtCursor?.();
                                }
                            } else {
                                // BLK PASTE: 단일 range면 일반 붙여넣기
                                const v = window.Editor?.get?.();
                                const ranges = window.BlockState?.getRanges?.();
                                const clipText = window.NavBlock?.getClipData?.();
                                if (!ranges || ranges.length <= 1) {
                                    window.Nav?.pasteAtCursor?.();
                                } else if (v && ranges.length && clipText) {
                                    const clipLines = clipText.split('\n');
                                    const count = Math.min(ranges.length, clipLines.length);
                                    const sorted = [...ranges]
                                        .map((r, i) => ({ r, i }))
                                        .sort((a, b) => b.r.head - a.r.head);
                                    const changes = sorted
                                        .filter(({ i }) => i < count)
                                        .map(({ r, i }) => ({
                                            from:   Math.min(r.anchor, r.head),
                                            to:     Math.max(r.anchor, r.head),
                                            insert: clipLines[i]
                                        }));
                                    if (changes.length) {
                                        v.dispatch({ changes, userEvent: 'input' });
                                        window.BlockState?.render?.();
                                    }
                                } else {
                                    window.NavBlock?.pasteColumnBlock?.(); // V1 폴백
                                }
                            }
                            // paste는 멀티 해제와 무관 — 멀티/라벨/셋트 유지
                        } else requestAnimationFrame(() => window.Nav?.pasteAtCursor?.());
                    }
                    else if (idx === 3) window.NavClipboard?.openModal?.();
                    break;
                case 'alt':
                    if (idx === 0) window.Nav?.jumpFirstChange?.();
                    else if (idx === 1) window.Nav?.jumpLastChange?.();
                    else if (idx === 2) _qnHistoryBack();
                    else if (idx === 3) _qnHistoryNext();
                    break;
                case 'ctrl_shiftr':
                    // CTRL + shiftr: BS/DEL = 단어단위, ENTER = insertLineBelow, SPACE = 일반
                    if (idx === 0) { window.Nav?.deleteWordBefore?.(); }
                    else if (idx === 1) { UIFeedback?.space?.(); window.Editor?.replaceSelection?.(' '); }
                    else if (idx === 2) { UIFeedback?.enter?.(); window.Nav?.insertLineBelow?.(); }
                    else if (idx === 3) { window.Nav?.deleteWordAfter?.(); }
                    break;
                case 'alt_shiftr': {
                    // ALT + shiftr: 라인(\n) 기준 편집
                    //   BS: 커서 앞 \n 하나 삭제
                    //   SPACE: 현재 라인 삭제 (통상 Delete Line)
                    //   ENTER: 현재 라인 끝에 \n, 커서 제자리
                    //   DEL: 커서 뒤 \n 하나 삭제
                    const v = window.Editor?.get?.();
                    if (!v) break;
                    const doc = v.state.doc;
                    const head = v.state.selection.main.head;
                    if (idx === 0) {
                        // Alt+BS: 커서 앞 \n 하나 삭제
                        if (head === 0) break;
                        const before = doc.sliceString(0, head);
                        const nl = before.lastIndexOf('\n');
                        if (nl < 0) break;
                        if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                        v.dispatch({ changes: { from: nl, to: nl + 1 }, userEvent: 'delete' });
                    } else if (idx === 1) {
                        // Alt+SPACE: 현재 라인 삭제
                        UIFeedback?.del?.();
                        const line = doc.lineAt(head);
                        const total = doc.length;
                        if (line.to < total) {
                            // 라인 + 뒤 \n → 다음 라인이 올라옴 (컬럼 유지 시도)
                            const prevCol = head - line.from;
                            const nextLine = doc.lineAt(line.to + 1);
                            const newHead = nextLine.from + Math.min(prevCol, nextLine.length);
                            v.dispatch({
                                changes:  { from: line.from, to: line.to + 1 },
                                selection:{ anchor: newHead },
                                userEvent: 'delete',
                            });
                        } else if (line.from > 0) {
                            // 마지막 라인: 앞 \n + 라인 → 커서는 이전 라인 끝
                            v.dispatch({
                                changes:  { from: line.from - 1, to: line.to },
                                selection:{ anchor: line.from - 1 },
                                userEvent: 'delete',
                            });
                        } else {
                            // 유일 라인: 내용만 비움
                            v.dispatch({
                                changes:  { from: 0, to: line.to },
                                selection:{ anchor: 0 },
                                userEvent: 'delete',
                            });
                        }
                    } else if (idx === 2) {
                        // Alt+ENTER: 현재 라인 끝에 \n, 커서 제자리
                        UIFeedback?.enter?.();
                        const line = doc.lineAt(head);
                        v.dispatch({
                            changes:  { from: line.to, insert: '\n' },
                            selection:{ anchor: head },
                            userEvent: 'input',
                        });
                    } else if (idx === 3) {
                        // Alt+DEL: 커서 뒤 \n 하나 삭제
                        if (head >= doc.length) break;
                        const after = doc.sliceString(head);
                        const rel = after.indexOf('\n');
                        if (rel < 0) break;
                        if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                        const nl = head + rel;
                        v.dispatch({ changes: { from: nl, to: nl + 1 }, userEvent: 'delete' });
                    }
                    break;
                }
                case 'shiftr': {
                    // IME 백업 중이면 먼저 복원
                    if (window._imeSnap) { window.imeSnapRestore?.(); return; }
                    // 단일커서 판단: 멀티모드여도 ranges가 1개면 CM6 직접 위임
                    const _isSingle = !_multiMode ||
                        (window.BlockState?.getRanges?.()?.length ?? 1) === 1;

                    if (_isSingle) {
                        // ── 단일커서: CM6 직접 위임 ──────────────────────
                        if (idx === 0) {
                            if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                            window.Editor?.execCommand?.('delCharBefore');
                        } else if (idx === 1) {
                            UIFeedback?.space?.();
                            window.Editor?.replaceSelection?.(' ');
                        } else if (idx === 2) {
                            UIFeedback?.enter?.();
                            window.Editor?.replaceSelection?.('\n');
                        } else if (idx === 3) {
                            if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                            window.Editor?.execCommand?.('delCharAfter');
                        }
                    } else {
                        // ── 멀티커서: CHECK/쉬프트ON/OFF 분기 ───────────
                        if (_checkMode) {
                            // CHECK ON: mainIdx 커서만 편집
                            if (idx === 0) {
                                if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                                window.NavBlockV2?.checkEdit?.('delBefore');
                            } else if (idx === 1) {
                                UIFeedback?.space?.();
                                window.NavBlockV2?.checkEdit?.('insert', ' ');
                            } else if (idx === 2) {
                                UIFeedback?.enter?.();
                                const ch = _cursorMode ? '\n' : ' ';
                                window.NavBlockV2?.checkEdit?.('insert', ch);
                            } else if (idx === 3) {
                                if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                                window.NavBlockV2?.checkEdit?.('delAfter');
                            }
                        } else if (_cursorMode) {
                            // CUR(쉬프트OFF): 각 커서에 CM6 위임
                            // ⌫로 라인 합쳐진 후 같은 라인 중복 커서 → rAF 후 dedup
                            if (idx === 0) {
                                if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                                window.Editor?.execCommand?.('delCharBefore');
                                // CM6 합치기 후 BlockState를 CM6 현재 selection으로 재동기화
                                requestAnimationFrame(() => {
                                    const v = window.Editor?.get?.();
                                    if (!v) return;
                                    const { EditorSelection } = CM6;
                                    const ranges = Array.from(v.state.selection.ranges);
                                    // 라인당 1개 보장 — 중복 제거
                                    const seen = new Set();
                                    const specs = [];
                                    for (const r of ranges) {
                                        const lineNum = v.state.doc.lineAt(r.head).number;
                                        if (seen.has(lineNum)) continue;
                                        seen.add(lineNum);
                                        specs.push({ anchor: r.anchor, head: r.head });
                                    }
                                    window.BlockState?.dispatch?.(specs, 0);
                                    window.BlockState?.render?.();
                                });
                            } else if (idx === 1) {
                                UIFeedback?.space?.();
                                window.Editor?.replaceSelection?.(' ');
                            } else if (idx === 2) {
                                UIFeedback?.enter?.();
                                window.Editor?.replaceSelection?.('\n');
                            } else if (idx === 3) {
                                if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                                window.Editor?.execCommand?.('delCharAfter');
                                // 라인 합치기 후 BlockState 재동기화
                                requestAnimationFrame(() => {
                                    const v = window.Editor?.get?.();
                                    if (!v) return;
                                    const ranges = Array.from(v.state.selection.ranges);
                                    const seen = new Set();
                                    const specs = [];
                                    for (const r of ranges) {
                                        const lineNum = v.state.doc.lineAt(r.head).number;
                                        if (seen.has(lineNum)) continue;
                                        seen.add(lineNum);
                                        specs.push({ anchor: r.anchor, head: r.head });
                                    }
                                    window.BlockState?.dispatch?.(specs, 0);
                                    window.BlockState?.render?.();
                                });
                            }
                        } else {
                            // BLK(쉬프트ON)
                            if (idx === 0) {
                                // ⌫ BLK(쉬프트ON)
                                // - 역방향 음영(head<anchor): 음영 무시, head 앞 1글자만 삭제
                                // - 정방향 음영: 음영 삭제
                                // - cursor: 앞 1글자 삭제 (단, 라인 맨 앞이면 엔터 안 지움 — 구조 유지)
                                if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                                const v = window.Editor?.get?.();
                                if (v) {
                                    const doc = v.state.doc;
                                    const ranges = Array.from(v.state.selection.ranges);
                                    const changes = [];
                                    for (const r of [...ranges].reverse()) {
                                        if (r.head < r.anchor) {
                                            // 역방향: head 앞 1글자 삭제 (라인 맨 앞이면 스킵)
                                            const lineFrom = doc.lineAt(r.head).from;
                                            if (r.head > lineFrom) {
                                                changes.push({ from: r.head - 1, to: r.head });
                                            }
                                            // 라인 맨 앞이면 엔터 안 지움
                                        } else if (r.anchor < r.head) {
                                            // 정방향 음영: 음영 삭제
                                            changes.push({ from: r.anchor, to: r.head });
                                        } else {
                                            // cursor: 라인 맨 앞이면 엔터 안 지움, 아니면 앞 1글자 삭제
                                            const lineFrom = doc.lineAt(r.head).from;
                                            if (r.head > lineFrom) {
                                                changes.push({ from: r.head - 1, to: r.head });
                                            }
                                            // 라인 맨 앞(r.head === lineFrom): 스킵
                                        }
                                    }
                                    if (changes.length) {
                                        v.dispatch({ changes });
                                        window.BlockState?.render?.();
                                        requestAnimationFrame(() => window.Editor?.focus?.());
                                    }
                                }
                            } else if (idx === 1) {
                                UIFeedback?.space?.();
                                window.Editor?.replaceSelection?.(' ');
                            } else if (idx === 2) {
                                UIFeedback?.enter?.();
                                window.Editor?.replaceSelection?.(' ');
                            } else if (idx === 3) {
                                // DEL BLK: ⌫의 반대 — head 오른쪽 1글자 삭제, 라인 끝이면 엔터 안 지움
                                if (isFirst) UIFeedback?.del?.(); else UIFeedback?.delRepeat?.();
                                const vDel = window.Editor?.get?.();
                                if (vDel) {
                                    const docDel = vDel.state.doc;
                                    const rangesDel = Array.from(vDel.state.selection.ranges);
                                    const changesDel = [];
                                    for (const r of [...rangesDel].reverse()) {
                                        const lineObj = docDel.lineAt(r.head);
                                        if (r.head < r.anchor) {
                                            // 정방향 음영(head 오른쪽에 음영): 음영 전체 삭제, 엔터 보호
                                            const to = Math.min(r.anchor, lineObj.to);
                                            if (to > r.head) changesDel.push({ from: r.head, to });
                                        } else if (r.head < lineObj.to) {
                                            // 음영 없거나 역방향: head 오른쪽 1글자 삭제
                                            changesDel.push({ from: r.head, to: r.head + 1 });
                                        }
                                        // 라인 끝(r.head === lineObj.to): 엔터 보호 — 스킵
                                    }
                                    if (changesDel.length) {
                                        vDel.dispatch({ changes: changesDel });
                                        window.BlockState?.render?.();
                                        requestAnimationFrame(() => window.Editor?.focus?.());
                                    }
                                }
                            }
                        }
                    }
                    requestAnimationFrame(() => window.Editor?.focus?.());
                    break;
                }
            }
            requestAnimationFrame(() => window.Editor?.focus?.());
        }

        ['qnS1','qnS2','qnS3','qnS4'].forEach((id, i) =>
            _bindRepeat(id, (isFirst) => { _qnExec(i, isFirst); _qnAfterAction(); }));

        // ── 2행: ⇧ HOME ◀ ▲ ▼ ▶ END ⇧ ──
        // 좌/우 ⇧는 독립 단발 Shift 토글
        function _qnSetShift(on) {
            _qnShift = on;
            window._qnShift = on; // 다른 스코프(_bindCMEvents 등)에서 참조
            const btn = document.getElementById('qnSHIFT_L');
            if (btn) {
                btn.classList.toggle('qn-mod-active', on);
            }
            // SHIFT 꺼지면 — multiMode 아닌 경우에만 blockCursorMode 리셋 + BS 클리어
            if (!on && !_multiMode) {
                _cursorMode = false;
                _qnShiftLocked = false;  // shift OFF → locked도 해제
                window.State?.clearBlock?.();   // 낡은 BS 앵커 제거 — 다음 Shift ON 시 재사용 방지
            }
            _qnApplyLabels((_qnPending() || _qnSet));
            _qnApplyShiftLockStyle();
        }

        // Shift 고정 모드 캡션 컬러 (레드 경고)
        function _qnApplyShiftLockStyle() {
            ['qnS1','qnS2','qnS3','qnS4'].forEach(id => {
                const btn = document.getElementById(id);
                if (btn) btn.classList.toggle('qn-shift-locked', _qnShiftLocked && _qnShift);
            });
            const shiftBtn = document.getElementById('qnSHIFT_L');
            if (shiftBtn) shiftBtn.classList.toggle('qn-shift-locked', _qnShiftLocked && _qnShift);
        }

        // SHIFT_L / SHIFT_R — 단독 탭: 모디파이어 on/off + 2행 shift 토글

        // SHIFT_L — 멀티모드: BLK/CUR 토글 (_cursorMode 관리, _qnShift 건드리지 않음)
        //            일반모드: 탭=1회용 shift, 롱클릭=고정(레드캡션)
        //            ※ 멀티 안에서 BLK/CUR 상태 판단은 반드시 _cursorMode 기준으로 할 것
        (function() {
            const el = document.getElementById('qnSHIFT_L');
            if (!el) return;
            const LONG_MS = 400;
            let _timer = null, _long = false;
            el.addEventListener('touchstart', e => {
                e.preventDefault();
                _long = false;
                _timer = setTimeout(() => {
                    _long = true;
                    // 롱클릭: 멀티모드에서는 무시, 퀵일반에서만 고정 토글
                    if (!_isBlockMode()) {
                        if (_qnShiftLocked) {
                            // 고정 해제
                            _qnShiftLocked = false;
                            _qnSetShift(false);
                            UIFeedback?.toggle?.();
                        } else {
                            // 고정 ON
                            _qnShiftLocked = true;
                            _qnSetShift(true);
                            UIFeedback?.toggle?.();
                        }
                        // 레드 캡션 갱신
                        _qnApplyShiftLockStyle();
                    }
                }, LONG_MS);
            }, { passive: false });
            el.addEventListener('pointerdown', e => e.preventDefault());
            el.addEventListener('touchend', e => {
                e.preventDefault();
                clearTimeout(_timer);
                if (_long) return; // 롱클릭은 이미 처리됨
                UIFeedback?.toggle();
                if (_isBlockMode()) {
                    // BLK/CUR 토글
                    _cursorMode = !_cursorMode;
                    window._imeSnap = null; // IME 백업 초기화
                    // 가상 오프셋 초기화 — 모드 전환 시 이전 M-LOCK 오프셋 잔류 방지
                    window.NavBlockV2?.mlockClear?.();
                    // CHECK ON 중이면 _uiIsCheckCurMode도 갱신
                    if (_checkMode) window._uiIsCheckCurMode = _cursorMode;
                    window.BlockState?.setCursorMode?.(_cursorMode);
                    // inputmode 건드리지 않음 — OS 키보드 상태 존중
                    const tabBtn = document.getElementById('qnTAB');
                    if (tabBtn && !_checkMode) tabBtn.textContent = _cursorMode ? 'CUR' : 'BLK';
                    const shiftBtn = document.getElementById('qnSHIFT_L');
                    if (shiftBtn) shiftBtn.classList.toggle('qn-mod-active', !_cursorMode);
                    if (_cursorMode) {
                        const colOffsets   = window._uiGetColOffsets?.();
                        const colBsOffsets = window._uiGetColBsOffsets?.();
                        if (_checkMode) {
                            // CHECK ON: ptrLine만 gamma=delta
                            const ptrLine = window.NavBlock?.getCheckPointer?.()?.line;
                            if (ptrLine != null && colOffsets?.has(ptrLine) && colBsOffsets) {
                                colBsOffsets.set(ptrLine, colOffsets.get(ptrLine));
                            }
                        } else {
                            // CHECK OFF + CUR 진입: 각 라인 gamma=delta (음영 제거)
                            if (colOffsets?.size) {
                                for (const [l, delta] of colOffsets) {
                                    colBsOffsets?.set(l, delta);
                                }
                            }
                        }
                        window.NavBlock?.applyColumnSelection?.();
                    } else {
                        // BLK 진입(쉬프트 ON): bases 동기화 후 재렌더
                        window.NavBlockV2?._syncBasesFromMainIdx?.();
                        // M-LOCK ON 상태면 현재 실측으로 mlockInit 재계산
                        // (CUR에서 이동 후 실제 head 위치가 바뀌었으므로)
                        if (_mLock) window.NavBlockV2?.mlockInit?.();
                        window.NavBlock?.applyColumnSelection?.();
                    }
                } else {
                    // 퀵일반 탭: locked 상태면 해제, 아니면 토글 (1회용)
                    if (_qnShiftLocked) {
                        _qnShiftLocked = false;
                        _qnSetShift(false);
                        _qnApplyShiftLockStyle();
                    } else {
                        _qnSetShift(!_qnShift);
                    }
                }
                _qnGuardScroll();
            });
            el.addEventListener('touchcancel', () => { clearTimeout(_timer); _long = false; });
        })();

        // SHIFT_R (■) — shiftr 셋트 모디파이어 (CTRL/ALT와 동일 방식)
        (function() {
            const el = document.getElementById('qnSHIFT_R');
            if (!el) return;
            el.textContent = '■';
            let _prevSet = 'default';
            let _shiftRTouchId = null;
            el.addEventListener('touchstart', e => {
                e.preventDefault();
                // 이 버튼에서 직접 시작된 터치 ID만 기록
                if (e.targetTouches.length > 0) _shiftRTouchId = e.targetTouches[0].identifier;
            }, { passive: false });
            el.addEventListener('touchend', e => {
                e.preventDefault();
                // 자신에서 시작된 터치만 처리
                const matched = Array.from(e.changedTouches).find(t => t.identifier === _shiftRTouchId);
                _shiftRTouchId = null;
                if (!matched) return;
                UIFeedback?.toggle();
                if (_multiMode) {
                    // 멀티모드: shiftr(편집) ↔ ctrl(복사) 토글
                    _qnSet = (_qnSet === 'shiftr') ? 'ctrl' : 'shiftr';
                } else if (_qnSet === 'shiftr') {
                    _qnSet = _prevSet;
                } else {
                    _prevSet = _qnSet;
                    _qnSet = 'shiftr';
                }
                _qnApplyLabels((_qnPending() || _qnSet));
                _qnGuardScroll();
            });
            el.addEventListener('touchcancel', () => { _shiftRTouchId = null; });
        })();

        // 방향키 리피트 헬퍼
        function _bindQnRepeat(id, fn) {
            const el = document.getElementById(id);
            if (!el) return;
            let _timer = null, _interval = null;
            const _run = () => { fn(); _qnGuardScroll(); };
            const stop = () => { clearTimeout(_timer); clearInterval(_interval); _timer = _interval = null; };
            el.addEventListener('touchstart', e => e.preventDefault(), { passive: false });
            el.addEventListener('pointerdown', e => {
                e.preventDefault();
                stop();
                _run();
                _timer = setTimeout(() => { _interval = setInterval(_run, 80); }, 350);
            });
            el.addEventListener('pointerup',     stop);
            el.addEventListener('pointercancel', stop);
            el.addEventListener('pointerleave',  stop);
        }

        _bindQnRepeat('qnLEFT',  () => { UIFeedback?.special();
            if (window._imeSnap) { window.imeSnapRestore?.(); return; }
            if (State.getModeF()) { NavFocus.scrollH(-3); return; }
            if (_multiMode) {
                if (_checkMode) window.NavBlockV2?.checkLR?.('left');
                else if (_mLock && _cursorMode) window.NavBlockV2?.shiftAllLR?.('left');
                else                 window.NavBlockV2?.moveLR?.('left');
                requestAnimationFrame(_qnUpdateDirHint); return;
            }
            if (_qnPending() === 'ctrl' && _qnShift) { window.Nav?.selectWordLeft?.();              return; }
            if (_qnPending() === 'alt'  && _qnShift) { window.Nav?.shiftIndent?.(-1);               return; }
            if (_qnPending() === 'ctrl')              { window.Nav?.wordLeft?.();                    return; }
            if (_qnPending() === 'alt')               { window.NavCursor?.jumpParagraphPrev?.();     return; }
            _qnShift ? window.Nav?.selectLeft?.()  : window.Nav?.moveLeft?.();  });
        _bindQnRepeat('qnRIGHT', () => { UIFeedback?.special();
            if (window._imeSnap) { window.imeSnapRestore?.(); return; }
            if (State.getModeF()) { NavFocus.scrollH(3); return; }
            if (_multiMode) {
                if (_checkMode) window.NavBlockV2?.checkLR?.('right');
                else if (_mLock && _cursorMode) window.NavBlockV2?.shiftAllLR?.('right');
                else                 window.NavBlockV2?.moveLR?.('right');
                requestAnimationFrame(_qnUpdateDirHint); return;
            }
            if (_qnPending() === 'ctrl' && _qnShift) { window.Nav?.selectWordRight?.();             return; }
            if (_qnPending() === 'alt'  && _qnShift) { window.Nav?.shiftIndent?.(1);                return; }
            if (_qnPending() === 'ctrl')              { window.Nav?.wordRight?.();                   return; }
            if (_qnPending() === 'alt')               { window.NavCursor?.jumpParagraphNext?.();     return; }
            _qnShift ? window.Nav?.selectRight?.() : window.Nav?.moveRight?.(); });
        _bindQnRepeat('qnUP',    () => { UIFeedback?.special();
            if (window._imeSnap) { window.imeSnapRestore?.(); return; }
            if (State.getModeF()) { NavFocus.scrollV(-1); return; }
            if (_multiMode) {
                if (_checkMode) { const _ml = _mLock; if (_ml) window.BlockState?.setMLock?.(false); window.NavBlockV2?.checkUD?.('up'); if (_ml) window.BlockState?.setMLock?.(true); }
                else if (_mLock && _cursorMode) window.NavBlockV2?.shiftAllUD?.('up');
                else                 window.NavBlockV2?.moveUD?.('up');
                requestAnimationFrame(_qnUpdateDirHint); return;
            }
            if (_qnPending() === 'ctrl' && _qnShift) { window.NavCursor?.selectLineUp?.();                return; }
            if (_qnPending() === 'alt'  && _qnShift) { window.Nav?.shiftMoveBlock?.(-1);            return; }
            if (_qnPending() === 'alt')               { window.Nav?.pageUp?.();                      return; }
            _qnShift ? window.Nav?.selectUp?.()    : window.Nav?.moveUp?.();    });
        _bindQnRepeat('qnDOWN',  () => { UIFeedback?.special();
            if (window._imeSnap) { window.imeSnapRestore?.(); return; }
            if (State.getModeF()) { NavFocus.scrollV(1); return; }
            if (_multiMode) {
                if (_checkMode) { const _ml = _mLock; if (_ml) window.BlockState?.setMLock?.(false); window.NavBlockV2?.checkUD?.('down'); if (_ml) window.BlockState?.setMLock?.(true); }
                else if (_mLock && _cursorMode) window.NavBlockV2?.shiftAllUD?.('down');
                else                 window.NavBlockV2?.moveUD?.('down');
                requestAnimationFrame(_qnUpdateDirHint); return;
            }
            if (_qnPending() === 'ctrl' && _qnShift) { window.NavCursor?.selectLineDown?.();              return; }
            if (_qnPending() === 'alt'  && _qnShift) { window.Nav?.shiftMoveBlock?.(1);             return; }
            if (_qnPending() === 'alt')               { window.Nav?.pageDown?.();                    return; }
            _qnShift ? window.Nav?.selectDown?.()  : window.Nav?.moveDown?.();  });

        // HOME / END — 짧게: 줄 홈/끝, 길게: 문서 처음/끝
        function _bindQnHomeEnd(id, shortFn, longFn) {
            const el = document.getElementById(id);
            if (!el) return;
            let _t = null, _fired = false;
            el.addEventListener('touchstart', e => e.preventDefault(), { passive: false });
            el.addEventListener('pointerdown', e => {
                e.preventDefault();
                _fired = false;
                _t = setTimeout(() => { _fired = true; UIFeedback?.longPress(); longFn(); _qnGuardScroll(); }, 400);
            });
            el.addEventListener('pointerup', () => {
                clearTimeout(_t);
                if (!_fired) { UIFeedback?.special(); shortFn(); }
                _fired = false;
                _qnGuardScroll();
            });
            el.addEventListener('pointercancel', () => { clearTimeout(_t); _fired = false; });
        }

        _bindQnHomeEnd('qnHOME',
            () => {
                if (_isBlockMode()) {
                    if (_multiMode && _checkMode) {
                        // CHECK ON: CUR(_cursorMode=true, Shift OFF) → BS로 이동, BLK(Shift ON) → 개별라인 checkOnly homeEnd
                        if (_cursorMode) {
                            const ranges = window.BlockState?.getRanges?.() ?? [];
                            const v = window.Editor?.get?.();
                            if (ranges.length && v) {
                                // BS = min 라인 → 해당 range index
                                let minLine = Infinity, minIdx = 0;
                                ranges.forEach((r, i) => {
                                    try {
                                        const ln = v.state.doc.lineAt(r.head).number;
                                        if (ln < minLine) { minLine = ln; minIdx = i; }
                                    } catch(e) {}
                                });
                                window.BlockState?.setMainIdx?.(minIdx);
                                window.BlockState?.render?.();
                            }
                        } else {
                            window.NavBlockV2?.homeEnd?.('home', { checkOnly: true });
                        }
                        requestAnimationFrame(_qnUpdateDirHint); return;
                    }
                    if (_multiMode) { window.NavBlockV2?.homeEnd?.('home'); if (_mLock) window.NavBlockV2?.mlockInit?.(); requestAnimationFrame(_qnUpdateDirHint); return; }
                    const bs = window.State?.getBS?.(), be = window.State?.getBE?.();
                    const sameLine = !bs || !be || bs.line === be.line;
                    // CHECK OFF는 대표커서 기준이 아니라 BS/BE 방향 자체로만 판정한다.
                    const isHomeDir = !!(bs && be && ((bs.line > be.line) || (bs.line === be.line && bs.ch > be.ch)));
                    const isEndDir  = !!(bs && be && ((bs.line < be.line) || (bs.line === be.line && bs.ch < be.ch)));
                    if (!_checkMode && !_cursorMode && bs && be && !sameLine && isEndDir) {
                        window.State?.setBS?.(be);
                        window.State?.setBE?.(bs);
                        // 체크오프 반대방향 첫 입력은 스왑만 하지 않고 HOME 1차 동작까지 한 번에 수행한다.
                        window.NavBlock?.columnHomeAll?.();
                        requestAnimationFrame(_qnUpdateDirHint);
                        return;
                    }
                    if (!sameLine) {
                        // CHECK ON: 액티브 하이라이트를 현재 방향 기준 HOME쪽 끝으로 보냄
                        if (_checkMode && bs && be) {
                            if (!_mLock) {
                                // M-LOCK OFF: 현재 하이라이트 라인 블럭 너비 조절 (pointer 이동 없음)
                                window.NavBlock?.cycleCurrentCheckLineHome?.();
                                requestAnimationFrame(() => {
                                    const ptr = window.NavBlock?.getCheckPointer?.();
                                    if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                                    window.NavBlock?.applyColumnSelection?.();
                                    _qnUpdateDirHint();
                                });
                                return;
                            }
                            // M-LOCK ON: pointer → BS 끝으로 이동
                            const isReverse = (be.line < bs.line) || (be.line === bs.line && be.ch < bs.ch);
                            const target = isReverse ? be : bs;
                            const ptr0 = window.NavBlock?.getCheckPointer?.();
                            const alreadyAtTarget = !!(ptr0 && ptr0.line === target.line);
                            if (alreadyAtTarget && window.NavBlock?.isCheckHeadDirection?.('home')) {
                                if (window.NavBlock?.areCheckHeadsAtSoftHome?.()) {
                                    window.NavBlock?.syncCheckHeadsToColumnZero?.();
                                } else {
                                    window.NavBlock?.syncCheckHeadsToSoftHome?.();
                                }
                                requestAnimationFrame(() => {
                                    const ptr = window.NavBlock?.getCheckPointer?.();
                                    if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                                    window.NavBlock?.applyColumnSelection?.();
                                    _qnUpdateDirHint();
                                });
                                return;
                            }
                            window.NavBlock?._setCheckPointer?.({ line: target.line, ch: target.ch });
                            window.NavBlock?.syncCheckHeadDirection?.('home');
                            requestAnimationFrame(() => {
                                const ptr = window.NavBlock?.getCheckPointer?.();
                                if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                                window.NavBlock?.applyColumnSelection?.();
                                _qnUpdateDirHint();
                            });
                            return;
                        }
                        // CHECK 모드: 오프셋 보존, nav_block에서 직접 처리
                        if (_cursorMode) {
                            window.NavBlock?.columnHomeAll?.({ cursorOnly: true });
                        } else {
                            window.NavBlock?.columnHomeAll?.();
                        }
                        requestAnimationFrame(_qnUpdateDirHint);
                        return;
                    }
                    // 같은 라인
                    if (_cursorMode) { window.NavBlock?.columnHomeAll?.({ cursorOnly: true }); requestAnimationFrame(_qnUpdateDirHint); return; }
                    // 같은 라인 MULTI: BS 고정, BE만 줄시작으로
                    const cur = window.Editor?.getCursor?.();
                    if (cur) {
                        if (!bs) window.State?.setBS?.(cur);
                        const newBE = { line: cur.line, ch: 0 };
                        window.State?.setBE?.(newBE);
                        window.Editor?.setCursor?.(newBE);
                        window.NavBlock?.applyColumnSelection?.();
                        requestAnimationFrame(_qnUpdateDirHint);
                    }
                    return;
                }
                if (_isBlockMode()) return; // 멀티모드: pending 무시
                if (_qnPending() === 'alt'  && _qnShift) { window.Nav?.shiftMoveBlockToStart?.(); return; }
                if ((_qnPending() === 'ctrl' || _qnPending() === 'alt') && _qnShift) { window.NavCursor?.selectDocStart?.(); _qnAfterAction(); return; }
                if (_qnPending() === 'ctrl') { window.NavCursor?.jumpDocStart?.(); _qnAfterAction(); return; }
                if (_qnPending() === 'alt')  { window.Nav?.jumpFirstChange?.();    return; }
                // V2 homeEnd 이식: selection 있으면 스왑→softHome→col0, 없으면 softHome→col0
                try {
                    const _v = window.Editor?.get?.();
                    const _sel = _v?.state?.selection?.main;
                    if (_v && _sel) {
                        const doc = _v.state.doc;
                        // 1단계: head > anchor 이면 스왑 (selection 유지, head 왼쪽으로)
                        //   State.BS/BE 동기화는 cursorActivity 리스너가 자동 처리
                        if (_sel.head > _sel.anchor) {
                            _v.dispatch({ selection: { anchor: _sel.head, head: _sel.anchor } });
                            return;
                        }
                        // 2/3단계: softHome ↔ col0
                        const hLo = doc.lineAt(_sel.head);
                        const txt = doc.sliceString(hLo.from, hLo.to);
                        let soft = 0;
                        while (soft < txt.length && (txt[soft] === ' ' || txt[soft] === '\t')) soft++;
                        const col = _sel.head - hLo.from;
                        const newHead = hLo.from + (col === soft ? 0 : soft);
                        // newAnchor 결정:
                        //   - Shift OFF → 항상 단순 커서 이동 (음영 해제)
                        //   - Shift ON + 영역 있음 → anchor 고정 (범위 확장/축소)
                        //   - Shift ON + 한 점 → 현재 위치를 BS로 고정 (음영 생성 트리거)
                        let newAnchor;
                        if (!_qnShift)                          newAnchor = newHead;
                        else if (_sel.anchor !== _sel.head)     newAnchor = _sel.anchor;
                        else                                    newAnchor = _sel.head;
                        _v.dispatch({ selection: { anchor: newAnchor, head: newHead } });
                        // State.BS/BE 동기화 (BS=anchor, BE=head 불변식)
                        //   - 단순 커서 이동(anchor===head) 시엔 둘 다 같은 위치로
                        const _aLn = doc.lineAt(newAnchor);
                        const _hLn = doc.lineAt(newHead);
                        window.State?.setBS?.({ line: _aLn.number - 1, ch: newAnchor - _aLn.from });
                        window.State?.setBE?.({ line: _hLn.number - 1, ch: newHead   - _hLn.from });
                        return;
                    }
                } catch (e) {}
                // fallback: CM6 selection 접근 실패 시 기존 경로
                _qnShift ? window.Nav?.selectLineStart?.() : window.NavCursor?.jumpH?.();
            },
            () => { if (_multiMode) return; _qnShift ? window.Nav?.selectDocStart?.() : window.NavCursor?.jumpDocStart?.(); }
        );
        _bindQnHomeEnd('qnEND',
            () => {
                if (_isBlockMode()) {
                    if (_multiMode && _checkMode) {
                        // CHECK ON: CUR(_cursorMode=true, Shift OFF) → BE로 이동, BLK(Shift ON) → 개별라인 checkOnly homeEnd
                        if (_cursorMode) {
                            const ranges = window.BlockState?.getRanges?.() ?? [];
                            const v = window.Editor?.get?.();
                            if (ranges.length && v) {
                                // BE = max 라인 → 해당 range index
                                let maxLine = -Infinity, maxIdx = 0;
                                ranges.forEach((r, i) => {
                                    try {
                                        const ln = v.state.doc.lineAt(r.head).number;
                                        if (ln > maxLine) { maxLine = ln; maxIdx = i; }
                                    } catch(e) {}
                                });
                                window.BlockState?.setMainIdx?.(maxIdx);
                                window.BlockState?.render?.();
                            }
                        } else {
                            window.NavBlockV2?.homeEnd?.('end', { checkOnly: true });
                        }
                        requestAnimationFrame(_qnUpdateDirHint); return;
                    }
                    if (_multiMode) { window.NavBlockV2?.homeEnd?.('end'); if (_mLock) window.NavBlockV2?.mlockInit?.(); requestAnimationFrame(_qnUpdateDirHint); return; }
                    const bs = window.State?.getBS?.(), be = window.State?.getBE?.();
                    const sameLine = !bs || !be || bs.line === be.line;
                    // CHECK OFF는 대표커서 기준이 아니라 BS/BE 방향 자체로만 판정한다.
                    const isHomeDir = !!(bs && be && ((bs.line > be.line) || (bs.line === be.line && bs.ch > be.ch)));
                    const isEndDir  = !!(bs && be && ((bs.line < be.line) || (bs.line === be.line && bs.ch < be.ch)));
                    if (!_checkMode && !_cursorMode && bs && be && !sameLine && isHomeDir) {
                        window.State?.setBS?.(be);
                        window.State?.setBE?.(bs);
                        // 체크오프 반대방향 첫 입력은 스왑만 하지 않고 END 1차 동작까지 한 번에 수행한다.
                        window.NavBlock?.columnEndAll?.();
                        requestAnimationFrame(_qnUpdateDirHint);
                        return;
                    }
                    if (!sameLine) {
                        // CHECK ON: 액티브 하이라이트를 현재 방향 기준 END쪽 끝으로 보냄
                        if (_checkMode && bs && be) {
                            if (!_mLock) {
                                // M-LOCK OFF: 현재 하이라이트 라인 블럭 너비 조절 (pointer 이동 없음)
                                window.NavBlock?.cycleCurrentCheckLineEnd?.();
                                requestAnimationFrame(() => {
                                    const ptr = window.NavBlock?.getCheckPointer?.();
                                    if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                                    window.NavBlock?.applyColumnSelection?.();
                                    _qnUpdateDirHint();
                                });
                                return;
                            }
                            // M-LOCK ON: pointer → BE 끝으로 이동
                            const isReverse = (be.line < bs.line) || (be.line === bs.line && be.ch < bs.ch);
                            const target = isReverse ? bs : be;
                            const ptr0 = window.NavBlock?.getCheckPointer?.();
                            const alreadyAtTarget = !!(ptr0 && ptr0.line === target.line);
                            if (alreadyAtTarget && window.NavBlock?.isCheckHeadDirection?.('end')) {
                                if (window.NavBlock?.areCheckHeadsAtSoftEnd?.()) {
                                    window.NavBlock?.pushBlockSnapshot?.();
                                    window.NavBlock?.syncCheckHeadsToLineEnd?.();
                                } else {
                                    window.NavBlock?.syncCheckHeadsToSoftEnd?.();
                                }
                                requestAnimationFrame(() => {
                                    const ptr = window.NavBlock?.getCheckPointer?.();
                                    if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                                    window.NavBlock?.applyColumnSelection?.();
                                    _qnUpdateDirHint();
                                });
                                return;
                            }
                            window.NavBlock?._setCheckPointer?.({ line: target.line, ch: target.ch });
                            window.NavBlock?.syncCheckHeadDirection?.('end');
                            requestAnimationFrame(() => {
                                const ptr = window.NavBlock?.getCheckPointer?.();
                                if (ptr != null) window.Editor?.setCheckLines?.([ptr.line + 1]);
                                window.NavBlock?.applyColumnSelection?.();
                                _qnUpdateDirHint();
                            });
                            return;
                        }
                        // CHECK 모드: 오프셋 보존, nav_block에서 직접 처리
                        if (_cursorMode) {
                            window.NavBlock?.columnEndAll?.({ cursorOnly: true });
                        } else {
                            window.NavBlock?.columnEndAll?.();
                        }
                        requestAnimationFrame(_qnUpdateDirHint);
                        return;
                    }
                    // 같은 라인
                    if (_cursorMode) { window.NavBlock?.columnEndAll?.({ cursorOnly: true }); requestAnimationFrame(_qnUpdateDirHint); return; }
                    // 같은 라인 MULTI: BS 고정, BE만 줄끝으로
                    const cur = window.Editor?.getCursor?.();
                    if (cur) {
                        if (!bs) window.State?.setBS?.(cur);
                        const len = (window.Editor?.getLine?.(cur.line) || '').length;
                        const newBE = { line: cur.line, ch: len };
                        window.State?.setBE?.(newBE);
                        window.Editor?.setCursor?.(newBE);
                        window.NavBlock?.applyColumnSelection?.();
                        requestAnimationFrame(_qnUpdateDirHint);
                    }
                    return;
                }
                if (_qnPending() === 'alt'  && _qnShift) { window.Nav?.shiftMoveBlockToEnd?.(); return; }
                if ((_qnPending() === 'ctrl' || _qnPending() === 'alt') && _qnShift) { window.NavCursor?.selectDocEnd?.(); _qnAfterAction(); return; }
                if (_qnPending() === 'ctrl') { window.NavCursor?.jumpDocEnd?.(); _qnAfterAction(); return; }
                if (_qnPending() === 'alt')  { window.Nav?.jumpLastChange?.();      return; }
                // V2 homeEnd 이식: selection 있으면 스왑→softEnd→lineEnd, 없으면 softEnd→lineEnd
                try {
                    const _v = window.Editor?.get?.();
                    const _sel = _v?.state?.selection?.main;
                    if (_v && _sel) {
                        const doc = _v.state.doc;
                        // 1단계: head < anchor 이면 스왑 (selection 유지, head 오른쪽으로)
                        //   State.BS/BE 동기화는 cursorActivity 리스너가 자동 처리
                        if (_sel.head < _sel.anchor) {
                            _v.dispatch({ selection: { anchor: _sel.head, head: _sel.anchor } });
                            return;
                        }
                        // 2/3단계: softEnd ↔ lineEnd
                        const hLo = doc.lineAt(_sel.head);
                        const txt = doc.sliceString(hLo.from, hLo.to);
                        let soft = txt.length;
                        while (soft > 0 && (txt[soft-1] === ' ' || txt[soft-1] === '\t')) soft--;
                        const col = _sel.head - hLo.from;
                        const newHead = hLo.from + (col === soft ? txt.length : soft);
                        // newAnchor 결정 (qnHOME와 동일 규칙)
                        //   - Shift OFF → 항상 단순 커서 이동 (음영 해제)
                        //   - Shift ON + 영역 있음 → anchor 고정
                        //   - Shift ON + 한 점 → 현재 위치를 BS로 고정
                        let newAnchor;
                        if (!_qnShift)                          newAnchor = newHead;
                        else if (_sel.anchor !== _sel.head)     newAnchor = _sel.anchor;
                        else                                    newAnchor = _sel.head;
                        _v.dispatch({ selection: { anchor: newAnchor, head: newHead } });
                        // State.BS/BE 동기화 (BS=anchor, BE=head 불변식)
                        const _aLn = doc.lineAt(newAnchor);
                        const _hLn = doc.lineAt(newHead);
                        window.State?.setBS?.({ line: _aLn.number - 1, ch: newAnchor - _aLn.from });
                        window.State?.setBE?.({ line: _hLn.number - 1, ch: newHead   - _hLn.from });
                        return;
                    }
                } catch (e) {}
                // fallback
                _qnShift ? window.Nav?.selectLineEnd?.() : window.NavCursor?.jumpE?.();
            },
            () => { if (_multiMode) return; _qnShift ? window.Nav?.selectDocEnd?.() : window.NavCursor?.jumpDocEnd?.(); }
        );

        // 슬롯 화살표
        // Slot arrows handled by SlotManager._bindEvents() — skipped here
    }

    // ── UI 상태 머신 ──────────────────────────────────────
    // _ui: 'quick' | 'menu' | 'hidden'
    let _ui = 'quick';
    let _slotNavMode = false;

    function _litGreen(id, on) {
        const b = document.getElementById(id);
        if (!b) return;
        const s = getComputedStyle(document.documentElement);
        const green = s.getPropertyValue('--ac-green-tx').trim();
        b.style.background  = '';
        b.style.borderColor = on ? green : '';
        b.style.color       = on ? green : '';
    }

    function _setSlotNavActive(on) {
        _slotNavMode = on;
        window._slotNavMode = on;
        window._setSlotNavActive = _setSlotNavActive;
        if (on) { window._setFooterFindMode?.(false); window._setBookmarkMode?.(false); }
        if (on && window.NavFind?.isActive?.()) {
            window.NavFind.deactivateSilent?.();
        }
        _litGreen('btnFooterPaste', on);
        _litGreen('btnFooterSave',  on);
        _litGreen('btnFooterLeft',  on);
        _litGreen('btnFooterRight', on);
        const pb = document.getElementById('btnFooterPaste');
        if (pb) pb.textContent = on ? '↹' : '⎘';
        const sb = document.getElementById('btnFooterSave');
        if (sb) {
            if (on) {
                sb.innerHTML = '↹';
            } else {
                sb.innerHTML = `<svg width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="margin-top:2px"><rect x="0.6" y="0.6" width="11.8" height="11.8" rx="1.5" fill="currentColor" opacity="0.55" stroke="currentColor" stroke-width="1.1" stroke-opacity="0.7"/><rect x="2.5" y="1.5" width="5.5" height="3.5" rx="0.3" fill="var(--floppy-fill, #c8d0dc)" opacity="0.85"/><rect x="7" y="1.8" width="0.9" height="2.8" rx="0.2" fill="currentColor" opacity="0.4"/><rect x="2.5" y="7" width="8" height="4.8" rx="0.6" fill="var(--floppy-fill, #c8d0dc)" opacity="0.8" stroke="currentColor" stroke-width="0.5" stroke-opacity="0.3"/><circle cx="6.5" cy="9.3" r="1.2" fill="var(--floppy-dot, #5a6a82)" opacity="0.9"/></svg>`;
                const isDirty = !!window.SlotManager?.isCurrentSlotDirty?.();
                sb.classList.toggle('is-dirty', isDirty);
            }
        }
        const closeBtn = document.getElementById('btnFooterClose');
        if (closeBtn) closeBtn.style.display = on ? '' : 'none';
        // OFF 시 풋터 좌/우 disable 초기화
        if (!on) {
            const fL = document.getElementById('btnFooterLeft');
            const fR = document.getElementById('btnFooterRight');
            if (fL) fL.disabled = false;
            if (fR) fR.disabled = false;
        }
        try { localStorage.setItem('usekit_slot_nav', on ? '1' : '0'); } catch(e) {}
        _updateMarkOverlay();
    }

    function _uiGo(next) {
        _ui = next;
        window.ActiveState?.setUI?.('uiMode', next);
        const _app = document.querySelector('.editor-app');

        if (next === 'quick') {
            const qp = document.querySelector('.swipe-panel.panel-quick');
            if (_app && qp) {
                document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
                qp.classList.add('active');
                _app.classList.remove('nav-hidden');
                UI.recalcHeight?.();
            }
        } else if (next === 'menu') {
            const bp = document.querySelector('.swipe-panel.panel-buttons');
            if (_app && bp) {
                document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
                bp.classList.add('active');
                document.querySelectorAll('.indicator-dot').forEach((d,i) => d.classList.toggle('active', i===0));
                _app.classList.remove('nav-hidden');
                UI.recalcHeight?.();
            }
        } else if (next === 'nav') {
            const np = document.querySelector('.swipe-panel.panel-navigation');
            if (_app && np) {
                document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
                np.classList.add('active');
                _app.classList.remove('nav-hidden');
                UI.recalcHeight?.();
            }
        } else if (next === 'hidden') {
            _hideNavPanel();
        }
        UIStats.updateKUButton(false);
    }

    function _hideNavPanel() {
        const app = document.querySelector('.editor-app');
        if (!app) return;
        document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
        app.classList.add('nav-hidden');
        if (window.UI && UI.recalcHeight) UI.recalcHeight();
    }

    function _slideNavPanel() {
        const app = document.querySelector('.editor-app');
        if (!app) return;
        if (app.classList.contains('nav-hidden')) {
            app.classList.remove('nav-hidden');
            if (window.UI && UI.recalcHeight) UI.recalcHeight();
            return;
        }
        const panels = document.querySelectorAll('.swipe-panel');
        let activeIdx = -1;
        panels.forEach((p, i) => { if (p.classList.contains('active')) activeIdx = i; });
        const nextIdx = (activeIdx + 1) % panels.length;
        panels.forEach((p, i) => p.classList.toggle('active', i === nextIdx));
        // indicator dot 동기화
        const dots = document.querySelectorAll('.indicator-dot');
        dots.forEach((d, i) => d.classList.toggle('active', i === nextIdx));
        // uiMode 동기화
        const activePanel = panels[nextIdx];
        if (activePanel) {
            const nextMode = activePanel.classList.contains('panel-buttons') ? 'menu'
                           : activePanel.classList.contains('panel-navigation') ? 'nav'
                           : 'quick';
            _ui = nextMode;
            window.ActiveState?.setUI?.('uiMode', nextMode);
        }
    }

    function _bindSwipeGesture() {
        // 인디케이터 영역에서만 스와이프 — 버튼 오발 없음
        const indicator = document.getElementById('swipeIndicator');
        if (!indicator) return;
        let _startX = 0, _valid = false;
        indicator.addEventListener('touchstart', (e) => {
            _startX = e.touches[0].clientX;
            _valid  = true;
        }, { passive: true });
        indicator.addEventListener('touchend', (e) => {
            if (!_valid) return;
            _valid = false;
            const dx = e.changedTouches[0].clientX - _startX;
            if (Math.abs(dx) <= 20) return;
            const panels = document.querySelectorAll('.swipe-panel');
            let activeIdx = -1;
            panels.forEach((p, i) => { if (p.classList.contains('active')) activeIdx = i; });
            if (activeIdx === 0 && dx < 0) _slideNavPanel();
            else if (activeIdx === 1 && dx > 0) _slideNavPanel();
        }, { passive: true });
        indicator.addEventListener('touchcancel', () => { _valid = false; }, { passive: true });
    }

    function _bindCMEvents() {
        // 에디터 클릭 시 S 모드면 BE 업데이트
        Editor.on('mousedown', () => {
            if (window._uiIsBlockMode?.()) {
                // M-LOCK ON: 클릭으로 앵커 변경 차단 (shiftBlock으로만 이동)
                if (window._uiIsMLock?.()) return;
                // CHECK ON: BS 고정, 클릭 위치는 무시 (멀티커서 유지)
                if (window._uiIsCheckMode?.()) return;
                requestAnimationFrame(() => {
                    const cur = Editor.getCursor();
                    State.setBS(cur);
                    State.setBE(cur);
                    window._uiClearColOffsets?.();
                    NavBlock.clearColumnOverlay?.();
                    UI.updateStats();
                });
                return;
            }
            // 단일커서 + Shift ON → 클릭 시 anchor 유지 + head=클릭 위치
            //   Shift OFF 이면 CM6 기본 동작(음영 해제, 커서 이동) 그대로
            //   BS/BE 존재 여부 체크 불필요 — 한 점 커서면 anchor===head 가 곧 BS가 됨
            if (window._qnShift) {
                const v0 = window.Editor?.get?.();
                const preservedAnchor = v0?.state?.selection?.main?.anchor;
                if (preservedAnchor == null) return;
                requestAnimationFrame(() => {
                    const v = window.Editor?.get?.();
                    if (!v) return;
                    const doc = v.state.doc;
                    const clickedHead = v.state.selection.main.head;
                    // anchor 유지, head만 클릭 위치로 재dispatch
                    v.dispatch({ selection: { anchor: preservedAnchor, head: clickedHead } });
                    // State.BS/BE 갱신 (불변식 BS=anchor, BE=head)
                    const aLn = doc.lineAt(preservedAnchor);
                    const hLn = doc.lineAt(clickedHead);
                    window.State?.setBS?.({ line: aLn.number - 1, ch: preservedAnchor - aLn.from });
                    window.State?.setBE?.({ line: hLn.number - 1, ch: clickedHead     - hLn.from });
                    UI.updateStats?.();
                });
                return;
            }
            if (State.getModeS()) {
                requestAnimationFrame(() => NavBlock.afterMove());
            }
            // A모드: 블록 밖 클릭 시 클릭 위치 그대로 초기화 (anchor 복귀 없이)
            if (State.getModeA()) {
                requestAnimationFrame(() => {
                    const view = Editor.get();
                    if (view && view.state.selection.main.empty) {
                        State.setModeA(false);
                        UI.updateStats();
                    }
                });
            }
        });

        // 변경 시 undo/redo 버튼 상태
        Editor.on('changes', (view, update) => {
            UIStats.updateUndoRedo();
            if (update && update.docChanged) {
                const pos = view.state.selection.main.head;
                window.Nav?.trackChange?.(pos);
            }
        });

        // CM6 selection 변경 시 State.BS/BE 동기화 (단일커서 경로만)
        //   - OS 투핸들, 마우스 드래그, 기타 selection 변경을 State에 반영
        //   - 불변식 BS=anchor, BE=head (한 점이면 둘 다 같은 값)
        Editor.on('cursorActivity', (view) => {
            if (window._uiIsBlockMode?.()) return; // 멀티는 BlockState 담당
            const sel = view.state.selection.main;
            const doc = view.state.doc;
            const aLn = doc.lineAt(sel.anchor);
            const hLn = doc.lineAt(sel.head);
            window.State?.setBS?.({ line: aLn.number - 1, ch: sel.anchor - aLn.from });
            window.State?.setBE?.({ line: hLn.number - 1, ch: sel.head   - hLn.from });
        });

        // CHECK ON + 클릭 → 기존 range면 mainIdx 변경, 없으면 ghost 설정
        //   contentDOM pointerdown 에서 좌표를 직접 받아 posAtCoords 로 라인 계산
        const _cmView = Editor.get();
        if (_cmView?.contentDOM) {
            _cmView.contentDOM.addEventListener('pointerdown', (e) => {
                if (!window._uiIsCheckMode?.()) return;
                if (window._uiIsMLock?.())     return; // M-LOCK 중엔 건드리지 않음
                const v = window.Editor?.get?.();
                if (!v) return;
                const pos = v.posAtCoords({ x: e.clientX, y: e.clientY });
                if (pos == null) return;
                const doc = v.state.doc;
                const clickedLine = doc.lineAt(pos).number - 1;
                // 기존 ranges 에서 클릭 라인 검색
                const ranges = window.BlockState?.getRanges?.() ?? [];
                let foundIdx = -1;
                for (let i = 0; i < ranges.length; i++) {
                    const r = ranges[i];
                    const lineNum = doc.lineAt(r.head).number - 1;
                    if (lineNum === clickedLine) { foundIdx = i; break; }
                }
                const curGhost = window.NavBlockV2?.getGhost?.();
                requestAnimationFrame(() => {
                    if (foundIdx >= 0) {
                        // 기존 커서 있음 → mainIdx 변경 (베이지 하이라이트 이동)
                        window.BlockState?.setMainIdx?.(foundIdx);
                        window.NavBlockV2?.renderWithGhost?.();
                    } else if (curGhost === clickedLine) {
                        // 같은 ghost 라인 재클릭 → ON/OFF 확정 + 클릭 정확 위치로 커서 삽입
                        window.NavBlockV2?.checkTabToggle?.({ forcedOffset: pos });
                    } else {
                        // 새 라인 → ghost 설정
                        window.NavBlockV2?.setGhost?.(clickedLine);
                        window.NavBlockV2?.renderWithGhost?.();
                    }
                });
            });
        }
    }
    function _bindKeyboard() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                SlotManager.save({ silent: false });
            }
            if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
                e.preventDefault();
                Nav.undo();
            }
        });
    }

    function _resyncPurpleButtons() {
        // Wrap 버튼
        _updateWrapBtnState();
        // LineNum 버튼
        _updateLineNumBtn(Editor.getOption('lineNumbers') !== false);
        // Find 버튼 (보라) - NavFind가 활성이면
        if (window.NavFind?.isActive?.()) {
            const s = getComputedStyle(document.documentElement);
            const btn = document.getElementById('btnFooterFind');
            if (btn) {
                btn.style.background  = s.getPropertyValue('--ac-purple-bg').trim();
                btn.style.borderColor = s.getPropertyValue('--ac-purple-bd').trim();
                btn.style.color       = s.getPropertyValue('--ac-purple').trim();
            }
        }
        // Focus 버튼
        if (window.NavFocus?.isOn?.()) window.NavFocus._resyncColor?.();
        // Save/슬롯네비 버튼 (초록)
        if (_slotNavMode) {
            _litGreen('btnFooterSave',  true);
            _litGreen('btnFooterPaste', true);
            _litGreen('btnFooterLeft',  true);
            _litGreen('btnFooterRight', true);
            const sb = document.getElementById('btnFooterSave');
            if (sb) sb.innerHTML = '↹';
            const pb = document.getElementById('btnFooterPaste');
            if (pb) pb.textContent = '↹';
        }
        // Keyboard/LK 버튼 — _syncButtonColors로 통합 처리
        _syncButtonColors();
    }

    return { init, _resyncPurpleButtons, resyncEditorButtons, _syncButtonColors, syncUiMode: (mode) => { _ui = mode; } };
})();

window.UIEvents = UIEvents;
