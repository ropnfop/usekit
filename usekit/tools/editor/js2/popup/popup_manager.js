/* Path: usekit/tools/editor/js2/popup/popup_manager.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * Popup Manager
 * - single active popup policy
 * - common open / close lifecycle
 * - keyboard-safe lift for mobile viewport
 * - popup position reset helper
 * ─────────────────────────────────────────────────────────── */

const PopupManager = (function () {
    'use strict';

    const _registry = new Map();
    let _currentKey = null;
    let _zIndexSeed = 600;

    function _getEntry(key) {
        return _registry.get(key) || null;
    }

    function _getBox(modal) {
        return modal?.querySelector('.modal, .popup, .save-popup, .load-popup') || modal?.firstElementChild || null;
    }

    function _showModal(modal) {
        if (!modal) return;
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
        modal.style.zIndex = String(++_zIndexSeed);
    }

    function _hideModal(modal) {
        if (!modal) return;
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }

    function _resetBoxPosition(modal) {
        const box = _getBox(modal);
        if (!box) return;

        box.dataset.userMoved = '0';
        box.dataset.autoPinned = '0';
        box.style.position = '';
        box.style.left = '';
        box.style.top = '';
        box.style.right = '';
        box.style.bottom = '';
        box.style.transform = '';
        box.style.marginTop = '';
        box.style.marginBottom = '';
    }

    function _resetOverlayLayout(modal, entry) {
        if (!modal || !entry) return;
        modal.style.alignItems = entry.baseAlignItems || '';
        modal.style.justifyContent = entry.baseJustifyContent || '';
        modal.style.paddingBottom = entry.basePaddingBottom || '';
        modal.style.removeProperty('--kb-h');
    }

    function _bindKeyboardSafe(modal, entry) {
        const vv = window.visualViewport;
        if (!modal || !entry || !vv) return null;

        const box = _getBox(modal);
        if (!box) return null;

        const apply = () => {
            const kbH = Math.max(0, window.innerHeight - vv.height);
            modal.style.setProperty('--kb-h', `${kbH}px`);

            const headerEl = document.querySelector('.header-section');
            const minTop = headerEl ? (headerEl.getBoundingClientRect().bottom + 4) : 6;

            let newTop;
            if (kbH > 0) {
                // 키보드 올라온 상태: 키보드 바로 위에 고정
                const kbTop = window.innerHeight - kbH;
                const rect = box.getBoundingClientRect();
                const boxH = rect.height || 200;
                const margin = 6;
                newTop = Math.max(minTop, kbTop - boxH - margin);
            } else {
                // 키보드 없음: 헤더 바로 아래
                newTop = minTop;
            }

            const rect = box.getBoundingClientRect();
            box.style.position  = 'fixed';
            box.style.transform = 'none';
            box.style.bottom    = 'auto';
            box.style.left      = `${Math.max(6, (window.innerWidth - rect.width) / 2)}px`;
            box.style.top       = `${newTop}px`;
            box.style.marginTop = '';
            box.style.marginBottom = '';
        };

        vv.addEventListener('resize', apply);
        vv.addEventListener('scroll', apply);
        window.addEventListener('resize', apply);
        apply();

        return function cleanup() {
            vv.removeEventListener('resize', apply);
            vv.removeEventListener('scroll', apply);
            window.removeEventListener('resize', apply);
            _resetOverlayLayout(modal, entry);
            if (box) {
                box.style.marginTop = '';
                box.style.marginBottom = '';
            }
        };
    }

    function register(key, config) {
        if (!key || !config?.modal) return null;

        const modal = config.modal;
        const entry = {
            key,
            modal,
            useKeyboardSafe: !!config.useKeyboardSafe,
            closeOnBackdrop: config.closeOnBackdrop !== false,
            onBeforeOpen: typeof config.onBeforeOpen === 'function' ? config.onBeforeOpen : null,
            onAfterOpen: typeof config.onAfterOpen === 'function' ? config.onAfterOpen : null,
            onBeforeClose: typeof config.onBeforeClose === 'function' ? config.onBeforeClose : null,
            onAfterClose: typeof config.onAfterClose === 'function' ? config.onAfterClose : null,
            cleanupLift: null,
            baseAlignItems: modal.style.alignItems || '',
            baseJustifyContent: modal.style.justifyContent || '',
            basePaddingBottom: modal.style.paddingBottom || '',
            backdropBound: false,
        };

        _registry.set(key, entry);

        if (entry.closeOnBackdrop && !entry.backdropBound) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) close(key, { reason: 'backdrop' });
            });
            entry.backdropBound = true;
        }

        return {
            open:  (opts) => open(key, opts),
            close: (opts) => close(key, opts),
            isOpen: () => _currentKey === key,
            key,
            modal,
        };
    }

    function open(key, opts = {}) {
        const entry = _getEntry(key);
        if (!entry?.modal) return false;

        if (_currentKey && _currentKey !== key) {
            close(_currentKey, { reason: 'switch', next: key });
        }

        try { entry.onBeforeOpen?.(opts); } catch (e) {}

        _resetBoxPosition(entry.modal);
        _showModal(entry.modal);

        try { entry.cleanupLift?.(); } catch (e) {}
        entry.cleanupLift = null;

        if (entry.useKeyboardSafe) {
            entry.cleanupLift = _bindKeyboardSafe(entry.modal, entry);
        } else {
            _resetOverlayLayout(entry.modal, entry);
        }

        try { entry.onAfterOpen?.(opts); } catch (e) {}
        _currentKey = key;
        return true;
    }

    function close(key, opts = {}) {
        const entry = _getEntry(key);
        if (!entry?.modal) return false;

        try { entry.onBeforeClose?.(opts); } catch (e) {}
        try { entry.cleanupLift?.(); } catch (e) {}
        entry.cleanupLift = null;

        _hideModal(entry.modal);
        // reset을 다음 프레임으로 미뤄 layout thrashing 방지
        const _modal = entry.modal;
        const _entry = entry;
        requestAnimationFrame(() => {
            _resetBoxPosition(_modal);
            _resetOverlayLayout(_modal, _entry);
        });

        try { entry.onAfterClose?.(opts); } catch (e) {}
        if (_currentKey === key) _currentKey = null;
        return true;
    }

    function closeAll(opts = {}) {
        for (const key of _registry.keys()) close(key, opts);
        _currentKey = null;
    }

    function isOpen(key) {
        return _currentKey === key;
    }

    return {
        register,
        open,
        close,
        closeAll,
        isOpen,
        getCurrentKey: () => _currentKey,
        resetPosition: _resetBoxPosition,
    };
})();

window.PopupManager = PopupManager;
