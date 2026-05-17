/* Path: usekit/tools/editor/js2/ui/ui_stats.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 상태 표시 (라인/컬럼/Undo-Redo) + stat 버튼 (chars/lines 상세) + KU 버튼 점등
 * ─────────────────────────────────────────────────────────── */

const UIStats = (function () {
    'use strict';

    let _throttleTimer = null;

    function updateStats() {
        if (_throttleTimer) return;
        _throttleTimer = setTimeout(() => {
            _throttleTimer = null;
            _render();
        }, 32); // ~30fps
    }

    function updateStatsNow() { _render(); }

    function _render() {
        if (!Editor.isReady()) return;

        const rawPos = Editor.getCursor();
        const btn = document.getElementById('btnLineInfo');

        // V2: BlockState 활성 시 CM6 ranges에서 파생
        if (window.BlockState?.isActive?.()) {
            const ptrLine = window.BlockState.getPtrLine();
            const ptr  = ptrLine != null ? { line: ptrLine, ch: 0 } : rawPos;
            // 대표커서: mainIdx range의 head
            const ptrRange = window.BlockState.getPtrRange();
            const ptrPos   = ptrRange ? window.BlockState.toPos(ptrRange.head) : rawPos;
            const line = ptrPos.line + 1;
            const col  = ptrPos.ch   + 1;

            if (btn) {
                const bs = window.BlockState.getBS();  // 전체 ranges 중 최소 anchor
                const be = window.BlockState.getBE();  // 전체 ranges 중 최대 head
                if (bs && be) {
                    // BS = 좌측 시작점(최소 ch), BE = 우측 끝점(최대 ch)
                    // 라인 범위: ranges의 첫 라인 ~ 마지막 라인
                    const lines  = window.BlockState.getEffectiveLines();
                    const fromL  = (lines[0]   ?? 0) + 1;
                    const toL    = (lines[lines.length - 1] ?? 0) + 1;
                    // 전체 ranges에서 min ch / max ch 계산
                    const ranges = window.BlockState.getRanges();
                    const doc    = window.Editor?.get?.()?.state.doc;
                    let minCh = Infinity, maxCh = 0;
                    if (doc) {
                        for (const r of ranges) {
                            const hCh = r.head   - doc.lineAt(r.head).from;
                            const aCh = r.anchor - doc.lineAt(r.anchor).from;
                            minCh = Math.min(minCh, hCh, aCh);
                            maxCh = Math.max(maxCh, hCh, aCh);
                        }
                    }
                    if (minCh === Infinity) minCh = 0;
                    btn.textContent = `L[${line}/${col}] ${fromL}:${minCh + 1}~${toL}:${maxCh + 1}`;
                    btn.style.maxWidth = '16rem';
                } else {
                    btn.textContent = `L[${line}/${col}]`;
                    btn.style.maxWidth = '';
                }
            }
            // CHECK 라인 하이라이트
            if (window._uiIsCheckMode?.() && ptrLine != null) {
                window.Editor?.setCheckLines?.([ptrLine + 1]);
            }
            _renderStatBtn();
            _setActive('btnModeS', State.getModeS());
            _setActive('btnSelectAll', State.getModeA?.() ?? false);
            _setActive('btnModeM', State.getModeM());
            _setActive('btnFooterFocus', State.getModeF?.() ?? false);
            return;
        }

        // 기존 렌더
        // CHECK 모드 포인터 > M-LOCK/블록모드 BE > 기본 커서 순으로 대표커서 결정
        const be0 = State.getBE();
        const checkPtr = window._uiIsCheckMode?.() ? window.NavBlock?.getCheckPointer?.() : null;
        const pos  = checkPtr ? checkPtr
            : ((window._uiIsMLock?.() || window._uiIsBlockMode?.()) && be0) ? be0 : rawPos;
        const line = pos.line + 1;   // 1-based
        const col  = pos.ch   + 1;   // 1-based

        if (btn) {
            const bs = State.getBS();
            const be = State.getBE();

            // 한 점(BS===BE)이면 블록 없음으로 간주하여 L[line/col]만 표시
            const hasRange = !!(bs && be && (bs.line !== be.line || bs.ch !== be.ch));

            if (hasRange) {
                // 영역 있음: L[line/col] BS:r:c~BE:r:c
                const bsR = bs.line + 1;
                const bsC = bs.ch   + 1;
                const beR = be.line + 1;
                const beC = be.ch   + 1;
                btn.textContent = `L[${line}/${col}] ${bsR}:${bsC}~${beR}:${beC}`;
                btn.style.maxWidth = '16rem';
            } else {
                // 한 점 or 블록 없음: L[line/col]
                btn.textContent = `L[${line}/${col}]`;
                btn.style.maxWidth = '';
            }
        }

        // 블럭모드: 대표커서(checkPointer > BE) 라인 배경색 오버레이
        if (window._uiIsCheckMode?.()) {
            const ptr = window.NavBlock?.getCheckPointer?.() || State.getBE();
            if (ptr) {
                Editor.setCheckLines?.([ptr.line + 1]);
            } else {
                Editor.clearCheckLines?.();
            }
        } else {
            Editor.clearCheckLines?.();
        }

        // stat 버튼
        _renderStatBtn();

        // S 버튼 색상
        _setActive('btnModeS', State.getModeS());

        // A 버튼 점등
        _setActive('btnSelectAll', State.getModeA?.() ?? false);

        // M 버튼 색상
        _setActive('btnModeM', State.getModeM());

        // Fixed Focus 버튼 점등
        _setActive('btnFooterFocus', State.getModeF?.() ?? false);

        // H/E 점등
        _updateHEButtons();

        // CPX 버튼 색상
        _updateCPXButtons();

        // 블록 있을 때 커서 하이라이트(activeLine) 제거
        _updateActiveLine();
    }

    // ── CM6 투핸들 스틸 ──────────────────────────────────────
    // CM6 터치 드래그 등으로 범위 선택이 생기면 BS/BE로 흡수
    // S 모드 아니면 H/E 미점등 (ui_stats가 S모드 체크로 자동 처리)
    function _stealCM6Selection(view) {
        if (!view) return;
        if (window.BlockState?.isActive?.()) return; // V2 활성 시 스킵
        // moveBlockBy 진행 중 — 중간 dispatch로 인한 블럭 초기화 차단
        if (window.NavBlock?.isMoving?.()) return;
        if (window.NavBlock?.isColumnEditing?.()) return;
        // 슬롯 전환 중 — BS/BE 복원 전 setCursor dispatch로 인한 초기화 차단
        if (window.SlotManager?.isSwitchingSlot?.()) return;
        const sel = view.state.selection.main;
        if (sel.from === sel.to) {
            // 단순 커서 클릭 — S모드/Shift/BlockMode/M-LOCK/멀티커서 활성 아니면 블록 초기화
            if (!State.getModeS() && !window.UIKeypad?.isShift?.() && !window._uiIsBlockMode?.() && !window._uiIsMLock?.() && view.state.selection.ranges.length <= 1) {
                State.clearBlock();
            }
            return;
        }

        // 범위 선택: anchor=BS(고정점), head=BE(커서)
        // 블럭모드(컬럼 선택)이면 CM6 selection으로 BS/BE 덮어쓰지 않음
        // 단, 멀티모드 + 오프셋 없음이면 투핸들 드래그로 BS/BE 설정 허용
        if (window._uiIsBlockMode?.()) {
            if (window._uiGetColOffsets?.()?.size === 0) {
                // 오프셋 없음 — 투핸들 드래그 BS/BE 갱신 허용
                const anchor2 = Editor.offsetToPos(sel.anchor);
                const head2   = Editor.offsetToPos(sel.head);
                State.setBS(anchor2);
                State.setBE(head2);
            }
            return;
        }
        // S모드 또는 Shift 중일 때만 흡수 — 일반 방향키 이동 시 오염 방지
        if (!State.getModeS() && !window.UIKeypad?.isShift?.()) return;
        const anchor = Editor.offsetToPos(sel.anchor);
        const head   = Editor.offsetToPos(sel.head);
        State.setBS(anchor);
        State.setBE(head);
    }

    // ── H/E 점등 ─────────────────────────────────────────────
    // activeEnd='H' → H 점등, 'E' → E 점등, null → 둘 다 소등
    function _updateHEButtons() {
        const bs = State.getBS();
        const isShift = window.UIKeypad?.isShift?.();

        if (!bs || !Editor.isReady()) {
            _setActive('btnNavH', false);
            _setActive('btnNavE', false);
            _setActive('kbHm',   false);
            _setActive('kbEnd',  false);
            return;
        }
        const cur = Editor.getCursor();
        const curAfterBs  = (cur.line > bs.line) || (cur.line === bs.line && cur.ch > bs.ch);
        const curBeforeBs = (cur.line < bs.line) || (cur.line === bs.line && cur.ch < bs.ch);

        if (isShift) {
            // Shift 모드: kbHm/kbEnd 점등
            _setActive('btnNavH', false);
            _setActive('btnNavE', false);
            _setActive('kbHm',  curBeforeBs);
            _setActive('kbEnd', curAfterBs);
        } else {
            // S모드: btnNavH/btnNavE 점등
            _setActive('btnNavH', curBeforeBs);
            _setActive('btnNavE', curAfterBs);
            _setActive('kbHm',   false);
            _setActive('kbEnd',  false);
        }
    }

    // ── activeLine 하이라이트 제어 ────────────────────────────
    // 블록 있을 때 커서줄 하이라이트 숨김
    let _activeLineStyle = null;
    function _updateActiveLine() {
        const bs = State.getBS();
        const be = State.getBE();
        const hasBlock = bs && be && !_posEqualSimple(bs, be);
        if (!_activeLineStyle) {
            _activeLineStyle = document.createElement('style');
            _activeLineStyle.id = 'cm-activeline-override';
            document.head.appendChild(_activeLineStyle);
        }
        _activeLineStyle.textContent = hasBlock
            ? '.cm-activeLine { background: transparent !important; } .cm-activeLineGutter { background: transparent !important; }'
            : '';
    }

    // ── CPX 버튼 색상 ─────────────────────────────────────────
    // Copy/Cut: 블록 있을 때 녹색
    // Paste: 클립보드 내용 있을 때 색변경
    let _hasClip = false;  // 클립보드 유무 플래그

    function _updateCPXButtons() {
        const bs = State.getBS();
        const be = State.getBE();
        const hasBlock = bs && be && !_posEqualSimple(bs, be);

        // Copy(⧉), Cut(✄) — 블록 있을 때 녹색
        _setColor('btnCopyQuick', hasBlock ? 'green' : '');
        _setColor('btnClearLine', hasBlock ? 'green' : '');

        // Paste(⎘), Clipboard(▤), Footer Paste — 클립보드 있을 때 파란색
        _setColor('btnPasteQuick',  _hasClip ? 'blue' : '');
        _setColor('btnNavR',        _hasClip ? 'blue' : '');
        // 슬롯 네비 모드 중엔 btnFooterPaste style 보존
        if (!window._slotNavMode) _setActive('btnFooterPaste', _hasClip);
    }

    function _posEqualSimple(a, b) {
        return a && b && a.line === b.line && a.ch === b.ch;
    }

    function _setActive(id, active) {
        const el = document.getElementById(id);
        if (!el) return;
        const s = getComputedStyle(document.documentElement);
        el.style.background  = active ? s.getPropertyValue('--ac-active-bg').trim() : '';
        el.style.borderColor = active ? s.getPropertyValue('--ac-active-bd').trim() : '';
        el.style.color       = active ? s.getPropertyValue('--ac-active-tx').trim() : '';
    }

    function _setColor(id, colorVar) {
        // colorVar: '' = reset, 'green' = ac-green-tx, 'blue' = ac-active-tx
        const el = document.getElementById(id);
        if (!el) return;
        if (!colorVar) { el.style.color = ''; return; }
        const s = getComputedStyle(document.documentElement);
        if (colorVar === 'green') el.style.color = s.getPropertyValue('--ac-green-tx').trim();
        else if (colorVar === 'blue') el.style.color = s.getPropertyValue('--ac-active-tx').trim();
        else el.style.color = colorVar; // 직접 값이면 그대로
    }
    function notifyCopied() {
        _hasClip = true;
        _updateCPXButtons();
    }
    function notifyClipCleared() {
        _hasClip = false;
        _updateCPXButtons();
    }
    function _renderStatBtn() {
        const btn = document.getElementById('btnStat');
        if (!btn) return;
        if (!Editor.isReady()) return;
        const text  = Editor.getText();
        const chars = text.length;
        const lines = (text.match(/\n/g) || []).length + 1;

        // 간결 표시: 80kC 3kL 형식
        function _fmt(n) {
            if (n >= 1000) return (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'k';
            return String(n);
        }
        btn.textContent = `C${_fmt(chars)} L${_fmt(lines)}`;
    }

    // ── stat 버튼 탭 → 상세 토스트 ──────────────────────────
    function _onStatTap() {
        if (!Editor.isReady()) return;
        const text     = Editor.getText();
        const chars    = text.length;
        const lines    = (text.match(/\n/g) || []).length + 1;
        const selected = Editor.getSelection()?.length || 0;
        const msg = selected > 0
            ? `${chars.toLocaleString()} chars  ${lines.toLocaleString()} lines  (sel: ${selected.toLocaleString()})`
            : `${chars.toLocaleString()} chars  ${lines.toLocaleString()} lines`;
        UI.showToast(msg, 2500);
    }

    // ── KU 버튼 점등/소등 ────────────────────────────────────
    function updateKUButton(kbOpen) {
        const btn = document.getElementById('btnFooterKeyboard');
        if (!btn) return;
        if (window._inputLocked) return;  // 레드 락 중 덮어쓰기 방지
        const app = document.querySelector('.editor-app');
        const navHidden = app?.classList.contains('nav-hidden');
        const buttonsActive = !navHidden &&
            !!document.querySelector('.swipe-panel.panel-buttons.active');
        const quickActive = !!document.querySelector('.swipe-panel.panel-quick.active');
        // Save/Load 패널 또는 약식도구 패널 상태면 무조건 무색
        if (navHidden || buttonsActive || quickActive) {
            btn.style.background = btn.style.borderColor = btn.style.color = '';
            return;
        }
        const padOpen = window.UIKeypad?.isOpen?.() ?? false;
        const editOpen = !!document.querySelector('.swipe-panel.panel-navigation.active');
        const s = getComputedStyle(document.documentElement);
        if (padOpen) {
            btn.style.background  = s.getPropertyValue('--ac-purple-bg').trim();
            btn.style.borderColor = s.getPropertyValue('--ac-purple-bd').trim();
            btn.style.color       = s.getPropertyValue('--ac-purple').trim();
        } else if (editOpen) {
            btn.style.background  = s.getPropertyValue('--ac-active-bg').trim();
            btn.style.borderColor = s.getPropertyValue('--ac-active-bd').trim();
            btn.style.color       = s.getPropertyValue('--ac-active-tx').trim();
        } else {
            btn.style.background = btn.style.borderColor = btn.style.color = '';
        }
    }

    function updateUndoRedo() {
        const { undo, redo } = Editor.historySize();
        // 멀티모드: 위치 히스토리 스냅샷도 undo 가능 수로 합산
        const snapCount   = window._uiIsBlockMode?.() ? (window.NavBlock?.getBlockSnapshotCount?.() ?? 0) : 0;
        const v2SnapCount = window._uiIsBlockMode?.() ? (window.NavBlockV2?.v2SnapshotCount?.() ?? 0) : 0;
        const undoTotal = undo + snapCount + v2SnapCount;
        _setDisabled('btnUndo',       undoTotal === 0);
        _setDisabled('btnFooterUndo', undoTotal === 0);
        _setDisabled('btnRedo',       redo === 0);
        _setDisabled('btnFooterRedo', redo === 0);
        _setUndoRedoActive('btnFooterUndo', undoTotal > 0);
        _setUndoRedoActive('btnFooterRedo', redo > 0);
    }

    function _setUndoRedoActive(id, active) {
        const el = document.getElementById(id);
        if (!el) return;
        const s = getComputedStyle(document.documentElement);
        el.style.background  = '';
        el.style.borderColor = active ? s.getPropertyValue('--ac-active-bd').trim() : '';
        el.style.color       = active ? s.getPropertyValue('--ac-active-tx').trim() : '';
    }

    function _setDisabled(id, disabled) {
        const el = document.getElementById(id);
        if (el) el.disabled = disabled;
    }

    function init() {
        // 초기 로드: localStorage 클립보드 항목 있으면 점등
        try {
            const stored = JSON.parse(localStorage.getItem('usekit_clipboard_history') || '[]');
            if (stored.length > 0) { _hasClip = true; _updateCPXButtons(); }
        } catch {}

        // M-LOCK 클릭 차단 핸들러 — touchstart는 막지 않고 selection만 복원
        function _mlockBlockClick(e) {
            // touchstart/mousedown은 통과 — OS 키보드 허용
            // selection 변화는 cursorActivity에서 처리
        }

        let _mlockSavedBS = null;
        let _mlockSavedBE = null;

        let _mlockListenerAttached = false;
        window._uiAttachMLockBlock = () => {
            if (_mlockListenerAttached) return;
            // BS/BE 현재 상태 저장
            _mlockSavedBS = State.getBS();
            _mlockSavedBE = State.getBE();
            _mlockListenerAttached = true;
        };
        window._uiDetachMLockBlock = () => {
            _mlockListenerAttached = false;
            _mlockSavedBS = null;
            _mlockSavedBE = null;
        };

        let _mlockRestoring = false;

        Editor.on('cursorActivity', (view) => {
            if (window.NavBlock?.isColumnEditing?.()) return; // 컬럼 편집 중이면 무시
            if (window.BlockState?.isActive?.()) {
                const sel = view.state.selection;
                // 클릭(단일 커서)이면 baseCh/baseLine만 재설정 (inputmode 유지)
                if (sel.ranges.length === 1 && sel.main.from === sel.main.to) {
                    window.BlockState?.reanchor?.();
                }
                updateStats();
                return;
            }
            if (_mlockListenerAttached) {
                if (_mlockRestoring) return;
                const sel = view.state.selection;
                if (sel.ranges.length === 1 && sel.main.from === sel.main.to) {
                    // 클릭 위치를 BE로 업데이트 후 재적용
                    const clickPos = Editor.offsetToPos?.(sel.main.head);
                    if (clickPos) {
                        const bs = State.getBS();
                        const be = State.getBE();
                        // BS=BE 일치 (ESC 후 앵커 미설정 상태) → 클릭 위치로 앵커 후 락온
                        if (bs && be && bs.line === be.line && bs.ch === be.ch) {
                            window._uiMLockOff?.();
                            State.setBS(clickPos);
                            State.setBE(clickPos);
                            window._uiMLockOn?.();
                            updateStats();
                            return;
                        }
                        _mlockRestoring = true;
                        // CUR 모드(쉬프트 오프)일 때만 BS ch 동기화 → 블럭 없이 멀티커서
                        // BLK 모드(쉬프트 온)이면 클릭 위치 그대로 → 블럭 생성
                        const bsCh = bs?.ch ?? clickPos.ch;
                        State.setBE(window._uiIsCurMode?.() ? { line: clickPos.line, ch: bsCh } : clickPos);
                        window.NavBlock?.applyColumnSelection?.();
                        setTimeout(() => { _mlockRestoring = false; }, 50);
                        return;
                    }
                }
            }
            // CM6 투핸들 스틸: 범위 선택이 있으면 BS/BE로 흡수
            _stealCM6Selection(view);
            updateStats();
        });
        Editor.on('changes', (view) => {
            updateStats();
            // 블럭모드: OS 키보드 입력 후 decoration + BS/BE 위치 갱신 (V2 활성 시 스킵)
            if (window._uiIsBlockMode?.() && !window.NavBlock?.isColumnEditing?.() && !window.BlockState?.isActive?.()) {
                window.NavBlock?.syncColumnAfterInput?.(view);
            }
        });
        Editor.on('focus',          updateStatsNow);

        // stat 버튼 탭 바인딩
        const statBtn = document.getElementById('btnStat');
        if (statBtn) {
            let _t = null, _fired = false;
            statBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                _fired = false;
                _t = setTimeout(() => {
                    _fired = true;
                    window.Nav?.goToLine?.();
                }, 400);
            }, { passive: false });
            statBtn.addEventListener('touchend', (e) => {
                e.preventDefault();
                clearTimeout(_t);
                if (!_fired) _onStatTap();
            }, { passive: false });
            statBtn.addEventListener('touchcancel', () => clearTimeout(_t));
            statBtn.addEventListener('click', _onStatTap);
        }
    }

    return { init, updateStats, updateStatsNow, updateUndoRedo, updateKUButton, notifyCopied, notifyClipCleared };
})();

window.UIStats = UIStats;
