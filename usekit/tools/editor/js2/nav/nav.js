/* Path: usekit/tools/editor/js2/nav/nav.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 통합 Nav API — 모든 이동/편집 명령의 단일 진입점
 * ─────────────────────────────────────────────────────────── */

const Nav = (function () {
    'use strict';

    // 이동 후 S 모드 처리 공통
    function _afterMove() {
        NavBlock.afterMove();
        UI.updateStats();
    }
    function moveLeft()  { NavCursor.moveLeft();  _afterMove(); }
    function moveRight() { NavCursor.moveRight(); _afterMove(); }
    function moveUp(n)   { NavCursor.moveUp(n);   _afterMove(); }
    function moveDown(n) { NavCursor.moveDown(n); _afterMove(); }
    function pageUp()    {
        const view = Editor.get?.();
        if (!view) return;
        const lineH = view.defaultLineHeight || 20;
        const visH  = view.scrollDOM.clientHeight || 300;
        const lines = Math.max(1, Math.floor(visH / lineH) - 1);
        Editor.scrollByLines?.(-lines);
        NavCursor.moveUp(lines);
        _afterMove();
    }
    function pageDown()  {
        const view = Editor.get?.();
        if (!view) return;
        const lineH = view.defaultLineHeight || 20;
        const visH  = view.scrollDOM.clientHeight || 300;
        const lines = Math.max(1, Math.floor(visH / lineH) - 1);
        Editor.scrollByLines?.(lines);
        NavCursor.moveDown(lines);
        _afterMove();
    }
    function selectLeft()  { NavCursor.selectLeft();      _afterMove(); Editor.focus(); }
    function selectRight() { NavCursor.selectRight();     _afterMove(); Editor.focus(); }
    function selectUp()    { NavCursor.selectUp();        _afterMove(); Editor.focus(); }
    function selectDown()  { NavCursor.selectDown();      _afterMove(); Editor.focus(); }
    function selectLineStart() { NavCursor.selectLineStart(); _afterMove(); Editor.focus(); }
    function selectLineEnd()   { NavCursor.selectLineEnd();   _afterMove(); Editor.focus(); }
    function selectDocStart()  { NavCursor.selectDocStart();  _afterMove(); Editor.focus(); }
    function selectDocEnd()    { NavCursor.selectDocEnd();    _afterMove(); Editor.focus(); }
    function jumpH()          { NavCursor.jumpH();          _afterMove(); }
    function jumpLineStart()  { NavCursor.jumpLineStart();  _afterMove(); }
    function jumpE()     { NavCursor.jumpE();     _afterMove(); }
    function swapHE()    { NavBlock.swapHE();     _afterMove(); }
    function jumpDocStart() { NavCursor.jumpDocStart(); _afterMove(); }
    function jumpDocEnd()   { NavCursor.jumpDocEnd();   _afterMove(); }
    function jumpToLine(n)  { NavCursor.jumpToLine(n);  _afterMove(); }
    function toggleModeS() {
        NavBlock.toggleModeS();
        UI.updateStats();
        UI.updateFooter();
    }

    function toggleModeM() {
        State.toggleModeM();
        UI.updateStats();
        UI.updateFooter();
    }

    // ── progressive select (a/A 버튼) ──────────────────────────
    // 단계: word → line → block(BS~BE) → doc
    // 현재 선택 상태를 보고 자동으로 다음 단계 결정
    // ── A모드 progressive select ──────────────────────────────
    // 단계: 1=단어 2=라인 3=전체
    // anchor 고정, head만 확장. 방향키로 head 조절 가능.
    function progressiveSelect() {
        const view = Editor.get();
        if (!view) return;

        // S켜져 있으면 해제
        if (State.getModeS()) {
            State.setModeS(false);
            State.clearBlock();
        }

        const step = State.getModeAStep();
        const pos  = Editor.getCursor();
        const doc  = view.state.doc;

        if (step === 0) {
            // 단어 선택
            State.setModeA(true);
            State.setModeAAnchor(pos);
            const posOff = doc.line(pos.line + 1).from + pos.ch;
            const word = view.state.wordAt(posOff);
            if (word) {
                view.dispatch({ selection: { anchor: word.from, head: word.to } });
            } else {
                // 단어 없으면 바로 라인
                _selectLineModeA(pos, doc);
                State.setModeAStep(2);
                _updateModeABtn();
                UI.updateStats();
                return;
            }
            State.setModeAStep(1);
        } else if (step === 1) {
            // 라인 선택
            _selectLineModeA(State.getModeAAnchor() || pos, doc);
            State.setModeAStep(2);
        } else if (step === 2) {
            // 전체 선택
            const total = doc.lines - 1;
            const lastLen = doc.line(doc.lines).length;
            view.dispatch({ selection: { anchor: 0, head: doc.length } });
            State.setModeAStep(3);
        } else {
            // step3 → 초기화
            resetModeA();
            return;
        }

        _updateModeABtn();
        UI.updateStats();
    }

    function _selectLineModeA(pos, doc) {
        const view = Editor.get();
        if (!view) return;
        const lineObj = doc.line(pos.line + 1);
        view.dispatch({ selection: { anchor: lineObj.from, head: lineObj.to } });
    }

    // A모드 방향키 — anchor 고정, head만 이동
    function modeAMoveLeft() {
        const view = Editor.get();
        if (!view || !State.getModeA()) return;
        const sel = view.state.selection.main;
        const newHead = Math.max(0, sel.head - 1);
        view.dispatch({ selection: { anchor: sel.anchor, head: newHead } });
        UI.updateStats();
    }
    function modeAMoveRight() {
        const view = Editor.get();
        if (!view || !State.getModeA()) return;
        const sel = view.state.selection.main;
        const newHead = Math.min(view.state.doc.length, sel.head + 1);
        view.dispatch({ selection: { anchor: sel.anchor, head: newHead } });
        UI.updateStats();
    }
    function modeAMoveUp() {
        const view = Editor.get();
        if (!view || !State.getModeA()) return;
        const sel = view.state.selection.main;
        const headLine = view.state.doc.lineAt(sel.head);
        if (headLine.number <= 1) return;
        const prevLine = view.state.doc.line(headLine.number - 1);
        const headCh = sel.head - headLine.from;
        const newHead = prevLine.from + Math.min(headCh, prevLine.length);
        view.dispatch({ selection: { anchor: sel.anchor, head: newHead } });
        UI.updateStats();
    }
    function modeAMoveDown() {
        const view = Editor.get();
        if (!view || !State.getModeA()) return;
        const sel = view.state.selection.main;
        const headLine = view.state.doc.lineAt(sel.head);
        if (headLine.number >= view.state.doc.lines) return;
        const nextLine = view.state.doc.line(headLine.number + 1);
        const headCh = sel.head - headLine.from;
        const newHead = nextLine.from + Math.min(headCh, nextLine.length);
        view.dispatch({ selection: { anchor: sel.anchor, head: newHead } });
        UI.updateStats();
    }

    // A모드에서 현재 커서가 H쪽인지 E쪽인지 판단
    // anchor <= head 이면 head가 E쪽 (커서가 끝에)
    // anchor > head 이면 head가 H쪽 (커서가 앞에)
    function _modeASide() {
        const view = Editor.get();
        if (!view) return 'E';
        const sel = view.state.selection.main;
        return sel.anchor <= sel.head ? 'E' : 'H';
    }

    function modeAH(type) {
        const side = _modeASide();
        if (side === 'H') {
            // H에서 H — 기본 커서 제어 (head만 이동)
            const view = Editor.get();
            if (!view) return;
            const sel = view.state.selection.main;
            const headLine = view.state.doc.lineAt(sel.head);
            const headCh = sel.head - headLine.from;
            const firstNonSpace = view.state.doc.lineAt(sel.head).text.search(/\S/);
            let newHead;
            if (type === 'long') {
                newHead = 0;  // 문서 처음
            } else if (type === 'double') {
                newHead = headLine.from;  // 라인 col 0
            } else {
                // 짧게: firstNonSpace <-> col0 토글
                newHead = (headCh !== firstNonSpace && firstNonSpace >= 0)
                    ? headLine.from + firstNonSpace
                    : headLine.from;
            }
            view.dispatch({ selection: { anchor: sel.anchor, head: newHead } });
            UI.updateStats();
        } else {
            // E에서 H — 스왑
            modeASwap();
        }
    }

    function modeAE(type) {
        const side = _modeASide();
        if (side === 'E') {
            // E에서 E — 기본 커서 제어 (head만 이동)
            const view = Editor.get();
            if (!view) return;
            const sel = view.state.selection.main;
            const headLine = view.state.doc.lineAt(sel.head);
            let newHead;
            if (type === 'long') {
                newHead = view.state.doc.length;  // 문서 끝
            } else {
                newHead = headLine.to;  // 라인 끝
            }
            view.dispatch({ selection: { anchor: sel.anchor, head: newHead } });
            UI.updateStats();
        } else {
            // H에서 E — 스왑
            modeASwap();
        }
    }

    // A모드 anchor ↔ head 스왑

    // A모드 초기화 — anchor로 커서 복귀
    function resetModeA() {
        const view = Editor.get();
        const anchor = State.getModeAAnchor();
        State.setModeA(false);
        if (view && anchor) {
            const doc = view.state.doc;
            const lineObj = doc.line(Math.min(anchor.line + 1, doc.lines));
            const off = lineObj.from + Math.min(anchor.ch, lineObj.length);
            view.dispatch({ selection: { anchor: off, head: off } });
        }
        _updateModeABtn();
        UI.updateStats();
    }

    function _updateModeABtn() {
        const btn = document.getElementById('btnSelectAll');
        if (!btn) return;
        const on = State.getModeA();
        btn.classList.toggle('is-active', on);
    }

    function _selectLine(pos) {
        const len = (Editor.getLine(pos.line) || '').length;
        Editor.setSelection({ line: pos.line, ch: 0 }, { line: pos.line, ch: len });
    }

    function selectAll() {
        State.clearBlock();
        const total = Editor.lineCount() - 1;
        const lastLen = (Editor.getLine(total) || '').length;
        Editor.setSelection({ line: 0, ch: 0 }, { line: total, ch: lastLen });
        UI.updateStats();
    }
    function selectAllModeA() {
        // 전체 선택 + modeA step3 진입 (다음 탭에서 reset 가능)
        if (State.getModeS()) { State.setModeS(false); State.clearBlock(); }
        State.setModeA(true);
        if (!State.getModeAAnchor()) State.setModeAAnchor(Editor.getCursor());
        const total = Editor.lineCount() - 1;
        const lastLen = (Editor.getLine(total) || '').length;
        Editor.setSelection({ line: 0, ch: 0 }, { line: total, ch: lastLen });
        State.setModeAStep(3);
        _updateModeABtn();
        UI.updateStats();
    }
    function moveBlock(n)  { NavBlock.moveBlockBy(n); UI.updateStats(); }
    function moveLineAlt(n) { NavBlock.moveLineAlt(n);  UI.updateStats(); }

    function toggleComment() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const { state, dispatch } = view;
        const sel = state.selection.main;
        const fromLine = state.doc.lineAt(sel.from);
        const toLine   = state.doc.lineAt(sel.to);
        // 모든 선택 라인이 //로 시작하면 제거, 아니면 추가
        const lines = [];
        for (let i = fromLine.number; i <= toLine.number; i++) lines.push(state.doc.line(i));
        const allCommented = lines.every(l => /^(\s*)(\/\/)/.test(l.text));
        const changes = lines.map(l => {
            if (allCommented) {
                const m = l.text.match(/^(\s*)\/\/ ?/);
                return { from: l.from, to: l.from + m[0].length, insert: m[1] };
            } else {
                const m = l.text.match(/^(\s*)/);
                return { from: l.from + m[1].length, to: l.from + m[1].length, insert: '// ' };
            }
        });
        dispatch({ changes });
        UI.updateStats?.();
    }

    function selectCurrentLine() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const { state, dispatch } = view;
        const line = state.doc.lineAt(state.selection.main.head);
        dispatch({ selection: { anchor: line.from, head: line.to } });
        UI.updateStats?.();
    }

    function selectWordLeft() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const sel = view.state.selection.main;
        const moved = view.moveByGroup(sel, false);
        view.dispatch({ selection: { anchor: sel.anchor, head: moved.head }, scrollIntoView: true });
        _afterMove();
    }

    function selectWordRight() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const sel = view.state.selection.main;
        const moved = view.moveByGroup(sel, true);
        view.dispatch({ selection: { anchor: sel.anchor, head: moved.head }, scrollIntoView: true });
        _afterMove();
    }

    function selectDocStart() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const anchor = view.state.selection.main.anchor;
        view.dispatch({ selection: { anchor, head: 0 }, scrollIntoView: true });
        _afterMove();
    }

    function selectDocEnd() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const anchor = view.state.selection.main.anchor;
        view.dispatch({ selection: { anchor, head: view.state.doc.length }, scrollIntoView: true });
        _afterMove();
    }

    function wordLeft() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const newSelL = view.moveByGroup(view.state.selection.main, false);
        view.dispatch({ selection: newSelL, scrollIntoView: true });
        _afterMove();
    }

    function wordRight() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const newSelR = view.moveByGroup(view.state.selection.main, true);
        view.dispatch({ selection: newSelR, scrollIntoView: true });
        _afterMove();
    }

    function deleteWordBefore() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const { state } = view;
        const pos = state.selection.main.head;
        const line = state.doc.lineAt(pos);
        const textBefore = line.text.slice(0, pos - line.from);
        const m = textBefore.match(/\S+\s*$|\s+$/);
        if (!m) {
            // 빈 라인 또는 라인 처음: 이전 개행 삭제
            if (pos > 0) view.dispatch({ changes: { from: pos - 1, to: pos } });
            return;
        }
        view.dispatch({ changes: { from: pos - m[0].length, to: pos } });
        _afterMove();
    }

    function deleteWordAfter() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const { state } = view;
        const pos = state.selection.main.head;
        const line = state.doc.lineAt(pos);
        const textAfter = line.text.slice(pos - line.from);
        const m = textAfter.match(/^\s*\S+|^\s+/);
        if (!m) {
            // 빈 라인 또는 라인 끝: 다음 개행 삭제
            if (pos < state.doc.length) view.dispatch({ changes: { from: pos, to: pos + 1 } });
            return;
        }
        view.dispatch({ changes: { from: pos, to: pos + m[0].length } });
        _afterMove();
    }

    function insertLineBelow() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const pos  = view.state.selection.main.head;
        const line = view.state.doc.lineAt(pos);
        view.dispatch({
            changes:  { from: line.to, insert: '\n' },
            selection: { anchor: line.to + 1 },
            scrollIntoView: true,
        });
    }

    function indent(n)     { NavBlock.indent(n); if (window._uiIsBlockMode?.()) window.NavBlock?.applyColumnSelection?.(); UI.updateStats(); }

    // Shift 블록(CM6 selection) 상태에서 블록 무브/인덴트
    function _withShiftBlock(fn) {
        const anchor = Editor.getAnchorPos?.() || Editor.getCursor();
        const head   = Editor.getCursor();
        if (anchor.line === head.line && anchor.ch === head.ch) return; // 선택 없음
        State.setBS(anchor);
        State.setBE(head);
        fn();
    }
    function shiftMoveBlock(n) {
        const anchor = Editor.getAnchorPos?.() || Editor.getCursor();
        const head   = Editor.getCursor();
        const hasSel = !(anchor.line === head.line && anchor.ch === head.ch);
        if (hasSel) {
            State.setBS(anchor);
            State.setBE(head);
        }
        NavBlock.moveBlockBy(n);
        UI.updateStats();
    }
    function shiftIndent(n) {
        const anchor = Editor.getAnchorPos?.() || Editor.getCursor();
        const head   = Editor.getCursor();
        const hasSel = !(anchor.line === head.line && anchor.ch === head.ch);
        if (hasSel) {
            State.setBS(anchor);
            State.setBE(head);
        }
        // 선택 없으면 indent가 커서 라인 단독 처리
        NavBlock.indent(n);
        UI.updateStats();
    }
    function copyBlock()   {
        const text = NavBlock.copyBlock();
        if (text) window.NavClipboard?.push(text);
        return text;
    }
    function cutLine()     {
        // cutLine은 내부에서 clipboard.writeText 하지만 텍스트를 반환하지 않음
        // → 먼저 현재 줄 텍스트를 캡처해서 push
        const pos = Editor.getCursor();
        const lineText = Editor.getLine(pos.line) || '';
        if (lineText) window.NavClipboard?.push(lineText);
        NavBlock.cutLine();
        UI.updateStats();
    }

    function pasteAtCursor() {
        // 내부 클립보드 우선 (모바일에서 readText 권한 문제 회피)
        const internal = NavBlock.getClipData();
        if (internal) {
            _insertText(internal);
            UI.updateStats();
            return;
        }
        // 폴백: 시스템 클립보드
        navigator.clipboard?.readText?.().then(text => {
            if (!text) return;
            NavBlock.setClipData(text);
            _insertText(text);
            UI.updateStats();
        }).catch(() => {});
    }

    // CM6: make edits behave like real keyboard input.
    // - Replaces current selection (if any)
    // - Moves caret to the end of inserted text
    // - Marks as userEvent='input' so CM6 treats it like typing
    function _insertText(text) {
        const view = Editor.get?.();
        if (!view) return;
        const sel = view.state.selection.main;
        const from = sel.from;
        const to   = sel.to;
        const ins  = text ?? '';
        view.dispatch({
            changes:   { from, to, insert: ins },
            selection: { anchor: from + ins.length },
            userEvent: 'input',
        });
    }
    function backspace() {
        // CM6 deleteCharBackward already matches keyboard semantics
        Editor.execCommand('delCharBefore');
        _afterMove();
    }

    function insertSpace() {
        _insertText(' ');
        _afterMove();
    }

    function insertNewline() {
        _insertText('\n');
        _afterMove();
    }

    function forwardDelete() {
        // CM6 deleteCharForward already matches keyboard semantics
        Editor.execCommand('delCharAfter');
        _afterMove();
    }
    let _jumpPopup = null;
    let _jumpPopupBound = false;
    let _jumpDragBound = false;

    function _jumpLineCount() {
        return Math.max(1, Editor.lineCount?.() || 1);
    }

    function _jumpCurrentLine() {
        const pos = Editor.getCursor?.();
        return Math.max(1, (pos?.line ?? 0) + 1);
    }

    function _updateJumpMeta() {
        const meta = document.getElementById('jumpLineMeta');
        if (!meta) return;
        meta.textContent = `Ln ${_jumpCurrentLine()} / ${_jumpLineCount()}`;
    }

    function _updateJumpPlaceholder() {
        const input = document.getElementById('jumpLineInput');
        if (!input) return;
        input.placeholder = `1 - ${_jumpLineCount()}`;
    }

    function _clearJumpInput({ refocus = true } = {}) {
        const input = document.getElementById('jumpLineInput');
        if (!input) return;
        input.value = '';
        _updateJumpPlaceholder();
        _updateJumpMeta();
        if (refocus) setTimeout(() => input.focus(), 0);
    }

    function _bindJumpModalDrag() {
        if (_jumpDragBound) return;
        const modal = document.getElementById('jumpLineModal');
        const box = modal?.querySelector('.modal');
        const handle = document.getElementById('jumpLineDragHandle') || box?.querySelector('.modal-title-row');
        if (!modal || !box || !handle) return;

        _jumpDragBound = true;

        let dragging = false;
        let startX = 0, startY = 0;
        let startLeft = 0, startTop = 0;

        const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

        const onDown = (e) => {
            if (e.button != null && e.button !== 0) return;
            dragging = true;
            box.dataset.userMoved = '1';
            try { handle.setPointerCapture(e.pointerId); } catch {}

            const rect = box.getBoundingClientRect();
            box.style.position = 'fixed';
            box.style.transform = 'none';
            box.style.left = `${rect.left}px`;
            box.style.top = `${rect.top}px`;
            box.style.bottom = 'auto';

            startX = e.clientX;
            startY = e.clientY;
            startLeft = rect.left;
            startTop = rect.top;
            e.preventDefault();
        };

        const onMove = (e) => {
            if (!dragging) return;
            const rect = box.getBoundingClientRect();
            const maxLeft = Math.max(12, window.innerWidth - rect.width - 6);
            const maxTop = Math.max(12, window.innerHeight - rect.height - 6);
            const nextLeft = clamp(startLeft + (e.clientX - startX), 6, maxLeft);
            const nextTop = clamp(startTop + (e.clientY - startY), 6, maxTop);
            box.style.left = `${nextLeft}px`;
            box.style.top = `${nextTop}px`;
        };

        const onUp = (e) => {
            dragging = false;
            try { handle.releasePointerCapture(e.pointerId); } catch {}
        };

        handle.addEventListener('pointerdown', onDown, { passive: false });
        window.addEventListener('pointermove', onMove, { passive: true });
        window.addEventListener('pointerup', onUp, { passive: true });
    }

    function _ensureJumpPopup() {
        if (_jumpPopup) return _jumpPopup;

        const modal   = document.getElementById('jumpLineModal');
        const input   = document.getElementById('jumpLineInput');
        const btnOk   = document.getElementById('btnJumpLineOk');
        const btnClear = document.getElementById('btnJumpLineClear');
        const btnCancel = document.getElementById('btnJumpLineCancel');
        const btnClose  = document.getElementById('btnJumpLineClose');

        if (!modal || !input || !window.PopupManager) return null;

        const _close = () => _jumpPopup?.close({ reason: 'user' });
        const _jump = () => {
            const n = parseInt(input.value, 10);
            _close();
            if (!isNaN(n)) { NavCursor.jumpToLine(n); _afterMove(); }
        };

        _jumpPopup = window.PopupManager.register('jumpLine', {
            modal,
            useKeyboardSafe: true,
            onAfterOpen() {
                _bindJumpModalDrag();
                _updateJumpMeta();
                _updateJumpPlaceholder();
                input.value = String(_jumpCurrentLine());
                input.inputMode = State?.getLK?.() ? 'none' : 'numeric';
                setTimeout(() => {
                    input.focus();
                    try { input.select(); } catch {}
                }, 80);
            },
            onAfterClose() {
                Editor.focus();
            },
        });

        if (!_jumpPopupBound) {
            _jumpPopupBound = true;
            btnOk.onclick     = _jump;
            btnClear && (btnClear.onclick = () => _clearJumpInput({ refocus: true }));
            btnCancel.onclick = _close;
            btnClose.onclick  = _close;
            input.oninput = () => _updateJumpMeta();
            input.onkeydown   = (e) => {
                if (e.key === 'Enter')  { e.preventDefault(); _jump(); }
                if (e.key === 'Escape') { _close(); }
            };
        }

        return _jumpPopup;
    }

    function goToLine() {
        const popup = _ensureJumpPopup();
        if (!popup) {
            const val = prompt('Go to line:');
            if (val === null) return;
            const n = parseInt(val, 10);
            if (!isNaN(n)) { NavCursor.jumpToLine(n); _afterMove(); }
            return;
        }

        document.activeElement?.blur?.();
        popup.open({ reason: 'command' });
    }
    // ALT+■ 조합 신규 함수
    // 변경 발생 라인 추적 (ALT+HOME/END용)
    const _changedLines = { min: Infinity, max: -1 };
    function trackChange(pos) {
        const view = window.Editor?.get?.();
        if (!view) return;
        const line = view.state.doc.lineAt(pos).number;
        if (line < _changedLines.min) _changedLines.min = line;
        if (line > _changedLines.max) _changedLines.max = line;
    }
    function jumpLastChange() {
        const view = window.Editor?.get?.();
        if (!view || _changedLines.max === -1) { window.NavCursor?.jumpDocEnd?.(); return; }
        const line = view.state.doc.line(Math.min(_changedLines.max, view.state.doc.lines));
        view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
    }

    function trackChange(pos) {
        const view = window.Editor?.get?.();
        if (!view) return;
        const line = view.state.doc.lineAt(pos).number;
        if (line < _changedLines.min) _changedLines.min = line;
        if (line > _changedLines.max) _changedLines.max = line;
    }
    function jumpFirstChange() {
        const view = window.Editor?.get?.();
        if (!view || _changedLines.min === Infinity) { window.NavCursor?.jumpDocStart?.(); return; }
        const line = view.state.doc.line(Math.min(_changedLines.min, view.state.doc.lines));
        view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
    }
    function jumpLastChange() {
        const view = window.Editor?.get?.();
        if (!view || _changedLines.max === -1) { window.NavCursor?.jumpDocEnd?.(); return; }
        const line = view.state.doc.line(Math.min(_changedLines.max, view.state.doc.lines));
        view.dispatch({ selection: { anchor: line.from }, scrollIntoView: true });
    }

    function shiftMoveBlockToStart() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const from = bs.line <= be.line ? bs : be;
        const to   = bs.line <= be.line ? be : bs;
        const startLine = from.line;
        const endLine   = to.ch === 0 && to.line > from.line ? to.line - 1 : to.line;
        if (startLine === 0) return;
        const totalLines = Editor.lineCount();

        const allLines = [];
        for (let i = 0; i < totalLines; i++) allLines.push(Editor.getLine(i));
        const blockLines = allLines.splice(startLine, endLine - startLine + 1);
        allLines.splice(0, 0, ...blockLines);

        const finalText = allLines.join('\n');
        const move = -startLine;
        const newBSLine = bs.line + move;
        const newBELine = be.line + move;
        const tempLines = finalText.split('\n');
        let bsOff = 0, beOff = 0;
        for (let i = 0; i < newBSLine; i++) bsOff += tempLines[i].length + 1;
        bsOff += bs.ch;
        for (let i = 0; i < newBELine; i++) beOff += tempLines[i].length + 1;
        beOff += be.ch;
        view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: finalText }, selection: { anchor: bsOff, head: beOff }, scrollIntoView: true });
        State.setBS({ line: newBSLine, ch: bs.ch });
        State.setBE({ line: newBELine, ch: be.ch });
    }
    function shiftMoveBlockToEnd() {
        const view = window.Editor?.get?.();
        if (!view) return;
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const from = bs.line <= be.line ? bs : be;
        const to   = bs.line <= be.line ? be : bs;
        const startLine = from.line;
        const endLine   = to.ch === 0 && to.line > from.line ? to.line - 1 : to.line;
        const totalLines = Editor.lineCount();
        if (endLine >= totalLines - 1) return;

        const allLines = [];
        for (let i = 0; i < totalLines; i++) allLines.push(Editor.getLine(i));
        const blockLines = allLines.splice(startLine, endLine - startLine + 1);
        allLines.splice(allLines.length, 0, ...blockLines);

        const finalText = allLines.join('\n');
        const move = totalLines - 1 - endLine;
        const newBSLine = bs.line + move;
        const newBELine = be.line + move;
        const tempLines = finalText.split('\n');
        let bsOff = 0, beOff = 0;
        for (let i = 0; i < newBSLine; i++) bsOff += tempLines[i].length + 1;
        bsOff += bs.ch;
        for (let i = 0; i < newBELine; i++) beOff += tempLines[i].length + 1;
        beOff += be.ch;
        view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: finalText }, selection: { anchor: bsOff, head: beOff }, scrollIntoView: true });
        State.setBS({ line: newBSLine, ch: bs.ch });
        State.setBE({ line: newBELine, ch: be.ch });
    }

    function resetAll() {
        State.reset();
        UI.updateStats();
        UI.updateFooter();
        UI.showToast('Reset', 600);
    }

    function _syncAfterUndoRedo() {
        if (!window._uiIsBlockMode?.()) return;
        const view = Editor.get?.();
        if (!view) return;

        // V2 BlockState 활성: CM6 selection → BlockState 재동기화
        if (window.BlockState?.isActive?.()) {
            const ranges = Array.from(view.state.selection.ranges);
            const specs = ranges.map(r => ({ anchor: r.anchor, head: r.head }));
            window.BlockState.dispatch(specs, 0);
            window.BlockState.render();
            return;
        }

        // V1 경로
        const ranges = view.state.selection.ranges;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        for (const r of ranges) {
            const headPos   = Editor.offsetToPos(r.head);
            const anchorPos = Editor.offsetToPos(r.anchor);
            if (colOffsets?.has(headPos.line))     colOffsets.set(headPos.line,     headPos.ch);
            if (colBsOffsets?.has(anchorPos.line)) colBsOffsets.set(anchorPos.line, anchorPos.ch);
        }
        const mainHead   = Editor.offsetToPos(view.state.selection.main.head);
        const mainAnchor = Editor.offsetToPos(view.state.selection.main.anchor);
        const bs = window.State?.getBS?.(), be = window.State?.getBE?.();
        if (bs) window.State?.forceSetBS?.({ line: bs.line, ch: mainAnchor.ch });
        if (be) window.State?.setBE?.({ line: be.line,     ch: mainHead.ch });
        window.NavBlock?.applyColumnSelection?.();
    }
    function undo() {
        if (window._uiIsBlockMode?.()) {
            const { undo: cm6Depth } = Editor.historySize();
            if (cm6Depth > 0) {
                Editor.undo(); _syncAfterUndoRedo(); UI.updateStats(); UI.updateUndoRedo(); return;
            }
            // V2 위치 스냅샷 우선
            if (window.NavBlockV2?.popV2Snapshot?.()) {
                UI.updateStats(); UI.updateUndoRedo(); return;
            }
            // V1 위치 스냅샷
            if (window.NavBlock?.popBlockSnapshot?.()) {
                UI.updateStats(); UI.updateUndoRedo(); return;
            }
        }
        Editor.undo(); _syncAfterUndoRedo(); UI.updateStats(); UI.updateUndoRedo();
    }
    function redo() { Editor.redo(); _syncAfterUndoRedo(); UI.updateStats(); UI.updateUndoRedo(); }
    const find = {
        open:       () => window.NavFind?.openModal(),
        close:      () => window.NavFind?.closeModal(),
        toggle:     () => window.NavFind?.toggleModal(),
        next:       () => window.NavFind?.findNext(),
        prev:       () => window.NavFind?.findPrev(),
        search:     () => window.NavFind?.doSearch(),
        replaceOne: () => window.NavFind?.replaceOne(),
        replaceAll: () => window.NavFind?.replaceAll(),
    };
    const num = {
        trigger:    (btnId) => window.NavNum?.trigger(btnId),
        toggleAxis: () => window.NavNum?.toggleAxis(),
    };

    return {
        moveLeft, moveRight, moveUp, moveDown, pageUp, pageDown,
        selectLeft, selectRight, selectUp, selectDown,
        selectLineStart, selectLineEnd,
        selectDocStart, selectDocEnd,
        modeAMoveLeft, modeAMoveRight, modeAMoveUp, modeAMoveDown,
        modeAH, modeAE, resetModeA,
        jumpH, jumpE, jumpLineStart, swapHE,
        jumpDocStart, jumpDocEnd,
        jumpToLine,
        toggleModeS, toggleModeM, selectAll, selectAllModeA, progressiveSelect,
        moveBlock, moveLineAlt, indent,
        toggleComment, selectCurrentLine,
        selectWordLeft, selectWordRight, selectDocStart, selectDocEnd,
        wordLeft, wordRight, deleteWordBefore, deleteWordAfter, insertLineBelow,
        jumpFirstChange, jumpLastChange, trackChange,
        shiftMoveBlockToStart, shiftMoveBlockToEnd,
        shiftMoveBlock, shiftIndent,
        copyBlock, cutLine, pasteAtCursor,
        backspace, insertSpace, insertNewline, forwardDelete,
        goToLine, resetAll,
        undo, redo,
        find, num,
    };
})();

window.Nav = Nav;
