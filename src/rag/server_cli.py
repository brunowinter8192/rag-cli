# INFRASTRUCTURE
import json
import time
from pathlib import Path

from . import error_log
from .server_utils import SERVERS, TIMESTAMP_DIR, _stop_by_state, _check_health_port
from .server_lifecycle import (
    start, stop, restart, start_all, stop_all, start_arbitrary, status,
)


# ORCHESTRATOR

# Handle 'workflow.py server' / 'rag-cli server' subcommand
def cli_server(args: list[str]) -> None:
    if not args:
        args = ["status"]
    action = args[0]
    target = args[1] if len(args) > 1 else None
    handlers = {
        "status":  _action_status,
        "start":   _action_start,
        "stop":    _action_stop,
        "restart": _action_restart,
        "list":    _action_list,
        "tail":    _action_tail,
        "errors":  _action_errors,
        "presets": _action_presets,
    }
    handler = handlers.get(action)
    if handler is None:
        print(f"Unknown action: {action}. Use: status, start, stop, restart, list, tail, errors, presets")
        return
    handler(args, target)


# FUNCTIONS

# Print server status table
def _action_status(args: list[str], target: str | None) -> None:
    st = status()
    print(f"{'Server':<12} {'Port':<6} {'Status':<10} {'PID':<8} {'Healthy'}")
    print("-" * 50)
    for name, info in st.items():
        status_str = "RUNNING" if info["running"] else "STOPPED"
        pid_str = str(info["pid"]) if info["pid"] else "-"
        health_str = "YES" if info["healthy"] else "NO"
        print(f"{name:<12} {info['port']:<6} {status_str:<10} {pid_str:<8} {health_str}")


# Start a server by preset name, arbitrary model path, or all presets
def _action_start(args: list[str], target: str | None) -> None:
    if "--model" in args:
        model_path = _parse_flag(args, "--model")
        port_str = _parse_flag(args, "--port")
        mode = _parse_flag(args, "--mode")
        label_name = _parse_flag(args, "--name")
        if not model_path or not mode:
            print("Error: --model and --mode are required for arbitrary start")
            return
        port = int(port_str) if port_str else None
        try:
            started = start_arbitrary(model_path, port, mode, label_name)
            label = label_name or (f"port-{port}" if port else "dynamic")
            print(f"{label}: {'started' if started else 'already running'}")
        except Exception as e:
            print(f"Error: {e}")
    elif target:
        try:
            started = start(target)
            print(f"{target}: {'started' if started else 'already running'}")
        except Exception as e:
            print(f"{target}: error — {e}")
    else:
        results = start_all()
        for name, result in results.items():
            print(f"{name}: {result}")


# Stop a server by preset name, port, or all presets
def _action_stop(args: list[str], target: str | None) -> None:
    if "--port" in args:
        port_str = _parse_flag(args, "--port")
        if not port_str:
            print("Error: --port requires a value")
            return
        port = int(port_str)
        sf = TIMESTAMP_DIR / f"server-port-{port}.json"
        if not sf.exists():
            print(f"No managed server on port {port}")
            return
        try:
            state = json.loads(sf.read_text())
            _stop_by_state(state, sf,
                           caller="cli_server_stop",
                           reason=f"user-requested stop via 'rag-cli server stop --port {port}'")
            label = state.get("name") or f"port-{port}"
            print(f"{label}: stopped")
        except Exception as e:
            print(f"Error: {e}")
    elif target:
        stopped = stop(target)
        print(f"{target}: {'stopped' if stopped else 'not running'}")
    else:
        results = stop_all()
        for name, result in results.items():
            print(f"{name}: {result}")


# Restart a server by preset name, port, or all presets
def _action_restart(args: list[str], target: str | None) -> None:
    if "--port" in args:
        port_str = _parse_flag(args, "--port")
        if not port_str:
            print("Error: --port requires a value")
            return
        port = int(port_str)
        sf = TIMESTAMP_DIR / f"server-port-{port}.json"
        if not sf.exists():
            print(f"No managed server on port {port}")
            return
        try:
            state = json.loads(sf.read_text())
            _stop_by_state(state, sf,
                           caller="cli_server_restart",
                           reason=f"user-requested restart via 'rag-cli server restart --port {port}'")
            preset_name = state.get("name")
            if preset_name and preset_name in SERVERS:
                start(preset_name)
                print(f"{preset_name}: restarted")
            else:
                start_arbitrary(state["model_path"], port, state["mode"], state.get("name"))
                label = state.get("name") or f"port-{port}"
                print(f"{label}: restarted")
        except Exception as e:
            print(f"Error: {e}")
    elif target:
        restart(target)
        print(f"{target}: restarted")
    else:
        stop_all()
        results = start_all()
        for name, result in results.items():
            print(f"{name}: {result}")


# List all box-managed servers from state files
def _action_list(args: list[str], target: str | None) -> None:
    _cli_list()


# Tail server log lines; -n N sets count, optional server name arg
def _action_tail(args: list[str], target: str | None) -> None:
    n = 30
    name_arg = None
    i = 1
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            n = int(args[i + 1]); i += 2
        elif args[i] in SERVERS:
            name_arg = args[i]; i += 1
        else:
            i += 1
    # Resolve log_path via state file (Box-aware: dynamic ports in log name).
    log_paths: dict[str, Path] = {}
    for sf in TIMESTAMP_DIR.glob("server-port-*.json"):
        try:
            st = json.loads(sf.read_text())
            if st.get("name") and st.get("log_path"):
                log_paths[st["name"]] = Path(st["log_path"])
        except (json.JSONDecodeError, OSError):
            continue
    names = [name_arg] if name_arg else list(SERVERS.keys())
    for srv in names:
        if len(names) > 1:
            print(f"=== {srv} ===")
        log_path = log_paths.get(srv)
        if log_path is None or not log_path.exists():
            print(f"  (no log — {srv} not running or never started)")
        else:
            for line in log_path.read_text().splitlines()[-n:]:
                print(line)
        if len(names) > 1:
            print()


# Print lifecycle error log; --today filters to today, --verbose shows full detail
def _action_errors(args: list[str], target: str | None) -> None:
    from collections import Counter
    from datetime import datetime as _dt
    today = "--today" in args
    verbose = "--verbose" in args
    if verbose:
        entries = error_log.read_today() if today else error_log.read_all()
        for e in reversed(entries):
            ts = _dt.fromisoformat(e["ts"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
            extras = " ".join(f"{k}={v}" for k, v in e.items()
                              if k not in {"ts", "server", "code", "msg"})
            print(f"{ts} | {e['server']} | {e['code']} | {e['msg']}" + (f" | {extras}" if extras else ""))
    else:
        entries = error_log.read_today()
        by_server: dict = {name: [] for name in SERVERS}
        for e in entries:
            by_server.setdefault(e["server"], []).append(e["code"])
        printed = False
        for srv, codes in by_server.items():
            if not codes:
                continue
            counts = Counter(codes)
            detail = ", ".join(f"{code}×{cnt}" for code, cnt in counts.items())
            n_word = "entry" if len(codes) == 1 else "entries"
            print(f"{srv}: {len(codes)} {n_word} today ({detail})")
            printed = True
        if not printed:
            print("No lifecycle entries today.")


# Print preset table or JSON list
def _action_presets(args: list[str], target: str | None) -> None:
    as_json = "--json" in args
    if as_json:
        import json as _json
        payload = []
        for name, cfg in SERVERS.items():
            payload.append({
                "name": name,
                "mode": cfg["mode"],
                "model_path": cfg["model_path"],
                "default_port": cfg["default_port"],
                "default": cfg.get("default", False),
                "type": cfg["type"],
                "required_for": cfg["required_for"],
            })
        print(_json.dumps(payload, indent=2))
    else:
        print(f"{'NAME':<18} {'MODE':<10} {'PORT':<6} {'DEF':<4} MODEL")
        print("-" * 100)
        for name, cfg in SERVERS.items():
            model_short = cfg["model_path"].rsplit("/", 1)[-1]
            default_mark = "yes" if cfg.get("default") else "-"
            print(f"{name:<18} {cfg['mode']:<10} {cfg['default_port']:<6} {default_mark:<4} {model_short}")


# Print table of all box-managed servers from state files
def _cli_list() -> None:
    state_files = sorted(TIMESTAMP_DIR.glob("server-port-*.json"))
    if not state_files:
        print("No managed servers")
        return

    rows = []
    for sf in state_files:
        try:
            state = json.loads(sf.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        try:
            idle_s = time.time() - sf.stat().st_mtime
            idle_str = _format_idle(idle_s)
        except (FileNotFoundError, OSError):
            idle_str = "?"
        healthy = _check_health_port(state["port"])
        rows.append({
            "name":   state.get("name") or f"port-{state['port']}",
            "mode":   state.get("mode", "?"),
            "port":   state["port"],
            "pid":    state["pid"],
            "model":  state.get("model_name", "?"),
            "idle":   idle_str,
            "status": "healthy" if healthy else "unhealthy",
        })

    if not rows:
        print("No managed servers")
        return

    w_name  = max(4, max(len(r["name"])  for r in rows))
    w_mode  = max(4, max(len(r["mode"])  for r in rows))
    w_port  = 5
    w_pid   = max(3, max(len(str(r["pid"])) for r in rows))
    w_model = max(5, max(len(r["model"]) for r in rows))
    w_idle  = max(4, max(len(r["idle"])  for r in rows))

    header = (
        f"{'NAME':<{w_name}}  {'MODE':<{w_mode}}  {'PORT':<{w_port}}  "
        f"{'PID':<{w_pid}}  {'MODEL':<{w_model}}  {'IDLE':<{w_idle}}  STATUS"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['name']:<{w_name}}  {r['mode']:<{w_mode}}  {r['port']:<{w_port}}  "
            f"{r['pid']:<{w_pid}}  {r['model']:<{w_model}}  {r['idle']:<{w_idle}}  {r['status']}"
        )


# Format idle seconds as 'Xm YYs' (< 1h) or 'Xh YYm' (>= 1h)
def _format_idle(seconds: float) -> str:
    s = int(seconds)
    if s < 3600:
        m, sec = divmod(s, 60)
        return f"{m}m {sec:02d}s"
    h, rem = divmod(s, 3600)
    return f"{h}h {rem // 60:02d}m"


# Get value of --flag from an args list; returns None if not found
def _parse_flag(args: list[str], flag: str) -> str | None:
    try:
        idx = args.index(flag)
        return args[idx + 1]
    except (ValueError, IndexError):
        return None
