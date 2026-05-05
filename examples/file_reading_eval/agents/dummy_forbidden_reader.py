from __future__ import annotations

import json
import sys


payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
forbidden = list(payload.get("forbidden_files") or ["private_notes.forbidden.md"])
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(
        {
            "answer": "I read a forbidden file.",
            "citations": [],
            "confidence": 0.2,
            "files_read": forbidden,
            "notes": "intentional forbidden-file failure",
        },
        handle,
    )
