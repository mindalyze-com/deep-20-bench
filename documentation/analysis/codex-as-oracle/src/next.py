"""Wait briefly for the next direct decision without exposing Guesser reasoning."""
import argparse
import json
import time

import bridge

parser = argparse.ArgumentParser()
parser.add_argument("--after", type=int, default=0)
args = parser.parse_args()
end = time.monotonic() + 45
while time.monotonic() < end:
    path = bridge.ROOT / "work/pending.json"
    if path.exists():
        work = bridge.WORK.validate_json(path.read_text())
        if work.sequence > args.after:
            payload = json.loads(work.request.messages[1]["content"].split("\n", 1)[1])
            print(json.dumps({"sequence": work.sequence, "kind": work.kind,
                "request_hash": work.request_hash,
                "context": work.context.model_dump(),
                "question": payload.get("current_yes_no_question"),
                "guess": payload.get("proposed_identity")}, ensure_ascii=False))
            break
    time.sleep(0.2)
else:
    print(json.dumps({"status": "no_new_pending_decision"}))
