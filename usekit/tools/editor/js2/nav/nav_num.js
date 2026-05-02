const NavNum = (function () {
    'use strict';

    const BASE_A = [-10, -4, -1, 1, 4, 10];  // even pattern (default)
    const BASE_B = [-7,  -5, -3, 3, 5,  7];  // odd pattern

    const ROWS = {
        row2: {
            btnIds:       ['btnLineMinus10','btnLineMinus4','btnLineMinus1','btnLine1','btnLine4','btnLine10'],
            axisBtnId:    'btnAxis',
            scaleBtnId:   'btnNavScale2',
            patternBtnId: 'btnPatternToggle',
        },
        row3: {
            btnIds:       ['btnThirdMinus10','btnThirdMinus4','btnThirdMinus1','btnThird1','btnThird4','btnThird10'],
            axisBtnId:    'btnAxisV',
            scaleBtnId:   'btnNavScale10',
            patternBtnId: 'btnThirdPatternToggle',
        },
    };

    // Independent state per row
    const _state = {
        row2: { axis: 'horizontal', scaleX2: false, patternB: false },
        row3: { axis: 'vertical',   scaleX10: false, patternB: false },
    };
    function _calcRow2(idx) {
        let val = (_state.row2.patternB ? BASE_B : BASE_A)[idx];
        if (_state.row2.scaleX2) val *= 2;
        return val;
    }

    function _calcRow3(idx) {
        let val = (_state.row3.patternB ? BASE_B : BASE_A)[idx];
        if (_state.row3.scaleX10) val *= 10;
        return val;
    }
    function _move(value, axis) {
        if (axis === 'vertical') {
            if (value < 0) Nav.moveUp(Math.abs(value));
            else           Nav.moveDown(value);
        } else {
            const pos     = Editor.getCursor();
            const lineLen = (Editor.getLine(pos.line) || '').length;
            const newCh   = Math.max(0, Math.min(pos.ch + value, lineLen));
            Editor.setCursor({ line: pos.line, ch: newCh });
            NavBlock.afterMove();
            UI.updateStats();
        }
    }

    // M 모드: 수평=스페이스 삽입/제거, 수직=라인(블록) 스왑
    function _moveM(value, axis) {
        const hasBlock = State.hasBlock?.() ?? (State.getBS?.() && State.getBE?.());
        if (axis === 'vertical') {
            // 수직: 라인/블록 스왑 — 한 번에 처리
            NavBlock.moveBlockBy(value);
            UI.updateStats();
        } else {
            // 수평: 스페이스 삽입/제거
            if (hasBlock) {
                // 블록 전체 indent/unindent
                NavBlock.indent(value);
            } else {
                // 단일 커서: 커서 앞에 스페이스 삽입 or 제거
                const pos = Editor.getCursor();
                const line = Editor.getLine(pos.line) || '';
                if (value > 0) {
                    // 스페이스 삽입 (value 개수만큼)
                    const spaces = ' '.repeat(Math.abs(value));
                    Editor.replaceRange(spaces, pos, pos);
                    Editor.setCursor({ line: pos.line, ch: pos.ch + Math.abs(value) });
                } else {
                    // 커서 앞 스페이스 제거 (있는 만큼만)
                    const remove = Math.abs(value);
                    let removed = 0;
                    let ch = pos.ch;
                    while (removed < remove && ch > 0 && line[ch - 1] === ' ') {
                        ch--;
                        removed++;
                    }
                    if (removed > 0) {
                        Editor.replaceRange('', { line: pos.line, ch }, { line: pos.line, ch: pos.ch });
                        Editor.setCursor({ line: pos.line, ch });
                    }
                }
                NavBlock.afterMove();
            }
            UI.updateStats();
        }
    }

    function trigger(btnId) {
        const modeM = State.getModeM?.() ?? false;
        const modeF = State.getModeF?.() ?? false;

        const r2 = ROWS.row2.btnIds.indexOf(btnId);
        if (r2 >= 0) {
            if (modeF) {
                _state.row2.axis === 'vertical'
                    ? NavFocus.scrollV(_calcRow2(r2))
                    : NavFocus.scrollH(_calcRow2(r2));
            } else {
                modeM ? _moveM(_calcRow2(r2), _state.row2.axis)
                      : _move(_calcRow2(r2),  _state.row2.axis);
            }
            return;
        }

        const r3 = ROWS.row3.btnIds.indexOf(btnId);
        if (r3 >= 0) {
            if (modeF) {
                _state.row3.axis === 'vertical'
                    ? NavFocus.scrollV(_calcRow3(r3))
                    : NavFocus.scrollH(_calcRow3(r3));
            } else {
                modeM ? _moveM(_calcRow3(r3), _state.row3.axis)
                      : _move(_calcRow3(r3),  _state.row3.axis);
            }
            return;
        }
    }
    function toggleAxis(rowKey) {
        const st = _state[rowKey];
        st.axis = (st.axis === 'vertical') ? 'horizontal' : 'vertical';
        _refreshRow(rowKey);
    }

    function toggleScale2() {
        _state.row2.scaleX2 = !_state.row2.scaleX2;
        _refreshRow('row2');
    }

    function toggleScale10() {
        _state.row3.scaleX10 = !_state.row3.scaleX10;
        _refreshRow('row3');
    }

    function togglePattern(rowKey) {
        _state[rowKey].patternB = !_state[rowKey].patternB;
        _refreshRow(rowKey);
    }
    function _btnActive(el, on) {
        const s = getComputedStyle(document.documentElement);
        el.style.background  = on ? s.getPropertyValue('--ac-active-bg').trim() : '';
        el.style.borderColor = on ? s.getPropertyValue('--ac-active-bd').trim() : '';
        el.style.color       = on ? s.getPropertyValue('--ac-active-tx').trim() : '';
    }

    function _refreshRow(rowKey) {
        const row  = ROWS[rowKey];
        const st   = _state[rowKey];
        const isH  = st.axis === 'horizontal';

        // Axis button — highlight only when vertical (non-default for row2, default for row3)
        const axisBtn = document.getElementById(row.axisBtnId);
        if (axisBtn) {
            const icon = axisBtn.querySelector('.axis-icon') || axisBtn;
            icon.textContent = isH ? '↔' : '↕';
            const highlight = (rowKey === 'row2') ? !isH : isH;
            _btnActive(axisBtn, highlight);
        }

        // Scale button
        const scaleBtn = document.getElementById(row.scaleBtnId);
        if (scaleBtn) {
            if (rowKey === 'row2') {
                const on = st.scaleX2;
                scaleBtn.textContent = on ? '÷2' : '×2';
                _btnActive(scaleBtn, on);
            } else {
                const on = st.scaleX10;
                scaleBtn.textContent = on ? '÷10' : '×10';
                _btnActive(scaleBtn, on);
            }
        }

        // Pattern button
        const patBtn = document.getElementById(row.patternBtnId);
        if (patBtn) {
            const on = st.patternB;
            patBtn.textContent = on ? 'o/e' : 'e/o';
            _btnActive(patBtn, on);
        }

        // Numpad labels
        row.btnIds.forEach((id, i) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.textContent = String(rowKey === 'row2' ? _calcRow2(i) : _calcRow3(i));
        });
    }
    function init() {
        _refreshRow('row2');
        _refreshRow('row3');
    }

    function resetAll() {
        _state.row2.axis     = 'horizontal';
        _state.row2.scaleX2  = false;
        _state.row2.patternB = false;
        _state.row3.axis     = 'vertical';
        _state.row3.scaleX10 = false;
        _state.row3.patternB = false;
        _refreshRow('row2');
        _refreshRow('row3');
    }

    return { init, trigger, toggleAxis, togglePattern, toggleScale2, toggleScale10, resetAll };
})();

window.NavNum = NavNum;
