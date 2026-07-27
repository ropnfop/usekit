// ---------------------------------------------------------------------------
//  usekit AI bridge server — MVP
//  Single file. ws only. No Express.
//
//  Usage:
//      npm install ws
//      node bridge.js
//
//  Listens:  ws://127.0.0.1:8081/ai
//
//  Protocol (see 검토안 §7):
//    → { type:"run",    id, provider, prompt }
//    → { type:"cancel", id }
//    ← { type:"start",  id }
//    ← { type:"delta",  id, text }
//    ← { type:"result", id, text }
//    ← { type:"error",  id, message }
//    ← { type:"end",    id }
//
//  Created by: The Little Prince x ROP x FOP
// ---------------------------------------------------------------------------

"use strict";

const { WebSocketServer } = require("ws");
const { spawn, execSync } = require("child_process");
const crypto = require("crypto");
const path = require("path");

// ---------------------------------------------------------------------------
//  Config
// ---------------------------------------------------------------------------

const PORT = parseInt(process.env.BRIDGE_PORT || "8081", 10);
const HOST = "127.0.0.1";
const DEBUG = process.env.BRIDGE_DEBUG === "1";

// Token — printed on startup, PWA must send in first message
const TOKEN = process.env.BRIDGE_TOKEN || crypto.randomBytes(16).toString("hex");

// Limits
const MAX_PROMPT_LENGTH = 32_000;      // chars
const JOB_TIMEOUT_MS    = 120_000;     // 2 min
const MAX_CONCURRENT    = 1;           // MVP: one job at a time

// Claude Code cli.js path — resolved once
const CLI_PATH = (() => {
  try {
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return path.join(root, "@anthropic-ai/claude-code/cli.js");
  } catch {
    return null;
  }
})();

// Allowed origins (PWA)
const ALLOWED_ORIGINS = new Set([
  "http://127.0.0.1",
  "http://localhost",
  "https://127.0.0.1",
  "https://localhost",
]);

// ---------------------------------------------------------------------------
//  State
// ---------------------------------------------------------------------------

let activeJob = null;   // { id, proc, ws, timer }

// ---------------------------------------------------------------------------
//  Helpers
// ---------------------------------------------------------------------------

function send(ws, obj) {
  if (ws.readyState === ws.OPEN) {
    ws.send(JSON.stringify(obj));
    if (DEBUG && obj.type !== 'delta') console.log(`TX:${obj.type}:${obj.id || 'n'}`);
  }
}

function killJob(reason) {
  if (!activeJob) return;
  const job = activeJob;
  activeJob = null;

  clearTimeout(job.timer);

  // Kill child process
  if (job.proc && !job.proc.killed) {
    try { job.proc.kill("SIGTERM"); } catch {}
    // Force kill after 2s
    setTimeout(() => {
      try { job.proc.kill("SIGKILL"); } catch {}
    }, 2000);
  }

  if (reason) {
    send(job.ws, { type: "error", id: job.id, message: reason });
  }
  send(job.ws, { type: "end", id: job.id });
}

function originAllowed(origin) {
  if (!origin) return false;
  try {
    const u = new URL(origin);
    const base = `${u.protocol}//${u.hostname}`;
    return ALLOWED_ORIGINS.has(base);
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
//  Provider registry — MVP: claude only
// ---------------------------------------------------------------------------

const providers = {
  claude: {
    spawn(prompt, options = {}) {
      if (!CLI_PATH) {
        throw new Error("Claude Code CLI not found. Run: npm install -g @anthropic-ai/claude-code@1.0.33");
      }
      const args = [
        CLI_PATH,
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
      ];

      if (options.continue) {
        args.push("--continue");
      } else if (options.session) {
        args.push("--resume", options.session);
      }

      if (options.model) {
        args.push("--model", options.model);
      }

      return spawn("node", args, {
        stdio: ["ignore", "pipe", "pipe"],
        env: { ...process.env },
      });
    },
  },
  // Future:
  // codex: { spawn(prompt, options) { ... } },
  // gemini: { spawn(prompt, options) { ... } },
};

// ---------------------------------------------------------------------------
//  JSONL parser — Claude Code stream-json
//
//  Types we care about (검토안 §6):
//    system/init    → ignore (or log)
//    assistant      → delta (streaming text)
//    result/success → final result
//    result + is_error → error
// ---------------------------------------------------------------------------

function parseJsonLine(line, jobId, ws) {
  let obj;
  try {
    obj = JSON.parse(line);
  } catch {
    return; // skip malformed lines
  }

  const type = obj.type;

  // Capture and forward session_id
  const sessionId = obj.session_id || obj.message?.session_id;
  if (sessionId && activeJob && activeJob.id === jobId) {
    activeJob.sessionId = sessionId;
  }

  if (type === "assistant") {
    // Extract text from assistant message content
    const content = obj.message?.content;
    if (Array.isArray(content)) {
      for (const block of content) {
        if (block.type === "text" && block.text) {
          send(ws, { type: "delta", id: jobId, text: block.text });
        }
      }
    } else if (typeof content === "string" && content) {
      send(ws, { type: "delta", id: jobId, text: content });
    }
  }

  if (type === "result") {
    if (obj.is_error) {
      send(ws, { type: "error", id: jobId, message: obj.result || "Unknown error" });
    } else {
      send(ws, { type: "result", id: jobId, text: obj.result || "" });
    }
  }
}

// ---------------------------------------------------------------------------
//  Job runner
// ---------------------------------------------------------------------------

function runJob(ws, id, provider, prompt, options = {}) {
  // Validate
  if (activeJob) {
    send(ws, { type: "error", id, message: "Another job is running. Cancel it first or wait." });
    return;
  }

  if (!providers[provider]) {
    send(ws, { type: "error", id, message: `Unknown provider: ${provider}` });
    send(ws, { type: "end", id });
    return;
  }

  if (!prompt || typeof prompt !== "string") {
    send(ws, { type: "error", id, message: "Empty prompt" });
    send(ws, { type: "end", id });
    return;
  }

  if (prompt.length > MAX_PROMPT_LENGTH) {
    send(ws, { type: "error", id, message: `Prompt too long (max ${MAX_PROMPT_LENGTH} chars)` });
    send(ws, { type: "end", id });
    return;
  }

  // Spawn
  let proc;
  try {
    proc = providers[provider].spawn(prompt, options);
  } catch (err) {
    send(ws, { type: "error", id, message: err.message });
    send(ws, { type: "end", id });
    return;
  }

  // Timeout
  const timer = setTimeout(() => {
    killJob("Job timed out");
  }, JOB_TIMEOUT_MS);

  activeJob = { id, proc, ws, timer };

  send(ws, { type: "start", id });

  // --- stdout: JSONL stream ---
  let buffer = "";

  proc.stdout.on("data", (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep incomplete line in buffer
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed) {
        parseJsonLine(trimmed, id, ws);
      }
    }
  });

  // --- stderr: log only ---
  proc.stderr.on("data", (chunk) => {
    if (DEBUG) {
      const msg = chunk.toString().trim();
      if (msg) console.error(`ERR:${id}:${msg.slice(0,100)}`);
    }
  });

  // --- exit ---
  proc.on("close", (code) => {
    // Flush remaining buffer
    if (buffer.trim()) {
      parseJsonLine(buffer.trim(), id, ws);
    }

    if (activeJob && activeJob.id === id) {
      if (code !== 0) {
        send(ws, { type: "error", id, message: `Process exited with code ${code}` });
      }
      const endMsg = { type: "end", id };
      if (activeJob.sessionId) endMsg.session_id = activeJob.sessionId;
      send(ws, endMsg);
      clearTimeout(activeJob.timer);
      activeJob = null;
    }
  });

  proc.on("error", (err) => {
    if (activeJob && activeJob.id === id) {
      send(ws, { type: "error", id, message: `Spawn error: ${err.message}` });
      send(ws, { type: "end", id });
      clearTimeout(activeJob.timer);
      activeJob = null;
    }
  });
}

// ---------------------------------------------------------------------------
//  WebSocket server
// ---------------------------------------------------------------------------

const wss = new WebSocketServer({
  host: HOST,
  port: PORT,
  path: "/ai",
  verifyClient: ({ origin, req }) => {
    // Allow same-device connections
    if (originAllowed(origin)) return true;

    // Also allow no-origin (CLI tools, curl, etc.)
    if (!origin) return true;

    if (DEBUG) console.warn(`REJ:${origin}`);
    return false;
  },
});

wss.on("connection", (ws, req) => {
  let authenticated = false;

  if (DEBUG) console.log(`CONN:${req.socket.remoteAddress}`);

  ws.on("message", (raw) => {
    let msg;
    try {
      msg = JSON.parse(raw.toString());
    } catch {
      send(ws, { type: "error", id: null, message: "Invalid JSON" });
      return;
    }

    // --- Auth: first message must contain token ---
    if (!authenticated) {
      if (msg.type === "auth" && msg.token === TOKEN) {
        authenticated = true;
        send(ws, { type: "auth", status: "ok" });
        if (DEBUG) console.log("AUTH:OK");
        return;
      }
      send(ws, { type: "error", id: null, message: "Auth required. Send {type:'auth', token:'...'} first." });
      ws.close(4001, "Unauthorized");
      return;
    }

    // --- Run ---
    if (msg.type === "run") {
      const options = {};
      if (msg.continue) options.continue = true;
      if (msg.session) options.session = msg.session;
      if (msg.model) options.model = msg.model;
      runJob(ws, msg.id, msg.provider || "claude", msg.prompt, options);
      return;
    }

    // --- Cancel ---
    if (msg.type === "cancel") {
      if (activeJob && activeJob.id === msg.id) {
        killJob("Cancelled by client");
      }
      return;
    }

    // --- Ping ---
    if (msg.type === "ping") {
      send(ws, { type: "pong" });
      return;
    }

    send(ws, { type: "error", id: msg.id || null, message: `Unknown type: ${msg.type}` });
  });

  ws.on("close", () => {
    if (DEBUG) console.log("DISC");
    // Kill active job if it belongs to this ws
    if (activeJob && activeJob.ws === ws) {
      killJob("Client disconnected");
    }
  });

  ws.on("error", (err) => {
    console.error(`WS:ERR:${err.message}`);
  });
});

// ---------------------------------------------------------------------------
//  Startup
// ---------------------------------------------------------------------------

wss.on("listening", () => {
  if (DEBUG) {
    console.log(`
╔══════════════════════════════════════════╗
║  usekit AI bridge                        ║
║  ws://${HOST}:${PORT}/ai                 ║
╠══════════════════════════════════════════╣
║  token: ${TOKEN}  ║
╠══════════════════════════════════════════╣
║  provider: claude (v1.0.33 cli.js)       ║
║  cli:      ${CLI_PATH ? "found" : "NOT FOUND"}                            ║
║  timeout:  ${JOB_TIMEOUT_MS / 1000}s                              ║
║  max jobs: ${MAX_CONCURRENT}                                ║
╚══════════════════════════════════════════╝
`);
  } else {
    console.log(`BRIDGE:${HOST}:${PORT}:${TOKEN}:${CLI_PATH ? 'CLI_OK' : 'CLI_MISSING'}`);
  }

  if (!CLI_PATH) {
    console.warn("CLI:MISSING - npm install -g @anthropic-ai/claude-code@1.0.33");
  }
});

// Graceful shutdown
process.on("SIGINT", () => {
  if (DEBUG) console.log("\nSHUT:SIGINT");
  killJob("Server shutting down");
  wss.close(() => process.exit(0));
});

process.on("SIGTERM", () => {
  killJob("Server shutting down");
  wss.close(() => process.exit(0));
});
