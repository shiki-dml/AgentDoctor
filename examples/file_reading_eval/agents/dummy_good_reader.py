from __future__ import annotations

import json
import sys


def main() -> int:
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    payload = json.loads(open(input_path, encoding="utf-8").read())
    task_id = payload.get("task_id", "")
    if "unanswerable" in task_id:
        answer = "Insufficient evidence in the allowed corpus."
        citations = []
        files_read = []
    elif "release" in task_id:
        answer = "Version 2 adds offline export and stricter citation checks."
        citations = [
            {
                "file_id": "release_notes_v2.md",
                "line_start": 3,
                "line_end": 3,
                "quote": "Adds offline export and stricter citation checks.",
            }
        ]
        files_read = ["release_notes_v2.md"]
    else:
        answer = "Enterprise customers must retain audit logs for 90 days."
        citations = [
            {
                "file_id": "policy.md",
                "line_start": 3,
                "line_end": 3,
                "quote": "Enterprise customers must retain audit logs for 90 days.",
            }
        ]
        files_read = ["policy.md"]
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "answer": answer,
                "citations": citations,
                "confidence": 0.9,
                "files_read": files_read,
                "notes": "deterministic dummy",
            },
            handle,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
