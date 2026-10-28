# NeuroScan AI

AI-powered brain tumor MRI segmentation research platform — React + FastAPI + MONAI 3D U-Net.

## Architecture

| Layer | Stack |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn-style UI, React Router, Recharts, React Three Fiber |
| Backend | FastAPI, Uvicorn, Pydantic |
| ML | PyTorch 2.5, MONAI 3D U-Net, NiBabel, SimpleITK, pydicom |
| Metrics | Dice, IoU (per tumor sub-region) |

```
NeuroScan-AI/
├── frontend/          # Web UI
├── backend/           # REST API + file storage
└── ml/                # Training, inference, sample data
```

If `pip install` fails with SSL errors on Windows, use:

```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend\requirements.txt
```

If `npm install` fails with certificate errors:

```powershell
npm install --strict-ssl=false
```

## Quick start

### 1. Python environment & ML bootstrap

```powershell
cd C:\Users\HP\NeuroScan-AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

# Synthetic BraTS-style training volumes
python ml\generate_sample_data.py

# Train 3D U-Net (CPU ok; use GPU if available) — ~5–15 min on CPU for 15 epochs
python ml\train.py --epochs 15
```

### 2. Backend API

```powershell
cd C:\Users\HP\NeuroScan-AI\backend
$env:PYTHONPATH = "C:\Users\HP\NeuroScan-AI"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open API docs: http://127.0.0.1:8000/docs

### 3. Frontend

```powershell
cd C:\Users\HP\NeuroScan-AI\frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

Optional: copy `.env.example` to `.env` and set `VITE_API_URL` if the API is not proxied.

## User workflow

1. **Home** — overview and navigation  
2. **Analyze MRI** — upload `.nii` / `.nii.gz`, multi-file DICOM series (≥4 slices), or **Load local sample MRI**  
3. **Segmentation Results** — run inference, view overlays, download NIfTI mask + text report  
4. **3D Visualization** — WebGL summary of segmented regions  
5. **Model Performance** — Dice/IoU and training curves from `ml/checkpoints/`  
6. **About** — disclaimers and stack notes  

## DICOM notes

- Upload an entire series folder (multiple `.dcm` files), not a single slice.  
- The API lists detected series; select one to convert to NIfTI via SimpleITK before segmentation.

## Deployment

- **Frontend**: `npm run build` → static files in `frontend/dist` (nginx, Vercel, etc.)  
- **Backend**: run Uvicorn behind a reverse proxy; set `CORS_ORIGINS` in `backend/app/core/config.py`  
- **GPU**: install CUDA-enabled PyTorch wheel if needed; inference falls back to CPU automatically  

## Evaluation pipeline

```powershell
python ml\generate_sample_data.py --count 8
python ml\train.py --data backend\data\sample --epochs 20
```

Metrics are written to `ml/checkpoints/checkpoint_meta.json` and `training_history.json`.

## Medical disclaimer

Research and education only — **not** for clinical diagnosis or treatment.

## License

Academic project — add your institution's license as required.
