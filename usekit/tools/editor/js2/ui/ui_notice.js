/* ui_notice.js — OPFS / Storage first-run notice modal
 * Shows once on first visit; dismissed state saved in localStorage.
 * Depends on: (none — self-contained, loaded after DOM ready)
 * ──────────────────────────────────────────────────────── */

const UINotice = (function () {
    'use strict';

    const ACK_KEY = 'usekit_notice_opfs_ack';
    let _lang = 'ko';

    function _show() {
        const el = document.getElementById('usekitNoticeOverlay');
        if (!el) return;
        el.style.display = 'flex';
        el.setAttribute('aria-hidden', 'false');
        requestAnimationFrame(() => el.classList.add('open'));
    }

    function _dismiss() {
        const el = document.getElementById('usekitNoticeOverlay');
        if (!el) return;
        el.classList.remove('open');
        el.classList.add('hiding');
        setTimeout(() => {
            el.style.display = 'none';
            el.classList.remove('hiding');
            el.setAttribute('aria-hidden', 'true');
        }, 260);
    }

    function _switchLang(lang) {
        _lang = lang;
        document.querySelectorAll('.notice-lang-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.lang === lang);
        });
        const ko = document.getElementById('noticeTextKo');
        const en = document.getElementById('noticeTextEn');
        if (ko) ko.classList.toggle('active', lang === 'ko');
        if (en) en.classList.toggle('active', lang === 'en');
        // checkbox label
        const lbl = document.querySelector('.notice-check-label');
        if (lbl) lbl.textContent = lang === 'ko' ? lbl.dataset.ko : lbl.dataset.en;
    }

    function _handleConfirm() {
        const chk = document.getElementById('noticeChkDontShow');
        if (chk?.checked) {
            try { localStorage.setItem(ACK_KEY, '1'); } catch (e) {}
        }
        _dismiss();
    }

    function _bind() {
        document.querySelectorAll('.notice-lang-tab').forEach(btn => {
            btn.addEventListener('click', () => _switchLang(btn.dataset.lang));
        });
        document.getElementById('btnNoticeConfirm')?.addEventListener('click', _handleConfirm);
        document.getElementById('btnNoticeClose')?.addEventListener('click', _dismiss);
    }

    function init() {
        _bind();
        // Already acknowledged → skip
        try { if (localStorage.getItem(ACK_KEY) === '1') return; } catch (e) {}
        _show();
    }

    return { init, show: _show };
})();

window.UINotice = UINotice;

// Auto-init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => UINotice.init());
} else {
    UINotice.init();
}
