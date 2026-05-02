/* Path: usekit/tools/editor/js2/editor/editor.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * CM6 EditorView wrapper — CM5 호환 API 제공 (getText/setCursor 등)
 * ─────────────────────────────────────────────────────────── */

const Editor = (function () {
    'use strict';

    // CM6 destructured from global bundle
    const {
        EditorView, keymap, lineNumbers, highlightActiveLine,
        highlightActiveLineGutter, drawSelection, ViewUpdate,
        EditorState, StateEffect, Compartment, Text,
        history, undo: cm6Undo, redo: cm6Redo, undoDepth, redoDepth,
        historyKeymap,
        syntaxHighlighting, defaultHighlightStyle, tags,
        python,
        Decoration, ViewPlugin, RangeSet, EditorSelection,
        allowMultipleSelections,
        autocompletion, CompletionContext, completeFromList,
        completionKeymap, acceptCompletion, closeCompletion,
    } = CM6;

    // HighlightStyle.define 접근 (번들 내부 $n 클래스)
    const HighlightStyle = defaultHighlightStyle.constructor;

    // 다크 테마 HighlightStyle
    const _darkHighlightStyle = HighlightStyle.define([
        { tag: tags.keyword,                         color: '#c792ea' },
        { tag: tags.controlKeyword,                  color: '#c792ea' },
        { tag: tags.definitionKeyword,               color: '#c792ea' },
        { tag: tags.moduleKeyword,                   color: '#82aaff' },
        { tag: tags.operatorKeyword,                 color: '#6fc3df' },
        { tag: tags.operator,                        color: '#6fc3df' },
        { tag: tags.comment,                         color: '#6a7d8a', fontStyle: 'italic' },
        { tag: tags.lineComment,                     color: '#6a7d8a', fontStyle: 'italic' },
        { tag: tags.string,                          color: '#a8e6a3' },
        { tag: tags.special(tags.string),            color: '#a8e6a3' },
        { tag: tags.number,                          color: '#f9a87c' },
        { tag: tags.bool,                            color: '#f9a87c' },
        { tag: tags.atom,                            color: '#f9a87c' },
        { tag: tags.null,                            color: '#f9a87c' },
        { tag: tags.variableName,                    color: '#e8edf6' },
        { tag: tags.definition(tags.variableName),   color: '#82aaff' },
        { tag: tags.function(tags.variableName),     color: '#82aaff' },
        { tag: tags.function(tags.definition(tags.variableName)), color: '#82aaff' },
        { tag: tags.typeName,                        color: '#7ec8e3' },
        { tag: tags.className,                       color: '#ffcb6b' },
        { tag: tags.propertyName,                    color: '#82aaff' },
        { tag: tags.namespace,                       color: '#85e89d' },
        { tag: tags.punctuation,                     color: '#89ddff' },
        { tag: tags.meta,                            color: '#8a93a3' },
        { tag: tags.invalid,                         color: '#ff6b6b', textDecoration: 'underline' },
        { tag: tags.escape,                          color: '#f9a87c' },
    ]);

    // 라이트 테마 HighlightStyle (에디터 bg #eceff3)
    const _lightHighlightStyle = HighlightStyle.define([
        { tag: tags.keyword,                         color: '#c792ea' },
        { tag: tags.controlKeyword,                  color: '#c792ea' },
        { tag: tags.definitionKeyword,               color: '#c792ea' },
        { tag: tags.moduleKeyword,                   color: '#3a6bc0' },
        { tag: tags.operatorKeyword,                 color: '#4a9aba' },
        { tag: tags.operator,                        color: '#4a9aba' },
        { tag: tags.comment,                         color: '#6a7d8a', fontStyle: 'italic' },
        { tag: tags.lineComment,                     color: '#6a7d8a', fontStyle: 'italic' },
        { tag: tags.string,                          color: '#1f7a53' },
        { tag: tags.special(tags.string),            color: '#1f7a53' },
        { tag: tags.number,                          color: '#d4774a' },
        { tag: tags.bool,                            color: '#d4774a' },
        { tag: tags.atom,                            color: '#d4774a' },
        { tag: tags.null,                            color: '#d4774a' },
        { tag: tags.variableName,                    color: '#202632' },
        { tag: tags.definition(tags.variableName),   color: '#3a6bc0' },
        { tag: tags.function(tags.variableName),     color: '#3a6bc0' },
        { tag: tags.function(tags.definition(tags.variableName)), color: '#3a6bc0' },
        { tag: tags.typeName,                        color: '#3a8fa0' },
        { tag: tags.className,                       color: '#b07d2a' },
        { tag: tags.propertyName,                    color: '#3a6bc0' },
        { tag: tags.namespace,                       color: '#2e7d62' },
        { tag: tags.punctuation,                     color: '#596372' },
        { tag: tags.meta,                            color: '#7a8899' },
        { tag: tags.invalid,                         color: '#cc3333', textDecoration: 'underline' },
        { tag: tags.escape,                          color: '#d4774a' },
    ]);

    // 화이트 테마 HighlightStyle (에디터 bg #ffffff)
    const _whiteHighlightStyle = HighlightStyle.define([
        { tag: tags.keyword,                         color: '#7c3aed' },
        { tag: tags.controlKeyword,                  color: '#7c3aed' },
        { tag: tags.definitionKeyword,               color: '#7c3aed' },
        { tag: tags.moduleKeyword,                   color: '#1d4ed8' },
        { tag: tags.operatorKeyword,                 color: '#0369a1' },
        { tag: tags.operator,                        color: '#0369a1' },
        { tag: tags.comment,                         color: '#6b7280', fontStyle: 'italic' },
        { tag: tags.lineComment,                     color: '#6b7280', fontStyle: 'italic' },
        { tag: tags.string,                          color: '#15803d' },
        { tag: tags.special(tags.string),            color: '#15803d' },
        { tag: tags.number,                          color: '#c2410c' },
        { tag: tags.bool,                            color: '#c2410c' },
        { tag: tags.atom,                            color: '#c2410c' },
        { tag: tags.null,                            color: '#c2410c' },
        { tag: tags.variableName,                    color: '#111111' },
        { tag: tags.definition(tags.variableName),   color: '#1d4ed8' },
        { tag: tags.function(tags.variableName),     color: '#1d4ed8' },
        { tag: tags.function(tags.definition(tags.variableName)), color: '#1d4ed8' },
        { tag: tags.typeName,                        color: '#1d4ed8' },
        { tag: tags.className,                       color: '#92400e' },
        { tag: tags.propertyName,                    color: '#1d4ed8' },
        { tag: tags.namespace,                       color: '#0f766e' },
        { tag: tags.punctuation,                     color: '#374151' },
        { tag: tags.meta,                            color: '#6b7280' },
        { tag: tags.invalid,                         color: '#dc2626', textDecoration: 'underline' },
        { tag: tags.escape,                          color: '#c2410c' },
    ]);

    function _getHighlightStyle(theme) {
        if (theme === 'light') return _lightHighlightStyle;
        if (theme === 'white') return _whiteHighlightStyle;
        return _darkHighlightStyle;
    }

    let _currentTheme = 'dark';

    let _view = null;
    let _extensions = null;   // saved at init() — reused by clearHistory()

    // Compartments for runtime-reconfigurable options
    const _comp = {
        lineNumbers:  new Compartment(),
        lineWrapping: new Compartment(),
        readOnly:     new Compartment(),
        language:     new Compartment(),
        highlight:    new Compartment(),
    };

    // Event listeners registered via on()
    const _listeners = {
        cursorActivity: [],
        changes:        [],
        focus:          [],
        blur:           [],
        mousedown:      [],
    };
    function _posToOffset(pos) {
        const doc = _view.state.doc;
        const lineNum = Math.min(pos.line + 1, doc.lines);
        const lineObj = doc.line(lineNum);
        const ch = Math.min(pos.ch || 0, lineObj.length);
        return Math.min(lineObj.from + ch, doc.length);
    }

    function _offsetToPos(offset) {
        const doc  = _view.state.doc;
        const line = doc.lineAt(offset);
        return { line: line.number - 1, ch: offset - line.from };
    }
    function _getAutocompletePopup() {
        return document.querySelector('.cm-tooltip-autocomplete');
    }

    function _isAutocompleteOpen() {
        const popup = _getAutocompletePopup();
        if (!popup) return false;
        const rect = popup.getBoundingClientRect?.();
        return !!rect && rect.width > 0 && rect.height > 0;
    }

    function _getAutocompleteScrollEl(target) {
        const popup = target?.closest?.('.cm-tooltip-autocomplete');
        if (!popup) return null;
        return popup.querySelector('ul') || popup;
    }

    function _installAutocompleteTouchGuard() {
        if (window.__USEKIT_AC_TOUCH_GUARD__) return;
        window.__USEKIT_AC_TOUCH_GUARD__ = true;

        let _acLastY = 0;

        document.addEventListener('touchstart', (e) => {
            const sc = _getAutocompleteScrollEl(e.target);
            if (!sc || !e.touches?.length) return;
            _acLastY = e.touches[0].clientY;
        }, { capture: true, passive: true });

        document.addEventListener('touchmove', (e) => {
            const sc = _getAutocompleteScrollEl(e.target);
            if (!sc || !e.touches?.length) return;

            const y = e.touches[0].clientY;
            const dy = y - _acLastY;
            _acLastY = y;

            const maxTop = Math.max(0, sc.scrollHeight - sc.clientHeight);
            const top = sc.scrollTop || 0;
            const noRange = maxTop <= 1;
            const atTopPullingDown = top <= 0 && dy > 0;
            const atBottomPushingUp = top >= maxTop - 1 && dy < 0;

            if (noRange || atTopPullingDown || atBottomPushingUp) {
                e.preventDefault();
                e.stopPropagation();
            } else {
                e.stopPropagation();
            }
        }, { capture: true, passive: false });
    }
    function init(hostEl) {
        if (_view) { console.warn('[Editor] already initialized'); return _view; }
        if (!hostEl) { console.error('[Editor] hostEl required'); return null; }

        _installAutocompleteTouchGuard();

        // 핸들 숨김 타이머 — selection 변경 시마다 재시작, 3초 후 +1/-1로 OS 물방울 해제
        let _handleHideTimer = null;
        let _handleSelfDispatch = false;  // 자가-dispatch 루프 방지

        function _scheduleHandleHide() {
            if (_handleHideTimer) { clearTimeout(_handleHideTimer); _handleHideTimer = null; }
            _handleHideTimer = setTimeout(() => {
                _handleHideTimer = null;
                if (!_view.hasFocus) return;
                // Skip handle release while the CM6 completion popup is open.
                if (_isAutocompleteOpen()) return;
                // 멀티커서 상태면 스킵 (단일 selection dispatch로 합쳐지는 문제 방지)
                if (_view.state.selection.ranges.length > 1) return;
                const sel = _view.state.selection.main;
                // 음영 상태면 스킵 (사용자가 선택 중)
                if (sel.anchor !== sel.head) return;
                const docLen = _view.state.doc.length;
                // 빈 문서면 스킵 (+1/-1 둘 다 유효 위치 없음)
                if (docLen === 0) return;
                // -1 우선: head가 0이면 +1, 아니면 -1
                const delta = sel.head > 0 ? -1 : 1;
                _handleSelfDispatch = true;
                _view.dispatch({ selection: { anchor: sel.head + delta, head: sel.head + delta } });
                requestAnimationFrame(() => {
                    _view.dispatch({ selection: { anchor: sel.head, head: sel.head } });
                    // 다음 프레임에 플래그 해제 — dispatch로 인한 updateListener 처리가 완료된 후
                    requestAnimationFrame(() => { _handleSelfDispatch = false; });
                });
            }, 3000);
        }

        const updateListener = EditorView.updateListener.of(update => {
            if (update.selectionSet || update.docChanged) {
                _listeners.cursorActivity.forEach(fn => fn(_view));
                // 자가-dispatch(물방울 해제)로 인한 변경은 무시
                if (!_handleSelfDispatch) {
                    _scheduleHandleHide();
                }
            }
            if (update.docChanged) {
                // 'editor.load' userEvent로 디스패치된 변경은 사용자 입력이 아님
                const isLoad = update.transactions.some(tr => tr.isUserEvent('editor.load'));
                if (!isLoad) {
                    _listeners.changes.forEach(fn => fn(_view, update));
                }

            }
            if (update.focusChanged) {
                if (_view.hasFocus) _listeners.focus.forEach(fn => fn(_view));
                else                _listeners.blur.forEach(fn => fn(_view));
            }
        });

        // 빈 라인 + 포인터 클릭 시 CM6 scrollIntoView 차단
        // scrollGuard가 scroll 이벤트에서 처리하므로 effect만 제거
        // KB 오픈 + 빈라인 → CM6 scrollIntoView 전 경로 차단
        // scrollGuard(scroll 이벤트)가 _lastStableTop 기준으로 복원 담당
        const emptyLineScrollGuard = EditorState.transactionFilter.of(tr => {
            if (!tr.effects.some(e => e.is(EditorView.scrollIntoView))) return tr;
            if (!window.UIViewport?.isKbOpen?.()) return tr;
            const head = tr.newSelection?.main?.head;
            if (head == null) return tr;
            let isEmpty = false;
            try { isEmpty = tr.newDoc.lineAt(head).length === 0; } catch (e) {}
            if (!isEmpty) return tr;
            return {
                ...tr,
                effects: tr.effects.filter(e => !e.is(EditorView.scrollIntoView)),
            };
        });

        // Minimal keymap: our CM6 bundle is intentionally slim and does not
        // ship the full @codemirror/commands defaultKeymap. Add the essentials
        // we rely on in the mobile UI.
        const essentialKeymap = keymap.of([
            {
                key: 'Enter',
                run: (view) => {
                    const sel = view.state.selection.main;
                    const from = sel.from, to = sel.to;
                    view.dispatch({
                        changes:        { from, to, insert: '\n' },
                        selection:      { anchor: from + 1 },
                        userEvent:      'input',
                        scrollIntoView: true,
                    });
                    return true;
                },
            },
            {
                key: 'Shift-Enter',
                run: (view) => {
                    const sel = view.state.selection.main;
                    const from = sel.from, to = sel.to;
                    view.dispatch({
                        changes:        { from, to, insert: '\n' },
                        selection:      { anchor: from + 1 },
                        userEvent:      'input',
                        scrollIntoView: true,
                    });
                    return true;
                },
            },
        ]);

        const extensions = [
                // 빈 라인 포인터 클릭 시 CM6 scrollIntoView 차단
                emptyLineScrollGuard,

                // History (undo/redo)
                history(),

                // Essential key bindings (Enter etc.)
                essentialKeymap,

                // Line numbers (compartment — can be toggled)
                _comp.lineNumbers.of(lineNumbers()),

                // Active line highlight
                highlightActiveLine(),
                highlightActiveLineGutter(),

                // Selection highlight
                drawSelection(),

                // Syntax
                _comp.language.of(python()),
                _comp.highlight.of(syntaxHighlighting(_getHighlightStyle(_currentTheme), { fallback: true })),

                // Line wrapping (compartment)
                _comp.lineWrapping.of([]),

                // Read-only (compartment)
                _comp.readOnly.of(EditorState.readOnly.of(false)),

                // Autocomplete — override는 loadAutocomplete() 후 _usekitSource로 주입
                autocompletion({ override: [_usekitSource] }),

                // Update listener
                updateListener,

                // Theme: base dark-friendly
                EditorView.theme({
                    '&': {
                        height: '100%',
                        fontSize: 'var(--cm-font-size, 0.9rem)',
                        fontFamily: 'var(--cm-font, monospace)',
                        background: 'var(--cm-bg)',
                        color:      'var(--cm-text)',
                    },
                    '.cm-content': {
                        caretColor: 'var(--cm-cursor)',
                        padding: '0',
                    },
                    '.cm-cursor, .cm-dropCursor': {
                        borderLeftColor: 'var(--cm-cursor)',
                        borderLeftWidth: '3px',
                    },
                    '.cm-cursor-secondary': {
                        animation: 'none',
                        opacity: '1',
                    },
                    '.cm-activeLine': {
                        backgroundColor: 'var(--cm-activeline)',
                    },
                    '.cm-activeLineGutter': {
                        backgroundColor: 'var(--cm-activeline)',
                    },
                    '.cm-gutters': {
                        background:  'var(--cm-gutter-bg)',
                        color:       'var(--cm-gutter-txt)',
                        borderRight: '1px solid var(--cm-gutter-bd)',
                    },
                    '.cm-lineNumbers .cm-gutterElement': {
                        fontSize: '0.78em',
                        padding:  '0 0.5rem',
                    },
                    '.cm-selectionBackground, ::selection': {
                        backgroundColor: 'var(--cm-selected) !important',
                    },
                    '.cm-scroller': {
                        overflow: 'auto',
                        fontFamily: 'var(--cm-font, monospace)',
                    },
                    '.cm-check-line': {
                        background: 'rgba(251,191,36,0.18) !important',
                    },
                }),
                // 컬럼 블럭 decoration 플러그인
                _colPlugin,
                // CHECK 라인 배경 decoration 플러그인
                _checkPlugin,
                // 멀티커서 허용
                EditorState.allowMultipleSelections.of(true),
            ];
        _extensions = extensions;   // save for clearHistory()

        const state = EditorState.create({
            doc: '',
            extensions,
        });

        _view = new EditorView({
            state,
            parent: hostEl,
        });

        // Prevent scroll propagation (Samsung Internet VP pan fix)
        _view.scrollDOM.addEventListener('touchmove', e => {
            e.stopPropagation();
        }, { passive: true });


        // OS '모두선택' 이벤트 감지 → CM6 전체선택으로 대체
        _view.contentDOM.addEventListener('selectall', (e) => {
            e.preventDefault();
            _view.dispatch({
                selection: { anchor: 0, head: _view.state.doc.length },
            });
        });

        let _lastSpaceKeyHintTs = 0;
        const _markSpaceKeyHint = (e) => {
            try {
                const k = e?.key;
                const c = e?.code;
                if (k === ' ' || k === 'Spacebar' || c === 'Space') {
                    _lastSpaceKeyHintTs = Date.now();
                }
            } catch(_) {}
        };
        const _consumeSpaceKeyHint = () => {
            const ok = (Date.now() - _lastSpaceKeyHintTs) < 1200;
            if (ok) _lastSpaceKeyHintTs = 0;
            return ok;
        };

        // CHECK IME ghost — OS입력 중 ranges 스냅샷
        // _imeSnap: window._imeSnap 으로 관리

        _view.contentDOM.addEventListener('keydown', (e) => {
            _markSpaceKeyHint(e);
            // ── SQL Autocomplete trigger ──
            if (window.SqlComplete?.handleKeyTrigger(e)) {
                // Ctrl/Alt/Shift+Space → completion 트리거
                // completionKeymap의 Ctrl-Space와 동일한 효과를 수동으로
                const cmds = CM6.completionKeymap || [];
                const startCmd = cmds.find(k => k.key === 'Ctrl-Space');
                if (startCmd && startCmd.run) {
                    startCmd.run(_view);
                } else {
                    // fallback: dispatch empty transaction to nudge autocompletion
                    _view.dispatch({ effects: [] });
                }
                return;
            }
            // ── Python Autocomplete trigger ──
            if (window.PyComplete?.handleKeyTrigger(e)) {
                const cmds = CM6.completionKeymap || [];
                const startCmd = cmds.find(k => k.key === 'Ctrl-Space');
                if (startCmd && startCmd.run) {
                    startCmd.run(_view);
                } else {
                    _view.dispatch({ effects: [] });
                }
                return;
            }
            if (window._uiIsBlockMode?.()) {
                // Unidentified = OS 키보드 문자 입력 예고
                if (e.key === 'Unidentified') {
                    // CUR모드: ptrLine 단일 커서만 CM6에 → 개별 라인 입력
                    if (window._uiIsCheckCurMode && !window.BlockState?.isActive?.()) {
                        window.NavBlock?.applyPtrLineSingleCursor?.();
                    }
                    // BLK모드: 음영 방향에 따라 DEL/BS 선택
                    // V2 활성 시: Unidentified 음영 삭제는 setTimeout에서 editAll로 일괄 처리
                    if (!window._uiIsCheckCurMode && !window.BlockState?.isActive?.()) {
                        const _ms = _view.state.selection.main;
                        const _hasCM6Sel = _ms.from < _ms.to;
                        const _hasColSel = window.NavBlock?.hasCurSelection?.();
                        if (_hasCM6Sel || _hasColSel) {
                            e.preventDefault();
                            e.stopPropagation();
                            // 커서(head)가 anchor보다 앞 → 음영이 뒤에 → DEL
                            // 커서(head)가 anchor보다 뒤 → 음영이 앞에 → BS
                            const _cursorBeforeSel = _hasCM6Sel
                                ? (_ms.head <= _ms.anchor)
                                : window.NavBlock?.isCursorBeforeSelection?.();
                            if (_cursorBeforeSel) {
                                window.NavBlock?.delCharAfterColumn?.();
                            } else {
                                window.NavBlock?.delCharBeforeColumn?.();
                            }
                            // IME 조합 강제 종료 — blur/focus로 대기 상태 끊기
                            _view.contentDOM.blur();
                            _view.contentDOM.focus();
                        }
                    }
                }
                if (window.BlockState?.isActive?.()) {
                    const _isCheck   = window.BlockState.isCheckMode();
                    const _isCurMode = window.BlockState.isCursorMode();

                    // CHECK OS입력 복원: 비Unidentified 키 → 조합 완료로 간주
                    if (window._imeSnap && _isCheck && e.key !== 'Unidentified') {
                        imeSnapRestore();
                    }

                    // CUR 모드: CM6 완전 위임 (라인 합침/분리 포함)
                    if (_isCurMode && !_isCheck) { /* CM6가 처리 */ }
                    else if (e.key === 'Unidentified' && _isCheck) {
                        // CHECK OS입력: 첫 진입만 스냅샷+축소, 이후는 ghost 유지
                        if (!window._imeSnap) {
                            const _ranges = window.BlockState.getRanges();
                            const _mIdx   = window.BlockState.getMainIdx();
                            const _rMain  = _ranges[_mIdx] ?? _ranges[0];
                            window._imeSnap = { ranges: _ranges, mIdx: _mIdx, before: _rMain.head,
                                ghost: window.NavBlockV2?.getGhost?.() ?? null,
                                checkMode: true };
                            _view.dispatch({
                                selection: { anchor: _rMain.anchor, head: _rMain.head }
                            });
                            updateColumnDecorationAsLines(window._imeSnap.ranges);
                        }
                        // 매 입력마다 백업 데코 유지
                        setTimeout(() => {
                            if (window._imeSnap) updateColumnDecorationAsLines(window._imeSnap.ranges);
                        }, 32);
                    }
                    else if (e.key === 'Unidentified' && !_isCheck) {
                        // V2 BLK: 입력 전 main=0 강제 (IME 안전) → CM6 완전 위임
                        const _curRanges = window.BlockState.getRanges();
                        if (_curRanges.length > 1 && window.BlockState.getMainIdx() !== 0) {
                            // main을 0번으로 강제 재설정
                            window.BlockState.dispatch(
                                _curRanges.map(r => ({ anchor: r.anchor, head: r.head })), 0
                            );
                        }
                        setTimeout(() => {
                            window.BlockState?.render?.();
                            window.UI?.updateStats?.();
                        }, 0);
                    }
                    else if (e.key === 'Backspace') {
                        e.preventDefault(); e.stopPropagation();
                        window._osBackspace?.();
                    } else if (e.key === 'Enter') {
                        e.preventDefault(); e.stopPropagation();
                        window._osEnter?.();
                    } else if (e.key === ' ') {
                        e.preventDefault(); e.stopPropagation();
                        if (_isCheck) window.NavBlockV2?.checkEdit?.('insert', ' ');
                        else          window.NavBlockV2?.editAll?.('insert', ' ');
                    }
                }
            }
        }, true);

        _view.contentDOM.addEventListener('input', (e) => {
            // V2: OS 입력 후 0번(대표) range 입력 완료 → 나머지 ranges에 동일 처리
            if (window.BlockState?.isActive?.() && !e.isComposing) {
                // Unidentified(한글 등) 경로: beforeinput 미처리 → 여기서 나머지 커서에 적용
                const _isCurMode = window.BlockState.isCursorMode();
                const _isCheck   = window.BlockState.isCheckMode();
                if (!_isCurMode && !_isCheck && e.inputType === 'insertText' && e.data) {
                    window.NavBlockV2?._applyToRestRanges?.('insert', e.data);
                }
                window.UI?.updateStats?.();
                return;
            }
            if (window._uiIsBlockMode?.() && e.data && !e.isComposing) {
                window.NavBlock?.syncColumnAfterInput?.(_view);
            } else if (!window._uiIsBlockMode?.() && e.data && !e.isComposing) {
                // 기본 모드: 실제 텍스트 입력 시만 BS=BE=커서 갱신
                const cur = window.Editor?.getCursor?.();
                if (cur) { window.State?.setBS?.(cur); window.State?.setBE?.(cur); }
                window.UI?.updateStats?.();
            }
        });

        // Samsung Browser OS 팝업 "모두 선택" — beforeinput selectAll 타입으로 들어오는 경우
        // 블럭모드 키입력 인터셉트
        _view.contentDOM.addEventListener('beforeinput', (e) => {
            if (e.inputType === 'selectAll') {
                e.preventDefault();
                _view.dispatch({
                    selection: { anchor: 0, head: _view.state.doc.length },
                });
                return;
            }
            // 블럭모드 입력 라우팅
            if (window._uiIsBlockMode?.()) {
                // V2: 0번(대표) range는 CM6에 위임, 나머지는 input 이벤트에서 처리
                if (window.BlockState?.isActive?.()) {
                    const _isCheck  = window.BlockState.isCheckMode();
                    const _isCurMode = window.BlockState.isCursorMode(); // CUR=쉬프트OFF

                    if (_isCurMode && !_isCheck) {
                        // CUR 모드: 문자입력은 CM6 위임, 백스/엔터는 스틸
                        if (e.inputType !== 'deleteContentBackward' &&
                            e.inputType !== 'insertParagraph' &&
                            e.inputType !== 'insertLineBreak') return;
                    }

                    const _isTextLikeInput = (
                        e.inputType === 'insertText' ||
                        e.inputType === 'insertCompositionText' ||
                        e.inputType === 'insertReplacementText'
                    );
                    if (_isTextLikeInput) {
                        const _raw = e.data;
                        const _spaceHint = _consumeSpaceKeyHint();
                        const _isOsSpaceLike = (
                            _raw === ' ' ||
                            _raw === null ||
                            ((_raw === '' || typeof _raw === 'undefined') && _spaceHint)
                        );
                        const _data = _isOsSpaceLike ? ' ' : ((typeof _raw === 'string' && _raw.length) ? _raw : null);
                        if (_isOsSpaceLike || _data != null) {
                            e.preventDefault();
                            const _ch = _isOsSpaceLike ? ' ' : _data;
                            // CHECK/BLK 모두 editAll/checkEdit으로 통일
                            // → Unidentified(CM6 위임) 경로와 동일 처리
                            if (_isCheck) window.NavBlockV2?.checkEdit?.('insert', _ch);
                            else          window.NavBlockV2?.editAll?.('insert', _ch);
                        }
                    } else if (e.inputType === 'insertParagraph' || e.inputType === 'insertLineBreak') {
                        e.preventDefault();
                        window._osEnter?.();
                    } else if (e.inputType === 'deleteContentBackward') {
                        e.preventDefault();
                        window._osBackspace?.();
                    } else if (e.inputType === 'deleteContentForward') {
                        e.preventDefault();
                        if (_isCheck) window.NavBlockV2?.checkEdit?.('delAfter');
                        else          window.NavBlockV2?.editAll?.('delAfter');
                    }
                    return;
                }
                // 기존 V1 처리 (V2 비활성 시)
                const isCheckCur = !!(window._uiIsCheckMode?.() && window._uiIsCheckCurMode);
                if (e.inputType === 'insertText') {
                    const _raw = e.data;
                    const _spaceHint = _consumeSpaceKeyHint();
                    const _isOsSpaceLike = (
                        _raw === ' ' ||
                        _raw === null ||
                        ((_raw === '' || typeof _raw === 'undefined') && _spaceHint)
                    );
                    const _data = _isOsSpaceLike ? ' ' : ((_raw != null && _raw !== '') ? _raw : null);
                    if (_isOsSpaceLike || _data != null) {
                        e.preventDefault();
                        if (_isOsSpaceLike) {
                            window.Editor?.replaceSelection?.(' ');
                        } else if (isCheckCur) { /* CM6 단일커서 삽입 */ }
                        else window.NavBlock?.insertAtColumnBlock?.(_data);
                    }
                }
            }
        });

        // 블럭모드 한글 조합 처리 (compositionstart/end)
        let _compStartCh = null;
        let _compHadSelection = false;
        let _v2InsertBefore = -1;  // V2: 0번 삽입 전 head 위치
        let _v2InsertData   = '';  // V2: 0번 삽입 예정 텍스트
        let _checkPendingRestore = null; // CHECK Unidentified 입력 후 복원 대기
        _view.contentDOM.addEventListener('compositionstart', () => {
            if (!window._uiIsBlockMode?.()) return;
            // V2 활성: 삼성 키보드는 compositionstart/end 미발생 — V1 경로도 건드리지 않음
            if (window.BlockState?.isActive?.()) return;
            // V1 경로
            const _ms = _view.state.selection.main;
            _compHadSelection = false;
            if (_ms.from < _ms.to) {
                window.NavBlock?.delCharBeforeColumn?.();
                _compHadSelection = true;
            } else if (window.NavBlock?.hasCurSelection?.()) {
                window.NavBlock?.deleteCurSelection?.();
                _compHadSelection = true;
            }
            window.NavBlock?.forceConvergeOffsets?.();
            _compStartCh = window.State?.getBS?.()?.ch ?? null;
        });
        _view.contentDOM.addEventListener('compositionend', (e) => {
            if (!window._uiIsBlockMode?.()) return;
            // V2 활성: 삼성 키보드는 compositionend 미발생 — 무시
            if (window.BlockState?.isActive?.()) return;
            // V1 경로
            const text = e.data;
            const isCheckCur = !!window._uiIsCheckCurMode;
            const startCh = _compStartCh;
            const hadSelection = _compHadSelection;
            _compStartCh = null;
            _compHadSelection = false;

            if (isCheckCur) {
                requestAnimationFrame(() => {
                    window.NavBlock?.syncColumnAfterInput?.(_view);
                });
                return;
            }

            if (!text) return;
            requestAnimationFrame(() => {
                const view = _view;
                const mainHead = view.state.selection.main.head;
                const inserted = view.state.doc.sliceString(mainHead - text.length, mainHead);
                if (inserted === text) {
                    view.dispatch({ changes: { from: mainHead - text.length, to: mainHead, insert: '' }, userEvent: 'input' });
                }
                window.NavBlock?.forceConvergeOffsets?.();
                window.NavBlock?.insertAtColumnBlock?.(text);
            });
        });

        // OS 팝업 "모두 선택" — selectstart + contentDOM 내 pointerdown 없을 때만 교정
        let _pointerActive = false;
        _view.contentDOM.addEventListener('pointerdown', () => { _pointerActive = true; });
        _view.contentDOM.addEventListener('pointerup',   () => { setTimeout(() => { _pointerActive = false; }, 300); });
        _view.contentDOM.addEventListener('pointercancel', () => { _pointerActive = false; });
        document.addEventListener('selectstart', (e) => {
            if (!_view?.contentDOM?.contains(e.target)) return;
            // CHECK / M-LOCK 모드: 물방울 핸들 억제 — selectstart 자체를 막음
            // ESC pending 중에는 우회 — 재앵커 허용
            if ((window._uiIsCheckMode?.() || window._uiIsMLock?.()) && !window._uiIsMLockPending?.()) { e.preventDefault(); return; }
            if (_pointerActive) return; // contentDOM 내 드래그 선택 — 건드리지 않음
            // contentDOM 내 pointerdown 없이 selectstart → OS 팝업 "모두 선택"
            e.preventDefault();
            _view.dispatch({ selection: { anchor: 0, head: _view.state.doc.length } });
        });

        _view.contentDOM.addEventListener('mousedown', () => {
            // In selection mode (S), keep keyboard blocked even on tap
            try {
                if (window.State?.getModeS?.()) {
                    _view.contentDOM.setAttribute('inputmode', 'none');
                }
            } catch (e) {}
            _listeners.mousedown.forEach(fn => fn(_view));
        });

        return _view;
    }
    function getText() {
        return _view ? _view.state.doc.toString() : '';
    }

    function setText(text) {
        if (!_view || !_extensions) return;
        // 히스토리 초기화 + 텍스트 설정을 하나의 setState로 처리
        // → updateListener에서 docChanged 이벤트 자체가 발생하지 않음
        const newState = EditorState.create({
            doc:        text ?? '',
            extensions: _extensions,
        });
        _view.setState(newState);
        setTheme(_currentTheme);
    }
    function getCursor() {
        if (!_view) return { line: 0, ch: 0 };
        return _offsetToPos(_view.state.selection.main.head);
    }

    function setCursor(pos) {
        if (!_view) return;
        const offset = _posToOffset(pos);

        _view.dispatch({
            selection:      { anchor: offset },
            scrollIntoView: true,
        });
    }
    function getSelection() {
        if (!_view) return '';
        const { from, to } = _view.state.selection.main;
        return _view.state.sliceDoc(from, to);
    }
    function getRange(from, to) {
        if (!_view) return '';
        const a = _posToOffset(from);
        const b = _posToOffset(to);
        return _view.state.sliceDoc(Math.min(a, b), Math.max(a, b));
    }

    // from=anchor(고정), to=head(커서) — 방향 그대로 유지
    function setSelection(from, to) {
        if (!_view) return;
        const anchor = _posToOffset(from);
        const head   = _posToOffset(to);
        _view.dispatch({ selection: { anchor, head } });
    }

    // anchor=고정점(BS), head=커서(BE) 를 명시적으로 지정
    function setSelectionDirected(anchor, head) {
        if (!_view) return;
        const a = _posToOffset(anchor);
        const h = _posToOffset(head);

        _view.dispatch({ selection: { anchor: a, head: h }, scrollIntoView: true });
    }

    function clearSelection() {
        if (!_view) return;
        const head = _view.state.selection.main.head;
        _view.dispatch({ selection: { anchor: head } });
    }

    // 컬럼 블럭 decoration ─────────────────────────────────
    const _colEffect = StateEffect.define();
    const _colPlugin = ViewPlugin.fromClass(class {
        constructor() { this.decorations = Decoration.none; }
        update(update) {
            // docChanged 시 자동 클리어 제거 — exitMulti에서 명시적으로 처리
            // (자동 클리어 시 highlight Off 상태에서 paste 후 decoration이 복원 안 되는 버그 발생)
            if (update.docChanged && this.decorations !== Decoration.none) {
                // offset 보정: 기존 decoration을 doc 변경에 맞춰 map
                this.decorations = this.decorations.map(update.changes);
            }
            for (const tr of update.transactions) {
                for (const e of tr.effects) {
                    if (e.is(_colEffect)) {
                        this.decorations = e.value;
                    }
                }
            }
        }
    }, { decorations: v => v.decorations });

    function _getColPlugin() { return _colPlugin; }

    // CHECK 라인 배경 decoration ────────────────────────────
    const _checkEffect = StateEffect.define();
    const _checkPlugin = ViewPlugin.fromClass(class {
        constructor() { this.decorations = Decoration.none; }
        update(update) {
            for (const tr of update.transactions) {
                for (const e of tr.effects) {
                    if (e.is(_checkEffect)) {
                        this.decorations = e.value;
                    }
                }
            }
        }
    }, { decorations: v => v.decorations });

    function setCheckLines(lineNumbers) {
        if (!_view) return;
        if (!lineNumbers.length) {
            _view.dispatch({ effects: _checkEffect.of(Decoration.none) });
            return;
        }
        const decos = [];
        const doc = _view.state.doc;
        for (const lineNum of lineNumbers) {
            if (lineNum < 1 || lineNum > doc.lines) continue;
            const line = doc.line(lineNum);
            decos.push(Decoration.line({ class: 'cm-check-line' }).range(line.from));
        }
        decos.sort((a, b) => a.from - b.from);
        const decoSet = decos.length ? RangeSet.of(decos) : Decoration.none;
        _view.dispatch({ effects: _checkEffect.of(decoSet) });
    }

    function clearCheckLines() {
        if (!_view) return;
        _view.dispatch({ effects: _checkEffect.of(Decoration.none) });
    }

    // anchor/head 쌍 배열 + mainIdx — CHECK 제외 반영 시 사용
    function setColumnSelectionFull(ranges, mainIdx) {
        if (!_view || !ranges.length) return;
        const decos = [];
        const selRanges = [];
        for (const { anchor, head } of ranges) {
            const from = Math.min(anchor, head);
            const to   = Math.max(anchor, head);
            if (from < to) {
                decos.push(Decoration.mark({ class: 'cm-col-block' }).range(from, to));
                selRanges.push(EditorSelection.range(anchor, head));
            } else {
                selRanges.push(EditorSelection.cursor(head));
            }
        }
        decos.sort((a, b) => a.from - b.from);
        const decoSet = decos.length ? RangeSet.of(decos) : Decoration.none;

        // CM6는 EditorSelection.create 시 ranges를 offset 순 재정렬함
        // mainIdx가 가리키는 range의 from 기준으로 재정렬 후 실제 인덱스를 찾아야 함
        const safeMain = Math.min(mainIdx ?? 0, selRanges.length - 1);
        const mainFrom = Math.min(ranges[safeMain]?.anchor ?? 0, ranges[safeMain]?.head ?? 0);
        // 재정렬 후 mainFrom과 가장 가까운 range 인덱스 계산
        const sortedFroms = [...ranges]
            .map((r, i) => ({ from: Math.min(r.anchor, r.head), i }))
            .sort((a, b) => a.from - b.from);
        const resolvedMain = sortedFroms.findIndex(x => x.i === safeMain);

        _view.dispatch({
            effects: _colEffect.of(decoSet),
            selection: EditorSelection.create(selRanges, Math.max(0, resolvedMain)),
            scrollIntoView: true,
        });
    }

    // decoration만 업데이트 (selection 변경 없음) — V2 render용
    // 입력 중 백업 표시용: 음영/커서 구분 없이 라인 전체 하이라이트
    function updateColumnDecorationAsLines(ranges) {
        if (!_view || !ranges.length) return;
        const doc  = _view.state.doc;
        const decos = [];
        const seen  = new Set();
        for (const { anchor, head } of ranges) {
            try {
                const lineFrom = doc.lineAt(Math.min(anchor, head)).from;
                if (!seen.has(lineFrom)) {
                    seen.add(lineFrom);
                    decos.push(Decoration.line({ class: 'cm-col-cursor-line' }).range(lineFrom));
                }
            } catch(e) {}
        }
        decos.sort((a, b) => a.from - b.from);
        _view.dispatch({ effects: _colEffect.of(
            decos.length ? RangeSet.of(decos) : Decoration.none
        )});
    }

    function updateColumnDecoration(ranges) {
        if (!_view || !ranges.length) return;
        const doc   = _view.state.doc;
        const decos = [];
        for (const { anchor, head } of ranges) {
            const from = Math.min(anchor, head);
            const to   = Math.max(anchor, head);
            if (from < to) {
                // 음영 있는 range: mark decoration
                decos.push(Decoration.mark({ class: 'cm-col-block' }).range(from, to));
            } else {
                // cursor point (빈 라인 포함): line decoration으로 라인 표시
                try {
                    const lineFrom = doc.lineAt(from).from;
                    decos.push(Decoration.line({ class: 'cm-col-cursor-line' }).range(lineFrom));
                } catch(e) {}
            }
        }
        decos.sort((a, b) => a.from - b.from || (a.value.startSide ?? 0) - (b.value.startSide ?? 0));
        const decoSet = decos.length ? RangeSet.of(decos) : Decoration.none;
        _view.dispatch({ effects: _colEffect.of(decoSet) });
    }

    function clearColumnDecoration() {
        if (!_view) return;
        _view.dispatch({ effects: _colEffect.of(Decoration.none) });
    }

    function replaceRange(text, from, to) {
        if (!_view) return;
        const anchor = _posToOffset(from);
        const end    = to ? _posToOffset(to) : anchor;
        _view.dispatch({ changes: { from: anchor, to: end, insert: text } });
    }

    function replaceSelection(text) {
        if (!_view) return;
        const state = _view.state;
        const ranges = Array.from(state.selection.ranges);
        if (ranges.length <= 1) {
            // 단일커서: 기존 방식
            const { from, to } = state.selection.main;
            const insertEnd = from + text.length;
            _view.dispatch({
                changes: { from, to, insert: text },
                selection: { anchor: insertEnd },
                scrollIntoView: true,
            });
            return;
        }

        // 멀티 SPACE: 커서 방향 기준 분기
        // - head === to  : 음영 치환 후 커서 collapse
        // - head === from: 왼쪽 경계에만 SPACE 삽입 후 커서 collapse
        // 빈 range는 일반 삽입과 동일
        if (text === ' ') {
            _view.dispatch(state.changeByRange((range) => {
                const from = range.from;
                const to = range.to;
                const head = range.head;
                const anchor = range.anchor;
                const hasSelection = from !== to;
                const isLeftCaret = hasSelection && head === from;
                const changeFrom = from;
                const changeTo = isLeftCaret ? from : to;
                const nextRange = isLeftCaret
                    ? EditorSelection.range(anchor + 1, head + 1)
                    : EditorSelection.cursor(from + 1);
                return {
                    changes: { from: changeFrom, to: changeTo, insert: text },
                    range: nextRange,
                };
            }));
            updateColumnDecoration(Array.from(_view.state.selection.ranges).map(r => ({ anchor: r.anchor, head: r.head })));
            return;
        }

        // 멀티 일반 삽입: 각 range 독립 치환 후 커서 collapse
        _view.dispatch(state.changeByRange((range) => ({
            changes: { from: range.from, to: range.to, insert: text },
            range: EditorSelection.cursor(range.from + text.length),
        })));
        updateColumnDecoration(Array.from(_view.state.selection.ranges).map(r => ({ anchor: r.anchor, head: r.head })));
    }
    function getScrollTop() {
        return _view ? _view.scrollDOM.scrollTop : 0;
    }

    function scrollTo(top) {
        if (_view) {
            _view.scrollDOM.scrollTop = top;
        }
    }

    // Fixed Focus 전용: CM6 인식 스크롤
    // fixH=true (기본/긴클릭): x축 고정 — 현재 가로 위치 유지
    // fixH=false (짧은클릭): CM6 기본 동작 — 커서 1컬럼으로 x축 보정
    function scrollByLines(lines, fixH = true) {
        if (!_view) return;
        const doc = _view.state.doc;
        const scrollLeft = _view.scrollDOM.scrollLeft;
        const scrollTop = _view.scrollDOM.scrollTop;
        const lineH = _view.defaultLineHeight || 20;
        const targetTop = Math.max(0, scrollTop + lines * lineH);
        const pos = _view.lineBlockAtHeight(targetTop)?.from ?? 0;
        const clampedPos = Math.min(pos, doc.length);
        _view.dispatch({
            effects: EditorView.scrollIntoView(clampedPos, { y: 'start', yMargin: 0 })
        });
        if (fixH) {
            // x축 복원 (CM6가 커서 컬럼으로 맞추는 것 방지)
            requestAnimationFrame(() => {
                _view.scrollDOM.scrollLeft = scrollLeft;
            });
        }
    }

    function scrollByChars(chars) {
        if (!_view) return;
        const charW = _view.defaultCharacterWidth || 8.5;
        _view.scrollDOM.scrollLeft = Math.max(0, _view.scrollDOM.scrollLeft + chars * charW);
    }

    function getOption(key) {
        if (key === 'highlight') return _options.highlight !== false;
        if (!_view) return undefined;
        switch (key) {
            case 'lineNumbers':
                // Check if lineNumbers extension is active
                return _optState.lineNumbers;
            case 'lineWrapping':
                return _optState.lineWrapping;
            case 'readOnly':
                return _view.state.readOnly;
            default:
                return undefined;
        }
    }

    // Track option states (CM6 has no direct getOption)
    const _options = { highlight: true };
    const _optState = { lineNumbers: true, lineWrapping: false };

    function setOption(key, value) {
        if (!_view) return;
        switch (key) {
            case 'lineNumbers':
                _optState.lineNumbers = !!value;
                _view.dispatch({
                    effects: _comp.lineNumbers.reconfigure(value ? lineNumbers() : []),
                });
                break;
            case 'lineWrapping':
                _optState.lineWrapping = !!value;
                _view.dispatch({
                    effects: _comp.lineWrapping.reconfigure(value ? EditorView.lineWrapping : []),
                });
                break;
            case 'readOnly':
                _view.dispatch({
                    effects: _comp.readOnly.reconfigure(EditorState.readOnly.of(!!value)),
                });
                break;
            case 'highlight':
                _options.highlight = !!value;
                _view.dispatch({
                    effects: _comp.highlight.reconfigure(
                        value ? syntaxHighlighting(_getHighlightStyle(_currentTheme), { fallback: true }) : []
                    ),
                });
                break;
            case 'theme':
                setTheme(value);
                break;
        }
    }

    function setTheme(theme) {
        if (!_view) return;
        _currentTheme = theme || 'dark';
        _view.dispatch({
            effects: _comp.highlight.reconfigure(
                _options.highlight !== false
                    ? syntaxHighlighting(_getHighlightStyle(_currentTheme), { fallback: true })
                    : []
            ),
        });
    }
    function undo() {
        if (_view) cm6Undo(_view);
    }

    function redo() {
        if (_view) cm6Redo(_view);
    }

    function saveEditorState() {
        return _view ? _view.state : null;
    }
    function restoreEditorState(state) {
        if (!_view || !state) return;
        _view.setState(state);
        setTheme(_currentTheme);
    }
    function clearHistory() {
        // CM6 has no clearHistory API.
        // We create a fresh EditorState with the same doc + the ORIGINAL
        // extensions array (_extensions). Using _view.state.config.base or
        // config.extensions causes "Duplicate compartment" errors because the
        if (!_view || !_extensions) return;
        const newState = EditorState.create({
            doc:        _view.state.doc,
            extensions: _extensions,
        });
        _view.setState(newState);
        // setState 후 compartment가 초기값으로 리셋되므로 현재 테마 재적용
        setTheme(_currentTheme);
    }

    function historySize() {
        if (!_view) return { undo: 0, redo: 0 };
        return {
            undo: undoDepth(_view.state),
            redo: redoDepth(_view.state),
        };
    }
    function on(event, fn) {
        if (_listeners[event]) _listeners[event].push(fn);
    }

    function off(event, fn) {
        if (_listeners[event]) {
            _listeners[event] = _listeners[event].filter(f => f !== fn);
        }
    }
    function lineCount() {
        return _view ? _view.state.doc.lines : 0;
    }

    function getLine(n) {
        if (!_view) return '';
        const doc = _view.state.doc;
        if (n < 0 || n >= doc.lines) return '';
        return doc.line(n + 1).text;
    }

    function focus() {
        if (!_view) return;
        // 이미 포커스 있으면 재호출 금지 — 삼성 브라우저에서 blur/focus 연속 발생으로 커서 깜빡임 소실
        if (_view.hasFocus) return;
        _view.focus();
    }

    function refresh() {
        if (_view) _view.requestMeasure();
    }

    // execCommand compatibility (used by nav.js backspace/forwardDelete)
    function execCommand(cmd) {
        if (!_view) return;
        const { deleteCharBackward, deleteCharForward } = CM6;
        if (cmd === 'delCharBefore' && deleteCharBackward) deleteCharBackward(_view);
        if (cmd === 'delCharAfter'  && deleteCharForward)  deleteCharForward(_view);
    }

    function get() { return _view; }
    function isReady() { return !!_view; }

    function getAnchorPos() {
        if (!_view) return { line: 0, ch: 0 };
        return _offsetToPos(_view.state.selection.main.anchor);
    }

    // ── Autocomplete ──────────────────────────────────────────────────────────
    let _acOverride = null;

    function _usekitSource(context) {
        // SQL 모드 → SqlComplete 우선
        const sqlMode = window.SqlComplete?.isSqlMode() || false;
        const sqlReady = window.SqlComplete?.schemaLoaded || false;
        if (context.explicit) {
            console.log('[Editor] _usekitSource: explicit=' + context.explicit, 'sqlMode=' + sqlMode, 'sqlReady=' + sqlReady);
        }
        if (sqlMode && sqlReady) {
            const result = window.SqlComplete.sqlSource(context);
            console.log('[Editor] _usekitSource: sqlSource result=', result ? result.options?.length + ' items' : 'null');
            if (result) return result;
        }
        // Python 모드 → PyComplete
        if (window.PyComplete?.isPyMode?.()) {
            const pyResult = window.PyComplete.pySource(context);
            if (pyResult) return pyResult;
        }
        if (!_acOverride) return null;
        return _acOverride(context);
    }

    async function loadAutocomplete() {
        try {
            const res  = await fetch('/api/complete');
            const data = await res.json();
            if (!data.ok || !data.items?.length) return;

            const uItems    = data.items.filter(i => i.kind === 'u')
                                        .map(i => ({ label: i.label, detail: i.detail, type: 'function' }));
            const use1Items = data.items.filter(i => i.kind === 'use1')
                                        .map(i => ({ label: i.label, detail: i.detail, type: 'function' }));
            const use2Items = data.items.filter(i => i.kind === 'use2')
                                        .map(i => ({ label: i.label, detail: i.detail, type: 'function' }));
            const use3Items = data.items.filter(i => i.kind === 'use3')
                                        .map(i => ({ label: i.label, detail: i.detail, type: 'function' }));

            _acOverride = function(context) {
                // use.read.json.xx 3단계
                const m3 = context.matchBefore(/use\.\w+\.\w+\.\w*/);
                if (m3) {
                    const parts = m3.text.split('.');
                    const prefix = parts[1] + '.' + parts[2] + '.' + (parts[3] || '');
                    return {
                        from: m3.to - (parts[3] || '').length,
                        options: use3Items
                            .filter(o => o.label.startsWith(prefix))
                            .map(o => ({ ...o, label: o.label.split('.')[2] })),
                    };
                }
                // use.read.xx 2단계
                const m2 = context.matchBefore(/use\.\w+\.\w*/);
                if (m2) {
                    const parts = m2.text.split('.');
                    const prefix = parts[1] + '.' + (parts[2] || '');
                    return {
                        from: m2.to - (parts[2] || '').length,
                        options: use2Items
                            .filter(o => o.label.startsWith(prefix))
                            .map(o => ({ ...o, label: o.label.split('.')[1] })),
                    };
                }
                // use.xx 1단계
                const m1 = context.matchBefore(/use\.\w*/);
                if (m1) {
                    const prefix = m1.text.slice(4);
                    return {
                        from: m1.to - prefix.length,
                        options: use1Items.filter(o => o.label.startsWith(prefix)),
                    };
                }
                // u.xx 단축형
                const mu = context.matchBefore(/u\.\w*/);
                if (mu) {
                    if (mu.from === mu.to && !context.explicit) return null;
                    const prefix = mu.text.slice(2);
                    return {
                        from: mu.from + 2,
                        options: uItems.filter(o => o.label.startsWith(prefix)),
                    };
                }
                return null;
            };
            // USEKIT 데이터를 PyComplete에 주입 (Ctrl/Alt+Space용)
            if (window.PyComplete) {
                window.PyComplete.setUsekitItems(uItems, use1Items, use2Items, use3Items);
            }
            console.log('[Editor] autocomplete ready:', data.items.length, 'items');
        } catch (e) {
            console.warn('[Editor] autocomplete load failed:', e);
        }
        // SQL 스키마도 로드 시도
        if (window.SqlComplete) {
            console.log('[Editor] calling SqlComplete.init()');
            window.SqlComplete.init();
        }
        // Python 런타임 모듈 로드 시도
        if (window.PyComplete) {
            console.log('[Editor] calling PyComplete.init()');
            window.PyComplete.init();
        }
    }
    return {
        init,
        loadAutocomplete,
        get, isReady,
        getText, setText,
        getCursor, setCursor,
        getAnchorPos,
        offsetToPos: _offsetToPos,
        posToOffset: _posToOffset,
        getSelection, getRange, setSelection, setSelectionDirected, clearSelection, setColumnSelectionFull, updateColumnDecoration, clearColumnDecoration,
        setCheckLines, clearCheckLines,
        replaceRange, replaceSelection,
        getScrollTop, scrollTo, scrollByLines, scrollByChars,
        getOption, setOption, setTheme,
        undo, redo, clearHistory, historySize,
        saveEditorState, restoreEditorState,
        on, off,
        lineCount, getLine,
        focus, refresh,
        execCommand,
    };
})();

function imeSnapRestore() {
    const snap = window._imeSnap;
    if (!snap) return;
    window._imeSnap = null;
    const _v = window.Editor?.get?.();
    if (!_v) return;
    const _newMain = _v.state.selection.main;
    const _delta   = _newMain.head - snap.before;
    const _restored = snap.ranges.map((r, i) => {
        if (i === snap.mIdx) return { anchor: _newMain.anchor, head: _newMain.head };
        const _shift = r.head > snap.before ? _delta : 0;
        return { anchor: r.anchor + _shift, head: r.head + _shift };
    });
    window.BlockState?.dispatch?.(_restored, snap.mIdx);
    if (snap.checkMode) window.BlockState?.setCheckMode?.(true);
    window.BlockState?.render?.();
    if (snap.ghost !== null) {
        window.NavBlockV2?.setGhost?.(snap.ghost);
        window.NavBlockV2?.renderWithGhost?.();
    }
    window.UI?.updateStats?.();
}

window.Editor = Editor;
window.imeSnapRestore = imeSnapRestore;

