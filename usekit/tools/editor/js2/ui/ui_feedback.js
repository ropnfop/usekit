/* Path: usekit/tools/editor/js2/ui/ui_feedback.js
 * --------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 * Purpose: Provides tactile (vibration) and audio (click sound) feedback for keypad interactions
 * --------------------------------------------------------------------------------------------
 */

const UIFeedback = (function () {
    'use strict';

    const SK_VIB = 'usekit_fb_vib';
    const SK_SND = 'usekit_fb_snd';

    // ── 설정 상태 ────────────────────────────────────────────
    let _vibOn = localStorage.getItem(SK_VIB) !== 'off';
    let _sndOn = localStorage.getItem(SK_SND) !== 'off';

    // 모바일 웹은 과도한 햅틱/사운드 호출에 약함 → 짧은 쿨다운
    let _lastVibAt = 0;
    let _lastSndAt = 0;
    const VIB_MIN_GAP_MS = 18;
    const SND_MIN_GAP_MS = 14;

    // 오디오 캐시
    let _ctx = null;
    let _masterGain = null;
    const _noiseCache = new Map();

    function setVib(on) {
        _vibOn = on;
        try { localStorage.setItem(SK_VIB, on ? 'on' : 'off'); } catch(e) {}
        _syncButtons();
    }

    function setSnd(on) {
        _sndOn = on;
        try { localStorage.setItem(SK_SND, on ? 'on' : 'off'); } catch(e) {}
        _syncButtons();
    }

    function _syncButtons() {
        document.getElementById('btnFeedbackVibOn') ?.classList.toggle('active',  _vibOn);
        document.getElementById('btnFeedbackVibOff')?.classList.toggle('active', !_vibOn);
        document.getElementById('btnFeedbackSndOn') ?.classList.toggle('active',  _sndOn);
        document.getElementById('btnFeedbackSndOff')?.classList.toggle('active', !_sndOn);
    }

    // ── 진동 ────────────────────────────────────────────────
    function _canVibrate() {
        return typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function';
    }

    function _vib(ms) {
        if (!_vibOn || !_canVibrate()) return false;
        const nowMs = Date.now();
        if (nowMs - _lastVibAt < VIB_MIN_GAP_MS) return false;
        _lastVibAt = nowMs;
        try {
            return !!navigator.vibrate.call(navigator, ms);
        } catch (_) {
            return false;
        }
    }

    // ── 오디오 ──────────────────────────────────────────────
    function _getCtx() {
        if (_ctx && _ctx.state !== 'closed') return _ctx;
        try {
            _ctx = new (window.AudioContext || window.webkitAudioContext)();
            _masterGain = _ctx.createGain();
            _masterGain.gain.value = 1.35;
            _masterGain.connect(_ctx.destination);
        } catch (e) {
            _ctx = null;
            _masterGain = null;
        }
        return _ctx;
    }

    function _getNoiseBuffer(ctx, dur) {
        const key = Math.max(1, Math.round(dur * 1000));
        if (_noiseCache.has(key)) return _noiseCache.get(key);

        const bufLen = Math.ceil(ctx.sampleRate * dur);
        const buf = ctx.createBuffer(1, bufLen, ctx.sampleRate);
        const data = buf.getChannelData(0);
        for (let i = 0; i < bufLen; i++) data[i] = Math.random() * 2 - 1;

        _noiseCache.set(key, buf);
        return buf;
    }

    // 모바일 OS 키보드 스타일: 노이즈 버스트 + 고역 강조
    // dur: 초, pitch: 밴드패스 중심 Hz, vol: 0~1
    function _tick(dur = 0.010, pitch = 3000, vol = 0.28) {
        if (!_sndOn) return false;
        const nowMs = Date.now();
        if (nowMs - _lastSndAt < SND_MIN_GAP_MS) return false;
        _lastSndAt = nowMs;

        const ctx = _getCtx();
        if (!ctx || !_masterGain) return false;
        if (ctx.state === 'suspended') ctx.resume();

        const now = ctx.currentTime;
        const src = ctx.createBufferSource();
        src.buffer = _getNoiseBuffer(ctx, dur);

        const bp = ctx.createBiquadFilter();
        bp.type = 'bandpass';
        bp.frequency.value = pitch;
        bp.Q.value = 0.9;

        const gain = ctx.createGain();
        gain.gain.setValueAtTime(Math.max(0.0001, vol), now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

        src.connect(bp);
        bp.connect(gain);
        gain.connect(_masterGain);
        src.start(now);
        src.stop(now + dur + 0.002);
        return true;
    }

    // ── 공개 피드백 함수 ─────────────────────────────────────
    // 모바일 웹에서 너무 긴 진동은 오히려 체감이 나빠짐
    function del()       { _vib(24); _tick(0.018, 1450, 0.52); }
    function delRepeat() { _vib(16); _tick(0.012, 1350, 0.34); }
    function enter()     { _vib(16); _tick(0.015, 2200, 0.38); }
    function space()     { _vib(10); _tick(0.010, 3200, 0.44); }
    function key()       { _vib(10); _tick(0.011, 3600, 0.62); }
    function special()   { _vib(12); _tick(0.012, 2700, 0.58); }
    function toggle()    { _vib(18); _tick(0.017, 1500, 0.40); }
    function longPress() { _vib(22); _tick(0.020, 1200, 0.44); }


    function unlock() {
        const ctx = _getCtx();
        if (ctx && ctx.state === 'suspended') ctx.resume();
    }

    function initButtons() {
        document.getElementById('btnFeedbackVibOn') ?.addEventListener('click', () => setVib(true));
        document.getElementById('btnFeedbackVibOff')?.addEventListener('click', () => setVib(false));
        document.getElementById('btnFeedbackSndOn') ?.addEventListener('click', () => setSnd(true));
        document.getElementById('btnFeedbackSndOff')?.addEventListener('click', () => setSnd(false));
        _syncButtons();
    }

    return { key, special, del, delRepeat, enter, space, toggle, longPress, unlock, initButtons, setVib, setSnd };
})();

window.UIFeedback = UIFeedback;
