// float_ai.js — AI Chat mode (edit ↔ chat tab switching)
// ────────────────────────────────────────────────────────
//  EDIT mode: editor = code,   panel = OUTPUT
//  CHAT mode: editor = prompt, panel = AI CHAT log
//
//  Run/Line/Block buttons change meaning per mode.
//  Uses /api/ai_stream (SSE) → uk ai claude "prompt"
//
//  Created by: The Little Prince x ROP x FOP
// ────────────────────────────────────────────────────────
(function() {
  'use strict';

  // ── State ──
  let _mode = 'edit';   // 'edit' | 'chat'

  // Saved editor state when switching
  let _editDoc = '';
  let _editCursor = null;

  // Saved chat draft when switching back to edit
  let _chatDraft = '';
  let _chatCursor = null;

  // Chat log HTML (persisted across switches)
  let _chatLogHtml = '';
  let _jobLogHtml = '';   // job 하위모드 화면 보관 (chat 과 분리)

  // AI provider — runtime-switchable (claude uses shell path,
  // others go through /api/ai_chat → us.ai.serve_chat → ua)
  let _provider = 'claude';

  // Running state
  let _aiRunning = false;
  let _sessionLocked = false;  // re-entry guard; released by _finishResponse

  // ── JOB sub-mode (deep work via /api/ai_job/*) ───────────
  // Chat panel has two sub-modes: 'chat' (light /api/ai_stream) and
  // 'job' (long-running /api/ai_job/start + SSE replay-on-reconnect).
  // chat and job histories are kept SEPARATE — different concerns.
  let _chatSubMode = 'chat';            // 'chat' | 'job'
  let _activeJobId = null;              // currently attached job for the live UI
  let _jobAbort = null;                 // legacy (kept for compat in resets)
  let _jobEs = null;                    // EventSource for live JOB stream
  let _jobReconnectTimer = null;        // retry handle if SSE drops
  let _jobResumeTries = {};             // { [jid]: count }
  const _JOB_LAST_KEY = 'usekit.ai.last_job';   // localStorage key (legacy global; superseded by slot-bound activeJobId)
  const _MODEL_KEY = 'usekit.ai.last_model';    // BUG1: persist last picked {provider, model} across reopen/reload
  let _restoredJobId = null;                    // job id discovered while restoring a slot (candidate for re-subscribe)
  // BUG3: providers actually probed alive THIS session. READY is only asserted
  // for free/cli providers in this set — stale health cache must not claim READY.
  const _sessionProbed = new Set();

  // ── Slot-bound chat persistence ──────────────────────────
  let _boundSlot = '';    // 현재 바인딩된 슬롯 fileName
  // Live session id for the current slot (P1-1). The server's serve_chat_v2
  // returns done.session_id; we keep it here, persist it with the chat, and
  // send it back on the next request so the server can reattach (or DB-restore)
  // the exact same TSK_SESSION instead of starting a fresh one. Per-slot:
  // _onSlotChanged()/_restoreChat() swap it so sessions never cross slots.
  let _activeLiveSessionId = '';

  // §4.8/4.9 Temporary session id for the current slot. Distinct from the live
  // (main) session above so the main_sid tracking flow is never disturbed. While
  // Continue is OFF we round-trip this so the server keeps appending OFF turns to
  // ONE temp_sid (§4.9 "하나의 temp_sid 누적") instead of minting a new one each
  // send. Cleared on slot change and when Continue flips back ON (temp flow ends).
  let _activeTempSessionId = '';

  function _currentSlotName() {
    return window.SlotManager?.getCurrentSlot?.() || '';
  }

  // transcript → OPFS 저장 (chat_ prefix)
  function _persistChat() {
    const name = _boundSlot || _currentSlotName();
    if (!name || !_transcript.length) return;
    try {
      window.SlotStorage?.writeChat?.(name, {
        transcript: _transcript,
        ctxMode: _ctxMode,
        sessionId: _activeLiveSessionId || '',
        timestamp: Date.now(),
      });
    } catch(e) { console.warn('[AiChat] persist failed:', e); }
  }

  // job 누적 → OPFS 저장 (job_ prefix). chat 과 분리.
  function _persistJob() {
    const name = _boundSlot || _currentSlotName();
    if (!name || !_jobTranscript.length) return;
    try {
      window.SlotStorage?.writeJob?.(name, {
        transcript: _jobTranscript,
        activeJobId: _activeJobId || null,
        timestamp: Date.now(),
      });
    } catch(e) { console.warn('[AiJob] persist failed:', e); }
  }

  // OPFS에서 복원 → transcript + chatLogHtml 재구성
  async function _restoreChat(slotName) {
    if (!slotName) return false;
    try {
      const data = window.SlotStorage?.readChat?.(slotName)
                || await window.SlotStorage?.readChatAsync?.(slotName);
      if (!data?.transcript?.length) {
        _transcript = [];
        _chatLogHtml = '';
        _restoredJobId = null;
        _activeLiveSessionId = '';
        return false;
      }
      _transcript = data.transcript.slice(-_MAX_TRANSCRIPT);
      if (data.ctxMode) _ctxMode = data.ctxMode;
      _activeLiveSessionId = data.sessionId || '';   // P1-1: reattach this slot's server session
      _restoredJobId = data.activeJobId || null;   // remember for re-subscribe (step 2)
      // transcript에서 HTML 재구성
      _chatLogHtml = _rebuildHtml(_transcript);
      return true;
    } catch(e) { console.warn('[AiChat] restore failed:', e); return false; }
  }

  // job_ 저장본 → 메모리 복원 (화면 렌더 안 함. 화면은 PHASE 2 몫)
  async function _restoreJob(slotName) {
    if (!slotName) return false;
    try {
      const data = window.SlotStorage?.readJob?.(slotName)
                || await window.SlotStorage?.readJobAsync?.(slotName);
      if (!data?.transcript?.length) {
        _jobTranscript = [];
        return false;
      }
      _jobTranscript = data.transcript.slice(-_MAX_JOB);
      if (data.activeJobId) _restoredJobId = data.activeJobId;  // 진행중 job 재구독용
      return true;
    } catch(e) { console.warn('[AiJob] restore failed:', e); return false; }
  }

  // ── AI 응답 복사 아이콘 ──────────────────────────────────
  // 헤더 끝에 붙이는 작은 복사 버튼 HTML. 클릭 처리는 runOutput 위임 리스너가 함.
  const _COPY_ICON_HTML =
    ' <span class="ai-copy" role="button" title="복사" ' +
    'style="cursor:pointer;opacity:0.95;color:#79c0ff;font-weight:700;padding:0 0.4rem;font-size:1rem;vertical-align:middle;">⧉</span>';

  // 🔊 음성 듣기 아이콘 (TTS). 클릭 처리는 runOutput 위임 리스너가 함.
  const _SPEAK_ICON_HTML =
    ' <span class="ai-speak" role="button" title="음성으로 듣기" ' +
    'style="cursor:pointer;opacity:0.95;color:#f0a868;font-weight:700;padding:0 0.4rem;font-size:1rem;vertical-align:middle;">🔊</span>';

  // TTS playback. One shared <audio>. _ttsBtn ties playback to the message's 🔊
  // icon so tapping that icon again STOPS it (toggle). _ttsGen guards against an
  // in-flight request finishing after the user already stopped.
  let _ttsAudio = null;
  let _ttsBtn = null;
  let _ttsReset = null;
  let _ttsGen = 0;

  // Auto-read / voice-loop use the BROWSER's on-device synthesizer
  // (speechSynthesis): zero network round-trip, and the browser plays queued
  // sentences back-to-back with no gap — unlike per-sentence server TTS, where
  // each sentence paid a fetch+synthesis latency (that was the stutter). The
  // manual 🔊 button still uses Gemini TTS (_speak) for higher voice quality.
  const _SS = (typeof window !== 'undefined' && window.speechSynthesis) || null;
  let _ssVoice = null;
  let _ssPending = 0;        // utterances queued but not yet ended
  let _sqGen = 0;            // bump to invalidate the current auto-read
  let _sqBtn = null;         // this message's 🔊 icon (state + tap-to-stop)
  let _sqEnded = false;      // stream finished → fire _sqDone once the queue drains
  let _sqDone = null;        // voice-loop relisten hook
  let _sqBody = null;        // message body el — voice-synced text reveal target
  let _sqRevealed = '';      // text shown so far (revealed as each sentence is SPOKEN)
  let _sqFinalText = '';     // canonical full text to show once the voice finishes
  let _chunkSpeakActive = false;  // this turn used auto-read (skip _finishResponse re-speak)

  function _ssGetVoice() {
    if (!_SS) return null;
    if (_ssVoice) return _ssVoice;
    const vs = _SS.getVoices() || [];
    _ssVoice = vs.find(v => /^ko/i.test(v.lang)) || vs.find(v => /ko/i.test(v.lang)) || null;
    return _ssVoice;
  }
  if (_SS && typeof _SS.addEventListener === 'function') {
    try { _SS.addEventListener('voiceschanged', () => { _ssVoice = null; _ssGetVoice(); }); } catch (e) {}
  }

  function _stopSpeak() {
    _ttsGen++;                                   // invalidate any in-flight Gemini request
    if (_ttsAudio) { try { _ttsAudio.pause(); } catch (e) {} }
    if (_ttsReset) { const r = _ttsReset; _ttsReset = null; r(); }  // restore icon + fire onDone
    _ttsAudio = null; _ttsBtn = null;
    // also cancel the browser auto-read queue
    _sqGen++; _ssPending = 0; _sqEnded = false; _sqDone = null;
    _sqBody = null; _sqRevealed = ''; _sqFinalText = '';
    if (_SS) { try { _SS.cancel(); } catch (e) {} }
    if (_sqBtn) { try { _sqBtn.textContent = '🔊'; } catch (e) {} _sqBtn = null; }
  }

  // Begin a fresh auto-read for one streamed reply. btn = message 🔊 icon;
  // bodyEl = message body (text is revealed here in sync with the voice);
  // onDone fires after the LAST sentence finishes (resumes the voice loop).
  function _speakQueueStart(btn, bodyEl, onDone) {
    _stopSpeak();
    _sqGen++;
    _ssPending = 0; _sqEnded = false;
    _sqBtn = btn || null; _sqBody = bodyEl || null; _sqDone = onDone || null;
    _sqRevealed = ''; _sqFinalText = '';
  }
  function _speakQueuePush(sentence) {
    if (!_SS || !sentence || !sentence.trim()) return;
    const myGen = _sqGen;
    const s = sentence.trim();
    const u = new SpeechSynthesisUtterance(s);
    const v = _ssGetVoice();
    if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = 'ko-KR'; }
    u.rate = 1.0; u.pitch = 1.0;
    // Voice leads, text follows: reveal this sentence the moment it's SPOKEN.
    u.onstart = () => {
      if (myGen !== _sqGen) return;
      if (_sqBody) {
        _sqRevealed += (_sqRevealed ? ' ' : '') + s;
        _sqBody.innerHTML = `<span style="color:#c9d1d9;">${_esc(_sqRevealed)}</span>`;
        const out = _el('runOutput'); if (out) out.scrollTop = out.scrollHeight;
      }
    };
    const end = () => {
      if (myGen !== _sqGen) return;             // cancelled generation
      _ssPending = Math.max(0, _ssPending - 1);
      if (_ssPending === 0) {
        if (_sqBtn) { try { _sqBtn.textContent = '🔊'; } catch (e) {} }
        if (_sqEnded) _sqFinishReveal();
      }
    };
    u.onend = end; u.onerror = end;
    _ssPending++;
    if (_sqBtn) { try { _sqBtn.textContent = '⏸'; } catch (e) {} }
    try { _SS.speak(u); } catch (e) { end(); }
  }
  // After the last spoken sentence: swap the revealed (sentence-joined) text for
  // the canonical full text (restores exact formatting), then fire the loop hook.
  function _sqFinishReveal() {
    if (_sqBody && _sqFinalText) {
      _sqBody.innerHTML = `<span style="color:#c9d1d9;">${_esc(_sqFinalText)}</span>`;
      const out = _el('runOutput'); if (out) out.scrollTop = out.scrollHeight;
    }
    const d = _sqDone; _sqDone = null; if (d) d();
  }
  function _speakQueueStreamEnded(finalText) {
    _sqEnded = true;
    _sqFinalText = finalText || _sqRevealed;
    if (_ssPending === 0) _sqFinishReveal();
  }

  async function _speak(text, btn, onDone) {
    // Tapping the icon of an active auto-read (browser TTS) = stop it.
    if (btn && btn === _sqBtn && _ssPending > 0) {
      _stopSpeak(); if (onDone) onDone(); return;
    }
    // Tapping the icon that's already playing = stop (interrupt mid-read).
    if (_ttsAudio && btn && btn === _ttsBtn) { _stopSpeak(); return; }
    const prev = btn ? btn.textContent : null;
    const _set = (v) => { if (btn) btn.textContent = v; };
    const _done = () => { if (onDone) { const f = onDone; onDone = null; f(); } };
    if (!text || !text.trim()) { _done(); return; }
    _stopSpeak();                                // stop whatever was playing first
    const myGen = ++_ttsGen;                     // claim this playback generation
    try {
      _set('⏳');
      const resp = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 5000), voice: 'Kore', provider: 'gemini' }),
      });
      if (myGen !== _ttsGen) { _set(prev); _done(); return; }   // stopped while fetching
      if (!resp.ok) {
        let msg = resp.status;
        try { msg = (await resp.json()).error || msg; } catch (e) {}
        window.UI?.showToast?.('TTS 실패: ' + msg, 2000);
        _set(prev); _done();
        return;
      }
      const blob = await resp.blob();
      if (myGen !== _ttsGen) { _set(prev); _done(); return; }   // stopped while buffering
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      _ttsAudio = audio; _ttsBtn = btn || null;
      _set('⏸');                                 // ⏸ = tap to stop
      const reset = () => {
        _set(prev); URL.revokeObjectURL(url);
        if (_ttsAudio === audio) { _ttsAudio = null; _ttsBtn = null; }
        _ttsReset = null; _done();
      };
      _ttsReset = reset;
      audio.onended = reset;
      audio.onerror = reset;
      await audio.play();
    } catch (err) {
      _set(prev);
      window.UI?.showToast?.('TTS 오류: ' + err.message, 2000);
      _done();
    }
  }

  // Read a full message on demand (the 🔊 icon). Routes by the ✨AI 음성 toggle:
  // OFF → on-device browser TTS (free/instant); ON → Gemini TTS (_speak, quality).
  function _speakBrowserOneShot(text, btn) {
    if (!_SS || !text) return;
    _speakQueueStart(btn, null, null);   // no body reveal, no loop hook
    const parts = [];
    let cur = '';
    for (const ch of text) {
      cur += ch;
      if (ch === '.' || ch === '!' || ch === '?' || ch === '。' ||
          ch === '！' || ch === '？' || ch === '…' || ch === '\n') { parts.push(cur); cur = ''; }
    }
    if (cur.trim()) parts.push(cur);
    if (!parts.length) parts.push(text);
    for (const p of parts) _speakQueuePush(p);
    _speakQueueStreamEnded();
  }
  function _speakAuto(text, btn) {
    // Tap an icon that's already speaking (either engine) = stop.
    if (btn && btn === _sqBtn && _ssPending > 0) { _stopSpeak(); return; }
    if (_ttsAudio && btn && btn === _ttsBtn) { _stopSpeak(); return; }
    if (_aiTts || !_SS) _speak(text, btn);          // Gemini (quality/tokens) or fallback
    else _speakBrowserOneShot(text, btn);           // device TTS (free/instant)
  }

  let _copyDelegationBound = false;
  function _ensureCopyDelegation() {
    if (_copyDelegationBound) return;
    const output = _el('runOutput');
    if (!output) return;
    output.addEventListener('click', (e) => {
      const btn = e.target.closest && e.target.closest('.ai-copy');
      if (!btn) return;
      // 헤더의 다음 형제(본문 div)에서 텍스트를 읽는다
      const header = btn.closest('div');
      const body = header && header.nextElementSibling;
      const txt = body ? (body.innerText || body.textContent || '') : '';
      if (!txt) return;
      const done = () => {
        const prev = btn.textContent;
        btn.textContent = '✓';
        btn.style.opacity = '1';
        setTimeout(() => { btn.textContent = prev; btn.style.opacity = '0.95'; }, 1000);
      };
      try {
        if (navigator.clipboard?.writeText) {
          navigator.clipboard.writeText(txt).then(done).catch(() => {});
        }
      } catch (err) {}
    });
    // 🔊 speak delegation — routes by ✨AI 음성 toggle (device TTS vs Gemini).
    output.addEventListener('click', (e) => {
      const sbtn = e.target.closest && e.target.closest('.ai-speak');
      if (!sbtn) return;
      const header = sbtn.closest('div');
      const body = header && header.nextElementSibling;
      const txt = body ? (body.innerText || body.textContent || '') : '';
      if (txt) _speakAuto(txt, sbtn);
    });
    _copyDelegationBound = true;
  }

  // transcript 배열 → chat log HTML 재구성
  function _rebuildHtml(transcript) {
    return transcript.map(t => {
      const role = t.role;
      const time = t.time || '??:??:??';
      const text = _esc(t.content || '');
      if (role === 'user') {
        return `<div style="margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;color:#a78bfa;">[${time}] YOU</div>`
             + `<div style="margin-bottom:0.2rem;"><span style="color:#e2e4e9;">${text}</span></div>`;
      } else if (role === 'ai') {
        const mTag = (t.model || '').toUpperCase() || 'AI';
        const tempTag = t.isTemp
          ? '<span style="color:#d29922;font-weight:700;opacity:0.9;margin-right:0.3rem;">[temp]</span>'
          : '';
        return `<div style="margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;color:#7ee787;">[${time}] ${_esc(mTag)} ${tempTag}${_COPY_ICON_HTML}${_SPEAK_ICON_HTML}</div>`
             + `<div style="margin-bottom:0.2rem;"><span style="color:#c9d1d9;">${text}</span></div>`;
      } else if (role === 'error') {
        return `<div style="margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.7;color:#ff7b72;">[${time}] ERROR</div>`
             + `<div style="margin-bottom:0.2rem;"><span style="color:#ff7b72;">${text}</span></div>`;
      }
      return '';
    }).join('');
  }

  // ── AI Context Mode ──────────────────────────────────────
  // light   : prompt only, no context (default, cheapest)
  // ctx     : recent 3 turns appended
  // recall  : raw transcript search (for "what did I say" questions)
  // file    : current editor file included
  // block   : selected block included
  let _ctxMode = 'light';

  // ── Transcript (local storage only, NOT sent by default) ──
  let _transcript = [];       // [{time, role, content}, ...]
  const _MAX_TRANSCRIPT = 50; // keep last N turns
  const _CTX_TURNS = 3;       // for 'ctx' mode: send last 3 turns only

  let _jobTranscript = [];      // job 답변 누적 (chat 과 분리)
  const _MAX_JOB = 30;          // job 누적 보관 한도

  // ── job transcript → HTML 헬퍼 ──
  function _rebuildJobHtml() {
    return _rebuildHtml(_jobTranscript || []);
  }

  // ── 헤더 모드 따라 현재 슬롯 출력 그리기 함수 ──
  function _renderActiveSubMode() {
    _ensureCopyDelegation();
    const output = _el('runOutput');
    if (!output) return;
    if (_chatSubMode === 'job') {
      _jobLogHtml = _rebuildJobHtml();      // job 데이터 → HTML
      output.innerHTML = _jobLogHtml;       // 없으면 빈 문자열 → 공백
    } else {
      output.innerHTML = _chatLogHtml || ''; // chat, 없으면 공백
    }
    output.scrollTop = output.scrollHeight;
  }

  // ── DOM refs ──
  function _el(id) { return document.getElementById(id); }

  // ── Helpers ──
  function _esc(s) {
    return (s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/\x1b\[[0-9;]*m/g, '')  // strip ANSI
      .replace(/\n/g, '<br>');
  }

  function _ts() {
    const d = new Date();
    return [d.getHours(), d.getMinutes(), d.getSeconds()]
      .map(n => String(n).padStart(2, '0')).join(':');
  }

  // ── Chat log manipulation ──
  function _appendToChatLog(role, text, isTemp) {
    const output = _el('runOutput');
    if (!output) return null;

    // Record to transcript (skip empty AI placeholders)
    if (text && (role === 'user' || role === 'ai')) {
      const entry = { time: _ts(), role, content: text };
      if (role === 'ai') { entry.model = _aiModel || ''; if (isTemp) entry.isTemp = true; }
      _transcript.push(entry);
      if (_transcript.length > _MAX_TRANSCRIPT) {
        _transcript = _transcript.slice(-_MAX_TRANSCRIPT);
      }
    }

    const header = document.createElement('div');
    header.style.cssText = 'margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;';

    const body = document.createElement('div');
    body.style.cssText = 'margin-bottom:0.2rem;';

    if (role === 'user') {
      header.style.opacity = '0.55';
      header.style.color = '#a78bfa';
      header.textContent = `[${_ts()}] YOU`;
      body.innerHTML = `<span style="color:#e2e4e9;">${_esc(text)}</span>`;
    } else if (role === 'ai') {
      header.style.opacity = '0.55';
      header.style.color = '#7ee787';
      const mTag = (_aiModel || '').toUpperCase() || 'AI';
      // §4.8: temporary turn (Continue OFF) — flag it so the user knows this
      // reply is isolated and won't be remembered. Sits just before the copy icon.
      const tempTag = isTemp
        ? '<span style="color:#d29922;font-weight:700;opacity:0.9;margin-right:0.3rem;">[temp]</span>'
        : '';
      header.innerHTML = `[${_ts()}] ${_esc(mTag)} ${tempTag}${_COPY_ICON_HTML}${_SPEAK_ICON_HTML}`;
      if (text) {
        body.innerHTML = `<span style="color:#c9d1d9;">${_esc(text)}</span>`;
      } else {
        body.innerHTML = '<span style="opacity:0.35;">thinking...</span>';
      }
    } else if (role === 'error') {
      header.style.opacity = '0.7';
      header.style.color = '#ff7b72';
      header.textContent = `[${_ts()}] ERROR`;
      body.innerHTML = `<span style="color:#ff7b72;">${_esc(text)}</span>`;
    }

    output.appendChild(header);
    output.appendChild(body);
    output.scrollTop = output.scrollHeight;

    // Save chat log
    _chatLogHtml = output.innerHTML;

    return body;  // for updating "thinking..." later
  }

  // ── Escape prompt for shell ──
  function _shellEscape(s) {
    // For !uk ai claude -c "prompt"
    // We use single quotes and escape internal single quotes
    return s.replace(/'/g, "'\\''");
  }

  // ── Build context based on _ctxMode ──
  function _buildContext(prompt) {
    let prefix = '';

    // §4.6 (P1-1+): server-side ua._history is the source of truth for
    // conversation context (live session or DB-restored). The client no longer
    // auto-prepends the raw transcript — that double-injected the same turns
    // (and leaked the log into the DB as a user message). [CONVERSATION LOG] is
    // only built on EXPLICIT /recall, never auto-detected from keywords.
    const effectiveMode = _ctxMode;

    if (effectiveMode === 'light') {
      // No context — cheapest
      return '';
    }

    if (effectiveMode === 'ctx') {
      // Last 3 turns only (compact)
      const recent = _transcript.slice(-_CTX_TURNS * 2); // 3 turns = up to 6 entries
      if (!recent.length) return '';
      const lines = recent.map(t =>
        `${t.role === 'user' ? 'USER' : 'AI'}: ${t.content.substring(0, 200)}`
      );
      return '[RECENT]\n' + lines.join('\n') + '\n[/RECENT]\n\n';
    }

    if (effectiveMode === 'recall') {
      // Full raw transcript for accurate recall
      if (!_transcript.length) return '';
      const lines = _transcript.map(t =>
        `[${t.time}] ${t.role === 'user' ? 'USER' : 'AI'}: ${t.content}`
      );
      return '[CONVERSATION LOG]\n' + lines.join('\n') + '\n[END LOG]\n\n';
    }

    if (effectiveMode === 'file') {
      // Include current edit file content
      const fileContent = _editDoc || window.Editor?.getText?.() || '';
      if (fileContent.trim()) {
        prefix = '[CURRENT FILE]\n' + fileContent.substring(0, 4000) + '\n[/FILE]\n\n';
      }
    }

    if (effectiveMode === 'block') {
      // Include selected block only
      const sel = window.Editor?.getSelection?.() || '';
      if (sel.trim()) {
        prefix = '[SELECTED CODE]\n' + sel.substring(0, 2000) + '\n[/CODE]\n\n';
      }
    }

    return prefix;
  }

  // ── Parse inline mode prefix from prompt ──
  // /ctx 이 문장 다듬어줘  → mode='ctx', prompt='이 문장 다듬어줘'
  // /file 리뷰해줘         → mode='file', prompt='리뷰해줘'
  // /recall 처음에 뭐라 했지 → mode='recall', prompt='처음에 뭐라 했지'
  function _parsePrompt(raw) {
    const modeMap = {
      '/light': 'light', '/l': 'light',
      '/ctx': 'ctx', '/c': 'ctx',
      '/recall': 'recall', '/r': 'recall',
      '/file': 'file', '/f': 'file',
      '/block': 'block', '/b': 'block',
    };
    const first = raw.split(/\s/, 1)[0].toLowerCase();
    if (modeMap[first]) {
      return {
        mode: modeMap[first],
        prompt: raw.substring(first.length).trim(),
      };
    }
    return { mode: null, prompt: raw };
  }

  // ── Shared: prepare prompt from raw input ──
  function _preparePrompt(rawPrompt) {
    const parsed = _parsePrompt(rawPrompt);
    const savedMode = _ctxMode;
    if (parsed.mode) _ctxMode = parsed.mode;
    const prompt = parsed.prompt || rawPrompt;

    const context = _buildContext(prompt);

    let attachPrefix = '';
    _lastImages = [];                       // reset every turn -> no stale images
    if (_attachments.length) {
      for (const att of _attachments) {
        if (att.type === 'file') attachPrefix += `[FILE: ${att.name}]\n${att.content}\n[/FILE]\n\n`;
        else if (att.type === 'block') attachPrefix += `[CODE]\n${att.content}\n[/CODE]\n\n`;
        else if (att.type === 'image') {
          if (att._path) {
            // Real bytes ride in the request body (images[]) and reach Gemini as
            // inlineData. Only a light text marker is kept; no path/read instruction.
            _lastImages.push({ path: att._path, mime_type: 'image/jpeg' });
            attachPrefix += `[IMAGE: ${att.name} attached]\n\n`;
          } else {
            attachPrefix += `[IMAGE: ${att.name}]\n`;
          }
        }
      }
      _attachments = [];
      _updateAttachPreview();
    }

    _ctxMode = savedMode;
    return context + attachPrefix + prompt;
  }

  // ── Shared: finalize after AI response ──
  function _finishResponse(aiText, aiBody, ok, providerInfo) {
    // CRITICAL: reset running state FIRST — nothing below should block next prompt
    _aiRunning = false;
    _streamAbort = null;
    _sessionLocked = false;  // always release lock on completion/cancel/error/timeout
    _updateStopBtn();

    try {
      if (!aiText) aiText = '(no response)';

      // In voice mode the TTS queue owns the body (reveals text synced to speech,
      // then sets the canonical full text once the voice finishes). Don't dump it
      // here, or all the text would appear before the voice does.
      const _voiceOwnsBody = _chunkSpeakActive && ok !== false
                             && aiText && aiText !== '(no response)';

      if (aiBody && !_voiceOwnsBody) {
        const color = ok === false ? '#ff7b72' : '#c9d1d9';
        // If the provider returned reasoning (e.g. Qwen <think>), show it as a
        // collapsed <details> block above the answer — kept, not discarded.
        const reasoning = (providerInfo && providerInfo.reasoning) || '';
        let html = '';
        if (reasoning) {
          html += '<details style="margin:0 0 0.4rem 0;">'
                + '<summary style="cursor:pointer;color:#8b949e;font-size:0.78rem;">🧠 reasoning</summary>'
                + `<div style="color:#6e7681;font-size:0.78rem;white-space:pre-wrap;margin-top:0.25rem;">${_esc(reasoning)}</div>`
                + '</details>';
        }
        html += `<span style="color:${color};">${_esc(aiText)}</span>`;
        aiBody.innerHTML = html;
      }

      // 🔊 Auto-speak: read the reply aloud when the toggle is ON, OR always
      // when the 📞 voice loop is active. Bind playback to THIS message's 🔊 icon
      // so the user can tap it to stop mid-read. Loop resumes listening on stop/end.
      const _hasReply = ok !== false && aiText && aiText !== '(no response)';
      if (_chunkSpeakActive) {
        // Sentence-chunk TTS already streamed the audio (and owns the voice-loop
        // relisten via the queue's done hook). Only handle the empty/error case
        // here so the voice loop doesn't stall.
        if (!_hasReply) { _stopSpeak(); if (_voiceLoopOn) _voiceAfterSpeak(); }
      } else if ((_autoSpeak || _voiceLoopOn) && _hasReply) {
        const _hdr = aiBody && aiBody.previousElementSibling;
        const _sb = _hdr ? _hdr.querySelector('.ai-speak') : null;
        _speak(aiText, _sb, _voiceLoopOn ? _voiceAfterSpeak : null);
      } else if (_voiceLoopOn) {
        _voiceAfterSpeak();   // nothing to speak (error/empty) → keep the loop alive
      }

      if (ok && providerInfo && providerInfo.provider) {
        _selectModel(providerInfo.provider, providerInfo.model_alias || _aiModel, { silent: true });
      }

      // P1-1: remember the server-side session id so the next request can
      // reattach the same TSK_SESSION (server reuses live ua history, or
      // DB-restores by this id after a restart). Only update on success and
      // when the server actually reported one.
      // §4.8: a temp_sid (Continue OFF) is kept separately so it never overwrites
      // the slot's main live session. It's prefixed "temp_" by the server.
      if (ok && providerInfo && providerInfo.session_id) {
        const _sid = providerInfo.session_id;
        if (_sid.startsWith('temp_')) {
          _activeTempSessionId = _sid;     // §4.9 accumulate OFF turns here
        } else {
          _activeLiveSessionId = _sid;
        }
      }

      _transcript.push({
        time: _ts(),
        role: 'ai',
        content: aiText,
        provider: providerInfo?.provider,
        model: providerInfo?.model_alias || providerInfo?.model,
      });
      if (_transcript.length > _MAX_TRANSCRIPT) {
        _transcript = _transcript.slice(-_MAX_TRANSCRIPT);
      }

      const output = _el('runOutput');
      if (output) {
        output.scrollTop = output.scrollHeight;
        _chatLogHtml = output.innerHTML;
      }

      _persistChat();

      if (_mode === 'chat') {
        window.Editor?.setText?.('');
        _chatDraft = '';
      }
    } catch (e) {
      console.error('[AiChat] _finishResponse error:', e);
    }
  }

  // ── Detect if provider uses CLI tier (streaming capable) ──
  function _isCliProvider(prov) {
    const p = (prov || '').toLowerCase().trim();
    return p === 'claude' || p === 'claude_code';
  }

  // ── Send prompt: routes to streaming or blocking ──
  async function _sendPrompt(rawPrompt) {
    if (!rawPrompt.trim()) return;

    // JOB sub-mode: route to background job runner instead of streaming chat.
    // Deep work shouldn't share the chat lock or 30s idle timeout.
    //
    // claude (CLI) providers ALWAYS go through the job runner: the legacy
    // /api/ai_stream path has a hard 30s abort that kills normal answers, and
    // the job runner additionally survives disconnects (events.jsonl replay).
    // Non-CLI providers (GPT/Gemini/Local/Qwen) keep the streaming/blocking path.
    if (_chatSubMode === 'job') {
      return _sendJobPrompt(rawPrompt.trim());
    }

    if (_aiRunning) return;
    if (_sessionLocked) {
      _appendToChatLog('ai', '[BLOCKED] Previous request still running in background. Wait for completion.');
      return;
    }

    _aiRunning = true;
    _chunkSpeakActive = false;   // reset per turn (set true only if auto-read engages)
    _updateStopBtn();
    _appendToChatLog('user', rawPrompt);
    // §4.8: Continue OFF => this reply is a temporary turn. Flag the bubble so it
    // shows [temp] and is recorded as temporary in the transcript.
    const _isTempTurn = !_continueMode;
    const aiBody = _appendToChatLog('ai', '', _isTempTurn);
    const fullPrompt = _preparePrompt(rawPrompt);

    try {
      if (_isCliProvider(_provider)) {
        await _sendPromptStream(fullPrompt, aiBody);
      } else {
        await _sendPromptBlocking(fullPrompt, aiBody);
      }
    } catch (e) {
      // Safety net: if anything throws past the inner handlers
      _finishResponse('[ERROR] ' + String(e), aiBody, false, null);
    }
    // Final guard: if _finishResponse somehow didn't run
    if (_aiRunning) {
      _aiRunning = false;
      _updateStopBtn();
    }
  }

  // ── JOB sub-mode: long-running deep work ──────────────────
  //   chat ─ user → POST /api/ai_job/start → job_id
  //   chat ← live ─ SSE /api/ai_job/stream?id=<jid>
  //                · event "start"    : show "▶ JOB started"
  //                · event "session"  : remember session_id
  //                · event "delta"    : append text to active body
  //                · event "tool_use" : render a one-line tool card
  //                · event "done"     : finalize with ✓ box
  //                · event "error"    : finalize with ✗ box
  //   Auto-resume on page load via localStorage(_JOB_LAST_KEY).

  function _saveLastJob(jid) {
    try { localStorage.setItem(_JOB_LAST_KEY, jid || ''); } catch (e) {}
  }
  function _loadLastJob() {
    try { return localStorage.getItem(_JOB_LAST_KEY) || ''; } catch (e) { return ''; }
  }

  // tiny helper to render structured JOB events in the chat log
  function _appendJobEvent(kind, text, color) {
    const output = _el('runOutput');
    if (!output) return null;
    const row = document.createElement('div');
    row.style.cssText = 'margin:0.25rem 0;font-size:0.78rem;color:' + (color || '#8b949e') + ';';
    row.innerHTML = `<span style="opacity:0.6;">[${_ts()}] ${kind}</span> ${_esc(text)}`;
    output.appendChild(row);
    output.scrollTop = output.scrollHeight;
    return row;
  }

  async function _sendJobPrompt(rawPrompt) {
    _ensureNotifyPermission();
    if (_activeJobId) {
      _appendJobEvent('JOB ⚠', '진행 중인 JOB이 있습니다. Stop 후 새 작업을 시작하세요.', '#d29922');
      return;
    }
    _jobTranscript.push({ time: _ts(), role: 'user', content: rawPrompt });
    if (_jobTranscript.length > _MAX_JOB) _jobTranscript = _jobTranscript.slice(-_MAX_JOB);
    _appendJobEvent('YOU', rawPrompt, '#a78bfa');

    let job_id = null;
    try {
      const resp = await fetch('/api/ai_job/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: rawPrompt, provider: 'claude' }),
      });
      const j = await resp.json();
      if (!j.ok) {
        _appendJobEvent('JOB ✗', j.error || 'failed to start', '#ff7b72');
        return;
      }
      job_id = j.job_id;
    } catch (e) {
      _appendJobEvent('JOB ✗', String(e), '#ff7b72');
      return;
    }

    _activeJobId = job_id;
    _saveLastJob(job_id);
    _updateStopBtn();
    _attachJobStream(job_id, /*resuming=*/false);
  }

  // The streaming body that delta events append to. Reset per session.
  let _jobBodyEl = null;
  let _jobBodyText = '';

  function _ensureJobBody() {
    if (_jobBodyEl) return _jobBodyEl;
    // 화면이 job 하위모드가 아니면 output 에 job DOM 을 그리지 않는다.
    // (chat 화면에 job 응답이 새는 것을 방지. 텍스트는 _jobBodyText/_jobTranscript 로 보존됨.)
    if (_chatSubMode !== 'job') return null;
    const output = _el('runOutput');
    if (!output) return null;
    const header = document.createElement('div');
    header.style.cssText = 'margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;color:#7ee787;';
    header.innerHTML = `[${_ts()}] CLAUDE (job)${_COPY_ICON_HTML}`;
    const body = document.createElement('div');
    body.style.cssText = 'white-space:pre-wrap;line-height:1.5;font-size:0.85rem;color:#c9d1d9;';
    output.appendChild(header);
    output.appendChild(body);
    output.scrollTop = output.scrollHeight;
    _jobBodyEl = body;
    _jobBodyText = '';
    return body;
  }

  function _attachJobStream(jid, resuming) {
    // close any prior stream
    if (_jobEs) { try { _jobEs.close(); } catch (e) {} _jobEs = null; }
    if (_jobAbort) { try { _jobAbort.abort(); } catch (e) {} _jobAbort = null; }
    _jobBodyEl = null; _jobBodyText = '';

    if (resuming) {
      _appendJobEvent('JOB ↻', `이전 작업 재연결 (${jid})`, '#a78bfa');
    } else {
      _appendJobEvent('JOB ▶', `시작 (${jid})`, '#7ee787');
    }

    // EventSource is the native browser API for SSE. It handles connection
    // lifecycle, reconnection, and buffering better than fetch+ReadableStream
    // — especially on mobile browsers (Samsung Internet abort issues).
    const url = `/api/ai_job/stream?id=${encodeURIComponent(jid)}`;
    let es;
    try {
      es = new EventSource(url);
    } catch (e) {
      _appendJobEvent('JOB ✗', 'EventSource 생성 실패: ' + e, '#ff7b72');
      _resetJobState();
      return;
    }
    _jobEs = es;

    // Generic message fallback (events without an explicit type)
    es.onmessage = (e) => {
      try { _renderJobEvent('msg', JSON.parse(e.data), jid); } catch (_) {}
    };

    // Named events emitted by the server (start, session, delta, tool_use,
    // tool_result, raw, raw_msg, ping, done, error, cancel)
    const _hook = (name) => {
      es.addEventListener(name, (e) => {
        let data = null;
        try { data = JSON.parse(e.data); } catch (_) { data = {}; }
        _renderJobEvent(name, data, jid);
      });
    };
    [
      'start', 'session', 'delta', 'tool_use', 'tool_result',
      'raw', 'raw_msg', 'ping', 'done', 'error', 'cancel',
    ].forEach(_hook);

    es.onerror = (_e) => {
      // EventSource auto-reconnects on transient errors; we only react when
      // the job is still considered active and the connection is closed.
      if (es.readyState === EventSource.CLOSED && _activeJobId === jid) {
        _scheduleJobReconnect(jid);
      }
    };
  }

  // ── JOB done/fail browser notification (상단바, 무음) ──
  // 권한 있고 + 화면이 백그라운드일 때만. 진동/소리 없음(silent).
  function _ensureNotifyPermission() {
    try {
      if (!('Notification' in window)) return;
      if (Notification.permission === 'default') {
        Notification.requestPermission().catch(() => {});
      }
    } catch (e) {}
  }
  function _notifyJob(title, body) {
    try {
      if (!('Notification' in window)) return;
      if (Notification.permission !== 'granted') return;
      // 이미 화면을 보고 있으면 알림 불필요
      if (typeof document !== 'undefined' && document.hidden === false) return;
      const n = new Notification(title, {
        body: body || '',
        tag: 'usekit-job',   // 같은 태그는 덮어쓰기 (알림 누적 방지)
        silent: true,        // 소리·진동 없음
      });
      // 탭으로 돌아오게: 클릭 시 포커스
      n.onclick = () => { try { window.focus(); n.close(); } catch (e) {} };
    } catch (e) {}
  }

  function _renderJobEvent(name, ev, jid) {
    if (name === 'start') {
      // already showed start marker above; ignore the replayed one
      return;
    }
    if (name === 'session') {
      _appendJobEvent('SESSION', ev.session_id || '', '#a78bfa');
      return;
    }
    if (name === 'delta') {
      const body = _ensureJobBody();
      if (!body) return;
      _jobBodyText += (ev.text || '');
      body.textContent = _jobBodyText;
      const output = _el('runOutput');
      if (output) output.scrollTop = output.scrollHeight;
      return;
    }
    if (name === 'tool_use') {
      const desc = ev.name + (ev.input && Object.keys(ev.input).length
        ? ' ' + JSON.stringify(ev.input).slice(0, 120) : '');
      _appendJobEvent('TOOL', desc, '#79c0ff');
      // next text goes into a fresh body block (separation between tool runs)
      _jobBodyEl = null;
      return;
    }
    if (name === 'tool_result') {
      // lightweight marker; we don't render the result body to keep UI clean
      return;
    }
    if (name === 'ping') {
      return;  // heartbeat
    }
    if (name === 'raw') {
      // Plain text line from CLI (not stream-json). Treat as delta-equivalent
      // so users see the response when CLI fails to emit structured JSON.
      const body = _ensureJobBody();
      if (!body) return;
      _jobBodyText += (ev.line || '') + '\n';
      body.textContent = _jobBodyText;
      const output = _el('runOutput');
      if (output) output.scrollTop = output.scrollHeight;
      return;
    }
    if (name === 'raw_msg') {
      // Unknown stream-json message type — try to surface useful text.
      const obj = ev.obj || {};
      const txt = obj.result || obj.text || '';
      if (txt) {
        const body = _ensureJobBody();
        if (body) {
          _jobBodyText += txt;
          body.textContent = _jobBodyText;
        }
      }
      return;
    }
    if (name === 'done') {
      // Final result text (if present and not already shown as deltas/raw)
      const finalTxt = (ev.text || '').trim();
      if (finalTxt && !_jobBodyText.trim()) {
        const body = _ensureJobBody();
        if (body) {
          _jobBodyText = finalTxt;
          body.textContent = finalTxt;
        }
      }
      _appendJobEvent('JOB ✓', '완료', '#7ee787');
      _notifyJob('JOB 완료' + (_boundSlot ? ' — ' + _boundSlot : ''), '작업이 끝났습니다.');
      // Persist the JOB answer into the transcript so it survives slot
      // reloads/tab switches. The streaming path stores via _appendToChatLog,
      // but JOB renders directly to _jobBodyEl and bypassed the transcript —
      // which made finished JOB answers vanish on restore.
      const answer = (_jobBodyText || finalTxt || '').trim();
      if (answer) {
        _jobTranscript.push({ time: _ts(), role: 'ai', content: answer, model: _aiModel || '' });
        if (_jobTranscript.length > _MAX_JOB) _jobTranscript = _jobTranscript.slice(-_MAX_JOB);
      }
      _resetJobState();
      _persistJob();   // write job transcript to the slot
      return;
    }
    if (name === 'error' || name === 'cancel') {
      _appendJobEvent(name === 'cancel' ? 'JOB ⊘' : 'JOB ✗',
                       ev.error || ev.text || 'ended', '#ff7b72');
      _notifyJob('JOB 중단' + (_boundSlot ? ' — ' + _boundSlot : ''), '작업이 중단되었습니다.');
      // Persist whatever partial answer streamed in before the job ended,
      // so it survives a slot reload (same reason as the done handler).
      const partial = (_jobBodyText || '').trim();
      if (partial) {
        _jobTranscript.push({ time: _ts(), role: 'ai', content: partial, model: _aiModel || '' });
        if (_jobTranscript.length > _MAX_JOB) _jobTranscript = _jobTranscript.slice(-_MAX_JOB);
      }
      _resetJobState();
      _persistJob();
      return;
    }
    // unknown event: keep quiet (already in events.jsonl on disk)
  }

  function _scheduleJobReconnect(jid) {
    if (_jobReconnectTimer) return;
    _appendJobEvent('JOB …', '연결 끊김 — 2초 뒤 재연결', '#d29922');
    _jobReconnectTimer = setTimeout(() => {
      _jobReconnectTimer = null;
      if (_activeJobId === jid) _attachJobStream(jid, /*resuming=*/true);
    }, 2000);
  }

  function _resetJobState() {
    _activeJobId = null;
    _saveLastJob('');
    if (_jobEs) { try { _jobEs.close(); } catch (e) {} _jobEs = null; }
    if (_jobAbort) { try { _jobAbort.abort(); } catch (e) {} _jobAbort = null; }
    if (_jobReconnectTimer) { clearTimeout(_jobReconnectTimer); _jobReconnectTimer = null; }
    _jobBodyEl = null; _jobBodyText = '';
    _updateStopBtn();
  }

  async function _cancelActiveJob() {
    if (!_activeJobId) return;
    try {
      await fetch('/api/ai_job/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: _activeJobId }),
      });
    } catch (e) {}
    // SSE will emit "cancel" → _resetJobState() runs there
  }

  // Unified Stop: one entry point for the header stop button.
  //   • claude JOB  → /api/ai_job/cancel (SSE 'cancel' → _resetJobState)
  //   • STREAM      → AbortController.abort() (fetch throws AbortError →
  //                   the path's catch runs _finishResponse, which clears
  //                   _aiRunning / _sessionLocked and refreshes the stop btn)
  function _stopActive() {
    if (_activeJobId) {
      _cancelActiveJob();
    } else if (_streamAbort) {
      try { _streamAbort.abort(); } catch (e) {}
      _streamAbort = null;
    }
  }

  // Expose JOB-mode setter + auto-resume init on first chat enter.
  function _setChatSubMode(m) {
    const next = (m === 'job') ? 'job' : 'chat';
    const prev = _chatSubMode;
    // 실제로 하위모드가 바뀔 때만 화면 스왑 (chat 모드일 때만 의미 있음)
    if (next !== prev && _mode === 'chat') {
      const output = _el('runOutput');
      if (output) {
        // 떠나는 모드의 화면을 보관
        if (prev === 'chat') _chatLogHtml = output.innerHTML;
        else                 _jobLogHtml  = output.innerHTML;
        // 들어오는 모드 그리기 (통일)
        _chatSubMode = next;
        _renderActiveSubMode();
      }
    } else {
      _chatSubMode = next;
    }
    const btn = _el('btnAiJobToggle');
    if (btn) {
      btn.textContent = 'task';     // 라벨만 task (내부 식별자는 job 유지)
      btn.style.color = '';
    }
    _updateSegState();
    // 2단 도크 갱신 — chat/job 하위모드 전환 시에도 도구가 뜨도록(빈 dock 버그 방지)
    if (_mode === 'chat') _updateMiniRunForChat(true);
  }

  function _tryResumeLastJob(preferredJid) {
    // Prefer the slot-bound job id (passed in by slot restore); fall back to
    // the legacy global key for backward compatibility.
    const jid = preferredJid || _loadLastJob();
    if (!jid) return;
    // already attached & connection live → nothing to do
    if (_activeJobId === jid && _jobEs && _jobEs.readyState !== 2 /* not CLOSED */) return;
    // peek status first; if already terminal, skip silently
    fetch(`/api/ai_job/status?id=${encodeURIComponent(jid)}`)
      .then(r => r.json())
      .then(st => {
        const alive = st && st.status && st.status !== 'done' && st.status !== 'error' && st.status !== 'cancelled';
        if (alive) {
          _jobResumeTries[jid] = (_jobResumeTries[jid] || 0) + 1;
          if (_jobResumeTries[jid] > 3) {
            // 좀비로 판정: 여러 번 재연결해도 안 끝남 → 키 비우고 중단
            _saveLastJob('');
            delete _jobResumeTries[jid];
            _appendJobEvent('JOB ⊘', '응답 없는 작업을 정리했습니다 (' + jid.slice(0,12) + ')', '#d29922');
            _updateStopBtn();
            return;
          }
          _activeJobId = jid;
          _saveLastJob(jid);          // keep legacy key in sync
          _setChatSubMode('job');
          _updateStopBtn();
          _attachJobStream(jid, /*resuming=*/true);
        } else {
          // terminal 이거나 status 불명 → 전역 키 정리 (preferredJid 여부 무관)
          _saveLastJob('');
          delete _jobResumeTries[jid];
        }
      })
      .catch(() => {});
  }

  // ── Non-CLI path → uses /api/ai_chat_v2 SSE (stage progress) ──
  async function _sendPromptBlocking(fullPrompt, aiBody) {
    let aiText = '';
    let providerInfo = null;
    let ok = true;

    // Show stage placeholder
    if (aiBody) {
      aiBody.innerHTML = '<span style="color:#8b949e;">⏳ 준비 중...</span>';
    }

    // Auto-read: if 자동읽기/음성대화 is on, speak each sentence as it streams
    // (sentence-chunk TTS) so the voice starts fast instead of waiting for the
    // whole reply + full synthesis at the end.
    // Browser sentence-chunk path is used only when AI 음성 is OFF (free/instant).
    // When AI 음성 is ON, _autoReadOn stays false → text streams live and
    // _finishResponse reads the full reply via Gemini TTS (_speak).
    const _autoReadOn = (_autoSpeak || _voiceLoopOn) && !!_SS && !_aiTts;
    let _spokenUpto = 0;
    if (_autoReadOn) {
      const _hdr0 = aiBody && aiBody.previousElementSibling;
      const _sb0 = _hdr0 ? _hdr0.querySelector('.ai-speak') : null;
      _chunkSpeakActive = true;
      _speakQueueStart(_sb0, aiBody, _voiceLoopOn ? _voiceAfterSpeak : null);
    }

    _streamAbort = new AbortController();
    // No time-based cutoff (see _sendPromptStream): end only on user Stop or
    // backend done/error. _kickV2() kept as a no-op for existing call sites.
    const _kickV2 = () => {};

    try {
      const modelOverride =
        (_aiModel && _aiModel !== 'auto' && _aiModel !== _provider) ? _aiModel : null;

      const resp = await fetch('/api/ai_chat_v2', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: _provider,
          prompt:   fullPrompt,
          images:   _lastImages,   // image attachments -> backend -> Gemini inlineData
          search:   _searchMode,   // google_search grounding on/off
          model:    modelOverride,
          // mode follows the worker count: 1 → single (fast), >=2 → parallel.
          // No "auto" guessing from prompt text anymore.
          mode:     (_workers > 1 ? 'parallel' : 'single'),
          worker:   _provider,
          workers:  _workers,
          quality:  'auto',
          timeout:  120,
          max_tokens: _maxTokens || 2048,
          temperature: _temperature ?? 0.7,
          // General USEKIT Project: flows into conn_kwargs (conn_kwargs.update(config))
          // → conn(project_meta=...) → system injection. OFF = key absent.
          config: _projectMeta ? { project_meta: true } : {},
          // Session reuse: Continue ON → server reuses live ua session (history
          // accumulates under one TSK_SESSION). OFF → each call is a new session.
          continue: !!_continueMode,
          // P1-1: round-trip the session id. On Continue ON the server matches
          // this against its live ua session; if they differ (e.g. after a
          // server restart) it DB-restores this exact session before replying.
          // Empty string → server starts/keeps its own.
          // Session id round-trip. Continue ON -> main live session (P1-1).
          // Continue OFF -> §4.8 temporary: send the slot's temp_sid so OFF turns
          // accumulate in one temp session; empty on first OFF send (server mints).
          session_id: (_continueMode
            ? (_activeLiveSessionId || '')
            : (_activeTempSessionId || '')),
          // Slot ownership (Memory Editor LINKED/ORPHAN single source of truth):
          // the server stamps the minted/temp session's TSK_SESSION.slot with this.
          slot: (_boundSlot || _currentSlotName() || ''),
        }),
        signal: _streamAbort.signal,
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamDone = false;

      // Stage icons for visual progress
      const _stageIcon = {
        start:       '🚀',
        quality:     '⚡',
        route:       '🔀',
        plan:        '📋',
        worker:      '⚙',
        worker_done: '✓',
        judge:       '🔍',
        recall:      '📚',
        assemble:    '📝',
        final_judge: '✨',
        done:        '✅',
      };

      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;
        _kickV2();  // activity → reset idle timeout

        buffer += decoder.decode(value, { stream: true });

        while (buffer.includes('\n\n')) {
          const idx = buffer.indexOf('\n\n');
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);

          let evtType = 'status';
          let evtData = null;
          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) {
              evtType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              try {
                evtData = JSON.parse(line.slice(6));
              } catch (e) { /* ignore */ }
            }
          }

          if (!evtData) continue;

          if (evtType === 'status') {
            // Stage progress only matters until the first token arrives. Once we
            // have streamed text, ignore late status so it doesn't overwrite it.
            if (!aiText) {
              const stage = evtData.stage || '';
              const msg = evtData.msg || '';
              const icon = _stageIcon[stage] || '·';
              if (aiBody) {
                aiBody.innerHTML = `<span style="color:#8b949e;">${icon} ${_esc(msg)}</span>`;
                const output = _el('runOutput');
                if (output) output.scrollTop = output.scrollHeight;
              }
            }
          } else if (evtType === 'delta') {
            // Real-time token chunk → append and render (same look as final).
            const piece = evtData.text || '';
            if (piece) {
              aiText += piece;
              // Voice OFF → stream text live. Voice ON → don't show text here;
              // it's revealed sentence-by-sentence as each is SPOKEN (voice leads).
              if (!_autoReadOn && aiBody) {
                aiBody.innerHTML = `<span style="color:#c9d1d9;">${_esc(aiText)}</span>`;
                const output = _el('runOutput');
                if (output) output.scrollTop = output.scrollHeight;
              }
              // Speak any newly-completed sentence(s) right away.
              if (_autoReadOn) {
                const scan = aiText.slice(_spokenUpto);
                let lastEnd = -1;
                for (let i = scan.length - 1; i >= 0; i--) {
                  const c = scan[i];
                  if (c === '.' || c === '!' || c === '?' || c === '。' ||
                      c === '！' || c === '？' || c === '…' || c === '\n') { lastEnd = i; break; }
                }
                if (lastEnd >= 0) {
                  const ready = scan.slice(0, lastEnd + 1).trim();
                  _spokenUpto += lastEnd + 1;
                  if (ready) _speakQueuePush(ready);
                }
              }
            }
          } else if (evtType === 'done') {
            ok = evtData.ok !== false;
            providerInfo = evtData;
            if (_autoReadOn) {
              const tail = aiText.slice(_spokenUpto).trim();   // unspoken remainder
              if (tail) _speakQueuePush(tail);
            }
            aiText = evtData.text || aiText;   // canonical full text; keep streamed if empty
            if (_autoReadOn) _speakQueueStreamEnded(aiText);   // reveal canonical once voice ends
            streamDone = true;
            break;
          } else if (evtType === 'error') {
            ok = false;
            aiText = '[ERROR] ' + (evtData.error || 'unknown error');
            streamDone = true;
            break;
          }
        }
      }
      try { reader.cancel(); } catch(e) {}
    } catch (err) {
      if (err.name === 'AbortError') {
        aiText = '[Cancelled]';
        ok = false;
      } else {
        aiText = '[Error] ' + String(err);
        ok = false;
      }
    }

    _streamAbort = null;
    _finishResponse(aiText.trim(), aiBody, ok, providerInfo);
  }

  // ── Streaming path (CLI providers: Claude Code) ──
  // Uses fetch + ReadableStream to parse SSE from /api/ai_stream.
  // Updates the chat bubble in real-time as text arrives.
  let _streamAbort = null;  // AbortController for cancel support

  async function _sendPromptStream(fullPrompt, aiBody) {
    let aiText = '';
    let providerInfo = null;
    let ok = true;

    // Show "thinking..." placeholder
    if (aiBody) {
      aiBody.innerHTML = '<span style="color:#8b949e;">thinking...</span>';
    }

    _streamAbort = new AbortController();
    // No time-based cutoff: a health-checked model must keep streaming until
    // the user presses Stop or the backend sends done/error. _kick() is kept
    // as a no-op so existing activity call sites need no changes.
    const _kick = () => {};

    try {
      const modelOverride =
        (_aiModel && _aiModel !== 'auto' && _aiModel !== _provider) ? _aiModel : null;

      const resp = await fetch('/api/ai_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: _provider,
          prompt:   fullPrompt,
          model:    modelOverride,
          timeout:  300,
          max_tokens: _maxTokens || 2048,
          temperature: _temperature ?? 0.7,
          config: _projectMeta ? { project_meta: true } : {},
        }),
        signal: _streamAbort.signal,
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamDone = false;

      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;
        _kick();  // activity → reset idle timeout

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE: "event: <type>\ndata: <json>\n\n"
        while (buffer.includes('\n\n')) {
          const idx = buffer.indexOf('\n\n');
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);

          // Parse event type and data from the block
          let evtType = 'delta';
          let evtData = null;
          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) {
              evtType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              try {
                evtData = JSON.parse(line.slice(6));
              } catch (e) { /* ignore parse errors */ }
            }
          }

          if (!evtData) continue;

          if (evtType === 'delta' && evtData.text) {
            aiText += evtData.text;
            if (aiBody) {
              aiBody.innerHTML = `<span style="color:#c9d1d9;">${_esc(aiText)}</span>`;
              const output = _el('runOutput');
              if (output) output.scrollTop = output.scrollHeight;
            }
          } else if (evtType === 'tool') {
            const toolName = evtData.name || '';
            const action = evtData.action || '';
            if (toolName && action === 'start' && aiBody) {
              aiBody.innerHTML = `<span style="color:#c9d1d9;">${_esc(aiText)}</span>`
                + `<span style="color:#8b949e;"> [${_esc(toolName)}...]</span>`;
            }
          } else if (evtType === 'status') {
            providerInfo = evtData;
          } else if (evtType === 'done') {
            ok = evtData.ok !== false;
            providerInfo = evtData;
            if (!aiText && evtData.text) aiText = evtData.text;
            streamDone = true;
            break;
          } else if (evtType === 'error') {
            ok = false;
            const errMsg = evtData.error || 'unknown error';
            aiText = (aiText ? aiText + '\n' : '') + '[ERROR] ' + errMsg;
            streamDone = true;
            break;
          }
        }
      }
      // Ensure reader is released
      try { reader.cancel(); } catch(e) {}
    } catch (err) {
      if (err.name === 'AbortError') {
        aiText += '\n[Cancelled]';
        ok = false;
      } else {
        aiText = aiText || '';
        aiText += '\n[Stream error] ' + String(err);
        ok = false;
      }
    }

    _streamAbort = null;
    _finishResponse(aiText.trim(), aiBody, ok, providerInfo);
  }

  // ── Mode switching ──
  // edit/chat = 내용만 다름. 패널 ON/OFF는 RunView.enterEditMode/exitEditMode 그대로 사용.
  // edit 탭 재클릭 = inline ON/OFF 토글 (float_run.js 원래 동작)
  // chat 탭 재클릭 = inline ON/OFF 토글 (동일 논리)
  // edit↔chat 전환 = 내용만 교체, 패널 ON/OFF 상태 유지.
  //   단, 패널이 닫혀있으면 열어줌 (chat 진입 시).

  // Called by slot_manager._apply() whenever the active slot changes.
  // The chat panel may already be open (_mode === 'chat'), in which case
  // _enterChatMode() early-returns and never rebinds — so the previous slot's
  // transcript would stay on screen. This rebinds + restores explicitly.
  function _onSlotChanged(name) {
    if (!name) return;
    if (name === _boundSlot) return;          // same slot → nothing to do
    // Not in chat mode: just update the binding. The next _enterChatMode()
    // will restore from this slot. (Do NOT touch the editor view here.)
    if (_mode !== 'chat') { _boundSlot = name; return; }
    // In chat mode: flush previous slot, rebind, restore new slot, redraw.
    if (_boundSlot && _transcript.length) _persistChat();
    if (_boundSlot && _jobTranscript.length) _persistJob();
    _boundSlot = name;
    // §4.8: temp_sid is per-slot and ends at a slot boundary. Drop it so the new
    // slot's Continue-OFF turns start a fresh temp session, never inheriting the
    // previous slot's temporary context.
    _activeTempSessionId = '';
    // Sync-first (cache hit draws immediately), else async refill then redraw.
    const syncChat = window.SlotStorage?.readChat?.(name);
    if (syncChat?.transcript?.length) {
      _transcript = syncChat.transcript.slice(-_MAX_TRANSCRIPT);
      if (syncChat.ctxMode) _ctxMode = syncChat.ctxMode;
      _activeLiveSessionId = syncChat.sessionId || '';   // P1-1: this slot's session
      _chatLogHtml = _rebuildHtml(_transcript);
    } else {
      _transcript = [];
      _chatLogHtml = '';
      _activeLiveSessionId = '';   // cleared; _restoreChat refills if cache miss
      _restoreChat(name).then(() => { if (_mode === 'chat') _renderActiveSubMode(); });
    }
    const syncJob = window.SlotStorage?.readJob?.(name);
    if (syncJob?.transcript?.length) {
      _jobTranscript = syncJob.transcript.slice(-_MAX_JOB);
    } else {
      _jobTranscript = [];
      _restoreJob(name).then(() => { if (_mode === 'chat') _renderActiveSubMode(); });
    }
    _renderActiveSubMode();   // draw immediately from sync state
  }

  function _enterChatMode() {
    if (_mode === 'chat') return;

    // Save edit state
    _editDoc = window.Editor?.getText?.() || '';
    _editCursor = window.Editor?.getCursor?.();

    // chat 전환 전에 원본 코드를 슬롯에 확실히 flush (비정상종료 대비)
    const curSlot = _currentSlotName();
    if (curSlot && _editDoc) {
      window.SlotStorage?.writeSlot?.(curSlot, { text: _editDoc, timestamp: Date.now() });
    }

    _mode = 'chat';

    // 슬롯 바인딩 — 슬롯이 바뀌었으면 이전 슬롯 챗 저장 + 새 슬롯 챗 복원
    if (curSlot && curSlot !== _boundSlot) {
      // 이전 슬롯 챗 저장 (있으면)
      if (_boundSlot && _transcript.length) _persistChat();
      _boundSlot = curSlot;
      // 새 슬롯 챗 복원 시도 (비동기지만 동기 우선)
      const syncData = window.SlotStorage?.readChat?.(curSlot);
      if (syncData?.transcript?.length) {
        _transcript = syncData.transcript.slice(-_MAX_TRANSCRIPT);
        if (syncData.ctxMode) _ctxMode = syncData.ctxMode;
        _activeLiveSessionId = syncData.sessionId || '';   // P1-1
        _restoredJobId = syncData.activeJobId || null;
        _chatLogHtml = _rebuildHtml(_transcript);
      } else {
        // Slot changed and the sync cache has no chat for it. The previous
        // slot's transcript must NOT carry over. Clear synchronously now to
        // avoid a flash of the old slot's chat, then async-restore may refill.
        _transcript = [];
        _chatLogHtml = '';
        _restoredJobId = null;
        _activeLiveSessionId = '';   // P1-1: _restoreChat refills on cache miss
        _restoreChat(curSlot).then(ok => {
          // ok=true → _restoreChat already refilled _transcript/_chatLogHtml
          if (_mode === 'chat') {
            const output = _el('runOutput');
            if (output) { output.innerHTML = _chatLogHtml; output.scrollTop = output.scrollHeight; }
          }
          _tryResumeLastJob(_restoredJobId);
        });
        _restoreJob(curSlot);
      }
    } else if (curSlot && (!_boundSlot || (_boundSlot === curSlot && !_transcript.length && !_jobTranscript.length))) {
      // First entry OR re-entry after reload.
      // Re-entry case: _onSlotChanged() already set _boundSlot=curSlot on boot
      // (while _mode was 'edit'), so the "slot changed" branch above is skipped
      // and _boundSlot is non-empty. But memory (_transcript/_jobTranscript) is
      // empty because nothing was restored yet. Detect that and restore from OPFS,
      // mirroring how the editor (slot_) restores its text on boot.
      _boundSlot = curSlot;
      const syncData = window.SlotStorage?.readChat?.(curSlot);
      if (syncData?.transcript?.length) {
        _transcript = syncData.transcript.slice(-_MAX_TRANSCRIPT);
        if (syncData.ctxMode) _ctxMode = syncData.ctxMode;
        _activeLiveSessionId = syncData.sessionId || '';   // P1-1
        _restoredJobId = syncData.activeJobId || null;
        _chatLogHtml = _rebuildHtml(_transcript);
      } else if (!_transcript.length) {
        _restoreChat(curSlot).then(ok => {
          if (ok && _mode === 'chat') {
            const output = _el('runOutput');
            if (output) { output.innerHTML = _chatLogHtml; output.scrollTop = output.scrollHeight; }
          }
          _tryResumeLastJob(_restoredJobId);   // re-subscribe to in-progress job (async path)
        });
      }
      // Job transcript restore (sync-first, async fallback) — independent of chat.
      const syncJob = window.SlotStorage?.readJob?.(curSlot);
      if (syncJob?.transcript?.length) {
        _jobTranscript = syncJob.transcript.slice(-_MAX_JOB);
        if (syncJob.activeJobId) _restoredJobId = syncJob.activeJobId;
      } else if (!_jobTranscript.length) {
        _restoreJob(curSlot).then(() => { if (_mode === 'chat') _renderActiveSubMode(); });
      }
    }

    // After slot restore: if this slot had an in-progress job, re-subscribe.
    // (async restore paths above handle their own resume inside .then)
    if (_restoredJobId) {
      const _rj = _restoredJobId; _restoredJobId = null;
      _tryResumeLastJob(_rj);
    } else if (_activeJobId && (!_jobEs || _jobEs.readyState === 2 /* CLOSED */)) {
      // Returning to chat (e.g. from the edit tab) without a slot change:
      // the restore block above was skipped, but a job may still be live and
      // its SSE detached/closed. Re-attach so output keeps flowing.
      _tryResumeLastJob(_activeJobId);
    }

    // Restore chat draft
    window.Editor?.setText?.(_chatDraft || '');
    if (_chatCursor) {
      try { window.Editor?.setCursor?.(_chatCursor); } catch(e) {}
    }

    // Switch output panel content
    const output = _el('runOutput');
    if (output) {
      _editOutputHtml = output.innerHTML;
      _renderActiveSubMode();
    }

    // ①c: 모드 전환은 뷰를 건드리지 않는다(현재 뷰 유지). 크기 변경은 ⬓(_toggleAiView) 전담.
    // (이전: 패널 닫혀있으면 inline 강제 열기 → 편집뷰에서 chat 전환 시 화면이 내려오던 원인)

    // 첨부 프리뷰 바 복원
    _updateAttachPreview();

    _updateTabUI();

    // Force the header toggle to render now (idempotent).
    _updateStopBtn();
    // Try to reattach the last active JOB (if any). Cheap status call;
    // does nothing if the previous job already finished.
    _tryResumeLastJob();
  }

  let _editOutputHtml = '';

  function _enterEditMode() {
    if (_mode === 'edit') return;
    _mode = 'edit';

    // Save chat draft
    _chatDraft = window.Editor?.getText?.() || '';
    _chatCursor = window.Editor?.getCursor?.();

    // Save chat log
    const output = _el('runOutput');
    if (output) {
      _chatLogHtml = output.innerHTML;
      output.innerHTML = _editOutputHtml;
    }

    // Restore edit doc
    window.Editor?.setText?.(_editDoc || '');
    if (_editCursor) {
      try { window.Editor?.setCursor?.(_editCursor); } catch(e) {}
    }

    // 첨부 프리뷰 바 숨김 (에디트모드에서는 불필요)
    const previewBar = _el('aiAttachPreview');
    if (previewBar) previewBar.style.display = 'none';

    _updateTabUI();
  }

  function _toggleMode() {
    if (_mode === 'edit') _enterChatMode();
    else _enterEditMode();
  }

  // §4-6 세그먼트 보더상태: 세 칸에 seg-active/seg-has/seg-empty 부여.
  // 글자점등(●) 대신 클래스로만 상태 표현. 글자는 항상 또렷.
  //   edit : 늘 코드창 → empty 안 씀. 활성이면 active, 아니면 무(기본색).
  //   chat : _transcript 있으면 has, 없으면 empty. 활성이면 active.
  //   job  : _jobTranscript(또는 진행중) 있으면 has, 없으면 empty. 활성이면 active.
  // 활성 판정: _mode==='chat' 이고 _chatSubMode 가 그 칸이면 그 칸이 활성.
  //           _mode==='edit' 이면 edit 칸이 활성.
  function _updateSegState() {
    const editBtn = _el('btnRunEdit');
    const chatBtn = _el('btnAiChat');
    const jobBtn  = _el('btnAiJobToggle');
    const setState = (el, { active, has }) => {
      if (!el) return;
      el.classList.remove('seg-active', 'seg-has', 'seg-empty');
      if (active) el.classList.add('seg-active');
      else if (has) el.classList.add('seg-has');
      else el.classList.add('seg-empty');
    };
    const editActive = (_mode !== 'chat');
    const chatActive = (_mode === 'chat' && _chatSubMode !== 'job');
    const jobActive  = (_mode === 'chat' && _chatSubMode === 'job');
    const chatHas = _transcript.length > 0;
    const jobHas  = _jobTranscript.length > 0 || !!_activeJobId;
    // edit: empty 미사용 → has=true 로 줘서 dim 안 되게(활성 아니면 기본색 유지)
    setState(editBtn, { active: editActive, has: true });
    setState(chatBtn, { active: chatActive, has: chatHas });
    setState(jobBtn,  { active: jobActive,  has: jobHas  });
  }

  // ── UI updates ──
  function _updateTabUI() {
    const editBtn = _el('btnRunEdit');
    const chatBtn = _el('btnAiChat');
    const title = _el('runPanelTitle');
    const aiLabel = _el('floatTpAiLabel');

    // TOOL 팝업 내용 모드별 전환
    const tpEditGroup = _el('floatTpEditGroup');
    const tpChatGroup = _el('floatTpChatGroup');
    const tpTitle = _el('floatTpTitle');

    if (_mode === 'chat') {
      if (editBtn) { editBtn.textContent = 'edit'; }
      if (chatBtn) { chatBtn.textContent = 'chat'; }
      if (title) { title.innerHTML = '<span style="font-size:9px;color:#a78bfa;">◆</span> AI CHAT'; }
      if (aiLabel) { aiLabel.innerHTML = 'AI <span style="font-size:6px;vertical-align:middle;color:#a78bfa;">●</span>'; }
      // TOOL 팝업: Edit 그룹 숨기고 Chat 그룹 표시
      if (tpEditGroup) tpEditGroup.style.display = 'none';
      if (tpChatGroup) tpChatGroup.style.display = 'block';
      if (tpTitle) tpTitle.textContent = 'AI Tool';
      // 미니런 패널: 챗모드 내용으로 교체
      _updateMiniRunForChat(true);
      // 패널 상단 보더 보라색
      const inner = _el('runPanelInner');
      if (inner && inner.style.borderTop) inner.style.borderTop = '2px solid #a78bfa';
      // Badge
      const badge = _el('aiBadge');
      if (badge) badge.style.display = 'block';
      // RUN 필은 그대로 유지 (스왑 없음)
    } else {
      // edit 모드 — 칸 상태는 _updateSegState 가 보더로 표시(글자점등 폐기)
      if (editBtn) { editBtn.textContent = 'edit'; }
      if (chatBtn) { chatBtn.textContent = 'chat'; }
      if (title) { title.innerHTML = '<span style="font-size:9px;">▶</span> OUTPUT'; }
      if (aiLabel) { aiLabel.textContent = 'AI'; }
      // TOOL 팝업: Edit 그룹 표시, Chat 그룹 숨김
      if (tpEditGroup) tpEditGroup.style.display = '';
      if (tpChatGroup) tpChatGroup.style.display = 'none';
      if (tpTitle) tpTitle.textContent = 'Run Tool';
      // 미니런 패널: 에디트모드 내용으로 복원
      _updateMiniRunForChat(false);
      // 패널 상단 보더 초록색 복원
      const inner = _el('runPanelInner');
      if (inner && inner.style.borderTop) inner.style.borderTop = '2px solid #4caf50';
      const badge = _el('aiBadge');
      if (badge) badge.style.display = 'none';
    }
    _updateSegState();
  }

  // ── 미니런 패널 내용을 챗모드/에디트모드에 따라 교체 ──
  // ── 2단(고정 도크) 내용을 챗/에디트 모드에 따라 교체 ──
  // STEP B ②: 떠다니던 miniRunPanel 폐기 → #rpDock2(붙박이)에 렌더.
  //  chat/job : Think / Add / ▾Model / Opt   (여기서 소유)
  //  edit     : Run / Line / Block           (float_run.js 가 소유 → 위임)
  function _updateMiniRunForChat(isChat) {
    const dock = document.getElementById('rpDock2');
    if (!dock) return;
    // 탭 전환(모드/하위모드 변경) 시 떠있는 부동 패널(첨부/모델/Opt) 자동 숨김.
    if (typeof _closeAiPanels === 'function') _closeAiPanels();

    if (isChat) {
      // chat 인지 job 하위모드인지에 따라 상단 라인색 구분 (§4-6)
      dock.dataset.mode = (_chatSubMode === 'job') ? 'job' : 'chat';
      dock.innerHTML = '';
      const body = document.createElement('div');
      body.className = 'minirun-body';

      const mkBtn = (icon, label, color, fn) => {
        const b = document.createElement('button');
        b.innerHTML = icon ? `<span class="mr-ico">${icon}</span> ${label}` : label;
        b.style.color = color;
        b.addEventListener('touchend', e => { e.preventDefault(); e.stopPropagation(); fn(); });
        b.addEventListener('mouseup', e => { e.stopPropagation(); fn(); });
        return b;
      };

      // ── chat 과 task 는 같은 입력부를 공유한다 ──
      // 셋(edit/chat/task)은 독립 컨텍스트. task 입력 = 작업 지시(job 세션에 쌓임, resume 대상).
      // 입력 도구(Add/Model/Cont/Session)는 chat=플랜 / task=실행 둘 다 필요하므로 동일.
      // task 일 때만 끝에 [⚙Manager](작업 관리)가 — 작업이 돌고 있을 때 — 추가된다(아래).

      // [＋Add] 첨부 — floatAiAttachPanel 재사용 (Add 버튼 바로 아래 앵커)
      const addBtn = mkBtn('\uFF0B', 'Add', '#7ee787', () => {
        const ap = _el('floatAiAttachPanel');
        if (ap) {
          const isOpen = ap.style.display === 'flex';
          ap.style.display = isOpen ? 'none' : 'flex';
          if (!isOpen) {
            const r = addBtn.getBoundingClientRect();
            ap.style.left = r.left + 'px';
            ap.style.top = (r.bottom + 6) + 'px';
            ap.style.right = 'auto'; ap.style.bottom = 'auto';
          }
        }
      });
      addBtn.classList.add('mr-add');
      body.appendChild(addBtn);

      // [▾Model] 모델 — 좌측 모델 패널(설정 허브: Continue·토큰·온도 포함)로 진입
      const _modelBtn = mkBtn('\u25BE', _aiModel, '#58a6ff', () => {
        const mp = _el('floatAiModelPanel');
        if (mp) {
          const isOpen = mp.classList.contains('open');
          if (isOpen) { _closeModelSheet(); return; }
          _openModelSheet();
        }
      });
      _modelBtn.id = 'floatAiMiniModelBtn';   // _selectModel 이 라벨 라이브 갱신
      _modelBtn.classList.add('mr-model');
      body.appendChild(_modelBtn);

      // [⟳ Cont] Continue 토글 — 2단에서 직접 토글(외부 토글). 패널 안 들어가도 됨.
      //   ON = 같은 세션으로 맥락 이어감(주황 강조) / OFF = 매 요청 새 세션(회색).
      //   _toggleContinue() 가 칩 + 패널 상태를 함께 갱신한다.
      const contBtn = mkBtn('', 'Cont', '#94A3B8', () => {
        _toggleContinue();
      });
      contBtn.id = 'rpDock2ContStatus';
      contBtn.style.color = '';   // 색은 CSS(.mr-status / .cont-on)가 소유
      contBtn.classList.add('mr-status');
      body.appendChild(contBtn);

      // [#세션id] 세션 상태등 — 표시 전용(향후 탭→세션 지정/리쥼).
      //   토큰이 어느 맥락에 연결/리쥼되는지를 가리키는 중요 정보.
      //   _activeJobId(연결중) 우선, 없으면 _restoredJobId(리쥼 대기), 둘 다 없으면 '#--'.
      const sessBtn = mkBtn('', 'session', '#94A3B8', () => {
        // A0: open Memory Editor overlay. Fallback to status toast if not loaded.
        if (window.MemEdit?.open) { window.MemEdit.open(); return; }
        const jid = _activeJobId || _restoredJobId;
        if (jid) window.UI?.showToast?.('세션 ' + jid + (_activeJobId ? ' (연결됨)' : ' (리쥼 대기)'), 1600);
        else window.UI?.showToast?.('연결된 세션 없음', 1000);
      });
      sessBtn.id = 'rpDock2SessStatus';
      sessBtn.style.color = '';   // 색은 CSS(.mr-status / .sess-*)가 소유
      sessBtn.classList.add('mr-status');
      body.appendChild(sessBtn);

      // [🔍 검색] google_search grounding 토글 — ON 이면 다음 질문에 검색 결합.
      const searchBtn = mkBtn('🔍', '검색', '#94A3B8', () => { _toggleSearch(); });
      searchBtn.id = 'rpDock2Search';
      searchBtn.classList.add('mr-status');
      body.appendChild(searchBtn);

      // [🎙 음성] 음성 I/O 묶음 — 탭하면 옵션 팝오버가 열린다:
      //   음성입력(STT, 1회) / 음성대화(핸즈프리 루프) / 자동읽기(TTS).
      const voiceBtn = mkBtn('🎙', '음성', '#94A3B8', () => { _toggleVoiceMenu(); });
      voiceBtn.id = 'rpDock2Voice';
      voiceBtn.classList.add('mr-status');
      body.appendChild(voiceBtn);

      // [⚙Manager] — task(=job 하위모드)에서만. 작업 관리(Stop/Tail/Check/Logs) 진입점.
      //   작업이 돌고 있을 때(_activeJobId) 점이 켜져 강조된다.
      if (_chatSubMode === 'job') {
        const mgrBtn = mkBtn('\u2699', 'Manager', '#94A3B8', () => { _openTaskManager(); });
        mgrBtn.id = 'rpDock2Manager';
        mgrBtn.style.color = '';
        mgrBtn.classList.add('mr-status', 'mr-manager');
        body.appendChild(mgrBtn);
      }

      dock.appendChild(body);
      // BUG2: re-applying innerHTML drops nothing but the is-collapsed class can be
      // stale (carried over from edit mode). Force-sync screen to the single source
      // of truth (RunView.dock2Collapsed). Policy: only the ☰ toggle may collapse;
      // a re-render must never hide the dock on its own.
      const _collapsed = !!window.RunView?.dock2Collapsed;
      dock.classList.toggle('is-collapsed', _collapsed);
      _syncContStatus();
      _syncSessStatus();
      _syncSearchChip();
      _syncSpeakChip();
      _syncMicChip();
      _syncVoiceChip();
      if (_chatSubMode === 'job') _syncManagerStatus();
    } else {
      // edit 모드: Run/Line/Block 은 float_run.js 가 소유 → 재렌더 위임.
      dock.dataset.mode = 'edit';
      window.RunView?._refreshMiniRun?.();
    }
  }

  // Continue 상태등 동기화 — _continueMode 를 읽어 2단 칩의 색/라벨/경고상태를 맞춘다.
  // ON 이면 .cont-on (주황 경고), OFF 면 회색.
  function _syncContStatus() {
    const chip = document.getElementById('rpDock2ContStatus');
    if (!chip) return;
    chip.textContent = 'Cont';
    chip.classList.toggle('cont-on', !!_continueMode);
    chip.setAttribute('aria-label', _continueMode ? 'Continue ON (토큰↑)' : 'Continue OFF');
  }

  // Continue 토글 — 외부(2단 Cont 칩)와 모델 패널 양쪽이 공유하는 단일 진입점.
  // 어느 쪽에서 눌러도 _continueMode + 칩 + 패널버튼/태그가 함께 갱신된다.
  function _toggleContinue() {
    _continueMode = !_continueMode;
    try { localStorage.setItem('usekit.ai.continue', _continueMode ? '1' : '0'); } catch (e) {}
    // §4.8: flipping Continue back ON ends the temporary flow — the next turn
    // belongs to the main session again, so forget the accumulated temp_sid.
    if (_continueMode) _activeTempSessionId = '';
    const pbtn = _el('aiOptContinue');
    const ptag = _el('aiOptContTag');
    if (pbtn) pbtn.classList.toggle('is-active', _continueMode);
    if (ptag) ptag.textContent = _continueMode ? 'ON' : 'OFF';
    _syncContStatus();
    window.UI?.showToast?.(_continueMode
      ? 'Continue: ON — 같은 세션으로 맥락 이어감(토큰↑)'
      : 'Continue: OFF — 매 요청 새 세션', 1000);
  }

  // 🔍 Search grounding toggle + chip sync (state shown via .search-on, not a dim).
  function _syncSearchChip() {
    const chip = document.getElementById('rpDock2Search');
    if (!chip) return;
    chip.classList.toggle('search-on', !!_searchMode);
    chip.setAttribute('aria-label', _searchMode ? '검색 ON (질문에 웹 검색 결합)' : '검색 OFF');
  }
  function _toggleSearch() {
    _searchMode = !_searchMode;
    try { localStorage.setItem('usekit.ai.search', _searchMode ? '1' : '0'); } catch (e) {}
    _syncSearchChip();
    window.UI?.showToast?.(_searchMode
      ? '🔍 검색: ON — 다음 질문에 웹 검색 결합'
      : '🔍 검색: OFF', 1000);
  }

  // ── 🎙 Voice UI: one pill + popover with three toggle rows ──
  //   The 🎙 pill glows (.voice-on) whenever ANY voice feature is live
  //   (dictating, in a call, or auto-read on). Popover rows mirror state.
  function _syncVoiceUI() {
    const pill = document.getElementById('rpDock2Voice');
    if (pill) pill.classList.toggle('voice-on', !!(_voiceLoopOn || _autoSpeak || _micListening));
    const dictate = document.getElementById('aiVoiceDictate');
    if (dictate) dictate.classList.toggle('is-active', _micListening);
    const talk = document.getElementById('aiVoiceTalk');
    const talkTag = document.getElementById('aiVoiceTalkTag');
    if (talk) talk.classList.toggle('is-active', _voiceLoopOn);
    if (talkTag) talkTag.textContent = _voiceLoopOn ? 'ON' : 'OFF';
    const read = document.getElementById('aiVoiceRead');
    const readTag = document.getElementById('aiVoiceReadTag');
    if (read) read.classList.toggle('is-active', _autoSpeak);
    if (readTag) readTag.textContent = _autoSpeak ? 'ON' : 'OFF';
    const aitts = document.getElementById('aiVoiceAiTts');
    const aittsTag = document.getElementById('aiVoiceAiTtsTag');
    if (aitts) aitts.classList.toggle('is-active', _aiTts);
    if (aittsTag) aittsTag.textContent = _aiTts ? 'ON' : 'OFF';
  }
  // Legacy names kept as thin aliases (still called from the render path).
  function _syncSpeakChip() { _syncVoiceUI(); }

  let _voiceMenuWired = false;
  function _wireVoiceMenu() {
    if (_voiceMenuWired) return;
    const dictate = _el('aiVoiceDictate');
    const talk = _el('aiVoiceTalk');
    const read = _el('aiVoiceRead');
    if (dictate) dictate.addEventListener('click', () => {
      const vp = _el('floatAiVoicePanel'); if (vp) vp.style.display = 'none';
      _toggleMic();                                   // Mode 1: dictate → editor
    });
    if (talk) talk.addEventListener('click', () => { _toggleVoiceLoop(); _syncVoiceUI(); });
    if (read) read.addEventListener('click', () => { _toggleAutoSpeak(); _syncVoiceUI(); });
    const aitts = _el('aiVoiceAiTts');
    if (aitts) aitts.addEventListener('click', () => { _toggleAiTts(); _syncVoiceUI(); });
    _voiceMenuWired = !!(dictate && talk && read);
  }
  // Open/close the voice options popover, anchored under the 🎙 pill (right-aligned
  // so it never runs off the right edge where the pill sits).
  function _toggleVoiceMenu() {
    const vp = _el('floatAiVoicePanel');
    if (!vp) { _toggleVoiceLoop(); return; }          // fallback if markup missing
    _wireVoiceMenu();
    const isOpen = vp.style.display === 'flex';
    const ap = _el('floatAiAttachPanel'); if (ap) ap.style.display = 'none';
    if (isOpen) { vp.style.display = 'none'; return; }
    vp.style.display = 'flex';
    const pill = document.getElementById('rpDock2Voice');
    if (pill) {
      const r = pill.getBoundingClientRect();
      vp.style.left = 'auto';
      vp.style.right = Math.max(8, window.innerWidth - r.right) + 'px';
      vp.style.top = (r.bottom + 6) + 'px';
      vp.style.bottom = 'auto';
    }
    _syncVoiceUI();
  }

  function _toggleAutoSpeak() {
    _autoSpeak = !_autoSpeak;
    try { localStorage.setItem('usekit.ai.autospeak', _autoSpeak ? '1' : '0'); } catch (e) {}
    _syncVoiceUI();
    window.UI?.showToast?.(_autoSpeak
      ? '🔊 자동읽기: ON — 답변을 자동 재생'
      : '🔊 자동읽기: OFF', 1000);
  }

  // ✨ AI 음성 toggle. OFF = browser TTS (free/instant). ON = Gemini TTS (quality,
  // but burns tokens) — applies to 자동읽기/음성대화 reading.
  function _toggleAiTts() {
    _aiTts = !_aiTts;
    try { localStorage.setItem('usekit.ai.aitts', _aiTts ? '1' : '0'); } catch (e) {}
    _syncVoiceUI();
    window.UI?.showToast?.(_aiTts
      ? '✨ AI 음성: ON — 고품질 Gemini TTS (토큰 소모 큼)'
      : '✨ AI 음성: OFF — 기기 내장 TTS (무료)', 1400);
  }

  // ── 🎤 Voice input (STT) — Mode 1: speech → editor (prompt), review → RUN ──
  //   Browser SpeechRecognition (Samsung Internet 4+ supports it). If absent,
  //   we degrade gracefully (Gemini-transcription fallback is a later step).
  let _sttRec = null;          // active SpeechRecognition instance
  let _micListening = false;

  function _sttSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  // onInterim(text), onFinal(text), onEnd(errOrNull)
  function _sttStart(onInterim, onFinal, onEnd) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { onEnd && onEnd('unsupported'); return false; }
    const rec = new SR();
    rec.lang = 'ko-KR';
    rec.interimResults = true;
    rec.continuous = false;     // Mode 1: a single utterance per tap
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      let interim = '', finalText = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript;
        else interim += r[0].transcript;
      }
      if (interim) onInterim && onInterim(interim);
      if (finalText) onFinal && onFinal(finalText);
    };
    rec.onerror = (e) => { onEnd && onEnd(e.error || 'error'); };
    rec.onend = () => { onEnd && onEnd(null); };
    _sttRec = rec;
    try { rec.start(); } catch (e) { onEnd && onEnd('start-failed'); return false; }
    return true;
  }

  function _sttStop() { if (_sttRec) { try { _sttRec.stop(); } catch (e) {} } }

  function _syncMicChip() { _syncVoiceUI(); }   // mic pill folded into 🎙 popover

  function _toggleMic() {
    if (_micListening) { _sttStop(); return; }   // onend resets the chip
    if (!_sttSupported()) {
      window.UI?.showToast?.('이 브라우저는 음성입력(STT) 미지원 — Gemini fallback은 다음 단계', 2200);
      return;
    }
    // Append onto whatever is already in the editor (don't clobber typed text).
    const base = (window.Editor?.getText?.() || '');
    const sep = (base && !/\s$/.test(base)) ? ' ' : '';
    let acc = '';   // final text accumulated this session
    _micListening = true; _syncMicChip();
    window.UI?.showToast?.('🎤 듣는 중… 말하면 입력창에 들어가요', 1500);
    _sttStart(
      (interim) => { window.Editor?.setText?.(base + sep + acc + interim); },
      (finalText) => { acc += finalText; window.Editor?.setText?.(base + sep + acc); },
      (err) => {
        _micListening = false; _syncMicChip();
        if (err === 'unsupported' || err === 'start-failed') {
          window.UI?.showToast?.('🎤 시작 실패 — 권한/지원 확인', 1800);
        } else if (err && err !== 'no-speech' && err !== 'aborted') {
          window.UI?.showToast?.('🎤 오류: ' + err, 1800);
        } else {
          window.UI?.showToast?.('🎤 입력 완료 — 확인 후 RUN 으로 전송', 1500);
        }
      }
    );
  }

  // ── 📞 Mode 2: hands-free voice conversation loop ──
  //   FSM:  LISTEN ──(onend: browser endpointing)──▶ auto-SEND ──▶ AI reply
  //           ▲                                                      │
  //           └──────────── relisten ◀── TTS playback ends ◀── auto-SPEAK
  //   Mic and TTS never run at once (no echo): we only relisten in _voiceAfterSpeak,
  //   which fires from _speak's onDone (playback finished/failed).
  let _voiceLoopOn = false;

  function _syncVoiceChip() { _syncVoiceUI(); }   // pill state via .voice-on class

  // One listening turn. On natural pause (onend), auto-send or relisten if silent.
  function _voiceListen() {
    if (!_voiceLoopOn) return;
    let acc = '';
    _micListening = true; _syncMicChip();
    _sttStart(
      null,                                   // interim ignored in loop mode
      (finalText) => { acc += finalText; },
      (err) => {
        _micListening = false; _syncMicChip();
        if (!_voiceLoopOn) return;            // exited mid-listen
        const text = acc.trim();
        if (text) {
          _voiceSend(text);                   // 자동 발신
        } else if (err && err !== 'no-speech' && err !== 'aborted') {
          window.UI?.showToast?.('🎤 오류: ' + err + ' — 음성대화 종료', 1800);
          _voiceStop();
        } else {
          setTimeout(() => _voiceListen(), 300);   // silence → listen again
        }
      }
    );
  }

  // Auto-send the spoken turn through the normal chat pipeline. The reply then
  // flows to _finishResponse → _speak → _voiceAfterSpeak (resume listening).
  function _voiceSend(text) {
    if (!_voiceLoopOn) return;
    if (_aiRunning || _sessionLocked) {       // busy → wait a beat, retry
      setTimeout(() => _voiceSend(text), 400);
      return;
    }
    _sendPrompt(text);
  }

  // Called after the AI reply finished playing (or had nothing to play).
  function _voiceAfterSpeak() {
    if (!_voiceLoopOn) return;
    setTimeout(() => _voiceListen(), 250);     // small gap, then next turn
  }

  function _voiceStop() {
    _voiceLoopOn = false; _syncVoiceChip();
    _sttStop();
    _stopSpeak();                 // halt any in-progress read + reset its 🔊 icon
    _micListening = false; _syncMicChip();
    window.UI?.showToast?.('📞 음성대화 종료', 1000);
  }

  function _toggleVoiceLoop() {
    if (_voiceLoopOn) { _voiceStop(); return; }
    if (!_sttSupported()) {
      window.UI?.showToast?.('이 브라우저는 음성입력 미지원 — 음성대화 불가', 2200);
      return;
    }
    _voiceLoopOn = true; _syncVoiceChip();
    window.UI?.showToast?.('📞 음성대화 시작 — 말하면 자동 전송·응답·읽기 (탭하면 종료)', 2200);
    _voiceListen();
  }

  // ── General USEKIT Project toggle (project_meta.md system injection) ──
  function _syncProjectMetaChip() {
    const tag = _el('aiOptProjMetaTag');
    if (tag) tag.textContent = _projectMeta ? 'ON' : 'OFF';
    const btn = _el('aiOptProjMeta');
    if (btn) btn.classList.toggle('is-active', _projectMeta);
    // Master OFF → section cards stay (checks preserved) but show as inactive.
    const cards = _el('metaCards');
    if (cards) cards.classList.toggle('master-off', !_projectMeta);
  }
  function _toggleProjectMeta() {
    _projectMeta = !_projectMeta;
    try { localStorage.setItem('usekit.ai.projectMeta', _projectMeta ? '1' : '0'); } catch (e) {}
    _syncProjectMetaChip();
    window.UI?.showToast?.(_projectMeta
      ? 'General USEKIT Project: ON — project_meta.md 를 system 으로 주입'
      : 'General USEKIT Project: OFF', 1200);
  }

  // ── META section cards (parse project_meta.md → per-section check+edit) ──
  // In-memory model: { Project:{body,enabled}, User:..., Meta:..., Request:... }
  const _META_SECS = ['Project', 'User', 'Meta', 'Request'];
  const _META_DEFAULT_ON = { Project: true, User: true, Meta: true, Request: false };
  let _metaModel = null;          // populated from server on first open
  let _metaPreamble = '';         // text before first ## header (e.g. "# USEKIT Project Meta")

  function _parseMetaText(text) {
    // → {preamble, secs:{name:{body,enabled,known}}}  (mirror of backend parser)
    const lines = (text || '').split('\n');
    const re = /^##\s+(.+?)(?:\s+\[(on|off)\])?\s*$/i;
    const secs = {};
    let cur = null, marker = null, buf = [], pre = [], started = false;
    const flush = () => {
      if (cur === null) return;
      const known = _META_DEFAULT_ON.hasOwnProperty(cur);
      const enabled = marker !== null ? marker
        : (known ? _META_DEFAULT_ON[cur] : false);
      secs[cur] = { body: buf.join('\n').trim(), enabled, known };
    };
    for (const line of lines) {
      const m = line.match(re);
      if (m) {
        flush();
        started = true;
        cur = m[1].trim();
        marker = m[2] == null ? null : (m[2].toLowerCase() === 'on');
        buf = [];
      } else if (cur !== null) {
        buf.push(line);
      } else if (!started) {
        pre.push(line);
      }
    }
    flush();
    return { preamble: pre.join('\n').trim(), secs };
  }

  function _serializeMeta() {
    // model → project_meta.md text (preamble + 4 sections w/ markers)
    const out = [];
    if (_metaPreamble) out.push(_metaPreamble, '');
    for (const name of _META_SECS) {
      const s = _metaModel[name] || { body: '', enabled: _META_DEFAULT_ON[name] };
      out.push(`## ${name} [${s.enabled ? 'on' : 'off'}]`);
      out.push(s.body || '');
      out.push('');
    }
    return out.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
  }

  function _renderMetaCards() {
    if (!_metaModel) return;
    for (const name of _META_SECS) {
      const s = _metaModel[name] || { body: '', enabled: _META_DEFAULT_ON[name] };
      const chk = document.querySelector(`.meta-chk[data-sec="${name}"]`);
      const card = document.querySelector(`.meta-card[data-sec="${name}"]`);
      if (chk) chk.textContent = s.enabled ? '☑' : '▢';
      if (card) card.classList.toggle('sec-on', s.enabled);
    }
  }

  function _loadMetaCards() {
    return fetch('/api/project_meta')
      .then(r => r.json())
      .then(j => {
        const parsed = _parseMetaText((j && j.ok) ? (j.text || '') : '');
        _metaPreamble = parsed.preamble || '# USEKIT Project Meta';
        _metaModel = {};
        for (const name of _META_SECS) {
          _metaModel[name] = parsed.secs[name]
            || { body: '', enabled: _META_DEFAULT_ON[name] };
        }
        _renderMetaCards();
        _refreshOpenPreviews();   // keep any expanded preview in sync after reload
      })
      .catch(() => {
        _metaModel = {};
        for (const name of _META_SECS) _metaModel[name] = { body: '', enabled: _META_DEFAULT_ON[name] };
        _renderMetaCards();
      });
  }

  // Save: snapshot the working copy → project_meta.last.md (manual checkpoint).
  function _saveMetaLast() {
    return fetch('/api/project_meta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ snapshot: true }),
    })
      .then(r => r.json())
      .then(j => window.UI?.showToast?.(j && j.ok ? '저장됨' : '저장 실패', 1200))
      .catch(() => window.UI?.showToast?.('저장 실패(네트워크)', 1500));
  }

  // Load: restore the last snapshot → working copy + repaint.
  function _restoreMetaLast() {
    return fetch('/api/project_meta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ restore: true }),
    })
      .then(r => r.json())
      .then(j => {
        if (j && j.ok) {
          const parsed = _parseMetaText(j.text || '');
          _metaPreamble = parsed.preamble || '# USEKIT Project Meta';
          _metaModel = {};
          for (const name of _META_SECS) {
            _metaModel[name] = parsed.secs[name] || { body: '', enabled: _META_DEFAULT_ON[name] };
          }
          _renderMetaCards();
          _refreshOpenPreviews();
          window.UI?.showToast?.('직전 저장본 불러옴', 1200);
        } else if (j && j.error === 'no_snapshot') {
          window.UI?.showToast?.('저장된 백업 없음', 1500);
        } else {
          window.UI?.showToast?.('불러오기 실패', 1500);
        }
      })
      .catch(() => window.UI?.showToast?.('불러오기 실패(네트워크)', 1500));
  }

  function _toggleMetaSection(name) {
    if (!_metaModel) return;
    const s = _metaModel[name] || (_metaModel[name] = { body: '', enabled: false });
    s.enabled = !s.enabled;
    _renderMetaCards();
    _saveMetaCards(false);   // auto-save: toggle persists to file immediately
  }

  // Inline readonly preview (peek) — toggles the body under the card head.
  function _toggleMetaPreview(name) {
    const pv = document.querySelector(`.meta-preview[data-sec="${name}"]`);
    const exp = document.querySelector(`.meta-card[data-sec="${name}"] .meta-exp`);
    if (!pv) return;
    const show = pv.style.display === 'none';
    if (show) {
      const body = (_metaModel && _metaModel[name] && _metaModel[name].body) || '';
      pv.textContent = body || '(empty)';
    }
    pv.style.display = show ? 'block' : 'none';
    if (exp) exp.textContent = show ? '▾' : '▸';
  }

  function _refreshOpenPreviews() {
    // keep any open preview in sync after edits
    document.querySelectorAll('.meta-preview').forEach(pv => {
      if (pv.style.display !== 'none') {
        const name = pv.getAttribute('data-sec');
        const body = (_metaModel && _metaModel[name] && _metaModel[name].body) || '';
        pv.textContent = body || '(empty)';
      }
    });
  }

  // Open the big editor overlay for a single section. Edits commit to the
  // in-memory model on Done; the sheet's Save persists to file (one source).
  let _meEditing = null;   // section name currently in the overlay
  const _META_HINT = {
    Project: 'Project rules & architecture. Injected into system.',
    User: 'Who the user is, preferences, coding style. Injected into system.',
    Meta: 'Routing/runtime hints. Injected into system.',
    Request: 'Injected before the current user message. Keep it off for normal chat.',
  };
  const _META_DEST = {
    Project: 'system', User: 'system', Meta: 'system', Request: 'user prefix',
  };

  function _expandMetaSection(name) {
    if (!_metaModel) return;
    _meEditing = name;
    const modal = _el('metaEditModal');
    const ta = _el('meText');
    const title = _el('meTitle');
    const dest = _el('meDest');
    const hint = _el('meHint');
    if (!modal || !ta) return;
    if (title) title.textContent = name;
    if (dest) dest.textContent = _META_DEST[name] || '';
    if (hint) hint.textContent = _META_HINT[name] || '';
    ta.value = (_metaModel[name] && _metaModel[name].body) || '';
    ta.readOnly = false;
    const _doneBtn = _el('meDone'); if (_doneBtn) _doneBtn.style.display = '';
    modal.style.display = 'block';
    modal.setAttribute('aria-hidden', 'false');
    setTimeout(() => ta.focus(), 50);
  }

  function _closeMetaEdit(commit) {
    const modal = _el('metaEditModal');
    const ta = _el('meText');
    if (commit && _meEditing && _metaModel && ta) {
      if (!_metaModel[_meEditing]) _metaModel[_meEditing] = { body: '', enabled: false };
      _metaModel[_meEditing].body = ta.value;
      _renderMetaCards();
      _refreshOpenPreviews();
      _saveMetaCards(false);   // auto-save: edited body persists immediately
    }
    _meEditing = null;
    if (modal) { modal.style.display = 'none'; modal.setAttribute('aria-hidden', 'true'); }
  }

  // Read-only reuse of the me* overlay (no new modal). _meEditing=null is the
  // safety latch: _closeMetaEdit only commits when _meEditing is truthy, so a
  // viewer Done/Cancel can never write into _metaModel (META can't be polluted).
  // Used by Memory Editor card [Input]/[Output] to show call-body text.
  function _openMetaView(title, text, opts) {
    opts = opts || {};
    _meEditing = null;                       // latch: blocks any commit path
    const modal = _el('metaEditModal');
    const ta = _el('meText');
    if (!modal || !ta) return;
    const titleEl = _el('meTitle');
    const dest = _el('meDest');
    const hint = _el('meHint');
    const doneBtn = _el('meDone');
    if (titleEl) titleEl.textContent = title || '';
    if (dest) dest.textContent = opts.dest || '';
    if (hint) hint.textContent = opts.hint || 'read-only';
    ta.value = (text == null ? '' : String(text));
    ta.readOnly = true;                      // view mode
    if (doneBtn) doneBtn.style.display = 'none';
    modal.style.display = 'block';
    modal.setAttribute('aria-hidden', 'false');
  }

  // Expose so Memory Editor (separate IIFE) can call it without touching me* internals.
  try { window.MetaView = { open: _openMetaView }; } catch (e) {}

  function _saveMetaCards(silent) {
    if (!_metaModel) return Promise.resolve();
    // bodies already live in _metaModel (edited via the overlay → Done).
    return fetch('/api/project_meta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: _serializeMeta() }),
    })
      .then(r => r.json())
      .then(j => {
        if (!silent) {
          window.UI?.showToast?.(j && j.ok ? 'META 저장됨' : '저장 실패', 1200);
        }
      })
      .catch(() => { if (!silent) window.UI?.showToast?.('저장 실패(네트워크)', 1500); });
  }

  function _resetMetaCards() {
    fetch('/api/project_meta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reset: true }),
    })
      .then(r => r.json())
      .then(j => {
        if (j && j.ok) {
          const parsed = _parseMetaText(j.text || '');
          _metaPreamble = parsed.preamble || '# USEKIT Project Meta';
          _metaModel = {};
          for (const name of _META_SECS) {
            _metaModel[name] = parsed.secs[name] || { body: '', enabled: _META_DEFAULT_ON[name] };
          }
          _renderMetaCards();
          _refreshOpenPreviews();   // sync expanded preview bodies to the default
          // (section states come from the default template; master forced ON here.)
          if (!_projectMeta) {
            _projectMeta = true;
            try { localStorage.setItem('usekit.ai.projectMeta', '1'); } catch (e) {}
          }
          _syncProjectMetaChip();
          window.UI?.showToast?.('기본값 복원 — General USEKIT Project ON', 1400);
        }
      })
      .catch(() => window.UI?.showToast?.('복원 실패', 1500));
  }

  // 세션 상태등 동기화 — 어느 세션에 토큰을 연결/리쥼하는지 표시.
  //   _activeJobId(연결중)=초록 / _restoredJobId(리쥼 대기)=주황 / 없음=흐린 '#--'.
  //   세션 변동 지점이 많으므로, 모든 곳에서 불리는 _updateStopBtn() 끝에서 호출(누락방지).
  function _syncSessStatus() {
    const chip = document.getElementById('rpDock2SessStatus');
    if (!chip) return;
    const active = _activeJobId;
    const resume = !active && _restoredJobId ? _restoredJobId : null;
    const jid = active || resume;
    const short = jid ? jid.slice(0, 6) : 'session';
    chip.textContent = short;
    chip.classList.toggle('sess-on', !!active);
    chip.classList.toggle('sess-resume', !!resume);
    chip.setAttribute('aria-label',
      active ? ('세션 연결됨 ' + jid) : (resume ? ('리쥼 대기 ' + jid) : '세션 없음'));
  }

  // TASK Tail 상태등 동기화 — Manager 패널 안 Tail 칩(_taskTail) 점/색.
  function _syncTaskStatus() {
    const chip = document.getElementById('tmTailBtn');
    if (!chip) return;
    chip.classList.toggle('on', !!_taskTail);
    chip.setAttribute('aria-label', _taskTail ? 'Tail ON (자동 스크롤)' : 'Tail OFF');
  }

  // Manager 칩 상태 — 작업이 돌고 있으면(_activeJobId) 점 켜고 강조.
  function _syncManagerStatus() {
    const chip = document.getElementById('rpDock2Manager');
    if (!chip) return;
    const running = !!_activeJobId;
    chip.textContent = 'Manager';
    chip.classList.toggle('mgr-on', running);
    chip.setAttribute('aria-label', running ? '작업 실행 중 — 관리' : '작업 관리 (대기)');
  }

  // ── TASK Manager 패널 — 작업 관리(Stop/Tail/Check/Logs) ──
  // 2단을 입력부로 비우는 대신, 관리 도구는 여기 시트로 격리(필요할 때만).
  function _openTaskManager() {
    let p = _el('taskManagerPanel');
    if (p) { p.remove(); return; }   // 열려있으면 토글로 닫기
    p = document.createElement('div');
    p.id = 'taskManagerPanel';
    p.className = 'task-mgr-panel';
    const jid = _activeJobId || _restoredJobId;
    const running = !!_activeJobId;
    p.innerHTML = `
      <div class="tm-head">
        <span class="tm-title">⚙ Task Manager</span>
        <span class="tm-state ${running ? 'on' : ''}">${running ? '● 실행 중' : '○ 대기'}</span>
        <button class="tm-x" type="button">✕</button>
      </div>
      <div class="tm-sess">${jid ? ('세션 ' + jid.slice(0, 12)) : '연결된 세션 없음'}</div>
      <div class="tm-grid">
        <button class="tm-btn tm-stop"  type="button"><span>■</span> Stop</button>
        <button class="tm-btn tm-tail" id="tmTailBtn" type="button"><span class="tm-dot"></span> Tail</button>
        <button class="tm-btn tm-check" type="button"><span>○</span> Check</button>
        <button class="tm-btn tm-logs"  type="button"><span>≡</span> Logs</button>
      </div>`;
    // 위치: Manager 버튼 위쪽(2단 바로 아래 출력 영역 좌상단)에 띄움
    const dock = _el('rpDock2');
    if (dock) {
      const r = dock.getBoundingClientRect();
      p.style.top = (r.bottom + 6) + 'px';
    }
    document.body.appendChild(p);

    const close = () => { p.remove(); };
    p.querySelector('.tm-x').addEventListener('click', close);

    // Stop — 실배선
    p.querySelector('.tm-stop').addEventListener('click', () => {
      if (_activeJobId || _streamAbort) { _stopActive(); window.UI?.showToast?.('작업 중단 요청', 900); }
      else window.UI?.showToast?.('진행 중인 작업이 없습니다', 900);
      close();
    });
    // Tail — 자동 스크롤 토글
    p.querySelector('.tm-tail').addEventListener('click', () => {
      _taskTail = !_taskTail;
      _syncTaskStatus();
      if (_taskTail) { const o = _el('runOutput'); if (o) o.scrollTop = o.scrollHeight; }
      window.UI?.showToast?.(_taskTail ? 'Tail: ON (새 로그 자동 따라감)' : 'Tail: OFF', 1000);
    });
    // Check — 상태 확인(틀)
    p.querySelector('.tm-check').addEventListener('click', () => {
      const j = _activeJobId || _restoredJobId;
      window.UI?.showToast?.(j ? ('작업 ' + j.slice(0,8) + ' 상태 확인 (준비 중)') : '확인할 작업이 없습니다', 1200);
    });
    // Logs — 출력 맨 아래로
    p.querySelector('.tm-logs').addEventListener('click', () => {
      const o = _el('runOutput'); if (o) o.scrollTop = o.scrollHeight;
      window.UI?.showToast?.('로그 최신으로', 700);
      close();
    });
    _syncTaskStatus();
  }

  // ── §4-6 평탄화 세그먼트 라우터 ──────────────────────────
  // edit│chat│job 한 줄 세그먼트의 단일 진입점. chat/job 은 "모드 진입 +
  // 하위모드 설정" 두 동작의 합이라, 순서를 여기서 보장한다.
  //   edit → _enterEditMode()
  //   chat → (edit이면)_enterChatMode() 먼저 → _setChatSubMode('chat')
  //   job  → activeJob 있으면 잠금 / 없으면 _enterChatMode() 먼저 → _setChatSubMode('job')
  // _enterChatMode()는 _mode를 chat으로 만들고(이미 chat이면 no-op), 그 뒤
  // _setChatSubMode는 _mode==='chat' 조건을 만족해 하위모드 화면 스왑까지 처리.
  // ※ 출력 높이는 이 경로에서 바뀌지 않는다(호출 함수들이 이미 보장).
  function _gotoSegment(seg) {
    if (seg === 'edit') {
      _enterEditMode();
      return;
    }
    if (seg === 'job') {
      // JOB 진행 중에는 하위모드 변경 금지(기존 규칙 보존).
      if (_activeJobId) {
        _appendToChatLog('ai', '[INFO] 진행 중인 JOB이 있어 모드 변경 불가. Stop 후 시도하세요.');
        return;
      }
      _enterChatMode();          // edit이면 chat으로 진입(이미 chat이면 no-op)
      _setChatSubMode('job');    // 그 다음 하위모드 job
      return;
    }
    // 기본: chat
    _enterChatMode();            // edit이면 chat으로 진입
    _setChatSubMode('chat');     // 그 다음 하위모드 chat
  }

  // ── 1단 라벨 / chat 버튼 공유: chat 모드에서 출력 보기 상태 순환 ──
  // inline → overlay → inline … (둘 다 닫혔으면 inline 으로 연다)
  // ※ 출력 높이는 건드리지 않는다. 오버레이는 is-open 클래스(덮기), inline 은
  //   RunView.enterEditMode 의 기존 메커니즘. 둘 다 출력 흐름을 밀지 않는다.
  function _cycleChatView() {
    if (_mode !== 'chat') return;
    const panel = _el('runPanel');
    const isOverlay = panel && panel.classList.contains('is-open');
    const isInline = window.RunView?.editModeActive;
    if (isInline) {
      // inline → overlay 전환
      window.RunView.exitEditMode(false); // inline 닫기
      if (panel) {
        panel.classList.add('is-open');    // overlay 열기
        const btnOut = _el('floatBtnOutput');
        if (btnOut) btnOut.classList.add('is-active');
      }
    } else if (isOverlay) {
      // overlay → inline 복귀
      if (panel) panel.classList.remove('is-open');
      const btnOut = _el('floatBtnOutput');
      if (btnOut) btnOut.classList.remove('is-active');
      window.RunView?.enterEditMode?.();
      _updateTabUI();
    } else {
      // 둘 다 닫힘 → inline으로 열기
      window.RunView?.enterEditMode?.();
      _updateTabUI();
    }
  }

  // STEP B ①b: ⬓ view toggle — mode-agnostic 2-state (overlay <-> inline edit).
  // Independent of _cycleChatView (chat-only 3-state). Calls RunView API directly.
  // This button is the ONLY intentional output-height change (§4-6 explicit exception).
  function _toggleAiView() {
    const panel = _el('runPanel');
    const btnOut = _el('floatBtnOutput');
    const isInline = !!window.RunView?.editModeActive;
    if (isInline) {
      // inline (⬒) -> overlay (⬓): close edit, output big
      window.RunView?.exitEditMode?.(false);
      if (panel) panel.classList.add('is-open');
      if (btnOut) btnOut.classList.add('is-active');
    } else {
      // overlay/default (⬓) -> inline (⬒): close overlay, edit big
      if (panel) panel.classList.remove('is-open');
      if (btnOut) btnOut.classList.remove('is-active');
      window.RunView?.enterEditMode?.();
    }
    _syncAiViewIcon();
    if (typeof _updateTabUI === 'function') _updateTabUI();
  }

  // Sync ⬓/⬒ icon to current view state (SSOT = editModeActive).
  // editModeActive=true (edit big) -> ⬒ (\u2b12) / false (output big) -> ⬓ (\u2b13)
  function _syncAiViewIcon() {
    const vw = _el('btnAiView');
    if (!vw) return;
    const inline = !!window.RunView?.editModeActive;
    vw.textContent = inline ? '\u2b12' : '\u2b13';     // ⬒ edit-big : ⬓ output-big
    vw.classList.toggle('vw-on', inline);              // ①c-3: 편집뷰일 때 청록 점등
    vw.setAttribute('aria-pressed', inline ? 'true' : 'false');
  }

  // Find the AI CHAT panel header by trying known IDs, then falling back
  // to scanning for the "edit"/"chat" button row. ID-independent — this
  // makes the JOB toggle injection robust to header DOM changes.
  function _findChatHeader() {
    let h = _el('aiChatHeader') || _el('floatAiHeader');
    if (h) return h;
    // Fallback: any element that contains BOTH the edit and chat buttons.
    const edit = _el('btnRunEdit');
    const chat = _el('btnAiChat');
    if (edit && chat) {
      // Their nearest common ancestor (parent of chat — usually the toolbar row)
      return chat.parentElement || edit.parentElement;
    }
    return null;
  }

  function _updateStopBtn() {
    _syncSessStatus();   // 세션 변동 지점 모두 여기 거치므로 2단 세션등 자동 동기화
    _syncManagerStatus(); // task Manager 칩(실행 중 강조)도 같이 갱신
    const hdr = _findChatHeader();
    if (!hdr) return;
    // job 토글은 세그먼트로(이전 STEP). 여기선 보장만.
    _ensureJobToggleBtn(hdr);

    // stop 은 "실행상태" 종속 → 세그먼트 밖, 헤더 끝 고정 슬롯.
    // 상태라벨 칩: 평소 '○ idle'(흐림) / 실행중 '■ stop'(밝은빨강, 클릭=중단).
    // 자리는 항상 차지(레이아웃 불변).
    let slot = hdr.querySelector('.ai-stop-slot');
    if (!slot) {
      slot = document.createElement('span');
      slot.className = 'ai-stop-slot';
      slot.style.cssText = 'display:inline-flex;align-items:center;min-width:3.4rem;margin-left:0.5rem;justify-content:flex-end;';
      const btn = document.createElement('span');
      btn.className = 'ai-stop-btn';
      btn.style.cssText = 'cursor:pointer;font-size:0.8rem;white-space:nowrap;';
      btn.onclick = () => { if (_aiRunning || _activeJobId) _stopActive(); };
      slot.appendChild(btn);
      hdr.appendChild(slot);
    }
    const btn = slot.querySelector('.ai-stop-btn');
    const busy = _aiRunning || !!_activeJobId;
    if (btn) {
      if (busy) {
        btn.textContent = '■ stop';
        btn.style.color = '#ff7b72';   // 밝은 빨강
        btn.style.cursor = 'pointer';
      } else {
        btn.textContent = '○ idle';
        btn.style.color = '#7a8a9a';   // copy/clear 수준 흐림
        btn.style.cursor = 'default';
      }
    }
  }

  // §4-6 모드 세그먼트(edit·chat·job 묶음) 컨테이너를 찾는다.
  // 없으면 null → 호출부가 기존 hdr 로 폴백(하위호환).
  function _findModeSeg() {
    return _el('rpModeSeg');
  }

  // Inject the [chat | job] sub-mode toggle into the chat panel header
  // (idempotent — only creates the button once).
  function _ensureJobToggleBtn(hdr) {
    if (!hdr || hdr.querySelector('#btnAiJobToggle')) return;
    const btn = document.createElement('span');
    btn.id = 'btnAiJobToggle';
    btn.className = 'ai-sub-mode-btn';
    btn.style.cssText = 'cursor:pointer;font-size:0.8rem;margin-left:0.5rem;opacity:0.85;';
    btn.textContent = 'task';   // 라벨만 task (내부 _chatSubMode 'job' 유지)
    btn.title = 'TASK 모드: 오래 걸리는 작업을 맡김 (백그라운드, 재접속 OK)';
    btn.onclick = () => {
      // 토글: job이면 chat으로, 아니면 job으로. 평탄화 라우터 경유.
      if (_chatSubMode === 'job') { _gotoSegment('chat'); }
      else                       { _gotoSegment('job'); }
    };
    // job 토글은 모드 세그먼트(있으면)에 붙인다. edit·chat 과 한 덩어리로.
    // 세그먼트가 없으면(구버전 DOM) 종전대로 받은 hdr 에 붙인다.
    const _seg = _findModeSeg();
    (_seg || hdr).appendChild(btn);
  }

  // ── Chat-mode execution (replaces Run/Line/Block) ──
  function _chatRun() {
    const text = window.Editor?.getText?.() || '';
    if (text.trim()) {
      // 키보드 내리기 + 출력 패널(오버레이)로 전환
      document.activeElement?.blur?.();
      if (window.RunView?.editModeActive) window.RunView.exitEditMode();
      const o = _el('runOutput'); if (o) setTimeout(() => { o.scrollTop = o.scrollHeight; }, 100);

      // Shell escape: !로 시작하면 AI 대신 셸 명령 실행
      if (text.trim().startsWith('!')) {
        window.runExec?.();
        return;
      }

      _sendPrompt(text.trim());
    }
  }

  function _chatLine() {
    const view = window.Editor?.get?.();
    if (!view) return;
    const pos = view.state.selection.main.head;
    const line = view.state.doc.lineAt(pos);
    const text = line.text.trim();
    if (text) {
      // Shell escape: !로 시작하면 셸 명령 실행
      if (text.startsWith('!')) {
        window.runExec?.();
        return;
      }
      _sendPrompt(text);
    }
  }

  function _chatBlock() {
    const sel = window.Editor?.getSelection?.() || '';
    if (sel.trim()) {
      _sendPrompt(sel.trim());
    } else {
      // No selection: send all text
      _chatRun();
    }
  }

  // ── Init: inject chat button into OUTPUT header ──
  document.addEventListener('DOMContentLoaded', () => {
    const actions = document.querySelector('#runPanelInner .rp-actions');
    if (!actions) return;

    // Give the title span an ID for switching
    const titleSpan = document.querySelector('#runPanelInner .rp-title');
    if (titleSpan) {
      titleSpan.id = 'runPanelTitle';
      // STEP B ①a: 라벨 텍스트만 비우고 엘리먼트/리스너는 유지 (①c에서 제거)
      titleSpan.textContent = '';
      titleSpan.style.width = '0';
      titleSpan.style.overflow = 'hidden';
      // ①c: 라벨(빈 요소)의 뷰순환 리스너 제거. 뷰 전환은 ⬓(_toggleAiView) 전담.
    }

    // Insert chat button after edit button
    const editBtn = _el('btnRunEdit');
    if (editBtn) {
      const chatBtn = document.createElement('button');
      chatBtn.id = 'btnAiChat';
      chatBtn.textContent = 'chat';
      chatBtn.style.cssText = editBtn.style.cssText || '';

      // §4-6: edit·chat·job 을 한 세그먼트(.rp-seg)로 묶는다.
      // 세그먼트를 edit 의 원래 자리에 끼우고, edit→chat 순으로 그 안에 넣는다.
      // (job 토글은 _ensureJobToggleBtn 이 세그먼트에 append — 3-2.)
      // copy/clear/✕close 는 세그먼트 밖에 그대로 둔다.
      const seg = document.createElement('span');
      seg.className = 'rp-seg';
      seg.id = 'rpModeSeg';
      editBtn.parentNode.insertBefore(seg, editBtn);  // edit 자리에 세그먼트
      seg.appendChild(editBtn);                        // edit 을 세그먼트 안으로
      seg.appendChild(chatBtn);                        // chat 을 그 다음에

      // STEP B ①a: ☰ 슬롯 (세그먼트 앞)
      const segEl = document.getElementById('rpModeSeg');
      if (segEl && !document.getElementById('btnAiTools')) {
        const tg = document.createElement('button');
        tg.id = 'btnAiTools';
        tg.className = 'rp-tools-toggle';
        tg.type = 'button';
        tg.textContent = '\u2630';            // ☰
        tg.setAttribute('aria-label', 'tools');
        segEl.parentNode.insertBefore(tg, segEl);
        // ②: ☰ 클릭 = 2단(#rpDock2) 펼침/접기. 펼침=☰, 접힘=⊟ (✕와 구분).
        tg.addEventListener('click', (e) => {
          e.stopPropagation();
          window.RunView?.toggleDock2?.();
          const collapsed = !!window.RunView?.dock2Collapsed;
          tg.textContent = collapsed ? '\u22A1' : '\u2630';   // ⊟ : ☰
          tg.classList.toggle('tools-collapsed', collapsed);
        });
      }

      // ── chat 탭 클릭 ──
      // edit→chat / job→chat: 모드(컨텍스트) 전환만. 뷰 전환은 ⬓ 전담(①c).
      // 이미 chat 이면 아무것도 안 함(같은 모드 재탭 = 무동작 = "하나에 한 기능").
      chatBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (_mode === 'chat') {
          // 이미 chat 모드: job 하위모드면 chat 으로만 되돌림(모드 전환). 뷰 순환 없음.
          if (_chatSubMode === 'job') { _setChatSubMode('chat'); return; }
          return;   // 같은 chat 재탭 → 무동작
        }
        // edit→chat 전환 (평탄화 라우터)
        _gotoSegment('chat');
      });
    }

    // ── edit 탭 클릭 ──
    // chat→edit: 내용을 output으로 전환 + 패널 상태 유지
    // edit→edit: float_run.js 원래 동작 (자체 ON/OFF 토글)
    const origEditBtn = _el('btnRunEdit');
    if (origEditBtn) {
      origEditBtn.addEventListener('click', (e) => {
        if (_mode === 'chat') {
          e.stopImmediatePropagation();  // float_run.js 토글 차단
          _gotoSegment('edit');          // 내용만 전환, 패널 상태 유지
        } else {
          // ①c: 이미 edit 모드 → 재탭은 무동작. float_run의 뷰 토글을 차단.
          // (뷰 전환은 ⬓(_toggleAiView) 전담 — "하나에 한 기능")
          e.stopImmediatePropagation();
        }
      }, true);  // capture phase
    }

    // Clear button: clear appropriate log
    const clearBtn = _el('btnRunClear');
    if (clearBtn) {
      // STEP B ①a: clear에도 2단 예정 표시 추가
      clearBtn.classList.add('rp-pending-2dan');
      clearBtn.addEventListener('click', () => {
        if (_mode === 'chat') {
          // Clear = output 렌더링만 일시적으로 지운다.
          // 메모리(_transcript/_jobTranscript/_chatLogHtml/_jobLogHtml)와
          // OPFS(chat_/job_)는 보존한다 → 슬롯 복귀/Load 시 다시 살아남.
          // 화면 DOM(runOutput.innerHTML='')은 float_run.js 핸들러가 처리한다.
        }
      });
    }

    // STEP B ①a: ⬓ 슬롯 (닫기 버튼 앞)
    const closeBtn = document.querySelector('#runPanelInner .rp-actions .rp-close');
    if (closeBtn && !document.getElementById('btnAiView')) {
      const vw = document.createElement('button');
      vw.id = 'btnAiView';
      vw.className = 'rp-view-toggle';
      vw.type = 'button';
      vw.textContent = '\u2b13';           // ⬓ (출력 큼=오버레이 기본)
      vw.setAttribute('aria-label', 'view');
      closeBtn.parentNode.insertBefore(vw, closeBtn);
      // ①b: ⬓ click -> mode-agnostic view toggle. (wired at the ①a slot)
      vw.addEventListener('click', (e) => {
        e.stopPropagation();
        _toggleAiView();
      });
      _syncAiViewIcon();   // initial icon to match current view state
    }

    // STEP B ①a: copy/clear — 2단 예정 표시
    const copyBtn = _el('btnRunCopy');
    if (copyBtn) copyBtn.classList.add('rp-pending-2dan');

    // Close button: AI 모드일 때는 edit 모드로 복귀 + 패널 닫기
    const closeBtnHandle = _el('btnRunClose');
    if (closeBtnHandle) {
      closeBtnHandle.addEventListener('click', (e) => {
        if (_mode === 'chat') {
          // float_run.js close 핸들러가 동작하도록 내버려둠 (패널 닫기)
          // 내용만 edit으로 전환
          _mode = 'edit';
          const output = _el('runOutput');
          if (output) {
            _chatLogHtml = output.innerHTML;
            output.innerHTML = _editOutputHtml;
          }
          _chatDraft = window.Editor?.getText?.() || '';
          _chatCursor = window.Editor?.getCursor?.();
          window.Editor?.setText?.(_editDoc || '');
          if (_editCursor) {
            try { window.Editor?.setCursor?.(_editCursor); } catch(e2) {}
          }
          _updateTabUI();
          // float_run.js의 close 핸들러가 나머지(패널 닫기) 처리
        }
      }, true); // capture phase — float_run.js보다 먼저, 하지만 propagation은 허용
    }
  });

  // ── AI button in tool panel (now static in Mode group) ──
  document.addEventListener('DOMContentLoaded', () => {
    const aiBtn = _el('floatTpAi');
    if (!aiBtn) return;
    aiBtn.addEventListener('click', () => {
      const tp = _el('floatToolPanel');
      if (tp) tp.style.display = 'none';
      const tbtn = _el('floatBtnTool');
      if (tbtn) tbtn.classList.remove('is-active');

      // 토글: edit↔chat
      if (_mode === 'chat') {
        _enterEditMode();
      } else {
        _enterChatMode();
      }
    });
  });

  // ── AI Floating Pill — 버튼 이벤트 + 드래그 + 패널 ──
  let _thinkMode = false;
  let _aiModel = 'auto';
  let _attachments = [];  // [{type:'file'|'block'|'image', name, content}]
  let _lastImages = [];   // image paths captured in _preparePrompt, sent in body.images
  // Assigned inside the DOMContentLoaded init below. Declared at module scope
  // so module-level _openModelSheet/_openOptSheet can call it — otherwise the
  // option chips (tokens/temp/workers) + Continue never re-sync on sheet open.
  let _syncOptChips;
  let _maxTokens = 2048;
  try {
    const _mt = parseInt(localStorage.getItem('usekit.ai.maxTokens'), 10);
    if ([512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072].includes(_mt)) _maxTokens = _mt;
  } catch (e) {}
  let _temperature = 0.7;
  try {
    const _tp = parseFloat(localStorage.getItem('usekit.ai.temperature'));
    if ([0, 0.3, 0.7, 1.0].includes(_tp)) _temperature = _tp;
  } catch (e) {}
  // Worker count for chat (ai_chat_v2). 1 = single mode (one LLM call, fast).
  // >=2 routes to the parallel pipeline (plan + N workers + judge → slower).
  // Persisted in localStorage; chat-only (task/job is a separate agent path).
  let _workers = 1;
  try {
    const _w = parseInt(localStorage.getItem('usekit.ai.workers'), 10);
    if (_w >= 1 && _w <= 3) _workers = _w;
  } catch (e) {}
  let _continueMode = false;
  try { _continueMode = localStorage.getItem('usekit.ai.continue') === '1'; } catch (e) {}
  // 🔍 Search grounding toggle (google_search). Sent per request as body.search.
  let _searchMode = false;
  try { _searchMode = localStorage.getItem('usekit.ai.search') === '1'; } catch (e) {}
  // 🔊 Auto-speak toggle: when ON, each AI reply is read aloud automatically.
  let _autoSpeak = false;
  try { _autoSpeak = localStorage.getItem('usekit.ai.autospeak') === '1'; } catch (e) {}
  // ✨ AI TTS toggle: OFF = on-device browser TTS (free, instant). ON = Gemini
  // TTS (higher quality but token-heavy) → OFF by default for free users.
  let _aiTts = false;
  try { _aiTts = localStorage.getItem('usekit.ai.aitts') === '1'; } catch (e) {}
  // General USEKIT Project: when ON, chat passes project_meta=true so the
  // backend injects project_meta.md (## Project/User/Meta) into the system
  // prompt. UI state → global (localStorage), per UI-vs-data principle.
  let _projectMeta = false;
  try { _projectMeta = localStorage.getItem('usekit.ai.projectMeta') === '1'; } catch (e) {}
  let _taskTail = true;   // TASK Tail(자동 스크롤 따라가기) 상태 (기본 ON)

  // ── AI meta cache (sys_ai.yaml via /api/ai_meta) ──
  // null = not loaded yet, {} = loaded but empty/error, populated = ready.
  let _aiMeta = null;
  let _aiMetaPromise = null;     // dedupe concurrent fetches

  function _loadAiMeta(force) {
    if (!force && _aiMeta) return Promise.resolve(_aiMeta);
    if (_aiMetaPromise && !force) return _aiMetaPromise;
    // Abort after 6s to avoid infinite Loading...
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 6000);
    _aiMetaPromise = fetch('/api/ai_meta', { signal: ctrl.signal })
      .then(r => { clearTimeout(tid); return r.json(); })
      .then(d => {
        _aiMeta = (d && d.ok && d.meta) ? d.meta : {};
        // BUG1: restore the user's last picked model (takes priority over yaml default).
        //   Only if it still exists + is enabled in current meta; else fall through.
        let _restored = false;
        if (_aiMeta.providers) {
          try {
            const saved = JSON.parse(localStorage.getItem(_MODEL_KEY) || 'null');
            if (saved && saved.provider) {
              const sp = _aiMeta.providers[saved.provider];
              if (sp && sp.enabled !== false) {
                _provider = saved.provider;
                _aiModel  = saved.model || sp.default || '';
                const lbl = _el('floatAiModelLabel');
                if (lbl) lbl.textContent = (_aiModel || _provider).toLowerCase();
                _restored = true;
              }
            }
          } catch (e) {}
        }
        // First-boot defaults from yaml: pick default_provider + its default model.
        if (!_restored && _aiMeta.default_provider && _aiMeta.providers) {
          const dp = _aiMeta.default_provider;
          const pdata = _aiMeta.providers[dp];
          if (pdata && pdata.default) {
            // Only override if user hasn't picked something explicitly yet.
            if (_aiModel === 'auto' && _provider === 'claude') {
              _provider = dp;
              _aiModel = pdata.default;
              const lbl = _el('floatAiModelLabel');
              if (lbl) lbl.textContent = _aiModel.toLowerCase();
            }
          }
        }
        return _aiMeta;
      })
      .catch(err => {
        clearTimeout(tid);
        console.warn('[AiMeta] fetch failed:', err);
        _aiMeta = {};
        return _aiMeta;
      })
      .finally(() => { _aiMetaPromise = null; });
    return _aiMetaPromise;
  }

  // ── AI health + key state (STEP 2: panel dots + key fields) ──
  // _aiHealth: { provider: {healthy, reason, retry_after_ts, state, tier, auth, label, color} }
  // _aiKeys:   { provider: {has_key, masked, key_env} }
  let _aiHealth = {};
  let _aiKeys = {};

  async function _loadAiHealth() {
    try {
      const r = await fetch('/api/ai_health');
      const j = await r.json();
      _aiHealth = (j && j.ok && j.health) ? j.health : {};
    } catch (_) { _aiHealth = {}; }
  }

  async function _loadAiKeyStatus() {
    try {
      const r = await fetch('/api/ai_key_status');
      const j = await r.json();
      _aiKeys = (j && j.ok && j.keys) ? j.keys : {};
    } catch (_) { _aiKeys = {}; }
  }

  // state-driven dot color. alive=green / gated|quota=amber / dead=red / unknown=grey.
  // Falls back to healthy/retry_after_ts when state absent (cache without probe).
  function _healthColor(provider) {
    const h = _aiHealth[provider];
    if (!h) return '#6b7280';
    const s = h.state;
    if (s === 'alive') return '#10b981';
    if (s === 'quota' || s === 'gated') return '#f59e0b';
    if (s === 'dead')  return '#ef4444';
    if (h.healthy === true)  return '#10b981';
    if (h.retry_after_ts)    return '#f59e0b';
    if (h.healthy === false) return '#ef4444';
    return '#6b7280';
  }
  function _healthTitle(provider) {
    const h = _aiHealth[provider];
    if (!h) return '';
    const bits = [];
    if (h.state)  bits.push(h.state);
    if (h.reason && h.reason !== 'ok') bits.push(h.reason);
    return bits.join(' · ');
  }

  // Per-provider probe (free only). Repaints the dot for that provider.
  async function _pingProvider(provider) {
    // visual: pulse the dot(s) while probing
    const list = _el('floatAiModelList');
    const dots = list ? list.querySelectorAll(`[data-health-dot="${provider}"]`) : [];
    dots.forEach(d => { d.style.opacity = '0.35'; });
    try {
      const r = await fetch(`/api/ai_probe?provider=${encodeURIComponent(provider)}`);
      const j = await r.json();
      const res = (j && j.result) || {};
      _aiHealth[provider] = Object.assign(_aiHealth[provider] || {}, {
        healthy: !!res.ok, state: res.state,
        reason: res.error || (_aiHealth[provider] || {}).reason,
      });
      // BUG3: record that THIS session actually verified the provider alive.
      if (res.ok || res.state === 'alive') _sessionProbed.add(provider);
    } catch (_) {}
    dots.forEach(d => { d.style.opacity = '1'; });
    _repaintHealthDots();
  }

  // Refresh all free providers in one token-free pass.
  async function _refreshAllFree() {
    try {
      const r = await fetch('/api/ai_probe_all');
      const j = await r.json();
      if (j && j.ok && j.results) {
        for (const [p, res] of Object.entries(j.results)) {
          _aiHealth[p] = Object.assign(_aiHealth[p] || {}, {
            healthy: !!res.ok, state: res.state,
          });
          // BUG3: refresh-all also counts as a real session probe.
          if (res.ok || res.state === 'alive') _sessionProbed.add(p);
        }
      }
    } catch (_) {}
    _repaintHealthDots();
  }

  // Re-color rendered dots without a full re-render.
  function _repaintHealthDots() {
    const list = _el('floatAiModelList');
    if (!list) return;
    list.querySelectorAll('[data-health-dot]').forEach(el => {
      const prov = el.getAttribute('data-health-dot');
      el.style.color = _healthColor(prov);
      el.title = _healthTitle(prov);
    });
  }

  // Save / clear an API key for a provider (api tier). POST /api/ai_key.
  async function _saveKey(provider, key, statusEl) {
    try {
      const r = await fetch('/api/ai_key', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, key }),
      });
      const j = await r.json();
      if (j && j.ok) {
        if (j.cleared) {
          _aiKeys[provider] = { has_key: false, masked: '(none)' };
          if (statusEl) statusEl.textContent = '(none)';
        } else {
          _aiKeys[provider] = { has_key: true, masked: j.masked };
          if (statusEl) statusEl.textContent = j.masked;
        }
        _updateSheetCurrent();   // reflect new key state on the badge right away
        return true;
      }
      if (statusEl) statusEl.textContent = (j && j.error) ? j.error : 'error';
      return false;
    } catch (_) {
      if (statusEl) statusEl.textContent = 'error';
      return false;
    }
  }

  // Build/refresh the model panel from cached meta.
  async function _renderModelPanel() {
    const list = _el('floatAiModelList');
    if (!list) return;
    const meta = await _loadAiMeta();
    // Load health + key status in parallel (cheap; network-0 health, masked keys).
    await Promise.all([_loadAiHealth(), _loadAiKeyStatus()]);
    // Keys/health were not yet loaded when the sheet first painted the badge
    // (_openModelSheet calls _updateSheetCurrent before this). Repaint now so the
    // badge reflects the real key state instead of a stale NO KEY.
    _updateSheetCurrent();
    if (!meta || !meta.providers || !Object.keys(meta.providers).length) {
      _renderFallbackPanel();
      return;
    }

    const tiers     = meta.tiers || {};
    const providers = meta.providers || {};

    // Group providers by tier, sorted by tier order.
    const byTier = {};
    Object.entries(providers).forEach(([name, p]) => {
      const t = p.tier || 'other';
      (byTier[t] ||= []).push([name, p]);
    });
    const tierOrder = Object.entries(tiers)
      .sort((a, b) => (a[1].order || 99) - (b[1].order || 99))
      .map(([k]) => k);
    Object.keys(byTier).forEach(t => { if (!tierOrder.includes(t)) tierOrder.push(t); });

    let html = '';
    for (const tierKey of tierOrder) {
      const provList = byTier[tierKey];
      if (!provList || !provList.length) continue;
      const tinfo = tiers[tierKey] || { label: tierKey.toUpperCase() };

      // Section opens only if it contains the current provider; else collapsed.
      // (No forced 'free' open — keeps the tree short; selected path expands itself.)
      const secHasCurrent = provList.some(([n]) => n === _provider);
      const secOpen = secHasCurrent;
      const secArrow = secOpen ? '▾' : '▸';
      const secBodyStyle = secOpen ? '' : 'display:none;';
      const refreshBtn = (tierKey === 'free')
        ? `<button class="amp-refresh-all" data-refresh-free="1" title="refresh all" style="background:none;border:0;color:#768390;cursor:pointer;font-size:0.95em;">↻</button>`
        : '';

      // Availability dot: is ANY provider in this section usable?
      //   free/cli → health alive ; api → has a saved key. (enabled required)
      const secAvail = provList.some(([n, pp]) => {
        if (pp.enabled === false) return false;
        const isKey = (pp.auth === 'api_key' || (pp.tier === 'api' && pp.key_env));
        if (isKey) return !!(_aiKeys[n] || {}).has_key;
        return (_aiHealth[n] || {}).state === 'alive';
      });
      const secDot = secAvail
        ? `<span title="available" style="color:#3fb950;font-size:0.6em;">●</span>`
        : `<span title="none available" style="color:#586069;font-size:0.6em;">○</span>`;

      // Current-section highlight (the SELECTED path lives here) — subtle bg + brighter label.
      const headBg    = secHasCurrent ? 'background:rgba(124,124,255,0.07);' : 'background:none;';
      const headColor = secHasCurrent ? '#adbac7' : '#768390';

      html += `<div class="amp-sec" data-sec="${_esc(tierKey)}">`;
      html += `<button class="amp-sec-head" data-sec-toggle="${_esc(tierKey)}" style="display:flex;align-items:center;gap:6px;width:100%;${headBg}border:0;border-bottom:1px solid #2d333b;border-radius:5px 5px 0 0;cursor:pointer;margin:10px 0 4px;padding:5px 10px;font-size:0.7rem;font-weight:700;letter-spacing:0.1em;color:${headColor};text-transform:uppercase;text-align:left;">`;
      html += `<span class="amp-sec-arrow" style="font-size:0.85em;opacity:0.7;">${secArrow}</span>`;
      html += `<span>${_esc(tinfo.label || tierKey)}</span>`;
      html += `<span style="margin-left:auto;display:flex;align-items:center;gap:9px;">${refreshBtn}${secDot}</span>`;
      html += `</button>`;
      html += `<div class="amp-sec-body" style="${secBodyStyle}">`;

      for (const [pname, p] of provList) {
        const enabled = p.enabled !== false;
        const models  = p.models || {};
        const aliases = Object.keys(models);
        const isApiKey = (p.auth === 'api_key' || (p.tier === 'api' && p.key_env));

        // Card BODY (models + key area). Hidden unless expanded.
        let bodyHtml = '';
        if (aliases.length) {
          for (const alias of aliases) {
            bodyHtml += _modelBtnHtml(pname, alias, p, enabled, aliases.length === 1 ? (p.label || pname) : alias, true);
          }
        } else if (enabled) {
          bodyHtml += _modelBtnHtml(pname, '', p, enabled, p.label || pname);
        }
        if (isApiKey) {
          bodyHtml += `<div class="amp-key-sec" style="border-top:1px solid #21262d;margin-top:3px;padding-top:4px;">`;
          bodyHtml += `<div style="font-size:0.6rem;letter-spacing:0.04em;color:#586069;padding:0 1rem 2px 1.8rem;">API KEY</div>`;
          bodyHtml += _keyFieldHtml(pname, p, enabled);
          bodyHtml += `</div>`;
        }

        // Card collapsed by default; only current provider opens.
        const isCurrent = _provider === pname;
        const arrow = '▸';                 // cards always start collapsed (tap to expand)
        const bodyStyle = 'display:none;';  // keep the tree short; selected model shows in the header
        // Single meaning: the ACTIVE provider is colored; everything else is grey.
        // Tagged with data-prov-dot so _repaintProviderDots can move it on select
        // without a full re-render (keeps expanded cards open).
        const _dotOn = (pname === _provider);
        const hdrDot = `<span data-prov-dot="${_esc(pname)}" style="color:${_dotOn ? '#3fb950' : '#586069'};font-size:0.7em;">${_dotOn ? '●' : '○'}</span>`;

        // Monochrome card: subtle border, neutral text. No per-provider accent color.
        html += `<div class="amp-card" data-card-prov="${_esc(pname)}" style="border:1px solid #21262d;border-radius:7px;margin:4px 8px;background:rgba(255,255,255,0.015);overflow:hidden;">`;
        html += `<button class="amp-card-head" data-card-toggle="${_esc(pname)}" style="display:flex;align-items:center;gap:8px;width:100%;background:none;border:0;cursor:pointer;padding:8px 10px;color:#adbac7;font-weight:600;font-size:0.9rem;text-align:left;">`;
        html += `<span class="amp-card-arrow" style="opacity:0.55;font-size:0.78em;">${arrow}</span>`;
        html += `${hdrDot}`;
        html += `<span style="flex:1;">${_esc(p.label || pname)}</span>`;
        if (!enabled) html += `<span style="font-size:0.6rem;color:#768390;font-weight:400;letter-spacing:0.05em;">soon</span>`;
        html += `</button>`;
        html += `<div class="amp-card-body" style="${bodyStyle}padding-bottom:4px;">${bodyHtml}</div>`;
        html += `</div>`;
      }
      html += `</div></div>`;  // /amp-sec-body /amp-sec
    }

    list.innerHTML = html;

    // Section header toggle (collapse/expand whole section).
    list.querySelectorAll('.amp-sec-head').forEach(btn => {
      btn.addEventListener('click', (e) => {
        if (e.target.closest('[data-refresh-free]')) return;
        e.stopPropagation();
        const sec = btn.closest('.amp-sec');
        if (!sec) return;
        const body = sec.querySelector('.amp-sec-body');
        const arrow = btn.querySelector('.amp-sec-arrow');
        if (!body) return;
        const open = body.style.display !== 'none';
        body.style.display = open ? 'none' : '';
        if (arrow) arrow.textContent = open ? '▸' : '▾';
      });
    });

    // Card header toggle (collapse/expand body).
    list.querySelectorAll('.amp-card-head').forEach(btn => {
      btn.addEventListener('click', (e) => {
        // Don't toggle when tapping the health dot inside the header.
        if (e.target.closest('[data-health-dot]')) return;
        e.stopPropagation();
        const card = btn.closest('.amp-card');
        if (!card) return;
        const body = card.querySelector('.amp-card-body');
        const arrow = btn.querySelector('.amp-card-arrow');
        if (!body) return;
        const open = body.style.display !== 'none';
        body.style.display = open ? 'none' : '';
        if (arrow) arrow.textContent = open ? '▸' : '▾';
      });
    });

    // Refresh-all (FREE header) → probe_all, token-free.
    const refBtn = list.querySelector('[data-refresh-free]');
    if (refBtn) {
      refBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        refBtn.textContent = '⟳'; refBtn.disabled = true;
        await _refreshAllFree();
        refBtn.textContent = '↻'; refBtn.disabled = false;
      });
    }

    // Per-provider health dot → click to probe (free only; api dots are gated).
    list.querySelectorAll('[data-health-dot]').forEach(dot => {
      dot.addEventListener('click', (e) => {
        const prov = dot.getAttribute('data-health-dot');
        const pd = (_aiMeta?.providers || {})[prov] || {};
        // Dot always swallows the click (so it never triggers model-select).
        e.stopPropagation();
        if (pd.auth === 'api_key') {
          // api: probing is key-gated; tapping the dot just hints to use the key field.
          window.UI?.showToast?.('Managed via API key', 800);
          return;
        }
        _pingProvider(prov);
      });
    });

    // Key field: save / clear (api tier).
    list.querySelectorAll('.amp-key').forEach(row => {
      const prov = row.getAttribute('data-key-prov');
      const input = row.querySelector('.amp-key-input');
      const saveBtn = row.querySelector('.amp-key-save');
      const clearBtn = row.querySelector('.amp-key-clear');
      const statusEl = row.querySelector('.amp-key-status');
      const dotEl = row.querySelector('.amp-key-dot');
      const setConnected = (has) => {
        row.setAttribute('data-has-key', has ? '1' : '0');
        if (dotEl) { dotEl.style.color = has ? '#3fb950' : '#586069'; dotEl.textContent = has ? '●' : '○'; dotEl.title = has ? 'connected' : 'no key'; }
        if (input) input.style.borderColor = has ? '#3fb950' : '#30363d';
        if (saveBtn) saveBtn.textContent = has ? '↻' : 'Save';
        if (statusEl) statusEl.style.color = has ? '#3fb950' : '#586069';
      };
      if (saveBtn) saveBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const key = (input && input.value || '').trim();
        if (!key) return;
        saveBtn.textContent = '…'; saveBtn.disabled = true;
        const ok = await _saveKey(prov, key, statusEl);
        if (ok && input) { input.value = ''; input.placeholder = (_aiKeys[prov] || {}).masked || ''; }
        saveBtn.disabled = false;
        setConnected(!!(_aiKeys[prov] || {}).has_key);
      });
      if (clearBtn) clearBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        await _saveKey(prov, '', statusEl);
        if (input) { input.value = ''; input.placeholder = 'paste API key'; }
        setConnected(false);
      });
    });

    // Highlight current selection.
    list.querySelectorAll('.ai-model-opt').forEach(b => {
      const isSel = b.dataset.provider === _provider && b.dataset.model === _aiModel;
      b.classList.toggle('is-selected', isSel);
    });
  }

  // Inline key field for an api-tier provider. Masked placeholder, Save/Clear.
  // anthropic: adapter not yet implemented (G3) — show note, key still storable.
  function _keyFieldHtml(provider, pdata, enabled) {
    const st = _aiKeys[provider] || { has_key: false, masked: '(none)' };
    const has = !!st.has_key;
    const ph = has ? _esc(st.masked) : 'paste API key';
    const adapterReady = (pdata.adapter === 'openai' || pdata.adapter === 'gemini');
    const note = adapterReady ? '' :
      `<span class="amp-key-status" style="font-size:0.68em;color:#768390;margin-left:6px;">adapter soon</span>`;
    // Connected state: green dot + green input border + masked value as placeholder.
    const dot = has
      ? `<span class="amp-key-dot" title="connected" style="color:#3fb950;font-size:0.8em;">●</span>`
      : `<span class="amp-key-dot" title="no key" style="color:#586069;font-size:0.8em;">○</span>`;
    const inputBorder = has ? '#3fb950' : '#30363d';
    const statusTxt = has ? `<span class="amp-key-status" style="font-size:0.7em;color:#3fb950;">${_esc(st.masked)}</span>` : (note || `<span class="amp-key-status" style="font-size:0.7em;color:#586069;"></span>`);
    return `<div class="amp-key" data-key-prov="${_esc(provider)}" data-has-key="${has ? '1' : '0'}" style="display:flex;gap:5px;align-items:center;padding:3px 1rem 6px 1.8rem;">
      ${dot}
      <input type="password" class="amp-key-input" placeholder="${ph}" style="flex:1;min-width:0;padding:3px 7px;font-size:12px;background:#161b22;border:1px solid ${inputBorder};border-radius:5px;color:#c9d1d9;">
      <button class="amp-key-save" title="save" style="background:none;border:1px solid #30363d;border-radius:5px;color:#79c0ff;cursor:pointer;font-size:11px;padding:3px 7px;">${has ? '↻' : 'Save'}</button>
      <button class="amp-key-clear" title="clear" style="background:none;border:1px solid #30363d;border-radius:5px;color:#8b949e;cursor:pointer;font-size:11px;padding:3px 6px;">✕</button>
      ${statusTxt}
    </div>`;
  }

  function _modelBtnHtml(provider, alias, pdata, enabled, label, indent) {
    const icon  = (pdata.tier === 'cli') ? '◇' : '●';
    const cls   = 'tp-btn ai-model-opt' + (enabled ? '' : ' is-disabled');
    const pad   = indent ? '1.8rem' : '1.0rem';
    const opacity = enabled ? '1' : '0.35';
    // Dot color = health state only (green/amber/red), else neutral grey.
    // No per-provider accent — keeps the palette calm.
    const dotColor = _healthColor(provider);
    const dotTitle = _esc(_healthTitle(provider));
    return `<button class="${cls}" data-provider="${_esc(provider)}" data-model="${_esc(alias)}" style="padding-left:${pad};opacity:${opacity};color:#adbac7;"><span class="tp-icon" data-health-dot="${_esc(provider)}" title="${dotTitle}" style="color:${_esc(dotColor)};">${icon}</span> ${_esc(label)}</button>`;
  }

  // Fallback: minimal hardcoded panel when /api/ai_meta unavailable.
  function _renderFallbackPanel() {
    const list = _el('floatAiModelList');
    if (!list) return;
    list.innerHTML = `
      <div class="ai-model-tier" style="padding:0.3rem 1rem 0.15rem;color:#888;font-size:0.7em;text-transform:uppercase;">FREE</div>
      <button class="tp-btn ai-model-opt" data-provider="qwen" data-model="QWEN" style="padding-left:1.2rem;"><span class="tp-icon" style="color:#c084fc;">●</span> Qwen</button>
      <hr style="border:0;border-top:1px solid #333;margin:4px 0;">
      <div class="ai-model-tier" style="padding:0.3rem 1rem 0.15rem;color:#888;font-size:0.7em;text-transform:uppercase;">CLI</div>
      <button class="tp-btn ai-model-opt" data-provider="claude_code" data-model="AUTO" style="padding-left:1.2rem;"><span class="tp-icon" style="color:#a78bfa;">◇</span> Claude Code</button>
    `;
  }

  // 시트 헤더의 "AI <current>" 갱신
  // Badge sub-label = tier + current options (tokens / temp / workers).
  // Replaces the provider path (already shown in the sheet title); tier kept so
  // a FREE LLAMA70 vs an API LLAMA70 stays distinguishable at a glance.
  function _badgeSubText() {
    const pdata = _aiMeta?.providers?.[_provider] || {};
    const tier = (pdata.tier || '').toUpperCase();
    const tok = _maxTokens >= 1024 ? (_maxTokens / 1024) + 'K' : String(_maxTokens);
    const opt = tok + ' · ' + _temperature + ' · W' + _workers;
    return [tier, opt].filter(Boolean).join(' · ');
  }

  function _updateSheetCurrent() {
    const el = _el('aiSheetCurrent');
    const prov = (_aiMeta?.providers?.[_provider]?.label) || _provider || '';
    const mdl  = _aiModel && _aiModel !== _provider ? _aiModel : '';
    const pdata0 = _aiMeta?.providers?.[_provider] || {};
    const tierUp = (pdata0.tier || '').toUpperCase();
    // Title: "AI · FREE / GROQ / LLAMA70" — tier / provider / model.
    if (el) {
      const parts = [tierUp, (prov || '').toUpperCase(), (mdl || '').toUpperCase()].filter(Boolean);
      el.textContent = parts.length ? `· ${parts.join(' / ')}` : '';
    }
    // 하단 강조 배지 갱신 — 점 색 = 실제 상태(free:헬스 / api:키유무), 텍스트는 중립색.
    const badge = _el('aiActiveBadge');
    if (badge) {
      const pdata  = _aiMeta?.providers?.[_provider] || {};
      const tier   = (pdata.tier || '').toLowerCase();
      const isApiKey = (pdata.auth === 'api_key' || (tier === 'api' && pdata.key_env));
      const modelEl = _el('aiActiveModel');
      const subEl   = _el('aiActiveSub');
      const dotEl   = _el('aiActiveDot');
      const modelName = (mdl || prov || 'AI').toString().toUpperCase();
      if (modelEl) modelEl.textContent = modelName;
      // sub: "API · 2K · 0.7 · W1" (tier · tokens · temp · workers).
      if (subEl) subEl.textContent = _badgeSubText();
      // 점 색: api=키 있으면 초록·없으면 회색 / free·cli=헬스 state 색
      let dotColor;
      if (isApiKey) dotColor = (_aiKeys[_provider] || {}).has_key ? '#3fb950' : '#586069';
      else dotColor = _healthColor(_provider);
      if (dotEl) { dotEl.style.background = dotColor; dotEl.style.boxShadow = 'none'; }
      badge.style.setProperty('--ai-active-accent', dotColor);
      // Status word on the action button (READY / NO KEY / SOON / PING).
      _updateBadgeStatus();
    }
  }

  // Compute and render the short status badge for the current provider.
  // Fixed status vocabulary (see BOUNDARY status spec):
  //   READY  usable        PING  tap to probe     NO KEY  api key missing
  //   FAIL   probe failed   SOON  adapter pending  BUSY    in-flight call
  //   LIMIT  rate/quota capped
  function _updateBadgeStatus() {
    const btn = _el('aiActivePing');
    if (!btn) return;
    const pdata = _aiMeta?.providers?.[_provider] || {};
    const enabled = pdata.enabled !== false;
    const isApiKey = (pdata.auth === 'api_key' || (pdata.tier === 'api' && pdata.key_env));
    const h = _aiHealth[_provider] || {};
    let word = 'PING', color = '#768390';
    if (!enabled) { word = 'SOON'; color = '#768390'; }
    else if (h.busy) { word = 'BUSY'; color = '#d29922'; }                 // in-flight
    else if (h.state === 'quota' || h.retry_after_ts) { word = 'LIMIT'; color = '#d29922'; } // rate-capped
    else if (isApiKey) {
      const has = (_aiKeys[_provider] || {}).has_key;
      if (has) { word = 'READY'; color = '#3fb950'; }
      else { word = 'NO KEY'; color = '#768390'; }
    } else {
      // BUG3: free/cli READY is only asserted when THIS session actually probed it
      // alive. A stale health cache (e.g. carried from a previously selected provider)
      // must show PING — "tap to verify" — not a false READY.
      const st = h.state;
      if (st === 'dead') { word = 'FAIL'; color = '#f85149'; }
      else if (st === 'alive' && _sessionProbed.has(_provider)) { word = 'READY'; color = '#3fb950'; }
      else word = 'PING';  // unverified this session → tap to probe
    }
    btn.textContent = word;
    btn.style.color = color;
    btn.style.borderColor = (color === '#768390') ? '#30363d' : color;
  }

  // Centralized model selection — called from panel click + auto-update after response.
  // Move the active-provider dot to the current _provider without re-rendering
  // the whole tree (so expanded cards stay open).
  function _repaintProviderDots() {
    document.querySelectorAll('[data-prov-dot]').forEach(el => {
      const on = el.getAttribute('data-prov-dot') === _provider;
      el.style.color = on ? '#3fb950' : '#586069';
      el.textContent = on ? '●' : '○';
    });
  }

  function _selectModel(provider, modelAlias, opts) {
    if (!provider) return;
    _provider = provider;
    _aiModel  = modelAlias || (_aiMeta?.providers?.[provider]?.default || '');
    const label = _el('floatAiModelLabel');
    if (label) {
      // Shorter display: alias if available, else provider name.
      label.textContent = (_aiModel || provider).toLowerCase();
    }
    _updateSheetCurrent();
    // Also refresh the mini bar's ▾ model button (separate element that was
    // previously only set at render time — caused label/selection mismatch).
    const miniBtn = _el('floatAiMiniModelBtn');
    if (miniBtn) {
      miniBtn.innerHTML = `<span style="font-size:11px;">▾</span> ${_esc(_aiModel || provider)}`;
    }
    if (!opts?.silent) {
      const pdata = _aiMeta?.providers?.[provider];
      const pname = pdata?.label || provider;
      const tmsg  = _aiModel ? `${pname} · ${_aiModel}` : pname;
      window.UI?.showToast?.(tmsg, 800);
    }
    // BUG1: persist the picked model so reopen/reload restores it (silent picks too).
    try {
      localStorage.setItem(_MODEL_KEY, JSON.stringify({ provider: _provider, model: _aiModel }));
    } catch (e) {}
    _repaintProviderDots();   // move the active dot to the newly selected provider
  }

  // Kick off meta load early so panel is ready by the time user opens it.
  // Failures are silent — fallback panel handles them.
  document.addEventListener('DOMContentLoaded', () => {
    _loadAiMeta();
  });

  // ── Model sheet open/close (Settings 패턴: .open 클래스 토글) ──
  // 떠있는 박스가 아니라 좌측 슬라이드 시트. 위치계산(_positionPanel) 불필요.
  function _openModelSheet() {
    const mp = _el('floatAiModelPanel');
    if (!mp) return;
    // 다른 떠있는 패널(attach/opt)은 닫는다.
    const ap = _el('floatAiAttachPanel'); if (ap) ap.style.display = 'none';
    const op = _el('floatAiOptPanel');    if (op) { op.classList.remove('open'); op.setAttribute('aria-hidden','true'); }
    mp.classList.add('open');
    mp.setAttribute('aria-hidden', 'false');
    const mb = _el('floatAiModel'); if (mb) mb.classList.add('is-active');
    // 모델 리스트 스크롤 / 옵션 바닥 고정 (2단)
    const _list = _el('floatAiModelList'); if (_list) { _list.style.flex = '1 1 auto'; _list.style.overflowY = 'auto'; }
    const _opts = _el('floatAiSheetOpts'); if (_opts) { _opts.style.flex = '0 0 auto'; _opts.style.borderTop = '1px solid rgba(167,139,250,0.18)'; }
    if (typeof _syncOptChips === 'function') _syncOptChips();
    _updateSheetCurrent();
    // 트리 렌더 (기존 함수 그대로 사용)
    _renderModelPanel().catch(err => {
      console.warn('[AiModel] render failed:', err);
      _renderFallbackPanel();
    });
  }
  function _closeModelSheet() {
    const mp = _el('floatAiModelPanel');
    if (!mp) return;
    mp.classList.remove('open');
    mp.setAttribute('aria-hidden', 'true');
    const mb = _el('floatAiModel'); if (mb) mb.classList.remove('is-active');
  }

  // ── Opt sheet open/close (모델 시트와 동일 패턴) ──
  function _openOptSheet() {
    const op = _el('floatAiOptPanel');
    if (!op) return;
    // 다른 떠있는/시트 패널 닫기
    const ap = _el('floatAiAttachPanel'); if (ap) ap.style.display = 'none';
    _closeModelSheet();
    op.classList.add('open');
    op.setAttribute('aria-hidden', 'false');
    const ob = _el('floatAiOpt'); if (ob) ob.classList.add('is-active');
    if (typeof _syncOptChips === 'function') _syncOptChips();
  }
  function _closeOptSheet() {
    const op = _el('floatAiOptPanel');
    if (!op) return;
    op.classList.remove('open');
    op.setAttribute('aria-hidden', 'true');
    const ob = _el('floatAiOpt'); if (ob) ob.classList.remove('is-active');
  }

  function _closeAiPanels() {
    const mp = _el('floatAiModelPanel');
    const ap = _el('floatAiAttachPanel');
    const op = _el('floatAiOptPanel');
    if (mp) { mp.classList.remove('open'); mp.setAttribute('aria-hidden','true'); }
    if (ap) ap.style.display = 'none';
    if (op) { op.classList.remove('open'); op.setAttribute('aria-hidden','true'); }
    const mb = _el('floatAiModel');
    const ab = _el('floatAiAttach');
    const ob = _el('floatAiOpt');
    if (mb) mb.classList.remove('is-active');
    if (ab) ab.classList.remove('is-active');
    if (ob) ob.classList.remove('is-active');
  }

  // ── 첨부 프리뷰 바 업데이트 ──
  function _updateAttachPreview() {
    const bar = _el('aiAttachPreview');
    if (!bar) return;
    if (!_attachments.length) {
      bar.style.display = 'none';
      bar.innerHTML = '';
      return;
    }
    bar.style.display = 'flex';
    bar.innerHTML = '';
    _attachments.forEach((att, idx) => {
      const chip = document.createElement('span');
      chip.className = 'ai-attach-chip';
      const icon = att.type === 'image' ? '📷' : att.type === 'file' ? '📄' : '📋';
      // Slot 타입 구분: name이 슬롯명이면 📋
      const displayIcon = (att._isSlot) ? '📋' : icon;
      const shortName = att.name.length > 16 ? att.name.substring(0, 14) + '…' : att.name;
      chip.innerHTML = `<span class="chip-icon">${displayIcon}</span><span class="chip-name">${_esc(shortName)}</span><button class="chip-close" data-idx="${idx}">✕</button>`;
      bar.appendChild(chip);
    });
    // ✕ 클릭 이벤트
    bar.querySelectorAll('.chip-close').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const i = parseInt(btn.dataset.idx);
        if (!isNaN(i) && i >= 0 && i < _attachments.length) {
          _attachments.splice(i, 1);
          _updateAttachPreview();
        }
      });
    });
  }

  function _positionPanel(panel, anchorBtn) {
    if (!panel || !anchorBtn) return;
    // Reset to natural position first for measurement
    panel.style.left = 'auto'; panel.style.top = 'auto';
    panel.style.right = 'auto'; panel.style.bottom = 'auto';

    const r = anchorBtn.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    // Desired: right-aligned, above the button
    let right = vw - r.right;
    let bottom = vh - r.top + 6;

    // Apply tentatively to measure panel size
    panel.style.right = right + 'px';
    panel.style.bottom = bottom + 'px';
    const pr = panel.getBoundingClientRect();

    // Clamp: if panel top goes above viewport, switch to top-anchored
    if (pr.top < 4) {
      panel.style.bottom = 'auto';
      panel.style.top = '4px';
    }
    // Clamp: if panel left goes off-screen
    if (pr.left < 4) {
      panel.style.right = 'auto';
      panel.style.left = '4px';
    }
    // Clamp: if panel right goes off-screen
    if (pr.right > vw - 4) {
      panel.style.left = 'auto';
      panel.style.right = '4px';
    }
  }

  // ── Drag support for floating panels ──
  function _initPanelDrag(panelId) {
    const panel = _el(panelId);
    if (!panel) return;

    let dragging = false, ox = 0, oy = 0, touchId = null;
    let startX = 0, startY = 0, moved = false;

    function isDragTarget(el) {
      if (el.closest('button')) return false;
      if (el.closest('.ai-model-opt')) return false;
      if (el.closest('.ai-opt-chip')) return false;
      return true;
    }
    function onStart(cx, cy, el) {
      if (!isDragTarget(el)) return;
      dragging = true; moved = false;
      startX = cx; startY = cy;
      const pr = panel.getBoundingClientRect();
      ox = cx - pr.left; oy = cy - pr.top;
    }
    function onMove(cx, cy) {
      if (!dragging) return;
      if (!moved) {
        if (Math.abs(cx - startX) < 6 && Math.abs(cy - startY) < 6) return;
        moved = true;
        const pr = panel.getBoundingClientRect();
        panel.style.left = pr.left + 'px';
        panel.style.top = pr.top + 'px';
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
      }
      const pw = panel.offsetWidth, ph = panel.offsetHeight;
      const nx = Math.max(0, Math.min(window.innerWidth - pw, cx - ox));
      const ny = Math.max(0, Math.min(window.innerHeight - ph, cy - oy));
      panel.style.left = nx + 'px';
      panel.style.top = ny + 'px';
    }
    function onEnd() { dragging = false; }

    panel.addEventListener('touchstart', e => {
      if (e.touches.length !== 1) return;
      touchId = e.touches[0].identifier;
      onStart(e.touches[0].clientX, e.touches[0].clientY, e.target);
    }, { passive: true });
    panel.addEventListener('touchmove', e => {
      for (const t of e.changedTouches) {
        if (t.identifier === touchId) { onMove(t.clientX, t.clientY); break; }
      }
    }, { passive: true });
    panel.addEventListener('touchend', () => onEnd(), { passive: true });
    panel.addEventListener('mousedown', e => {
      if (!isDragTarget(e.target)) return;
      e.preventDefault();
      onStart(e.clientX, e.clientY, e.target);
    });
    window.addEventListener('mousemove', e => { if (dragging) onMove(e.clientX, e.clientY); });
    window.addEventListener('mouseup', () => { if (dragging) onEnd(); });
  }

  (function() {
    document.addEventListener('DOMContentLoaded', () => {
      // _initPanelDrag('floatAiModelPanel'); // 좌측 시트로 전환 — 드래그 비활성
      // _initPanelDrag('floatAiOptPanel'); // 좌측 시트로 전환 — 드래그 비활성
    });
  })();

  document.addEventListener('DOMContentLoaded', () => {
    const aiWrap = _el('floatAiTool');
    if (!aiWrap) return;

    // ── Run 버튼 — prompt 전송 ──
    const aiRunBtn = _el('floatAiRun');
    if (aiRunBtn) {
      aiRunBtn.addEventListener('click', (e) => {
        if (_aiDragMoved) return;
        e.stopPropagation();
        _closeAiPanels();
        if (_mode === 'chat') _chatRun();
      });
    }

    // ── Think 토글 ──
    const aiThinkBtn = _el('floatAiThink');
    if (aiThinkBtn) {
      aiThinkBtn.addEventListener('click', (e) => {
        if (_aiDragMoved) return;
        e.stopPropagation();
        _closeAiPanels();
        _thinkMode = !_thinkMode;
        aiThinkBtn.classList.toggle('is-active', _thinkMode);
        const label = _el('floatAiThinkLabel');
        if (label) label.textContent = _thinkMode ? 'Think●' : 'Think';
      });
    }

    // ── Attach(+) 버튼 — 패널 토글 ──
    const aiAttachBtn = _el('floatAiAttach');
    const attachPanel = _el('floatAiAttachPanel');
    if (aiAttachBtn && attachPanel) {
      aiAttachBtn.addEventListener('click', (e) => {
        if (_aiDragMoved) return;
        e.stopPropagation();
        _closeModelSheet();
        const isOpen = attachPanel.style.display === 'flex';
        if (isOpen) {
          attachPanel.style.display = 'none';
          aiAttachBtn.classList.remove('is-active');
        } else {
          _positionPanel(attachPanel, aiAttachBtn);
          attachPanel.style.display = 'flex';
          aiAttachBtn.classList.add('is-active');
        }
      });
    }

    // ── Attach 옵션: Current File ──
    // ── Attach 옵션: Slot (현재 슬롯 파일 내용) ──
    const attSlot = _el('aiAttachSlot');
    if (attSlot) {
      attSlot.addEventListener('click', () => {
        // 챗모드에서는 _editDoc에 원본 코드가 저장되어 있음
        let text = _editDoc || '';
        const name = window.SlotManager?.getCurrentSlot?.() || 'slot';
        // _editDoc이 비어있으면 SlotStorage에서 직접 읽기
        if (!text.trim() && name) {
          try {
            const data = window.SlotStorage?.readSlot?.(name);
            if (data?.text) text = data.text;
          } catch(e) {}
        }
        if (text.trim()) {
          _attachments.push({ type: 'file', name, content: text.substring(0, 8000), _isSlot: true });
          if (attachPanel) attachPanel.style.display = 'none';
          if (aiAttachBtn) aiAttachBtn.classList.remove('is-active');
          _updateAttachPreview();
          window.UI?.showToast?.('📋 Slot attached: ' + name, 1000);
        } else {
          window.UI?.showToast?.('No slot content', 1000);
        }
      });
    }

    // ── Attach 옵션: File (일반 파일 선택) ──
    const attFile = _el('aiAttachFile');
    const fileInput = _el('aiFileInput');
    if (attFile && fileInput) {
      attFile.addEventListener('click', () => {
        fileInput.click();
        if (attachPanel) attachPanel.style.display = 'none';
        if (aiAttachBtn) aiAttachBtn.classList.remove('is-active');
      });
      fileInput.addEventListener('change', () => {
        const file = fileInput.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          const content = reader.result || '';
          _attachments.push({ type: 'file', name: file.name, content: content.substring(0, 8000) });
          _updateAttachPreview();
          window.UI?.showToast?.('📄 ' + file.name + ' attached', 1000);
        };
        reader.onerror = () => {
          window.UI?.showToast?.('File read error', 1000);
        };
        reader.readAsText(file);
        fileInput.value = '';  // 리셋
      });
    }

    // ── Attach 옵션: Image ──
    const attImage = _el('aiAttachImage');
    const imgInput = _el('aiImageInput');
    if (attImage && imgInput) {
      attImage.addEventListener('click', () => {
        imgInput.click();
        if (attachPanel) attachPanel.style.display = 'none';
        if (aiAttachBtn) aiAttachBtn.classList.remove('is-active');
      });
      imgInput.addEventListener('change', () => {
        const file = imgInput.files?.[0];
        if (!file) return;
        window.UI?.showToast?.('📷 Resizing...', 1500);
        // Canvas 리사이즈 후 업로드
        const img = new Image();
        const objUrl = URL.createObjectURL(file);
        img.onload = async () => {
          URL.revokeObjectURL(objUrl);
          try {
            const MAX = 1280, QUALITY = 0.7;
            let w = img.naturalWidth, h = img.naturalHeight;
            if (w > MAX || h > MAX) {
              const r = Math.min(MAX / w, MAX / h);
              w = Math.round(w * r);
              h = Math.round(h * r);
            }
            const cvs = document.createElement('canvas');
            cvs.width = w; cvs.height = h;
            cvs.getContext('2d').drawImage(img, 0, 0, w, h);
            const dataUrl = cvs.toDataURL('image/jpeg', QUALITY);
            const b64 = dataUrl.split(',')[1];
            if (!b64) throw new Error('base64 conversion failed');
            const origKB = Math.round(file.size / 1024);
            const newKB = Math.round(b64.length * 3 / 4 / 1024);
            window.UI?.showToast?.(`📷 ${origKB}KB → ${newKB}KB`, 1200);
            // /api/upload로 전송 → Termux 파일시스템에 저장
            const resp = await fetch('/api/upload', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ data: b64, filename: file.name.replace(/\.\w+$/, '.jpg'), slot: _currentSlotName() }),
            });
            const d = await resp.json();
            if (d.ok && d.path) {
              // 저장된 절대 경로를 prompt에 포함 → CLI Read 도구로 읽기 가능
              _attachments.push({ type: 'image', name: file.name, content: d.path, _path: d.path });
              _updateAttachPreview();
              window.UI?.showToast?.('📷 ' + file.name, 1000);
            } else {
              window.UI?.showToast?.('Upload failed: ' + (d.error || 'unknown'), 2000);
            }
          } catch (e) {
            window.UI?.showToast?.('Upload error: ' + e.message, 2000);
          }
        };
        img.onerror = () => {
          URL.revokeObjectURL(objUrl);
          window.UI?.showToast?.('Image load error', 1000);
        };
        img.src = objUrl;
        imgInput.value = '';  // 리셋
      });
    }

    // ── Model(▾) 버튼 — 패널 토글 + 동적 렌더링 ──
    const aiModelBtn = _el('floatAiModel');
    const modelPanel = _el('floatAiModelPanel');
    if (aiModelBtn && modelPanel) {
      aiModelBtn.addEventListener('click', (e) => {
        if (_aiDragMoved) return;
        e.stopPropagation();
        if (attachPanel) attachPanel.style.display = 'none';
        const isOpen = modelPanel.classList.contains('open');
        if (isOpen) {
          _closeModelSheet();
        } else {
          _openModelSheet();
        }
      });

      // Click delegation — buttons are dynamic, can't bind directly at init.
      const listEl = _el('floatAiModelList') || modelPanel;
      listEl.addEventListener('click', (e) => {
        // Ignore clicks on key fields / health dots (handled by their own listeners).
        if (e.target.closest('.amp-key')) return;
        if (e.target.closest('[data-health-dot]')) return;
        const btn = e.target.closest('.ai-model-opt');
        if (!btn) return;
        if (btn.classList.contains('is-disabled')) {
          window.UI?.showToast?.('Not available yet', 800);
          return;
        }
        _selectModel(btn.dataset.provider, btn.dataset.model);
        // Keep panel open so users can configure keys / ping — update highlight in place.
        listEl.querySelectorAll('.ai-model-opt').forEach(b => {
          b.classList.toggle('is-selected',
            b.dataset.provider === _provider && b.dataset.model === _aiModel);
        });
      });

      // Active-badge action — READY/NO KEY/SOON are info; PING/FAIL probe on tap.
      const pingBtn = _el('aiActivePing');
      if (pingBtn) {
        pingBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const pdata = _aiMeta?.providers?.[_provider] || {};
          const isApiKey = (pdata.auth === 'api_key' || (pdata.tier === 'api' && pdata.key_env));
          if (pdata.enabled === false) { window.UI?.showToast?.('Adapter not ready', 900); return; }
          if (isApiKey) {
            const has = (_aiKeys[_provider] || {}).has_key;
            window.UI?.showToast?.(has ? 'Key set — ready' : 'No API key — open the card to add one', 1100);
            return;
          }
          pingBtn.textContent = '…'; pingBtn.disabled = true;
          await _pingProvider(_provider);
          const dotEl = _el('aiActiveDot');
          if (dotEl) dotEl.style.background = _healthColor(_provider);
          pingBtn.disabled = false;
          _updateBadgeStatus();
        });
      }

      // 시트 배경(오버레이) 탭 → 닫기
      const _modelOverlay = _el('floatAiModelOverlay');
      if (_modelOverlay) {
        _modelOverlay.addEventListener('click', () => { _closeModelSheet(); });
      }
    }

    // ── Opt(⚙) 버튼 — 옵션 패널 토글 ──
    const aiOptBtn  = _el('floatAiOpt');
    const optPanel  = _el('floatAiOptPanel');
    if (aiOptBtn && optPanel) {
      aiOptBtn.addEventListener('click', (e) => {
        if (_aiDragMoved) return;
        e.stopPropagation();
        const mp = _el('floatAiModelPanel');
        const isOpen = mp && mp.classList.contains('open');
        _closeAiPanels();
        if (!isOpen) { _openModelSheet(); }
      });
    }

    // Continue button — Opt 버튼 존재와 무관하게 항상 배선해야 한다.
    // (2단에서 Opt 버튼을 제거한 뒤에도 모델 시트의 Continue 가 동작하도록 if 밖으로 분리)
    _el('aiOptContinue')?.addEventListener('click', () => {
      _toggleContinue();   // 칩 + 패널 동기화 (외부 Cont 칩과 단일 진입점 공유)
    });

    // General USEKIT Project — master toggle (overrides section checks).
    _el('aiOptProjMeta')?.addEventListener('click', () => { _toggleProjectMeta(); });

    // META section cards — event delegation on the cards container.
    const _metaCards = _el('metaCards');
    if (_metaCards) {
      _metaCards.addEventListener('click', (e) => {
        // checkbox → inject ON/OFF
        const chk = e.target.closest('.meta-chk');
        if (chk) { _toggleMetaSection(chk.getAttribute('data-sec')); return; }
        // edit button → big overlay editor
        const edit = e.target.closest('.meta-edit');
        if (edit) { _expandMetaSection(edit.getAttribute('data-sec')); return; }
        // anywhere else on the head → inline readonly preview (peek)
        const head = e.target.closest('.meta-card-head');
        if (head) {
          const card = head.closest('.meta-card');
          const sec = card && card.getAttribute('data-sec');
          if (sec) _toggleMetaPreview(sec);
        }
      });
    }
    _el('metaSnapshot')?.addEventListener('click', () => {
      if (!window.confirm('현재 상태를 저장하시겠습니까?')) return;
      _saveMetaLast();
    });
    _el('metaLoad')?.addEventListener('click', () => {
      // Load = restore the last manual snapshot (project_meta.last.md).
      if (!window.confirm('직전 저장본을 불러올까요?\n현재 편집 중 내용은 사라집니다.')) return;
      _restoreMetaLast();
    });
    _el('metaReset')?.addEventListener('click', () => {
      // Destructive: replaces all META with the built-in default. Confirm first.
      if (!window.confirm('기본 설정으로 되돌립니다.\n현재 META 내용이 모두 사라집니다. 계속할까요?')) return;
      _resetMetaCards();
    });

    // ── Foldable sheet sections (Options / META) ──
    // Collapsed by default (display:none in HTML) to keep the sheet short on
    // mobile — the whole panel was taller than the viewport. Tap header to open.
    function _wireFold(headId, bodyId, arrowId) {
      const head = _el(headId), body = _el(bodyId), arrow = _el(arrowId);
      if (!head || !body) return;
      head.addEventListener('click', (e) => {
        e.stopPropagation();   // don't bubble to sheet/overlay close handlers
        const open = body.style.display === 'none';
        body.style.display = open ? '' : 'none';
        if (arrow) arrow.textContent = open ? '▾' : '▸';
      });
    }
    _wireFold('aiOptFoldHead', 'aiOptFold', 'aiOptFoldArrow');
    _wireFold('metaFoldHead', 'metaFold', 'metaFoldArrow');
    // Section editor overlay
    // Clicks inside the editor overlay must NOT bubble to the document-level
    // sheet/overlay close handlers (same reason _wireFold stops propagation),
    // otherwise closing/editing here also closes the whole META sheet → chat.
    _el('metaEditModal')?.addEventListener('click', (e) => { e.stopPropagation(); });
    _el('meCancel')?.addEventListener('click', () => { _closeMetaEdit(false); });
    _el('meCancel2')?.addEventListener('click', () => { _closeMetaEdit(false); });
    _el('meBackdrop')?.addEventListener('click', () => { _closeMetaEdit(false); });
    _el('meDone')?.addEventListener('click', () => { _closeMetaEdit(true); });
    _loadMetaCards();        // populate cards from project_meta.md on load
    _syncProjectMetaChip();  // reflect persisted master state

    if (aiOptBtn && optPanel) {
      // Model shortcut — opens model panel
      _el('aiOptModel')?.addEventListener('click', () => {
        _closeOptSheet();
        if (modelPanel) {
          _openModelSheet();
        }
      });

      const _optOverlay = _el('floatAiOptOverlay');
      if (_optOverlay) _optOverlay.addEventListener('click', () => { _closeOptSheet(); });

      // Token chips
      document.querySelectorAll('#aiOptTokenGroup .ai-opt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const val = parseInt(chip.dataset.tokens);
          if (!isNaN(val)) {
            _maxTokens = val;
            try { localStorage.setItem('usekit.ai.maxTokens', String(val)); } catch (e) {}
            document.querySelectorAll('#aiOptTokenGroup .ai-opt-chip').forEach(c => c.classList.remove('is-active'));
            chip.classList.add('is-active');
            window.UI?.showToast?.('Tokens: ' + val, 600);
            const _se = _el('aiActiveSub'); if (_se) _se.textContent = _badgeSubText();
          }
        });
      });

      // Temperature chips
      document.querySelectorAll('#aiOptTempGroup .ai-opt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const val = parseFloat(chip.dataset.temp);
          if (!isNaN(val)) {
            _temperature = val;
            try { localStorage.setItem('usekit.ai.temperature', String(val)); } catch (e) {}
            document.querySelectorAll('#aiOptTempGroup .ai-opt-chip').forEach(c => c.classList.remove('is-active'));
            chip.classList.add('is-active');
            window.UI?.showToast?.('Temp: ' + val, 600);
            const _se = _el('aiActiveSub'); if (_se) _se.textContent = _badgeSubText();
          }
        });
      });

      // Worker chips (chat only). 1 = single/fast, >=2 = parallel.
      document.querySelectorAll('#aiOptWorkerGroup .ai-opt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const val = parseInt(chip.dataset.workers, 10);
          if (!isNaN(val)) {
            _workers = val;
            try { localStorage.setItem('usekit.ai.workers', String(val)); } catch (e) {}
            document.querySelectorAll('#aiOptWorkerGroup .ai-opt-chip').forEach(c => c.classList.remove('is-active'));
            chip.classList.add('is-active');
            window.UI?.showToast?.(val > 1 ? ('Workers: ' + val + ' (parallel)') : 'Workers: 1 (fast)', 800);
            const _se = _el('aiActiveSub'); if (_se) _se.textContent = _badgeSubText();
          }
        });
      });
    }

    _syncOptChips = function () {
      // Continue button/tag/chip reflect the persisted _continueMode on open.
      const _contBtn = _el('aiOptContinue');
      const _contTag = _el('aiOptContTag');
      if (_contBtn) _contBtn.classList.toggle('is-active', _continueMode);
      if (_contTag) _contTag.textContent = _continueMode ? 'ON' : 'OFF';
      _syncContStatus();
      // Highlight active token chip
      const tokGrp = _el('aiOptTokenGroup');
      if (tokGrp) {
        tokGrp.querySelectorAll('.ai-opt-chip').forEach(c => {
          c.classList.toggle('is-active', parseInt(c.dataset.tokens) === (_maxTokens || 2048));
        });
      }
      // Highlight active temp chip
      const tmpGrp = _el('aiOptTempGroup');
      if (tmpGrp) {
        tmpGrp.querySelectorAll('.ai-opt-chip').forEach(c => {
          c.classList.toggle('is-active', parseFloat(c.dataset.temp) === (_temperature ?? 0.7));
        });
      }
      // Highlight active worker chip
      const wrkGrp = _el('aiOptWorkerGroup');
      if (wrkGrp) {
        wrkGrp.querySelectorAll('.ai-opt-chip').forEach(c => {
          c.classList.toggle('is-active', parseInt(c.dataset.workers, 10) === (_workers || 1));
        });
      }
      // WORKERS only applies to chat (ai_chat_v2). task(=job) is an agent path
      // with no worker concept — hide the section there to avoid confusion.
      const _wrkSec = _el('aiOptWorkerSection');
      const _wrkDiv = _el('aiOptWorkerDivider');
      const _hideWrk = (_chatSubMode === 'job');
      if (_wrkSec) _wrkSec.style.display = _hideWrk ? 'none' : '';
      if (_wrkDiv) _wrkDiv.style.display = _hideWrk ? 'none' : '';
    };

    // ── 패널 닫기 버튼 (✕) ──
    document.querySelectorAll('#floatAiModelPanel .float-panel-close, #floatAiAttachPanel .float-panel-close, #floatAiOptPanel .float-panel-close').forEach(btn => {
      btn.addEventListener('click', () => {
        const pid = btn.dataset.panel;
        if (pid) { const p = _el(pid); if (p) p.style.display = 'none'; }
        _closeAiPanels();
      });
    });

    // ── 드래그 (floatRunTool과 동일 패턴) ──
    let _aiDragging = false, _aiOx = 0, _aiOy = 0;
    let _aiDragMoved = false, _aiTouchId = null;

    function _aiOnStart(cx, cy) {
      _aiDragging = true; _aiDragMoved = false;
      const r = aiWrap.getBoundingClientRect();
      _aiOx = cx - r.left; _aiOy = cy - r.top;
    }
    function _aiOnMove(cx, cy) {
      if (!_aiDragging) return;
      const dx = Math.abs(cx - (aiWrap.getBoundingClientRect().left + _aiOx));
      const dy = Math.abs(cy - (aiWrap.getBoundingClientRect().top + _aiOy));
      if (dx > 8 || dy > 8) _aiDragMoved = true;
      if (!_aiDragMoved) return;
      _closeAiPanels();
      const w = aiWrap.offsetWidth || 48;
      const h = aiWrap.offsetHeight || 170;
      aiWrap.style.left = Math.max(0, Math.min(window.innerWidth - w, cx - _aiOx)) + 'px';
      aiWrap.style.top = Math.max(0, Math.min(window.innerHeight - h, cy - _aiOy)) + 'px';
      aiWrap.style.right = 'auto';
      aiWrap.style.bottom = 'auto';
    }
    function _aiOnEnd() {
      _aiDragging = false;
      setTimeout(() => { _aiDragMoved = false; }, 50);
    }

    aiWrap.addEventListener('touchstart', (e) => {
      if (e.touches.length !== 1) return;
      _aiTouchId = e.touches[0].identifier;
      _aiOnStart(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
    aiWrap.addEventListener('touchmove', (e) => {
      for (const t of e.changedTouches) {
        if (t.identifier === _aiTouchId) { _aiOnMove(t.clientX, t.clientY); break; }
      }
    }, { passive: true });
    aiWrap.addEventListener('touchend', () => { _aiOnEnd(); }, { passive: true });

    aiWrap.addEventListener('mousedown', (e) => { _aiOnStart(e.clientX, e.clientY); });
    window.addEventListener('mousemove', (e) => { if (_aiDragging) _aiOnMove(e.clientX, e.clientY); });
    window.addEventListener('mouseup', () => { if (_aiDragging) _aiOnEnd(); });

    // 배경 클릭 시 패널 닫기
    document.addEventListener('click', (e) => {
      if (!aiWrap.contains(e.target) &&
          !(modelPanel && modelPanel.contains(e.target)) &&
          !(attachPanel && attachPanel.contains(e.target))) {
        _closeAiPanels();
      }
    });
  });

  // ── TOOL 팝업 안 챗모드 버튼 (Think/Add/Model) 이벤트 ──
  document.addEventListener('DOMContentLoaded', () => {
    const _closeTp = () => {
      const tp = _el('floatToolPanel');
      if (tp) tp.style.display = 'none';
      const tb = _el('floatBtnTool');
      if (tb) tb.classList.remove('is-active');
    };

    // Think 토글
    _el('floatTpThink')?.addEventListener('click', () => {
      _thinkMode = !_thinkMode;
      const label = _el('floatTpThinkLabel');
      if (label) label.textContent = _thinkMode ? 'Think ●' : 'Think';
      _closeTp();
    });

    // Add (Attach) — 패널 토글
    _el('floatTpAdd')?.addEventListener('click', () => {
      _closeTp();
      const ap = _el('floatAiAttachPanel');
      if (!ap) return;
      const isOpen = ap.style.display === 'flex';
      _closeAiPanels();
      if (!isOpen) {
        // TOOL 버튼 근처에 표시
        const toolBtn = _el('floatBtnTool');
        if (toolBtn) {
          const r = toolBtn.getBoundingClientRect();
          ap.style.right = (window.innerWidth - r.right) + 'px';
          ap.style.bottom = (window.innerHeight - r.top + 6) + 'px';
          ap.style.left = 'auto'; ap.style.top = 'auto';
        }
        ap.style.display = 'flex';
      }
    });

    // Model — 패널 토글
    _el('floatTpModel')?.addEventListener('click', () => {
      _closeTp();
      const mp = _el('floatAiModelPanel');
      if (!mp) return;
      const isOpen = mp.classList.contains('open');
      _closeAiPanels();
      if (!isOpen) {
        _openModelSheet();
      }
    });

    // Model click delegation — handles dynamic buttons from _renderModelPanel
    // (static binding on init-time DOM misses dynamically created buttons)

    // Inject JOB toggle eagerly so users see it without first switching to chat.
    // Retries cover cases where the header is rendered asynchronously by other modules.
    _updateStopBtn();
    setTimeout(_updateStopBtn, 200);
    setTimeout(_updateStopBtn, 800);
  });

  // ── Global API — used by float_run.js to check mode ──
  window.AiChat = {
    get mode() { return _mode; },
    get isChat() { return _mode === 'chat'; },
    get subMode() { return _chatSubMode; },   // 'chat' | 'job' — float_run dock2 mode 매칭용
    get isRunning() { return _aiRunning; },
    get transcript() { return _transcript; },
    get ctxMode() { return _ctxMode; },
    set ctxMode(m) { _ctxMode = m; },
    onSlotChanged: _onSlotChanged,
    get boundSlot() { return _boundSlot; },
    get thinkMode() { return _thinkMode; },
    get model() { return _aiModel; },
    get attachments() { return _attachments; },
    enterChat: _enterChatMode,
    enterEdit: _enterEditMode,
    toggle: _toggleMode,
    _updateTabUI,
    refreshSegState: _updateSegState,
    // 고정 2단(#rpDock2) chat 도구 재렌더 (float_run._ensureDock2Filled 가 위임)
    refreshDock2() { _updateMiniRunForChat(true); },
    // Chat-mode execution (called from Run/Line/Block routing)
    run: _chatRun,
    line: _chatLine,
    block: _chatBlock,
    // Persistence
    persist: _persistChat,
    restore: _restoreChat,
    // Clear transcript + OPFS
    clearTranscript() {
      _transcript = [];
      _chatLogHtml = '';
      _activeLiveSessionId = '';   // P1-1: next message starts a fresh session
      const name = _boundSlot || _currentSlotName();
      if (name) window.SlotStorage?.removeChat?.(name);
    },
    get isLocked() { return _sessionLocked; },
    unlock() { _sessionLocked = false; },
    // JOB sub-mode (console debugging / manual control)
    get jobMode() { return _chatSubMode; },
    setJobMode(m) { _setChatSubMode(m); },
    get activeJob() { return _activeJobId; },
    forceJobToggle() { _updateStopBtn(); return _el('btnAiJobToggle'); },
  };
})();
