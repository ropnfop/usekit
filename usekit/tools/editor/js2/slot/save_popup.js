// save_popup.js
// Save modal: LOCAL tab + USEKIT tab
// Depends on: SlotStorage, Editor

const SavePopup = (function () {
    'use strict';

    function _fmtSize(bytes) {
        if (!bytes) return '';
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes/1024).toFixed(1)}K`;
        return `${(bytes/1024/1024).toFixed(1)}M`;
    }

    function open(api) {
        const modal     = document.getElementById('saveModal');
        const listEl    = document.getElementById('saveModalList');
        const pathEl    = document.getElementById('saveModalPath');
        const slotEl    = document.getElementById('saveModalSlot');
        const dirEl     = document.getElementById('saveModalDir');
        const dirRow    = document.getElementById('saveModalDirRow');
        const nameEl    = document.getElementById('saveModalName');
        const extEl     = document.getElementById('saveModalExt');
        const btnX      = document.getElementById('btnSaveModalClose');
        const btnCncl   = document.getElementById('btnSaveModalCancel');
        const btnOk     = document.getElementById('btnSaveModalOk');
        const tabLocal  = document.getElementById('saveTabLocal');
        const tabUsekit = document.getElementById('saveTabUsekit');
        if (!modal || !nameEl || !extEl) return;

        const info = api.getCurrentSlotInfo?.() || {};
        let currentTab = (info.storage === 'usekit') ? 'usekit' : 'local';

        // Close
        function closeModal() {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        }

        if (!modal.dataset.saveBound) {
            modal.dataset.saveBound = '1';
            modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
            btnX?.addEventListener('click', closeModal);
            btnCncl?.addEventListener('click', closeModal);
            document.addEventListener('keydown', e => {
                if (modal.style.display !== 'none' && e.key === 'Escape') closeModal();
            });
        }

        // Tab switch
        function switchTab(tab) {
            currentTab = tab;
            tabLocal?.classList.toggle('active',  tab === 'local');
            tabUsekit?.classList.toggle('active', tab === 'usekit');
            if (dirRow) dirRow.style.display = (tab === 'usekit') ? '' : 'none';
            // LOCAL탭도 Ext 행 표시
            const extRow = extEl?.closest('.save-input-row');
            if (extRow) extRow.style.display = '';
            initInputs();
            render();
        }

        // Init inputs
        function initInputs() {
            const info = api.getCurrentSlotInfo?.() || {};
            if (currentTab === 'usekit') {
                const upath = info.usekitPath || '';
                const fname = upath ? upath.split('/').pop() : (info.fileName || '');
                const m = fname.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
                nameEl.value = m ? m[1] : (fname || info.fileName || '');
                extEl.value  = m ? m[2] : 'txt';
                extEl.classList.toggle('is-none', false);
                const nav = window._usekitNav;
                const curPath = nav?.currentPath || '/_tmp/';
                if (pathEl) pathEl.textContent = curPath;
                if (dirEl)  dirEl.value = curPath;
                if (slotEl) slotEl.textContent = '';
            } else {
                const fname = info.fileName || '';
                const m = fname.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
                nameEl.value = m ? m[1] : fname;
                let ext = m ? m[2] : '';
                if (!ext && info.usekitPath) {
                    const em = info.usekitPath.match(/\.([a-zA-Z0-9]{1,6})$/);
                    if (em) ext = em[1];
                }
                extEl.value = ext || 'txt';
                extEl.classList.toggle('is-none', false);
                if (slotEl) slotEl.textContent = fname ? '-> ' + fname : '';
                if (pathEl) pathEl.textContent = (SlotStorage.getMode?.() || 'local') + '://' + SlotStorage.PREFIX + fname;
            }
        }

        // Highlight overwrite
        function _highlightOverwrite() {
            const name = nameEl.value.trim();
            listEl.querySelectorAll('.modal-item').forEach(div => {
                div.classList.toggle('save-item-overwrite', !!name && div.dataset.name === name);
            });
        }
        nameEl.removeEventListener('input', _highlightOverwrite);
        nameEl.addEventListener('input', _highlightOverwrite);

        // Render
        async function render() {
            listEl.innerHTML = '';
            if (currentTab === 'usekit') await _renderUsekitList();
            else _renderLocalList();
        }

        function _renderLocalList() {
            const items = [];
            const names = SlotStorage.listLocalSlotNames();
            for (const name of names) {
                if (!name || name.startsWith('usekitmeta_') || name === '__meta__') continue;
                const meta = SlotStorage.getLocalOnlyMeta(name);
                items.push({ name, timestamp: meta.timestamp || 0, chars: meta.chars || 0 });
            }
            items.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            const curName = nameEl.value.trim();
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'modal-item' + (item.name === curName ? ' save-item-overwrite' : '');
                div.dataset.name = item.name;
                const meta = [];
                if (item.timestamp) meta.push(SlotStorage.formatTime(item.timestamp));
                if (item.chars)     meta.push(item.chars + 'ch');
                div.innerHTML = '<div class="item-body"><div class="item-name">' + item.name + '</div><div class="item-meta">' + meta.join(' · ') + '</div></div>';
                div.addEventListener('click', () => {
                    const m = item.name.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
                    nameEl.value = m ? m[1] : item.name;
                    if (m && extEl) extEl.value = m[2];
                    _highlightOverwrite(); nameEl.focus();
                });
                listEl.appendChild(div);
            });
            if (!items.length) listEl.innerHTML = '<div style="padding:16px;opacity:0.4;text-align:center;font-size:0.85rem">(no saved files)</div>';
        }

        async function _renderUsekitList() {
            if (!window.IOSlotUsekitTab?.buildItems) {
                listEl.innerHTML = '<div style="padding:16px;opacity:0.4;font-size:0.85rem">USEKIT not available</div>';
                return;
            }
            listEl.innerHTML = '<div style="padding:10px;opacity:0.5;font-size:0.8rem">Loading...</div>';

            const result = await window.IOSlotUsekitTab.buildItems({ filterText: '' });
            const items  = result.items || [];
            if (pathEl) pathEl.textContent = result.pathText || '/_tmp/';

            listEl.innerHTML = '';
            const curName = nameEl.value.trim();

            items.forEach(item => {
                const div = document.createElement('div');

                // nav_parent: 상위 폴더
                if (item.type === 'nav_parent') {
                    div.className = 'usekit-nav-row' + (item.disabled ? ' disabled' : '');
                    div.innerHTML = '<span class="usekit-nav-icon">↑</span><span class="usekit-nav-label">Parent folder</span>';
                    if (!item.disabled) {
                        div.addEventListener('click', () => {
                            if (window._usekitNav) { window._usekitNav.currentPath = item.name; window._usekitNav._skipFetchOnce = false; }
                            if (dirEl) dirEl.value = item.name;
                            _renderUsekitList();
                        });
                    }
                    listEl.appendChild(div); return;
                }

                // nav_current: 현재 폴더 표시
                if (item.type === 'nav_current') {
                    div.className = 'usekit-nav-row current';
                    const parts = item.name.replace(/\/$/, '').split('/').filter(Boolean);
                    const last   = parts.pop() || '/';
                    const parent = parts.length ? parts.join('/') + '/' : '';
                    div.innerHTML = '<span class="usekit-folder-icon">📁</span><span class="usekit-nav-label"><span style="opacity:0.5">/' + parent + '</span><strong>' + last + '</strong></span>';
                    listEl.appendChild(div); return;
                }

                // separator
                if (item.type === 'separator') {
                    div.className = 'usekit-separator';
                    listEl.appendChild(div); return;
                }

                // info: 빈/오류
                if (item.type === 'info') {
                    div.className = 'usekit-info-row';
                    div.textContent = item.name;
                    listEl.appendChild(div); return;
                }

                // dir: 폴더
                if (item.type === 'dir') {
                    div.className = 'modal-item usekit-dir';
                    div.innerHTML = '<div class="item-left" style="font-size:1.1rem;">📁</div><div class="item-body"><div class="item-name">' + item.name + '</div></div>';
                    div.addEventListener('click', () => {
                        if (window._usekitNav) { window._usekitNav.currentPath = item.path + '/'; window._usekitNav._skipFetchOnce = false; }
                        if (dirEl) dirEl.value = item.path + '/';
                        _renderUsekitList();
                    });
                    listEl.appendChild(div); return;
                }

                // file: 클릭 → 파일명/확장자 자동 채우기
                if (item.type === 'file') {
                    const m = item.name.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
                    const baseName = m ? m[1] : item.name;
                    div.className = 'modal-item' + (baseName === curName ? ' save-item-overwrite' : '');
                    div.dataset.name = baseName;
                    const meta = [];
                    if (item.meta?.timestamp) meta.push(SlotStorage.formatTime(item.meta.timestamp));
                    if (item.meta?.size)      meta.push(_fmtSize(item.meta.size));
                    div.innerHTML = '<div class="item-left" style="font-size:1rem;">📄</div><div class="item-body"><div class="item-name">' + item.name + '</div><div class="item-meta">' + meta.join(' · ') + '</div></div>';
                    div.addEventListener('click', () => {
                        nameEl.value = baseName;
                        if (m) extEl.value = m[2];
                        _highlightOverwrite(); nameEl.focus();
                    });
                    listEl.appendChild(div); return;
                }
            });
        }

        // Save action
        function doSave() {
            // DOM 활성 탭 상태로 currentTab 재동기화 (클로저 불일치 방어)
            if (tabLocal?.classList.contains('active'))  currentTab = 'local';
            if (tabUsekit?.classList.contains('active')) currentTab = 'usekit';
            let name = SlotStorage.sanitizeFileName(nameEl.value.trim());
            if (!name) { SlotStorage.toast('Enter a file name'); nameEl.focus(); return; }
            const extRaw = extEl.value.trim();
            const ext = (extRaw === '(NONE)' || extRaw === '') ? '' : extRaw.replace(/^\./, '');
            const metaExtEl = document.getElementById('metaExt');
            if (metaExtEl) metaExtEl.value = ext;

            // name에 이미 .ext 포함된 경우 중복 방지
            const nameSuffix = '.' + ext;
            if (name.toLowerCase().endsWith(nameSuffix.toLowerCase())) {
                name = name.slice(0, name.length - nameSuffix.length);
            }

            if (currentTab === 'usekit') {
                const nav = window._usekitNav;
                const folderRaw = (dirEl?.value?.trim() || nav?.currentPath || '/_tmp/');
                const folder = folderRaw.replace(/\/?$/, '');
                const sandboxPath = folder + '/' + name + (ext ? '.' + ext : '');
                api.saveUsekit?.(sandboxPath, name);
            } else {
                const localName = ext ? name + '.' + ext : name;
                api.renameAndSaveLocal?.(localName);
            }
            closeModal();
        }

        if (btnOk) btnOk.onclick = doSave;

        // 탭 onclick: 매 open()마다 재바인딩 + 핸들러 교체 (클로저·누적 방지)
        if (tabLocal) {
            tabLocal._swHandler && tabLocal.removeEventListener('click', tabLocal._swHandler);
            tabLocal._swHandler = () => switchTab('local');
            tabLocal.addEventListener('click', tabLocal._swHandler);
        }
        if (tabUsekit) {
            tabUsekit._swHandler && tabUsekit.removeEventListener('click', tabUsekit._swHandler);
            tabUsekit._swHandler = () => switchTab('usekit');
            tabUsekit.addEventListener('click', tabUsekit._swHandler);
        }

        // 목록 접힘/펼침 + 화살표 네비게이션
        const listNav     = document.getElementById('saveListNav');
        const btnListUp   = document.getElementById('btnSaveListUp');
        const btnListDown = document.getElementById('btnSaveListDown');
        const listNavInfo = document.getElementById('saveListNavInfo');
        let _listFolded = false;
        let _listCursor = -1;

        function _getListItems() {
            return Array.from(listEl.querySelectorAll('.modal-item'));
        }
        function _updateNavInfo() {
            const items = _getListItems();
            if (!items.length) { if (listNavInfo) listNavInfo.textContent = '0 files'; return; }
            if (listNavInfo) listNavInfo.textContent = `${_listCursor + 1} / ${items.length}`;
        }
        function _foldList() {
            _listFolded = true;
            if (listEl) listEl.style.display = 'none';
            if (listNav) listNav.style.display = '';
            _updateNavInfo();
        }
        function _unfoldList() {
            _listFolded = false;
            if (listEl) listEl.style.display = '';
            if (listNav) listNav.style.display = 'none';
        }
        function _navList(dir) {
            const items = _getListItems();
            if (!items.length) return;
            _listCursor = Math.max(0, Math.min(items.length - 1, _listCursor + dir));
            const item = items[_listCursor];
            if (item) {
                const raw = item.dataset.name || '';
                const m = raw.match(/^(.+)\.([a-zA-Z0-9]{1,6})$/);
                if (nameEl) { nameEl.value = m ? m[1] : raw; _highlightOverwrite(); }
                if (m && extEl) extEl.value = m[2];
            }
            _updateNavInfo();
        }

        if (btnListUp   && !btnListUp.dataset.navBound)   { btnListUp.dataset.navBound   = '1'; btnListUp.addEventListener('click',   e => { e.preventDefault(); _navList(-1); }); }
        if (btnListDown && !btnListDown.dataset.navBound) { btnListDown.dataset.navBound = '1'; btnListDown.addEventListener('click', e => { e.preventDefault(); _navList(1);  }); }

        // 인풋 포커스 시 목록 접힘
        function _onInputFocus() { _listCursor = -1; _inputFocused = true; _foldList(); }
        function _onInputBlur()  {
            _inputFocused = false;
            setTimeout(() => { if (!_inputFocused) _unfoldList(); }, 200);
        }
        let _inputFocused = false;
        [nameEl, extEl, dirEl].forEach(el => {
            if (!el || el.dataset.foldBound) return;
            el.dataset.foldBound = '1';
            el.addEventListener('focus', _onInputFocus);
            el.addEventListener('blur',  _onInputBlur);
        });

        // Ext 커스텀 드롭다운
        const extDropBtn  = document.getElementById('saveExtDropBtn');
        const extDropList = document.getElementById('saveExtDropList');
        if (extDropBtn && extDropList) {
            // 매 open()마다 재바인딩 (extBound 가드 제거)
            if (extDropBtn._extHandler) extDropBtn.removeEventListener('click', extDropBtn._extHandler);
            extDropBtn._extHandler = e => {
                e.stopPropagation();
                const isOpen = extDropList.style.display !== 'none';
                if (isOpen) {
                    extDropList.style.display = 'none';
                    return;
                }
                // position:fixed 기준 버튼 위치 계산
                const rect = extDropBtn.getBoundingClientRect();
                const spaceBelow = window.innerHeight - rect.bottom;
                const listH = Math.min(extDropList.scrollHeight || 300, window.innerHeight * 0.4);
                if (spaceBelow >= listH + 8) {
                    // 아래로
                    extDropList.style.top  = (rect.bottom + 4) + 'px';
                    extDropList.style.bottom = '';
                } else {
                    // 위로
                    extDropList.style.bottom = (window.innerHeight - rect.top + 4) + 'px';
                    extDropList.style.top  = '';
                }
                extDropList.style.left = rect.left + 'px';
                extDropList.style.display = '';
                const cur = extEl?.value?.trim() || '';
                extDropList.querySelectorAll('.save-ext-drop-item').forEach(item => {
                    const match = item.dataset.ext === '__none__' ? (cur === '' || cur === '(NONE)') : item.dataset.ext === cur;
                    item.classList.toggle('active', match);
                });
            };
            extDropBtn.addEventListener('click', extDropBtn._extHandler);

            // 아이템 클릭: 매번 새로 바인딩
            extDropList.querySelectorAll('.save-ext-drop-item').forEach(item => {
                if (item._extItemHandler) item.removeEventListener('click', item._extItemHandler);
                item._extItemHandler = e => {
                    e.stopPropagation();
                    if (extEl) {
                        extEl.value = item.dataset.ext === '__none__' ? '(NONE)' : item.dataset.ext;
                        extEl.classList.toggle('is-none', item.dataset.ext === '__none__');
                    }
                    extDropList.style.display = 'none';
                };
                item.addEventListener('click', item._extItemHandler);
            });

            // 외부 클릭/터치 시 드롭다운 닫기
            if (!document._extDropDismiss) {
                document._extDropDismiss = (e) => {
                    const list = document.getElementById('saveExtDropList');
                    const btn  = document.getElementById('saveExtDropBtn');
                    if (list && list.style.display !== 'none'
                            && !list.contains(e.target) && e.target !== btn) {
                        list.style.display = 'none';
                    }
                };
                document.addEventListener('click',     document._extDropDismiss, true);
                document.addEventListener('touchstart', document._extDropDismiss, true);
            }
        }

        // Show
        switchTab(currentTab);
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
    }

    return { open };
})();

window.SavePopup = SavePopup;
