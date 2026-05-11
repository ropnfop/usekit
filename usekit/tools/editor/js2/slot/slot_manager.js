/* Path: usekit/tools/editor/js2/slot/slot_manager.js
 * --------------------------------------------------------------------------------------------
 * SlotManager v4 — 단순 설계
 *
 * 슬롯  = 작업공간. 변경 즉시 slot_xxx(OPFS)에 오토세이브. isDirty 유지.
 * Save  = 슬롯 내용을 로컬(xxx) 또는 유즈킷(서버)에 복사. isDirty 해제.
 *
 * isDirty 변경:
 *   true  → 에디터 변경(_markDirty)
 *   false → Save / Save As 성공 시만
 * ─────────────────────────────────────────────────────────── */

const SlotManager = (function () {
    'use strict';

    const WIN = 3;
    let _slots    = [];
    let _active   = -1;
    let _winStart = 0;
    let _switching  = false;
    let _initDone   = false;
    let _editorStateCache = new Map();
    let _usekitBase = '';
    let _autoTimer  = null;


    // ── Helpers ───────────────────────────────────────────────
    function _clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
    function _esc(s) {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }

    // ── 슬롯 오토세이브 ────────────────────────────────────────
    // slot_xxx(OPFS) 항상 저장. isDirty 유지.
    function _scheduleAutosave() {
        if (_autoTimer) clearTimeout(_autoTimer);
        _autoTimer = setTimeout(() => {
            _autoTimer = null;
            // chat 모드에서는 에디터에 prompt가 들어있으므로 슬롯에 저장하지 않음
            if (window.AiChat?.isChat) return;
            if (_active < 0 || !_slots[_active]) return;
            const slot = _slots[_active];
            // storage('local'|'usekit')는 Save 목적지일 뿐 — autosave는 항상 OPFS(slot_xxx)에
            const data = { text: Editor.getText(), timestamp: Date.now() };
            SlotStorage.writeSlot(slot.fileName, data);
        }, 300);
    }

    // ── Mark dirty ────────────────────────────────────────────
    function _markDirty() {
        if (_active < 0 || !_slots[_active] || _switching) return;
        // chat 모드에서는 dirty 표시/autosave 하지 않음
        if (window.AiChat?.isChat) return;
        const slot = _slots[_active];
        if (!slot.isDirty) { slot.isDirty = true; _display(); _saveMeta(); }
        _scheduleAutosave();
    }

    // ── Metadata ──────────────────────────────────────────────
    function _saveMeta() {
        SlotStorage.saveMetadata(_slots, _active, _winStart, window.ActiveState?.getUI?.());
    }
    function saveUIState() {
        if (!_initDone) return;
        if (!_switching) _capture();
        _saveMeta();
    }

    // ── Capture / Apply ───────────────────────────────────────
    function _capture() {
        if (_active < 0 || !_slots[_active]) return;
        const slot = _slots[_active];
        slot.state = ActiveState.toSnapshot();
        const es = window.Editor?.saveEditorState?.();
        if (es) _editorStateCache.set(slot.slotIndex, es);
    }

    function _applyLKToEditor() {
        const cm = Editor.get?.()?.contentDOM;
        if (!cm) return;
        if (ActiveState.getEdit('lkMode')) {
            cm.setAttribute('inputmode', 'none');
        } else if (window.UIViewport?.isKbAllowed?.() !== false) {
            // _allowKb가 false(KB 차단 상태)면 inputmode 건드리지 않음
            cm.removeAttribute('inputmode');
        }
    }

    function _apply(slot, opts) {
        _switching = true;
        const cachedState = _editorStateCache.get(slot.slotIndex);
        if (cachedState) {
            window.Editor?.restoreEditorState?.(cachedState);
            if (slot.state) StateSlot.apply(slot.state, { deferCursor: true, skipText: true });
            _applyLKToEditor();
        } else if (slot.state) {
            StateSlot.apply(slot.state, { deferCursor: true, skipText: true }); // 텍스트는 _loadText가 책임
            _applyLKToEditor();
        } else {
            // 텍스트는 _loadText(async)가 책임짐 - 여기서 setText('')하지 않음
            Editor.setCursor({ line: 0, ch: 0 });
            const prevLK = State.getLK();
            State.reset();
            if (window.ActiveState) ActiveState.reset(slot.slotIndex);
            State.setLK(prevLK);
            ActiveState.setEdit('lkMode', prevLK);
            ActiveState.applyToUI();   // 패널 상태 복원 (uiMode 유지)
            _applyLKToEditor();
        }
        requestAnimationFrame(() => { requestAnimationFrame(() => {
            StateSlot.applyCursorScroll();
            UIStats.updateStatsNow();
            window.UIEvents?.resyncEditorButtons?.();
            requestAnimationFrame(() => {
                _switching = false;
                if (_active >= 0 && _slots[_active]) {
                    const es = window.Editor?.saveEditorState?.();
                    if (es) _editorStateCache.set(_slots[_active].slotIndex, es);
                }
                window.UIStats?.updateUndoRedo?.();
            });
        }); });
    }

    // ── Load text ─────────────────────────────────────────────
    // 텍스트만 복원. isDirty는 메타에서 이미 복원됨.
    // async - await해서 _apply 전에 텍스트가 확실히 세팅되도록.
    async function _loadText(slot) {
        // 1. 슬롯파일(slot_xxx) sync 우선 (cache hit 시 즉시)
        const stored = SlotStorage.readSlot(slot.fileName);
        if (stored) { Editor.setText(stored.text || ''); return; }

        // 2. async fallback (OPFS/IDB)
        const data = await SlotStorage.readSlotAsync(slot.fileName);
        if (data) {
            if (window.SlotManager?.getCurrentSlotInfo?.()?.slotIndex === slot.slotIndex)
                Editor.setText(data.text || '');
            return;
        }

        // 3. 로컬파일(xxx) fallback
        const local = SlotStorage.readLocal(slot.fileName)
                   || await SlotStorage.readLocalAsync(slot.fileName);
        if (local) {
            if (window.SlotManager?.getCurrentSlotInfo?.()?.slotIndex === slot.slotIndex)
                Editor.setText(local.text || '');
            return;
        }

        // 4. 데이터 없음 → 빈 에디터
        Editor.setText('');
    }

    // ── Header / Display ──────────────────────────────────────
    function _syncHeader(slot) {
        const nameEl = document.getElementById('metaFile');
        if (nameEl) nameEl.value = slot.fileName;
        const funcEl = document.getElementById('metaFunc');
        if (funcEl) {
            funcEl.textContent = slot.storage || 'local';
            funcEl.classList.toggle('is-usekit', slot.storage === 'usekit');
            funcEl.classList.toggle('is-dirty',  !!slot.isDirty);
        }
        const extSrc   = slot.storage === 'usekit' ? (slot.usekitPath || slot.fileName || '') : (slot.fileName || '');
        const extMatch = extSrc.match(/\.([a-zA-Z0-9]{1,6})$/);
        const extVal   = extMatch ? extMatch[1] : '';
        const extEl    = document.getElementById('metaExt');
        if (extEl) extEl.value = extVal;
        const displayEl = document.getElementById('metaFileDisplay');
        if (displayEl) {
            const fname  = slot.fileName || '—';
            const suffix = (extVal && !fname.toLowerCase().endsWith('.' + extVal.toLowerCase())) ? '.' + extVal : '';
            displayEl.textContent = (slot.isDirty ? '*' : '') + fname + suffix;
            displayEl.classList.toggle('is-dirty',  !!slot.isDirty);
            displayEl.classList.toggle('is-usekit', slot.storage === 'usekit');
        }
        _updateLocDisplay(slot);
    }

    function _updateLocDisplay(slot) {
        const locEl = document.getElementById('metaLoc');
        if (!locEl) return;
        if (slot.storage === 'usekit' && slot.usekitPath) {
            const sandboxPath = slot.usekitPath.replace(/^\//, '');
            const absPath = _usekitBase ? _usekitBase.replace(/\/$/, '') + '/' + sandboxPath : slot.usekitPath;
            // USEKIT_BASE 상위를 잘라내고 프로젝트 폴더명부터 표시 (e.g. pj01/_tmp/foo.txt)
            const baseParts = _usekitBase ? _usekitBase.replace(/\/+$/, '').split('/') : [];
            const projName  = baseParts.length ? baseParts[baseParts.length - 1] : '';
            locEl.value = projName ? projName + '/' + sandboxPath : absPath;
            locEl.dataset.fullpath = absPath;  // 팝업용 전체 경로
        } else {
            const displayVal = `${SlotStorage.getMode?.() || 'opfs'}://${slot.fileName}`;
            locEl.value = displayVal;
            locEl.dataset.fullpath = displayVal;
        }
    }
    function setUsekitBase(base) { if (base) _usekitBase = base; }

    function _display() {
        _winOk();
        for (let i = 1; i <= WIN; i++) {
            const el  = document.getElementById(`slot${i}`);
            if (!el) continue;
            const abs = _winStart + (i - 1);
            const s   = _slots[abs];
            if (!s) { el.textContent = '—'; el.className = 'slot-box slot-inactive'; el.dataset.absIndex = '-1'; continue; }
            const label = (s.isDirty ? '*' : '') + s.fileName;
            el.dataset.absIndex = String(abs);
            if (abs === _active) {
                el.innerHTML = `<span class="slot-label">${_esc(label)}</span><button type="button" class="slot-close" aria-label="Close">x</button>`;
            } else {
                el.textContent = label;
            }
            el.className = 'slot-box' +
                (abs === _active         ? ' slot-active'  : '') +
                (s.isDirty              ? ' slot-dirty'   : '') +
                (s.storage === 'usekit' ? ' slot-usekit'  : ' slot-local');
        }
        const L = document.getElementById('slotArrowLeft');
        const R = document.getElementById('slotArrowRight');
        if (L) L.disabled = _active <= 0;
        if (R) R.disabled = _active >= _slots.length - 1;
        if (_active >= 0 && _slots[_active]) {
            const slot     = _slots[_active];
            const isDirty  = !!slot.isDirty;
            const isUsekit = slot.storage === 'usekit';
            const displayEl = document.getElementById('metaFileDisplay');
            if (displayEl) {
                const fname  = slot.fileName || '—';
                const extSrc = isUsekit ? (slot.usekitPath || fname) : fname;
                const extM   = extSrc.match(/\.([a-zA-Z0-9]{1,6})$/);
                const extV   = extM ? extM[1] : '';
                const sfx    = (extV && !fname.toLowerCase().endsWith('.' + extV.toLowerCase())) ? '.' + extV : '';
                displayEl.textContent = (isDirty ? '*' : '') + fname + sfx;
                displayEl.classList.toggle('is-dirty',  isDirty);
                displayEl.classList.toggle('is-usekit', isUsekit);
            }
            const funcEl  = document.getElementById('metaFunc');
            if (funcEl) { funcEl.classList.toggle('is-dirty', isDirty); funcEl.classList.toggle('is-usekit', isUsekit); }
            const saveBtn = document.getElementById('btnFooterSave');
            if (saveBtn) saveBtn.classList.toggle('is-dirty', isDirty);
        }
    }

    // ── Win / Slot helpers ────────────────────────────────────
    function _winOk() {
        if (_slots.length > 0 && _active === _slots.length - 1 && _slots.length >= WIN)
            _winStart = _active - (WIN - 2);
        else
            _winStart = _clamp(_winStart, 0, Math.max(0, _slots.length - WIN));
        _winStart = Math.max(0, _winStart);
    }
    function _centerWin() {
        if (_active >= 0) _winStart = _clamp(_active - 1, 0, Math.max(0, _slots.length - WIN));
    }
    function _insertSlot(slot, at, { notify = false } = {}) {
        const dup = _slots.findIndex(s => s.fileName === slot.fileName && s.storage === slot.storage);
        if (dup >= 0) {
            if (notify) (window.showConfirm || ((m,cb,opt) => window.alert(m)))(
                `'${slot.fileName}' already exists in slots.`, () => {}, { okLabel: 'OK', cancelHide: true });
            return dup;
        }
        _slots.splice(at, 0, slot);
        return at;
    }

    // ── Core switch ───────────────────────────────────────────
    async function _switchTo(absIdx) {
        if (absIdx < 0 || absIdx >= _slots.length || absIdx === _active) return;
        if (_autoTimer) { clearTimeout(_autoTimer); _autoTimer = null; }
        const prev = _switching; _switching = false;
        _capture();
        _switching = true; // await 중에도 switching 유지 → allowKeyboard 오발화 방지
        _active = absIdx;
        const slot = _slots[_active];
        _syncHeader(slot);
        await _loadText(slot);
        _editorStateCache.delete(slot.slotIndex);
        _apply(slot, { skipSetText: true });
        _centerWin(); _display(); _saveMeta();
    }

    // ── Save local ────────────────────────────────────────────
    function _doSaveLocal(slot, silent) {
        const data = { text: Editor.getText(), timestamp: Date.now() };
        const ok   = SlotStorage.writeLocal(slot.fileName, data);
        if (ok) {
            SlotStorage.writeSlot(slot.fileName, data);
            slot.isDirty = false;
            slot.state   = StateSlot.capture();
            _display(); _saveMeta(); _updateLocDisplay(slot);
            if (!silent) SlotStorage.toast(`Saved: ${slot.fileName}`);
        }
        return ok;
    }

    function _saveLocal({ silent = false } = {}) {
        if (_active < 0 || !_slots[_active]) return false;
        const slot    = _slots[_active];
        const rawName = slot.fileName || document.getElementById('metaFile')?.value?.trim() || '';
        const name    = SlotStorage.sanitizeFileName(rawName) || slot.fileName;
        if (name !== slot.fileName) {
            if (SlotStorage.localKeyExists(name)) {
                (window.showConfirm || ((m,cb) => { if(window.confirm(m)) cb(); }))(
                    `'${name}' already exists. Overwrite?`, () => {
                        const dupIdx = _slots.findIndex((s,i) => i !== _active && s.fileName === name && s.storage === 'local');
                        if (dupIdx >= 0) { _slots.splice(dupIdx, 1); if (_active > dupIdx) _active--; }
                        SlotStorage.migrateLocalKey(slot.fileName, name, { allowOverwrite: true });
                        SlotStorage.migrateSlotKey(slot.fileName, name);
                        slot.fileName = name;
                        _doSaveLocal(slot, silent);
                    }
                );
                return false;
            }
            SlotStorage.migrateLocalKey(slot.fileName, name, { allowOverwrite: true });
            SlotStorage.migrateSlotKey(slot.fileName, name);
            slot.fileName = name;
        }
        return _doSaveLocal(slot, silent);
    }

    // ── Save usekit ───────────────────────────────────────────
    function _saveUsekit({ silent = false, _prevStorage = null, _prevPath = null } = {}) {
        if (_active < 0 || !_slots[_active]) return false;
        const slot       = _slots[_active];
        const targetPath = slot.usekitPath || '';
        if (!targetPath) { SlotStorage.toast('No USEKIT path — use SAVE AS'); return false; }
        const text         = Editor.getText();
        const sandboxMatch = targetPath.match(/(\/)?((\_tmp\/).+)$/);
        const sandboxPath  = sandboxMatch ? '/' + sandboxMatch[2] : targetPath;
        const _onFail = (msg) => {
            if (_prevStorage !== null) {
                slot.storage = _prevStorage; slot.usekitPath = _prevPath || '';
                _saveMeta(); _syncHeader(slot); _display();
            }
            SlotStorage.toast(msg, 2500, 'top');
        };
        fetch('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ storage: 'usekit', path: sandboxPath.replace(/^\//, ''), text }),
            signal: AbortSignal.timeout(3000) })
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(j => {
            if (!j?.ok) { _onFail(`Save failed: ${j?.error || 'unknown'}`); return; }
            SlotStorage.writeSlot(slot.fileName, { text, timestamp: Date.now() });
            slot.isDirty = false;
            slot.state   = StateSlot.capture();
            _display(); _saveMeta(); _updateLocDisplay(slot);
            if (!silent) SlotStorage.toast(`Saved: ${slot.fileName}`);
        })
        .catch(e => _onFail(`Save failed: ${e?.message || e}`));
        return true;
    }

    // ── Public save ───────────────────────────────────────────
    function save({ silent = false } = {}) {
        if (_active < 0 || !_slots[_active]) { SlotStorage.toast('No active slot'); return false; }
        const slot = _slots[_active];
        if (slot.storage !== 'usekit' && !SlotStorage.localKeyExists(slot.fileName)) {
            openSavePopup(); return false;
        }
        return slot.storage === 'usekit' ? _saveUsekit({ silent }) : _saveLocal({ silent });
    }

    // ── Close ─────────────────────────────────────────────────
    function closeCurrentSlot(onDone) {
        if (_active < 0 || !_slots[_active]) { SlotStorage.toast('No active slot'); return; }
        closeSlotAt(_active, onDone);
    }

    function closeSlotAt(idx, onDone) {
        if (idx < 0 || !_slots[idx]) return;
        const slot = _slots[idx];
        const isActive = idx === _active;

        async function _doClose() {
            _editorStateCache.delete(slot.slotIndex);
            SlotStorage.removeSlot(slot.fileName);
            SlotStorage.removeChat(slot.fileName);
            // 슬롯 연동 업로드 이미지 가비지 삭제
            try { fetch('/api/delete-uploads', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({slot:slot.fileName}) }); } catch(e) {}
            _slots.splice(idx, 1);
            _saveMeta();
            if (_slots.length === 0) {
                _active = -1; _winStart = 0; Editor.setText('');
                const nameEl = document.getElementById('metaFile');
                if (nameEl) nameEl.value = '';
                _display(); SlotStorage.toast('All slots closed'); onDone?.(0); return;
            }
            if (isActive) {
                _active = Math.min(idx, _slots.length - 1);
                _winOk();
                const next = _slots[_active];
                _switching = true; _syncHeader(next); await _loadText(next); _editorStateCache.delete(next.slotIndex); _apply(next, { skipSetText: true });
            } else {
                // 비활성 슬롯 삭제 시 active 인덱스 보정
                if (_active > idx) _active--;
                _winOk();
            }
            _centerWin(); _display(); _saveMeta();
            SlotStorage.toast(`Closed: ${slot.fileName}`);
            onDone?.(_slots.length);
        }

        if (slot.isDirty) {
            (window.showConfirm || ((m,cb) => { if(window.confirm(m)) cb(); }))(
                `'${slot.fileName}' has unsaved changes. Close anyway?`, _doClose);
            return;
        }
        _doClose();
    }

    // ── New file ──────────────────────────────────────────────
    function newFile() {
        _capture();
        const funcEl  = document.getElementById('metaFunc');
        const storage = (funcEl?.textContent?.trim().toLowerCase() === 'usekit') ? 'usekit' : 'local';
        const maxIdx  = _slots.length > 0 ? Math.max(..._slots.map(s => s.slotIndex)) : -1;
        const name    = 'tmp_' + String(Date.now()).slice(-6);
        let usekitPath = '';
        if (storage === 'usekit') {
            const ping   = window._usekitPing;
            const relDir = (ping?.default_usekit_rel_dir || '_tmp').replace(/\/?$/, '');
            const ext    = document.getElementById('metaExt')?.value?.trim() || 'txt';
            usekitPath   = `/${relDir}/${name}.${ext}`;
        }
        const newSlot = { slotIndex: maxIdx + 1, storage, fileName: name, isDirty: false, usekitPath, state: null };
        _active = _insertSlot(newSlot, _slots.length, { notify: true });
        _winOk(); _syncHeader(newSlot); _updateLocDisplay(newSlot);
        Editor.setText(''); Editor.setCursor({ line: 0, ch: 0 });
        UIStats.updateStatsNow(); _display(); _saveMeta();
        SlotStorage.toast(`New slot: ${name}`);
    }

    // ── Rename ────────────────────────────────────────────────
    function renameCurrentSlot(newName, { allowOverwrite = false, silent = true } = {}) {
        if (_active < 0 || !_slots[_active]) return false;
        const slot = _slots[_active];
        const name = SlotStorage.sanitizeFileName(newName);
        if (!name || name === slot.fileName) return !!name;
        const dup = _slots.some((s, i) => i !== _active && s.fileName === name && s.storage === slot.storage);
        if (dup || (slot.storage === 'local' && SlotStorage.localKeyExists(name))) {
            const nameEl = document.getElementById('metaFile');
            if (nameEl) nameEl.value = slot.fileName;
            SlotStorage.toast('Duplicate name exists.'); return false;
        }
        SlotStorage.migrateLocalKey(slot.fileName, name, { allowOverwrite }); // 로컬 파일 rename
        SlotStorage.migrateSlotKey(slot.fileName, name);                          // slot_ 작업본도 rename (고아 방지)
        SlotStorage.migrateChatKey(slot.fileName, name);                          // chat_ 기록도 rename
        slot.fileName = name; slot.isDirty = true;
        _saveMeta();
        const nameEl = document.getElementById('metaFile');
        if (nameEl) nameEl.value = name;
        _updateLocDisplay(slot); _display();
        if (!silent) SlotStorage.toast(`Renamed -> ${name}`);
        return true;
    }

    // ── Delete ────────────────────────────────────────────────
    async function deleteSlot(name) {
        SlotStorage.removeLocal(name);
        SlotStorage.removeSlot(name);
        SlotStorage.removeChat(name);
        // 슬롯 연동 업로드 이미지 가비지 삭제
        try { fetch('/api/delete-uploads', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({slot:name}) }); } catch(e) {}
        const idx = _slots.findIndex(s => s.fileName === name);
        if (idx < 0) return;
        _editorStateCache.delete(_slots[idx].slotIndex);
        const wasActive = idx === _active;
        _slots.splice(idx, 1);
        if (_active > idx) _active--;
        else if (wasActive) _active = Math.max(0, _active - 1);
        _winOk();
        if (_slots.length === 0) { _active = -1; Editor.setText(''); }
        else if (wasActive || idx <= _active) {
            _switching = true; _syncHeader(_slots[_active]); await _loadText(_slots[_active]); _editorStateCache.delete(_slots[_active].slotIndex); _apply(_slots[_active], { skipSetText: true });
        }
        _display(); _saveMeta();
    }

    // ── Misc ──────────────────────────────────────────────────
    function setActiveStorage(storage) {
        const s = String(storage || '').trim().toLowerCase();
        if (!s || _active < 0 || !_slots[_active]) return;
        _slots[_active].storage = s; _saveMeta();
        const funcEl = document.getElementById('metaFunc');
        if (funcEl) { funcEl.textContent = s; funcEl.classList.toggle('is-usekit', s === 'usekit'); }
        _updateLocDisplay(_slots[_active]); _display();
    }

    function loadSlot(visNum) { _switchTo(_winStart + (_clamp(Number(visNum), 1, WIN) - 1)); }

    let _sliding = false;
    async function slideActive(delta) {
        if (_sliding || _slots.length <= 1) return;
        const dir = Number(delta) || 0;
        if (!dir) return;
        _sliding = true;
        const next = _clamp(_active + dir, 0, _slots.length - 1);
        if (next !== _active) {
            const posInWin = _active - _winStart;
            if (dir > 0 && posInWin === WIN - 1) _winStart = Math.min(_winStart + 1, Math.max(0, _slots.length - WIN));
            else if (dir < 0 && posInWin === 0)  _winStart = Math.max(_winStart - 1, 0);
            const prev = _switching; _switching = false; _capture(); _switching = true; // await 중 switching 유지
            _active = next;
            const slot = _slots[_active];
            _syncHeader(slot); await _loadText(slot); _editorStateCache.delete(slot.slotIndex); _apply(slot, { skipSetText: true }); _display(); _saveMeta();
        }
        _sliding = false;
    }

    async function activateByIdx(absIdx, textOverride, opts) {
        if (_autoTimer) { clearTimeout(_autoTimer); _autoTimer = null; }
        _capture(); _switching = true; _active = absIdx; _centerWin(); // await 중 switching 유지
        const slot = _slots[_active];
        _syncHeader(slot);
        if (textOverride !== undefined) {
            _editorStateCache.delete(slot.slotIndex); // _capture가 방금 세운 캐시 제거
            slot.state = null;                        // snapshot도 초기화
            if (!opts?.keepDirty) slot.isDirty = false; // 서버/로컬 버전 로드 → dirty 해제
            Editor.setText(textOverride);
        } else {
            await _loadText(slot);
            _editorStateCache.delete(slot.slotIndex); // 텍스트 로드 후 캐시 클리어
        }
        _apply(slot, { skipSetText: true });
        _display(); _saveMeta();
    }

    function switchToFileName(name, callback) {
        const idx = _slots.findIndex(s => s.fileName === name);
        if (idx < 0) { UI?.showToast?.(`Not found: ${name}`, 1000); return; }
        activateByIdx(idx);
        if (callback) requestAnimationFrame(() => requestAnimationFrame(callback));
    }

    // ── Popup API ─────────────────────────────────────────────
    function _makePopupApi() {
        return {
            getSlots:      () => _slots.map(s => ({ ...s })),
            getActiveIdx:  () => _active,
            activateByIdx: (idx, text, opts) => activateByIdx(idx, text, opts),
            activateLocalByName: async (name) => {
                const existIdx = _slots.findIndex(s => s.storage === 'local' && s.fileName === name);
                if (!SlotStorage.localKeyExists(name)) { SlotStorage.toast(`Not found: ${name}`); return; }
                let stored = SlotStorage.readLocal(name) || await SlotStorage.readLocalAsync(name);
                if (!stored) { SlotStorage.toast(`Not found: ${name}`); return; }
                // 로컬 저장본으로 slot_ key 덮어쓰기
                SlotStorage.writeSlot(name, { text: stored.text || '', timestamp: stored.timestamp || Date.now() });
                if (existIdx >= 0) {
                    const si = _slots[existIdx].slotIndex;
                    if (_autoTimer) { clearTimeout(_autoTimer); _autoTimer = null; }
                    _capture();
                    _active = existIdx;
                    _centerWin();
                    _syncHeader(_slots[_active]);
                    _editorStateCache.delete(si);
                    _slots[_active].isDirty = false;
                    _slots[_active].state = null;
                    Editor.setText(stored.text || '');
                    // skipSetText: else분기의 setText('')가 방금 세팅한 텍스트를 덮어쓰지 않도록
                    _apply(_slots[_active], { skipSetText: true });
                    _display(); _saveMeta();
                    return;
                }
                const maxIdx = _slots.length > 0 ? Math.max(..._slots.map(s => s.slotIndex)) : -1;
                const ns = { slotIndex: maxIdx + 1, storage: 'local', fileName: name, isDirty: false, usekitPath: '', state: null };
                activateByIdx(_insertSlot(ns, _slots.length), stored.text || '');
            },
            addSlot: (slotObj) => {
                const maxIdx = _slots.length > 0 ? Math.max(..._slots.map(s => s.slotIndex)) : -1;
                const ns = { slotIndex: maxIdx + 1, usekitPath: '', ...slotObj };
                const at = _active >= 0 && _active < _slots.length - 1 ? _active + 1 : _slots.length;
                // 텍스트가 있으면 slot_ 키에 캐시 → _loadText가 나중에 읽을 수 있음
                if (slotObj.data?.text !== undefined && slotObj.fileName) {
                    SlotStorage.writeSlot(slotObj.fileName, {
                        text: slotObj.data.text,
                        timestamp: slotObj.data.timestamp || Date.now(),
                    });
                }
                return _insertSlot(ns, at);
            },
            deleteLocalSlot: (name) => deleteSlot(name),
            deleteUsekitFile: async (item) => {
                const ok = await window.IOSlotUsekitTab?.deleteFile(item.path);
                if (!ok) return false;
                [..._slots.map((s,i) => i).filter(i => _slots[i].usekitPath === item.path)].reverse()
                    .forEach(i => {
                        const wasActive = i === _active;
                        _editorStateCache.delete(_slots[i].slotIndex);
                        // 슬롯 연동 업로드 이미지 가비지 삭제
                        try { fetch('/api/delete-uploads', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({slot:_slots[i].fileName}) }); } catch(e) {}
                        SlotStorage.removeSlot(_slots[i].fileName);
                        _slots.splice(i, 1);
                        if (wasActive) _active = Math.min(i, _slots.length - 1);
                        else if (_active > i) _active--;
                    });
                _winOk();
                if (_slots.length === 0) { _active = -1; Editor.setText(''); }
                else if (_active >= 0) { _switching = true; _syncHeader(_slots[_active]); await _loadText(_slots[_active]); _editorStateCache.delete(_slots[_active].slotIndex); _apply(_slots[_active], { skipSetText: true }); }
                _saveMeta(); _display(); return true;
            },
            newFile,
            closeSlotAt: (idx) => closeSlotAt(idx),
            moveSlot: (from, to) => _moveSlot(from, to),
        };
    }

    function openLoadPopup() { SlotPopup.open(_makePopupApi()); }
    function openSavePopup() {
        SavePopup.open({
            getCurrentSlotInfo: () => _slots[_active] ? { ..._slots[_active] } : {},
            renameAndSaveLocal: (name) => {
                if (!_slots[_active]) return false;
                const oldName = _slots[_active].fileName;
                SlotStorage.migrateSlotKey(oldName, name); // slot_ 작업본 rename (고아 방지)
                _slots[_active].fileName   = name;
                _slots[_active].storage    = 'local'; // usekit→local 전환 시 storage 갱신
                _slots[_active].usekitPath = '';       // usekit 경로 초기화
                _saveMeta();
                _syncHeader(_slots[_active]);
                return _saveLocal({ silent: false });
            },
            saveUsekit: (sandboxPath, newName) => {
                if (!_slots[_active]) return;
                const _prevStorage = _slots[_active].storage;
                const _prevPath    = _slots[_active].usekitPath;
                if (newName) {
                    SlotStorage.migrateSlotKey(_slots[_active].fileName, newName); // slot_ 작업본 rename (고아 방지)
                    _slots[_active].fileName = newName;
                }
                _slots[_active].usekitPath = sandboxPath;
                _slots[_active].storage    = 'usekit';
                _saveMeta();
                _saveUsekit({ silent: false, _prevStorage, _prevPath });
                _syncHeader(_slots[_active]);
            },
            setUsekitPath: (absPath) => {
                if (_slots[_active]) { _slots[_active].usekitPath = absPath; _saveMeta(); }
            },
        });
    }

    // ── Init ──────────────────────────────────────────────────
    function init() {
        const meta    = SlotStorage.loadMetadata();
        const hasMeta = !!localStorage.getItem(SlotStorage.META_KEY);

        if (meta.slots?.length > 0) {
            _slots = meta.slots.map(m => ({
                slotIndex:  m.slotIndex,
                storage:    m.storage    || 'local',
                fileName:   m.fileName,
                isDirty:    m.isDirty    || false,
                usekitPath: m.usekitPath || '',
                state:      m.state      || null,
            }));
            _active   = _clamp(meta.activeSlotIndex || 0, 0, _slots.length - 1);
            _winStart = _clamp(meta.windowStart     || 0, 0, Math.max(0, _slots.length - WIN));
            const uiToRestore = meta.uiState || (meta.slots?.[meta.activeSlotIndex || 0]?.state?.ui) || null;
            if (uiToRestore && window.ActiveState?.setUI)
                Object.keys(uiToRestore).forEach(k => ActiveState.setUI(k, uiToRestore[k]));
            else if (window.ActiveState?.setUI)
                ActiveState.setUI('uiMode', 'quick');
        } else if (!hasMeta) {
            if (window.ActiveState?.setUI) ActiveState.setUI('uiMode', 'quick');
            const names = SlotStorage.listLocalSlotNames();
            if (names.length > 0) {
                _slots = names.map((n, i) => ({
                    slotIndex: i, storage: 'local', fileName: n,
                    isDirty: false, usekitPath: '', state: null,
                }));
                _active = 0; _winStart = 0; _saveMeta();
            }
        } else {
            _slots = []; _active = -1; _winStart = 0;
        }

        if (_active < 0) {
            // URL에 ?file=/?data= 있으면 _handleUrlParams가 슬롯 추가하므로 여기선 skip
            const _p = new URLSearchParams(location.search);
            const _hasUrlFile = !!(_p.get('file') || _p.get('data'));
            if (!_hasUrlFile) {
                // 슬롯 없으면 빈 신규 파일 하나 생성
                requestAnimationFrame(() => newFile());
            }
        } else if (_active >= 0 && _slots[_active]) {
            const slot = _slots[_active];
            _syncHeader(slot);
            if (slot.state?.edit?.lkMode && window.ActiveState?.setEdit)
                ActiveState.setEdit('lkMode', !!slot.state.edit.lkMode);
            // await로 텍스트 확실히 세팅 후 _apply
            _switching = true; // _apply 전까지 switching 유지 → allowKeyboard 오발화 방지
            _loadText(slot).then(() => {
                _editorStateCache.delete(slot.slotIndex);
                _apply(slot, { skipSetText: true }); UIStats.updateStatsNow();
            });
        }

        _display(); _bindEvents(); _bindEditorChange();
        requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(() =>
            requestAnimationFrame(() => requestAnimationFrame(() => { _initDone = true; }))
        )));
        _initPing();
        // 고아 slot_ 파일 정리 — 메타에 없는 slot_* 파일 백그라운드 제거
        setTimeout(() => {
            const knownNames = new Set(_slots.map(s => s.fileName));
            const orphans = SlotStorage.listSlotFileNames().filter(n => !knownNames.has(n));
            if (orphans.length > 0) {
                console.log('[SlotManager] orphan slot files:', orphans);
                orphans.forEach(n => SlotStorage.removeSlot(n));
            }
            // 고아 chat_ 파일도 정리
            const chatOrphans = SlotStorage.listChatFileNames().filter(n => !knownNames.has(n));
            if (chatOrphans.length > 0) {
                console.log('[SlotManager] orphan chat files:', chatOrphans);
                chatOrphans.forEach(n => SlotStorage.removeChat(n));
            }
            // 실패했던 swap 파일도 함께 재시도
            if (SlotStorage.sweepSwapFiles) SlotStorage.sweepSwapFiles();
        }, 2000);
    }

    function _initPing() {
        fetch('/api/ping', { signal: AbortSignal.timeout(2000) })
            .then(r => r.json())
            .then(j => {
                if (!j?.ok) return;
                window._usekitPing = j; _usekitBase = j.usekit_base || '';
                const relDir = (j.default_usekit_rel_dir || '_tmp').replace(/\/?$/, '');
                let changed = false;
                _slots.forEach(s => {
                    if (s.storage === 'usekit' && !s.usekitPath) {
                        const fn = s.fileName;
                        const fnWithExt = fn.includes('.') ? fn : fn + '.txt';
                        s.usekitPath = `/${relDir}/${fnWithExt}`; changed = true;
                    }
                });
                if (changed) _saveMeta();
                if (_active >= 0 && _slots[_active]) _updateLocDisplay(_slots[_active]);

                // ── URL 파라미터 처리 (?file= / ?data=) ──────────────
                _handleUrlParams(j);
            }).catch(() => {});
    }

    // URL ?file=&data= 제거 — 처리 완료 후 리로드 시 재생성 방지
    function _cleanUrlParams() {
        try { history.replaceState(null, '', location.pathname); } catch(e) {}
    }

    function _handleUrlParams(ping) {
        const params  = new URLSearchParams(location.search);
        const fileArg = params.get('file');   // e.g. "_tmp/scratch.txt" or "/storage/.../foo.py"
        const dataArg = params.get('data');   // base64 encoded initial text

        if (!fileArg && !dataArg) return;

        // initial_data 디코딩
        let initialText = null;
        if (dataArg) {
            try {
                const b64 = dataArg.replace(/-/g, '+').replace(/_/g, '/');
                initialText = decodeURIComponent(escape(atob(b64)));
            } catch (e) {
                console.warn('[SlotManager] data param decode failed', e);
            }
        }

        if (!fileArg) return; // data만 있는 경우는 현재 슬롯에 inject 안 함 (보존성)

        // ── 이름 정규화 ─────────────────────────────────────────
        // 다른 슬롯과 규칙 통일: fileName = 확장자 제외, 확장자는 usekitPath에만 포함
        const fileNameWithExt = fileArg.split('/').pop();  // "scratch.txt"
        const slotName        = fileNameWithExt.replace(/\.[a-zA-Z0-9]{1,6}$/, '');  // "scratch"

        // ── usekitPath 결정 ────────────────────────────────────
        const isAbs = fileArg.startsWith('/');
        let usekitPath;
        if (isAbs) {
            usekitPath = fileArg;
        } else if (fileArg.includes('/')) {
            usekitPath = '/' + fileArg.replace(/^\/+/, '');
        } else {
            const relDir = (ping?.default_usekit_rel_dir || '_tmp').replace(/\/?$/, '');
            usekitPath = `/${relDir}/${fileNameWithExt}`;
        }

        // ── 이미 열려있으면 아무것도 안 함 ──────────────────────
        // (메타에서 복원된 활성 슬롯 / 사용자가 이미 열어둔 슬롯을 보호)
        const _normForCmp = (p) => p ? '/' + String(p).replace(/^\/+/, '') : '';
        const pathNorm    = _normForCmp(usekitPath);
        const existing = _slots.findIndex(s =>
            s.usekitPath === pathNorm ||
            s.usekitPath === usekitPath ||
            s.fileName   === slotName
        );
        if (existing >= 0) { _cleanUrlParams(); return; }

        // ── default scratch이고 슬롯이 이미 있으면 무시 ──────────
        // u.editor() 인자 없이 재호출 시 기존 작업 보호
        const defaultFile = ping?.default_file || '_tmp/scratch.txt';
        if (fileArg === defaultFile && _slots.length > 0) {
            _cleanUrlParams(); return;
        }

        // ── 새 슬롯 추가 (완전 빈 상태이거나 해당 파일이 처음 등장) ──
        const maxIdx = _slots.length > 0 ? Math.max(..._slots.map(s => s.slotIndex)) : -1;
        const slot = {
            slotIndex:  maxIdx + 1,
            storage:    'usekit',
            fileName:   slotName,           // 확장자 제외
            isDirty:    !!initialText,
            usekitPath,                     // 확장자 포함
            state:      null,
        };

        _slots.push(slot);
        _active = _slots.length - 1;
        _winOk(); _saveMeta();
        _syncHeader(slot);
        _cleanUrlParams();

        if (initialText !== null) {
            // 서버에 파일 없음 + initialText → 에디터에 직접 주입
            requestAnimationFrame(() => {
                if (window.Editor?.setText) Editor.setText(initialText);
                _initDone = true;
                _display(); _updateLocDisplay(slot); UIStats.updateStatsNow?.();
            });
        } else {
            // 서버에 파일 있음 → 일반 로드
            _switching = true;
            _loadText(slot).then(() => {
                _editorStateCache.delete(slot.slotIndex);
                _apply(slot, { skipSetText: true }); UIStats.updateStatsNow?.();
            });
        }
    }

    // ── Move slot (shared by tab drag + popup drag) ──────────
    function _moveSlot(from, to) {
        if (from === to || from < 0 || to < 0 || from >= _slots.length || to >= _slots.length) return;
        const item = _slots.splice(from, 1)[0];
        _slots.splice(to, 0, item);
        if (_active === from) _active = to;
        else if (from < _active && to >= _active) _active--;
        else if (from > _active && to <= _active) _active++;
        _winOk(); _saveMeta(); _display();
    }

    // ── Event binding ─────────────────────────────────────────
    function _bindEvents() {
        const _drag = { timer: null, active: false, didDrag: false, fromAbs: -1, el: null };
        function _resetDrag() {
            if (_drag.timer) { clearTimeout(_drag.timer); _drag.timer = null; }
            _drag.active = false; _drag.didDrag = false; _drag.fromAbs = -1;
            if (_drag.el) _drag.el.classList.remove('slot-dragging');
            _drag.el = null;
        }
        for (let i = 1; i <= WIN; i++) {
            const el = document.getElementById(`slot${i}`);
            if (!el || el.dataset.smBound) continue;
            el.dataset.smBound = '1';
            el.addEventListener('click', (ev) => {
                if (_drag.active) return;
                if (_drag.didDrag) { _resetDrag(); return; }
                const btn = ev.target?.closest?.('.slot-close');
                if (btn) { ev.preventDefault(); ev.stopPropagation(); closeCurrentSlot(); return; }
                const abs = parseInt(el.dataset.absIndex);
                if (abs >= 0) loadSlot(i); else newFile();
            });
            const LONG_MS = 320, MOVE_PX = 10;
            function getXY(e) {
                if (e.touches?.[0])        return { x: e.touches[0].clientX,        y: e.touches[0].clientY };
                if (e.changedTouches?.[0]) return { x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY };
                return { x: e.clientX, y: e.clientY };
            }
            let _downXY = null;
            function onDown(ev) {
                if (ev.target?.closest?.('.slot-close')) return;
                _resetDrag(); _downXY = getXY(ev);
                _drag.timer = setTimeout(() => {
                    const abs = parseInt(el.dataset.absIndex);
                    if (!(abs >= 0)) { _resetDrag(); return; }
                    _drag.active = true; _drag.didDrag = false;
                    _drag.fromAbs = abs; _drag.el = el;
                    el.classList.add('slot-dragging');
                    try { navigator.vibrate?.(15); } catch(e) {}
                }, LONG_MS);
            }
            function onMove(ev) {
                if (!_downXY) return;
                const p = getXY(ev);
                const dx = Math.abs(p.x - _downXY.x), dy = Math.abs(p.y - _downXY.y);
                if (!_drag.active && (dx > MOVE_PX || dy > MOVE_PX)) { _resetDrag(); _downXY = null; return; }
                if (!_drag.active) return;
                ev.preventDefault();
                const hit = document.elementFromPoint(p.x, p.y);
                const box = hit?.closest?.('.slot-box');
                if (!box) return;
                const toAbs = parseInt(box.dataset.absIndex);
                if (toAbs >= 0 && toAbs !== _drag.fromAbs) { _drag.didDrag = true; _moveSlot(_drag.fromAbs, toAbs); _drag.fromAbs = toAbs; }
            }
            function onUp() { _downXY = null; _resetDrag(); }
            el.addEventListener('touchstart',  onDown, { passive: true });
            window.addEventListener('touchmove',   onMove, { passive: false });
            window.addEventListener('touchend',    onUp,   { passive: true });
            window.addEventListener('touchcancel', onUp,   { passive: true });
            el.addEventListener('mousedown', onDown);
            window.addEventListener('mousemove', onMove);
            window.addEventListener('mouseup', onUp);
        }
        let _lastArrow = 0;
        const _arrow = dir => () => {
            const now = Date.now(); if (now - _lastArrow < 280) return; _lastArrow = now; slideActive(dir);
        };
        const L = document.getElementById('slotArrowLeft');
        const R = document.getElementById('slotArrowRight');
        if (L && !L.dataset.smBound) { L.dataset.smBound = '1'; L.addEventListener('click', _arrow(-1)); }
        if (R && !R.dataset.smBound) { R.dataset.smBound = '1'; R.addEventListener('click', _arrow(1)); }
    }

    function _bindEditorChange() {
        Editor.on('changes', _markDirty);
        const _emergencySave = () => {
            if (_active < 0 || !_slots[_active]) return;
            const slot = _slots[_active];
            // storage와 무관하게 OPFS(slot_xxx)에 항상 저장 (종료 직전 편집 보존)
            SlotStorage.writeSlot(slot.fileName, { text: Editor.getText(), timestamp: Date.now() });
            _saveMeta();
        };
        document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') _emergencySave(); });
        window.addEventListener('pagehide',     _emergencySave);
        window.addEventListener('beforeunload', _emergencySave);
    }

    // ── Public API ────────────────────────────────────────────
    function slotPrev()  { if (_active > 0) _switchTo(_active - 1); else UI?.showToast?.('First slot', 800); }
    function slotNext()  { if (_active < _slots.length - 1) _switchTo(_active + 1); else openLoadPopup(); }
    function slotFirst() { if (_slots.length > 0) _switchTo(0); }
    function slotLast()  { if (_slots.length > 0) _switchTo(_slots.length - 1); }
    function getActiveIndex()      { return _active; }
    function getSlotCount()        { return _slots.length; }
    function getCurrentSlot()      { return _slots[_active]?.fileName || ''; }
    function getCurrentSlotInfo()  { return _slots[_active] ? { ..._slots[_active] } : null; }
    function isCurrentSlotDirty()  { return !!_slots[_active]?.isDirty; }
    function isSwitchingSlot()     { return _switching; }
    function setUsekitPathForActive(path) {
        if (_slots[_active]) { _slots[_active].usekitPath = path; _saveMeta(); _updateLocDisplay(_slots[_active]); }
    }

    return {
        init,
        loadSlot, slideActive,
        slotPrev, slotNext, slotFirst, slotLast,
        getActiveIndex, getSlotCount,
        newFile, save, closeCurrentSlot, closeSlotAt, renameCurrentSlot,
        setActiveStorage, deleteSlot,
        activateByIdx, switchToFileName,
        openLoadPopup, openSavePopup,
        getCurrentSlot, getCurrentSlotInfo, isCurrentSlotDirty,
        isSwitchingSlot,
        setUsekitPathForActive, setUsekitBase,
        saveUIState,
        display: _display,
        moveSlot: _moveSlot,
    };
})();

window.SlotManager = SlotManager;
