"""Package existing reviewed sources without regenerating configuration/UI files."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from documentation import check as check_documentation

check_documentation()

root = Path(__file__).resolve().parent
component = root / "custom_components/desk_booking"
files = sorted(p for p in component.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
dist = root / "dist"
dist.mkdir(exist_ok=True)
version = json.loads((component / "manifest.json").read_text(encoding="utf-8"))["version"]
target = dist / f"desk-booking-{version}.zip"
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, path.relative_to(root).as_posix())
manifest = {p.relative_to(component).as_posix(): sha256(p.read_bytes()).hexdigest() for p in files}
(dist / f"desk-booking-{version}.sha256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Packaged {len(files)} files: {target.name}")
print(f"SHA256 {sha256(target.read_bytes()).hexdigest()}")
