"""Medical Segmentation Decathlon (MSD) task registry — public multi-organ training targets."""

from __future__ import annotations

from dataclasses import dataclass

# Official MSD release base (user must accept MSD terms when downloading)
MSD_RELEASE_BASE = "https://msd.csail.mit.edu/releases"

MSD_TASKS: dict[str, dict] = {
    "Task01_BrainTumour": {
        "organ": "Brain tumour",
        "out_channels": 4,
        "regions": {1: "Necrotic core", 2: "Edema", 3: "Enhancing tumour"},
    },
    "Task02_Heart": {
        "organ": "Heart",
        "out_channels": 2,
        "regions": {1: "Left atrium"},
    },
    "Task03_Liver": {
        "organ": "Liver",
        "out_channels": 2,
        "regions": {1: "Liver"},
    },
    "Task04_Hippocampus": {
        "organ": "Hippocampus",
        "out_channels": 2,
        "regions": {1: "Hippocampus"},
    },
    "Task05_Prostate": {
        "organ": "Prostate",
        "out_channels": 2,
        "regions": {1: "Prostate peripheral zone"},
    },
    "Task06_Lung": {
        "organ": "Lung",
        "out_channels": 2,
        "regions": {1: "Lung cancer / nodule"},
    },
    "Task07_Pancreas": {
        "organ": "Pancreas",
        "out_channels": 2,
        "regions": {1: "Pancreas"},
    },
    "Task08_HepaticVessel": {
        "organ": "Hepatic vessel",
        "out_channels": 2,
        "regions": {1: "Hepatic vessel"},
    },
    "Task09_Spleen": {
        "organ": "Spleen",
        "out_channels": 2,
        "regions": {1: "Spleen"},
    },
    "Task10_Colon": {
        "organ": "Colon",
        "out_channels": 2,
        "regions": {1: "Colon cancer primaries"},
    },
}


@dataclass(frozen=True)
class MsdTaskSpec:
    task_id: str
    model_id: str
    checkpoint_name: str
    display_name: str
    out_channels: int
    region_names: dict[int, str]
    anatomy_mode: str


def _spec(task_id: str, anatomy_mode: str = "body") -> MsdTaskSpec:
    meta = MSD_TASKS[task_id]
    slug = task_id.lower().replace("task", "task")
    model_id = f"msd_{slug}"
    return MsdTaskSpec(
        task_id=task_id,
        model_id=model_id,
        checkpoint_name=f"{model_id}.pt",
        display_name=f"MSD {meta['organ']} U-Net",
        out_channels=meta["out_channels"],
        region_names=dict(meta["regions"]),
        anatomy_mode=anatomy_mode,
    )


MSD_MODELS: dict[str, MsdTaskSpec] = {
    t: _spec(t, "neuro" if t == "Task01_BrainTumour" else "body") for t in MSD_TASKS
}

# Primary MSD checkpoint per MRI application module
APPLICATION_MSD_TASK: dict[str, str] = {
    "brain_tumor": "Task01_BrainTumour",
    "stroke": "Task01_BrainTumour",
    "multiple_sclerosis": "Task01_BrainTumour",
    "pediatric_neuro": "Task01_BrainTumour",
    "vascular_mra": "Task06_Lung",
    "head_neck": "Task01_BrainTumour",
    "ent_sinus": "Task01_BrainTumour",
    "neurodegenerative": "Task04_Hippocampus",
    "cardiac": "Task02_Heart",
    "abdominal": "Task03_Liver",
    "breast": "Task06_Lung",
    "prostate": "Task05_Prostate",
    "pelvic": "Task05_Prostate",
    "musculoskeletal": "Task10_Colon",
    "spinal": "Task10_Colon",
}


def msd_task_for_application(application_type: str) -> MsdTaskSpec | None:
    task_id = APPLICATION_MSD_TASK.get(application_type)
    if not task_id:
        return None
    return MSD_MODELS.get(task_id)


def msd_data_dir(root: str | None, task_id: str) -> str:
    from pathlib import Path

    base = Path(root or "backend/data/msd")
    return str(base / task_id)
