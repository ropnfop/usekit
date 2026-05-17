// float_common.js — clamp + blk pill + touch prevent (extracted from index.html)
(function() {
  const _CLAMP_MARGIN = 4;

  // ─────────────────────────────────
  // 자동 위치 보정: 패널이 화면 밖으로 넘치면 밀어넣기
  // ─────────────────────────────────
  function _clampPanel(panel) {
    if (!panel || panel.style.display === 'none') return;
    const r = panel.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let changed = false;
    let top  = r.top;
    let left = r.left;

    if (r.bottom > vh - _CLAMP_MARGIN) {
      top = Math.max(_CLAMP_MARGIN, vh - r.height - _CLAMP_MARGIN);
      changed = true;
    }
    if (r.top < _CLAMP_MARGIN) {
      top = _CLAMP_MARGIN;
      changed = true;
    }
    if (r.right > vw - _CLAMP_MARGIN) {
      left = Math.max(_CLAMP_MARGIN, vw - r.width - _CLAMP_MARGIN);
      changed = true;
    }
    if (r.left < _CLAMP_MARGIN) {
      left = _CLAMP_MARGIN;
      changed = true;
    }

    if (changed) {
      panel.style.top    = top  + 'px';
      panel.style.left   = left + 'px';
      panel.style.right  = 'auto';
      panel.style.bottom = 'auto';
    }
  }

  // ─────────────────────────────────
  // 패널 드래그: 헤더 영역을 잡고 이동
  // ─────────────────────────────────
  function _makePanelDraggable(panelId, headerSelector) {
    const panel  = document.getElementById(panelId);
    if (!panel) return;
    const handle = panel.querySelector(headerSelector);
    if (!handle) return;

    // 드래그용 커서 표시
    handle.style.cursor = 'grab';
    handle.style.touchAction = 'none';

    let dragging = false, ox = 0, oy = 0, moved = false, _touchId = null;

    function onStart(cx, cy) {
      dragging = true; moved = false;
      const r = panel.getBoundingClientRect();
      ox = cx - r.left;
      oy = cy - r.top;
      handle.style.cursor = 'grabbing';
    }
    function onMove(cx, cy) {
      if (!dragging) return;
      if (!moved) {
        const r = panel.getBoundingClientRect();
        if (Math.abs(cx - (r.left + ox)) < 4 && Math.abs(cy - (r.top + oy)) < 4) return;
        moved = true;
      }
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const w  = panel.offsetWidth;
      const h  = panel.offsetHeight;
      const left = Math.max(_CLAMP_MARGIN, Math.min(vw - w - _CLAMP_MARGIN, cx - ox));
      const top  = Math.max(_CLAMP_MARGIN, Math.min(vh - h - _CLAMP_MARGIN, cy - oy));
      panel.style.left   = left + 'px';
      panel.style.top    = top  + 'px';
      panel.style.right  = 'auto';
      panel.style.bottom = 'auto';
    }
    function onEnd() {
      dragging = false;
      handle.style.cursor = 'grab';
    }

    handle.addEventListener('touchstart', e => {
      if (e.touches.length !== 1) return;
      e.stopPropagation();
      const t = e.touches[0]; _touchId = t.identifier;
      onStart(t.clientX, t.clientY);
    }, { passive: true });
    handle.addEventListener('touchmove', e => {
      const t = [...e.touches].find(x => x.identifier === _touchId);
      if (t && dragging) {
        e.preventDefault();
        onMove(t.clientX, t.clientY);
      }
    }, { passive: false });
    handle.addEventListener('touchend', e => {
      if (dragging) { e.stopPropagation(); onEnd(); }
    }, { passive: true });
    handle.addEventListener('mousedown', e => {
      e.stopPropagation();
      onStart(e.clientX, e.clientY);
    });
    document.addEventListener('mousemove', e => { if (dragging) onMove(e.clientX, e.clientY); });
    document.addEventListener('mouseup',   e => { if (dragging) onEnd(); });
  }

  // ─────────────────────────────────
  // 아코디언 토글 후 자동 보정 바인딩
  // ─────────────────────────────────
  function _bindClampOnToggle(panelId, toggleSelector) {
    const panel = document.getElementById(panelId);
    if (!panel) return;
    const toggles = panel.querySelectorAll(toggleSelector);
    toggles.forEach(btn => {
      btn.addEventListener('click', () => {
        // 아코디언 토글 후 높이 변경 반영 대기
        requestAnimationFrame(() => _clampPanel(panel));
      });
    });
  }

  // ─────────────────────────────────
  // 4개 패널에 적용
  // ─────────────────────────────────
  const _PANELS = [
    { id: 'floatToolPanel',     header: '.tp-header',  toggles: '.tp-grp-toggle'  },
    { id: 'floatSqlToolPanel',  header: '.stp-header', toggles: '.stp-grp-toggle' },
    { id: 'floatClipToolPanel', header: '.ctp-header', toggles: '.ctp-grp-toggle' },
    { id: 'floatMenuToolPanel', header: '.mtp-header', toggles: '.mtp-grp-toggle' },
  ];

  for (const p of _PANELS) {
    _makePanelDraggable(p.id, p.header);
    _bindClampOnToggle(p.id, p.toggles);
  }

  // ─────────────────────────────────
  // 패널 닫기 버튼 (✕)
  // ─────────────────────────────────
  document.querySelectorAll('.float-panel-close').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const panelId = btn.dataset.panel;
      const panel = document.getElementById(panelId);
      if (panel) panel.style.display = 'none';
    });
  });
})();

// ═══════════════════════════════════════════
// BLOCK TOOL pill — 드래그 로직 (MENU pill과 동일 패턴)
// 탭 → qnBlkOff 핸들러 실행 (ui_events.js의 _bind('qnBlkOff', ...))
// 드래그 → 위치 이동 + localStorage 저장
// ═══════════════════════════════════════════
(function() {
  const pill = document.getElementById('floatBlkTool');
  const btn  = document.getElementById('qnBlkOff');
  if (!pill || !btn) return;

  // 저장된 위치 복원
  try {
    const saved = localStorage.getItem('usekit_blk_float_pos');
    if (saved) {
      const pos = JSON.parse(saved);
      if (typeof pos.left === 'number' && typeof pos.top === 'number') {
        // 화면 경계 클램프
        const w = 40, h = 40, margin = 6;
        const left = Math.max(margin, Math.min(window.innerWidth  - w - margin, pos.left));
        const top  = Math.max(margin, Math.min(window.innerHeight - h - margin, pos.top));
        pill.style.left = left + 'px';
        pill.style.top  = top + 'px';
        pill.style.right = 'auto';
        pill.style.bottom = 'auto';
      }
    }
  } catch (e) {}

  // 드래그 상태
  // DRAG_THRESHOLD: 손가락 흔들림으로 인한 의도치 않은 드래그 판정 방지
  //   작으면 탭 시도 중 미세 이동이 드래그로 잡힘 → 가끔 핸들러 미발화
  //   크면 의도적 드래그 시작이 둔함 → 12px 정도가 체감상 무난
  const DRAG_THRESHOLD = 12;
  let dragging = false, ox = 0, oy = 0, moved = false, _touchId = null;

  function onStart(cx, cy) {
    dragging = true; moved = false;
    const r = pill.getBoundingClientRect();
    ox = cx - r.left; oy = cy - r.top;
  }
  function onMove(cx, cy) {
    if (!dragging) return;
    const r = pill.getBoundingClientRect();
    // moved 확정은 임계값 초과 시에만 — 이후 계속 이동 중이면 moved는 true 유지
    if (!moved) {
      if (Math.abs(cx - (r.left + ox)) > DRAG_THRESHOLD ||
          Math.abs(cy - (r.top  + oy)) > DRAG_THRESHOLD) {
        moved = true;
      } else {
        return;  // 아직 탭 가능성 — 위치 이동시키지 않음
      }
    }
    // moved === true: 실제 드래그 진행 중 — 위치 업데이트
    const w = pill.offsetWidth || 40;
    const h = pill.offsetHeight || 40;
    pill.style.left   = Math.max(0, Math.min(window.innerWidth  - w, cx - ox)) + 'px';
    pill.style.top    = Math.max(0, Math.min(window.innerHeight - h, cy - oy)) + 'px';
    pill.style.right  = 'auto';
    pill.style.bottom = 'auto';
  }
  function onEnd(target) {
    const wasDragging = dragging;
    const wasMoved = moved;
    dragging = false;
    moved = false;  // 다음 인터랙션 위해 초기화
    if (!wasDragging) return;
    if (wasMoved) {
      // 드래그 종료: 위치 저장, 클릭 트리거 안 함
      try {
        const r = pill.getBoundingClientRect();
        localStorage.setItem('usekit_blk_float_pos', JSON.stringify({ left: r.left, top: r.top }));
      } catch (e) {}
      return;
    }
    // 단순 탭: ui_events.js의 핸들러 직접 호출
    if (target === btn || target?.closest?.('#qnBlkOff')) {
      window._blkOffExec?.();
    }
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
})();

// float pill 본체 — 터치 시 OS 키보드 방지 (preventDefault)
['floatRunTool','floatSqlTool','floatClipTool','floatMenuTool','floatBlkTool'
].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('touchstart', e => {
    if (e.target.closest('button,a,[role="button"]')) e.preventDefault();
  }, { passive: false });
});

// float tool 패널 — 키보드 미오픈 시만 차단 (퀵도구 패턴)
['floatToolPanel','floatSqlToolPanel','floatClipToolPanel','floatMenuToolPanel'
].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('touchstart', () => {
    if (!window.UIViewport?.isKbOpen?.()) window.UIViewport?.blockKeyboard?.();
  }, { passive: true });
});
