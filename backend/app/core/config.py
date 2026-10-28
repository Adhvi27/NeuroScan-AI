from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
SAMPLE_DIR = DATA_DIR / "sample"
CHECKPOINT_DIR = BASE_DIR.parent / "ml" / "checkpoints"

for d in (UPLOAD_DIR, RESULTS_DIR, SAMPLE_DIR, CHECKPOINT_DIR):
    d.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 512 * 1024 * 1024  # 512 MB
ALLOWED_NIFTI = {".nii", ".gz"}
DEFAULT_CHECKPOINT = CHECKPOINT_DIR / "best.pt"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
