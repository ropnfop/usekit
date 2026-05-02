// float_run.js — Run pill logic (extracted from index.html)
(function() {
  const wrap      = document.getElementById('floatRunTool');
  const toolPanel = document.getElementById('floatToolPanel');
  const btnRun    = document.getElementById('floatBtnRun');
  const btnOut    = document.getElementById('floatBtnOutput');
  const btnTool   = document.getElementById('floatBtnTool');
  if (!wrap || !toolPanel) return;

  // ── 풋터 btnRunTool → 플로팅 표시 ──
  const trigger = document.getElementById('btnRunTool');
  if (trigger) {
    let _tc = false;
    trigger.addEventListener('touchstart', e => { e.preventDefault(); _tc = true; }, { passive: false });
    trigger.addEventListener('touchend',   e => { e.preventDefault(); if (_tc) { _tc = false; toggleFloat(); } }, { passive: false });
    trigger.addEventListener('mouseup',    e => { if (!_tc) toggleFloat(); });
  }

  // ── 타임스탬프 ──
  function _ts() {
    const d = new Date();
    return [d.getHours(), d.getMinutes(), d.getSeconds()]
      .map(n => String(n).padStart(2,'0')).join(':');
  }

  // ── stdout pretty-format (Python list/dict 출력 정리) ──
  function _fmtStdout(raw) {
    if (!raw || !raw.trim()) return raw;
    console.log('[_fmtStdout] called, len=', raw.length);
    // 여러 줄일 수 있으므로 줄 단위로 처리
    return raw.split('\n').map(line => {
      const t = line.trim();
      if (!t) return line;
      // 1) JSON 시도
      if ((t[0] === '[' || t[0] === '{') && (t[t.length-1] === ']' || t[t.length-1] === '}')) {
        try {
          const obj = JSON.parse(t);
          return JSON.stringify(obj, null, 2);
        } catch(_) { /* fall through to Python repr formatter */ }
      }
      // 2) Python repr 패턴: [{...},...] 또는 {...} 형태가 길면 포맷팅
      if (t.length > 80 && /^[\[({]/.test(t)) {
        return _fmtPythonRepr(t);
      }
      return line;
    }).join('\n');
  }

  // Python repr → 읽기 쉬운 들여쓰기
  function _fmtPythonRepr(s) {
    let out = '', indent = 0, inStr = false, strCh = '';
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      // 문자열 내부 추적
      if (inStr) {
        out += c;
        if (c === '\\') { out += s[++i] || ''; continue; }
        if (c === strCh) inStr = false;
        continue;
      }
      if (c === "'" || c === '"') { inStr = true; strCh = c; out += c; continue; }
      if (c === '{' || c === '[' || c === '(') {
        indent++;
        out += c + '\n' + '  '.repeat(indent);
      } else if (c === '}' || c === ']' || c === ')') {
        indent = Math.max(0, indent - 1);
        out += '\n' + '  '.repeat(indent) + c;
      } else if (c === ',') {
        out += ',\n' + '  '.repeat(indent);
        // 콤마 뒤 공백 스킵
        if (s[i+1] === ' ') i++;
      } else {
        out += c;
      }
    }
    return out;
  }

  // ── 출력 누적 append ──
  function _appendOutput(mode, data) {
    const outPanel = document.getElementById('runPanel');
    const output   = document.getElementById('runOutput');
    if (!outPanel || !output) return;

    // 패널 열기 (edit 모드가 아닐 때만 overlay로)
    if (!_runEditActive) outPanel.classList.add('is-open');
    btnOut.classList.add('is-active');

    const esc = s => s
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      // ANSI 이스케이프 제거
      .replace(/\x1b\[[0-9;]*m/g,'')
      .replace(/\n/g,'<br>');

    // 헤더 블록
    const header = document.createElement('div');
    header.style.cssText = 'margin-top:0.7rem;margin-bottom:0.25rem;font-size:0.72rem;font-weight:700;letter-spacing:0.04em;opacity:0.55;';
    header.textContent = `[USEKIT - ${_ts()}] [${mode}]`;

    // 콘텐츠 블록
    const body = document.createElement('div');
    body.style.cssText = 'margin-bottom:0.2rem;';
    let html = '';
    if (data.running) {
      html = '<span style="opacity:0.35;">running...</span>';
    } else {
      if (data.stdout) html += `<span style="color:#c9d1d9;">${esc(_fmtStdout(data.stdout))}</span>`;
      if (data.stderr) html += `<span style="color:#f97583;">${esc(data.stderr)}</span>`;
      if (data.error && !data.ok) html += `<span style="color:#ff7b72;">[ERROR] ${esc(data.error)}</span>`;
      if (!html) html = '<span style="opacity:0.35;">(no output)</span>';
    }
    body.innerHTML = html;

    output.appendChild(header);
    output.appendChild(body);
    output.scrollTop = output.scrollHeight;

    return body; // running 중 교체용
  }

  // ── 공통 fetch + output 처리 ──
  function _execFetch(code, label) {
    if (!_runEditActive) { try { window.UIViewport?.blockKeyboard?.(); } catch (e) {} }
    if (!code.trim()) return;
    const bodyEl = _appendOutput(label, { running: true });
    fetch('/api/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, inputs: [], timeout: 15 }),
    })
    .then(r => r.json())
    .catch(() => ({ ok: false, error: 'network_error', stdout: '', stderr: '' }))
    .then(d => {
      if (!bodyEl) return;
      const esc = s => s
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/\x1b\[[0-9;]*m/g,'')
        .replace(/\n/g,'<br>');
      let html = '';
      if (d.stdout) html += `<span style="color:#c9d1d9;">${esc(_fmtStdout(d.stdout))}</span>`;
      if (d.stderr) html += `<span style="color:#f97583;">${esc(d.stderr)}</span>`;
      if (d.error && !d.ok) html += `<span style="color:#ff7b72;">[ERROR] ${esc(d.error)}</span>`;
      if (!html) html = '<span style="opacity:0.35;">(no output)</span>';
      bodyEl.innerHTML = html;
      const output = document.getElementById('runOutput');
      if (output) output.scrollTop = output.scrollHeight;
    });
  }

  // ── 실행: Run (repl — exec 직접 실행) ──
  function _doExec() {
    if (window.runExec) { window.runExec(); return; }
    const code = window.Editor?.getText?.() || '';
    _execFetch(code, 'RUN');
  }

  // ── 실행: File tmp (u.wpt + u.xpt 래핑 → repl로 실행) ──
  function _doExecFileTmp() {
    const raw = window.Editor?.getText?.() || '';
    if (!raw.trim()) return;
    // ''' 충돌 방지: 코드 내 ''' → 이스케이프
    const escaped = raw.replace(/'''/g, "\\'''");
    const wrapped = `u.wpt(r'''${escaped}''',"_ed_run")\nu.xpt("_ed_run")`;
    _execFetch(wrapped, 'FILE');
  }

  // ── 실행: Run Print (block_echo — 마지막 표현식 결과 자동표시) ──
  function _doExecPrint() {
    const code = window.Editor?.getText?.() || '';
    if (!code.trim()) return;
    if (!_runEditActive) { try { window.UIViewport?.blockKeyboard?.(); } catch (e) {} }
    const bodyEl = _appendOutput('PRINT', { running: true });
    fetch('/api/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, mode: 'block_echo', inputs: [], timeout: 15 }),
    })
    .then(r => r.json())
    .catch(() => ({ ok: false, error: 'network_error', stdout: '', stderr: '' }))
    .then(d => {
      if (!bodyEl) return;
      const esc = s => s
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/\x1b\[[0-9;]*m/g,'')
        .replace(/\n/g,'<br>');
      let html = '';
      if (d.stdout) html += `<span style="color:#c9d1d9;">${esc(_fmtStdout(d.stdout))}</span>`;
      if (d.stderr) html += `<span style="color:#f97583;">${esc(d.stderr)}</span>`;
      if (d.error && !d.ok) html += `<span style="color:#ff7b72;">[ERROR] ${esc(d.error)}</span>`;
      if (!html) html = '<span style="opacity:0.35;">(no output)</span>';
      bodyEl.innerHTML = html;
      const output = document.getElementById('runOutput');
      if (output) output.scrollTop = output.scrollHeight;
    });
  }

  // ── Output 패널 토글 ──
  function _toggleOutput() {
    const outPanel = document.getElementById('runPanel');
    if (!outPanel) return;
    if (_runEditActive) {
      _exitRunEditMode();
      return;
    }
    const isOpen = outPanel.classList.contains('is-open');
    if (isOpen) {
      outPanel.classList.remove('is-open');
      btnOut.classList.remove('is-active');
    } else {
      // 키보드 내린 후 overlay 열기 (딜레이로 리사이즈 깜박임 방지)
      try { window.UIViewport?.blockKeyboard?.(); } catch (e) {}
      setTimeout(() => {
        outPanel.classList.add('is-open');
        btnOut.classList.add('is-active');
        const output = document.getElementById('runOutput');
        if (output) output.scrollTop = output.scrollHeight;
      }, 150);
    }
  }

  // ── Tool 패널 토글 ──
  function _positionToolPanel() {
    const r = wrap.getBoundingClientRect();
    const isHorizontal = wrap.classList.contains('is-horizontal');
    const margin = 8;
    const panelW = toolPanel.offsetWidth  || 148;
    const panelH = toolPanel.offsetHeight || 320;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const pillCx = r.left + r.width / 2;
    const pillCy = r.top  + r.height / 2;

    if (isHorizontal) {
      // 가로 pill: 상/하 중 공간 있는 쪽으로 드롭, 좌우는 pill 우측끝 정렬
      const pillOnUpperHalf = pillCy < vh / 2;
      let topVal;
      if (pillOnUpperHalf) {
        topVal = r.bottom + 8;                 // pill 아래
      } else {
        topVal = r.top - panelH - 8;           // pill 위
      }
      topVal = Math.max(margin, Math.min(vh - panelH - margin, topVal));

      let leftVal = r.right - panelW;          // 우측 정렬
      leftVal = Math.max(margin, Math.min(vw - panelW - margin, leftVal));

      toolPanel.style.top    = topVal  + 'px';
      toolPanel.style.left   = leftVal + 'px';
      toolPanel.style.right  = 'auto';
      toolPanel.style.bottom = 'auto';
    } else {
      // 세로 pill: 좌/우 중 공간 있는 쪽으로 attach, 세로는 pill 중앙 정렬
      const pillOnLeftHalf = pillCx < vw / 2;
      if (pillOnLeftHalf) {
        // 오른쪽 attach (left = pill 오른쪽 + 간격)
        let leftVal = r.right + 10;
        leftVal = Math.max(margin, Math.min(vw - panelW - margin, leftVal));
        toolPanel.style.left   = leftVal + 'px';
        toolPanel.style.right  = 'auto';
      } else {
        // 왼쪽 attach (right = 화면폭 - pill 왼쪽 + 간격)
        let rightVal = vw - r.left + 10;
        rightVal = Math.max(margin, Math.min(vw - panelW - margin, rightVal));
        toolPanel.style.right = rightVal + 'px';
        toolPanel.style.left  = 'auto';
      }
      let topVal = pillCy - panelH / 2;
      topVal = Math.max(margin, Math.min(vh - panelH - margin, topVal));
      toolPanel.style.top    = topVal + 'px';
      toolPanel.style.bottom = 'auto';
    }
  }

  function _toggleTool() {
    const show = toolPanel.style.display === 'none' || toolPanel.style.display === '';
    if (show) {
      _positionToolPanel();
    }
    toolPanel.style.display = show ? 'flex' : 'none';
    btnTool.classList.toggle('is-active', show);
    // 렌더 후 위치 재보정 (offsetWidth/Height 확정된 후)
    if (show) requestAnimationFrame(_positionToolPanel);
  }

  function showFloat() {
    wrap.style.display = 'flex';
    wrap.style.pointerEvents = '';          // 히트테스트 복원
    toolPanel.style.display = 'none';
    try { localStorage.setItem('usekit_float_visible', '1'); } catch (e) {}
  }
  function hideFloat() {
    wrap.style.display = 'none';
    wrap.style.pointerEvents = 'none';      // 숨김 중 이벤트 히트테스트 차단
    toolPanel.style.display = 'none';
    btnTool.classList.remove('is-active');
    btnOut.classList.remove('is-active');
    try { localStorage.removeItem('usekit_float_visible'); } catch (e) {}
  }
  function toggleFloat() {
    const isOpen = wrap.style.display === 'flex';
    if (isOpen) hideFloat();
    else showFloat();
  }

  // 초기화 — 이전 상태 복원 (재시작 후에도 유지)
  try {
    if (localStorage.getItem('usekit_float_visible') === '1') {
      wrap.style.display = 'flex';
      wrap.style.pointerEvents = '';
    } else {
      wrap.style.pointerEvents = 'none';   // 숨김 상태 히트테스트 차단
    }
  } catch (e) {
    wrap.style.pointerEvents = 'none';
  }

  // ── 드래그 + 클릭 통합 ──
  let dragging = false, ox = 0, oy = 0, moved = false, _touchId = null;

  function onStart(cx, cy) {
    dragging = true; moved = false;
    const r = wrap.getBoundingClientRect();
    ox = cx - r.left; oy = cy - r.top;
  }
  function onMove(cx, cy) {
    if (!dragging) return;
    const dx = Math.abs(cx - (wrap.getBoundingClientRect().left + ox));
    const dy = Math.abs(cy - (wrap.getBoundingClientRect().top  + oy));
    if (dx > 8 || dy > 8) moved = true;
    if (!moved) return;
    // 가로 모드 진입 시 적용된 transform: translateX(-50%) 제거 (위치가 어긋나지 않도록)
    wrap.style.transform = 'none';
    // 컨테이너 폭은 가로 모드에서 가변이므로 boundingRect 사용
    const w = wrap.offsetWidth || 58;
    const h = wrap.offsetHeight || 150;
    wrap.style.left   = Math.max(0, Math.min(window.innerWidth  - w, cx - ox)) + 'px';
    wrap.style.top    = Math.max(0, Math.min(window.innerHeight - h, cy - oy)) + 'px';
    wrap.style.right  = 'auto';
    wrap.style.bottom = 'auto';
    toolPanel.style.display = 'none';
    btnTool.classList.remove('is-active');
  }
  function onEnd(target) {
    dragging = false;
    if (moved) {
      // 드래그로 이동한 경우 — 위치 저장
      try {
        const r = wrap.getBoundingClientRect();
        localStorage.setItem('usekit_float_pos', JSON.stringify({ left: r.left, top: r.top }));
      } catch (e) {}
      return;
    }
    const id = target?.id || target?.closest?.('[id]')?.id;
    if      (id === 'floatBtnRun'    || target?.closest?.('#floatBtnRun'))    { if (_cliMode) _doExecCli(); else _doExec(); }
    else if (id === 'floatBtnOutput' || target?.closest?.('#floatBtnOutput')) { _toggleOutput(); }
    else if (id === 'floatBtnTool'   || target?.closest?.('#floatBtnTool'))   { _toggleTool(); }
  }

  wrap.addEventListener('touchstart', e => {
    e.preventDefault();
    const t = e.touches[0]; _touchId = t.identifier;
    onStart(t.clientX, t.clientY);
  }, { passive: false });
  wrap.addEventListener('touchmove', e => {
    e.preventDefault();
    const t = [...e.touches].find(x => x.identifier === _touchId);
    if (t) onMove(t.clientX, t.clientY);
  }, { passive: false });
  wrap.addEventListener('touchend', e => {
    e.preventDefault();
    const t = [...e.changedTouches].find(x => x.identifier === _touchId);
    onEnd(document.elementFromPoint(t?.clientX ?? 0, t?.clientY ?? 0));
  }, { passive: false });

  wrap.addEventListener('mousedown',    e => { onStart(e.clientX, e.clientY); });
  document.addEventListener('mousemove', e => { if (dragging) onMove(e.clientX, e.clientY); });
  document.addEventListener('mouseup',   e => { if (dragging) onEnd(e.target); });

  // ── Tool 패널 버튼 ──

  // 그룹 아코디언 토글 — Run / Edit / Menu 공통 패턴
  // 열린 섹션은 강조색(#7BA8D9), 닫힌 섹션은 subdued(#94A3B8)
  const _TP_COLOR_ACTIVE  = '#7BA8D9';
  const _TP_COLOR_SUBDUED = '#94A3B8';

  function _updateTpGroupColor(toggleId, isOpen) {
    const btn = document.getElementById(toggleId);
    if (!btn) return;
    const color = isOpen ? _TP_COLOR_ACTIVE : _TP_COLOR_SUBDUED;
    btn.querySelectorAll('.tp-grp-chevron, .tp-grp-label').forEach(el => {
      el.style.color = color;
    });
    // arrow도 맞춤
    const arrow = btn.querySelector('[id$="Arrow"]');
    if (arrow) arrow.style.color = color;
  }

  function _bindTpGroupToggle(toggleId, sectionId, arrowId) {
    const storageKey = 'usekit_mtp_grp_' + sectionId;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) {
        const sec = document.getElementById(sectionId);
        const arrow = document.getElementById(arrowId);
        if (sec) {
          const isOpen = saved === 'open';
          sec.style.display = isOpen ? 'block' : 'none';
          if (arrow) arrow.textContent = isOpen ? '▴' : '▾';
          _updateTpGroupColor(toggleId, isOpen);
        }
      }
    } catch (e) {}
    document.getElementById(toggleId)?.addEventListener('click', () => {
      const sec = document.getElementById(sectionId);
      const arrow = document.getElementById(arrowId);
      if (!sec) return;
      const wasOpen = sec.style.display !== 'none';
      sec.style.display = wasOpen ? 'none' : 'block';
      if (arrow) arrow.textContent = wasOpen ? '▾' : '▴';
      _updateTpGroupColor(toggleId, !wasOpen);
      try { localStorage.setItem(storageKey, wasOpen ? 'closed' : 'open'); } catch (e) {}
    });
  }
  _bindTpGroupToggle('floatTpRunToggle',  'floatTpRunSection',  'floatTpRunArrow');
  _bindTpGroupToggle('floatTpEditToggle', 'floatTpEditSection', 'floatTpEditArrow');
  _bindTpGroupToggle('floatTpMenuToggle', 'floatTpMenuSection', 'floatTpMenuArrow');

  // Run 그룹 — 기존 동작 유지
  document.getElementById('floatTpRun')?.addEventListener('click', () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    if (_cliMode) { _doExecCli(); return; }
    // Show live ns indicator
    const dot = document.getElementById('floatTpLiveDot');
    if (dot) dot.style.display = 'inline';
    if (window.runLive) window.runLive();
    else _doExec();  // fallback
  });
  document.getElementById('floatTpPrint')?.addEventListener('click', () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    if (_cliMode) { _doExecCli(); return; }
    if (window.runPrint) window.runPrint();
    else console.warn('[Tool] runPrint not ready');
  });
  document.getElementById('floatTpLine')?.addEventListener('click', () => {
    if (_cliMode) { _doExecCli(); return; }
    // Line Run은 연타 사용이 주 패턴이라 메뉴 유지
    if (window.runLine) window.runLine();
    else console.warn('[Tool] runLine not ready');
  });
  document.getElementById('floatTpBlock')?.addEventListener('click', () => {
    if (_cliMode) { _doExecCli(); return; }
    // Current Block도 연타 사용 패턴이라 메뉴 유지
    if (window.runBlock) window.runBlock();
    else console.warn('[Tool] runBlock not ready');
  });
  document.getElementById('floatTpFileTmp')?.addEventListener('click', () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    if (_cliMode) { _doExecCli(); return; }
    _doExecFileTmp();
  });

  // ── Reset REPL ──────────────────────────────────────────────
  document.getElementById('floatTpResetRepl')?.addEventListener('click', async () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    // Hide live ns indicator
    const dot = document.getElementById('floatTpLiveDot');
    if (dot) dot.style.display = 'none';
    try {
      const res = await fetch('/api/reset_repl', { method: 'POST' });
      const d = await res.json();
      if (d.ok) {
        _appendOutput('RESET', { stdout: '✓ REPL namespace reset\n' });
      } else {
        _appendOutput('RESET', { error: 'Reset failed' });
      }
    } catch (e) {
      _appendOutput('RESET', { error: 'Reset failed: ' + e.message });
    }
  });

  // ── Edit 그룹 ─────────────────────────────────────────────
  //   공통: 선택 있으면 선택만, 없으면 전체 문서 대상
  //   팝업은 실행 후 닫음 (Copy Tool 패턴)
  // ────────────────────────────────────────────────────────────
  function _closeToolPanel() {
    toolPanel.style.display = 'none';
    btnTool.classList.remove('is-active');
  }

  // 현재 선택 범위 반환. 선택 없으면 전체 문서 범위.
  function _getEditRange(view) {
    const sel = view.state.selection.main;
    if (sel.from !== sel.to) return { from: sel.from, to: sel.to, hasSelection: true };
    return { from: 0, to: view.state.doc.length, hasSelection: false };
  }

  // Case transform — 순환 3단계: UPPER → lower → Title → UPPER...
  // 상태는 IIFE 변수로 유지 (다음 탭에서 다음 단계로)
  let _caseStage = 0; // 0=UPPER, 1=lower, 2=Title
  document.getElementById('floatTpCaseTransform')?.addEventListener('click', () => {
    _closeToolPanel();
    const view = window.Editor?.get?.();
    if (!view) return;
    const { from, to } = _getEditRange(view);
    if (from === to) return;
    const src = view.state.sliceDoc(from, to);
    let out;
    if (_caseStage === 0) {
      out = src.toUpperCase();
    } else if (_caseStage === 1) {
      out = src.toLowerCase();
    } else {
      // Title case: 각 단어의 첫 글자만 대문자 (공백/탭/줄바꿈 기준)
      out = src.toLowerCase().replace(/(^|\s)(\S)/g, (_, ws, ch) => ws + ch.toUpperCase());
    }
    _caseStage = (_caseStage + 1) % 3;
    if (out === src) return;
    view.dispatch({
      changes:   { from, to, insert: out },
      selection: { anchor: from, head: from + out.length },
      userEvent: 'input.replace',
    });
  });

  // Tab → Space — 탭 1개를 공백 4개로 변환
  document.getElementById('floatTpTabToSpace')?.addEventListener('click', () => {
    _closeToolPanel();
    const view = window.Editor?.get?.();
    if (!view) return;
    const { from, to } = _getEditRange(view);
    if (from === to) return;
    const src = view.state.sliceDoc(from, to);
    const tabSize = view.state.tabSize || 4;
    const spaces = ' '.repeat(tabSize);
    if (!src.includes('\t')) return;
    const out = src.replace(/\t/g, spaces);
    view.dispatch({
      changes:   { from, to, insert: out },
      selection: { anchor: from, head: from + out.length },
      userEvent: 'input.replace',
    });
  });

  // Trim trailing — 각 라인 끝 공백/탭 제거
  document.getElementById('floatTpTrimTrailing')?.addEventListener('click', () => {
    _closeToolPanel();
    const view = window.Editor?.get?.();
    if (!view) return;
    const { from, to } = _getEditRange(view);
    if (from === to) return;
    const src = view.state.sliceDoc(from, to);
    const out = src.replace(/[ \t]+$/gm, '');
    if (out === src) return;
    view.dispatch({
      changes:   { from, to, insert: out },
      selection: { anchor: from, head: from + out.length },
      userEvent: 'input.replace',
    });
  });

  // ── Layout 토글 (세로 ↔ 가로) ── 위치 유지
  function _setLayout(orientation, opts) {
    // orientation: 'vertical' | 'horizontal'
    // opts.preservePosition: true면 현재 pill 중심점을 기준으로 유지 (토글). false면 기본 위치로 배치 (초기 복원).
    const isHorizontal = orientation === 'horizontal';
    const preserve = opts?.preservePosition !== false;  // 기본 true

    // 전환 전 중심점 기록
    const preRect = wrap.getBoundingClientRect();
    const preCx = preRect.left + preRect.width  / 2;
    const preCy = preRect.top  + preRect.height / 2;
    const hadVisualPosition = preRect.width > 0;  // 현재 렌더돼있는지

    // 클래스 토글 (크기가 즉시 바뀜)
    wrap.classList.toggle('is-horizontal', isHorizontal);

    if (preserve && hadVisualPosition) {
      // 새 크기 측정
      const newW = wrap.offsetWidth;
      const newH = wrap.offsetHeight;
      // 기존 중심점을 새 중심점으로 맞추기
      let newLeft = preCx - newW / 2;
      let newTop  = preCy - newH / 2;
      // 화면 밖 클램프
      const margin = 6;
      newLeft = Math.max(margin, Math.min(window.innerWidth  - newW - margin, newLeft));
      newTop  = Math.max(margin, Math.min(window.innerHeight - newH - margin, newTop));
      wrap.style.transform = 'none';
      wrap.style.right  = 'auto';
      wrap.style.bottom = 'auto';
      wrap.style.left   = newLeft + 'px';
      wrap.style.top    = newTop  + 'px';
    } else {
      // 초기 복원 등 — 기본 위치
      if (isHorizontal) {
        wrap.style.right  = 'auto';
        wrap.style.left   = '50%';
        wrap.style.transform = 'translateX(-50%)';
        wrap.style.top    = '12px';
        wrap.style.bottom = 'auto';
      } else {
        wrap.style.left   = 'auto';
        wrap.style.transform = 'none';
        wrap.style.right  = '14px';
        wrap.style.top    = 'auto';
        wrap.style.bottom = '120px';
      }
    }

    // 라벨/아이콘 업데이트 — "다음 상태"를 표시 (탭하면 이리로 간다)
    const lbl = document.getElementById('floatTpLayoutLabel');
    const ico = document.getElementById('floatTpLayoutIcon');
    if (lbl) lbl.textContent = isHorizontal ? 'Vertical' : 'Horizontal';
    if (ico) ico.textContent = isHorizontal ? '▤' : '▦';
    try { localStorage.setItem('usekit_float_layout', orientation); } catch (e) {}
  }
  // 초기값 복원 (기본 위치 사용)
  try {
    const saved = localStorage.getItem('usekit_float_layout');
    if (saved === 'horizontal') _setLayout('horizontal', { preservePosition: false });
  } catch (e) {}

  // ── 위치 복원 (레이아웃 복원 직후) ──
  //   저장된 좌표가 있으면 적용하되 화면 밖이면 클램프.
  //   회전/창 크기 변경 케이스 대응.
  try {
    const raw = localStorage.getItem('usekit_float_pos');
    if (raw) {
      const pos = JSON.parse(raw);
      if (pos && typeof pos.left === 'number' && typeof pos.top === 'number') {
        const w = wrap.offsetWidth  || 58;
        const h = wrap.offsetHeight || 150;
        const margin = 6;
        const left = Math.max(margin, Math.min(window.innerWidth  - w - margin, pos.left));
        const top  = Math.max(margin, Math.min(window.innerHeight - h - margin, pos.top));
        wrap.style.transform = 'none';
        wrap.style.right  = 'auto';
        wrap.style.bottom = 'auto';
        wrap.style.left   = left + 'px';
        wrap.style.top    = top  + 'px';
      }
    }
  } catch (e) {}

  document.getElementById('floatTpLayout')?.addEventListener('click', () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    const next = wrap.classList.contains('is-horizontal') ? 'vertical' : 'horizontal';
    _setLayout(next);  // 기본 preserve=true
    // 레이아웃 전환 후 새 위치 저장
    try {
      const r = wrap.getBoundingClientRect();
      localStorage.setItem('usekit_float_pos', JSON.stringify({ left: r.left, top: r.top }));
    } catch (e) {}
  });
  // ── edit 모드: 패널을 editor-section 안으로 인라인 (SQL 뷰 패턴) ──
  let _runEditActive = false;
  let _runVvHandler = null;

  function _updateRunEditHeight() {
    const inner = document.getElementById('runPanelInner');
    if (!inner || !_runEditActive) return;
    const vv = window.visualViewport;
    const screenH = window.screen.height || window.innerHeight;
    const viewH = vv ? vv.height : window.innerHeight;
    const kbOpen = (screenH - viewH) > 150;
    if (kbOpen) {
      inner.style.height = '70px';
      inner.style.maxHeight = '70px';
    } else {
      inner.style.height = '45vh';
      inner.style.maxHeight = '400px';
    }
  }

  function _enterRunEditMode() {
    const panel = document.getElementById('runPanel');
    const inner = document.getElementById('runPanelInner');
    const section = document.querySelector('.editor-section');
    const host = document.getElementById('editor-host');
    const btn = document.getElementById('btnRunEdit');
    if (!panel || !inner || !section) return;

    _runEditActive = true;

    // overlay 숨김
    panel.classList.remove('is-open');

    if (host) host.style.flex = '1 1 0';
    // 패널: 고정 높이, grow 없음
    inner.style.flex = '0 0 auto';
    inner.style.overflow = 'hidden';
    inner.style.borderRadius = '0';
    inner.style.borderTop = '2px solid #4caf50';
    inner.style.boxShadow = '0 -4px 12px rgba(0,0,0,0.15)';
    section.appendChild(inner);

    // 초기 높이 + 키보드 감시
    _updateRunEditHeight();
    _runVvHandler = _updateRunEditHeight;
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', _runVvHandler);
    }

    if (btn) { btn.textContent = 'edit ●'; btn.classList.add('is-active'); }

    // 미니 실행 패널 표시
    _showMiniRun();
  }

  // ── 미니 실행 패널 (edit 모드 전용) ──
  let _miniRunEl = null;
  let _miniCollapsed = false;
  let _miniPos = { x: -1, y: -1 };  // 세션 내 위치 기억

  function _showMiniRun() {
    if (_miniRunEl) return;

    const el = document.createElement('div');
    el.id = 'miniRunPanel';
    el.style.cssText = `
      position:fixed; z-index:10000;
      background:rgba(30,34,42,0.92); border:1px solid rgba(76,175,80,0.5);
      border-radius:8px; box-shadow:0 2px 12px rgba(0,0,0,0.35);
      padding:0; user-select:none; touch-action:none;
      font-family:-apple-system,sans-serif; font-size:13px;
      backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
    `;

    // 헤더 (드래그 핸들 + 접기)
    const hdr = document.createElement('div');
    hdr.style.cssText = `
      display:flex; align-items:center; justify-content:space-between;
      padding:5px 8px; cursor:grab;
      border-bottom:1px solid rgba(255,255,255,0.08);
      color:rgba(255,255,255,0.5); font-size:10px; font-weight:600;
      letter-spacing:0.05em;
    `;
    hdr.textContent = 'RUN';

    const foldBtn = document.createElement('span');
    foldBtn.textContent = '▾';
    foldBtn.style.cssText = 'cursor:pointer; font-size:12px; padding:0 4px; color:rgba(255,255,255,0.4);';
    hdr.appendChild(foldBtn);
    el.appendChild(hdr);

    // 버튼 영역
    const body = document.createElement('div');
    body.className = 'minirun-body';
    body.style.cssText = 'display:flex; gap:2px; padding:4px 6px;';

    const mkBtn = (icon, label, color, fn) => {
      const b = document.createElement('button');
      b.innerHTML = `<span style="font-size:11px;">${icon}</span> ${label}`;
      b.style.cssText = `
        flex:1; padding:6px 4px; border:none; border-radius:5px;
        background:rgba(255,255,255,0.06); color:${color};
        font-size:11px; font-weight:500; cursor:pointer;
        white-space:nowrap;
      `;
      b.addEventListener('touchend', e => { e.preventDefault(); e.stopPropagation(); fn(); });
      b.addEventListener('mouseup', e => { e.stopPropagation(); fn(); });
      return b;
    };

    body.appendChild(mkBtn('▶', 'Run', '#7ee787', () => { if (_cliMode) _doExecCli(); else _doExec(); }));
    body.appendChild(mkBtn('~', 'Line', '#79c0ff', () => { if (_cliMode) _doExecCli(); else if (window.runLine) window.runLine(); }));
    body.appendChild(mkBtn('◻', 'Block', '#d2a8ff', () => { if (_cliMode) _doExecCli(); else if (window.runBlock) window.runBlock(); }));
    el.appendChild(body);

    // 접힌 상태 캡션
    const cap = document.createElement('div');
    cap.className = 'minirun-cap';
    cap.innerHTML = '<span style="color:#7ee787;">▶</span> <span style="color:#79c0ff;">~</span> <span style="color:#d2a8ff;">◻</span>';
    cap.style.cssText = `
      display:none; padding:6px 10px; cursor:pointer;
      font-size:13px; letter-spacing:4px; text-align:center;
    `;
    el.appendChild(cap);

    // 접기/펼치기
    const toggleFold = () => {
      _miniCollapsed = !_miniCollapsed;
      body.style.display = _miniCollapsed ? 'none' : 'flex';
      cap.style.display = _miniCollapsed ? 'block' : 'none';
      hdr.style.borderBottom = _miniCollapsed ? 'none' : '1px solid rgba(255,255,255,0.08)';
      foldBtn.textContent = _miniCollapsed ? '▸' : '▾';
    };
    foldBtn.addEventListener('click', e => { e.stopPropagation(); toggleFold(); });
    cap.addEventListener('click', e => { e.stopPropagation(); toggleFold(); });

    // 드래그
    let dragging = false, dx = 0, dy = 0;
    const onStart = (cx, cy) => { dragging = true; const r = el.getBoundingClientRect(); dx = cx - r.left; dy = cy - r.top; hdr.style.cursor = 'grabbing'; };
    const onMove = (cx, cy) => { if (!dragging) return; el.style.left = (cx - dx) + 'px'; el.style.top = (cy - dy) + 'px'; el.style.right = 'auto'; el.style.bottom = 'auto'; };
    const onEnd = () => { if (!dragging) return; dragging = false; hdr.style.cursor = 'grab'; const r = el.getBoundingClientRect(); _miniPos = { x: r.left, y: r.top }; };
    hdr.addEventListener('touchstart', e => { e.preventDefault(); const t = e.touches[0]; onStart(t.clientX, t.clientY); }, { passive: false });
    document.addEventListener('touchmove', e => { if (!dragging) return; const t = e.touches[0]; onMove(t.clientX, t.clientY); }, { passive: true });
    document.addEventListener('touchend', () => onEnd());
    hdr.addEventListener('mousedown', e => { e.preventDefault(); onStart(e.clientX, e.clientY); });
    document.addEventListener('mousemove', e => onMove(e.clientX, e.clientY));
    document.addEventListener('mouseup', () => onEnd());

    document.body.appendChild(el);
    _miniRunEl = el;

    // 위치 설정
    if (_miniPos.x >= 0) {
      el.style.left = _miniPos.x + 'px';
      el.style.top = _miniPos.y + 'px';
    } else {
      // 기본: output 헤더 우측 위
      el.style.right = '12px';
      el.style.bottom = '50%';
    }
  }

  function _hideMiniRun() {
    if (_miniRunEl) {
      _miniRunEl.remove();
      _miniRunEl = null;
    }
  }

  function _exitRunEditMode(reopenPanel = true) {
    if (!_runEditActive) return;
    const panel = document.getElementById('runPanel');
    const inner = document.getElementById('runPanelInner');
    const host = document.getElementById('editor-host');
    const btn = document.getElementById('btnRunEdit');
    if (!panel || !inner) return;

    _runEditActive = false;

    if (_runVvHandler && window.visualViewport) {
      window.visualViewport.removeEventListener('resize', _runVvHandler);
      _runVvHandler = null;
    }

    // edit 모드에서 추가한 inline style 전부 제거
    inner.style.flex = '';
    inner.style.minHeight = '';
    inner.style.maxHeight = '';
    inner.style.height = '';
    inner.style.overflow = '';
    inner.style.borderRadius = '';
    inner.style.borderTop = '';
    inner.style.boxShadow = '';
    inner.style.order = '';

    // inner를 다시 runPanel(overlay) 안으로 복귀
    panel.appendChild(inner);
    if (reopenPanel) panel.classList.add('is-open');

    // editor-host 복원
    if (host) { host.style.flex = ''; host.style.minHeight = ''; }
    if (btn) { btn.textContent = 'edit'; btn.classList.remove('is-active'); }

    // 미니 실행 패널 제거
    _hideMiniRun();
  }

  // ── Output clear / close / edit / copy ──
  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btnRunEdit')?.addEventListener('click', () => {
      if (_runEditActive) _exitRunEditMode();
      else _enterRunEditMode();
    });
    document.getElementById('btnRunCopy')?.addEventListener('click', () => {
      const o = document.getElementById('runOutput');
      if (!o) return;
      const text = o.innerText || o.textContent || '';
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(text).catch(() => {});
      }
    });
    document.getElementById('btnRunClear')?.addEventListener('click', () => {
      const o = document.getElementById('runOutput');
      if (o) o.innerHTML = '';
    });
    document.getElementById('btnRunClose')?.addEventListener('click', () => {
      if (_runEditActive) _exitRunEditMode(false);  // close이므로 overlay 재오픈 안 함
      const p = document.getElementById('runPanel');
      if (p) p.classList.remove('is-open');
      btnOut.classList.remove('is-active');
    });
  });

  // ── 에디터 영역 클릭 시 output overlay 닫기 (edit 모드가 아닐 때만) ──
  document.addEventListener('DOMContentLoaded', () => {
    const host = document.getElementById('editor-host');
    if (host) {
      host.addEventListener('mousedown', () => {
        if (_runEditActive) return;
        const p = document.getElementById('runPanel');
        if (p && p.classList.contains('is-open')) {
          p.classList.remove('is-open');
          btnOut.classList.remove('is-active');
        }
      });
      host.addEventListener('touchstart', () => {
        if (_runEditActive) return;
        const p = document.getElementById('runPanel');
        if (p && p.classList.contains('is-open')) {
          p.classList.remove('is-open');
          btnOut.classList.remove('is-active');
        }
      }, { passive: true });
    }
  });

  document.getElementById('floatTpHide')?.addEventListener('click', () => {
    hideFloat();
  });

  // Menu → Menu: 자기 Hide + Menu pill(허브) 표시
  document.getElementById('floatTpMenuHub')?.addEventListener('click', () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    hideFloat();
    if (window.MenuView?.show) window.MenuView.show();
  });

  // Help → Python Help 모달 오픈
  document.getElementById('floatTpHelp')?.addEventListener('click', () => {
    toolPanel.style.display = 'none'; btnTool.classList.remove('is-active');
    const modal = document.getElementById('pyHelpModal');
    if (modal) { modal.style.display = 'flex'; modal.setAttribute('aria-hidden', 'false'); }
  });

  // Python Help 모달 닫기
  const _pyHelpClose = () => {
    const modal = document.getElementById('pyHelpModal');
    if (modal) { modal.style.display = 'none'; modal.setAttribute('aria-hidden', 'true'); }
  };
  document.getElementById('btnPyHelpClose')?.addEventListener('click', _pyHelpClose);
  document.getElementById('btnPyHelpOk')?.addEventListener('click', _pyHelpClose);
  document.getElementById('pyHelpModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'pyHelpModal') _pyHelpClose();
  });

  // ── 외부 클릭 시 Tool 패널 닫기 ──
  document.addEventListener('click', e => {
    if (!wrap.contains(e.target) && !toolPanel.contains(e.target)) {
      toolPanel.style.display = 'none';
      btnTool.classList.remove('is-active');
    }
  });
  // ESC로 TOOL 메뉴 닫기 (메뉴 열린 상태일 때만 가로채서 다른 ESC 동작과 충돌 방지)
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    const isOpen = toolPanel.style.display && toolPanel.style.display !== 'none';
    if (!isOpen) return;
    e.preventDefault();
    e.stopPropagation();
    toolPanel.style.display = 'none';
    btnTool.classList.remove('is-active');
  }, true);  // capture phase: 다른 에디터 ESC 핸들러보다 먼저 받도록

  // ── CLI 모드 ─────────────────────────────────────────────────
  let _cliMode = false;
  let _cliHistory = [];
  let _cliHistIdx = -1;

  function _enterCliMode() {
    _cliMode = true;
    const badge = document.getElementById('cliBadge');
    if (badge) badge.style.display = 'block';
    const label = document.getElementById('floatTpCliLabel');
    if (label) label.textContent = 'CLI ●';
  }

  function _exitCliMode() {
    _cliMode = false;
    const badge = document.getElementById('cliBadge');
    if (badge) badge.style.display = 'none';
    const label = document.getElementById('floatTpCliLabel');
    if (label) label.textContent = 'CLI';
  }
  let _cliPrevContent = null;

  function _toggleCliMode() {
    if (_cliMode) _exitCliMode();
    else _enterCliMode();
  }

  // CLI 모드 실행: 커서 줄 ~ 마지막 줄을 묶어서 cli 모드로 /api/exec 전송
  function _doExecCli() {
    const view = window.Editor?.get?.();
    if (!view) return;

    // 커서가 있는 줄 번호 (1-based)
    const cursorPos = view.state.selection.main.head;
    const cursorLine = view.state.doc.lineAt(cursorPos).number;
    const totalLines = view.state.doc.lines;

    // 커서 줄부터 마지막 줄까지 추출, 빈 줄 스킵
    const lines = [];
    for (let i = cursorLine; i <= totalLines; i++) {
      const lineText = view.state.doc.line(i).text;
      if (lineText.trim()) lines.push(lineText);
    }
    if (!lines.length) return;

    const code = lines.join('\n');

    // 히스토리 추가
    if (!_cliHistory.length || _cliHistory[_cliHistory.length - 1] !== code) {
      _cliHistory.push(code);
    }
    _cliHistIdx = _cliHistory.length;

    if (!_runEditActive) { try { window.UIViewport?.blockKeyboard?.(); } catch (e) {} }
    const bodyEl = _appendOutput('CLI', { running: true });
    fetch('/api/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, mode: 'cli', inputs: [], timeout: 15 }),
    })
    .then(r => r.json())
    .catch(() => ({ ok: false, error: 'network_error', stdout: '', stderr: '' }))
    .then(d => {
      if (!bodyEl) return;
      const esc = s => s
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/\x1b\[[0-9;]*m/g,'')
        .replace(/\n/g,'<br>');
      let html = '';
      if (d.stdout) html += `<span style="color:#c9d1d9;">${esc(_fmtStdout(d.stdout))}</span>`;
      if (d.stderr) html += `<span style="color:#f97583;">${esc(d.stderr)}</span>`;
      if (d.error && !d.ok) html += `<span style="color:#ff7b72;">[ERROR] ${esc(d.error)}</span>`;
      if (!html) html = '<span style="opacity:0.35;">(no output)</span>';
      bodyEl.innerHTML = html;
      const output = document.getElementById('runOutput');
      if (output) output.scrollTop = output.scrollHeight;

      // 마지막 줄이 비어있지 않을 때만 새 줄 추가 + 커서 이동
      const doc = view.state.doc;
      const lastLine = doc.line(doc.lines);
      if (lastLine.text.trim()) {
        const docLen = doc.length;
        view.dispatch({
          changes: { from: docLen, insert: '\n' },
          selection: { anchor: docLen + 1 },
        });
      } else {
        // 이미 빈 줄이면 커서만 끝으로
        view.dispatch({ selection: { anchor: doc.length } });
      }
    });
  }

  // CLI 히스토리 탐색 (방향키)
  document.addEventListener('keydown', e => {
    if (!_cliMode) return;
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      if (!_cliHistory.length) return;
      e.preventDefault();
      if (e.key === 'ArrowUp') {
        _cliHistIdx = Math.max(0, _cliHistIdx - 1);
      } else {
        _cliHistIdx = Math.min(_cliHistory.length, _cliHistIdx + 1);
      }
      const val = _cliHistIdx < _cliHistory.length ? _cliHistory[_cliHistIdx] : '';
      window.Editor?.setText?.(val);
    }
  });

  // CLI 탭 클릭
  document.getElementById('floatTpCli')?.addEventListener('click', () => {
    _closeToolPanel();
    _toggleCliMode();
  });

  // RUN 버튼 동작 분기 — CLI 모드에서는 _doExecCli 호출
  // _doExec를 래핑
  const _origDoExec = _doExec;
  function _doExecRouted() {
    if (_cliMode) { _doExecCli(); return; }
    _origDoExec();
  }

  // 글로벌 접근점 — 퀵도구 Shift+CTRL+TAB 등에서 사용
  window.RunView = {
    toggle: toggleFloat,
    get editModeActive() { return _runEditActive; },
    exitEditMode: _exitRunEditMode,
    execFileTmp: _doExecFileTmp,
    get cliMode() { return _cliMode; },
    toggleCli: _toggleCliMode,
  };
})();
