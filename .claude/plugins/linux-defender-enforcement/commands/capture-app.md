---
description: Capture and inspect the real Tauri/WebKitGTK app window for visual bugs.
---

Focus the Linux Defender Tauri window, then run:

```bash
bash ${CLAUDE_PROJECT_DIR}/scripts/capture-app-window.sh
```

Read the saved PNG with the image-capable read tool and inspect the real
WebKitGTK rendering. Compare with the browser visual harness at
`${CLAUDE_PROJECT_DIR}/desktop/visual-harness.html` only as a secondary check:
Chromium is not WebKitGTK. Report any visual or accessibility difference and
fix it with a regression check so it cannot recur.
