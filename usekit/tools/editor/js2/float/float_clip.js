// float_clip.js — Clip pill logic (extracted from index.html)
(function() {
  const pill = document.getElementById('floatClipTool');
  const panel = document.getElementById('floatClipToolPanel');
  const btnCopy = document.getElementById('floatBtnClipCopy');
  const btnPaste = document.getElementById('floatBtnClipPaste');
  const btnTool = document.getElementById('floatBtnClipTool');
  if (!pill || !panel) return;

  // ────────────────────────────────
  // 플로팅 전용 액션 — CTRL 모드와 독립적으로 동작
  //   ui_events.js의 CTRL 세트 동작(블록/단일 자동 분기)을 참조해 재구현.
  // ────────────────────────────────
  function _isBlockMode() { return !!window._uiIsBlockMode?.(); }

  // execCommand 우선 clipboard 유틸 (Samsung Browser user-gesture 호환)
  function _clipCopy(text) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
      document.body.appendChild(ta);
      ta.focus();
      ta.setSelectionRange(0, ta.value.length);
      document.execCommand('copy');
      ta.remove();
    } catch (e) {
      navigator.clipboard?.writeText?.(text).catch(() => {});
    }
  }

  function _doAll() {
    window.Nav?.selectAll?.();
  }

  function _doCopy() {
    if (_isBlockMode()) {
      // V2 멀티커서: 빈 range 제외, 같은 라인 중복 제거
      const text = window.NavBlockV2?.copyAll?.();
      if (text) {
        window.NavClipboard?.push?.(text);
        window.NavBlock?.setClipData?.(text);
        _clipCopy(text);
      } else {
        window.NavBlock?.copyColumnBlock?.(); // V1 폴백
      }
    } else {
      // CM6 선택 있으면 우선, 없으면 현재 라인(copyBlock)
      const sel = window.Editor?.getSelection?.();
      const t = sel || window.NavBlock?.copyBlock?.();
      if (t) {
        window.NavBlock?.setClipData?.(t);
        window.NavClipboard?.push?.(t);
        _clipCopy(t);
      }
    }
  }

  function _doPaste() {
    // 단일 모드는 단순 경로로 위임 (블록모드 멀티 페이스트 복잡 로직은 생략)
    // — 플로팅 사용자는 보통 단일 커서 상황이라 판단
    window.Nav?.pasteAtCursor?.();
  }

  function _doCut() {
    // 선택 있으면 CM6 선택 잘라내기, 없으면 V1 cutLine (현재 라인 cut)
    const sel = window.Editor?.getSelection?.();
    if (sel) {
      window.NavBlock?.setClipData?.(sel);
      window.NavClipboard?.push?.(sel);
      _clipCopy(sel);
      window.Editor?.replaceSelection?.('');
    } else {
      window.NavBlock?.cutLine?.();
    }
  }

  function _doList() {
    window.NavClipboard?.openModal?.();
  }

  // ────────────────────────────────
  // 표시/숨김
  // ────────────────────────────────
  function showClipFloat() {
    pill.style.display = 'flex';
    pill.style.pointerEvents = '';
    panel.style.display = 'none';
    try { localStorage.setItem('usekit_clip_float_visible', '1'); } catch (e) {}
    window._uiRefreshQnLabels?.();
  }
  function hideClipFloat() {
    pill.style.display = 'none';
    pill.style.pointerEvents = 'none';
    panel.style.display = 'none';
    try { localStorage.removeItem('usekit_clip_float_visible'); } catch (e) {}
    window._uiRefreshQnLabels?.();
  }
  function toggleClipFloat() {
    const isOpen = pill.style.display === 'flex';
    if (isOpen) hideClipFloat();
    else showClipFloat();
  }

  // 초기 상태 복원
  try {
    if (localStorage.getItem('usekit_clip_float_visible') === '1') {
      pill.style.display = 'flex';
      pill.style.pointerEvents = '';
    } else {
      pill.style.pointerEvents = 'none';
    }
  } catch (e) {
    pill.style.pointerEvents = 'none';
  }

  // ────────────────────────────────
  // 팝업 위치 계산 — 4방향 adaptive
  // ────────────────────────────────
  function _positionPanel() {
    if (!panel) return;
    const r = pill.getBoundingClientRect();
    const isHorizontal = pill.classList.contains('is-horizontal');
    const margin = 8;
    const panelW = panel.offsetWidth  || 160;
    const panelH = panel.offsetHeight || 200;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const pillCx = r.left + r.width / 2;
    const pillCy = r.top  + r.height / 2;

    if (isHorizontal) {
      const pillOnUpperHalf = pillCy < vh / 2;
      let topVal = pillOnUpperHalf ? r.bottom + 8 : r.top - panelH - 8;
      topVal = Math.max(margin, Math.min(vh - panelH - margin, topVal));
      let leftVal = r.right - panelW;
      leftVal = Math.max(margin, Math.min(vw - panelW - margin, leftVal));
      panel.style.top    = topVal  + 'px';
      panel.style.left   = leftVal + 'px';
      panel.style.right  = 'auto';
      panel.style.bottom = 'auto';
    } else {
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
  }

  function _togglePanel() {
    const show = panel.style.display === 'none' || panel.style.display === '';
    if (show) _positionPanel();
    panel.style.display = show ? 'flex' : 'none';
    btnTool.classList.toggle('is-active', show);
    if (show) requestAnimationFrame(_positionPanel);
  }
  function _closePanel() {
    panel.style.display = 'none';
    btnTool.classList.remove('is-active');
  }

  // ────────────────────────────────
  // 드래그 + 클릭 통합
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
    const dx = Math.abs(cx - (r.left + ox));
    const dy = Math.abs(cy - (r.top + oy));
    if (dx > 8 || dy > 8) moved = true;
    if (!moved) return;
    pill.style.transform = 'none';
    const w = pill.offsetWidth || 40;
    const h = pill.offsetHeight || 150;
    pill.style.left   = Math.max(0, Math.min(window.innerWidth  - w, cx - ox)) + 'px';
    pill.style.top    = Math.max(0, Math.min(window.innerHeight - h, cy - oy)) + 'px';
    pill.style.right  = 'auto';
    pill.style.bottom = 'auto';
    panel.style.display = 'none';
    btnTool.classList.remove('is-active');
  }
  function onEnd(target) {
    dragging = false;
    if (moved) {
      try {
        const r = pill.getBoundingClientRect();
        localStorage.setItem('usekit_clip_float_pos', JSON.stringify({ left: r.left, top: r.top }));
      } catch (e) {}
      return;
    }
    const id = target?.id || target?.closest?.('[id]')?.id;
    if      (id === 'floatBtnClipCopy' || target?.closest?.('#floatBtnClipCopy')) _doCopy();
    else if (id === 'floatBtnClipPaste' || target?.closest?.('#floatBtnClipPaste')) _doPaste();
    else if (id === 'floatBtnClipTool' || target?.closest?.('#floatBtnClipTool')) _togglePanel();
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
  // TOOL 패널 버튼
  // ────────────────────────────────
  function _bindCtpGroupToggle(toggleId, sectionId, arrowId) {
    const storageKey = 'usekit_mtp_grp_' + sectionId;
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
  _bindCtpGroupToggle('floatCtpClipToggle', 'floatCtpClipSection', 'floatCtpClipArrow');
  _bindCtpGroupToggle('floatCtpMenuToggle', 'floatCtpMenuSection', 'floatCtpMenuArrow');

  document.getElementById('floatCtpSelectAll')?.addEventListener('click', () => { _closePanel(); _doAll();   });
  document.getElementById('floatCtpCut')  ?.addEventListener('click', () => { _closePanel(); _doCut();   });
  document.getElementById('floatCtpList') ?.addEventListener('click', () => { _closePanel(); _doList();  });
  document.getElementById('floatCtpMenuHide')?.addEventListener('click', () => { _closePanel(); hideClipFloat(); });

  // Menu → Menu: 자기 Hide + Menu pill(허브) 표시
  document.getElementById('floatCtpMenuHub')?.addEventListener('click', () => {
    _closePanel();
    hideClipFloat();
    if (window.MenuView?.show) window.MenuView.show();
  });

  // ────────────────────────────────
  // 레이아웃 토글 (vertical ↔ horizontal)
  // ────────────────────────────────
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
      pill.style.right  = 'auto';
      pill.style.bottom = 'auto';
      pill.style.left   = newLeft + 'px';
      pill.style.top    = newTop  + 'px';
    } else {
      if (isHorizontal) {
        pill.style.right  = 'auto';
        pill.style.left   = '50%';
        pill.style.transform = 'translateX(-50%)';
        pill.style.top    = '12px';
        pill.style.bottom = 'auto';
      } else {
        pill.style.left   = 'auto';
        pill.style.right  = '14px';
        pill.style.top    = '50%';
        pill.style.transform = 'translateY(-50%)';
        pill.style.bottom = 'auto';
      }
    }
    const lbl = document.getElementById('floatCtpLayoutLabel');
    const ico = document.getElementById('floatCtpLayoutIcon');
    if (lbl) lbl.textContent = isHorizontal ? 'Vertical' : 'Horizontal';
    if (ico) ico.textContent = isHorizontal ? '▤' : '▦';
    try { localStorage.setItem('usekit_clip_float_layout', orientation); } catch (e) {}
  }
  try {
    const saved = localStorage.getItem('usekit_clip_float_layout');
    if (saved === 'horizontal') _setLayout('horizontal', { preservePosition: false });
  } catch (e) {}

  // 위치 복원 (레이아웃 복원 직후)
  try {
    const raw = localStorage.getItem('usekit_clip_float_pos');
    if (raw) {
      const pos = JSON.parse(raw);
      if (pos && typeof pos.left === 'number' && typeof pos.top === 'number') {
        const w = pill.offsetWidth  || 40;
        const h = pill.offsetHeight || 150;
        const margin = 6;
        const left = Math.max(margin, Math.min(window.innerWidth  - w - margin, pos.left));
        const top  = Math.max(margin, Math.min(window.innerHeight - h - margin, pos.top));
        pill.style.transform = 'none';
        pill.style.right  = 'auto';
        pill.style.bottom = 'auto';
        pill.style.left   = left + 'px';
        pill.style.top    = top  + 'px';
      }
    }
  } catch (e) {}

  document.getElementById('floatCtpMenuHorizontal')?.addEventListener('click', () => {
    _closePanel();
    const next = pill.classList.contains('is-horizontal') ? 'vertical' : 'horizontal';
    _setLayout(next);
    try {
      const r = pill.getBoundingClientRect();
      localStorage.setItem('usekit_clip_float_pos', JSON.stringify({ left: r.left, top: r.top }));
    } catch (e) {}
  });

  // 팝업 외부 탭 시 닫기
  document.addEventListener('touchstart', (e) => {
    if (panel && panel.style.display === 'flex') {
      if (!panel.contains(e.target) && !pill.contains(e.target)) _closePanel();
    }
  }, { passive: true, capture: true });

  // 외부 API (디버깅/확장용)
  window.ClipView = {
    show: showClipFloat,
    hide: hideClipFloat,
    toggle: toggleClipFloat,
  };
})();
