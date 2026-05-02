/* Path: usekit/tools/editor/js2/ui/ui_settings.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * UISettings — 테마/폰트/폰트크기 설정
 *
 * 개선:
 *   - global 정책 항목(fontSize)은 SetupPolicy.setGlobal()에 저장
 *   - slot 정책 항목(theme/font)은 ActiveState.set()에 반영
 *   - slotOverride 모드: localStorage 저장 없이 임시 적용
 * ─────────────────────────────────────────────────────────── */

const UISettings = (function () {
    'use strict';

    const STORAGE_KEY_THEME  = 'usekit_theme';
    const STORAGE_KEY_FONT   = 'usekit_font';
    const STORAGE_KEY_SIZE   = 'usekit_font_size';
    const STORAGE_KEY_LAYOUT = 'usekit_nav_layout';
    const STORAGE_KEY_DEBUG  = 'usekit_debug';

    const FONT_STACKS = {
        default:       'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New", monospace',
        jetbrains:     '"JetBrains Mono", monospace',
        firacode:      '"Fira Code", monospace',
        sourcecodepro: '"Source Code Pro", monospace',
        nanum:         '"Nanum Gothic Coding", monospace',
        inconsolata:   '"Inconsolata", monospace',
    };

    const _WEB_FONTS = new Set(['jetbrains', 'firacode', 'sourcecodepro', 'nanum', 'inconsolata']);

    const THEME_FILES = {
        dark:  'theme-dark.css',
        light: 'theme-light.css',
        white: 'theme-white.css',
    };

    const FONT_SIZE_MIN = 10;
    const FONT_SIZE_MAX = 24;

    let _theme           = 'light';
    let _font            = 'default';
    let _fontSize        = 14;
    let _layout          = 'B';
    let _isOpen          = false;
    let _pendingThemeLink = null;  // preload 중인 theme link

    function open() {
        const panel = document.getElementById('settingsPanel');
        if (!panel) return;
        // OS 키보드 내리기
        window.UIViewport?.blockKeyboard?.();
        // 커서 핸들 숨기기 (에디터 blur)
        window.Editor?.get?.()?.contentDOM?.blur();
        panel.classList.add('open');
        panel.setAttribute('aria-hidden', 'false');
        _isOpen = true;
        _syncCheckboxes();  // 열릴 때 체크박스 상태 동기화
    }

    function close() {
        const panel = document.getElementById('settingsPanel');
        if (!panel) return;
        panel.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        _isOpen = false;
        // 환경(설정) 저장: 닫힐 때 ActiveState + SetupPolicy 동기화
        _persistSettings();
    }

    function _persistSettings() {
        try {
            // SetupPolicy global 저장
            if (window.SetupPolicy) {
                SetupPolicy.setGlobal('theme',    _theme);
                SetupPolicy.setGlobal('font',     _font);
                SetupPolicy.setGlobal('fontSize', _fontSize);
            }
            // ActiveState 동기화 (이미 set()으로 했지만 확인차)
            if (window.ActiveState) {
                ActiveState.set('theme',    _theme);
                ActiveState.set('font',     _font);
                ActiveState.set('fontSize', _fontSize);
            }
            // localStorage fallback
            localStorage.setItem(STORAGE_KEY_THEME, _theme);
            localStorage.setItem(STORAGE_KEY_FONT,  _font);
            localStorage.setItem(STORAGE_KEY_SIZE,  _fontSize);
        } catch(e) { console.warn('[UISettings] persist failed', e); }
    }

    function toggle() { _isOpen ? close() : open(); }

    // slotOverride: true → localStorage 저장 안 함 (슬롯 전환용 일시 적용)
    function applyTheme(theme, { slotOverride = false } = {}) {
        if (!THEME_FILES[theme]) theme = 'dark';
        _theme = theme;

        const newFile = THEME_FILES[theme];
        const link = document.getElementById('themeLink');

        if (link) {
            // 현재 href에서 파일명만 추출해 비교 (브라우저가 절대URL로 바꿔도 안전)
            const curFile = (link.getAttribute('href') || '').replace(/\?.*$/, '').replace(/.*[\/\\]/, '');
            if (curFile === newFile) {
                // 같은 테마 — 버튼 상태만 갱신 & highlight 재동기화
                _updateThemeButtons(theme);
                if (window.Editor?.isReady?.()) Editor.setTheme?.(theme);
                return;
            }
        }

        // ── Preload 패턴: 새 link를 미리 로드한 뒤 기존 것을 교체 ──
        // 기존 link를 즉시 제거하지 않으므로 CSS 깜빡임 없음
        const newLink = document.createElement('link');
        newLink.rel  = 'stylesheet';
        newLink.href = newFile; // 쿼리스트링 없이 (SW 캐시 key 일치)

        // 이전 pending preload 취소
        if (_pendingThemeLink) {
            try { _pendingThemeLink.remove(); } catch(e) {}
            _pendingThemeLink = null;
        }
        _pendingThemeLink = newLink;

        newLink.addEventListener('load', () => {
            _pendingThemeLink = null;
            newLink.id = 'themeLink';
            if (link) link.removeAttribute('id');
            requestAnimationFrame(() => {
                if (link) { try { link.remove(); } catch(e) {} }
                // OS 상태바/브라우저 theme-color 동기화
                const themeColors = { white: '#ffffff', light: '#1e2a3a', dark: '#0b1220' };
                const meta = document.querySelector('meta[name="theme-color"]');
                if (meta) meta.content = themeColors[theme] || '#0b1220';
                requestAnimationFrame(() => {
                    if (window.Editor?.isReady?.()) {
                        Editor.setTheme?.(theme);
                        Editor.refresh();
                    }
                    _resyncActiveButtons();
                });
            });
        });

        newLink.addEventListener('error', () => {
            _pendingThemeLink = null;
            try { newLink.remove(); } catch(e) {}
            console.warn('[UISettings] theme load failed:', newFile);
        });

        // head에 추가 (숨겨진 상태로 미리 로드)
        document.head.appendChild(newLink);
        _updateThemeButtons(theme);

        // ActiveState 동기화
        if (window.ActiveState) ActiveState.set('theme', theme);

        if (!slotOverride) {
            try { localStorage.setItem(STORAGE_KEY_THEME, theme); } catch(e) {}
            // SetupPolicy가 slot이면 global 저장 안 함 (localStorage는 fallback용)
        }
    }

    function _updateThemeButtons(theme) {
        document.querySelectorAll('.settings-theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
    }

    function _resyncActiveButtons() {
        if (window.UIStats?.updateStatsNow) UIStats.updateStatsNow();
        if (window.UIStats?.updateUndoRedo) UIStats.updateUndoRedo();
        if (window.NavNum?.init) NavNum.init();
        if (window.NavFind?.isActive?.()) {
            const _NAV_IDS = ['btnNavUp','btnNavDown','btnNavLeft','btnNavRight',
                              'btnFooterLeft','btnFooterRight','btnFooterFind'];
            const s = getComputedStyle(document.documentElement);
            _NAV_IDS.forEach(id => {
                const b = document.getElementById(id);
                if (!b || !b.style.background) return;
                b.style.background  = s.getPropertyValue('--ac-active-bg').trim();
                b.style.borderColor = s.getPropertyValue('--ac-active-bd').trim();
                b.style.color       = s.getPropertyValue('--ac-active-tx').trim();
            });
        }
        // 보라 계열 버튼 재적용 (LK, Focus 롱프레스, Keyboard)
        if (window.UIEvents?._resyncPurpleButtons) UIEvents._resyncPurpleButtons();
    }

    function getTheme() { return _theme; }

    function applyFont(fontKey) {
        _font = fontKey;
        const stack = FONT_STACKS[fontKey] || FONT_STACKS.default;
        document.documentElement.style.setProperty('--font-mono', stack);
        document.documentElement.style.setProperty('--cm-font', stack);

        const domF = Editor.get?.()?.dom;
        if (domF) domF.style.fontFamily = stack;

        function _doRefresh() {
            requestAnimationFrame(() => requestAnimationFrame(() => {
                const d = Editor.get?.()?.dom;
                if (d) d.style.fontFamily = stack;
                if (window.Editor?.isReady?.()) Editor.refresh();
            }));
        }

        if (_WEB_FONTS.has(fontKey) && document.fonts?.ready) {
            document.fonts.ready.then(_doRefresh);
        } else {
            _doRefresh();
        }

        document.querySelectorAll('.settings-font-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.font === fontKey);
        });

        // ActiveState 동기화
        if (window.ActiveState) ActiveState.set('font', fontKey);

        try { localStorage.setItem(STORAGE_KEY_FONT, fontKey); } catch(e) {}
    }

    function applyFontSize(size) {
        _fontSize = Math.max(FONT_SIZE_MIN, Math.min(FONT_SIZE_MAX, size));
        document.documentElement.style.setProperty('--editor-font-size', _fontSize + 'px');
        document.documentElement.style.setProperty('--cm-font-size', _fontSize + 'px');

        const domS = Editor.get?.()?.dom;
        if (domS) domS.style.fontSize = _fontSize + 'px';
        requestAnimationFrame(() => requestAnimationFrame(() => {
            if (window.Editor?.isReady?.()) Editor.refresh();
        }));

        const val = document.getElementById('fontSizeVal');
        if (val) val.textContent = _fontSize + 'px';

        // global 정책이면 SetupPolicy에 저장
        if (window.SetupPolicy?.isGlobal?.('fontSize')) {
            SetupPolicy.setGlobal('fontSize', _fontSize);
        }
        // ActiveState 동기화
        if (window.ActiveState) ActiveState.set('fontSize', _fontSize);

        try { localStorage.setItem(STORAGE_KEY_SIZE, _fontSize); } catch(e) {}
    }

    function increaseFontSize() { applyFontSize(_fontSize + 1); }
    function decreaseFontSize() { applyFontSize(_fontSize - 1); }

    function applyLayout(layout) {
        _layout = (layout === 'B') ? 'B' : 'A';
        const nav = document.querySelector('.panel-navigation');
        if (nav) nav.classList.toggle('layout-b', _layout === 'B');
        const app = document.querySelector('.editor-app');
        if (app) app.classList.toggle('layout-b', _layout === 'B');
        document.querySelectorAll('.settings-layout-btn[data-layout]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.layout === _layout);
        });
        // A타입: 인디케이터 숨김, B타입: 인디케이터 표시 (사용자 on/off 우선)
        const userIndicator = localStorage.getItem('usekit_indicator');
        if (!userIndicator) {
            _applyIndicatorVisibility(_layout === 'B');
        }
        if (window.UI?.recalcHeight) UI.recalcHeight();
        try { localStorage.setItem(STORAGE_KEY_LAYOUT, _layout); } catch(e) {}
    }

    function _applyIndicatorVisibility(on) {
        const el = document.getElementById('swipeIndicator');
        if (el) el.style.display = on ? '' : 'none';
    }

    function applyIndicator(val) {
        const on = (val !== 'off');
        _applyIndicatorVisibility(on);
        document.querySelectorAll('.settings-layout-btn[data-indicator]').forEach(btn => {
            btn.classList.toggle('active', (btn.dataset.indicator === 'on') === on);
        });
        try { localStorage.setItem('usekit_indicator', on ? 'on' : 'off'); } catch(e) {}
    }

    function applyHighlight(val) {
        const on = (val !== 'off');
        window.Editor?.setOption?.('highlight', on);
        // global 정책 — highlight 변경값을 SetupPolicy + ActiveState에 저장
        window.SetupPolicy?.setGlobal?.('highlight', on);
        window.ActiveState?.set?.('highlight', on);
        window.SlotManager?.saveUIState?.();
        document.querySelectorAll('.settings-layout-btn[data-highlight]').forEach(btn => {
            btn.classList.toggle('active', (btn.dataset.highlight === 'on') === on);
        });
    }

    function applyDebug(on) {
        const isOn = on === 'on' || on === true;
        try { localStorage.setItem(STORAGE_KEY_DEBUG, isOn ? 'on' : 'off'); } catch(e) {}
        document.querySelectorAll('.settings-layout-btn[data-debug]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.debug === (isOn ? 'on' : 'off'));
        });
        if (isOn) {
            if (!window._erudaLoaded) {
                const s = document.createElement('script');
                s.src = 'https://cdn.jsdelivr.net/npm/eruda';
                s.onload = () => { eruda.init(); window._erudaLoaded = true; };
                document.head.appendChild(s);
            } else if (window.eruda) {
                eruda.show();
            }
        } else {
            if (window.eruda) eruda.hide();
        }
    }

    function _restore() {
        try {
            // SetupPolicy global 값 우선, fallback → localStorage
            const gTheme = window.SetupPolicy?.getGlobal?.('theme');
            const gFont  = window.SetupPolicy?.getGlobal?.('font');
            const gSize  = window.SetupPolicy?.getGlobal?.('fontSize');
            const theme = gTheme || localStorage.getItem(STORAGE_KEY_THEME) || 'light';
            const font  = gFont  || localStorage.getItem(STORAGE_KEY_FONT)  || 'default';
            const size  = gSize  || parseInt(localStorage.getItem(STORAGE_KEY_SIZE)) || 14;
            applyTheme(theme);
            applyFont(font);
            applyFontSize(size);
            // highlight global 복원 (저장값 없으면 on 기본)
            const gHighlight = window.SetupPolicy?.getGlobal?.('highlight');
            applyHighlight(gHighlight === false ? 'off' : 'on');
            const layout = localStorage.getItem(STORAGE_KEY_LAYOUT) || 'B';
            applyLayout(layout);
            const indicator = localStorage.getItem('usekit_indicator');
            if (indicator) applyIndicator(indicator);
            // indicator 설정 없으면 layout이 자동 처리
            const debug = localStorage.getItem(STORAGE_KEY_DEBUG) || 'off';
            applyDebug(debug);

        } catch(e) {
            applyTheme('dark');
            applyFont('default');
            applyFontSize(14);
        }
    }

    function _bindEvents() {
        document.getElementById('btnSettingsClose')?.addEventListener('click', close);
        document.getElementById('btnSettingsHelp')?.addEventListener('click', () => {
            close();
            window.KpFn?.[1]?.();
        });
        document.getElementById('settingsOverlay')?.addEventListener('click', close);
        document.querySelectorAll('.settings-theme-btn').forEach(btn => {
            btn.addEventListener('click', () => applyTheme(btn.dataset.theme));
        });
        document.querySelectorAll('.settings-font-btn').forEach(btn => {
            btn.addEventListener('click', () => applyFont(btn.dataset.font));
        });
        document.getElementById('btnFontPlus') ?.addEventListener('click', increaseFontSize);
        document.getElementById('btnFontMinus')?.addEventListener('click', decreaseFontSize);

        // ── Layout A/B ──────────────────────────────────────────
        document.querySelectorAll('.settings-layout-btn[data-layout]').forEach(btn => {
            btn.addEventListener('click', () => applyLayout(btn.dataset.layout));
        });

        // ── Indicator on/off ────────────────────────────────────
        document.querySelectorAll('.settings-layout-btn[data-indicator]').forEach(btn => {
            btn.addEventListener('click', () => applyIndicator(btn.dataset.indicator));
        });
        document.querySelectorAll('.settings-layout-btn[data-highlight]').forEach(btn => {
            btn.addEventListener('click', () => applyHighlight(btn.dataset.highlight));
        });



        // ── Debug on/off ────────────────────────────────────────
        document.querySelectorAll('.settings-layout-btn[data-debug]').forEach(btn => {
            btn.addEventListener('click', () => applyDebug(btn.dataset.debug));
        });

        // ── Feedback (vib / sound) ───────────────────────────────
        UIFeedback?.initButtons?.();

        // ── Global All 토글 ─────────────────────────────────────
        const chkAll = document.getElementById('chkGlobalAll');
        if (chkAll) {
            chkAll.addEventListener('change', () => {
                _applyGlobalAllPolicy(chkAll.checked);
            });
        }

        // ── 개별 체크박스 ────────────────────────────────────────
        const _INDIVIDUAL = {
            chkGlobalTheme: 'theme',
            chkGlobalFont:  'font',
            chkGlobalSize:  'fontSize',
        };
        Object.entries(_INDIVIDUAL).forEach(([id, key]) => {
            document.getElementById(id)?.addEventListener('change', (e) => {
                const isGlobal = e.target.checked;
                if (window.SetupPolicy) SetupPolicy.setPolicy(key, isGlobal ? 'global' : 'slot');
                _persistSettings();
            });
        });
    }

    // All 체크 ON/OFF → 전체 정책 일괄 변경
    function _applyGlobalAllPolicy(allOn) {
        const keys = ['theme', 'font', 'fontSize'];
        const individual = document.getElementById('settingsIndividual');

        if (allOn) {
            // 전체 global
            keys.forEach(k => {
                if (window.SetupPolicy) SetupPolicy.setPolicy(k, 'global');
            });
            // 개별 체크박스도 전부 체크
            ['chkGlobalTheme','chkGlobalFont','chkGlobalSize'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.checked = true;
            });
            // 개별 패널 숨김
            if (individual) individual.classList.remove('visible');
        } else {
            // 개별 패널 표시 (개별 체크박스 상태는 유지)
            if (individual) individual.classList.add('visible');
            // 개별 체크 상태 → 정책 반영
            const _INDIVIDUAL = {
                chkGlobalTheme: 'theme',
                chkGlobalFont:  'font',
                chkGlobalSize:  'fontSize',
            };
            Object.entries(_INDIVIDUAL).forEach(([id, key]) => {
                const el = document.getElementById(id);
                if (!el || !window.SetupPolicy) return;
                SetupPolicy.setPolicy(key, el.checked ? 'global' : 'slot');
            });
        }

        // 토글 텍스트
        const text = document.getElementById('globalAllText');
        if (text) text.textContent = allOn ? 'ALL' : 'PER';

        _persistSettings();
    }

    // Settings 열릴 때 체크박스 상태 동기화
    function _syncCheckboxes() {
        if (!window.SetupPolicy) return;
        const policy = SetupPolicy.get();

        const themeG = policy.theme    !== 'slot';
        const fontG  = policy.font     !== 'slot';
        const sizeG  = policy.fontSize !== 'slot';
        const allOn  = themeG && fontG && sizeG;

        const chkAll   = document.getElementById('chkGlobalAll');
        const chkTheme = document.getElementById('chkGlobalTheme');
        const chkFont  = document.getElementById('chkGlobalFont');
        const chkSize  = document.getElementById('chkGlobalSize');
        const individual = document.getElementById('settingsIndividual');
        const text     = document.getElementById('globalAllText');

        if (chkAll)   chkAll.checked   = allOn;
        if (chkTheme) chkTheme.checked = themeG;
        if (chkFont)  chkFont.checked  = fontG;
        if (chkSize)  chkSize.checked  = sizeG;
        if (individual) individual.classList.toggle('visible', !allOn);
        if (text) text.textContent = allOn ? 'ALL' : 'PER';
    }

    function init() {
        _bindEvents();
        _restore();
        _syncCheckboxes();
    }

    return { init, open, close, toggle, applyTheme, applyFont, applyFontSize, applyLayout, applyIndicator, applyHighlight, getTheme, isOpen: () => _isOpen };
})();

window.UISettings = UISettings;
