/* Path: usekit/tools/editor/js/io/slot/slot_usekit.js
 * -----------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 * USEKIT / Termux sync layer for slot system.
 * Depends on: SlotStorage, EditorEnv, EditorIO
 *---------------------------------------------------------------------------------------------*/

const SlotUsekit = (function () {
    'use strict';

    let _loadSeq = 0; // global seq guard for async loads

    // ===== PATH HELPERS =====

    function isUsekitSlot(slot) {
        return !!slot && String(slot.storage || '').toLowerCase() === 'usekit';
    }

    function isAbsPath(p) {
        const s = String(p || '').trim();
        return s.startsWith('/_tmp/');
    }

    function getTargetPath(slot) {
        const p = String(slot?.usekitPath || '').trim();
        if (p) return p;
        const fn = String(slot?.fileName || '').trim();
        return isAbsPath(fn) ? fn : '';
    }

    // ===== SYNC FROM SERVER =====

    /**
     * USEKIT 슬롯을 Termux 서버에서 동기화.
     *
     * @param {object}   slot              - 슬롯 객체 (slots[] 의 원본 참조)
     * @param {number}   absIndex          - slots[] 내 절대 인덱스
     * @param {string}   reason            - 디버그용 호출 이유
     * @param {object}   ctx               - 컨텍스트 (슬롯 배열 접근용 accessor)
     * @param {Function} ctx.getSlot       - (idx) => slot 객체
     * @param {Function} ctx.getActiveIdx  - () => 현재 activeSlotIndex
     * @param {Function} ctx.onRemove      - (idx, opts) 슬롯 제거 콜백
     * @param {Function} ctx.onSynced      - (text, applyToEditor) 성공 후 콜백
     * @param {boolean}  [forceApply]      - activeSlot 여부 무관하게 editor에 반영
     */
    function syncFromServer(slot, absIndex, reason, ctx, forceApply = false) {
        if (!isUsekitSlot(slot)) return Promise.resolve(false);

        const targetPath = getTargetPath(slot);
        if (!targetPath) {
            console.warn('[SlotUsekit] missing usekitPath', { slot: slot?.fileName, absIndex, reason });
            return Promise.resolve(false);
        }

        const seq = ++_loadSeq;
        slot.__usekitLoadSeq = seq;
        const expectedName = slot.fileName;


        const url = isAbsPath(targetPath)
            ? `/api/read?path=${encodeURIComponent(targetPath)}`
            : `/api/load?path=${encodeURIComponent(targetPath)}`;

        return fetch(url)
            .then(r => r.json().catch(() => ({})).then(j => ({ r, j })))
            .then(({ r, j }) => {
                if (!j || !j.ok) {
                    const err = (j && j.error) ? String(j.error) : `http_${r.status}`;
                    console.warn('[SlotUsekit] sync failed', { seq, err, slot: expectedName });
                    if (err === 'file_not_found' || r.status === 404) {
                        SlotStorage.toast('File does not exist.');
                        ctx.onRemove(absIndex, { removeUsekitMeta: true });
                    } else {
                        SlotStorage.toast(`Load failed: ${err}`);
                    }
                    return false;
                }

                // stale guard
                const currentSlot = ctx.getSlot(absIndex);
                const stillSame = currentSlot && currentSlot.fileName === expectedName;
                const stillLatest = slot.__usekitLoadSeq === seq;
                if (!stillSame || !stillLatest) {
                    return false;
                }

                const text = j.text || '';
                slot.data = { text, cursor: 0, timestamp: Date.now() };

                const activeNow = ctx.getSlot(ctx.getActiveIdx())?.fileName === expectedName;
                const apply = activeNow || forceApply;
                ctx.onSynced(text, apply);

                if (EditorIO?.updateLocationDisplay) EditorIO.updateLocationDisplay(expectedName);

                return true;
            })
            .catch(e => {
                console.warn('[SlotUsekit] sync exception', e);
                SlotStorage.toast(`Load failed: ${e?.message || e}`);
                return false;
            });
    }

    // ===== ADD USEKIT FILE AS SLOT =====

    /**
     * USEKIT 탭에서 파일 선택 시 슬롯에 추가 후 editor에 로드.
     * @param {string}   filePath
     * @param {string}   fileName
     * @param {object}   ctx
     * @param {Function} ctx.findSlot        - (pred) => index
     * @param {Function} ctx.addSlot         - (slotObj) => newIndex
     * @param {Function} ctx.activateSlot    - (idx) => void  (sets activeSlotIndex, updates UI)
     * @param {Function} ctx.closeModal      - () => void
     */
    async function openUsekitFile(filePath, fileName, ctx) {
        try {
            // filePath: /_tmp/... (sandbox 절대경로)
            // fileName: 파일명만 (L01.txt 등) - 슬롯 표시용

            // 이미 슬롯에 있으면 무시 (usekitPath 기준)
            const _extMatchChk  = fileName.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
            const slotNameCheck = _extMatchChk ? _extMatchChk[1] : fileName;
            const existIdx = ctx.findSlot(s => s.storage === 'usekit' && (s.usekitPath === filePath || s.fileName === slotNameCheck));
            if (existIdx >= 0) {
                // 이미 슬롯에 있으면 서버에서 최신 내용 fetch 후 diff
                const isSandboxChk = !filePath.startsWith('/storage') && !filePath.startsWith('/data');
                const readUrlChk = isSandboxChk
                    ? `/api/read?path=${encodeURIComponent(filePath)}`
                    : `/api/read_abs?path=${encodeURIComponent(filePath)}`;
                try {
                    const res = await fetch(readUrlChk);
                    if (res.ok) {
                        const d = await res.json().catch(() => null);
                        if (d?.ok && d.text !== undefined) {
                            const serverText = d.text;
                            // 현재 슬롯 텍스트
                            const slots = ctx.getSlots?.() ?? [];
                            const activeIdx = ctx.getActiveIdx?.() ?? -1;
                            const slotText = existIdx === activeIdx
                                ? (window.Editor?.getText?.() ?? '')
                                : (SlotStorage.readSlot(slots[existIdx]?.fileName)?.text ?? serverText);
                            if (!slotText || slotText === serverText) {
                                ctx.activateSlot(existIdx, serverText);
                                ctx.closeModal();
                            } else {
                                ctx.openDiff(fileName, slotText, serverText,
                                    () => { ctx.activateSlot(existIdx, serverText); ctx.closeModal(); },
                                    () => { ctx.activateSlot(existIdx); ctx.closeModal(); },
                                    ['SLOT', 'SERVER', 'Keep Slot', 'Load Server', 'current', 'remote', 'Version Conflict']
                                );
                            }
                            return;
                        }
                    }
                } catch(e) {}
                // fetch 실패 시 캐시로 폴백
                ctx.activateSlot(existIdx);
                ctx.closeModal();
                return;
            }

            // sandbox 경로(/_tmp/...)는 /api/read, 절대경로(/storage/...)는 /api/read_abs
            const isSandbox = !filePath.startsWith('/storage') && !filePath.startsWith('/data');
            const readUrl = isSandbox
                ? `/api/read?path=${encodeURIComponent(filePath)}`
                : `/api/read_abs?path=${encodeURIComponent(filePath)}`;
            const response = await fetch(readUrl);
            if (!response.ok) {
                SlotStorage.toast(`Load failed: HTTP ${response.status}`);
                return;
            }
            const data = await response.json().catch(e => { console.error('[openUsekitFile] json parse error', e); return null; });
            if (!data || !data.ok) {
                SlotStorage.toast(`Load failed: ${data?.error || 'parse_error'}`);
                return;
            }

            // fileName: 확장자 제거 (U01.txt → U01, helper_debug.txt → helper_debug)
            // 마지막 점 이후가 1~6자 영문숫자면 확장자로 간주
            const _extMatch = fileName.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
            const slotName  = _extMatch ? _extMatch[1] : fileName;

            // usekitPath: sandbox 상대경로 그대로 저장 (LOC 표시는 slot_manager가 base 붙임)
            const idx = ctx.addSlot({
                storage:    'usekit',
                fileName:   slotName,
                isDirty:    false,
                usekitPath: filePath,
                data:       { text: data.text, cursor: 0, timestamp: data.mtime || Date.now() }
            });

            // 슬롯에 동명 로컬 파일이 있으면 diff
            const localStored = SlotStorage.readLocal(slotName)
                             || await SlotStorage.readLocalAsync?.(slotName);
            const localText = localStored?.text;
            if (localText !== undefined && localText !== data.text) {
                ctx.openDiff(slotName, data.text, localText,
                    () => { ctx.activateSlot(idx, data.text);  ctx.closeModal(); },  // Load Usekit
                    () => { ctx.activateSlot(idx, localText);  ctx.closeModal(); },  // Load Local
                    ['SERVER', 'LOCAL', 'Load Server', 'Load Local', 'loaded', 'saved', 'Load Which Version?']
                );
            } else {
                ctx.activateSlot(idx, data.text);
                ctx.closeModal();
                SlotStorage.toast(`Loaded: ${fileName}`);
            }
        } catch (e) {
            console.error('[SlotUsekit.openUsekitFile] exception', e, e?.stack);
            SlotStorage.toast(`Load failed: ${e?.message || e}`);
        }
    }

    return {
        isUsekitSlot,
        isAbsPath,
        getTargetPath,
        syncFromServer,
        openUsekitFile,
    };
})();

window.SlotUsekit = SlotUsekit;
