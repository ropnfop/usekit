/* Path: usekit/tools/editor/js2/state/state_slot.js
 * --------------------------------------------------------------------------------------------
 * StateSlot — ActiveState ↔ SlotSnapshot 브리지
 *
 * v1.3 핵심 변경:
 *   «활성창이 진실, 슬롯은 활성창의 복제»
 *
 *   슬롯이 저장하는 것:  text / cursor / scrollTop / wrap / lineNumbers / edit / ui
 *   슬롯이 저장 안 하는 것: theme / font / fontSize  (→ global, 활성창 유지)
 *
 *   슬롯 복원 시 theme/font/fontSize는 건드리지 않음.
 *   → href 교체 없음 → 깨짐 없음.
 * ─────────────────────────────────────────────────────────── */

const StateSlot = (function () {
    'use strict';

    // ── 구버전 flat 스냅샷 → 신규 포맷 변환 ──────────────────────
    function migrate(snap) {
        if (!snap) return null;
        // 신규 포맷: settings + edit 있으면 통과 (ui는 없을 수 있음)
        if (snap.settings && snap.edit) return snap;
        return {
            text:      snap.text      ?? '',
            cursor:    snap.cursor    ? { ...snap.cursor } : { line: 0, ch: 0 },
            scrollTop: snap.scrollTop ?? 0,
            settings: {
                // theme/font/fontSize는 저장하되, 복원 시 global 정책이면 무시됨
                theme:       snap.theme    ?? null,
                font:        snap.font     ?? null,
                fontSize:    snap.fontSize ?? null,
                wrap:        snap.lineWrapping !== undefined ? !!snap.lineWrapping
                           : snap.wrapOn      !== undefined ? !!snap.wrapOn : false,
                lineNumbers: snap.lineNumbers !== undefined ? !!snap.lineNumbers
                           : snap.lineNumOn   !== undefined ? !!snap.lineNumOn : true,
            },
            edit: {
                lkMode: !!snap.lkOn,
                modeS:  false,   // 슬롯 전환 시 선택 모드 초기화
                modeM:  !!snap.modeM,
            },
            ui: {
                navVisible:      snap.navVisible      !== undefined ? !!snap.navVisible : true,
                navPanelIndex:   snap.navPanelIdx     !== undefined ? snap.navPanelIdx  : 0,
                thirdRowVisible: snap.navThirdRowVisible !== undefined ? !!snap.navThirdRowVisible : false,
            },
            updatedAt: snap.updatedAt ?? 0,
        };
    }

    // ── Capture: ActiveState → SlotSnapshot ──────────────────────
    function capture() {
        return ActiveState.toSnapshot();
    }

    // ── Apply: SlotSnapshot → 활성창 복원 ────────────────────────
    //
    // 복원 순서 (정비방향 §7):
    //   1. text 복원
    //   2. wrap / lineNumbers 복원  (레이아웃 변경)
    //   3. edit 모드 복원
    //   4. UI 패널 복원
    //   5. cursor / scroll 복원  ← 반드시 마지막
    //
    // theme / font / fontSize: global 정책이면 현재 활성창 값 유지 (건드리지 않음)
    function apply(snap, opts) {
        if (!snap) return;
        if (!Editor.isReady()) return;

        const normalized = migrate(snap);
        if (!normalized) return;

        // 1. ActiveState에 로드
        ActiveState.fromSnapshot(normalized);

        // 2. text + wrap/lineNumbers 적용 (cursor는 defer)
        ActiveState.applyToEditor({ deferCursor: true, text: opts?.skipText !== true });

        // 3. edit 모드 (lk/modeS/modeM + BS/BE)
        ActiveState.applyToState();

        // 4. UI 패널/nav
        ActiveState.applyToUI();

        // 5. slot-policy 항목만 적용 (theme/font/size는 global이면 스킵)
        _applySlotSettings(normalized.settings || {});

        // 6. cursor/scroll — 레이아웃 안정 후 마지막
        //    BS/BE selection은 cursor 복원 이후에 덮어씀
        if (!opts?.deferCursor) {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    ActiveState.applyCursorScroll();
                    _applyBlockSelection();
                });
            });
        }

    }

    // BS/BE → CM6 selection 반영
    function _applyBlockSelection() {
        const bs = ActiveState.get('bs');
        const be = ActiveState.get('be');
        if (bs && be) {
            window.Editor?.setSelectionDirected?.(bs, be);
        }
    }

    // slot 정책 항목만 적용 — theme/font/fontSize는 global이면 무조건 스킵
    function _applySlotSettings(settings) {
        if (!window.UISettings) return;
        const policy = SetupPolicy?.get?.() || {};

        // theme: global이면 현재 테마 유지, slot이면 스냅샷 테마 적용
        if (policy.theme === 'slot' && settings.theme) {
            UISettings.applyTheme(settings.theme, { slotOverride: true });
        }
        // font: global이면 스킵
        if (policy.font === 'slot' && settings.font) {
            UISettings.applyFont(settings.font);
        }
        // fontSize: global이면 스킵
        if (policy.fontSize === 'slot' && settings.fontSize != null) {
            UISettings.applyFontSize(Number(settings.fontSize));
        }
    }

    // cursor/scroll 단독 복원 (init 마지막 단계)
    function applyCursorScroll() {
        ActiveState.applyCursorScroll();
        _applyBlockSelection();
    }

    return { capture, apply, migrate, applyCursorScroll };
})();

window.StateSlot = StateSlot;
