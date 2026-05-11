// float_ai.js — AI Chat mode (edit ↔ chat tab switching)
// ────────────────────────────────────────────────────────
//  EDIT mode: editor = code,   panel = OUTPUT
//  CHAT mode: editor = prompt, panel = AI CHAT log
//
//  Run/Line/Block buttons change meaning per mode.
//  Uses /api/exec → !uk ai claude -c "prompt" (shell escape)
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

  // AI provider
  const _provider = 'claude';

  // Running state
  let _aiRunning = false;

  // ── Slot-bound chat persistence ──────────────────────────
  let _boundSlot = '';    // 현재 바인딩된 슬롯 fileName

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
        timestamp: Date.now(),
      });
    } catch(e) { console.warn('[AiChat] persist failed:', e); }
  }

  // OPFS에서 복원 → transcript + chatLogHtml 재구성
  async function _restoreChat(slotName) {
    if (!slotName) return false;
    try {
      const data = window.SlotStorage?.readChat?.(slotName)
                || await window.SlotStorage?.readChatAsync?.(slotName);
      if (!data?.transcript?.length) return false;
      _transcript = data.transcript.slice(-_MAX_TRANSCRIPT);
      if (data.ctxMode) _ctxMode = data.ctxMode;
      // transcript에서 HTML 재구성
      _chatLogHtml = _rebuildHtml(_transcript);
      return true;
    } catch(e) { console.warn('[AiChat] restore failed:', e); return false; }
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
        return `<div style="margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;color:#7ee787;">[${time}] AI</div>`
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
  function _appendToChatLog(role, text) {
    const output = _el('runOutput');
    if (!output) return null;

    // Record to transcript (skip empty AI placeholders)
    if (text && (role === 'user' || role === 'ai')) {
      _transcript.push({ time: _ts(), role, content: text });
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
      header.textContent = `[${_ts()}] AI`;
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

    // Detect recall-type questions → auto-upgrade to 'recall'
    const recallKeywords = /뭐라고 했|뭐라 했|처음에|첫 말|기억|원문|정확히|뭐였/;
    const effectiveMode = recallKeywords.test(prompt) ? 'recall' : _ctxMode;

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

  // ── Send prompt via /api/exec ──
  async function _sendPrompt(rawPrompt) {
    if (!rawPrompt.trim()) return;
    if (_aiRunning) return;

    // Parse inline mode override
    const parsed = _parsePrompt(rawPrompt);
    const savedMode = _ctxMode;
    if (parsed.mode) _ctxMode = parsed.mode;
    const prompt = parsed.prompt || rawPrompt;

    _aiRunning = true;
    _updateStopBtn();

    // Show user message (display original, not with context)
    _appendToChatLog('user', rawPrompt);

    // Show thinking placeholder
    const aiBody = _appendToChatLog('ai', '');

    // Build prompt with context (based on mode)
    const context = _buildContext(prompt);

    // Build attachments prefix
    let attachPrefix = '';
    if (_attachments.length) {
      for (const att of _attachments) {
        if (att.type === 'file') attachPrefix += `[FILE: ${att.name}]\n${att.content}\n[/FILE]\n\n`;
        else if (att.type === 'block') attachPrefix += `[CODE]\n${att.content}\n[/CODE]\n\n`;
        else if (att.type === 'image') {
          if (att._path) {
            // 파일 경로 포함 → CLI가 Read 도구로 이미지 분석 가능
            attachPrefix += `[IMAGE: ${att.name}]\nFile path: ${att._path}\nPlease read and analyze this image file.\n[/IMAGE]\n\n`;
          } else {
            attachPrefix += `[IMAGE: ${att.name}]\n`;
          }
        }
      }
      _attachments = [];  // 전송 후 초기화
      _updateAttachPreview();
    }

    const fullPrompt = context + attachPrefix + prompt;

    // Restore mode after use
    _ctxMode = savedMode;

    // Build shell command
    const escaped = _shellEscape(fullPrompt);
    const cmd = `!uk ai ${_provider} -c '${escaped}'`;

    let aiText = '';
    try {
      const resp = await fetch('/api/exec', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: cmd, mode: 'single', inputs: [], timeout: 120 }),
      });
      const d = await resp.json();

      if (d.stdout) aiText = d.stdout.trim();
      if (d.stderr) aiText += (aiText ? '\n' : '') + d.stderr.trim();
      if (d.error && !d.ok) aiText += (aiText ? '\n' : '') + '[ERROR] ' + d.error;
      if (!aiText) aiText = '(no response)';

      if (aiBody) {
        aiBody.innerHTML = `<span style="color:#c9d1d9;">${_esc(aiText)}</span>`;
      }
    } catch (err) {
      aiText = '[Network error] ' + String(err);
      if (aiBody) {
        aiBody.innerHTML = `<span style="color:#ff7b72;">${_esc(aiText)}</span>`;
      }
    }

    // Record AI response to transcript (always, for local history)
    _transcript.push({ time: _ts(), role: 'ai', content: aiText });
    if (_transcript.length > _MAX_TRANSCRIPT) {
      _transcript = _transcript.slice(-_MAX_TRANSCRIPT);
    }

    _aiRunning = false;
    _updateStopBtn();

    // Save chat log
    const output = _el('runOutput');
    if (output) {
      output.scrollTop = output.scrollHeight;
      _chatLogHtml = output.innerHTML;
    }

    // Persist to OPFS (슬롯에 묶어서 보관)
    _persistChat();

    // Clear editor (prompt consumed) and move cursor to line 1
    if (_mode === 'chat') {
      window.Editor?.setText?.('');
      _chatDraft = '';
    }
  }

  // ── Mode switching ──
  // edit/chat = 내용만 다름. 패널 ON/OFF는 RunView.enterEditMode/exitEditMode 그대로 사용.
  // edit 탭 재클릭 = inline ON/OFF 토글 (float_run.js 원래 동작)
  // chat 탭 재클릭 = inline ON/OFF 토글 (동일 논리)
  // edit↔chat 전환 = 내용만 교체, 패널 ON/OFF 상태 유지.
  //   단, 패널이 닫혀있으면 열어줌 (chat 진입 시).

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
        _chatLogHtml = _rebuildHtml(_transcript);
      } else if (!_transcript.length) {
        // 동기 miss → 비동기 시도 (OPFS lazy load)
        _restoreChat(curSlot).then(ok => {
          if (ok && _mode === 'chat') {
            const output = _el('runOutput');
            if (output) { output.innerHTML = _chatLogHtml; output.scrollTop = output.scrollHeight; }
          }
        });
      }
    } else if (!_boundSlot && curSlot) {
      // 최초 진입 — 복원 시도
      _boundSlot = curSlot;
      const syncData = window.SlotStorage?.readChat?.(curSlot);
      if (syncData?.transcript?.length) {
        _transcript = syncData.transcript.slice(-_MAX_TRANSCRIPT);
        if (syncData.ctxMode) _ctxMode = syncData.ctxMode;
        _chatLogHtml = _rebuildHtml(_transcript);
      } else if (!_transcript.length) {
        _restoreChat(curSlot).then(ok => {
          if (ok && _mode === 'chat') {
            const output = _el('runOutput');
            if (output) { output.innerHTML = _chatLogHtml; output.scrollTop = output.scrollHeight; }
          }
        });
      }
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
      output.innerHTML = _chatLogHtml;
      output.scrollTop = output.scrollHeight;
    }

    // 패널이 닫혀있으면 inline으로 열기
    if (!window.RunView?.editModeActive) {
      window.RunView?.enterEditMode?.();
    }

    // 첨부 프리뷰 바 복원
    _updateAttachPreview();

    _updateTabUI();
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
      if (editBtn) { editBtn.textContent = 'edit'; editBtn.classList.remove('is-active'); }
      if (chatBtn) { chatBtn.innerHTML = 'chat <span style="font-size:6px;vertical-align:middle;color:#a78bfa;">●</span>'; chatBtn.classList.add('is-active'); chatBtn.style.color = '#a78bfa'; }
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
      // edit 모드 — inline 패널이 열려있으면 edit ● 점등
      if (window.RunView?.editModeActive) {
        if (editBtn) { editBtn.textContent = 'edit ●'; editBtn.classList.add('is-active'); }
      } else {
        if (editBtn) { editBtn.textContent = 'edit'; editBtn.classList.remove('is-active'); }
      }
      if (chatBtn) { chatBtn.textContent = 'chat'; chatBtn.classList.remove('is-active'); chatBtn.style.color = ''; }
      if (title) { title.innerHTML = '<span style="font-size:9px;">▶</span> OUTPUT'; }
      if (aiLabel) { aiLabel.textContent = 'AI'; }
      // TOOL 팝업: Edit 그룹 표시, Chat 그룹 숨김
      if (tpEditGroup) tpEditGroup.style.display = '';
      if (tpChatGroup) tpChatGroup.style.display = 'none';
      if (tpTitle) tpTitle.textContent = 'Run Tool';
      // 미니런 패널: 에디트모드 내용으로 복원
      _updateMiniRunForChat(false);
      // 미니런 패널 복원 (edit inline이면)
      const mini = _el('miniRunPanel');
      if (mini && window.RunView?.editModeActive) mini.style.display = '';
      // 패널 상단 보더 초록색 복원
      const inner = _el('runPanelInner');
      if (inner && inner.style.borderTop) inner.style.borderTop = '2px solid #4caf50';
      const badge = _el('aiBadge');
      if (badge) badge.style.display = 'none';
    }
  }

  // ── 미니런 패널 내용을 챗모드/에디트모드에 따라 교체 ──
  function _updateMiniRunForChat(isChat) {
    const mini = _el('miniRunPanel');
    if (!mini) return;
    const body = mini.querySelector('.minirun-body');
    const cap = mini.querySelector('.minirun-cap');
    const hdr = mini.querySelector('div'); // first div = header
    if (!body) return;

    if (isChat) {
      // 챗모드: Think / Add / Model
      body.innerHTML = '';
      const mkBtn = (icon, label, color, fn) => {
        const b = document.createElement('button');
        b.innerHTML = `<span style="font-size:11px;">${icon}</span> ${label}`;
        b.style.cssText = `flex:1; padding:6px 4px; border:none; border-radius:5px;
          background:rgba(255,255,255,0.06); color:${color};
          font-size:11px; font-weight:500; cursor:pointer; white-space:nowrap;`;
        b.addEventListener('touchend', e => { e.preventDefault(); e.stopPropagation(); fn(); });
        b.addEventListener('mouseup', e => { e.stopPropagation(); fn(); });
        return b;
      };
      body.appendChild(mkBtn('◎', _thinkMode ? 'Think●' : 'Think', '#a78bfa', () => {
        _thinkMode = !_thinkMode;
        _updateMiniRunForChat(true); // 라벨 갱신
      }));
      body.appendChild(mkBtn('＋', 'Add', '#7ee787', () => {
        // Attach panel 토글 — floatAiAttachPanel 재사용
        const ap = _el('floatAiAttachPanel');
        if (ap) {
          const isOpen = ap.style.display === 'flex';
          ap.style.display = isOpen ? 'none' : 'flex';
          if (!isOpen) {
            const r = mini.getBoundingClientRect();
            ap.style.right = (window.innerWidth - r.right) + 'px';
            ap.style.bottom = (window.innerHeight - r.top + 6) + 'px';
            ap.style.left = 'auto'; ap.style.top = 'auto';
          }
        }
      }));
      body.appendChild(mkBtn('▾', _aiModel, '#58a6ff', () => {
        // Model panel 토글 — floatAiModelPanel 재사용
        const mp = _el('floatAiModelPanel');
        if (mp) {
          const isOpen = mp.style.display === 'flex';
          mp.style.display = isOpen ? 'none' : 'flex';
          if (!isOpen) {
            const r = mini.getBoundingClientRect();
            mp.style.right = (window.innerWidth - r.right) + 'px';
            mp.style.bottom = (window.innerHeight - r.top + 6) + 'px';
            mp.style.left = 'auto'; mp.style.top = 'auto';
            mp.querySelectorAll('.ai-model-opt').forEach(b => {
              b.classList.toggle('is-selected', b.dataset.model === _aiModel);
            });
          }
        }
      }));
      if (cap) cap.innerHTML = '<span style="color:#a78bfa;">◎</span> <span style="color:#7ee787;">＋</span> <span style="color:#58a6ff;">▾</span>';
      if (hdr) hdr.textContent = 'AI';
      // fold 버튼 재생성 (hdr 교체 시 사라지므로)
      if (hdr) {
        const foldBtn = document.createElement('span');
        foldBtn.textContent = '▾';
        foldBtn.style.cssText = 'cursor:pointer; font-size:12px; padding:0 4px; color:rgba(255,255,255,0.4);';
        foldBtn.addEventListener('click', e => { e.stopPropagation(); mini.querySelector('.minirun-body')?.style && _toggleMiniFold(mini); });
        hdr.appendChild(foldBtn);
      }
    } else {
      // 에디트모드: Run / Line / Block — float_run.js가 재생성하므로 여기서는 hide만
      // miniRunPanel은 float_run.js의 _showMiniRun이 생성하므로 삭제 후 재생성 위임
      mini.remove();
      if (window.RunView?.editModeActive) {
        // float_run.js가 다시 만들어줌
        window.RunView._refreshMiniRun?.();
      }
    }
  }

  function _toggleMiniFold(mini) {
    const body = mini.querySelector('.minirun-body');
    const cap = mini.querySelector('.minirun-cap');
    if (!body) return;
    const wasOpen = body.style.display !== 'none';
    body.style.display = wasOpen ? 'none' : 'flex';
    if (cap) cap.style.display = wasOpen ? 'block' : 'none';
  }

  function _updateStopBtn() {
    // Could show/hide a stop indicator in the header
  }

  // ── Chat-mode execution (replaces Run/Line/Block) ──
  function _chatRun() {
    const text = window.Editor?.getText?.() || '';
    if (text.trim()) {
      // 키보드 내리기 + 출력 패널(오버레이)로 전환
      document.activeElement?.blur?.();
      if (window.RunView?.editModeActive) window.RunView.exitEditMode();
      const o = _el('runOutput'); if (o) setTimeout(() => { o.scrollTop = o.scrollHeight; }, 100);
      _sendPrompt(text.trim());
    }
  }

  function _chatLine() {
    const view = window.Editor?.get?.();
    if (!view) return;
    const pos = view.state.selection.main.head;
    const line = view.state.doc.lineAt(pos);
    const text = line.text.trim();
    if (text) _sendPrompt(text);
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
    if (titleSpan) titleSpan.id = 'runPanelTitle';

    // Insert chat button after edit button
    const editBtn = _el('btnRunEdit');
    if (editBtn) {
      const chatBtn = document.createElement('button');
      chatBtn.id = 'btnAiChat';
      chatBtn.textContent = 'chat';
      chatBtn.style.cssText = editBtn.style.cssText || '';
      editBtn.parentNode.insertBefore(chatBtn, editBtn.nextSibling);

      // ── chat 탭 클릭 ──
      // edit→chat: 모드 전환 (내용 교체 + 패널 열기)
      // chat→chat (inline): inline 닫고 overlay로 크게 보기
      // chat→chat (overlay): overlay 닫고 inline 복귀
      // chat→chat (둘 다 닫힘): inline으로 열기
      chatBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (_mode === 'chat') {
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
          return;
        }
        // edit→chat 전환
        _enterChatMode();
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
          _enterEditMode();              // 내용만 전환, 패널 상태 유지
        }
      }, true);  // capture phase
    }

    // Clear button: clear appropriate log
    const clearBtn = _el('btnRunClear');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (_mode === 'chat') {
          _chatLogHtml = '';
          _transcript = [];
          // OPFS에서도 삭제
          const name = _boundSlot || _currentSlotName();
          if (name) window.SlotStorage?.removeChat?.(name);
          // DOM is already cleared by float_run.js handler
        }
      });
    }

    // Close button: AI 모드일 때는 edit 모드로 복귀 + 패널 닫기
    const closeBtn = _el('btnRunClose');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
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

  function _closeAiPanels() {
    const mp = _el('floatAiModelPanel');
    const ap = _el('floatAiAttachPanel');
    if (mp) mp.style.display = 'none';
    if (ap) ap.style.display = 'none';
    const mb = _el('floatAiModel');
    const ab = _el('floatAiAttach');
    if (mb) mb.classList.remove('is-active');
    if (ab) ab.classList.remove('is-active');
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
    const r = anchorBtn.getBoundingClientRect();
    panel.style.right = (window.innerWidth - r.right) + 'px';
    panel.style.bottom = (window.innerHeight - r.top + 6) + 'px';
    panel.style.left = 'auto';
    panel.style.top = 'auto';
  }

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
        const mp = _el('floatAiModelPanel');
        if (mp) mp.style.display = 'none';
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

    // ── Model(▾) 버튼 — 패널 토글 ──
    const aiModelBtn = _el('floatAiModel');
    const modelPanel = _el('floatAiModelPanel');
    if (aiModelBtn && modelPanel) {
      aiModelBtn.addEventListener('click', (e) => {
        if (_aiDragMoved) return;
        e.stopPropagation();
        if (attachPanel) attachPanel.style.display = 'none';
        const isOpen = modelPanel.style.display === 'flex';
        if (isOpen) {
          modelPanel.style.display = 'none';
        } else {
          _positionPanel(modelPanel, aiModelBtn);
          modelPanel.style.display = 'flex';
          // 현재 선택 표시
          modelPanel.querySelectorAll('.ai-model-opt').forEach(b => {
            b.classList.toggle('is-selected', b.dataset.model === _aiModel);
          });
        }
      });

      // 모델 선택
      modelPanel.querySelectorAll('.ai-model-opt').forEach(btn => {
        btn.addEventListener('click', () => {
          _aiModel = btn.dataset.model;
          const label = _el('floatAiModelLabel');
          if (label) label.textContent = _aiModel;
          modelPanel.style.display = 'none';
          window.UI?.showToast?.('Model: ' + _aiModel, 800);
        });
      });
    }

    // ── 패널 닫기 버튼 (✕) ──
    document.querySelectorAll('#floatAiModelPanel .float-panel-close, #floatAiAttachPanel .float-panel-close').forEach(btn => {
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
      const isOpen = mp.style.display === 'flex';
      _closeAiPanels();
      if (!isOpen) {
        const toolBtn = _el('floatBtnTool');
        if (toolBtn) {
          const r = toolBtn.getBoundingClientRect();
          mp.style.right = (window.innerWidth - r.right) + 'px';
          mp.style.bottom = (window.innerHeight - r.top + 6) + 'px';
          mp.style.left = 'auto'; mp.style.top = 'auto';
        }
        mp.style.display = 'flex';
        mp.querySelectorAll('.ai-model-opt').forEach(b => {
          b.classList.toggle('is-selected', b.dataset.model === _aiModel);
        });
      }
    });

    // Model 선택 이벤트 (기존 floatAiModelPanel 내 버튼 재활용)
    _el('floatAiModelPanel')?.querySelectorAll('.ai-model-opt').forEach(btn => {
      btn.addEventListener('click', () => {
        _aiModel = btn.dataset.model;
        const label = _el('floatTpModelLabel');
        if (label) label.textContent = _aiModel;
        const mp = _el('floatAiModelPanel');
        if (mp) mp.style.display = 'none';
        window.UI?.showToast?.('Model: ' + _aiModel, 800);
      });
    });
  });

  // ── Global API — used by float_run.js to check mode ──
  window.AiChat = {
    get mode() { return _mode; },
    get isChat() { return _mode === 'chat'; },
    get isRunning() { return _aiRunning; },
    get transcript() { return _transcript; },
    get ctxMode() { return _ctxMode; },
    set ctxMode(m) { _ctxMode = m; },
    get boundSlot() { return _boundSlot; },
    get thinkMode() { return _thinkMode; },
    get model() { return _aiModel; },
    get attachments() { return _attachments; },
    enterChat: _enterChatMode,
    enterEdit: _enterEditMode,
    toggle: _toggleMode,
    _updateTabUI,
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
      const name = _boundSlot || _currentSlotName();
      if (name) window.SlotStorage?.removeChat?.(name);
    },
  };
})();
