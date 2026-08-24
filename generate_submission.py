import json
from pathlib import Path
from engine.context_store import store
from engine.composer import composer

DATASET_DIR = Path("dataset")

def run():
    print("Loading dataset into store...")
    cat_dir = DATASET_DIR / "categories"
    if cat_dir.exists():
        for f in cat_dir.glob("*.json"):
            data = json.load(open(f, encoding="utf-8"))
            store.push_context("category", data.get("slug", f.stem), 1, data)

    for name, scope, key in [
        ("merchants_seed.json", "merchant", "merchant_id"),
        ("customers_seed.json", "customer", "customer_id"),
        ("triggers_seed.json", "trigger", "id")
    ]:
        path = DATASET_DIR / name
        if path.exists():
            data = json.load(open(path, encoding="utf-8"))
            items = data.get(scope + "s", data.get(scope, []))
            for it in items:
                if key in it:
                    store.push_context(scope, it[key], 1, it)

    triggers = store.get_all_by_scope("trigger")
    print(f"Generating submission for {len(triggers)} triggers...")

    output_lines = []
    for i, (tid, trg) in enumerate(triggers.items(), 1):
        mid = trg.get("merchant_id")
        cid = trg.get("customer_id")
        merchant = store.get_context("merchant", mid) if mid else None
        if not merchant:
            continue
        category = store.get_context("category", merchant.get("category_slug"))
        customer = store.get_context("customer", cid) if cid else None

        composed = composer.compose(category, merchant, trg, customer)
        line = {
            "test_id": f"T{i:02d}",
            "trigger_id": tid,
            "merchant_id": mid,
            "customer_id": cid,
            "body": composed["body"],
            "cta": composed["cta"],
            "send_as": composed["send_as"],
            "suppression_key": composed["suppression_key"],
            "rationale": composed["rationale"]
        }
        output_lines.append(line)

    with open("submission.jsonl", "w", encoding="utf-8") as f:
        for item in output_lines:
            f.write(json.dumps(item) + "\n")

    print(f"Successfully generated submission.jsonl with {len(output_lines)} test lines.")

if __name__ == "__main__":
    run()
