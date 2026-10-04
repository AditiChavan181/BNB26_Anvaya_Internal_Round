from app.services.provenance import analyze_provenance
from app.services.hash_service import calculate_sha256


file_path = "../sample-assets/trusted/signed.jpg"

provenance = analyze_provenance(file_path)
file_hash = calculate_sha256(file_path)

print("PROVENANCE")
print(provenance)

print("\nSHA-256")
print(file_hash)