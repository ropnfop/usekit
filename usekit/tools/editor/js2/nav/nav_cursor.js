/* Path: usekit/tools/editor/js2/nav/nav_cursor.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 커서 이동 (left/right/up/down, H/E, jumpToLine)
 * ─────────────────────────────────────────────────────────── */

const NavCursor = (function () {
    'use strict';

    // Keep editor focused after every move (required for contenteditable)
    function _afterMove() {
        Editor.focus();
        clearSelectAnchorOnMove();
    }
    function moveLeft() {
        _clearTargetCol();
        const pos = Editor.getCursor();
        if (pos.ch > 0) {
            Editor.setCursor({ line: pos.line, ch: pos.ch - 1 });
        } else if (pos.line > 0) {
            const prevLen = (Editor.getLine(pos.line - 1) || '').length;
            Editor.setCursor({ line: pos.line - 1, ch: prevLen });
        }
        _afterMove();
    }

    function moveRight() {
        _clearTargetCol();
        const pos     = Editor.getCursor();
        const lineLen = (Editor.getLine(pos.line) || '').length;
        if (pos.ch < lineLen) {
            Editor.setCursor({ line: pos.line, ch: pos.ch + 1 });
        } else if (pos.line < Editor.lineCount() - 1) {
            Editor.setCursor({ line: pos.line + 1, ch: 0 });
        }
        _afterMove();
    }

    // ── Sticky column (targetCol) ────────────────────────────
    // IDE 표준: 상하 이동 시 원래 컬럼 기억, 짧은 줄을 지나도 복원
    let _targetCol = null;

    function _clearTargetCol()       { _targetCol = null; }
    function _setTargetColIfNull(ch) { if (_targetCol === null) _targetCol = ch; }

    function moveUp(n = 1) {
        const pos = Editor.getCursor();
        _setTargetColIfNull(pos.ch);
        const targetLine = Math.max(0, pos.line - n);
        const lineLen    = (Editor.getLine(targetLine) || '').length;
        Editor.setCursor({ line: targetLine, ch: Math.min(_targetCol, lineLen) });
        _afterMove();
    }

    function moveDown(n = 1) {
        const pos = Editor.getCursor();
        _setTargetColIfNull(pos.ch);
        const targetLine = Math.min(Editor.lineCount() - 1, pos.line + n);
        const lineLen    = (Editor.getLine(targetLine) || '').length;
        Editor.setCursor({ line: targetLine, ch: Math.min(_targetCol, lineLen) });
        _afterMove();
    }
    function jumpLineStart() {
        const pos = Editor.getCursor();
        Editor.setCursor({ line: pos.line, ch: 0 });
        _afterMove();
    }

    function jumpH() {
        _clearTargetCol();
        if (!window._uiIsBlockMode?.()) window._uiClearColOffsets?.();
        const pos  = Editor.getCursor();
        const text = Editor.getLine(pos.line) || '';
        // 빈라인 단일커서: 이동 불필요, 가드만 활성
        if (text.length === 0) { window.UIViewport?.triggerScrollGuard?.(); return; }
        const firstNonSpace = text.search(/\S/);
        const target = (firstNonSpace >= 0 && pos.ch !== firstNonSpace)
            ? firstNonSpace : 0;
        Editor.setCursor({ line: pos.line, ch: target });
        // 라인번호 gutter에 커서가 가려지지 않도록 가로 스크롤 리셋
        requestAnimationFrame(() => {
            const sc = Editor.get?.()?.scrollDOM;
            if (sc) sc.scrollLeft = 0;
        });
        _afterMove();
    }

    function jumpE() {
        _clearTargetCol();
        if (!window._uiIsBlockMode?.()) window._uiClearColOffsets?.();
        const pos  = Editor.getCursor();
        const text = Editor.getLine(pos.line) || '';
        const len  = text.length;
        // 빈라인: 가드만 활성
        if (len === 0) { window.UIViewport?.triggerScrollGuard?.(); return; }
        // softEnd: 후행 공백/탭 앞
        let softEnd = len;
        while (softEnd > 0 && (text[softEnd - 1] === ' ' || text[softEnd - 1] === '\t')) softEnd--;
        // 토글: softEnd 위치면 라인끝, 아니면 softEnd
        const target = (pos.ch !== softEnd) ? softEnd : len;
        Editor.setCursor({ line: pos.line, ch: target });
        _afterMove();
    }

    function jumpDocStart() {
        _clearTargetCol();
        Editor.setCursor({ line: 0, ch: 0 });
        Editor.scrollTo(0);
        _afterMove();
    }

    function jumpDocEnd() {
        _clearTargetCol();
        const last = Editor.lineCount() - 1;
        const len  = (Editor.getLine(last) || '').length;
        Editor.setCursor({ line: last, ch: len });
        _afterMove();
    }

    // 문단 단위 이동 — 빈 줄(엔터만 있는 줄) 경계로 점프
    function jumpParagraphPrev() {
        _clearTargetCol();
        const pos = Editor.getCursor();
        let line = pos.line;
        // 현재 줄이 빈 줄이면 한 칸 더 올라가서 탐색
        if (line > 0 && (Editor.getLine(line) || '').trim() === '') line--;
        // 위로 올라가며 빈 줄 찾기
        while (line > 0 && (Editor.getLine(line) || '').trim() !== '') line--;
        Editor.setCursor({ line, ch: 0 });
        _afterMove();
    }

    function jumpParagraphNext() {
        _clearTargetCol();
        const pos   = Editor.getCursor();
        const total = Editor.lineCount();
        let line = pos.line;
        // 현재 줄이 빈 줄이면 한 칸 더 내려가서 탐색
        if (line < total - 1 && (Editor.getLine(line) || '').trim() === '') line++;
        // 아래로 내려가며 빈 줄 찾기
        while (line < total - 1 && (Editor.getLine(line) || '').trim() !== '') line++;
        Editor.setCursor({ line, ch: 0 });
        _afterMove();
    }

    function jumpToLine(lineNum) {
        _clearTargetCol();
        const line = Math.max(0, Math.min(lineNum - 1, Editor.lineCount() - 1));
        Editor.setCursor({ line, ch: 0 });
        requestAnimationFrame(() => {
            window.UIViewport?.ensureCursorVisible?.();
        });
        _afterMove();
    }

    // 클릭으로 커서가 바뀌면 targetCol 리셋
    function init() {
        Editor.on('mousedown', _clearTargetCol);
        // 직접 입력(CM6 cursorActivity) 시에도 리셋
        // — 단, moveUp/moveDown 내에서 발생하는 cursorActivity는 리셋하면 안 되므로
        //   mousedown만으로 충분 (입력은 좌우 이동과 동일하게 처리됨)
    }

    // ── Shift+방향키 선택 확장 ──────────────────────────────
    // BS = anchor(고정점), BE = head(커서) — S모드와 동일한 State.BS/BE 사용

    // 처음 select 시작 시 BS 세팅, 이후엔 유지
    function _ensureBS() {
        if (!State.getBS()) {
            const cur = Editor.getCursor();
            State.setBS(cur);
            State.setBE(cur);
        }
    }

    // Shift 해제 시: 블럭은 유지, BS 고정점만 해제 (커서이동 허용)
    function clearSelectAnchorOnMove() {
        if (!State.getModeS?.()) {
            const bm = window._uiIsBlockMode?.();
            if (bm) return;
            State.clearBlock();
            Editor.clearSelection();
        }
    }

    function clearSelectAnchor() {
        // 블럭/selection은 건드리지 않음 — Shift 놓은 후에도 블럭 유지
    }

    // 일반 커서 이동 시: S모드 아니면 블럭+selection 완전 해제

    function selectLeft() {
        _clearTargetCol();
        _ensureBS();
        const head = Editor.getCursor();
        const newHead = (head.ch > 0)
            ? { line: head.line, ch: head.ch - 1 }
            : head.line > 0
                ? { line: head.line - 1, ch: (Editor.getLine(head.line - 1) || '').length }
                : head;
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectRight() {
        _clearTargetCol();
        _ensureBS();
        const head = Editor.getCursor();
        const lineLen = (Editor.getLine(head.line) || '').length;
        const newHead = (head.ch < lineLen)
            ? { line: head.line, ch: head.ch + 1 }
            : head.line < Editor.lineCount() - 1
                ? { line: head.line + 1, ch: 0 }
                : head;
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectUp() {
        _ensureBS();
        const head = Editor.getCursor();
        _setTargetColIfNull(head.ch);
        const targetLine = Math.max(0, head.line - 1);
        const lineLen = (Editor.getLine(targetLine) || '').length;
        const newHead = { line: targetLine, ch: Math.min(_targetCol, lineLen) };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectDown() {
        _ensureBS();
        const head = Editor.getCursor();
        _setTargetColIfNull(head.ch);
        const targetLine = Math.min(Editor.lineCount() - 1, head.line + 1);
        const lineLen = (Editor.getLine(targetLine) || '').length;
        const newHead = { line: targetLine, ch: Math.min(_targetCol, lineLen) };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectLineUp() {
        _ensureBS();
        const head = Editor.getCursor();
        const targetLine = Math.max(0, head.line - 1);
        const lineText = Editor.getLine(targetLine) || '';
        const newHead = { line: targetLine, ch: lineText.length };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectLineDown() {
        _ensureBS();
        const head = Editor.getCursor();
        const targetLine = Math.min(Editor.lineCount() - 1, head.line + 1);
        const lineText = Editor.getLine(targetLine) || '';
        const newHead = { line: targetLine, ch: lineText.length };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectLineStart() {
        _ensureBS();
        const head = Editor.getCursor();
        const text = Editor.getLine(head.line) || '';
        const firstNonSpace = text.search(/\S/);
        const newHead = { line: head.line, ch: (firstNonSpace >= 0 && head.ch !== firstNonSpace) ? firstNonSpace : 0 };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectLineEnd() {
        _ensureBS();
        const head = Editor.getCursor();
        const newHead = { line: head.line, ch: (Editor.getLine(head.line) || '').length };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectDocStart() {
        _ensureBS();
        const newHead = { line: 0, ch: 0 };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }
    function selectDocEnd() {
        _ensureBS();
        const lastLine = Editor.lineCount() - 1;
        const newHead = { line: lastLine, ch: (Editor.getLine(lastLine) || '').length };
        State.setBE(newHead);
        Editor.setSelectionDirected(State.getBS(), newHead);
    }

    return {
        init,
        moveLeft, moveRight, moveUp, moveDown,
        selectLeft, selectRight, selectUp, selectDown, selectLineUp, selectLineDown,
        selectLineStart, selectLineEnd,
        selectDocStart, selectDocEnd,
        jumpH, jumpE, jumpLineStart,
        jumpDocStart, jumpDocEnd,
        jumpParagraphPrev, jumpParagraphNext,
        jumpToLine,
        clearSelectAnchor,
    };
})();

window.NavCursor = NavCursor;
