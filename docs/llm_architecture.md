# LLM Layer Architecture — Final Design

> usekit `classes/` 와 나란한 위상의 `llm/` 레이어

---

## 1. 디렉토리 구조

```
usekit/
├── classes/                    # existing
│   ├── common/
│   ├── core/
│   ├── data/
│   │   └── base/
│   │       ├── init/           # dbi_ prefix
│   │       ├── load/           # dbl_ prefix
│   │       └── post/           # dbp_ prefix (parser)
│   ├── exec/
│   ├── navi/
│   ├── support/
│   │   └── base/init/dbms/     # ud (DBHandler)
│   └── wrap/
│
├── llm/                        # ★ NEW — same level as classes/
│   ├── __init__.py             # exports: ua, UA
│   │
│   ├── base/                   # core pipeline
│   │   ├── init/               # lli_ prefix — connection, config
│   │   │   ├── lli_conn.py     # provider connection router
│   │   │   ├── lli_config.py   # set/get config (temp, tokens, etc)
│   │   │   └── lli_key.py      # API key management
│   │   │
│   │   ├── load/               # lll_ prefix — send/execute
│   │   │   ├── lll_send.py     # unified send dispatcher
│   │   │   └── lll_warm.py     # session warmup / ping
│   │   │
│   │   └── post/               # llp_ prefix — recv/parse
│   │       ├── llp_recv.py     # unified recv dispatcher
│   │       └── parser/         # provider-specific parsers
│   │           ├── parser_openai.py    # OpenAI-compatible (Qwen, vLLM, Ollama)
│   │           ├── parser_gemini.py    # Google Gemini SDK + REST
│   │           ├── parser_vertex.py    # Vertex AI
│   │           └── parser_raw.py       # raw/fallback
│   │
│   ├── provider/               # provider adapters
│   │   ├── __init__.py
│   │   ├── prov_openai.py      # OpenAI-compatible adapter
│   │   ├── prov_gemini.py      # Gemini SDK adapter
│   │   ├── prov_vertex.py      # Vertex adapter
│   │   └── prov_local.py       # local model (Gemma, Ollama)
│   │
│   ├── session/                # session state management
│   │   ├── __init__.py
│   │   └── llm_session.py      # warm/cold state, usekit json cache
│   │
│   └── handler/                # top-level handler class
│       ├── __init__.py
│       └── ua_handler.py       # UA class (= DBHandler equivalent)
│
└── usemain.py                  # adds: from usekit.llm import ua
```

---

## 2. 접두어 컨벤션

| Layer   | Prefix | Role              | Example               |
|---------|--------|-------------------|-----------------------|
| data    | `dbi_` `dbl_` `dbp_` | init/load/post | `dbl_read.py`    |
| exec    | `ebi_` `ebl_` `ebp_` | init/load/post | `ebl_ops_loader.py` |
| **llm** | `lli_` `lll_` `llp_` | init/load/post | `lli_conn.py`    |

```
lli_ = LLM Init    (conn, config, key)
lll_ = LLM Load    (send, warm, execute)
llp_ = LLM Post    (recv, parser)
```

---

## 3. UA Handler API — Final

```python
from usekit import ua

# ── Core ──────────────────────────────────────────
ua.conn("qwen")                     # connect provider
ua.conn("gemini", model="G15F")     # connect with model
ua.send("prompt")                   # send → raw response
ua.recv(res)                        # recv → parsed result dict
ua.close()                          # close session

# ── Config ────────────────────────────────────────
ua.set(temperature=0.3)             # set generation params
ua.set(max_tokens=1200)             # per-key set
ua.set(model="Q30B")                # switch model in provider
ua.get("temperature")               # get current config value

ua.key("sk-xxx")                    # set API key at runtime
ua.key()                            # get current key (masked)

# ── Status ────────────────────────────────────────
ua.ping()                           # health check → {ok, elapsed}
ua.warm()                           # ensure warm session
ua.info()                           # session info (provider, model, state)

# ── Shortcut ──────────────────────────────────────
ua.ask("prompt")                    # send + recv one-shot → text
ua.ask("prompt", json=True)         # send + recv → parsed json
```

---

## 4. ud ↔ ua Symmetry

```
DBHandler (ud)              AIHandler (ua)
─────────────────           ─────────────────
ud.conn("path")             ua.conn("qwen")
ud.exec("SQL")              ua.send("prompt")
ud.fetch("SQL")             ua.recv(res)
ud.one("SQL")               ua.ask("prompt")
ud.close()                  ua.close()
                            
ud.tables()                 ua.info()
ud.has("t")                 ua.ping()
ud.commit()                 ua.warm()
                            ua.set(k=v)
                            ua.key("xxx")
                            ua.get("k")
```

---

## 5. recv 파이프라인 (post layer detail)

`ua.recv(res)` 호출 시:

```
raw response
    │
    ▼
llp_recv.py  ─── provider 감지 (from session state)
    │
    ├── parser_openai.py   → OpenAI choices[0].message.content
    ├── parser_gemini.py   → Gemini SDK .text / REST candidates
    ├── parser_vertex.py   → Vertex predictions
    └── parser_raw.py      → fallback str()
    │
    ▼
Unified result dict:
{
    "text":     str,          # parsed text output
    "content":  dict | None,  # JSON parsed (if fenced)
    "usage":    dict,         # token usage
    "elapsed":  float,        # seconds
    "provider": str,          # "qwen" | "gemini" | ...
    "model":    str,          # actual model name
    "status":   str,          # "success" | "error"
    "finish":   str,          # "stop" | "length" | ...
    "error":    str | None,   # error message
    "raw":      Any,          # original response object
}
```

파서 확장 시: `parser/` 안에 `parser_<name>.py` 추가하면 끝.

---

## 6. Provider Adapter 규격

각 `prov_*.py` 는 동일 인터페이스:

```python
class ProviderAdapter:
    name: str = "openai"

    def connect(self, config: dict) -> dict:
        """Return session info dict"""
        ...

    def send(self, prompt: str, config: dict) -> Any:
        """Send prompt, return raw response"""
        ...

    def ping(self, config: dict) -> dict:
        """Health check → {ok: bool, elapsed: float}"""
        ...

    def close(self) -> None:
        ...
```

`lli_conn.py` 에서 provider name → adapter 매핑:

```python
PROVIDERS = {
    "qwen":    ProvOpenAI,     # OpenAI-compatible
    "openai":  ProvOpenAI,
    "ollama":  ProvOpenAI,
    "vllm":    ProvOpenAI,
    "gemini":  ProvGemini,
    "vertex":  ProvVertex,
    "local":   ProvLocal,
}
```

---

## 7. Session State (usekit native)

기존 pickle 캐시 → usekit `u.wjb/rjb` 로 교체:

```python
SESSION_KEY = "llm_session"

# save
u.wjb({
    "provider": "qwen",
    "model": "Qwen3-Coder-30B",
    "base_url": "https://qwen.ai.unturf.com/v1",
    "warm_state": "full_warm",
    "last_ping": 1.171,
    "config": {"temperature": 0.3, "max_tokens": 1200},
    "connected_at": "2026-05-14T23:12:03",
}, SESSION_KEY)

# load
meta = u.rjb(SESSION_KEY)
```

---

## 8. usemain.py 변경

```python
# [EXISTING]
from usekit.classes.wrap.sub.use_support import ut, uw, ud, us

# [NEW — add after support]
from usekit.llm import ua

__all__ = [
    "use", "u", "safe", "s", "ut", "uw", "ud", "us",
    "ua",   # ★ AI/LLM handler
]
```

---

## 9. 사용 예시

### Basic

```python
from usekit import ua

ua.conn("qwen")
ua.set(temperature=0.3, max_tokens=1200)

res = ua.send("Hello, what is 2+2?")
out = ua.recv(res)

print(out["text"])      # "2+2 = 4"
print(out["elapsed"])   # 1.23
```

### One-shot

```python
from usekit import ua

ua.conn("qwen")
text = ua.ask("Summarize this code")
print(text)
```

### Provider switch

```python
ua.conn("gemini", model="G15F")
ua.key("AIzaSy...")
text = ua.ask("Explain quantum computing")

ua.conn("qwen")   # auto-closes previous, opens new
text = ua.ask("Same question, different model")
```

### With warmup

```python
ua.conn("qwen")
state = ua.warm()       # ensure model loaded
print(state)            # {"warm": True, "elapsed": 1.17, "state": "full_warm"}

ua.set(temperature=0.5)
text = ua.ask("Write a haiku")
```

---

## 10. Implementation Priority

```
Phase 1: skeleton
   llm/__init__.py
   llm/handler/ua_handler.py      (UA class)
   llm/base/init/lli_conn.py      (conn router)
   llm/base/init/lli_config.py    (set/get)
   llm/base/load/lll_send.py      (send)
   llm/base/post/llp_recv.py      (recv dispatcher)

Phase 2: first provider
   llm/provider/prov_openai.py    (Qwen, OpenAI-compatible)
   llm/base/post/parser/parser_openai.py
   llm/session/llm_session.py

Phase 3: Gemini provider
   llm/provider/prov_gemini.py
   llm/base/post/parser/parser_gemini.py
   llm/base/init/lli_key.py

Phase 4: extras
   llm/provider/prov_vertex.py
   llm/provider/prov_local.py
   llm/base/load/lll_warm.py
   ua.ask() shortcut
```
