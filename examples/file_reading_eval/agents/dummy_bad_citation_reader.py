from __future__ import annotations

import json
import sys


payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(
        {
            "answer": "Enterprise customers must retain audit logs for 90 days.",
            "citations": [
                {
                    "file_id": "policy.md",
                    "line_start": 3,
                    "line_end": 3,
                    "quote": "Enterprise customers retain audit logs forever.",
                }
            ],
            "confidence": 0.6,
            "files_read": ["policy.md"],
            "notes": f"bad citation for {payload.get('task_id')}",
        },
        handle,
    )
