// float_menu.js — Menu pill logic (extracted from index.html)
(function() {
  const pill = document.getElementById('floatMenuTool');
  const panel = document.getElementById('floatMenuToolPanel');
  const btnMenu = document.getElementById('floatBtnMenu');
  if (!pill || !panel) return;

  // ────────────────────────────────
  // 표시/숨김
  // ────────────────────────────────
  function showMenuFloat() {
    pill.style.display = 'flex';
    pill.style.pointerEvents = '';
    panel.style.display = 'none';
    try { localStorage.setItem('usekit_menu_float_visible', '1'); } catch (e) {}
  }
  function hideMenuFloat() {
    pill.style.display = 'none';
    pill.style.pointerEvents = 'none';
    panel.style.display = 'none';
    try { localStorage.removeItem('usekit_menu_float_visible'); } catch (e) {}
  }
  function toggleMenuFloat() {
    const isOpen = pill.style.display === 'flex';
    if (isOpen) hideMenuFloat();
    else showMenuFloat();
  }

  // 초기 복원
  try {
    if (localStorage.getItem('usekit_menu_float_visible') === '1') {
      pill.style.display = 'flex';
      pill.style.pointerEvents = '';
    } else {
      pill.style.pointerEvents = 'none';
    }
  } catch (e) {
    pill.style.pointerEvents = 'none';
  }

  // ────────────────────────────────
  // 팝업 위치 — 단일 버튼이라 vertical 로직만 (좌/우 attach)
  // ────────────────────────────────
  function _positionPanel() {
    if (!panel) return;
    const r = pill.getBoundingClientRect();
    const margin = 8;
    const panelW = panel.offsetWidth  || 170;
    const panelH = panel.offsetHeight || 240;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const pillCx = r.left + r.width / 2;
    const pillCy = r.top  + r.height / 2;

    const pillOnLeftHalf = pillCx < vw / 2;
    if (pillOnLeftHalf) {
      let leftVal = r.right + 10;
      leftVal = Math.max(margin, Math.min(vw - panelW - margin, leftVal));
      panel.style.left  = leftVal + 'px';
      panel.style.right = 'auto';
    } else {
      let rightVal = vw - r.left + 10;
      rightVal = Math.max(margin, Math.min(vw - panelW - margin, rightVal));
      panel.style.right = rightVal + 'px';
      panel.style.left  = 'auto';
    }
    let topVal = pillCy - panelH / 2;
    topVal = Math.max(margin, Math.min(vh - panelH - margin, topVal));
    panel.style.top    = topVal + 'px';
    panel.style.bottom = 'auto';
  }

  function _togglePanel() {
    const show = panel.style.display === 'none' || panel.style.display === '';
    if (show) {
      _positionPanel();
      _syncFloatStates();  // Floats 상태 동기화
    }
    panel.style.display = show ? 'flex' : 'none';
    btnMenu.classList.toggle('is-active', show);
    if (show) requestAnimationFrame(_positionPanel);
  }
  function _closePanel() {
    panel.style.display = 'none';
    btnMenu.classList.remove('is-active');
  }

  // ────────────────────────────────
  // Floats 그룹 — 다른 pill 상태 읽기/토글
  // ────────────────────────────────
  function _isPillVisible(id) {
    const el = document.getElementById(id);
    return el && el.style.display === 'flex';
  }
  function _syncFloatStates() {
    const map = [
      ['floatMtpRunPill',  'floatRunTool'],
      ['floatMtpSqlPill',  'floatSqlTool'],
      ['floatMtpCopyPill', 'floatClipTool'],
    ];
    for (const [btnId, pillId] of map) {
      const btn = document.getElementById(btnId);
      if (btn) btn.classList.toggle('is-active', _isPillVisible(pillId));
    }
  }

  // 각 pill 토글 — 해당 pill 각자의 API 사용 (없으면 display 직접)
  function _toggleRunPill() {
    const el = document.getElementById('floatRunTool');
    if (!el) return;
    const isOpen = el.style.display === 'flex';
    if (isOpen) {
      el.style.display = 'none';
      el.style.pointerEvents = 'none';
      const tp = document.getElementById('floatToolPanel');
      if (tp) tp.style.display = 'none';
      try { localStorage.removeItem('usekit_float_visible'); } catch (e) {}
    } else {
      el.style.display = 'flex';
      el.style.pointerEvents = '';
      try { localStorage.setItem('usekit_float_visible', '1'); } catch (e) {}
    }
  }
  function _toggleSqlPill() {
    if (window.SqlView?.toggle) { window.SqlView.toggle(); return; }
    const el = document.getElementById('floatSqlTool');
    if (!el) return;
    const isOpen = el.style.display === 'flex';
    el.style.display = isOpen ? 'none' : 'flex';
    el.style.pointerEvents = isOpen ? 'none' : '';
  }
  function _toggleCopyPill() {
    if (window.ClipView?.toggle) { window.ClipView.toggle(); return; }
    const el = document.getElementById('floatClipTool');
    if (!el) return;
    const isOpen = el.style.display === 'flex';
    el.style.display = isOpen ? 'none' : 'flex';
    el.style.pointerEvents = isOpen ? 'none' : '';
  }

  // Floats 버튼 바인딩 — 탭 후 패널 유지(상태 동기화만)해서 연속 조작 가능
  document.getElementById('floatMtpRunPill') ?.addEventListener('click', () => { _toggleRunPill();  _syncFloatStates(); });
  document.getElementById('floatMtpSqlPill') ?.addEventListener('click', () => { _toggleSqlPill();  _syncFloatStates(); });
  document.getElementById('floatMtpCopyPill')?.addEventListener('click', () => { _toggleCopyPill(); _syncFloatStates(); });

  // ────────────────────────────────
  // 드래그 + 클릭
  // ────────────────────────────────
  let dragging = false, ox = 0, oy = 0, moved = false, _touchId = null;
  function onStart(cx, cy) {
    dragging = true; moved = false;
    const r = pill.getBoundingClientRect();
    ox = cx - r.left; oy = cy - r.top;
  }
  function onMove(cx, cy) {
    if (!dragging) return;
    const r = pill.getBoundingClientRect();
    if (Math.abs(cx - (r.left + ox)) > 8 || Math.abs(cy - (r.top + oy)) > 8) moved = true;
    if (!moved) return;
    pill.style.transform = 'none';
    const w = pill.offsetWidth || 40;
    const h = pill.offsetHeight || 40;
    pill.style.left   = Math.max(0, Math.min(window.innerWidth  - w, cx - ox)) + 'px';
    pill.style.top    = Math.max(0, Math.min(window.innerHeight - h, cy - oy)) + 'px';
    pill.style.right  = 'auto';
    pill.style.bottom = 'auto';
    panel.style.display = 'none';
    btnMenu.classList.remove('is-active');
  }
  function onEnd(target) {
    dragging = false;
    if (moved) {
      try {
        const r = pill.getBoundingClientRect();
        localStorage.setItem('usekit_menu_float_pos', JSON.stringify({ left: r.left, top: r.top }));
      } catch (e) {}
      return;
    }
    const id = target?.id || target?.closest?.('[id]')?.id;
    if (id === 'floatBtnMenu' || target?.closest?.('#floatBtnMenu')) _togglePanel();
  }

  pill.addEventListener('touchstart', e => {
    e.preventDefault();
    const t = e.touches[0]; _touchId = t.identifier;
    onStart(t.clientX, t.clientY);
  }, { passive: false });
  pill.addEventListener('touchmove', e => {
    e.preventDefault();
    const t = [...e.touches].find(x => x.identifier === _touchId);
    if (t) onMove(t.clientX, t.clientY);
  }, { passive: false });
  pill.addEventListener('touchend', e => {
    e.preventDefault();
    const t = [...e.changedTouches].find(x => x.identifier === _touchId);
    onEnd(document.elementFromPoint(t?.clientX ?? 0, t?.clientY ?? 0));
  }, { passive: false });
  pill.addEventListener('mousedown',    e => { onStart(e.clientX, e.clientY); });
  document.addEventListener('mousemove', e => { if (dragging) onMove(e.clientX, e.clientY); });
  document.addEventListener('mouseup',   e => { if (dragging) onEnd(e.target); });

  // ────────────────────────────────
  // This 그룹 (자기 Horizontal / Hide)
  // ────────────────────────────────
  function _bindMtpGroupToggle(toggleId, sectionId, arrowId) {
    const storageKey = 'usekit_mtp_grp_' + sectionId;
    // 저장된 상태 복원
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) {
        const sec = document.getElementById(sectionId);
        const arrow = document.getElementById(arrowId);
        if (sec) {
          sec.style.display = saved === 'open' ? 'block' : 'none';
          if (arrow) arrow.textContent = saved === 'open' ? '▴' : '▾';
        }
      }
    } catch (e) {}
    // 클릭 토글 + 저장
    document.getElementById(toggleId)?.addEventListener('click', () => {
      const sec = document.getElementById(sectionId);
      const arrow = document.getElementById(arrowId);
      if (!sec) return;
      const open = sec.style.display !== 'none';
      sec.style.display = open ? 'none' : 'block';
      if (arrow) arrow.textContent = open ? '▾' : '▴';
      try { localStorage.setItem(storageKey, open ? 'closed' : 'open'); } catch (e) {}
    });
  }
  _bindMtpGroupToggle('floatMtpFloatsToggle', 'floatMtpFloatsSection', 'floatMtpFloatsArrow');
  _bindMtpGroupToggle('floatMtpSelfToggle',   'floatMtpSelfSection',   'floatMtpSelfArrow');
  _bindMtpGroupToggle('floatMtpAlignToggle',  'floatMtpAlignSection',  'floatMtpAlignArrow');

  // ────────────────────────────────────────────────────────────
  // 일괄 정렬 (Align 그룹)
  // ────────────────────────────────────────────────────────────
  // 타겟 3 pill:
  //   파랑(Run)  — 기준점에서 가장 멀리  (prio 0)
  //   노랑(Sql)  — 중간                  (prio 1)
  //   녹색(Clip) — 기준점에 가장 가까이  (prio 2)
  // 기준점: 우측 상단 끝 (헤더 아래)
  // 가로 정렬: 우측 상단에서 왼쪽으로 녹색→노랑→파랑 (화면상 파랑 | 노랑 | 녹색)
  // 세로 정렬: 우측 상단에서 아래로 파랑→노랑→녹색   (키보드 덮여도 녹색 살아있음)
  // 각 pill의 localStorage 위치/레이아웃을 직접 갱신 → 새로고침 후 상태 유지
  // MENU pill은 별도 앵커라 건드리지 않음
  const _ALIGN_TARGETS = [
    { id: 'floatRunTool',  prio: 0, posKey: 'usekit_float_pos',      layoutKey: 'usekit_float_layout',      visKey: 'usekit_float_visible',      panelId: 'floatToolPanel'     },
    { id: 'floatSqlTool',  prio: 1, posKey: 'usekit_sql_float_pos',  layoutKey: 'usekit_sql_float_layout',  visKey: 'usekit_sql_float_visible',  panelId: 'floatSqlToolPanel'  },
    { id: 'floatClipTool', prio: 2, posKey: 'usekit_clip_float_pos', layoutKey: 'usekit_clip_float_layout', visKey: 'usekit_clip_float_visible', panelId: 'floatClipToolPanel' },
  ];
  const _ALIGN_GAP    = 6;
  const _ALIGN_MARGIN = 4;

  function _isPillShown(id) {
    const el = document.getElementById(id);
    return !!(el && el.style.display === 'flex');
  }
  function _setPillOrientation(id, isHorizontal) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('is-horizontal', isHorizontal);
  }
  function _placePill(id, left, top, posKey) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.transform = 'none';
    el.style.right  = 'auto';
    el.style.bottom = 'auto';
    el.style.left   = left + 'px';
    el.style.top    = top  + 'px';
    try { localStorage.setItem(posKey, JSON.stringify({ left, top })); } catch (e) {}
  }

  function _alignAll(orientation) {
    const isHorizontal = orientation === 'horizontal';

    // 1) 모양(orientation) 통일 + layoutKey 저장
    for (const t of _ALIGN_TARGETS) {
      _setPillOrientation(t.id, isHorizontal);
      try { localStorage.setItem(t.layoutKey, orientation); } catch (e) {}
    }

    // 2) 크기는 클래스 토글 직후에 재측정되어야 함 → 강제 reflow 후 계산
    //    (브라우저가 layout flush를 할 기회를 줌)
    void document.body.offsetHeight;

    // 기준점: 우측 상단 (헤더를 오버레이로 침범)
    const topY   = _ALIGN_MARGIN;
    const rightX = window.innerWidth - _ALIGN_MARGIN;

    // 3) 켜진 pill만 우선순위 오름차순 (파랑→노랑→녹색)으로 수집
    const visible = _ALIGN_TARGETS
      .filter(t => _isPillShown(t.id))
      .sort((a, b) => a.prio - b.prio);

    if (visible.length === 0) return;

    if (isHorizontal) {
      // 우측 끝에서 왼쪽으로. 녹색(prio 2)부터 우측에 붙임 → 파랑(prio 0)이 가장 왼쪽
      let cursorRight = rightX;
      for (const t of [...visible].reverse()) {
        const el = document.getElementById(t.id);
        if (!el) continue;
        const w = el.offsetWidth || 40;
        const left = cursorRight - w;
        _placePill(t.id, left, topY, t.posKey);
        cursorRight = left - _ALIGN_GAP;
      }
    } else {
      // 우측 상단에서 아래로. 파랑(prio 0) 맨 위, 녹색(prio 2) 맨 아래
      let cursorTop = topY;
      for (const t of visible) {
        const el = document.getElementById(t.id);
        if (!el) continue;
        const w = el.offsetWidth  || 40;
        const h = el.offsetHeight || 40;
        const left = rightX - w;
        _placePill(t.id, left, cursorTop, t.posKey);
        cursorTop += (h + _ALIGN_GAP);
      }
    }
  }

  function _showAllPills() {
    for (const t of _ALIGN_TARGETS) {
      const el = document.getElementById(t.id);
      if (!el) continue;
      el.style.display = 'flex';
      el.style.pointerEvents = '';
      try { localStorage.setItem(t.visKey, '1'); } catch (e) {}
    }
    _alignAll('horizontal');  // 기본 가로 정렬 = 가장 효율적 공간 배치
  }
  function _hideAllPills() {
    for (const t of _ALIGN_TARGETS) {
      const el = document.getElementById(t.id);
      if (el) {
        el.style.display = 'none';
        el.style.pointerEvents = 'none';
      }
      if (t.panelId) {
        const p = document.getElementById(t.panelId);
        if (p) p.style.display = 'none';
      }
      try { localStorage.removeItem(t.visKey); } catch (e) {}
    }
  }

  document.getElementById('floatMtpAlignHorizontal')?.addEventListener('click', () => {
    _alignAll('horizontal');
    _syncFloatStates();
    _closePanel();
  });
  document.getElementById('floatMtpAlignVertical')?.addEventListener('click', () => {
    _alignAll('vertical');
    _syncFloatStates();
    _closePanel();
  });
  document.getElementById('floatMtpAlignShowAll')?.addEventListener('click', () => {
    _showAllPills();
    _syncFloatStates();
    _closePanel();
  });
  document.getElementById('floatMtpAlignHideAll')?.addEventListener('click', () => {
    _hideAllPills();
    _syncFloatStates();
    _closePanel();
  });

  document.getElementById('floatMtpHide')?.addEventListener('click', () => {
    _closePanel();
    hideMenuFloat();
  });

  // Dock Block Off — OFF 버튼을 MENU 도킹 위치로 이동
  document.getElementById('floatMtpDockOff')?.addEventListener('click', () => {
    _closePanel();
    const offPill = document.getElementById('floatBlkTool');
    if (offPill) {
      const w = offPill.offsetWidth || 34;
      const h = offPill.offsetHeight || 34;
      const left = window.innerWidth - w - 6;
      const top  = window.innerHeight - h;
      offPill.style.transform = 'none';
      offPill.style.right = 'auto'; offPill.style.bottom = 'auto';
      offPill.style.left = left + 'px'; offPill.style.top = top + 'px';
      try { localStorage.setItem('usekit_blk_float_pos', JSON.stringify({ left, top })); } catch (e) {}
    }
  });

  // Keyboard — 가상 키패드 토글 (localStorage 기반)
  // usekit_kp_on: '1' = 키패드 모드, 없음 = 키패드 꺼짐

  function _kpIsWanted() {
    try { return localStorage.getItem('usekit_kp_on') === '1'; } catch(e) { return false; }
  }

  function _kpTurnOn() {
    try { localStorage.setItem('usekit_kp_on', '1'); } catch(e) {}
    const app = document.querySelector('.editor-app');
    const np = document.querySelector('.swipe-panel.panel-navigation');
    if (app && np) {
      document.querySelectorAll('.swipe-panel').forEach(p => p.classList.remove('active'));
      np.classList.add('active');
      app.classList.remove('nav-hidden');
    }
    window._sysKbMode = true;
    window.UIKeypad.show();
    window.UI?.recalcHeight?.();
  }

  function _kpTurnOff() {
    try { localStorage.removeItem('usekit_kp_on'); } catch(e) {}
    window._sysKbMode = false;
    window.UIKeypad.hide();
    const np = document.querySelector('.swipe-panel.panel-navigation');
    if (np) np.classList.remove('active');
    window.UI?.recalcHeight?.();
  }

  document.getElementById('floatMtpKeyboard')?.addEventListener('click', () => {
    _closePanel();
    // 판단: panel-navigation이 active이고 키패드가 보이면 → OFF, 아니면 → ON
    const npActive = document.querySelector('.swipe-panel.panel-navigation.active');
    if (npActive && window.UIKeypad?.isOpen?.()) _kpTurnOff();
    else                                          _kpTurnOn();
  });

  // 레이아웃 토글 (단일 버튼이라 실제 모양 변화는 미미하지만 일관성 유지)
  function _setLayout(orientation, opts) {
    const isHorizontal = orientation === 'horizontal';
    const preserve = opts?.preservePosition !== false;
    const preRect = pill.getBoundingClientRect();
    const preCx = preRect.left + preRect.width  / 2;
    const preCy = preRect.top  + preRect.height / 2;
    const hadVisualPosition = preRect.width > 0;
    pill.classList.toggle('is-horizontal', isHorizontal);
    if (preserve && hadVisualPosition) {
      const newW = pill.offsetWidth;
      const newH = pill.offsetHeight;
      let newLeft = preCx - newW / 2;
      let newTop  = preCy - newH / 2;
      const margin = 6;
      newLeft = Math.max(margin, Math.min(window.innerWidth  - newW - margin, newLeft));
      newTop  = Math.max(margin, Math.min(window.innerHeight - newH - margin, newTop));
      pill.style.transform = 'none';
      pill.style.right = 'auto'; pill.style.bottom = 'auto';
      pill.style.left = newLeft + 'px'; pill.style.top = newTop + 'px';
    } else {
      pill.style.left = 'auto'; pill.style.top = 'auto';
      pill.style.transform = 'none';
      pill.style.right = '6px'; pill.style.bottom = '0';
    }
    const lbl = document.getElementById('floatMtpLayoutLabel');
    const ico = document.getElementById('floatMtpLayoutIcon');
    if (lbl) lbl.textContent = isHorizontal ? 'Undock' : 'Dock';
    if (ico) ico.textContent = isHorizontal ? '⊞' : '⊟';
    try { localStorage.setItem('usekit_menu_float_layout', orientation); } catch (e) {}
  }
  try {
    const saved = localStorage.getItem('usekit_menu_float_layout');
    if (saved === 'horizontal') _setLayout('horizontal', { preservePosition: false });
  } catch (e) {}
  try {
    const raw = localStorage.getItem('usekit_menu_float_pos');
    if (raw) {
      const pos = JSON.parse(raw);
      if (pos && typeof pos.left === 'number' && typeof pos.top === 'number') {
        const w = pill.offsetWidth  || 40;
        const h = pill.offsetHeight || 40;
        const margin = 6;
        const left = Math.max(margin, Math.min(window.innerWidth  - w - margin, pos.left));
        const top  = Math.max(margin, Math.min(window.innerHeight - h - margin, pos.top));
        pill.style.transform = 'none';
        pill.style.right = 'auto'; pill.style.bottom = 'auto';
        pill.style.left = left + 'px'; pill.style.top = top + 'px';
      }
    }
  } catch (e) {}
  document.getElementById('floatMtpHorizontal')?.addEventListener('click', () => {
    _closePanel();
    pill.style.transform = 'none';
    pill.style.left = 'auto'; pill.style.top = 'auto';
    pill.style.right = '6px'; pill.style.bottom = '0';
    try {
      const r = pill.getBoundingClientRect();
      localStorage.setItem('usekit_menu_float_pos', JSON.stringify({ left: r.left, top: r.top }));
    } catch (e) {}
  });

  // 외부 탭 시 패널 닫기
  document.addEventListener('touchstart', (e) => {
    if (panel && panel.style.display === 'flex') {
      if (!panel.contains(e.target) && !pill.contains(e.target)) _closePanel();
    }
  }, { passive: true, capture: true });

  // ────────────────────────────────
  // 풋터 btnMenuTool → MENU pill 토글 (기존 run tool / sql view 패턴과 동일)
  // 풋터 btnCopyTool → Copy pill 토글 (기존 CTRL+TAB과 병행하는 즉발 경로)
  // ────────────────────────────────
  function _bindFooterToggle(btnId, toggleFn) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    let _tc = false;
    btn.addEventListener('touchstart', e => { e.preventDefault(); _tc = true; }, { passive: false });
    btn.addEventListener('touchend',   e => { e.preventDefault(); if (_tc) { _tc = false; toggleFn(); } }, { passive: false });
    btn.addEventListener('mouseup',    e => { if (!_tc) toggleFn(); });
  }
  _bindFooterToggle('btnMenuTool', toggleMenuFloat);
  _bindFooterToggle('btnCopyTool', () => {
    if (window.ClipView?.toggle) window.ClipView.toggle();
  });

  // ────────────────────────────────
  // 트리거 경로 정리:
  //   ALT+TAB → Menu pill 토글 (ui_events.js qnTAB 바인드에서 처리)
  //   CTRL+TAB → Copy pill 토글 (ui_events.js qnTAB 바인드에서 처리)
  //   풋터 btnMenuTool → Menu pill 토글 (위 _bindFooterToggle)
  //   SHIFT_R+TAB 경로는 ALT+TAB으로 일원화하여 제거됨.
  // ────────────────────────────────

  // 외부 API
  window.MenuView = {
    show: showMenuFloat,
    hide: hideMenuFloat,
    toggle: toggleMenuFloat,
  };
})();
