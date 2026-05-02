/* Path: usekit/tools/editor/js2/state/setup_policy.js
 * --------------------------------------------------------------------------------------------
 * SetupPolicy — 설정 항목별 global / slot 정책
 *
 * 정책 변경 (v1.3):
 *   theme / font / fontSize → global  (활성창이 진실, 슬롯 이동해도 유지)
 *   wrap / lineNumbers      → slot    (파일별 개별 설정)
 *
 * 이유:
 *   테마/폰트는 "에디터 환경" — 슬롯마다 바뀌면 시각적 불안정
 *   wrap/lineNumbers는 "파일 속성" — 파일마다 다를 수 있음
 * ─────────────────────────────────────────────────────────── */

const SetupPolicy = (function () {
    'use strict';

    const STORAGE_KEY = 'usekit_setup_policy';
    const GLOBAL_KEY  = 'usekit_global_settings';

    // 기본 정책 — theme/font/fontSize는 global (활성창 기준)
    const _DEFAULT_POLICY = {
        theme:       'global',
        font:        'global',
        fontSize:    'global',
        highlight:   'global',  // 하이라이트: 에디터 환경 설정 → 슬롯마다 바뀌지 않음
        wrap:        'slot',
        lineNumbers: 'slot',
    };

    const _DEFAULT_GLOBAL = {
        theme:    'light',
        font:     'default',
        fontSize: 14,
    };

    let _policy = { ..._DEFAULT_POLICY };
    let _global = { ..._DEFAULT_GLOBAL };

    function get()             { return { ..._policy }; }
    function getPolicy(key)    { return _policy[key] || 'global'; }
    function isGlobal(key)     { return _policy[key] !== 'slot'; }
    function isSlot(key)       { return _policy[key] === 'slot'; }

    function setPolicy(key, value) {
        if (!['global', 'slot'].includes(value)) return;
        _policy[key] = value;
        _save();
    }

    function getGlobal(key) { return key ? _global[key] : { ..._global }; }

    function setGlobal(key, value) {
        _global[key] = value;
        _saveGlobal();
    }

    function _save() {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(_policy)); } catch(e) {}
    }

    function _saveGlobal() {
        try { localStorage.setItem(GLOBAL_KEY, JSON.stringify(_global)); } catch(e) {}
    }

    function _load() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) _policy = { ..._DEFAULT_POLICY, ...JSON.parse(raw) };
        } catch(e) {}
        try {
            const raw = localStorage.getItem(GLOBAL_KEY);
            if (raw) _global = { ..._DEFAULT_GLOBAL, ...JSON.parse(raw) };
        } catch(e) {}
    }

    function init() { _load(); }

    return { init, get, getPolicy, setPolicy, isGlobal, isSlot, getGlobal, setGlobal };
})();

window.SetupPolicy = SetupPolicy;
