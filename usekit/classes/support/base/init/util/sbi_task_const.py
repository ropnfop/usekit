# Path: usekit.classes.support.base.init.util.sbi_task_const.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# Task Queue — enum / shape SSOT  (single source of truth)
#
# One place defines the vocabulary of the task queue engine. The DDL comments
# in sys/sys_ddl/01_TSK.sql and the TBL_META enum dictionary both DERIVE from
# here; nothing else should hard-code these strings. This kills the "three
# scattered copies drift apart" failure (DESIGN §2.4 / DECISION 'enum 불일치').
#
# Touched by:
#   uu.task   (sbi_util)   - writes status / worker_type / action_type
#   uu.queue  (sbi_queue)  - owns status transition; validates against STATUS
#   ua bridge (sbi_ai_action) - clamps proposals to ACTION_TYPE whitelist
#
# This module has NO imports and NO side effects on purpose: it must be safe to
# import from DDL tooling, the engine, and tests alike.
# -----------------------------------------------------------------------------------------------


# -- step lifecycle ------------------------------------------------------------------------------
# 8-state enum. Legacy 'error' is folded into 'failed'; 'cancelled' is handled
# early on as failed(reason=cancelled) or archived rather than its own state.
STATUS_PENDING = "pending"                  # queued, not yet run
STATUS_RUNNING = "running"                  # worker executing
STATUS_WAITING_FEEDBACK = "waiting_feedback"  # awaiting user / external input
STATUS_RETRY = "retry"                      # scheduled for re-attempt
STATUS_BLOCKED = "blocked"                  # prerequisite unmet
STATUS_DONE = "done"                        # completed
STATUS_FAILED = "failed"                    # failed (absorbs legacy 'error')
STATUS_ARCHIVED = "archived"                # retained after cleanup

STATUS = (
    STATUS_PENDING,
    STATUS_RUNNING,
    STATUS_WAITING_FEEDBACK,
    STATUS_RETRY,
    STATUS_BLOCKED,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_ARCHIVED,
)

# Terminal states never transition further (queue must not re-dispatch these).
STATUS_TERMINAL = (STATUS_DONE, STATUS_FAILED, STATUS_ARCHIVED)


# -- worker dispatch -----------------------------------------------------------------------------
WORKER_LLM = "llm"                          # dispatch to ua / llp
WORKER_CLI = "cli"                          # dispatch to task_manager.run_command
WORKER_READ = "read"                        # read handler
WORKER_WRITE = "write"                      # write handler
WORKER_NONE = "none"                        # no worker (terminal / marker step)

WORKER_TYPE = (WORKER_LLM, WORKER_CLI, WORKER_READ, WORKER_WRITE, WORKER_NONE)


# -- action vocabulary (what a step asks to happen next) -----------------------------------------
ACTION_NONE = "none"                        # stop the chain
ACTION_NEXT_TURN = "next_turn"              # schedule another llm turn
ACTION_READ = "read"                        # read a resource
ACTION_WRITE = "write"                      # write a resource
ACTION_RUN_COMMAND = "run_command"          # run a CLI command

ACTION_TYPE = (
    ACTION_NONE,
    ACTION_NEXT_TURN,
    ACTION_READ,
    ACTION_WRITE,
    ACTION_RUN_COMMAND,
)

# Actions the server policy judge admits by default. Mutating / shell actions
# are intentionally NOT here yet (DESIGN §3.3 — added with their guards).
ACTION_WHITELIST_DEFAULT = (ACTION_NONE, ACTION_NEXT_TURN, ACTION_READ)


# -- json envelope (version:1 minimal common shape) ----------------------------------------------
# Columns (worker_type/action_type/status) carry query/filter load; JSON is body
# only. Keep the shape minimal but forward-extensible (DECISION 'JSON 최소공통형').
JSON_VERSION = 1


def payload(source="chat", input=None, options=None):
    """Build a payload_json dict: worker input."""
    return {
        "version": JSON_VERSION,
        "source": source,
        "input": input or {},
        "options": options or {},
    }


def result(ok=True, output=None, summary=""):
    """Build a result_json dict: worker output."""
    return {
        "version": JSON_VERSION,
        "ok": bool(ok),
        "output": output or {},
        "summary": summary,
    }


def error(type="runtime_error", message="", trace="", retryable=False):
    """Build an error_json dict: failure detail."""
    return {
        "version": JSON_VERSION,
        "type": type,
        "message": message,
        "trace": trace,
        "retryable": bool(retryable),
    }


# -- recursion guard -----------------------------------------------------------------------------
DEFAULT_MAX_DEPTH = 5                        # mirrors TSK_STEP.max_depth DEFAULT


# -- validators (cheap, no deps) -----------------------------------------------------------------
def is_status(v):
    return v in STATUS


def is_worker_type(v):
    return v in WORKER_TYPE


def is_action_type(v):
    return v in ACTION_TYPE


def is_terminal(status):
    return status in STATUS_TERMINAL


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
