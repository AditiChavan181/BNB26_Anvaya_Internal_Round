import json

import c2pa

FILE_PATH = "../sample-assets/trusted/signed.jpg"

with c2pa.Reader(FILE_PATH) as reader:
    print("\n========== C2PA JSON ==========\n")

    manifest_store = json.loads(reader.json())
    print(json.dumps(manifest_store, indent=2))

    print("\n========== VALIDATION STATE ==========\n")
    print(reader.get_validation_state())

    print("\n========== VALIDATION RESULTS ==========\n")

    try:
        print(
            json.dumps(
                reader.get_validation_results(),
                indent=2,
                default=str,
            )
        )
    except Exception as exc:
        print(
            "Could not read validation results:",
            exc,
        )