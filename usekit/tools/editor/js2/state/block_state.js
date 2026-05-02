/* Path: usekit/tools/editor/js2/state/block_state.js
 * CM6 ranges 기반 멀티블럭 상태 — 진실의 소스: CM6 view.state.selection.ranges[]
 * ranges[i] = { anchor=gamma(고정점), head=delta(커서) }
 * ─────────────────────────────────────────────────────────── */

const BlockState = (function () {
    'use strict';

    let _active     = false;
    let _checkMode  = false;
    let _cursorMode = false;  // true=CUR(쉬프트OFF), false=BLK(쉬프트ON)
    let _mLock      = false;
    let _mainIdx    = 0;      // 대표커서 인덱스 (CHECK 하이라이트)
    let _moveDir    = 'down'; // 진행 방향: 'up' | 'down'
    let _baseCh     = 0;      // 멀티 진입 시 기준 컬럼 (anchor 고정점)
    let _baseHdCh   = 0;      // 멀티 세션 최대 넓이 (0번 range head ch) — BLK 좌우이동/진입/reanchor 시 갱신
    let _baseLine   = 0;      // 멀티 진입 시 기준 라인 (투핸들 방향 판단 기준)

    // ── CM6 접근 ─────────────────────────────────────────
    function _v()   { return window.Editor?.get?.(); }
    function _doc() { return _v()?.state.doc ?? null; }

    function _toPos(offset) {
        const doc = _doc();
        if (!doc) return { line: 0, ch: 0 };
        const line = doc.lineAt(offset);
        return { line: line.number - 1, ch: offset - line.from };
    }

    function _toOffset(pos) {
        const doc = _doc();
        if (!doc) return 0;
        const lineNum = Math.min((pos.line ?? 0) + 1, doc.lines);
        const lineObj = doc.line(lineNum);
        return lineObj.from + Math.min(pos.ch ?? 0, lineObj.length);
    }

    function _lineLen(lineNum0) {  // 0-based
        const doc = _doc();
        if (!doc) return 0;
        const n = lineNum0 + 1;
        if (n < 1 || n > doc.lines) return 0;
        return doc.line(n).length;
    }

    function _lineFrom(lineNum0) {
        const doc = _doc();
        if (!doc) return 0;
        const n = lineNum0 + 1;
        if (n < 1 || n > doc.lines) return 0;
        return doc.line(n).from;
    }

    // ── ranges 읽기 ───────────────────────────────────────
    function getRanges() {
        const v = _v();
        if (!v) return [];
        return Array.from(v.state.selection.ranges);
    }

    function getMainIdx() { return _mainIdx; }

    function getPtrRange() {
        const ranges = getRanges();
        return ranges[Math.min(_mainIdx, ranges.length - 1)] ?? null;
    }

    function getPtrLine() {
        const r = getPtrRange();
        if (!r) return null;
        return _toPos(r.head).line;
    }

    // 유효 라인 배열 (ranges에 있는 라인들, 오름차순)
    function getEffectiveLines() {
        const doc = _doc();
        if (!doc) return [];
        const lines = getRanges().map(r => doc.lineAt(r.head).number - 1);
        return [...new Set(lines)].sort((a, b) => a - b);
    }

    // BS = 전체 ranges 중 첫 라인 anchor의 ch
    function getBS() {
        const ranges = getRanges();
        if (!ranges.length) return null;
        const doc = _doc();
        if (!doc) return null;
        let minLine = Infinity, bsCh = 0;
        for (const r of ranges) {
            const line = doc.lineAt(r.anchor).number - 1;
            if (line < minLine) { minLine = line; bsCh = r.anchor - doc.line(line + 1).from; }
        }
        return { line: minLine, ch: bsCh };
    }

    // BE = 전체 ranges 중 마지막 라인 head의 ch
    function getBE() {
        const ranges = getRanges();
        if (!ranges.length) return null;
        const doc = _doc();
        if (!doc) return null;
        let maxLine = -Infinity, beCh = 0;
        for (const r of ranges) {
            const line = doc.lineAt(r.head).number - 1;
            if (line > maxLine) { maxLine = line; beCh = r.head - doc.line(line + 1).from; }
        }
        return { line: maxLine, ch: beCh };
    }

    // ── ranges 쓰기 ───────────────────────────────────────
    function dispatch(specs, mainIdx, scroll = true) {
        const v = _v();
        if (!v || !specs.length) return;
        const { EditorSelection } = CM6;
        const doc = v.state.doc;

        // 같은 라인에 중복 range 제거 (head 기준 라인, 먼저 나온 것 우선)
        const seenLines = new Set();
        const dedupedSpecs = specs.filter(({ head }) => {
            try {
                const lineNum = doc.lineAt(head).number;
                if (seenLines.has(lineNum)) return false;
                seenLines.add(lineNum);
                return true;
            } catch(e) { return true; }
        });
        if (!dedupedSpecs.length) return;

        // 각 range의 head/anchor를 해당 라인 끝으로 클램프
        const clampedSpecs = dedupedSpecs.map(({ anchor, head }) => {
            // head 클램프
            let hLine, hFrom, hLen;
            try {
                const hLineObj = doc.lineAt(head);
                hFrom = hLineObj.from;
                hLen  = hLineObj.length;
            } catch(e) { hFrom = 0; hLen = 0; }
            const clampedHead = Math.max(hFrom, Math.min(head, hFrom + hLen));

            // anchor 클램프
            let aLine, aFrom, aLen;
            try {
                const aLineObj = doc.lineAt(anchor);
                aFrom = aLineObj.from;
                aLen  = aLineObj.length;
            } catch(e) { aFrom = hFrom; aLen = hLen; }
            const clampedAnchor = Math.max(aFrom, Math.min(anchor, aFrom + aLen));

            return { anchor: clampedAnchor, head: clampedHead };
        });

        const selRanges = clampedSpecs.map(({ anchor, head }) =>
            anchor === head
                ? EditorSelection.cursor(head)
                : EditorSelection.range(anchor, head)
        );
        // CM6 selection.main = 항상 0 고정 (입력/IME 안정)
        // _mainIdx = 표시용 포인터 (L[n/n]) — CM6에 넘기지 않고 별도 관리
        const displayMain = Math.max(0, Math.min(mainIdx ?? 0, selRanges.length - 1));
        _mainIdx = displayMain;
        v.dispatch({
            selection: EditorSelection.create(selRanges, 0),
            scrollIntoView: scroll,
        });
    }

    // ── 렌더 (decoration + checkLines + stats) ────────────
    function render() {
        const v = _v();
        if (!v) return;
        const ranges = getRanges();
        if (!ranges.length) return;
        // decoration만 업데이트 — selection은 dispatch()에서 이미 설정됨
        const specs = ranges.map(r => ({ anchor: r.anchor, head: r.head }));
        window.Editor?.updateColumnDecoration?.(specs);
        if (_checkMode) {
            const ptrLine = getPtrLine();
            if (ptrLine != null) window.Editor?.setCheckLines?.([ptrLine + 1]);
        } else {
            window.Editor?.clearCheckLines?.();
        }
        window.UI?.updateStats?.();
    }

    // ── 진입/종료 ─────────────────────────────────────────
    function enterMulti() {
        const v = _v();
        if (!v) return;
        _active     = true;
        _mainIdx    = 0;
        _checkMode  = false;
        _cursorMode = false;
        _mLock      = false;
        // 현재 CM6 커서 위치로 단일 range 초기화
        const head = v.state.selection.main.head;
        const doc  = v.state.doc;
        const lineObj = doc.lineAt(head);
        _baseCh   = head - lineObj.from;
        _baseHdCh = head - lineObj.from;  // 진입 시 넓이=0 (커서점)
        _baseLine = lineObj.number - 1;
        dispatch([{ anchor: head, head }], 0);
        // inputmode 건드리지 않음 — OS 키보드 상태 존중
    }

    // 클릭 시 baseCh/baseLine만 재설정 (inputmode/ranges 변경 없음)
    function reanchor() {
        const v = _v();
        if (!v) return;
        const head = v.state.selection.main.head;
        const doc  = v.state.doc;
        const lineObj = doc.lineAt(head);
        _baseCh   = head - lineObj.from;
        _baseHdCh = head - lineObj.from;  // 클릭 재앵커 시 넓이 리셋
        _baseLine = lineObj.number - 1;
        _mainIdx  = 0;
    }

    function applyInputMode() {
        const v = _v();
        if (!v) return;
        if (_active && !_cursorMode) {
            // BLK 모드: OS 키보드 차단
            v.contentDOM.setAttribute('inputmode', 'none');
        } else {
            v.contentDOM.removeAttribute('inputmode');
        }
    }

    function exitMulti() {
        const v = _v();
        _active     = false;
        _checkMode  = false;
        _cursorMode = false;
        _mLock      = false;
        _mainIdx    = 0;
        _baseCh     = 0;
        _baseHdCh   = 0;
        _baseLine   = 0;
        if (v) {
            const head = v.state.selection.main.head;
            v.dispatch({ selection: { anchor: head } });
            // inputmode 건드리지 않음 — OS 키보드 상태 존중
        }
        window.Editor?.clearCheckLines?.();
        window.Editor?.clearColumnDecoration?.();
    }

    // CHECK ON: 각 라인 오프셋 실제 라인 길이로 클램프
    function enterCheck() {
        _checkMode = true;
        const v = _v();
        if (!v) return;
        const doc = v.state.doc;
        const specs = Array.from(v.state.selection.ranges).map(r => {
            const lineObj = doc.lineAt(r.head);
            return {
                anchor: Math.min(r.anchor, lineObj.to),
                head:   Math.min(r.head,   lineObj.to),
            };
        });
        dispatch(specs, _mainIdx);
    }

    // CHECK OFF: selection 그대로 유지, 플래그만 변경
    function exitCheck() {
        _checkMode = false;
        window.Editor?.clearCheckLines?.();
    }

    // ── 모드 플래그 ───────────────────────────────────────
    function isActive()     { return _active; }
    function isCheckMode()  { return _checkMode; }
    function isCursorMode() { return _cursorMode; }
    function isMLock()      { return _mLock; }

    function setActive(v)     { _active     = !!v; }
    function setCheckMode(v)  { _checkMode  = !!v; }
    function setCursorMode(v) { _cursorMode = !!v; }
    function setMLock(v)      { _mLock      = !!v; }
    function setMainIdx(v)    { _mainIdx    = Math.max(0, v); }

    // ── 유틸 ─────────────────────────────────────────────
    function toPos(offset)  { return _toPos(offset); }
    function lineLen(l)     { return _lineLen(l); }
    function lineFrom(l)    { return _lineFrom(l); }

    return {
        getRanges, getMainIdx, getPtrRange, getPtrLine,
        getMoveDir:  () => _moveDir,  setMoveDir:  (v) => { _moveDir  = v; },
        getBaseCh:   () => _baseCh,   setBaseCh:   (v) => { _baseCh   = v; },
        getBaseHdCh: () => _baseHdCh, setBaseHdCh: (v) => { _baseHdCh = v; },
        getBaseLine: () => _baseLine, setBaseLine: (v) => { _baseLine = v; },
        getEffectiveLines, getBS, getBE,
        dispatch, render,
        enterMulti, exitMulti, reanchor, enterCheck, exitCheck, applyInputMode,
        isActive, isCheckMode, isCursorMode, isMLock,
        setActive, setCheckMode, setCursorMode, setMLock, setMainIdx,
        toPos, lineLen, lineFrom,
    };
})();

window.BlockState = BlockState;
