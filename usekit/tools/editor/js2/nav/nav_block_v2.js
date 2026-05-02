/* Path: usekit/tools/editor/js2/nav/nav_block_v2.js
 * CM6 ranges 기반 멀티블럭 편집 — BlockState 위에서 동작
 * ─────────────────────────────────────────────────────────── */

const NavBlockV2 = (function () {
    'use strict';

    const BS = () => window.BlockState;

    function _v()   { return window.Editor?.get?.(); }
    function _doc() { return _v()?.state.doc ?? null; }

    // ── M-LOCK 논리 컬럼 ─────────────────────────────────
    // _logicalCol: 모든 range가 공유하는 논리적 head 컬럼
    //   실제 head = min(_logicalCol, lineLen)
    //   짧은 라인은 lineEnd에 고정, 긴 라인도 _logicalCol 기준으로 동기화
    let _logicalCol = null;

    function _mlockInit() {
        const doc = _doc(); if (!doc) return;
        const ranges = BS().getRanges();
        if (!ranges.length) { _logicalCol = null; return; }
        // 진입 시 논리 컬럼 = 가장 긴 실제 head col
        _logicalCol = Math.max(...ranges.map(r => r.head - doc.lineAt(r.head).from));
    }

    function _mlockClear() {
        _logicalCol = null;
    }

    // ── V2 위치 스냅샷 (undo/redo용) ────────────────────
    const _V2_SNAP_MAX = 40;
    const _v2Snapshots = [];

    function _pushV2Snapshot() {
        const ranges = BS().getRanges();
        if (!ranges.length) return;
        const snap = ranges.map(r => ({ anchor: r.anchor, head: r.head }));
        _v2Snapshots.push({ ranges: snap, mainIdx: BS().getMainIdx() });
        if (_v2Snapshots.length > _V2_SNAP_MAX) _v2Snapshots.shift();
        window.UI?.updateUndoRedo?.();
    }

    function _popV2Snapshot() {
        const snap = _v2Snapshots.pop();
        if (!snap) return false;
        BS().dispatch(snap.ranges, snap.mainIdx);
        BS().render();
        window.UI?.updateUndoRedo?.();
        return true;
    }

    function _v2SnapshotCount() { return _v2Snapshots.length; }

    function _lineLen(l) { return BS().lineLen(l); }
    function _lineFrom(l){ return BS().lineFrom(l); }
    function _clamp(ch, l){ return Math.max(0, Math.min(ch, _lineLen(l))); }

    // ── ghostLine (CHECK CUR 모드 범위 밖 임시 포인터) ───
    let _ghostLine = null; // 라인 번호 (0-based), null = 비활성

    function _clearGhost() {
        _ghostLine = null;
    }

    // 기존 ranges + ghostLine 프리하이라이트를 합쳐서 decoration 업데이트
    function _renderWithGhost() {
        const doc = _doc(); if (!doc) return;
        const ranges = BS().getRanges();
        const decoSpecs = ranges.map(r => ({ anchor: r.anchor, head: r.head }));
        if (_ghostLine !== null) {
            const mainIdx   = BS().getMainIdx();
            const mainR     = ranges[Math.min(mainIdx, ranges.length - 1)];
            const mainCol   = mainR ? (mainR.head - _lineFrom(_doc().lineAt(mainR.head).number - 1)) : 0;
            const gLineFrom = _lineFrom(_ghostLine);
            const gLineLen  = _doc().line(_ghostLine + 1).length;
            const gCol      = Math.min(mainCol, gLineLen);
            const gOffset   = gLineFrom + gCol;
            decoSpecs.push({ anchor: gOffset, head: gOffset });
        }
        // ghost 포함 decoration 직접 업데이트 (BS().render() 생략 — 덮어쓰기 방지)
        window.Editor?.updateColumnDecoration?.(decoSpecs);
    }

    function _syncBasesFromView(mainIdx = 0) {
        const v = _v(); if (!v) return;
        const ranges = Array.from(v.state.selection.ranges || []);
        if (!ranges.length) return;
        const idx = Math.max(0, Math.min(mainIdx, ranges.length - 1));
        const r = ranges[idx];
        const line = v.state.doc.lineAt(r.head);
        BS().setBaseLine(line.number - 1);
        BS().setBaseCh(Math.max(0, r.anchor - line.from));
        BS().setBaseHdCh(Math.max(0, r.head - line.from));
    }

    function _applySelectionToView(specs, mainIdx = 0) {
        const normalized = (specs || []).map(r => ({ anchor: r.anchor, head: r.head }));
        if (!normalized.length) return;
        window.Editor?.setColumnSelectionFull?.(normalized, mainIdx);
        // DEL 좌측음영 유지처럼 selection은 같은데 데코만 빠지는 케이스를 막기 위해
        // decoration도 한 번 더 명시적으로 동기화한다.
        window.Editor?.updateColumnDecoration?.(normalized);
        _syncBasesFromView(mainIdx);
        BS().render();
    }

    // ── 방향키 ───────────────────────────────────────────

    // CHECK OFF:
    // CUR(쉬프트OFF): anchor=head 동시 이동 (커서만, 음영 없음)
    // BLK + mLock OFF: anchor=baseCh 고정, head만 이동 (음영 생성)
    // BLK + mLock ON: _logicalCol 공유 — 모든 range가 동일 논리 컬럼 유지
    //   실제 head = clamp(_logicalCol, lineLen)
    //   짧은 라인은 lineEnd 고정, 긴 라인도 _logicalCol 기준 동기화
    function moveLR(dir) {
        const doc = _doc(); if (!doc) return;
        const d = dir === 'left' ? -1 : 1;
        const isCur   = BS().isCursorMode();
        const isMLock = BS().isMLock();

        // BLK/CUR + mLock: _logicalCol 기반 동기 이동
        if (isMLock && _logicalCol !== null) {
            _logicalCol = Math.max(0, _logicalCol + d);
            const ranges = BS().getRanges();
            const specs = ranges.map(r => {
                const line      = doc.lineAt(r.head).number - 1;
                const lineFrom  = _lineFrom(line);
                const curAnchor = r.anchor - lineFrom;
                const newHead   = _clamp(_logicalCol, line);
                if (isCur) {
                    // CUR+mLock: anchor도 함께 이동 (영역 유지)
                    const newAnchor = _clamp(curAnchor + d, line);
                    return { anchor: lineFrom + newAnchor, head: lineFrom + newHead };
                } else {
                    // BLK+mLock: anchor 고정, head만 logicalCol로
                    return { anchor: lineFrom + curAnchor, head: lineFrom + newHead };
                }
            });
            const curMain = BS().getMainIdx();
            BS().dispatch(specs, curMain);
            _syncBasesFromView(curMain);
            BS().render();
            return;
        }

        const specs = BS().getRanges().map(r => {
            const line      = doc.lineAt(r.head).number - 1;
            const lineFrom  = _lineFrom(line);
            const curHead   = r.head - lineFrom;
            const curAnchor = r.anchor - lineFrom;
            const newHead   = _clamp(curHead + d, line);

            if (isCur) {
                // CUR: anchor=head 동시이동
                return { anchor: lineFrom + newHead, head: lineFrom + newHead };
            } else {
                // BLK mLock OFF: anchor 고정, head만 이동
                return { anchor: lineFrom + curAnchor, head: lineFrom + newHead };
            }
        });
        const curMain = BS().getMainIdx();
        BS().dispatch(specs, curMain);
        _syncBasesFromView(curMain);
        BS().render();
    }

    // CHECK OFF + mLock OFF:
    // anchor = 기준점(고정), head = 이동 방향
    // head > anchor(아래 방향): down=추가, up=제거
    // head < anchor(위 방향):  up=추가,   down=제거
    // head = anchor(단일):     방향키로 단순 이동
    function moveUD(dir) {
        const doc = _doc(); if (!doc) return;
        const ranges  = BS().getRanges();
        const baseCh  = BS().getBaseCh();
        if (!ranges.length) return;

        // 진입 시 기준 라인으로 방향 판단 (ranges 변경에 영향 없음)
        const baseLine   = BS().getBaseLine();
        const headLines  = ranges.map(r => doc.lineAt(r.head).number - 1);
        const topLine    = Math.min(...headLines);
        const botLine    = Math.max(...headLines);



        const isCur = BS().isCursorMode();

        // CUR: 단일/다중 모두 — 전체 커서 anchor=head 동시 이동 (추가/제거 없음)
        if (isCur) {
            const d = dir === 'down' ? 1 : -1;
            const mainIdx = BS().getMainIdx();
            const specs = ranges.map(r => {
                const curLine = doc.lineAt(r.head).number - 1;
                const newLine = Math.max(0, Math.min(doc.lines - 1, curLine + d));
                const newPos  = _lineFrom(newLine) + _clamp(r.head - _lineFrom(curLine), newLine);
                return { anchor: newPos, head: newPos };
            });
            BS().dispatch(specs, mainIdx);
            _syncBasesFromView(mainIdx);
            BS().render();
            return;
        }

        // BLK: 단일 range — 방향에 따라 추가
        if (ranges.length === 1) {
            const curLine = headLines[0];
            const baseHdCh = BS().getBaseHdCh();
            if (dir === 'down') {
                const newLine = Math.min(doc.lines - 1, curLine + 1);
                if (newLine === curLine) return;
                const newAnchor = _lineFrom(newLine) + _clamp(baseCh,   newLine);
                const newHead   = _lineFrom(newLine) + _clamp(baseHdCh, newLine);
                BS().dispatch([
                    { anchor: ranges[0].anchor, head: ranges[0].head },
                    { anchor: newAnchor, head: newHead },
                ], 1);
            } else {
                const newLine = Math.max(0, curLine - 1);
                if (newLine === curLine) return;
                const newAnchor = _lineFrom(newLine) + _clamp(baseCh,   newLine);
                const newHead   = _lineFrom(newLine) + _clamp(baseHdCh, newLine);
                BS().dispatch([
                    { anchor: newAnchor, head: newHead },
                    { anchor: ranges[0].anchor, head: ranges[0].head },
                ], 0);
            }
            BS().render();
            return;
        }

        // BLK 다중 range: _mainIdx 위치 기준 방향 판단
        // mainLine == topLine (HOME 점등): ▼=탑제거, ▲=위추가
        // mainLine == botLine (END  점등): ▼=아래추가, ▲=바텀제거
        // mainLine == 중간: baseLine 기준 fallback
        const mainLine = headLines[Math.min(BS().getMainIdx(), headLines.length - 1)];
        const mainAtTop = mainLine === topLine;
        const mainAtBot = mainLine === botLine;

        // baseLine 기준 fallback (중간 range가 mainIdx인 경우)
        const headGoingDown = botLine > baseLine;
        const headGoingUp   = topLine < baseLine;
        const headAtBase    = !headGoingDown && !headGoingUp;

        if (dir === 'down') {
            if (mainAtTop) {
                // 탑에서 ▼ → 탑 제거 (범위 줄어듦), mainIdx는 제거 후 새 탑
                const specs = ranges.slice(1).map(r => ({ anchor: r.anchor, head: r.head }));
                if (!specs.length) return;
                BS().dispatch(specs, 0);
            } else if (mainAtBot || headGoingDown || headAtBase) {
                // 바텀에서 ▼ → 아래에 추가 (범위 늘어남)
                const newLine = Math.min(doc.lines - 1, botLine + 1);
                if (newLine === botLine) return;
                const baseHdCh  = BS().getBaseHdCh();
                const newAnchor = _lineFrom(newLine) + _clamp(baseCh,   newLine);
                const newHead   = _lineFrom(newLine) + _clamp(baseHdCh, newLine);
                const newSpecs  = [
                    ...ranges.map(r => ({ anchor: r.anchor, head: r.head })),
                    { anchor: newAnchor, head: newHead },
                ];
                BS().dispatch(newSpecs, newSpecs.length - 1);
            }
        } else {
            if (mainAtBot) {
                // 바텀에서 ▲ → 바텀 제거 (범위 줄어듦), mainIdx는 제거 후 새 바텀
                const specs = ranges.slice(0, -1).map(r => ({ anchor: r.anchor, head: r.head }));
                if (!specs.length) return;
                BS().dispatch(specs, specs.length - 1);
            } else if (mainAtTop || headGoingUp || headAtBase) {
                // 탑에서 ▲ → 위에 추가 (범위 늘어남)
                const newLine = Math.max(0, topLine - 1);
                if (newLine === topLine) return;
                const baseHdCh  = BS().getBaseHdCh();
                const newAnchor = _lineFrom(newLine) + _clamp(baseCh,   newLine);
                const newHead   = _lineFrom(newLine) + _clamp(baseHdCh, newLine);
                BS().dispatch([
                    { anchor: newAnchor, head: newHead },
                    ...ranges.map(r => ({ anchor: r.anchor, head: r.head })),
                ], 0);
            }
        }
        BS().render();
    }

    // mLock ON: 전체 ranges anchor+head 동시 이동
    function shiftAllLR(dir) {
        const doc = _doc(); if (!doc) return;
        const d = dir === 'left' ? -1 : 1;
        const curMain = BS().getMainIdx();
        // _logicalCol 갱신 (moveLR와 일관성 유지)
        if (_logicalCol !== null) _logicalCol = Math.max(0, _logicalCol + d);
        const specs = BS().getRanges().map(r => {
            const hLine = doc.lineAt(r.head).number - 1;
            const aLine = doc.lineAt(r.anchor).number - 1;
            return {
                head:   _lineFrom(hLine) + _clamp(r.head   - _lineFrom(hLine)   + d, hLine),
                anchor: _lineFrom(aLine) + _clamp(r.anchor - _lineFrom(aLine)   + d, aLine),
            };
        });
        BS().dispatch(specs, curMain);
        _syncBasesFromView(curMain);
        BS().render();
    }

    // mLock CUR 상하: 롤링(rolling) 방식
    //   ▲: 맨 위에 새 range 추가 + 맨 아래 제거 → 전체가 위로 굴러감
    //   ▼: 맨 아래에 새 range 추가 + 맨 위 제거 → 전체가 아래로 굴러감
    //   중간 ranges 그대로, 블록 크기/모양 보존
    function shiftAllUD(dir) {
        const doc = _doc(); if (!doc) return;
        const ranges = BS().getRanges();
        if (!ranges.length) return;

        // ranges는 CM6가 topmost-first로 정렬 보장
        const topR = ranges[0];
        const botR = ranges[ranges.length - 1];
        const topLine = doc.lineAt(topR.head).number - 1;
        const botLine = doc.lineAt(botR.head).number - 1;

        let specs;
        let newMain;

        // 복제 기준: 전체 ranges 중 anchor col 최솟값, head col 최댓값
        // — 빈 라인 통과로 clamp 수렴되어도 원래 최대 크기 유지
        const refACh = Math.min(...ranges.map(r => r.anchor - _lineFrom(doc.lineAt(r.anchor).number - 1)));
        const refHCh = Math.max(...ranges.map(r => r.head   - _lineFrom(doc.lineAt(r.head).number   - 1)));

        if (dir === 'up') {
            if (topLine <= 0) return;
            const newLine   = topLine - 1;
            const newAnchor = _lineFrom(newLine) + _clamp(refACh, newLine);
            const newHead   = _lineFrom(newLine) + _clamp(refHCh, newLine);
            specs = [
                { anchor: newAnchor, head: newHead },
                ...ranges.slice(0, -1).map(r => ({ anchor: r.anchor, head: r.head })),
            ];
            newMain = 0;
        } else {
            if (botLine >= doc.lines - 1) return;
            const newLine   = botLine + 1;
            const newAnchor = _lineFrom(newLine) + _clamp(refACh, newLine);
            const newHead   = _lineFrom(newLine) + _clamp(refHCh, newLine);
            specs = [
                ...ranges.slice(1).map(r => ({ anchor: r.anchor, head: r.head })),
                { anchor: newAnchor, head: newHead },
            ];
            newMain = specs.length - 1;
        }

        BS().dispatch(specs, newMain);
        _syncBasesFromView(newMain);
        BS().render();
    }

    // CHECK ON + 상하: mainIdx 이동 (범위 내 왕복) or ghost 이동 or BLK 확장
    function checkUD(dir) {
        const doc = _doc(); if (!doc) return;
        const ranges  = BS().getRanges();
        const mainIdx = BS().getMainIdx();
        const lines   = BS().getEffectiveLines();
        if (!lines.length) return;

        const ptrLine = BS().getPtrLine() ?? lines[0];
        const minLine = lines[0];
        const maxLine = lines[lines.length - 1];
        const isCur   = BS().isCursorMode();

        // ── ghost 기준점: ghost 있으면 ghost, 없으면 범위 끝 ──
        const ghostBase = _ghostLine;

        // 현재 포인터 라인: ghost 있으면 ghost, 없으면 ptrLine
        const curLine = ghostBase !== null ? ghostBase : ptrLine;
        const lineSet = new Set(lines); // range에 있는 라인들

        if (dir === 'up') {
            const newLine = Math.max(0, curLine - 1);

            if (newLine < minLine) {
                // ── 범위 위로 벗어남 ──────────────────────────
                if (isCur) {
                    // CUR: ghost 위로 이동
                    _ghostLine = newLine;
                    _renderWithGhost();
                } else {
                    // BLK: ghost 기준 위로 확장 확정
                    const targetLine = ghostBase !== null ? ghostBase - 1 : minLine - 1;
                    const tLine = Math.max(0, targetLine);
                    const templateRange = ranges[0];
                    const colCh = templateRange.head - _lineFrom(doc.lineAt(templateRange.head).number - 1);
                    const newOffset = _lineFrom(tLine) + _clamp(colCh, tLine);
                    const newSpecs = [{ anchor: newOffset, head: newOffset },
                        ...ranges.map(r => ({ anchor: r.anchor, head: r.head }))];
                    _clearGhost();
                    BS().dispatch(newSpecs, 0);
                    BS().render();
                }
            } else {
                // ── 범위 안 (minLine~maxLine) ──────────────────
                if (lineSet.has(newLine)) {
                    // 등록된 라인 → mainIdx 업데이트
                    _clearGhost();
                    const newIdx = lines.indexOf(newLine);
                    BS().dispatch(ranges.map(r => ({ anchor: r.anchor, head: r.head })), newIdx);
                    BS().render();
                } else {
                    if (isCur) {
                        // CUR: 제외 라인 건너뜀 — 다음 등록 라인으로
                        let skip = newLine - 1;
                        while (skip >= minLine && !lineSet.has(skip)) skip--;
                        if (skip >= minLine) {
                            _clearGhost();
                            BS().dispatch(ranges.map(r => ({ anchor: r.anchor, head: r.head })), lines.indexOf(skip));
                            BS().render();
                        }
                    } else {
                        // BLK: 제외 라인 ghost 표시 (TAB으로 재등록)
                        _ghostLine = newLine;
                        _renderWithGhost();
                    }
                }
            }
        } else {
            const newLine = Math.min(doc.lines - 1, curLine + 1);

            if (newLine > maxLine) {
                // ── 범위 아래로 벗어남 ───────────────────────
                if (isCur) {
                    // CUR: ghost 아래로 이동
                    _ghostLine = newLine;
                    _renderWithGhost();
                } else {
                    // BLK: ghost 기준 아래로 확장 확정
                    const targetLine = ghostBase !== null ? ghostBase + 1 : maxLine + 1;
                    const tLine = Math.min(doc.lines - 1, targetLine);
                    const templateRange = ranges[ranges.length - 1];
                    const colCh = templateRange.head - _lineFrom(doc.lineAt(templateRange.head).number - 1);
                    const newOffset = _lineFrom(tLine) + _clamp(colCh, tLine);
                    const newSpecs = [...ranges.map(r => ({ anchor: r.anchor, head: r.head })),
                        { anchor: newOffset, head: newOffset }];
                    _clearGhost();
                    BS().dispatch(newSpecs, newSpecs.length - 1);
                    BS().render();
                }
            } else {
                // ── 범위 안 (minLine~maxLine) ──────────────────
                if (lineSet.has(newLine)) {
                    // 등록된 라인 → mainIdx 업데이트
                    _clearGhost();
                    const newIdx = lines.indexOf(newLine);
                    BS().dispatch(ranges.map(r => ({ anchor: r.anchor, head: r.head })), newIdx);
                    BS().render();
                } else {
                    if (isCur) {
                        // CUR: 제외 라인 건너뜀 — 다음 등록 라인으로
                        let skip = newLine + 1;
                        while (skip <= maxLine && !lineSet.has(skip)) skip++;
                        if (skip <= maxLine) {
                            _clearGhost();
                            BS().dispatch(ranges.map(r => ({ anchor: r.anchor, head: r.head })), lines.indexOf(skip));
                            BS().render();
                        }
                    } else {
                        // BLK: 제외 라인 ghost 표시 (TAB으로 재등록)
                        _ghostLine = newLine;
                        _renderWithGhost();
                    }
                }
            }
        }
    }

    // CHECK ON + 좌우: mainIdx range만 이동
    function checkLR(dir) {
        const doc = _doc(); if (!doc) return;
        const ranges  = BS().getRanges();
        const mainIdx = BS().getMainIdx();
        const ptr     = ranges[Math.min(mainIdx, ranges.length - 1)];
        if (!ptr) return;

        const line    = doc.lineAt(ptr.head).number - 1;
        const lineFrom = _lineFrom(line);
        const d = dir === 'left' ? -1 : 1;
        const curDelta = ptr.head   - lineFrom;
        const curGamma = ptr.anchor - lineFrom;
        const newDelta = _clamp(curDelta + d, line);

        let newGamma;
        if (BS().isMLock() && BS().isCursorMode()) {
            newGamma = _clamp(curGamma + d, line); // mLock+CUR: 영역 유지하며 이동
        } else if (BS().isCursorMode()) {
            newGamma = newDelta; // CUR: 음영 없음
        } else {
            newGamma = curGamma; // BLK (mLock ON/OFF 무관): anchor 고정, delta만 이동
        }

        const specs = ranges.map((r, i) =>
            i === mainIdx
                ? { anchor: lineFrom + newGamma, head: lineFrom + newDelta }
                : { anchor: r.anchor, head: r.head }
        );
        BS().dispatch(specs, mainIdx);
        BS().render();
    }

    // ── 편집 ─────────────────────────────────────────────

    // CHECK ON: mainIdx range만 편집
    function checkEdit(action, text) {
        const v = _v(); if (!v) return;
        const doc     = v.state.doc;
        const ranges  = BS().getRanges();
        const mainIdx = BS().getMainIdx();
        const ptr     = ranges[Math.min(mainIdx, ranges.length - 1)];
        if (!ptr) return;

        const lineObj = doc.lineAt(ptr.head);
        const delta   = ptr.head   - lineObj.from;
        const gamma   = ptr.anchor - lineObj.from;
        const pos     = lineObj.from + delta;
        const hasSel  = delta !== gamma;
        const headLeft  = delta < gamma;
        const headRight = gamma < delta;

        let change = null;
        let nextSpec = { anchor: ptr.anchor, head: ptr.head };

        if (hasSel) {
            if (action === 'delBefore') {
                if (headLeft) {
                    if (pos <= lineObj.from) return;
                    change = { from: pos - 1, to: pos, insert: '' };
                    nextSpec = { anchor: ptr.anchor - 1, head: ptr.head - 1 };
                } else {
                    const from = lineObj.from + Math.min(delta, gamma);
                    change = { from, to: lineObj.from + Math.max(delta, gamma), insert: '' };
                    nextSpec = { anchor: from, head: from };
                }
            } else if (action === 'delAfter') {
                if (headRight) {
                    if (pos < lineObj.to) {
                        change = { from: pos, to: pos + 1, insert: '' };
                        nextSpec = { anchor: ptr.anchor, head: ptr.head };
                    } else if (lineObj.number < doc.lines) {
                        change = { from: pos, to: pos + 1, insert: '' };
                        nextSpec = { anchor: ptr.anchor, head: ptr.head };
                    } else return;
                } else {
                    const from = lineObj.from + Math.min(delta, gamma);
                    change = { from, to: lineObj.from + Math.max(delta, gamma), insert: '' };
                    nextSpec = { anchor: from, head: from };
                }
            } else {
                const from = lineObj.from + Math.min(delta, gamma);
                change = { from, to: lineObj.from + Math.max(delta, gamma), insert: text };
                const np = from + text.length;
                nextSpec = { anchor: np, head: np };
            }
        } else {
            if (action === 'delBefore') {
                if (pos <= lineObj.from) return;
                change = { from: pos - 1, to: pos, insert: '' };
                nextSpec = { anchor: pos - 1, head: pos - 1 };
            } else if (action === 'delAfter') {
                if (pos < lineObj.to) {
                    change = { from: pos, to: pos + 1, insert: '' };
                    nextSpec = { anchor: pos, head: pos };
                } else if (lineObj.number < doc.lines) {
                    change = { from: pos, to: pos + 1, insert: '' };
                    nextSpec = { anchor: pos, head: pos };
                } else return;
            } else if (action === 'insert') {
                change = { from: pos, to: pos, insert: text };
                const np = pos + text.length;
                nextSpec = { anchor: np, head: np };
            }
        }

        if (!change) return;
        const changeSet = v.state.changes(change);
        v.dispatch({ changes: change, userEvent: action === 'insert' ? 'input' : 'delete' });
        const post = ranges.map((r, i) =>
            i === mainIdx
                ? { anchor: nextSpec.anchor, head: nextSpec.head }
                : { anchor: changeSet.mapPos(r.anchor, -1), head: changeSet.mapPos(r.head, -1) }
        );
        _applySelectionToView(post, mainIdx);
    }

    // input 이벤트 후 0번 제외 나머지 ranges 처리
    // 0번은 CM6가 이미 삽입 완료 → 1번~에만 적용
    function _applyToRestRanges(action, text) {
        const v = _v(); if (!v) return;
        const doc    = v.state.doc;
        const ranges = BS().getRanges();
        if (ranges.length <= 1) return; // 단일 커서면 불필요

        // 0번 range의 현재 head 위치 파악 (CM6가 삽입 후 이동된 위치)
        const mainHead = v.state.selection.main.head;
        const mainLine = doc.lineAt(mainHead).number - 1;

        // 1번~ ranges에 동일 변경 적용 (아래→위 순서, offset 충돌 방지)
        const restRanges = ranges.slice(1);
        const changes = [];

        for (const r of [...restRanges].reverse()) {
            const line    = doc.lineAt(r.head).number - 1;
            const lineObj = doc.line(line + 1);
            const delta   = r.head   - lineObj.from;
            const gamma   = r.anchor - lineObj.from;
            const pos     = lineObj.from + delta;

            if (delta !== gamma) {
                const from = lineObj.from + Math.min(delta, gamma);
                const to   = lineObj.from + Math.max(delta, gamma);
                if (action === 'insert') changes.push({ from, to, insert: text });
                else changes.push({ from, to, insert: '' });
            } else {
                if (action === 'delBefore' && pos > lineObj.from) {
                    changes.push({ from: pos - 1, to: pos, insert: '' });
                } else if (action === 'delAfter' && pos < lineObj.to) {
                    changes.push({ from: pos, to: pos + 1, insert: '' });
                } else if (action === 'insert') {
                    changes.push({ from: pos, to: pos, insert: text });
                }
            }
        }
        if (!changes.length) return;
        v.dispatch({ changes, userEvent: 'input' });
        BS().render();
    }

    // CHECK OFF: 전체 ranges 동시 편집
    function editAll(action, text) {
        const v = _v(); if (!v) return;
        const doc    = v.state.doc;
        const ranges = BS().getRanges();
        const changes = [];
        const nextSpecs = new Array(ranges.length);

        // _needsMap:
        //   true  — nextSpec이 변경 전 offset (del 커서유지) → mapPos 필요
        //   false — nextSpec이 이미 변경 후 정확한 offset (insert/수렴) → mapPos 불필요
        const _needsMap = new Array(ranges.length).fill(false);

        const sorted = [...ranges].map((r, i) => ({ r, i }))
            .sort((a, b) => b.r.head - a.r.head);

        for (const { r, i } of sorted) {
            const lineObj = doc.lineAt(r.head);
            const delta   = r.head   - lineObj.from;
            const gamma   = r.anchor - lineObj.from;
            const pos     = lineObj.from + delta;
            const hasSel  = delta !== gamma;
            const headLeft  = delta < gamma; // head가 왼쪽 (역방향 음영)
            const headRight = gamma < delta; // head가 오른쪽 (정방향 음영)
            let nextSpec = { anchor: r.anchor, head: r.head };

            if (hasSel) {
                if (action === 'delBefore') {
                    if (headLeft) {
                        // 역방향: 커서(head) 왼쪽 1글자 삭제, 음영 유지
                        if (pos > lineObj.from) {
                            changes.push({ from: pos - 1, to: pos, insert: '' });
                            _needsMap[i] = true; // 원본 offset → mapPos 필요
                        }
                    } else {
                        // 정방향: 음영 전체 삭제 → cursor 수렴
                        const from = lineObj.from + Math.min(delta, gamma);
                        changes.push({ from, to: lineObj.from + Math.max(delta, gamma), insert: '' });
                        nextSpec = { anchor: from, head: from }; // 변경 후 정확한 위치
                        _needsMap[i] = true; // from도 변경 전 offset → mapPos 필요
                    }
                } else if (action === 'delAfter') {
                    if (headRight) {
                        // 정방향: 커서(head) 오른쪽 1글자 삭제, 음영 유지
                        if (pos < lineObj.to) {
                            changes.push({ from: pos, to: pos + 1, insert: '' });
                            _needsMap[i] = true;
                        }
                    } else {
                        // 역방향: 음영 전체 삭제 → cursor 수렴
                        const from = lineObj.from + Math.min(delta, gamma);
                        changes.push({ from, to: lineObj.from + Math.max(delta, gamma), insert: '' });
                        nextSpec = { anchor: from, head: from };
                        _needsMap[i] = true;
                    }
                } else if (action === 'insert') {
                    // 음영 삭제 + 삽입: from은 변경 전 offset이지만
                    // 이 range 자신의 change(from~to 삭제+삽입)만 반영하면 됨
                    // 다른 range의 change는 sorted 역순이라 이 range보다 높은 offset
                    // → 이 range의 from에 영향 없음 → mapPos 불필요
                    const from = lineObj.from + Math.min(delta, gamma);
                    changes.push({ from, to: lineObj.from + Math.max(delta, gamma), insert: text });
                    nextSpec = { anchor: from + text.length, head: from + text.length };
                    // _needsMap[i] = false (기본값 유지)
                }
            } else {
                if (action === 'delBefore' && pos > lineObj.from) {
                    changes.push({ from: pos - 1, to: pos, insert: '' });
                    _needsMap[i] = true;
                } else if (action === 'delAfter' && pos < lineObj.to) {
                    changes.push({ from: pos, to: pos + 1, insert: '' });
                    _needsMap[i] = true;
                } else if (action === 'insert') {
                    changes.push({ from: pos, to: pos, insert: text });
                    nextSpec = { anchor: pos + text.length, head: pos + text.length };
                    // _needsMap[i] = false (기본값 유지)
                }
            }
            nextSpecs[i] = nextSpec;
        }
        if (!changes.length) return;

        const changeSet = v.state.changes(changes);
        const mappedSpecs = nextSpecs.map((s, i) =>
            _needsMap[i]
                ? { anchor: changeSet.mapPos(s.anchor, -1), head: changeSet.mapPos(s.head, -1) }
                : s
        );

        v.dispatch({ changes, userEvent: action === 'insert' ? 'input' : 'delete' });

        _applySelectionToView(mappedSpecs, 0);
        window.UI?.updateStats?.();
    }

    // ── HOME/END ──────────────────────────────────────────
    // anchor/head 직접 비교 (mainIdx 강제 0 제약 없음)
    //
    // HOME:
    //   하나라도 head > anchor → 전체 스왑(anchor↔head) → return
    //   전체 head ≤ anchor    → softH/0 토글
    //
    // HOME: mainIdx=탑이면 END로 점프, 아니면 각 라인 softHome/col0 정렬
    // END:  mainIdx=바텀이면 HOME으로 점프, 아니면 각 라인 softEnd/lineEnd 정렬
    // anchor/head 방향 무관 — 스왑 없이 무조건 head를 목표 col로 이동
    function homeEnd(type, opts) {
        _pushV2Snapshot(); // undo 대상
        const doc = _doc(); if (!doc) return;
        const ranges  = BS().getRanges();
        const mainIdx = BS().getMainIdx();
        if (!ranges.length) return;

        // ── CHECK 모드: mainIdx 단건만 처리 ──────────────────
        if (opts?.checkOnly) {
            const r = ranges[mainIdx];
            if (!r) return;
            function _softH(txt) { let i=0; while(i<txt.length&&(txt[i]===' '||txt[i]==='\t'))i++; return i; }
            function _softE(txt) { let i=txt.length; while(i>0&&(txt[i-1]===' '||txt[i-1]==='\t'))i--; return i; }
            const hLo = doc.lineAt(r.head);
            const txt = doc.sliceString(hLo.from, hLo.to);
            const col = r.head - hLo.from;

            let newAnchor = r.anchor, newHead;

            if (type === 'home') {
                if (r.head > r.anchor) {
                    // 1단계: 스왑
                    newAnchor = r.head; newHead = r.anchor;
                } else {
                    // 2~3단계: softHome → col0
                    const soft = _softH(txt);
                    newHead = hLo.from + (col === soft ? 0 : soft);
                }
            } else {
                if (r.head < r.anchor) {
                    // 1단계: 스왑
                    newAnchor = r.head; newHead = r.anchor;
                } else {
                    // 2~3단계: softEnd → lineEnd
                    const soft = _softE(txt);
                    newHead = hLo.from + (col === soft ? txt.length : soft);
                }
            }

            const specs = ranges.map((rr, i) =>
                i === mainIdx ? { anchor: newAnchor, head: newHead } : { anchor: rr.anchor, head: rr.head }
            );
            BS().dispatch(specs, mainIdx);
            BS().render();
            return;
        }

        // ── 다중 range: _mainIdx 위치 기준 투핸들 스왑 ──────
        // HOME: mainIdx가 바텀 → 탑으로 점프
        // END:  mainIdx가 탑  → 바텀으로 점프
        // CUR: 핸들 불필요 — 스왑 스킵, 바로 soft 정렬로 fall-through
        if (ranges.length > 1 && !BS().isCursorMode()) {
            const headLines = ranges.map(r => doc.lineAt(r.head).number - 1);
            const topLine   = Math.min(...headLines);
            const botLine   = Math.max(...headLines);
            const topIdx    = headLines.indexOf(topLine);
            const botIdx    = headLines.lastIndexOf(botLine);
            const mainLine  = headLines[Math.min(mainIdx, headLines.length - 1)];

            if (type === 'home' && mainLine === botLine) {
                // 바텀→탑 스왑: head가 왼쪽이어야 ▲로 범위 조작 가능
                // head > anchor → anchor↔head 교환 (범위 유지, head 왼쪽으로)
                // head <= anchor → 이미 왼쪽, 그대로
                const specs = ranges.map(r => r.head > r.anchor
                    ? { anchor: r.head, head: r.anchor }
                    : { anchor: r.anchor, head: r.head }
                );
                BS().dispatch(specs, topIdx);
                _syncBasesFromView(topIdx);
                const topHead = specs[topIdx].head;
                _v()?.dispatch({ effects: CM6.EditorView.scrollIntoView(topHead, { y: 'center' }) });
                BS().render();
                return;
            }
            if (type === 'end' && mainLine === topLine) {
                // 탑→바텀 스왑: head가 오른쪽이어야 ▼로 범위 조작 가능
                // head < anchor → anchor↔head 교환 (범위 유지, head 오른쪽으로)
                // head >= anchor → 이미 오른쪽, 그대로
                const specs = ranges.map(r => r.head < r.anchor
                    ? { anchor: r.head, head: r.anchor }
                    : { anchor: r.anchor, head: r.head }
                );
                BS().dispatch(specs, botIdx);
                _syncBasesFromView(botIdx);
                const botHead = specs[botIdx].head;
                _v()?.dispatch({ effects: CM6.EditorView.scrollIntoView(botHead, { y: 'center' }) });
                BS().render();
                return;
            }
            // 그 외: col 이동 (아래 공통 처리로 fall-through)
            // anchor < head (HOME 방향 반대) 여도 스왑 없이 softHome 정렬로 직행
        }

        // ── 상태 정렬 순서 (단계별 구분 동작) ──────────────
        //
        // HOME:
        //   1단계: head > anchor 인 range 있으면 → 해당 range만 anchor↔head 교환 (방향 정렬)
        //   2단계: 전체 head <= anchor → softHome 불일치 있으면 → softHome 정렬
        //   3단계: 전체 softHome → col0
        //
        // END:
        //   1단계: head < anchor 인 range 있으면 → 해당 range만 anchor↔head 교환
        //   2단계: 전체 head >= anchor → softEnd 불일치 있으면 → softEnd 정렬
        //   3단계: 전체 softEnd → lineEnd

        function _softH(txt) {
            let i = 0;
            while (i < txt.length && (txt[i] === ' ' || txt[i] === '\t')) i++;
            return i;
        }
        function _softE(txt) {
            let i = txt.length;
            while (i > 0 && (txt[i-1] === ' ' || txt[i-1] === '\t')) i--;
            return i;
        }

        const isCur = BS().isCursorMode();

        if (type === 'home') {
            // CUR: 1단계(방향정렬) 스킵 — head 기준으로만 이동, anchor=head (음영 없음)
            if (!isCur) {
                // 1단계: head > anchor 인 range 있으면 → 방향 정렬 (anchor↔head 교환)
                const hasWrongDir = ranges.some(r => r.head > r.anchor);
                if (hasWrongDir) {
                    const specs = ranges.map(r => r.head > r.anchor
                        ? { anchor: r.head, head: r.anchor }
                        : { anchor: r.anchor, head: r.head }
                    );
                    BS().dispatch(specs, mainIdx);
                    BS().render();
                    return;
                }
            }
            // 2단계: softHome 불일치 있으면 → softHome 정렬
            const rangeInfos = ranges.map(r => {
                const hLo = doc.lineAt(r.head);
                const txt = doc.sliceString(hLo.from, hLo.to);
                return { r, hLo, txt, col: r.head - hLo.from };
            });
            const allAtSoft = rangeInfos.every(({ txt, col }) => col === _softH(txt));
            // 3단계: 전체 softHome → col0
            const goTo = allAtSoft ? 'hard' : 'soft';
            const specs = rangeInfos.map(({ r, hLo, txt }) => {
                const newHead = hLo.from + (goTo === 'soft' ? _softH(txt) : 0);
                return { anchor: isCur ? newHead : r.anchor, head: newHead };
            });
            BS().dispatch(specs, mainIdx);
            BS().render();
        } else {
            // CUR: 1단계(방향정렬) 스킵
            if (!isCur) {
                // 1단계: head < anchor 인 range 있으면 → 방향 정렬 (anchor↔head 교환)
                const hasWrongDir = ranges.some(r => r.head < r.anchor);
                if (hasWrongDir) {
                    const specs = ranges.map(r => r.head < r.anchor
                        ? { anchor: r.head, head: r.anchor }
                        : { anchor: r.anchor, head: r.head }
                    );
                    BS().dispatch(specs, mainIdx);
                    BS().render();
                    return;
                }
            }
            // 2단계: softEnd 불일치 있으면 → softEnd 정렬
            const rangeInfos = ranges.map(r => {
                const hLo = doc.lineAt(r.head);
                const txt = doc.sliceString(hLo.from, hLo.to);
                return { r, hLo, txt, col: r.head - hLo.from };
            });
            const allAtSoft = rangeInfos.every(({ txt, col }) => col === _softE(txt));
            // 3단계: 전체 softEnd → lineEnd
            const goTo = allAtSoft ? 'hard' : 'soft';
            const specs = rangeInfos.map(({ r, hLo, txt }) => {
                const newHead = hLo.from + (goTo === 'soft' ? _softE(txt) : txt.length);
                return { anchor: isCur ? newHead : r.anchor, head: newHead };
            });
            BS().dispatch(specs, mainIdx);
            BS().render();
        }
    }
    // ── TAB: ghost 확정 or 현재 pointer range 제외 토글 ──
    function checkTabToggle(opts) {
        const doc = _doc(); if (!doc) return;
        const ranges = BS().getRanges();
        const mainIdx = BS().getMainIdx();

        // ghost 있으면 → ghost 라인 확정 추가 (건너뛴 라인 포함)
        if (_ghostLine !== null) {
            const gLine = _ghostLine;
            // forcedOffset 있으면 클릭 위치를 그대로 사용, 없으면 mainIdx 컬럼 복제
            let newOffset;
            if (opts && typeof opts.forcedOffset === 'number') {
                newOffset = opts.forcedOffset;
            } else {
                const templateRange = ranges[mainIdx] ?? ranges[ranges.length - 1];
                const colCh = templateRange
                    ? templateRange.head - _lineFrom(doc.lineAt(templateRange.head).number - 1)
                    : 0;
                newOffset = _lineFrom(gLine) + _clamp(colCh, gLine);
            }
            // ghost가 범위 아래면 끝에 추가, 위면 앞에 추가
            const minLine = BS().getEffectiveLines()[0] ?? 0;
            let newSpecs, newMain;
            if (gLine >= (BS().getEffectiveLines().slice(-1)[0] ?? 0)) {
                newSpecs = [...ranges.map(r => ({ anchor: r.anchor, head: r.head })),
                    { anchor: newOffset, head: newOffset }];
                newMain = newSpecs.length - 1;
            } else {
                newSpecs = [{ anchor: newOffset, head: newOffset },
                    ...ranges.map(r => ({ anchor: r.anchor, head: r.head }))];
                newMain = 0;
            }
            _clearGhost();
            BS().dispatch(newSpecs, newMain, false);
            // CM6 재정렬 후 실제 ghost 라인 인덱스를 찾아 _mainIdx 보정
            {
                const reordered = BS().getRanges();
                const ghostIdx = reordered.findIndex(r => r.head === newOffset);
                if (ghostIdx >= 0) BS().setMainIdx(ghostIdx);
            }
            BS().render();
            return;
        }

        // ghost 없으면 → 기존: 현재 mainIdx range 제외 토글
        if (ranges.length <= 1) return; // 마지막 하나는 제거 불가
        const newSpecs = ranges
            .filter((_, i) => i !== mainIdx)
            .map(r => ({ anchor: r.anchor, head: r.head }));
        const newMain = Math.min(mainIdx, newSpecs.length - 1);
        BS().dispatch(newSpecs, newMain);
        BS().render();
    }

    // ── 클립보드 ─────────────────────────────────────────
    function copyAll() {
        const v = _v(); if (!v) return '';
        const doc = v.state.doc;
        const seenLines = new Set();
        const lines = [];
        for (const r of BS().getRanges()) {
            const from = Math.min(r.anchor, r.head);
            const to   = Math.max(r.anchor, r.head);
            if (from === to) continue;                      // 빈 range 제외
            const lineNo = doc.lineAt(r.head).number;
            if (seenLines.has(lineNo)) continue;            // 같은 라인 중복 제외
            seenLines.add(lineNo);
            lines.push(doc.sliceString(from, to));
        }
        const text = lines.join('\n');
        if (text) {
            window.NavBlock?.setClipData?.(text);
            if (navigator.clipboard) navigator.clipboard.writeText(text).catch(() => {});
            // execCommand fallback for Samsung Browser
            try {
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
                document.body.appendChild(ta);
                ta.focus();
                ta.setSelectionRange(0, ta.value.length);
                document.execCommand('copy');
                ta.remove();
            } catch (e) {}
        }
        return text;
    }

    return {
        // M-LOCK BLK 가상 head
        mlockInit: _mlockInit,
        mlockClear: _mlockClear,
        // 방향키
        moveLR, moveUD, shiftAllLR, shiftAllUD,
        // OS 입력 후 나머지 ranges 처리
        _applyToRestRanges,
        checkUD, checkLR,
        // 편집
        checkEdit, editAll,
        // HOME/END
        homeEnd,
        // TAB
        checkTabToggle,
        // ghost 초기화
        clearGhost: _clearGhost,
        getGhost: () => _ghostLine,
        setGhost: (v) => { _ghostLine = v; },
        renderWithGhost: _renderWithGhost,
        // bases 외부 동기화 (M-LOCK OFF 등)
        _syncBasesFromMainIdx: () => _syncBasesFromView(BS().getMainIdx()),
        // 클립보드
        copyAll,
        // 스냅샷 (undo/redo)
        popV2Snapshot:  _popV2Snapshot,
        v2SnapshotCount: _v2SnapshotCount,
    };
})();

window.NavBlockV2 = NavBlockV2;
