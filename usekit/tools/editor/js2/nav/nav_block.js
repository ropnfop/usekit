/* Path: usekit/tools/editor/js2/nav/nav_block.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * BLK/CUR/CHECK 멀티블럭 편집, 블록 선택·이동·인덴트 조작
 * activeEnd: 'H'=커서가 BS쪽, 'E'=커서가 BE쪽, null=미정
 * _checkPointer: CHECK 모드 대표커서, _checkTemp*: 임시 preview 라인
 * ─────────────────────────────────────────────────────────── */

const NavBlock = (function () {
    'use strict';

    function _earlier(a, b) {
        if (a.line < b.line) return a;
        if (a.line > b.line) return b;
        return a.ch <= b.ch ? a : b;
    }
    function _later(a, b) { return _earlier(a, b) === a ? b : a; }
    function _posEqual(a, b) { return a && b && a.line === b.line && a.ch === b.ch; }


    function _applyInputModePolicy() {
        // view.contentDOM이 곧 .cm-content — 직접 사용
        const cm = Editor.get?.()?.contentDOM;
        if (!cm) return;

        if (State.getModeS?.() && State.getModeS()) {
            cm.setAttribute('inputmode', 'none');
            return;
        }
        if (State.getLK?.() && State.getLK()) {
            cm.setAttribute('inputmode', 'none');
        } else {
            cm.removeAttribute('inputmode');
        }
    }

    function toggleModeS() {
        State.toggleModeS();
        if (State.getModeS()) {
            const cur = Editor.getCursor();
            State.setBS(cur);
            State.setBE(cur);
            State.setActiveEnd(null);
        } else {
            State.setActiveEnd(null);
            Editor.clearSelection();
        }
        _applyInputModePolicy();
        UI?.updateStats?.();
    }

    let _swapping = false;
    let _columnEditing = false;
    let _columnEditingTimer = null;

    let _mlockApplying = false;
    let _checkPointer = null;  // CHECK 모드 대표커서 { line, ch }
    let _checkTempBE = null;   // SHIFT OFF에서 만든 임시 BE line
    let _checkTempBS = null;   // SHIFT OFF에서 만든 임시 BS line
    let _checkTempIncluded = false; // 임시 BE/BS가 실제 구조에 반영되었는지 여부
    let _checkAnchorTemplate = null; // CHECK 진입 시 최초 BS 라인의 anchor/head 템플릿

    // 멀티모드 위치 히스토리 스택 (HOME/END/방향키 이동 전 상태 저장)
    const _blockSnapshots = [];
    const _BLOCK_SNAP_MAX = 20;

    function _pushBlockSnapshot() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const snap = {
            bs: { ...bs }, be: { ...be },
            colOffsets:   colOffsets   ? new Map(colOffsets)   : new Map(),
            colBsOffsets: colBsOffsets ? new Map(colBsOffsets) : new Map(),
        };
        _blockSnapshots.push(snap);
        if (_blockSnapshots.length > _BLOCK_SNAP_MAX) _blockSnapshots.shift();
        UI?.updateUndoRedo?.(); // 풋터 버튼 활성화 갱신
    }

    function _popBlockSnapshot() {
        const snap = _blockSnapshots.pop();
        if (!snap) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        // BS/BE 복원 (CHECK ON 중이어도 forceSetBS 사용)
        State.forceSetBS(snap.bs);
        State.setBE(snap.be);
        // colOffsets 복원
        if (colOffsets)   { colOffsets.clear();   snap.colOffsets.forEach((v,k)   => colOffsets.set(k,v)); }
        if (colBsOffsets) { colBsOffsets.clear(); snap.colBsOffsets.forEach((v,k) => colBsOffsets.set(k,v)); }
        _applyColumnSelection();
        UI?.updateUndoRedo?.(); // 풋터 버튼 활성화 갱신
        return true;
    }

    function _clearBlockSnapshots() {
        _blockSnapshots.length = 0;
        UI?.updateUndoRedo?.();
    }
    function afterMove() {
        if (_swapping) return;
        if (_columnEditing) return; // 컬럼 편집 중이면 무시
        if (window.BlockState?.isActive?.()) return; // V2 활성 시 완전 스킵
        if (!State.getModeS()) {
            // Shift 음영 선택 중(_qnShift ON)이면 BS 앵커 유지 — 덮어쓰면 안됨
            if (window._uiIsShiftMode?.()) return;
            // S모드/Shift 없으면 BS/BE 세팅 불필요
            State.clearBlock();
            return;
        }
        // M-LOCK ON: 현재 커서 위치를 BE로 갱신 후 재적용
        if (window._uiIsMLock?.()) {
            if (_mlockApplying) return;
            _mlockApplying = true;
            const view = Editor.get?.();
            if (view) {
                const head = view.state.selection.main.head;
                const cur = Editor.offsetToPos(head);
                State.setBE(cur);
                _applyColumnSelection();
            }
            UI?.updateStats?.();
            _mlockApplying = false;
            return;
        }

        const cur = Editor.getCursor();

        // BE = 항상 커서. BS는 절대 건드리지 않음.
        State.setBE(cur);

        const bs = State.getBS();
        const be = State.getBE();

        if (!bs || !be || _posEqual(bs, be)) {
            Editor.clearSelection();
            UI?.updateStats?.();
            return;
        }

        // anchor=BS(고정), head=BE(커서)
        Editor.setSelectionDirected(bs, be);
        UI?.updateStats?.();
    }

    function trySwapByKey(targetEnd) {
        if (!State.getModeS()) return false;
        const bs = State.getBS();
        const be = State.getBE();
        if (!bs || !be || _posEqual(bs, be)) return false;

        // H 클릭: E점등 상태(BE>BS)에서만 실행
        // E 클릭: H점등 상태(BE<BS)에서만 실행
        const beAfterBs = (be.line > bs.line) || (be.line === bs.line && be.ch > bs.ch);
        if (targetEnd === 'H' && !beAfterBs) return false;  // 이미 H상태
        if (targetEnd === 'E' && beAfterBs)  return false;  // 이미 E상태

        // 새 BS = 구 BE, 새 BE = 구 BS
        // 커서를 새 BE(=구 BS) 위치로 이동
        const newBS = { ...be };
        const newBE = { ...bs };
        State.setBS(newBS);
        State.setBE(newBE);

        _swapping = true;
        Editor.setCursor(newBE);
        Editor.setSelectionDirected(newBS, newBE);
        setTimeout(() => { _swapping = false; }, 150);

        UI?.updateStats?.();
        return true;
    }

    function swapHE() {
        const bs = State.getBS();
        const be = State.getBE();
        if (!bs || !be || _posEqual(bs, be)) return;
        const beAfterBs = (be.line > bs.line) || (be.line === bs.line && be.ch > bs.ch);
        trySwapByKey(beAfterBs ? 'H' : 'E');
    }

    function moveBlockBy(n) {
        if (n === 0) return;
        if (!State.hasBlock()) { _moveCursorLineBy(n); return; }
        _swapping = true;
        const bs = State.getBS(), be = State.getBE();
        const from = _earlier(bs, be);
        const to   = _later(bs, be);
        const startLine  = from.line;
        const endLine    = to.ch === 0 && to.line > from.line ? to.line - 1 : to.line;
        const totalLines = Editor.lineCount();
        const blockSize  = endLine - startLine + 1;

        // 이동 가능 범위 클램프
        let move = n;
        if (move < 0) move = Math.max(move, -startLine);
        else          move = Math.min(move, totalLines - 1 - endLine);
        if (move === 0) { _swapping = false; return; }

        // 블록 라인 수집
        const blockLines = [];
        for (let i = startLine; i <= endLine; i++) blockLines.push(Editor.getLine(i));

        if (move < 0) {
            // 위로: swap 대상 라인들 수집
            const swapLines = [];
            for (let i = startLine + move; i < startLine; i++) swapLines.push(Editor.getLine(i));
            const swapCount = swapLines.length;
            // 블록 위치에 swap 라인 쓰기 (아래서 위로 덮어쓰기)
            for (let i = 0; i < swapCount; i++) {
                Editor.replaceRange(
                    swapLines[i] + '\n',
                    { line: endLine - swapCount + 1 + i, ch: 0 },
                    { line: endLine - swapCount + 1 + i + 1, ch: 0 }
                );
            }
            // 블록 라인을 새 위치에 쓰기
            for (let i = 0; i < blockLines.length; i++) {
                Editor.replaceRange(
                    blockLines[i] + '\n',
                    { line: startLine + move + i, ch: 0 },
                    { line: startLine + move + i + 1, ch: 0 }
                );
            }
        } else {
            // 아래로: swap 대상 라인들 수집
            const swapLines = [];
            for (let i = endLine + 1; i <= endLine + move; i++) swapLines.push(Editor.getLine(i));
            const swapCount = swapLines.length;
            // swap 라인을 블록 위로 올리기
            for (let i = 0; i < swapCount; i++) {
                Editor.replaceRange(
                    swapLines[i] + '\n',
                    { line: startLine + i, ch: 0 },
                    { line: startLine + i + 1, ch: 0 }
                );
            }
            // 블록 라인을 새 위치에 쓰기
            for (let i = 0; i < blockLines.length; i++) {
                Editor.replaceRange(
                    blockLines[i] + '\n',
                    { line: startLine + swapCount + i, ch: 0 },
                    { line: startLine + swapCount + i + 1, ch: 0 }
                );
            }
        }

        // BS/BE를 원본 방향 유지하면서 라인만 이동
        const newBS = { line: bs.line + move, ch: bs.ch };
        const newBE = { line: be.line + move, ch: be.ch };
        State.setBS(newBS); State.setBE(newBE);
        Editor.setSelectionDirected(newBS, newBE);
        _swapping = false;
    }

    // M-LOCK BLK: 음영 전체를 상하좌우로 이동 (텍스트 변경 없음)
    function shiftBlock(dir) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const totalLines = Editor.lineCount();
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();

        if (dir === 'up' || dir === 'down') {
            const d = dir === 'down' ? 1 : -1;
            const newBsLine = bs.line + d;
            const newBeLine = be.line + d;
            if (newBsLine < 0 || newBeLine < 0) return;
            if (newBsLine >= totalLines || newBeLine >= totalLines) return;
            // colOffsets 라인 키 전체 이동
            if (colOffsets?.size) {
                const entries = [...colOffsets.entries()];
                colOffsets.clear();
                for (const [l, v] of entries) colOffsets.set(l + d, v);
            }
            if (colBsOffsets?.size) {
                const entries = [...colBsOffsets.entries()];
                colBsOffsets.clear();
                for (const [l, v] of entries) colBsOffsets.set(l + d, v);
            }
            const checkedHeads = window._uiGetCheckedHeads?.();
            if (checkedHeads?.size) {
                const arr = [...checkedHeads];
                checkedHeads.clear();
                for (const l of arr) checkedHeads.add(l + d);
            }
            State.forceSetBS({ line: newBsLine, ch: bs.ch });
            State.setBE({ line: newBeLine, ch: be.ch });
        } else {
            // 좌우: colOffsets delta ±1, colBsOffsets gamma ±1, BS/BE ch ±1
            const d = dir === 'right' ? 1 : -1;
            if (colOffsets?.size) {
                for (const [l, v] of colOffsets) colOffsets.set(l, Math.max(0, v + d));
            }
            if (colBsOffsets?.size) {
                for (const [l, v] of colBsOffsets) colBsOffsets.set(l, Math.max(0, v + d));
            }
            State.forceSetBS({ line: bs.line, ch: Math.max(0, bs.ch + d) });
            State.setBE({ line: be.line, ch: Math.max(0, be.ch + d) });
        }
        _applyColumnSelection();
    }

    function _isBlankLine(line) {
        return /^[ \t\u00a0]*$/.test(line ?? '');
    }

    function _moveCursorLineBy(n) {
        const pos        = Editor.getCursor();
        const totalLines = Editor.lineCount();
        const target     = Math.max(0, Math.min(pos.line + n, totalLines - 1));
        if (target === pos.line) return;
        const srcLine = Editor.getLine(pos.line);
        const tgtLine = Editor.getLine(target);
        if (n < 0) {
            Editor.replaceRange(srcLine + '\n', { line: target,   ch: 0 }, { line: target + 1,   ch: 0 });
            Editor.replaceRange(tgtLine + '\n', { line: pos.line, ch: 0 }, { line: pos.line + 1, ch: 0 });
        } else {
            Editor.replaceRange(tgtLine + '\n', { line: pos.line, ch: 0 }, { line: pos.line + 1, ch: 0 });
            Editor.replaceRange(srcLine + '\n', { line: target,   ch: 0 }, { line: target + 1,   ch: 0 });
        }
        Editor.setCursor({ line: target, ch: pos.ch });
    }

    // Alt+↑↓ 전용: 커서가 공백라인이고 인접도 공백이면 삭제, 아니면 스왑
    function moveLineAlt(n) {
        const pos        = Editor.getCursor();
        const totalLines = Editor.lineCount();
        const target     = Math.max(0, Math.min(pos.line + n, totalLines - 1));
        if (target === pos.line) return;
        const srcLine = Editor.getLine(pos.line);
        const tgtLine = Editor.getLine(target);
        if (_isBlankLine(srcLine) && _isBlankLine(tgtLine)) {
            // 둘 다 공백 → 인접 공백 라인 삭제
            const isLast = target >= totalLines - 1;
            if (isLast) {
                Editor.replaceRange('', { line: target, ch: 0 }, { line: target, ch: tgtLine.length });
            } else {
                Editor.replaceRange('', { line: target, ch: 0 }, { line: target + 1, ch: 0 });
            }
            Editor.setCursor({ line: n < 0 ? pos.line - 1 : pos.line, ch: pos.ch });
        } else {
            // 스왑
            if (n < 0) {
                Editor.replaceRange(srcLine + '\n', { line: target,   ch: 0 }, { line: target + 1,   ch: 0 });
                Editor.replaceRange(tgtLine + '\n', { line: pos.line, ch: 0 }, { line: pos.line + 1, ch: 0 });
            } else {
                Editor.replaceRange(tgtLine + '\n', { line: pos.line, ch: 0 }, { line: pos.line + 1, ch: 0 });
                Editor.replaceRange(srcLine + '\n', { line: target,   ch: 0 }, { line: target + 1,   ch: 0 });
            }
            Editor.setCursor({ line: target, ch: pos.ch });
        }
    }

    function indent(spaces) {
        const bs = State.getBS(), be = State.getBE();
        const startLine = bs ? _earlier(bs, be ?? bs).line : Editor.getCursor().line;
        const endLine   = be ? _later(bs, be).line         : startLine;
        const pad   = spaces > 0 ? ' '.repeat(spaces) : null;
        const dedent = spaces < 0 ? Math.abs(spaces) : 0;
        const TAB_W = 4;
        for (let i = startLine; i <= endLine; i++) {
            const line = Editor.getLine(i) || '';
            if (spaces > 0) {
                Editor.replaceRange(pad, { line: i, ch: 0 }, { line: i, ch: 0 });
            } else {
                // 탭은 TAB_W 스페이스로 시각 정규화 후 dedent
                let normLen = 0, normCols = 0;
                while (normCols < dedent && normLen < line.length) {
                    if (line[normLen] === '\t') {
                        normCols += TAB_W - (normCols % TAB_W);
                    } else if (/[ \u00a0]/.test(line[normLen])) {
                        normCols++;
                    } else {
                        break;
                    }
                    normLen++;
                }
                if (normLen > 0) {
                    const keep = normCols > dedent ? ' '.repeat(normCols - dedent) : '';
                    Editor.replaceRange(keep, { line: i, ch: 0 }, { line: i, ch: normLen });
                }
            }
        }
    }

    let _clipData = '';  // 내부 클립보드

    function _blockRange() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be || _posEqual(bs, be)) return null;
        const from = _earlier(bs, be);
        const to   = _later(bs, be);
        return { from, to };
    }

    const _CLIP_MAX = 512 * 1024; // 512KB — Samsung Browser 실질 한계
    function _clipWrite(text) {
        if (text.length > _CLIP_MAX) {
            // 용량 초과: 내부 클립보드만 사용, 토스트 안내
            window.UI?.showToast?.('Copied to internal clipboard (size limit)', 1800);
            return;
        }
        // execCommand 우선 (Samsung Browser user-gesture 호환)
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
            document.body.appendChild(ta);
            ta.focus();
            ta.setSelectionRange(0, ta.value.length);
            const ok = document.execCommand('copy');
            ta.remove();
            if (ok) return;
        } catch (e) { /* fall through */ }
        // Clipboard API fallback
        navigator.clipboard?.writeText?.(text).catch(e => {
            console.warn('[COPY] clipboard fail', e);
            window.UI?.showToast?.('System clipboard failed (internal saved)', 1800);
        });
    }

    function copyBlock() {
        const range = _blockRange();
        let text;
        if (range) {
            text = Editor.getRange(range.from, range.to);
        } else {
            const pos = Editor.getCursor();
            text = Editor.getLine(pos.line) || '';
        }
        _clipData = text;
        _clipWrite(text);
        return text;
    }

    function cutLine() {
        const range = _blockRange();
        if (range) {
            // 블록 영역 복사 후 삭제
            const text = Editor.getRange(range.from, range.to);
            _clipData = text;
            _clipWrite(text);
            Editor.replaceRange('', range.from, range.to);
            State.clearBlock();
            Editor.clearSelection();
        } else {
            // 블록 없으면 현재 줄 자르기
            const pos        = Editor.getCursor();
            const totalLines = Editor.lineCount();
            const from = { line: pos.line, ch: 0 };
            const to   = pos.line < totalLines - 1
                ? { line: pos.line + 1, ch: 0 }
                : { line: pos.line, ch: (Editor.getLine(pos.line) || '').length };
            const lineText = Editor.getLine(pos.line) || '';
            const text = pos.line < totalLines - 1 ? lineText + '\n' : lineText;
            _clipData = text;
            _clipWrite(text);
            Editor.replaceRange('', from, to);
        }
    }

    function getClipData() { return _clipData; }
    function setClipData(v) { _clipData = v; }

    // ── 컬럼 블럭 (사각형 선택) ──────────────────────────────
    // dispatch 후 CM6 실제 커서 위치로 colOffsets/colBsOffsets 재확정
    // direction: 'insert'(delta+gamma 동일 이동) | 'delete_before' | 'delete_after' | 'selection'(delta=gamma=fromCh)
    // BS/BE 싱크 검증 — 불일치 시 CM6 실제 커서 기준으로 재확정

    // 전체 effectiveLines 오프셋을 CM6 실제 커서 위치로 수렴 (delta=gamma=실제ch)
    function forceConvergeOffsets() {
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return;
        const effectiveLines = _getEffectiveLines();
        const bs = State.getBS();
        const bsCh = bs?.ch ?? 0;
        const view = Editor.get?.();
        const doc = view?.state.doc;
        for (const l of effectiveLines) {
            // 라인 길이로 클램프 — 
 보호
            let ch = bsCh;
            if (doc) {
                const lineNum = l + 1;
                if (lineNum <= doc.lines) {
                    ch = Math.min(bsCh, doc.line(lineNum).length);
                }
            }
            colOffsets.set(l, ch);
            colBsOffsets.set(l, ch);
        }
    }

    // 유효 라인 배열 반환 — BS~BE 중 _checkedHeads 제외
    function _getEffectiveLines() {
        validateAndSyncBsBe();
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return [];
        const fromLine = Math.min(bs.line, be.line);
        const toLine   = Math.max(bs.line, be.line);
        const excluded = window._uiGetCheckedHeads?.() || new Set();
        const lines = [];
        for (let l = fromLine; l <= toLine; l++) {
            if (!excluded.has(l)) lines.push(l);
        }
        return lines;
    }

    function _applyColumnSelection() {
        if (window.BlockState?.isActive?.()) return; // V2 활성 시 스킵
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const fromCh    = Math.min(bs.ch, be.ch);
        const toCh      = Math.max(bs.ch, be.ch);
        const view      = Editor.get?.();
        if (!view) return;
        const doc       = view.state.doc;
        const beIsLeft  = be.ch < bs.ch;
        const beIsAbove = be.line < bs.line;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;

        // 포인터 기준 mainIdx 계산
        const ptrLine = _checkPointer?.line ?? (beIsAbove ? be.line : bs.line);
        let mainIdx = 0, bestDist = Infinity;
        for (let i = 0; i < effectiveLines.length; i++) {
            const dist = Math.abs(effectiveLines[i] - ptrLine);
            if (dist < bestDist) { bestDist = dist; mainIdx = i; }
        }

        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();

        const offsets = [];
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const chFrom  = lineObj.from + Math.min(fromCh, lineObj.length);
            const chTo    = lineObj.from + Math.min(toCh,   lineObj.length);
            let anchor, head;
            // CHECK OFF rectangular block: all effective lines must share the same
            // anchor/head direction. When vertical direction flips (BE moves above BS),
            // the active end should change, but the anchor line must not become the
            // only line with inverted head/anchor, otherwise the bottom line behaves
            // differently from the rest during subsequent up/down moves.
            anchor = beIsLeft ? chTo   : chFrom;
            head   = beIsLeft ? chFrom : chTo;
            if (colOffsets?.has(l) || colBsOffsets?.has(l)) {
                const baseCh = Math.min(bs.ch, be.ch);
                const delta = colOffsets?.has(l)   ? colOffsets.get(l)   : baseCh;
                const gamma = colBsOffsets?.has(l) ? colBsOffsets.get(l) : baseCh;
                const dPos = lineObj.from + Math.min(delta, lineObj.length);
                const gPos = lineObj.from + Math.min(gamma, lineObj.length);
                anchor = gPos;
                head   = dPos;
            }
            offsets.push({ anchor, head });
        }
        if (!offsets.length) return;

        // 항상 setColumnSelectionFull (mainIdx 포함) 사용
        Editor.setColumnSelectionFull?.(offsets, mainIdx);
        UI?.updateStats?.();
    }

    // 블럭모드 CHECK ON: 각 라인 독립 커서 dispatch (colOffsets 반영)
    function _applyCheckOffsetSelection() {
        if (window.BlockState?.isActive?.()) return; // V2 활성 시 스킵
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const baseCh = Math.min(bs.ch, be.ch);

        const ptrLine = _checkPointer?.line ?? be.line;
        const hasTempPreviewOnly = (!_checkTempIncluded) && ((_checkTempBS != null) || (_checkTempBE != null));
        const renderLines = effectiveLines.slice();

        // CUR모드(쉬프트 오프): ptrLine → mainIdx → 해당 라인이 대표커서 → 해당 라인만 입력
        // BLK모드(쉬프트 온):  mainIdx=0 → top 라인 대표커서 → 전체 동시 입력
        const isCurMode = !!window._uiIsCheckCurMode;
        let mainIdx = 0, bestDist = Infinity;
        const offsets = renderLines.map((l, i) => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return null;
            const lineObj = doc.line(lineNum);
            const baseCh2 = Math.min(bs.ch, be.ch);
            const delta = colOffsets?.has(l)   ? colOffsets.get(l)   : baseCh2;
            const gamma = colBsOffsets?.has(l) ? colBsOffsets.get(l) : baseCh2;
            const dPos = lineObj.from + Math.min(delta, lineObj.length);
            const gPos = lineObj.from + Math.min(gamma, lineObj.length);
            if (isCurMode) {
                const dist = Math.abs(l - ptrLine);
                if (dist < bestDist) { bestDist = dist; mainIdx = i; }
            }
            return { anchor: gPos, head: dPos };
        }).filter(Boolean);

        if (!offsets.length) return;
        Editor.setColumnSelectionFull?.(offsets, mainIdx);
        // 포인터 라인 하이라이트
        Editor.setCheckLines?.([ptrLine + 1]);
        UI?.updateStats?.();
        clearTimeout(_columnEditingTimer); _columnEditingTimer = setTimeout(() => { _columnEditing = false; }, 50);
    }

    function isCheckHeadDirection(mode) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const lo = Math.min(a, b);
            const hi = Math.max(a, b);
            const head = b;
            if (mode === 'home') {
                if (head !== lo) return false;
            } else {
                if (head !== hi) return false;
            }
        }
        return true;
    }

    function areCheckHeadsAtSoftHome() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return false;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softHomeCh(lineText);
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const head = b;
            if (head !== softCh) return false;
        }
        return true;
    }

    function syncCheckHeadsToSoftHome() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;

        const ptrLine = _checkPointer?.line ?? Math.min(bs.line, be.line);
        let ptrHeadCh = null;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softHomeCh(lineText);
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const other = Math.max(a, b);
            const head = Math.min(softCh, other);
            const anchor = Math.max(softCh, other);
            colOffsets.set(l, head);
            colBsOffsets.set(l, anchor);
            if (l === ptrLine) ptrHeadCh = head;
        }
        if (_checkPointer) {
            _checkPointer = { line: ptrLine, ch: ptrHeadCh ?? _checkPointer.ch ?? bs.ch };
        }
        UI?.updateStats?.();
        return true;
    }

    function syncCheckHeadsToColumnZero() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;

        const ptrLine = _checkPointer?.line ?? Math.min(bs.line, be.line);
        let ptrHeadCh = null;
        for (const l of effectiveLines) {
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const other = Math.max(a, b);
            const head = 0;
            const anchor = Math.max(other, 0);
            colOffsets.set(l, head);
            colBsOffsets.set(l, anchor);
            if (l === ptrLine) ptrHeadCh = head;
        }
        if (_checkPointer) {
            _checkPointer = { line: ptrLine, ch: ptrHeadCh ?? 0 };
        }
        UI?.updateStats?.();
        return true;
    }

    function areCheckHeadsAtSoftEnd() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return false;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softEndCh(lineText);
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const head = b;
            if (head !== softCh) return false;
        }
        return true;
    }

    function syncCheckHeadsToSoftEnd() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;

        const ptrLine = _checkPointer?.line ?? Math.max(bs.line, be.line);
        let ptrHeadCh = null;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softEndCh(lineText);
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const other = Math.min(a, b);
            const head = Math.max(softCh, other);
            const anchor = Math.min(softCh, other);
            colOffsets.set(l, head);
            colBsOffsets.set(l, anchor);
            if (l === ptrLine) ptrHeadCh = head;
        }
        if (_checkPointer) {
            _checkPointer = { line: ptrLine, ch: ptrHeadCh ?? _checkPointer.ch ?? be.ch };
        }
        UI?.updateStats?.();
        return true;
    }

    function syncCheckHeadsToLineEnd() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;

        const ptrLine = _checkPointer?.line ?? Math.max(bs.line, be.line);
        let ptrHeadCh = null;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const endCh = lineObj.length;
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const other = Math.min(a, b);
            const head = Math.max(endCh, other);
            const anchor = Math.min(endCh, other);
            colOffsets.set(l, head);
            colBsOffsets.set(l, anchor);
            if (l === ptrLine) ptrHeadCh = head;
        }
        if (_checkPointer) {
            _checkPointer = { line: ptrLine, ch: ptrHeadCh ?? _checkPointer.ch ?? be.ch };
        }
        UI?.updateStats?.();
        return true;
    }

    function syncCheckHeadDirection(mode) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;

        const ptrLine = _checkPointer?.line ?? Math.min(bs.line, be.line);
        let ptrHeadCh = null;
        for (const l of effectiveLines) {
            const a = colBsOffsets.has(l) ? colBsOffsets.get(l) : bs.ch;
            const b = colOffsets.has(l)   ? colOffsets.get(l)   : be.ch;
            const lo = Math.min(a, b);
            const hi = Math.max(a, b);
            if (mode === 'home') {
                colOffsets.set(l, lo);   // head = smaller
                colBsOffsets.set(l, hi); // anchor = larger
                if (l === ptrLine) ptrHeadCh = lo;
            } else {
                colOffsets.set(l, hi);   // head = larger
                colBsOffsets.set(l, lo); // anchor = smaller
                if (l === ptrLine) ptrHeadCh = hi;
            }
        }
        if (_checkPointer) {
            _checkPointer = { line: ptrLine, ch: ptrHeadCh ?? _checkPointer.ch ?? bs.ch };
        }
        UI?.updateStats?.();
        return true;
    }

    function _getCheckLineMeta(line, fallbackAnchor, fallbackHead) {
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const anchor = colBsOffsets?.has(line) ? colBsOffsets.get(line) : fallbackAnchor;
        const head   = colOffsets?.has(line)   ? colOffsets.get(line)   : fallbackHead;
        return { anchor, head };
    }

    function _seedCheckLineRangeAsBlock(startLine, endLine, templateLine, fallbackAnchor, fallbackHead) {
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return;
        const lo = Math.min(startLine, endLine);
        const hi = Math.max(startLine, endLine);
        const lineMeta = _getCheckLineMeta(templateLine, fallbackAnchor, fallbackHead);
        // anchor: _checkAnchorTemplate 우선 (세로 전체 기준선 유지)
        // head:   templateLine 실제값 사용 (라인별 개별 delta 복제)
        const seedAnchor = _checkAnchorTemplate ? _checkAnchorTemplate.anchor : lineMeta.anchor;
        const seedHead   = lineMeta.head;
        for (let l = lo; l <= hi; l++) {
            if (!colOffsets.has(l))   colOffsets.set(l, seedHead);
            if (!colBsOffsets.has(l)) colBsOffsets.set(l, seedAnchor);
        }
    }

    function _setCheckAnchorTemplate(template) {
        _checkAnchorTemplate = template ? { anchor: template.anchor, head: template.head } : null;
    }

    function columnMoveEnd(dir) {
        // CHECK 모드 + 상하
        // - BS는 시작 경계라서 위로 벗어날 수 없다.
        // - BS~BE 사이는 왕복만 한다.
        // - 아래 확장은 현재 포인터가 BE에 있을 때만 허용한다.
        // - 내부 왕복 중에는 checkedHeads를 자동 변경하지 않는다. (TAB으로만 on/off)
        if (window._uiIsCheckMode?.() && (dir === 'up' || dir === 'down')) {
            const bs = State.getBS(), be = State.getBE();
            if (bs && be) {
                const bsCh = bs.ch;
                if (!_checkPointer) _checkPointer = { line: be.line, ch: bsCh };

                const curLine = _checkPointer.line;
                const totalLines = Editor.lineCount();
                const rangeTop = Math.min(bs.line, be.line);
                const realBot  = Math.max(bs.line, be.line);
                // SHIFT OFF에서 BE 아래로 임시 하이라이트를 내린 경우,
                // _checkPointer가 사실상 "임시 BE" 역할을 한다.
                const tempBot  = Math.max(realBot, curLine);

                // up:
                // - CUR(쉬프트 OFF): 기존처럼 위로 preview/왕복만 한다.
                // - BLK(쉬프트 ON): BE down 확정의 반대 개념으로,
                //   현재 포인터가 BS 시작점(또는 그 위 preview)에 있으면 BS를 한 줄 위로 확정 확장한다.
                if (dir === 'up') {
                    const nextLine = Math.max(0, curLine - 1);

                    // CUR(쉬프트 OFF): 구조는 바꾸지 않고 BS temp preview만 표시
                    if (window._uiIsCheckCurMode) {
                        _checkTempBS = nextLine;
                        _checkTempIncluded = false;
                        _checkPointer = { line: nextLine, ch: bsCh };
                        _applyCheckOffsetSelection();
                        return;
                    }

                    // BLK(쉬프트 ON): BS 확정 로직 (temp BS가 있으면 그 라인을 확정)
                    if (curLine <= rangeTop) {
                        const hasTempPreview = (_checkTempBS != null && _checkTempBS < rangeTop);
                        const commitBSLine = hasTempPreview ? _checkTempBS : nextLine;
                        if (commitBSLine !== bs.line) {
                            State.forceSetBS?.({ line: commitBSLine, ch: bs.ch }) ?? State.setBS({ line: commitBSLine, ch: bs.ch });
                            _seedCheckLineRangeAsBlock(commitBSLine, rangeTop - 1, rangeTop, bs.ch, be.ch);
                        }
                        const ptrMeta = _getCheckLineMeta(commitBSLine, bs.ch, be.ch);
                        _checkTempIncluded = true;
                        _checkTempBS = null;
                        _checkPointer = { line: commitBSLine, ch: ptrMeta.head };
                        _applyCheckOffsetSelection();
                        _checkTempIncluded = false;
                        UI?.updateStats?.();
                        return;
                    }

                    // 영역 안에서는 위로 왕복만
                    _checkTempBS = null;
                    _checkPointer = { line: nextLine, ch: bsCh };
                    if (window._uiIsCheckMode?.()) _applyCheckOffsetSelection();
                    else _applyColumnSelection();
                    return;
                }

                // down:
                // 1) 아직 현재 왕복 범위 안쪽이면 이동만
                if (curLine < tempBot) {
                    _checkTempBS = null;
                    _checkPointer = { line: curLine + 1, ch: bsCh };
                    if (window._uiIsCheckMode?.()) _applyCheckOffsetSelection();
                    else _applyColumnSelection();
                    return;
                }

                // 2) 현재 포인터가 마지막 끝점(BE 또는 임시 BE)에 있을 때만 아래 확장/하이라이트
                const newBELine = Math.min(totalLines - 1, tempBot + 1);

                // CUR(쉬프트 OFF): 구조는 바꾸지 않고, 다음 라인 포인터 하이라이트만 표시
                if (window._uiIsCheckCurMode) {
                    _checkTempBE = newBELine;
                    _checkTempIncluded = false;
                    _checkPointer = { line: newBELine, ch: bsCh };
                    _applyCheckOffsetSelection();
                    return;
                }

                // BLK(쉬프트 ON)
                // - 임시 BE preview가 있으면: preview 라인들은 "제외"로 확정하고,
                //   이번 down 이벤트의 새 마지막 라인을 실제 BE(포함 + 커서)로 만든다.
                // - 임시 BE가 없으면: 기존대로 한 칸 아래 실제 BE 확장
                const checkedHeads = window._uiGetCheckedHeads?.();
                const hasTempPreview = (_checkTempBE != null && _checkTempBE > realBot);
                const commitBELine = hasTempPreview ? newBELine : newBELine;
                if (hasTempPreview && checkedHeads) {
                    for (let l = realBot + 1; l <= _checkTempBE; l++) checkedHeads.add(l);
                }
                if (checkedHeads) checkedHeads.delete(commitBELine);
                if (commitBELine !== be.line) {
                    State.setBE({ line: commitBELine, ch: be.ch });
                    _seedCheckLineRangeAsBlock(realBot + 1, commitBELine, realBot, bs.ch, be.ch);
                }
                const ptrMeta = _getCheckLineMeta(commitBELine, bs.ch, be.ch);
                _checkTempBS = null;
                _checkTempIncluded = true;
                _checkTempBE = null;
                _checkPointer = { line: commitBELine, ch: ptrMeta.head };
                _applyCheckOffsetSelection();
                _checkTempIncluded = false;
                return;
            }
        }
        const bs0 = State.getBS(), be = State.getBE() || Editor.getCursor();
        let { line, ch } = be;
        const totalLines = Editor.lineCount();
        if      (dir === 'left')  ch   = Math.max(0, ch - 1);
        else if (dir === 'right') ch   = ch + 1;
        else if (dir === 'up')    line = Math.max(0, line - 1);
        else if (dir === 'down')  line = Math.min(totalLines - 1, line + 1);
        State.setBE({ line, ch });

        // BLK 상하: 새 라인 colOffsets 시드 (직전 라인 delta/gamma 복제)
        if (!window._uiIsCheckMode?.() && (dir === 'up' || dir === 'down')) {
            const newLine = line;
            const colOffsets   = window._uiGetColOffsets?.();
            const colBsOffsets = window._uiGetColBsOffsets?.();
            if (colOffsets && colBsOffsets && !colOffsets.has(newLine)) {
                const prevLine = dir === 'down' ? newLine - 1 : newLine + 1;
                const bsCh = bs0?.ch ?? ch;
                const beCh = be.ch;
                if (!colOffsets.has(prevLine))   colOffsets.set(prevLine, beCh);
                if (!colBsOffsets.has(prevLine)) colBsOffsets.set(prevLine, bsCh);
                colOffsets.set(newLine, colOffsets.get(prevLine));
                colBsOffsets.set(newLine, colBsOffsets.get(prevLine));
            }
        }

        if (window._uiIsCheckMode?.() && (dir === 'left' || dir === 'right')) {
            const isCurMode = !!window._uiIsCheckCurMode;
            if (!isCurMode) {
                const ptrLine = _checkPointer?.line ?? be.line;
                const colOffsets   = window._uiGetColOffsets?.();
                const colBsOffsets = window._uiGetColBsOffsets?.();
                const baseCh = Math.min((State.getBS()?.ch ?? be.ch), be.ch);
                const curDelta = colOffsets?.has(ptrLine)   ? colOffsets.get(ptrLine)   : baseCh;
                const curGamma = colBsOffsets?.has(ptrLine) ? colBsOffsets.get(ptrLine) : baseCh;
                const d = dir === 'left' ? -1 : 1;
                const newDelta = Math.max(0, curDelta + d);
                if (colOffsets) colOffsets.set(ptrLine, newDelta);
                if (window._uiIsMLock?.()) {
                    // M-LOCK ON: gamma도 동시 이동 (영역 유지하며 통째로 이동)
                    const newGamma = Math.max(0, curGamma + d);
                    if (colBsOffsets) colBsOffsets.set(ptrLine, newGamma);
                } else {
                    // M-LOCK OFF: gamma 고정 (최초 한 번만 등록)
                    if (colBsOffsets && !colBsOffsets.has(ptrLine)) colBsOffsets.set(ptrLine, baseCh);
                }
                State.setBE({ line: be.line, ch: be.ch });
                _applyCheckOffsetSelection();
                return;
            } else {
                // CUR모드: delta=절대ch로 이동, gamma=최초 baseCh 고정
                // 중요: 좌우에서는 미확정 preview(temp BE)를 확정하지 않는다.
                // 여기서는 현재 포인터 라인만 개별 편집하고, BE/temp BE/checkedHeads는 보존한다.
                const ptrLine = _checkPointer?.line ?? be.line;
                const colOffsets   = window._uiGetColOffsets?.();
                const colBsOffsets = window._uiGetColBsOffsets?.();
                const baseCh = Math.min((State.getBS()?.ch ?? be.ch), be.ch);
                // delta: 현재 절대 ch에서 ±1
                const curDelta = colOffsets?.has(ptrLine) ? colOffsets.get(ptrLine) : baseCh;
                const newDelta = dir === 'left' ? Math.max(0, curDelta - 1) : curDelta + 1;
                if (colOffsets) colOffsets.set(ptrLine, newDelta);
                // gamma도 delta와 동일 (BS=BE, 커서만 이동, 음영 없음)
                if (colBsOffsets) colBsOffsets.set(ptrLine, newDelta);
                // 중간 라인에서는 원본 BE / temp BE / checkedHeads를 건드리지 않는다.
                // 마지막 끝점에서의 확정 로직만 별도 버전에서 처리되며, 여기서는 기존 상태를 그대로 보존한다.
                State.setBE({ line: be.line, ch: be.ch });
                _applyCheckOffsetSelection();
                return;
            }
        }
        // BLK OFF 좌우: colOffsets 있으면 누적, 없으면 BE.ch 갱신
        if (!window._uiIsCheckMode?.() && (dir === 'left' || dir === 'right')) {
            const colOffsets   = window._uiGetColOffsets?.();
            const colBsOffsets = window._uiGetColBsOffsets?.();
            if (colOffsets && colBsOffsets) {
                const effectiveLines = _getEffectiveLines();
                const bsCh = bs0?.ch ?? be.ch;
                const initDelta = be.ch; // setBE 이전 원래 be.ch
                for (const l of effectiveLines) {
                    if (!colOffsets.has(l))   colOffsets.set(l, initDelta);
                    if (!colBsOffsets.has(l)) colBsOffsets.set(l, bsCh);
                    const curDelta = colOffsets.get(l);
                    colOffsets.set(l, dir === 'left' ? Math.max(0, curDelta - 1) : curDelta + 1);
                }
            }
            // BE.ch는 colOffsets가 담당 — line은 유지, ch는 anchor로 복구
            State.setBE({ line, ch: bs0?.ch ?? be.ch });
        }
        // BE 범위 밖 확장 시 _checkedHeads 범위 밖 라인 정리
        window._uiTrimCheckedHeads?.();
        if (window._uiIsCheckMode?.()) _applyCheckOffsetSelection();
        else _applyColumnSelection();
    }

    // CHECK 모드: 제외 셋 반영해서 커서 재적용
    // BS/BE 동시 이동 — 단일커서 멀티라인 모드 (TAB CUR)

    function clearColumnOverlay() { Editor.clearColumnDecoration?.(); }

    // OS 키보드 입력 후 멀티커서 위치 기준으로 BS/BE + decoration 재동기화
    function syncColumnAfterInput(view) {
        if (!view) return;
        const ranges = view.state.selection.ranges;
        const bs = State.getBS();
        if (!bs) return;

        const isCheck   = !!window._uiIsCheckMode?.();
        const isCurMode = isCheck && !!window._uiIsCheckCurMode;

        if (!isCurMode && ranges.length < 2) return;

        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();

        // ranges를 line → head ch 맵으로 변환 (순서 의존 제거)
        const rangeByLine = new Map();
        for (const r of ranges) {
            const pos = Editor.offsetToPos(r.head);
            rangeByLine.set(pos.line, pos.ch);
        }

        const effectiveLines = _getEffectiveLines();

        // 음영 있으면 동기화 스킵 (음영 보호)
        if (hasCurSelection()) return;

        // CHECK ON + CUR + 단일 커서: BS/BE 범위는 유지하고 ptrLine의 delta/gamma/pointer만 갱신
        if (isCurMode && ranges.length === 1) {
            const main = view.state.selection.main;
            const pos  = Editor.offsetToPos(main.head);
            const ptrLine = _checkPointer?.line ?? pos.line;
            const ch = pos.ch;
            if (colOffsets)   colOffsets.set(ptrLine, ch);
            if (colBsOffsets) colBsOffsets.set(ptrLine, ch);
            _checkPointer = { line: ptrLine, ch };
            _applyCheckOffsetSelection();
            return;
        }

        // delta/gamma 실제 커서 위치로 갱신
        // CUR모드: ptrLine만 동기화, 나머지 라인은 유지
        if (colOffsets?.size || colBsOffsets?.size) {
            const ptrLine = _checkPointer?.line ?? (State.getBE()?.line ?? -1);
            for (const l of effectiveLines) {
                if (!rangeByLine.has(l)) continue;
                if (isCurMode && l !== ptrLine) continue; // CUR모드: ptrLine 외 스킵
                const ch = rangeByLine.get(l);
                if (colOffsets?.has(l))   colOffsets.set(l, ch);
                if (colBsOffsets?.has(l)) colBsOffsets.set(l, ch);
            }
        }
        const lines = [...rangeByLine.keys()].sort((a, b) => a - b);
        if (!lines.length) return;
        const topCh = rangeByLine.get(lines[0]);
        if (isCheck) {
            // CHECK ON: BS/BE ch는 건드리지 않음 — 이미 insertAtColumnBlock/delCharBeforeColumn이 관리
            const bs = State.getBS(), be = State.getBE();
            if (bs) State.forceSetBS({ line: lines[0], ch: bs.ch });
            if (be) State.setBE({ line: lines[lines.length - 1], ch: be.ch });
            _applyCheckOffsetSelection();
        } else {
            State.setBS({ line: lines[0], ch: topCh });
            State.setBE({ line: lines[lines.length - 1], ch: topCh });
            _applyColumnSelection();
        }
    }

    // 컬럼 블럭 각 라인 fromCh 위치에 text 삽입 (유효 라인 기준)
    // CHECK ON + CUR 전용 — ptrLine 단일커서 위치에서 일반 편집
    // action: 'delBefore' | 'delAfter' | 'insert'

    // CUR 모드 전용 ENTER — 각 커서 위치에 줄 분리, 커서 다음 줄 처음으로

    function insertAtColumnBlock(text) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        // BS/BE ch 불일치 시 BE를 BS 기준으로 수렴 (빠른 입력 시 선반영 방지)
        if (bs.ch !== be.ch) {
            State.setBE({ line: be.line, ch: bs.ch });
        }
        const isCheck      = window._uiIsCheckMode?.();
        const isCurMode    = isCheck && !!window._uiIsCheckCurMode;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const baseCh       = Math.min(bs.ch, be.ch);
        const hasOffsets   = colOffsets?.size > 0;
        const ptrLine      = _checkPointer?.line ?? be.line;

        // 현재 상태로 읽기 (음영 삭제는 호출부에서 처리)
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;

        const len = text.length;

        if (isCurMode) {
            // CUR모드: ptrLine만 실제 삽입, 나머지는 오프셋만 유지
            const lineNum = ptrLine + 1;
            if (lineNum > doc.lines) return;
            const lineObj = doc.line(lineNum);
            const delta = colOffsets?.has(ptrLine) ? colOffsets.get(ptrLine) : baseCh;
            const ch    = Math.min(delta, lineObj.length);
            _columnEditing = true;
            view.dispatch({ changes: [{ from: lineObj.from + ch, to: lineObj.from + ch, insert: text }], userEvent: 'input' });
            // ptrLine delta/gamma +len
            const d = colOffsets?.has(ptrLine) ? colOffsets.get(ptrLine) : baseCh;
            const g = colBsOffsets?.has(ptrLine) ? colBsOffsets.get(ptrLine) : baseCh;
            colOffsets?.set(ptrLine,   d + len);
            colBsOffsets?.set(ptrLine, g + len);
            // BS/BE ch +len 동기화 (CHECK ON 시 스킵)
            if (!isCheck) {
                State.forceSetBS({ line: bs.line, ch: bs.ch + len });
                State.setBE({ line: be.line, ch: be.ch + len });
            }
            // 나머지 라인: 오프셋 변화 없음 (삽입 없으므로)
        } else {
            // BLK모드 또는 CHECK OFF: 전체 라인 삽입
            const changes = [];
            for (const l of effectiveLines) {
                const lineNum = l + 1;
                if (lineNum > doc.lines) continue;
                const lineObj = doc.line(lineNum);
                const delta = colOffsets?.has(l) ? colOffsets.get(l) : baseCh;
                const ch    = Math.min(delta, lineObj.length);
                changes.push({ from: lineObj.from + ch, to: lineObj.from + ch, insert: text });
            }
            if (!changes.length) return;
            _columnEditing = true;
                view.dispatch({ changes, userEvent: 'input' });
            // delta +len, gamma +len
            for (const l of effectiveLines) {
                const d = colOffsets?.has(l) ? colOffsets.get(l) : baseCh;
                const g = colBsOffsets?.has(l) ? colBsOffsets.get(l) : baseCh;
                colOffsets?.set(l,   d + len);
                colBsOffsets?.set(l, g + len);
            }
            // BS/BE ch +len 동기화 (CHECK ON 시 스킵 — colOffsets 독립 운용)
            if (!isCheck) {
                State.forceSetBS({ line: bs.line, ch: bs.ch + len });
                State.setBE({ line: be.line, ch: be.ch + len });
            }
        }

        if (isCurMode) {
            // CUR모드: 멀티커서 전체 재렌더 (ptrLine 커서가 +len 위치에 있음)
            _applyCheckOffsetSelection();
        } else if (isCheck) {
            _applyCheckOffsetSelection();
        } else {
            _applyColumnSelection();
        }
        Editor.focus();
        clearTimeout(_columnEditingTimer); _columnEditingTimer = setTimeout(() => { _columnEditing = false; }, 50);
    }

    // 멀티라인 각 커서에서 앞 글자 삭제
    function delCharBeforeColumn(opts) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;
        const isCheck      = window._uiIsCheckMode?.();
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const baseCh       = bs.ch;
        const allowNewline = opts?.allowNewline ?? false;
        const hasOffsets   = colOffsets?.size > 0;

        // 커서(delta)가 뒤(END쪽): 음영이 앞에 있음 → 음영 삭제
        if (hasOffsets && isCursorAfterSelection()) {
            deleteCurSelection();
            return;
        }

        // 커서(delta)가 앞이거나 음영 없음: delta 위치 앞 문자 삭제
        // 오프셋 정보(delta/gamma)는 그대로 유지하되 둘 다 -1 이동
        const changes = [];
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj  = doc.line(lineNum);
            const delta = colOffsets?.has(l) ? colOffsets.get(l) : baseCh;
            const pos   = lineObj.from + Math.min(delta, lineObj.length);
            if (!allowNewline && pos <= lineObj.from) continue;
            if (pos <= 0) continue;
            const prevCh = doc.sliceString(pos - 1, pos);
            if (!allowNewline && prevCh === '\n') continue;
            changes.push({ from: pos - 1, to: pos });
        }
        if (!changes.length) return;
        _columnEditing = true;
        view.dispatch({ changes, userEvent: 'input' });

        // 줄바꿈 삭제(라인 병합) 여부 감지 — delta=0 이었던 라인이 병합됨
        // dispatch 후 CM6 실제 커서 위치로 BS/BE 동기화
        const mainAfter = view.state.selection.main;
        const posAfter  = Editor.offsetToPos(mainAfter.head);
        const didMerge  = effectiveLines.some(l => {
            const delta = colOffsets?.has(l) ? colOffsets.get(l) : baseCh;
            return delta === 0 && l > 0;
        });

        if (didMerge && !isCheck) {
            // 병합: CM6 실제 커서 위치로 BS/BE 갱신, colOffsets 클리어
            State.forceSetBS({ line: posAfter.line, ch: posAfter.ch });
            State.setBE({ line: posAfter.line, ch: posAfter.ch });
            if (colOffsets)   colOffsets.clear();
            if (colBsOffsets) colBsOffsets.clear();
            _applyColumnSelection();
        } else {
            // 일반 BS: delta -1, gamma -1
            for (const l of effectiveLines) {
                const d = colOffsets?.has(l)   ? colOffsets.get(l)   : baseCh;
                const g = colBsOffsets?.has(l) ? colBsOffsets.get(l) : baseCh;
                colOffsets?.set(l,   Math.max(0, d - 1));
                colBsOffsets?.set(l, Math.max(0, g - 1));
            }
            if (!isCheck) {
                State.forceSetBS({ line: bs.line, ch: Math.max(0, bs.ch - 1) });
                State.setBE({ line: be.line, ch: Math.max(0, be.ch - 1) });
            }
            if (isCheck) _applyCheckOffsetSelection();
            else _applyColumnSelection();
        }
        Editor.focus();
        clearTimeout(_columnEditingTimer); _columnEditingTimer = setTimeout(() => { _columnEditing = false; }, 50);
    }

    // 멀티라인 각 커서에서 뒤 글자 삭제
    function delCharAfterColumn(opts) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;
        const isCheck      = window._uiIsCheckMode?.();
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const baseCh       = bs.ch;
        const allowNewline = opts?.allowNewline ?? false;
        const hasOffsets   = colOffsets?.size > 0;

        // 커서(delta)가 앞(HOME쪽): 음영이 뒤에 있음 → 음영 삭제
        if (hasOffsets && isCursorBeforeSelection()) {
            deleteCurSelection();
            return;
        }

        // 커서(delta)가 뒤이거나 음영 없음: delta 위치 뒤 문자 삭제
        // 커서 위치 불변 → delta/gamma 변화 없음
        const changes = [];
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj  = doc.line(lineNum);
            const delta = colOffsets?.has(l) ? colOffsets.get(l) : baseCh;
            const pos   = lineObj.from + Math.min(delta, lineObj.length);
            if (!allowNewline && pos >= lineObj.to) continue;
            if (pos >= doc.length) continue;
            const nextCh = doc.sliceString(pos, pos + 1);
            if (!allowNewline && nextCh === '\n') continue;
            changes.push({ from: pos, to: pos + 1 });
        }
        if (!changes.length) return;
        _columnEditing = true;
        view.dispatch({ changes, userEvent: 'input' });
        // DEL: 커서 위치 불변 — 오프셋 변화 없음

        // 렌더
        if (isCheck) {
            _applyCheckOffsetSelection();
        } else {
            _applyColumnSelection();
        }
        Editor.focus();
        clearTimeout(_columnEditingTimer); _columnEditingTimer = setTimeout(() => { _columnEditing = false; }, 50);
    }

    // CHECK ON + BLK: 각 라인 개별 음영(gamma~delta) 삭제 후 delta=gamma로 수렴
    function hasCurSelection() {
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const [l, delta] of colOffsets) {
            const gamma = colBsOffsets.has(l) ? colBsOffsets.get(l) : delta;
            if (delta !== gamma) return true;
        }
        return false;
    }

    // 커서(delta)가 음영 앞쪽인지: delta < gamma (커서가 왼쪽, 음영이 오른쪽)
    function isCursorBeforeSelection() {
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const [l, delta] of colOffsets) {
            const gamma = colBsOffsets.has(l) ? colBsOffsets.get(l) : delta;
            if (delta < gamma) return true;
        }
        return false;
    }

    // 커서(delta)가 음영 뒤쪽인지: delta > gamma (커서가 오른쪽, 음영이 왼쪽)

    function deleteCurSelection() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;
        _columnEditing = true;

        // 각 라인 독립 dispatch — 자기 음영만 삭제, gamma=delta=fromCh로 수렴
        for (const l of effectiveLines) {
            const doc = view.state.doc;
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const delta = colOffsets?.has(l)   ? colOffsets.get(l)   : 0;
            const gamma = colBsOffsets?.has(l) ? colBsOffsets.get(l) : delta;
            if (delta === gamma) continue;
            const fromCh = Math.min(delta, gamma);
            const toCh   = Math.max(delta, gamma);
            const from = lineObj.from + Math.min(fromCh, lineObj.length);
            const to   = lineObj.from + Math.min(toCh,   lineObj.length);
            if (from >= to) continue;
            // 개별 dispatch
            view.dispatch({ changes: { from, to, insert: '' }, userEvent: 'delete' });
            // CM6 동기화: delta=gamma=fromCh
            colOffsets?.set(l,   fromCh);
            colBsOffsets?.set(l, fromCh);
        }

        _applyCheckOffsetSelection();
        Editor.focus();
        clearTimeout(_columnEditingTimer); _columnEditingTimer = setTimeout(() => { _columnEditing = false; }, 50);
    }

    function copyColumnBlock() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return '';
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const effectiveLines = _getEffectiveLines();
        const baseCh = Math.min(bs.ch, be.ch);
        const lines = [];
        for (const l of effectiveLines) {
            const row = Editor.getLine(l) || '';
            if (colOffsets?.has(l) || colBsOffsets?.has(l)) {
                // 개별 delta/gamma 블럭
                const delta = colOffsets?.has(l)   ? colOffsets.get(l)   : baseCh;
                const gamma = colBsOffsets?.has(l) ? colBsOffsets.get(l) : baseCh;
                const from = Math.min(delta, gamma);
                const to   = Math.max(delta, gamma);
                lines.push(row.slice(from, to));
            } else {
                // 일반 컬럼 범위
                const fromCh = Math.min(bs.ch, be.ch);
                const toCh   = Math.max(bs.ch, be.ch);
                lines.push(row.slice(fromCh, toCh));
            }
        }
        const text = lines.join('\n');
        _clipData = text;
        _clipWrite(text);
        return text;
    }

    function _getOffBlockLinePair(line) {
        const bs = State.getBS(), be = State.getBE();
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        const anchor = colBsOffsets?.has(line) ? colBsOffsets.get(line) : (bs?.ch ?? 0);
        const head   = colOffsets?.has(line)   ? colOffsets.get(line)   : (be?.ch ?? 0);
        return { anchor, head };
    }

    function _areOffBlockHeadsAtDirection(mode) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        for (const l of effectiveLines) {
            const { anchor, head } = _getOffBlockLinePair(l);
            const lo = Math.min(anchor, head);
            const hi = Math.max(anchor, head);
            if (mode === 'home') {
                if (head !== lo) return false;
            } else {
                if (head !== hi) return false;
            }
        }
        return true;
    }

    function _syncOffBlockHeadDirection(mode) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const { anchor, head } = _getOffBlockLinePair(l);
            const lo = Math.min(anchor, head);
            const hi = Math.max(anchor, head);
            if (mode === 'home') {
                colOffsets.set(l, lo);
                colBsOffsets.set(l, hi);
            } else {
                colOffsets.set(l, hi);
                colBsOffsets.set(l, lo);
            }
        }
        UI?.updateStats?.();
        return true;
    }

    function _areOffBlockHeadsAtSoftHome() {
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return false;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softHomeCh(lineText);
            const { head } = _getOffBlockLinePair(l);
            if (head !== softCh) return false;
        }
        return true;
    }

    function _syncOffBlockHeadsToSoftHome() {
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softHomeCh(lineText);
            const { anchor, head } = _getOffBlockLinePair(l);
            const other = Math.max(anchor, head);
            colOffsets.set(l, Math.min(softCh, other));
            colBsOffsets.set(l, Math.max(softCh, other));
        }
        UI?.updateStats?.();
        return true;
    }

    function _areOffBlockHeadsAtColumnZero() {
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        for (const l of effectiveLines) {
            const { head } = _getOffBlockLinePair(l);
            if (head !== 0) return false;
        }
        return true;
    }

    function _syncOffBlockHeadsToColumnZero() {
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const { anchor, head } = _getOffBlockLinePair(l);
            const other = Math.max(anchor, head);
            colOffsets.set(l, 0);
            colBsOffsets.set(l, Math.max(other, 0));
        }
        UI?.updateStats?.();
        return true;
    }

    function _areOffBlockHeadsAtSoftEnd() {
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return false;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softEndCh(lineText);
            const { head } = _getOffBlockLinePair(l);
            if (head !== softCh) return false;
        }
        return true;
    }

    function _syncOffBlockHeadsToSoftEnd() {
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            const softCh = _softEndCh(lineText);
            const { anchor, head } = _getOffBlockLinePair(l);
            const other = Math.min(anchor, head);
            colOffsets.set(l, Math.max(softCh, other));
            colBsOffsets.set(l, Math.min(softCh, other));
        }
        UI?.updateStats?.();
        return true;
    }

    function _areOffBlockHeadsAtLineEnd() {
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return false;
            const lineObj = doc.line(lineNum);
            const endCh = lineObj.length;
            const { head } = _getOffBlockLinePair(l);
            if (head !== endCh) return false;
        }
        return true;
    }

    function _syncOffBlockHeadsToLineEnd() {
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return false;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        for (const l of effectiveLines) {
            const lineNum = l + 1;
            if (lineNum > doc.lines) continue;
            const lineObj = doc.line(lineNum);
            const endCh = lineObj.length;
            const { anchor, head } = _getOffBlockLinePair(l);
            const other = Math.min(anchor, head);
            colOffsets.set(l, Math.max(endCh, other));
            colBsOffsets.set(l, Math.min(endCh, other));
        }
        UI?.updateStats?.();
        return true;
    }

    // 블럭모드 멀티커서 HOME — 유효 라인 각 커서를 라인 시작으로
    // 소프트홈 ch — 들여쓰기 끝 위치
    function _softHomeCh(lineText) {
        let i = 0;
        while (i < lineText.length && (lineText[i] === ' ' || lineText[i] === '\t')) i++;
        return i;
    }

    function _softEndCh(lineText) {
        let i = lineText.length;
        while (i > 0 && (lineText[i - 1] === ' ' || lineText[i - 1] === '\t')) i--;
        return i;
    }

    function cycleCurrentCheckLineHome() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const ptrLine = _checkPointer?.line ?? Math.min(bs.line, be.line);
        const lineNum = ptrLine + 1;
        if (lineNum > doc.lines) return false;
        const colOffsets = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        const lineObj = doc.line(lineNum);
        const lineText = doc.sliceString(lineObj.from, lineObj.to);
        const softCh = _softHomeCh(lineText);
        const a = colBsOffsets.has(ptrLine) ? colBsOffsets.get(ptrLine) : bs.ch;
        const b = colOffsets.has(ptrLine) ? colOffsets.get(ptrLine) : be.ch;
        const lo = Math.min(a, b), hi = Math.max(a, b);
        let head, anchor;
        if (b !== lo) {
            head = lo; anchor = hi;
        } else if (b !== softCh) {
            const other = hi;
            head = Math.min(softCh, other);
            anchor = Math.max(softCh, other);
        } else {
            const target = (b === 0) ? softCh : 0;
            const other = hi;
            head = Math.min(target, other);
            anchor = Math.max(target, other);
        }
        colOffsets.set(ptrLine, head);
        colBsOffsets.set(ptrLine, anchor);
        _checkPointer = { line: ptrLine, ch: head };
        _applyCheckOffsetSelection();
        return true;
    }

    function cycleCurrentCheckLineEnd() {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return false;
        if (!window._uiIsCheckMode?.()) return false;
        const view = Editor.get?.();
        if (!view) return false;
        const doc = view.state.doc;
        const ptrLine = _checkPointer?.line ?? Math.max(bs.line, be.line);
        const lineNum = ptrLine + 1;
        if (lineNum > doc.lines) return false;
        const colOffsets = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        if (!colOffsets || !colBsOffsets) return false;
        const lineObj = doc.line(lineNum);
        const lineText = doc.sliceString(lineObj.from, lineObj.to);
        const softCh = _softEndCh(lineText);
        const endCh = lineObj.length;
        const a = colBsOffsets.has(ptrLine) ? colBsOffsets.get(ptrLine) : bs.ch;
        const b = colOffsets.has(ptrLine) ? colOffsets.get(ptrLine) : be.ch;
        const lo = Math.min(a, b), hi = Math.max(a, b);
        let head, anchor;
        if (b !== hi) {
            head = hi; anchor = lo;
        } else if (b != softCh) {
            const other = lo;
            head = Math.max(softCh, other);
            anchor = Math.min(softCh, other);
        } else {
            const target = (b === endCh) ? softCh : endCh;
            // softCh→endCh: 블럭 밖으로 나가는 순간 스냅샷
            if (target === endCh) _pushBlockSnapshot();
            const other = lo;
            head = Math.max(target, other);
            anchor = Math.min(target, other);
        }
        colOffsets.set(ptrLine, head);
        colBsOffsets.set(ptrLine, anchor);
        _checkPointer = { line: ptrLine, ch: head };
        _applyCheckOffsetSelection();
        return true;
    }

    // 블럭모드 멀티커서 HOME
    // CHECK+CUR: ptrLine delta/gamma를 softCh↔0 토글 후 전체 재렌더 (다른 라인 커서 유지)
    // CHECK+BLK / 일반: 유효 라인 전체를 컬럼0으로 (gamma=delta, 음영 없음 or 음영)
    function columnHomeAll(opts) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        const doc = view.state.doc;
        const cursorOnly = opts?.cursorOnly;
        const isCheck = window._uiIsCheckMode?.();

        // CHECK + CUR: ptrLine만 토글, 나머지 그대로
        if (isCheck && cursorOnly) {
            const ptrLine      = _checkPointer?.line ?? be.line;
            const lineNum      = ptrLine + 1;
            if (lineNum > doc.lines) return;
            const lineObj      = doc.line(lineNum);
            const lineText     = doc.sliceString(lineObj.from, lineObj.to);
            const softCh       = _softHomeCh(lineText);
            const colOffsets   = window._uiGetColOffsets?.();
            const colBsOffsets = window._uiGetColBsOffsets?.();
            // 현재 delta — CHECK ON 시 이미 등록되어 있음
            const curDelta = colOffsets?.has(ptrLine) ? colOffsets.get(ptrLine) : Math.min(bs.ch, be.ch);
            // 토글: softCh 위치면 0으로, 그 외는 softCh로
            const targetCh = (curDelta === softCh) ? 0 : softCh;
            if (colOffsets)   colOffsets.set(ptrLine, targetCh);
            if (colBsOffsets) colBsOffsets.set(ptrLine, targetCh); // gamma=delta (음영 없음)
            // 전체 재렌더 — 다른 라인 커서 유지
            _applyCheckOffsetSelection();
            return;
        }

        // CHECK+BLK: delta=gamma=0 전체 초기화 후 재렌더
        if (isCheck) {
            const colOffsets   = window._uiGetColOffsets?.();
            const colBsOffsets = window._uiGetColBsOffsets?.();
            for (const l of _getEffectiveLines()) {
                colOffsets?.set(l, 0);
                colBsOffsets?.set(l, 0);
            }
            State.setBS({ line: bs.line, ch: 0 });
            State.setBE({ line: be.line, ch: 0 });
            _applyCheckOffsetSelection();
            return;
        }

        // 일반 블럭모드: 체크온과 같은 개별 오프셋 기반 HOME 사이클
        if (!cursorOnly) {
            if (!_areOffBlockHeadsAtDirection('home')) {
                _syncOffBlockHeadDirection('home');
            } else if (_areOffBlockHeadsAtSoftHome()) {
                if (_areOffBlockHeadsAtColumnZero()) {
                    _syncOffBlockHeadsToSoftHome();
                } else {
                    _pushBlockSnapshot(); // 블럭 밖(column 0)으로 나가기 전 저장
                    _syncOffBlockHeadsToColumnZero();
                }
            } else {
                _syncOffBlockHeadsToSoftHome();
            }
            _applyColumnSelection();
            return;
        }

        // 일반 CUR: softHome → ch=0 사이클 (BLK와 동일)
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;
        const colOffsets   = window._uiGetColOffsets?.();
        const colBsOffsets = window._uiGetColBsOffsets?.();
        // 모든 라인이 softHome에 있으면 ch=0, 아니면 softHome
        const allAtSoftHome = effectiveLines.every(l => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return true;
            const lineText = doc.sliceString(doc.line(lineNum).from, doc.line(lineNum).to);
            const softCh = _softHomeCh(lineText);
            const curCh = colOffsets?.has(l) ? colOffsets.get(l) : Math.min(bs.ch, be.ch);
            return curCh === softCh;
        });
        if (allAtSoftHome) _pushBlockSnapshot(); // 블럭 밖(column 0)으로 나가기 전 저장
        const targetCh = (l) => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return 0;
            const lineText = doc.sliceString(doc.line(lineNum).from, doc.line(lineNum).to);
            return allAtSoftHome ? 0 : _softHomeCh(lineText);
        };
        const offsets = effectiveLines.map(l => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return null;
            const ch = targetCh(l);
            const pos = doc.line(lineNum).from + ch;
            if (colOffsets)   colOffsets.set(l, ch);
            if (colBsOffsets) colBsOffsets.set(l, ch);
            return { anchor: pos, head: pos };
        }).filter(Boolean);
        if (!offsets.length) return;
        Editor.setColumnSelectionFull?.(offsets, 0);
        const newBsCh = targetCh(effectiveLines[0]);
        const newBeCh = targetCh(effectiveLines[effectiveLines.length - 1]);
        State.setBS({ line: bs.line, ch: newBsCh });
        State.setBE({ line: be.line, ch: newBeCh });
        UI?.updateStats?.();
    }

    // 블럭모드 멀티커서 END
    // CHECK+CUR: ptrLine delta/gamma를 라인끝으로, 전체 재렌더
    // CHECK+BLK / 일반: 유효 라인 전체를 라인끝으로
    function columnEndAll(opts) {
        const bs = State.getBS(), be = State.getBE();
        if (!bs || !be) return;
        const view = Editor.get?.();
        if (!view) return;
        const doc = view.state.doc;
        const cursorOnly = opts?.cursorOnly;
        const isCheck = window._uiIsCheckMode?.();

        // CHECK + CUR: ptrLine만, 나머지 그대로
        if (isCheck && cursorOnly) {
            const ptrLine      = _checkPointer?.line ?? be.line;
            const lineNum      = ptrLine + 1;
            if (lineNum > doc.lines) return;
            const lineObj      = doc.line(lineNum);
            const endCh        = lineObj.length;
            const colOffsets   = window._uiGetColOffsets?.();
            const colBsOffsets = window._uiGetColBsOffsets?.();
            if (colOffsets)   colOffsets.set(ptrLine, endCh);
            if (colBsOffsets) colBsOffsets.set(ptrLine, endCh); // gamma=delta
            _applyCheckOffsetSelection();
            return;
        }

        // CHECK+BLK: delta=라인끝, gamma 유지 (앵커 보존)
        if (isCheck) {
            const colOffsets = window._uiGetColOffsets?.();
            const view2 = Editor.get?.();
            const doc2  = view2?.state.doc;
            for (const l of _getEffectiveLines()) {
                const lineNum = l + 1;
                if (!doc2 || lineNum > doc2.lines) continue;
                const endCh = doc2.line(lineNum).length;
                colOffsets?.set(l, endCh); // delta만, gamma 그대로
            }
            const beLen = (Editor.getLine(be.line) || '').length;
            State.setBE({ line: be.line, ch: beLen });
            _applyCheckOffsetSelection();
            return;
        }

        // 일반 블럭모드: 체크온과 같은 개별 오프셋 기반 END 사이클
        if (!cursorOnly) {
            if (!_areOffBlockHeadsAtDirection('end')) {
                _syncOffBlockHeadDirection('end');
            } else if (_areOffBlockHeadsAtSoftEnd()) {
                if (_areOffBlockHeadsAtLineEnd()) {
                    _pushBlockSnapshot(); // 라인 끝(블럭 밖)에서 softEnd로 복귀 전 저장
                    _syncOffBlockHeadsToSoftEnd();
                } else {
                    _pushBlockSnapshot(); // 블럭 밖(라인 끝)으로 나가기 전 저장
                    _syncOffBlockHeadsToLineEnd();
                }
            } else {
                _syncOffBlockHeadsToSoftEnd();
            }
            _applyColumnSelection();
            return;
        }

        // 일반 CUR: softEnd → 라인끝 사이클 (BLK와 동일)
        const effectiveLines = _getEffectiveLines();
        if (!effectiveLines.length) return;
        const colOffsets2   = window._uiGetColOffsets?.();
        const colBsOffsets2 = window._uiGetColBsOffsets?.();
        // 모든 라인이 softEnd에 있으면 라인끝, 아니면 softEnd
        const allAtSoftEnd = effectiveLines.every(l => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return true;
            const lineText = doc.sliceString(doc.line(lineNum).from, doc.line(lineNum).to);
            const softCh = _softEndCh(lineText);
            const curCh = colOffsets2?.has(l) ? colOffsets2.get(l) : Math.max(bs.ch, be.ch);
            return curCh === softCh;
        });
        if (allAtSoftEnd) _pushBlockSnapshot(); // softEnd → lineEnd(블럭 밖) 직전 저장
        // lineEnd에서 한번 더 누를 때(softEnd로 복귀): 스냅샷
        if (!allAtSoftEnd) {
            const allAtLineEnd = effectiveLines.every(l => {
                const lineNum = l + 1;
                if (lineNum > doc.lines) return true;
                const lineObj = doc.line(lineNum);
                const curCh = colOffsets2?.has(l) ? colOffsets2.get(l) : Math.max(bs.ch, be.ch);
                return curCh === lineObj.length;
            });
            if (allAtLineEnd) _pushBlockSnapshot(); // lineEnd(블럭 밖)에서 softEnd로 복귀 전 저장
        }
        const targetEndCh = (l) => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return 0;
            const lineObj = doc.line(lineNum);
            const lineText = doc.sliceString(lineObj.from, lineObj.to);
            return allAtSoftEnd ? lineObj.length : _softEndCh(lineText);
        };
        const offsets = effectiveLines.map(l => {
            const lineNum = l + 1;
            if (lineNum > doc.lines) return null;
            const lineObj = doc.line(lineNum);
            const ch = targetEndCh(l);
            const pos = lineObj.from + ch;
            if (colOffsets2)   colOffsets2.set(l, ch);
            if (colBsOffsets2) colBsOffsets2.set(l, ch);
            return { anchor: pos, head: pos };
        }).filter(Boolean);
        if (!offsets.length) return;
        Editor.setColumnSelectionFull?.(offsets, 0);
        const bsLen = targetEndCh(effectiveLines[0]);
        const beLen = targetEndCh(effectiveLines[effectiveLines.length - 1]);
        State.setBS({ line: bs.line, ch: bsLen });
        State.setBE({ line: be.line, ch: beLen });
        UI?.updateStats?.();
    }

    // 컬럼 클립데이터를 커서 위치 기준으로 각 라인에 삽입
    function pasteColumnBlock() {
        if (!_clipData) return;
        const bs = State.getBS(), be = State.getBE();
        if (!bs) return;
        const clipLines = _clipData.split('\n');
        const startLine = Math.min(bs.line, be ? be.line : bs.line);
        const insertCh  = Math.min(bs.ch, be ? be.ch : bs.ch);
        const view = Editor.get?.();
        if (!view) return;
        const doc = view.state.doc;
        const changes = [];
        for (let i = 0; i < clipLines.length; i++) {
            const lineNum = startLine + i + 1;
            if (lineNum > doc.lines) break;
            const lineObj = doc.line(lineNum);
            const pos = lineObj.from + Math.min(insertCh, lineObj.length);
            changes.push({ from: pos, to: pos, insert: clipLines[i] });
        }
        if (!changes.length) return;
        view.dispatch({ changes, userEvent: 'input' });
        const lastLine = startLine + Math.min(clipLines.length, doc.lines - startLine) - 1;
        const newCh = insertCh + clipLines[0].length;
        State.setBS({ line: startLine, ch: insertCh });
        State.setBE({ line: lastLine,  ch: newCh });
        _applyColumnSelection();
        Editor.focus?.();
    }
    return {
        toggleModeS, afterMove,
        trySwapByKey, swapHE,
        moveBlockBy, moveLineAlt, indent, shiftBlock,
        copyBlock, cutLine,
        getClipData, setClipData,
        columnMoveEnd, copyColumnBlock, pasteColumnBlock, clearColumnOverlay,
        columnHomeAll, columnEndAll,
        insertAtColumnBlock, deleteCurSelection, hasCurSelection, isCursorBeforeSelection, delCharBeforeColumn, delCharAfterColumn, syncColumnAfterInput, forceConvergeOffsets,
        applyColumnSelection: _applyColumnSelection,
        isMoving: () => _swapping,
        isColumnEditing: () => _columnEditing,
        applyPtrLineSingleCursor: () => {
            // CUR모드: ptrLine만 단일 커서로 CM6에 등록, 멀티커서 구조는 유지
            const bs = State.getBS(), be = State.getBE();
            if (!bs || !be) return;
            const view = Editor.get?.();
            if (!view) return;
            const colOffsets   = window._uiGetColOffsets?.();
            const colBsOffsets = window._uiGetColBsOffsets?.();
            const ptrLine = window.NavBlock?.getCheckPointer?.()?.line ?? be.line;
            const baseCh  = Math.min(bs.ch, be.ch);
            const doc     = view.state.doc;
            const lineNum = ptrLine + 1;
            if (lineNum > doc.lines) return;
            const lineObj = doc.line(lineNum);
            const delta = colOffsets?.has(ptrLine)   ? colOffsets.get(ptrLine)   : baseCh;
            const gamma = colBsOffsets?.has(ptrLine) ? colBsOffsets.get(ptrLine) : baseCh;
            const dPos  = lineObj.from + Math.min(delta, lineObj.length);
            const gPos  = lineObj.from + Math.min(gamma, lineObj.length);
            // ptrLine 단일 커서만 CM6에
            Editor.setColumnSelectionFull?.([{ anchor: gPos, head: dPos }], 0);
        },
        _resetCheckPointer: () => { _checkPointer = null; _checkTempBS = null; _checkTempBE = null; _checkTempIncluded = false; Editor.clearCheckLines?.(); },
        pushBlockSnapshot: _pushBlockSnapshot,
        popBlockSnapshot: _popBlockSnapshot,
        clearBlockSnapshots: _clearBlockSnapshots,
        getBlockSnapshotCount: () => _blockSnapshots.length,
        _setCheckPointer: (pos) => { _checkPointer = pos ? { ...pos } : null; },
        getCheckPointer: () => _checkPointer,
        syncCheckHeadDirection,
        isCheckHeadDirection,
        areCheckHeadsAtSoftHome,
        syncCheckHeadsToSoftHome,
        syncCheckHeadsToColumnZero,
        cycleCurrentCheckLineHome,
        cycleCurrentCheckLineEnd,
        areCheckHeadsAtSoftEnd,
        syncCheckHeadsToSoftEnd,
        syncCheckHeadsToLineEnd,
        _setCheckAnchorTemplate,
    };
})();

window.NavBlock = NavBlock;
