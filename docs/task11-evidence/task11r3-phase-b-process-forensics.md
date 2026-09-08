# Task 11R-3 Phase B — Process Forensics

```text
ORIGINAL_APP_SERVER_PID = 60504
PROCESS_NAME = codex.exe
EXECUTABLE_PATH = C:\Users\KSH\.codex\plugins\.plugin-appserver\codex.exe
PARENT_PID = 69196
START_TIME = 2026-09-06 18:58:36 +09:00
SESSION_ID = 1
COMMAND_LINE = app-server -- analytics-default-enabled ...
```

PID `60504` is a Codex app-server, not an arbitrary `codex.exe`. A read-only
WMI process snapshot also showed JDIPT children running
`scripts/jdipt_runtime_mcp.py` under PID `60504` (including processes started
at 22:41:31 and 22:55:32). The process is therefore `RELATED_CONFIRMED` as a
runtime host, but this does not by itself prove that it owns a cache handle.

The active cache target was:

```text
C:\Users\KSH\.codex\plugins\cache\sage1993\jdipt\0.2.4
```

No unrelated process was terminated. The current app-server was not stopped
because it is the host of the live verification session and its cache-handle
ownership was not proven.

