"""MRI application profiles and educational framing (research / teaching only)."""

from __future__ import annotations

from enum import Enum


class MriApplication(str, Enum):
    brain_tumor = "brain_tumor"
    stroke = "stroke"
    multiple_sclerosis = "multiple_sclerosis"
    neurodegenerative = "neurodegenerative"
    spinal = "spinal"
    musculoskeletal = "musculoskeletal"
    abdominal = "abdominal"
    cardiac = "cardiac"
    breast = "breast"
    prostate = "prostate"
    pelvic = "pelvic"
    head_neck = "head_neck"
    vascular_mra = "vascular_mra"
    pediatric_neuro = "pediatric_neuro"
    ENT_sinus = "ent_sinus"


def _entry(
    title: str,
    description: str,
    focus: str,
    category: str,
    sequences: list[str],
    learning_goals: list[str],
) -> dict:
    return {
        "title": title,
        "description": description,
        "focus": focus,
        "category": category,
        "typical_sequences": sequences,
        "learning_goals": learning_goals,
    }


APPLICATION_CATALOG: dict[str, dict] = {
    MriApplication.brain_tumor.value: _entry(
        "Brain Tumor MRI",
        "Glioma and metastasis workup with multi-class segmentation (necrosis, edema, enhancing tumor).",
        "oncology neuroimaging",
        "Neuro · Oncology",
        ["T1", "T2", "FLAIR", "T1 post-contrast"],
        ["BraTS labels", "Tumor volumes", "Treatment planning concepts"],
    ),
    MriApplication.stroke.value: _entry(
        "Stroke / Cerebrovascular MRI",
        "Acute infarct, hemorrhage, and territorial perfusion teaching.",
        "acute neuro emergency",
        "Neuro · Vascular",
        ["DWI", "ADC", "FLAIR", "GRE/SWI"],
        ["DWI restriction", "Penumbra", "ASPECTS (concept)"],
    ),
    MriApplication.multiple_sclerosis.value: _entry(
        "Multiple Sclerosis (MS) MRI",
        "Demyelinating plaque burden and McDonald criteria coursework.",
        "demyelinating disease",
        "Neuro · Inflammatory",
        ["FLAIR", "T2", "T1 post-contrast"],
        ["DIS", "DMT overview", "Lesion counting"],
    ),
    MriApplication.neurodegenerative.value: _entry(
        "Neurodegenerative MRI",
        "Atrophy patterns in Alzheimer and Parkinson spectrum teaching.",
        "structural neurodegeneration",
        "Neuro · Degenerative",
        ["T1", "FLAIR", "Hippocampal T2"],
        ["Atrophy scales", "Hippocampal volume (concept)"],
    ),
    MriApplication.pediatric_neuro.value: _entry(
        "Pediatric Neuro MRI",
        "Developmental anomalies, posterior fossa tumors, and myelination courses.",
        "pediatric imaging",
        "Neuro · Pediatric",
        ["T1", "T2", "FLAIR", "DWI"],
        ["Myelination timeline", "Posterior fossa anatomy"],
    ),
    MriApplication.spinal.value: _entry(
        "Spinal MRI",
        "Cord compression, disc herniation, stenosis, and syrinx basics.",
        "spine",
        "Spine",
        ["T2 sagittal", "T1 axial", "STIR"],
        ["Canal stenosis", "Cord signal", "Disc levels"],
    ),
    MriApplication.musculoskeletal.value: _entry(
        "Musculoskeletal MRI",
        "Knee, shoulder, and ankle — ligament, meniscus, cartilage.",
        "MSK",
        "Musculoskeletal",
        ["PD", "T2 FS", "T1"],
        ["Meniscus zones", "ACL tear grades"],
    ),
    MriApplication.abdominal.value: _entry(
        "Abdominal MRI",
        "Hepatobiliary, renal, and pancreatic lesion characterization.",
        "body imaging",
        "Body",
        ["T1 in/out phase", "T2", "DWI", "MRCP"],
        ["LI-RADS intro", "Renal mass Bosniak (concept)"],
    ),
    MriApplication.cardiac.value: _entry(
        "Cardiac MRI",
        "Ventricular function, scar (LGE), and cardiomyopathy teaching.",
        "cardiovascular",
        "Cardiac",
        ["Cine SSFP", "LGE", "T1 mapping"],
        ["LVEF", "Scar transmurality"],
    ),
    MriApplication.breast.value: _entry(
        "Breast MRI",
        "High-risk screening, lesion morphology, and kinetic curve basics.",
        "breast oncology",
        "Breast",
        ["T1 post-contrast", "DWI"],
        ["BI-RADS MRI", "Kinetics (concept)"],
    ),
    MriApplication.prostate.value: _entry(
        "Prostate MRI",
        "PI-RADS workflow and zone anatomy (peripheral vs transition).",
        "urologic oncology",
        "Prostate",
        ["T2", "DWI", "ADC", "DCE"],
        ["PI-RADS scoring intro", "Zone anatomy"],
    ),
    MriApplication.pelvic.value: _entry(
        "Pelvic MRI",
        "Gynecologic staging, fibroids, and rectal cancer depth teaching.",
        "pelvic imaging",
        "Pelvic",
        ["T2", "DWI", "T1 post-contrast"],
        ["FIGO staging (concept)", "CRM for rectal CA"],
    ),
    MriApplication.head_neck.value: _entry(
        "Head & Neck MRI",
        "Squamous cell staging, nodal levels, and skull base anatomy.",
        "H&N oncology",
        "Head & Neck",
        ["T1", "T2 FS", "post-contrast fat-suppressed"],
        ["Nodal levels", "Perineural spread (concept)"],
    ),
    MriApplication.vascular_mra.value: _entry(
        "MR Angiography (MRA)",
        "Intracranial and peripheral vessel stenosis, aneurysm search.",
        "vascular",
        "Vascular",
        ["TOF MRA", "Contrast MRA"],
        ["Stenosis grading", "Aneurysm neck (concept)"],
    ),
    MriApplication.ENT_sinus.value: _entry(
        "Sinuses & ENT MRI",
        "Rhinosinusitis, skull base, and inner ear / IAC courses.",
        "ENT",
        "ENT",
        ["T1", "T2", "FLAIR"],
        ["Lund-Mackay (concept)", "IAC anatomy"],
    ),
}


def list_applications() -> list[dict]:
    return [{"id": key, **value} for key, value in APPLICATION_CATALOG.items()]


def get_application(app_id: str) -> dict | None:
    if app_id not in APPLICATION_CATALOG:
        return None
    return {"id": app_id, **APPLICATION_CATALOG[app_id]}
