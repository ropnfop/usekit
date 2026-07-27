// float_memedit.js — Memory Editor overlay
// Entry point: float_ai.js rpDock2SessStatus ('session' pill) -> MemEdit.open()
//
// A2 SCOPE: session list (A1) + turn raw view with expand (this step) +
//   slot back-link on session cards. All read-only. No backend writes.
//
// Two views in one overlay:
//   'list'  GET /api/sessions      -> MAIN/TEMP 2-zone session cards
//   'turns' GET /api/session_turns -> that session's turns (load_turns_raw),
//           expandable cards (nav_clipboard clip-* pattern), status badges.
//
// Slot back-link (어린왕자: "어느 슬롯에서 파생됐나"):
//   The slot->session link lives CLIENT-side (OPFS), not in TSK_SESSION.
//   float_ai._restoreChat reads slot's chat.sessionId / job.sessionId. So we
//   build a reverse index { sessionId: {slot, kind} } from SlotStorage and tag
//   session cards. Sessions with no owning slot (temp / cleared) show nothing.
//
// Card title rule: TSK_SESSION.title (auto-backfill, ~40c) -> session_id[:12].
// Badges (A2, display only — toggles are Pack B):
//   importance · summary · temp · excluded(include_in_context=0) · status!=ok.
//
// Design: MEMORY_EDITOR_DESIGN_v2.md · MEMORY_EDITOR_BUILD_PLAN.md
// Invariants: separate module; view-only; load_turns_raw shows hidden turns too.

const MemEdit = (function () {
    'use strict';

    function _el(id) { return document.getElementById(id); }

    var _bound    = false;   // modal-level handlers bound once
    var _view     = 'list';  // 'list' | 'turns'
    var _curSid   = '';      // session_id when in 'turns'
    var _curTitle = '';      // session title when in 'turns'
    var _expanded = null;    // expanded turn seq (single, clip pattern)
    var _slotMap  = null;    // { sessionId: {slot, kind} } reverse index (cached per open)
    // A2.5: 3-way classification (어린왕자) — keyed on slot link, not server zone.
    //   linked = slot owns this session (OPFS reverse map hit)
    //   orphan = non-temp session with NO owning slot (slot gone, DB remains)
    //   temp   = temp_ scratch session (meaningless unit)
    var _zones    = { linked: [], orphan: [], temp: [] };
    var _zoneTab  = 'linked';  // active classification tab
    var _search   = '';        // A3: search query (view-only filter)
    var _sort     = 'latest';  // A3: latest | oldest | az | turns (view-only)
    // A3.5: turn-view filters (view-only; _curTurns 원본 불변)
    var _tSearch  = '';        // turn text search
    var _tRole    = 'all';     // all | you | ai
    var _tFlags   = { excluded: false, temp: false, failed: false };  // status toggles (AND)

    // --- util -------------------------------------------------------------
    function _esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function _fmtTime(s) {
        if (!s) return '';
        var d = new Date(String(s).replace(' ', 'T'));
        if (!isNaN(d.getTime())) {
            var p = function (n) { return String(n).padStart(2, '0'); };
            return String(d.getFullYear()).slice(2) + '-' + p(d.getMonth() + 1) + '-' +
                   p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
        }
        return String(s).slice(0, 16);
    }

    function _cardTitle(sess) {
        var t = (sess.title || '').trim();
        if (t) return t;
        var sid = String(sess.session_id || '');
        return sid ? sid.slice(0, 12) : '(no id)';
    }

    function _sidTail(sid) {
        sid = String(sid || '');
        return sid.length > 4 ? sid.slice(-4) : sid;
    }

    // --- slot reverse index (client-side OPFS) ----------------------------
    //   { sessionId : {slot, kind:'chat'|'task'} }. Best-effort; failures ignored.
    function _buildSlotMap() {
        var map = {};
        var SS = window.SlotStorage;
        if (!SS) return Promise.resolve(map);

        var jobs = [];
        var addFrom = function (names, reader, kind) {
            (names || []).forEach(function (name) {
                jobs.push(Promise.resolve()
                    .then(function () { return reader.call(SS, name); })
                    .then(function (data) {
                        var sid = data && data.sessionId;
                        if (sid && !map[sid]) map[sid] = { slot: name, kind: kind };
                    })
                    .catch(function () {}));
            });
        };
        try {
            var chatReader = SS.readChatAsync || SS.readChat;
            var jobReader  = SS.readJobAsync  || SS.readJob;
            addFrom(SS.listChatFileNames && SS.listChatFileNames(), chatReader, 'chat');
            addFrom(SS.listJobFileNames  && SS.listJobFileNames(),  jobReader,  'task');
        } catch (e) {}
        return Promise.all(jobs).then(function () { return map; });
    }

    // --- bindings (once) --------------------------------------------------
    function _bindOnce(modal) {
        if (_bound) return;
        _bound = true;
        var btnX    = _el('btnMemEditClose');
        var btnCncl = _el('btnMemEditCancel');
        modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
        if (btnX)    btnX.addEventListener('click', close);
        if (btnCncl) btnCncl.addEventListener('click', close);
        document.addEventListener('keydown', function (e) {
            if (modal.style.display === 'none') return;
            if (e.key === 'Escape') { _view === 'turns' ? _backToList() : close(); }
        });
        // A2.5: zone tabs (LINKED / ORPHAN / TEMP)
        var _tab = function (id, zone) {
            var el = _el(id);
            if (el) el.addEventListener('click', function () {
                if (_view !== 'list') return;
                _zoneTab = zone;
                _search = '';                       // A3: reset search per tab
                var sEl = _el('memEditSearch'); if (sEl) sEl.value = '';
                _renderActiveZone();
            });
        };
        _tab('memEditTabLinked', 'linked');
        _tab('memEditTabOrphan', 'orphan');
        _tab('memEditTabTemp',   'temp');

        // A3: search (view-only) — re-render active zone on input
        var sEl = _el('memEditSearch');
        if (sEl) sEl.addEventListener('input', function () {
            if (_view !== 'list') return;
            _search = sEl.value || '';
            _renderActiveZone();
        });
        // A3: sort buttons (view-only)
        var sortBtns = document.querySelectorAll('#memEditSortRow .load-sort-btn');
        for (var i = 0; i < sortBtns.length; i++) {
            sortBtns[i].addEventListener('click', function (e) {
                if (_view !== 'list') return;
                _sort = e.currentTarget.getAttribute('data-msort') || 'latest';
                _renderActiveZone();
            });
        }
    }

    // --- render: simple message row ---------------------------------------
    function _renderMsg(msg, dim) {
        var listEl = _el('memEditList');
        if (!listEl) return;
        listEl.innerHTML =
            '<div class="modal-item"><div class="item-body"><div class="item-name"' +
            (dim ? ' style="opacity:0.55;"' : '') + '>' + _esc(msg) + '</div></div></div>';
    }

    function _setHeader(title, count, path) {
        var t = _el('memEditTitle'); if (t) t.textContent = title;
        var c = _el('memEditCount'); if (c) c.textContent = count || '';
        var p = _el('memEditPath');  if (p) p.textContent = path || '';
    }

    // ====================================================================
    //  VIEW 1 — session list
    // ====================================================================
    function _renderCard(listEl, sess) {
        var div = document.createElement('div');
        div.className = 'modal-item';
        var sid = sess.session_id || '';
        div.dataset.sid = sid;

        var metaParts = [];
        var pm = [sess.provider, sess.model].filter(Boolean).join('/');
        if (pm) metaParts.push(_esc(pm));
        metaParts.push((sess.turn_count || 0) + ' turns');
        var ts = _fmtTime(sess.last_active_at);
        if (ts) metaParts.push(ts);
        metaParts.push('#' + _esc(_sidTail(sid)));   // disambiguate same-title sessions

        // slot back-link (DB slot first, OPFS backfill) — see _slotOf
        var link = _slotOf(sess);
        var linkHtml = link
            ? '<div class="memedit-slot-link">&#8592; ' + _esc(link.slot) + ' (' + _esc(link.kind) + ')</div>'
            : '';

        div.innerHTML =
            '<div class="item-body">' +
            '<div class="item-name">' + _esc(_cardTitle(sess)) + '</div>' +
            '<div class="item-meta">' + metaParts.join(' . ') + '</div>' +
            linkHtml +
            '</div>';

        div.addEventListener('click', function () { _openSession(sid, _cardTitle(sess)); });
        listEl.appendChild(div);
    }

    // Resolve a session's owning slot. DB TSK_SESSION.slot is the single source
    // of truth (1:N safe — every session carries its own slot). OPFS reverse map
    // is a backfill for legacy sessions saved before the slot column existed.
    function _slotOf(s) {
        if (s && s.slot) return { slot: s.slot, kind: 'chat' };
        var sid = s && s.session_id;
        if (sid && _slotMap && _slotMap[sid]) return _slotMap[sid];
        return null;
    }

    // A2.5: classify main/temp into linked/orphan/temp.
    //   linked = session owns a slot (DB slot, or OPFS backfill)
    //   orphan = real session with NO owning slot (deletable / re-bindable)
    function _classify(main, temp) {
        var z = { linked: [], orphan: [], temp: (temp || []).slice() };
        (main || []).forEach(function (s) {
            if (_slotOf(s)) z.linked.push(s);
            else z.orphan.push(s);
        });
        return z;
    }

    function _setTabsVisible(on) {
        var tabs = _el('memEditTabs');
        if (tabs) tabs.style.display = on ? '' : 'none';
    }

    function _setSearchSortVisible(on) {
        var s = _el('memEditSearch');   if (s) s.style.display = on ? '' : 'none';
        var r = _el('memEditSortRow');  if (r) r.style.display = on ? '' : 'none';
    }

    function _syncSortUI() {
        var btns = document.querySelectorAll('#memEditSortRow .load-sort-btn');
        for (var i = 0; i < btns.length; i++) {
            btns[i].classList.toggle('active', btns[i].getAttribute('data-msort') === _sort);
        }
    }

    function _syncTabUI() {
        var map = { linked: 'memEditTabLinked', orphan: 'memEditTabOrphan', temp: 'memEditTabTemp' };
        Object.keys(map).forEach(function (k) {
            var el = _el(map[k]);
            if (!el) return;
            el.classList.toggle('active', k === _zoneTab);
            // show count in label
            var base = k.toUpperCase();
            var n = _zones[k] ? _zones[k].length : 0;
            el.textContent = base + (n ? ' ' + n : '');
        });
    }

    // A3: view-only filter+sort. Operates on a COPY — _zones 원본 불변(원자 규율).
    function _slotNameOf(s) {
        var l = _slotOf(s);
        return l ? l.slot : '';
    }
    function _applyView(arr) {
        var q = _search.trim().toLowerCase();
        var out = arr;
        if (q) {
            out = arr.filter(function (s) {
                var sid = s.session_id || '';
                var hay = [
                    _cardTitle(s),
                    s.provider, s.model,
                    _slotNameOf(s),
                    sid
                ].join(' ').toLowerCase();
                return hay.indexOf(q) !== -1;
            });
        }
        out = out.slice();  // copy before sort
        var ts = function (s) { return new Date(String(s.last_active_at || '').replace(' ', 'T')).getTime() || 0; };
        if (_sort === 'latest') out.sort(function (a, b) { return ts(b) - ts(a); });
        else if (_sort === 'oldest') out.sort(function (a, b) { return ts(a) - ts(b); });
        else if (_sort === 'az') out.sort(function (a, b) { return _cardTitle(a).localeCompare(_cardTitle(b)); });
        else if (_sort === 'turns') out.sort(function (a, b) { return (b.turn_count || 0) - (a.turn_count || 0); });
        return out;
    }

    // render the active zone's session cards
    function _renderActiveZone() {
        var listEl = _el('memEditList');
        if (!listEl) return;
        listEl.innerHTML = '';
        _setTabsVisible(true);
        _setSearchSortVisible(true);
        var th = _el('memEditTurnHead'); if (th) th.style.display = 'none';

        var raw = _zones[_zoneTab] || [];
        var arr = _applyView(raw);
        var total = _zones.linked.length + _zones.orphan.length + _zones.temp.length;
        _setHeader('Memory Editor', total ? (total + ' sessions') : '', 'sessions');
        _syncTabUI();
        _syncSortUI();

        if (!arr.length) {
            var hint = _search
                ? '(no match)'
                : _zoneTab === 'linked' ? '(no slot-linked sessions)'
                : _zoneTab === 'orphan' ? '(no orphan sessions)'
                : '(no temp sessions)';
            _renderMsg(hint, true);
            return;
        }
        arr.forEach(function (s) { _renderCard(listEl, s); });
    }

    function _loadSessions() {
        _view = 'list'; _curSid = ''; _expanded = null;
        _renderMsg('loading...', true);
        // build slot map (client) and fetch sessions (server) in parallel
        Promise.all([
            _buildSlotMap().catch(function () { return {}; }),
            fetch('/api/sessions').then(function (r) {
                return r.json().catch(function () { return {}; });
            })
        ]).then(function (res) {
            _slotMap = res[0] || {};
            var j = res[1] || {};
            if (j.ok === false) {
                _renderMsg('(load failed: ' + _esc(j.error || 'unknown') + ')');
                return;
            }
            _renderSessions_done(j.main || [], j.temp || []);
        }).catch(function (e) {
            _renderMsg('(fetch error: ' + _esc(e && e.message ? e.message : e) + ')');
        });
    }

    function _renderSessions_done(main, temp) {
        _zones = _classify(main, temp);
        // keep current tab if it has items, else fall to first non-empty
        if (!_zones[_zoneTab] || !_zones[_zoneTab].length) {
            _zoneTab = _zones.linked.length ? 'linked'
                     : _zones.orphan.length ? 'orphan'
                     : 'temp';
        }
        _renderActiveZone();
    }

    // ====================================================================
    //  VIEW 2 — turns of one session (load_turns_raw, read-only)
    // ====================================================================
    function _badges(t) {
        var b = [];
        if (t.is_temporary)           b.push('<span class="memedit-badge bg-temp">temp</span>');
        if (Number(t.include_in_context) === 0)
                                      b.push('<span class="memedit-badge bg-excl">excluded</span>');
        if (t.turn_status && t.turn_status !== 'ok')
                                      b.push('<span class="memedit-badge bg-fail">' + _esc(t.turn_status) + '</span>');
        if (t.has_summary)            b.push('<span class="memedit-badge">summary</span>');
        b.push('<span class="memedit-badge">i' + (t.i != null ? _esc(t.i) : '0') + '</span>');
        return b.join('');
    }

    function _renderTurnCard(listEl, t) {
        var seq = t.seq;
        var isOpen = _expanded === seq;
        var dim = Number(t.include_in_context) === 0 || t.is_temporary;

        var wrap = document.createElement('div');
        wrap.className = 'memedit-turn' + (isOpen ? ' open' : '') + (dim ? ' dim' : '');

        var first = String(t.text || t.s || '').split('\n')[0] || '';
        if (first.length > 80) first = first.slice(0, 80) + '\u2026';

        var roleCls = _isUserRole(t.role) ? 'you' : 'ai';
        var row = document.createElement('div');
        row.className = 'memedit-turn-row';
        row.innerHTML =
            '<span class="memedit-turn-seq">#' + _esc(seq) + '</span>' +
            '<span class="memedit-turn-role role-' + roleCls + '">' + _esc(t.role) + '</span>' +
            '<span class="memedit-turn-title">' + _esc(first) + '</span>' +
            '<span class="memedit-turn-toggle">' + (isOpen ? '\u25B2' : '\u25BC') + '</span>';
        row.addEventListener('click', function () {
            _expanded = isOpen ? null : seq;
            _renderTurns(_curTurns);
        });
        wrap.appendChild(row);

        var badgeRow = document.createElement('div');
        badgeRow.className = 'memedit-turn-badges';
        badgeRow.innerHTML = _badges(t);
        wrap.appendChild(badgeRow);

        if (isOpen) {
            var detail = document.createElement('div');
            detail.className = 'memedit-turn-detail';
            // C3c: ASSISTANT turns carry an AI call -> read-only [Input]/[Output] body view.
            if (!_isUserRole(t.role)) {
                var tabs = document.createElement('div');
                tabs.style.cssText = 'display:flex; gap:.4rem; margin-bottom:.5rem;';
                var _mkTab = function (lbl, fld) {
                    var b = document.createElement('button');
                    b.textContent = lbl;
                    b.style.cssText = 'padding:.25rem .7rem; font-size:.8rem; border-radius:4px; ' +
                        'border:1px solid #3a4a6a; background:#26344e; color:#cdd9ee; cursor:pointer;';
                    b.addEventListener('click', function (e) {
                        e.stopPropagation();
                        _showCallBody(_curSid, seq, fld, lbl, t);
                    });
                    return b;
                };
                tabs.appendChild(_mkTab('\uC785\uB825', 'input_prompt'));   // 입력
                tabs.appendChild(_mkTab('\uC815\uBCF4', '_meta'));          // 정보 (telemetry)
                detail.appendChild(tabs);
            }
            var pre = document.createElement('pre');
            pre.className = 'memedit-turn-content';
            pre.textContent = t.text || '(no content)';
            detail.appendChild(pre);
            if (t.s) {
                var sm = document.createElement('div');
                sm.className = 'memedit-turn-summary';
                sm.textContent = 'summary: ' + t.s;
                detail.appendChild(sm);
            }
            wrap.appendChild(detail);
        }
        listEl.appendChild(wrap);
    }

    // C3c: fetch one turn's AI-call body and show it read-only via MetaView.
    //   sid+seq -> /api/call_body -> {has_body, input_prompt, output_text, level, ctx_mode,...}.
    //   No body (summary level / no call) is shown as an explicit notice, not an error.
    function _showCallBody(sid, seq, field, label, t) {
        if (!sid || seq == null) return;
        var open = (window.MetaView && window.MetaView.open)
            ? window.MetaView.open
            : function (t, x) { try { alert(t + '\n\n' + x); } catch (e) {} };
        var title = label + ' \u00b7 #' + seq;
        fetch('/api/call_body?sid=' + encodeURIComponent(sid) + '&seq=' + encodeURIComponent(seq))
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (!j || !j.ok || !j.found) { open(title, '(\uC774 \uD134\uC758 AI \uD638\uCD9C \uAE30\uB85D\uC774 \uC5C6\uC2B5\uB2C8\uB2E4)'); return; }
                // [정보] telemetry — available even without body (summary level).
                if (field === '_meta') {
                    var v = function (x) { return (x == null) ? '?' : x; };
                    var comp = (j.completion_tokens != null) ? j.completion_tokens
                        : ((j.total_tokens != null && j.prompt_tokens != null) ? (j.total_tokens - j.prompt_tokens) : null);
                    var L = [];
                    L.push('\uBAA8\uB378   : ' + v(j.provider) + ' / ' + v(j.model));
                    L.push('\uD1A0\uD070   : prompt ' + v(j.prompt_tokens) + ' \u00b7 completion ' + v(comp) + ' \u00b7 total ' + v(j.total_tokens));
                    L.push('\uC2DC\uAC04   : ' + (j.elapsed_ms != null ? (j.elapsed_ms + ' ms') : '?') + (j.ttft_ms != null ? ('  (ttft ' + j.ttft_ms + ' ms)') : ''));
                    L.push('finish : ' + v(j.finish) + (Number(j.ok) === 0 ? '  (FAILED)' : ''));
                    L.push('context: ' + v(j.ctx_mode) + ' \u00b7 merged ' + v(j.turns_merged) + (j.refeed ? (' \u00b7 refeed ' + j.refeed) : ''));
                    L.push('level  : ' + v(j.level));
                    if (j.error_type) L.push('error  : ' + j.error_type + ' \u2014 ' + (j.error_summary || ''));
                    L.push('\uC0DD\uC131   : ' + v(j.created_at));
                    L.push('call_id: ' + v(j.call_id));
                    if (t) {
                        L.push('');
                        L.push('\uC694\uC57D   : ' + (t.s || '(\uC5C6\uC74C)'));               // 요약 (meta.s)
                        L.push('\uC911\uC694\uB3C4 : ' + v(t.i) + ' / 9');                      // 중요도 (meta.i)
                        L.push('\uD0A4\uC6CC\uB4DC : ' + ((t.kw && t.kw.length) ? t.kw.join(', ') : '(\uC5C6\uC74C)')); // 키워드 (meta.kw)
                    }
                    open(title, L.join('\n'), { hint: 'read-only \u00b7 telemetry' });
                    return;
                }
                if (!j.has_body) {
                    open(title, '(\uBCF8\uBB38 \uBBF8\uAE30\uB85D \u2014 telemetry.level=summary. debug\uB85C \uCF1C\uC57C \uC785\uCD9C\uB825\uC774 \uC800\uC7A5\uB429\uB2C8\uB2E4)');
                    return;
                }
                var text = j[field];
                open(title,
                    (text == null || text === '') ? '(' + label + ' \uBCF8\uBB38\uC774 \uBE44\uC5B4 \uC788\uC2B5\uB2C8\uB2E4)' : text,
                    { hint: 'read-only \u00b7 level=' + (j.level || '?') + ' \u00b7 ctx=' + (j.ctx_mode || '?') +
                            (j.turns_merged != null ? (' \u00b7 merged=' + j.turns_merged) : '') });
            })
            .catch(function (e) { open(title, '(call_body \uC870\uD68C \uC2E4\uD328: ' + e + ')'); });
    }

    var _curTurns = [];

    // A3.5: filter turns on a copy (원본 _curTurns 불변 — 원자 규율).
    //   role values vary in data (you|user vs ai|assistant) — match loosely.
    function _isUserRole(role) {
        var r = String(role || '').toLowerCase();
        return r === 'you' || r === 'user';
    }
    function _applyTurnView(turns) {
        var q = _tSearch.trim().toLowerCase();
        return turns.filter(function (t) {
            // role
            if (_tRole === 'you' && !_isUserRole(t.role)) return false;
            if (_tRole === 'ai'  &&  _isUserRole(t.role)) return false;
            // status toggles (AND: each enabled flag must match)
            if (_tFlags.excluded && Number(t.include_in_context) !== 0) return false;
            if (_tFlags.temp     && !t.is_temporary) return false;
            if (_tFlags.failed   && (!t.turn_status || t.turn_status === 'ok')) return false;
            // text
            if (q) {
                var hay = String(t.text || '') + ' ' + String(t.s || '');
                if (hay.toLowerCase().indexOf(q) === -1) return false;
            }
            return true;
        });
    }

    // A3.5: build the turn filter bar (role seg + status toggles + text)
    function _buildTurnFilterBar() {
        var bar = document.createElement('div');
        bar.className = 'memedit-tfilter';

        // role segment
        var roleWrap = document.createElement('div');
        roleWrap.className = 'load-sort-group';
        [['all', 'All'], ['you', 'You'], ['ai', 'AI']].forEach(function (r) {
            var b = document.createElement('button');
            b.className = 'load-sort-btn' + (_tRole === r[0] ? ' active' : '');
            b.textContent = r[1];
            b.addEventListener('click', function () { _tRole = r[0]; _renderTurns(_curTurns); });
            roleWrap.appendChild(b);
        });
        bar.appendChild(roleWrap);

        // status toggles
        var flagWrap = document.createElement('div');
        flagWrap.className = 'load-sort-group';
        [['excluded', 'excluded'], ['temp', 'temp'], ['failed', 'failed']].forEach(function (f) {
            var b = document.createElement('button');
            b.className = 'load-sort-btn' + (_tFlags[f[0]] ? ' active' : '');
            b.textContent = f[1];
            b.addEventListener('click', function () { _tFlags[f[0]] = !_tFlags[f[0]]; _renderTurns(_curTurns); });
            flagWrap.appendChild(b);
        });
        bar.appendChild(flagWrap);

        // text search
        var inp = document.createElement('input');
        inp.className = 'modal-search';
        inp.type = 'text';
        inp.placeholder = 'search turn text...';
        inp.value = _tSearch;
        inp.setAttribute('autocomplete', 'off');
        inp.addEventListener('input', function () {
            _tSearch = inp.value || '';
            _renderTurnsListOnly();   // keep input focus — re-render only the list part
        });
        bar.appendChild(inp);

        return bar;
    }

    // re-render only turn cards (used by text input to preserve focus)
    function _renderTurnsListOnly() {
        var listEl = _el('memEditList');
        if (!listEl) return;
        listEl.innerHTML = '';
        var shown = _applyTurnView(_curTurns);
        _setHeader(_curTitle || 'session', shown.length + ' / ' + _curTurns.length + ' turns', '#' + _sidTail(_curSid));
        if (!shown.length) { _renderMsgAppend(listEl, '(no match)'); return; }
        shown.forEach(function (t) { _renderTurnCard(listEl, t); });
    }

    function _renderMsgAppend(listEl, msg) {
        var d = document.createElement('div');
        d.className = 'modal-item';
        d.innerHTML = '<div class="item-body"><div class="item-name" style="opacity:0.55;">' + _esc(msg) + '</div></div>';
        listEl.appendChild(d);
    }

    function _renderTurns(turns) {
        var listEl = _el('memEditList');
        var headEl = _el('memEditTurnHead');
        if (!listEl) return;
        listEl.innerHTML = '';

        // head (back + filter) lives OUTSIDE the scroll area -> no overlap
        if (headEl) {
            headEl.style.display = '';
            headEl.innerHTML = '';
            var back = document.createElement('div');
            back.className = 'memedit-back';
            back.innerHTML = '\u2190 sessions';
            back.addEventListener('click', _backToList);
            headEl.appendChild(back);
            headEl.appendChild(_buildTurnFilterBar());
        }

        var shown = _applyTurnView(turns);
        _setHeader(_curTitle || 'session', shown.length + ' / ' + turns.length + ' turns', '#' + _sidTail(_curSid));

        if (!turns.length) { _renderMsgAppend(listEl, '(no turns)'); return; }
        if (!shown.length) { _renderMsgAppend(listEl, '(no match)'); return; }
        shown.forEach(function (t) { _renderTurnCard(listEl, t); });
    }

    function _openSession(sid, title) {
        if (!sid) return;
        _view = 'turns'; _curSid = sid; _curTitle = title || ''; _expanded = null;
        _tSearch = ''; _tRole = 'all'; _tFlags = { excluded: false, temp: false, failed: false };
        _setTabsVisible(false);
        _setSearchSortVisible(false);
        var listEl = _el('memEditList');
        if (listEl) listEl.innerHTML = '';
        _setHeader(_curTitle || 'session', 'loading...', '#' + _sidTail(sid));
        fetch('/api/session_turns?sid=' + encodeURIComponent(sid) + '&limit=200')
            .then(function (r) { return r.json().catch(function () { return {}; }); })
            .then(function (j) {
                if (j.ok === false) { _renderMsg('(load failed: ' + _esc(j.error || 'unknown') + ')'); return; }
                _curTurns = j.turns || [];
                _renderTurns(_curTurns);
            })
            .catch(function (e) {
                _renderMsg('(fetch error: ' + _esc(e && e.message ? e.message : e) + ')');
            });
    }

    function _backToList() {
        _view = 'list'; _curSid = ''; _expanded = null; _curTurns = [];
        _loadSessions();
    }

    // --- public open/close ------------------------------------------------
    function open() {
        var modal = _el('memEditModal');
        if (!modal) {
            if (window.UI && window.UI.showToast) window.UI.showToast('Memory Editor not loaded', 1200);
            return;
        }
        if (modal.style.display === 'flex') { close(); return; }   // toggle
        _bindOnce(modal);
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
        _loadSessions();
    }

    function close() {
        var modal = _el('memEditModal');
        if (!modal) return;
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        _view = 'list'; _expanded = null;
    }

    return { open: open, close: close };
})();

window.MemEdit = MemEdit;
