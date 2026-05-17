/* Path: usekit/tools/editor/js2/state/state.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 *--------------------------------------------------------------------------------------------
 * 에디터 전역 상태 (BS/BE/모드/LK 등)
 * ─────────────────────────────────────────────────────────── */

const State = (function () {
    'use strict';

    // BS/BE: {line, ch} | null
    // activeEnd: 'H' | 'E' | null  (커서가 붙어있는 끝)
    // modeS, modeM, lkOn: bool
    let _bs        = null;
    let _be        = null;
    let _activeEnd = null;   // 'H' = 커서가 BS쪽, 'E' = 커서가 BE쪽
    let _modeS     = false;
    let _modeM     = false;
    let _modeF     = false;   // Fixed Focus (가상 포커스 스크롤 모드)
    let _modeA     = false;   // A모드 (카피 전용 선택)
    let _modeAStep = 0;       // 0=없음 1=단어 2=라인 3=전체
    let _modeAAnchor = null;  // anchor 위치
    let _lkOn      = false;

    function getBS()        { return _bs; }
    function getBE()        { return _be; }
    function getActiveEnd() { return _activeEnd; }

    function setBS(pos) {
        // CHECK ON 중: BS 앵커 고정 — 변경 무시 (columnMoveEnd 등이 실수로 덮어쓰는 것 방지)
        // 역배열 정렬 등 의도적 변경은 CHECK ON 진입 전(ui_events.js)에서 처리
        if (window._uiIsCheckMode?.()) return;
        _bs = pos ? { line: pos.line, ch: pos.ch } : null;
    }
    function forceSetBS(pos) {
        _bs = pos ? { line: pos.line, ch: pos.ch } : null;
    }
    function setBE(pos) {
        _be = pos ? { line: pos.line, ch: pos.ch } : null;
    }
    function setActiveEnd(v) { _activeEnd = v; }  // 'H' | 'E' | null

    function clearBlock() {
        _bs        = null;
        _be        = null;
        _activeEnd = null;
    }

    function hasBlock() { return _bs !== null && _be !== null; }
    function getModeA()      { return _modeA; }
    function getModeAStep()  { return _modeAStep; }
    function getModeAAnchor(){ return _modeAAnchor; }
    function setModeA(v)     { _modeA = !!v; if (!v) { _modeAStep = 0; _modeAAnchor = null; } }
    function setModeAStep(v) { _modeAStep = v; }
    function setModeAAnchor(p){ _modeAAnchor = p ? { line: p.line, ch: p.ch } : null; }
    function getModeS()      { return _modeS; }
    function getModeM()      { return _modeM; }
    function getModeF()      { return _modeF; }
    function setModeS(v)     { _modeS = !!v; }
    function setModeM(v)     { _modeM = !!v; }
    function toggleModeS() {
        _modeS = !_modeS;
        if (!_modeS) clearBlock();
        else { _activeEnd = null; _modeA = false; _modeAStep = 0; _modeAAnchor = null; }
    }
    function toggleModeM()   { _modeM = !_modeM; }
    function toggleModeF()   { _modeF = !_modeF; }
    function getLK()         { return _lkOn; }
    function setLK(v)        { _lkOn = !!v; }
    function toggleLK()      { _lkOn = !_lkOn; }

    function reset() {
        _bs        = null;
        _be        = null;
        _activeEnd = null;
        _modeS     = false;
        _modeM     = false;
        _modeF     = false;
        _modeA     = false;
        _modeAStep = 0;
        _modeAAnchor = null;
        _lkOn      = false;
    }

    function snapshot() {
        return {
            bs:        _bs        ? { ..._bs }        : null,
            be:        _be        ? { ..._be }        : null,
            activeEnd: _activeEnd,
            modeS:     _modeS,
            modeM:     _modeM,
            lkOn:      _lkOn,
        };
    }

    return {
        getBS, getBE, setBS, setBE, forceSetBS,
        getActiveEnd, setActiveEnd,
        clearBlock, hasBlock,
        getModeA, getModeAStep, getModeAAnchor, setModeA, setModeAStep, setModeAAnchor,
        getModeS, getModeM, getModeF, setModeS, setModeM, toggleModeS, toggleModeM, toggleModeF,
        getLK, setLK, toggleLK,
        reset,
        snapshot,
    };
})();

window.State = State;
