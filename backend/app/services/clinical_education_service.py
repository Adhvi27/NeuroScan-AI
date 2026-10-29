"""Build learning, risk, and treatment education from analysis outputs."""

from __future__ import annotations

from app.services.application_catalog import APPLICATION_CATALOG, MriApplication


def _risk_level(spatial: dict, confidence: float, app: str) -> dict:
    vol = spatial.get("tumor_volume_cm3") or 0.0
    detected = spatial.get("tumor_detected", False)

    if not detected or vol < 0.5:
        score = 0.15
        level = "low"
        label = "Low (educational)"
    elif vol < 5:
        score = 0.35 + confidence * 0.2
        level = "moderate"
        label = "Moderate (educational)"
    elif vol < 15:
        score = 0.55 + confidence * 0.25
        level = "elevated"
        label = "Elevated (educational)"
    else:
        score = min(0.95, 0.7 + confidence * 0.25)
        level = "high"
        label = "High (educational)"

    app_mod = {
        MriApplication.stroke.value: 0.12,
        MriApplication.cardiac.value: 0.08,
    }.get(app, 0.0)
    score = min(0.98, score + app_mod)

    drivers = []
    if detected:
        drivers.append(f"Segmented abnormal volume ≈ {vol} cm³ in this scan.")
    drivers.append(f"Model confidence (educational proxy): {confidence * 100:.1f}%.")
    if spatial.get("affected_region"):
        drivers.append(f"Predominant location context: {spatial['affected_region']}.")

    return {
        "level": level,
        "label": label,
        "score": round(score, 3),
        "drivers": drivers,
        "disclaimer": (
            "Risk level is a teaching heuristic from segmentation geometry — not a clinical "
            "prognosis. Only qualified clinicians can assess patient risk."
        ),
    }


def _learning_from_analysis(
    app: str,
    spatial: dict,
    regions: list[dict],
    class_probabilities: list[dict],
) -> dict:
    profile = APPLICATION_CATALOG.get(app, APPLICATION_CATALOG[MriApplication.brain_tumor.value])
    bullets: list[str] = []

    bullets.append(
        f"Application lens: **{profile['title']}** — {profile['description']}"
    )
    if spatial.get("tumor_detected"):
        bullets.append(
            f"Your upload shows a segmented region of ≈ {spatial.get('tumor_volume_cm3', 0)} cm³ "
            f"with center near voxel {', '.join(str(int(x)) for x in (spatial.get('center_voxel') or [])[:3])}."
        )
    else:
        bullets.append("No substantial abnormal region was segmented in this volume (under current model).")

    pathology_regions = [r for r in regions if r.get("kind") != "non_tumor" and r.get("label_id", -1) != 0]
    top_region = max(pathology_regions, key=lambda r: r.get("volume_voxels", 0), default=None)
    if top_region and top_region.get("volume_voxels", 0) > 0:
        bullets.append(
            f"Largest predicted sub-region: {top_region['region']} "
            f"({top_region['volume_voxels']:,} voxels)."
        )

    if class_probabilities:
        top = max(class_probabilities, key=lambda c: c.get("probability", 0))
        bullets.append(
            f"Highest educational class probability: {top['label']} ({top['probability']:.2f}) — "
            "compare with radiology ground truth in real datasets."
        )

    app_specific = _app_learning_snippets(app, spatial)
    bullets.extend(app_specific)

    concepts = _concepts_for_app(app)

    return {
        "summary": f"Personalized learning generated from your {profile['title']} analysis.",
        "key_findings": bullets,
        "concepts_to_study": concepts,
    }


def _app_learning_snippets(app: str, spatial: dict) -> list[str]:
    region = spatial.get("affected_region") or "the imaged anatomy"
    snippets: dict[str, list[str]] = {
        MriApplication.brain_tumor.value: [
            "BraTS labels separate edema from enhancing tumor — notice color overlays in results.",
            "Tumor volume trends matter for treatment planning studies (research context).",
        ],
        MriApplication.stroke.value: [
            "Stroke imaging often pairs DWI (restricted diffusion) with ADC maps — this demo uses structural overlap only.",
            f"Lesion location ({region}) would guide vascular territory teaching in a full PACS workflow.",
        ],
        MriApplication.multiple_sclerosis.value: [
            "MS teaching emphasizes lesion count, location (periventricular, juxtacortical), and enhancement.",
            "Compare your segmented volume to dissemination-in-space criteria in coursework.",
        ],
        MriApplication.neurodegenerative.value: [
            "Atrophy and hippocampal volume are key — segmentation here proxies focal abnormality for lab exercises.",
            "Link structural findings to cognitive staging only in supervised clinical training.",
        ],
        MriApplication.spinal.value: [
            "Spinal MRI labs focus on T2 hyperintensity, cord compression, and disc herniation levels.",
            "Relate bounding-box center to vertebral level when using annotated datasets.",
        ],
        MriApplication.musculoskeletal.value: [
            "MSK MRI teaches tear grades (meniscus, ACL) and bone marrow edema patterns.",
            "Volume metrics here stand in for focal pathology size in student reports.",
        ],
        MriApplication.abdominal.value: [
            "LI-RADS and organ-specific criteria apply in hepatobiliary imaging courses.",
            "Use segmentation size to practice lesion categorization homework (not diagnosis).",
        ],
        MriApplication.cardiac.value: [
            "Cardiac MRI combines cine function, LGE scar, and T1 mapping — extend this platform with cine stacks later.",
            "Scar burden correlates with arrhythmia risk in research literature — not computed clinically here.",
        ],
    }
    default = [
        f"Typical sequences for this module: {', '.join(APPLICATION_CATALOG.get(app, {}).get('typical_sequences', ['T1', 'T2'])[:4])}.",
        "Segmentation output supports lab measurements — validate against course rubrics.",
    ]
    return snippets.get(app, default)


def _concepts_for_app(app: str) -> list[str]:
    common = ["MRI signal basics (T1, T2, FLAIR)", "Voxel geometry and NIfTI headers", "AI segmentation metrics (Dice, IoU)"]
    extra: dict[str, list[str]] = {
        MriApplication.brain_tumor.value: ["BraTS regions", "3D U-Net", "Radiotherapy target volumes"],
        MriApplication.stroke.value: ["DWI/ADC", "Penumbra", "ASPECTS scoring (concept)"],
        MriApplication.multiple_sclerosis.value: ["McDonald criteria", "DMT classes (overview)"],
        MriApplication.neurodegenerative.value: ["Hippocampal atrophy", "PET amyloid (companion modality)"],
        MriApplication.spinal.value: ["Cord signal", "Stenosis grades"],
        MriApplication.musculoskeletal.value: ["Meniscus zones", "ACL tear patterns"],
        MriApplication.abdominal.value: ["HCC screening", "Renal mass Bosniak (concept)"],
        MriApplication.cardiac.value: ["LVEF", "Late gadolinium enhancement"],
    }
    return common + extra.get(app, APPLICATION_CATALOG.get(app, {}).get("learning_goals", []))


def _treatment_education(app: str, risk: dict) -> dict:
    level = risk["level"]
    options: dict[str, list[dict]] = {
        MriApplication.brain_tumor.value: [
            {"name": "Maximal safe resection", "notes": "Often discussed for accessible gliomas (teaching)."},
            {"name": "Radiotherapy + temozolomide", "notes": "Standard teaching pathway for high-grade glioma protocols."},
            {"name": "Clinical trial enrollment", "notes": "Consider in academic centers for recurrent disease."},
        ],
        MriApplication.stroke.value: [
            {"name": "Thrombolysis / thrombectomy window", "notes": "Time-critical; imaging gates eligibility (concept)."},
            {"name": "Antiplatelet / anticoagulation", "notes": "Depends on stroke subtype — not inferable from demo AI."},
            {"name": "Rehabilitation", "notes": "Functional recovery planning."},
        ],
        MriApplication.multiple_sclerosis.value: [
            {"name": "Disease-modifying therapies", "notes": "Injectable, oral, or infusion options in curricula."},
            {"name": "Steroids for relapses", "notes": "Short-course for acute inflammatory events."},
            {"name": "Symptom management", "notes": "Fatigue, spasticity, neuro rehab."},
        ],
        MriApplication.neurodegenerative.value: [
            {"name": "Cholinesterase inhibitors / memantine", "notes": "Alzheimer spectrum teaching."},
            {"name": "Lifestyle & cognitive rehab", "notes": "Exercise, sleep, cardiovascular risk control."},
            {"name": "Caregiver planning", "notes": "Multidisciplinary support."},
        ],
        MriApplication.spinal.value: [
            {"name": "Conservative care", "notes": "PT, NSAIDs, activity modification."},
            {"name": "Surgical decompression", "notes": "When cord compression or progressive deficit (concept)."},
            {"name": "Pain management", "notes": "Multimodal approaches."},
        ],
        MriApplication.musculoskeletal.value: [
            {"name": "Physical therapy", "notes": "First-line for many meniscal/ligament grades."},
            {"name": "Arthroscopy / reconstruction", "notes": "Taught for ACL and repairable meniscus tears."},
            {"name": "Injection therapies", "notes": "Teaching overview only."},
        ],
        MriApplication.abdominal.value: [
            {"name": "Ablation / resection", "notes": "Liver lesion pathways in oncology courses."},
            {"name": "Systemic therapy", "notes": "When unresectable (overview)."},
            {"name": "Surveillance imaging", "notes": "Interval MRI/US protocols."},
        ],
        MriApplication.cardiac.value: [
            {"name": "Guideline-directed medical therapy", "notes": "Heart failure teaching blocks."},
            {"name": "Catheter ablation / ICD", "notes": "Arrhythmia risk linkage to scar (concept)."},
            {"name": "Revascularization", "notes": "When ischemic cardiomyopathy suspected."},
        ],
    }

    base = options.get(app)
    if not base:
        base = [
            {"name": "Multidisciplinary review", "notes": "Tumor board / specialty clinic (teaching simulation)."},
            {"name": "Guideline-based therapy", "notes": "Match to organ-specific curriculum pathways."},
            {"name": "Follow-up imaging", "notes": "Practice interval and modality selection in case reports."},
        ]
    if level in ("elevated", "high"):
        urgency = (
            "Elevated educational risk score: coursework should emphasize expedited specialist referral "
            "and multidisciplinary tumor board discussion (simulation only)."
        )
    elif level == "moderate":
        urgency = "Moderate score: practice writing an imaging follow-up plan and differential diagnosis list."
    else:
        urgency = "Lower score: focus on documentation, differential breadth, and when to escalate imaging."

    return {
        "urgency_note": urgency,
        "options": base,
        "disclaimer": (
            "Treatment options are generic educational summaries from medical curricula — NOT recommendations "
            "for this patient or scan. Real decisions require licensed clinicians and full clinical data."
        ),
    }


def build_clinical_education_package(
    application_type: str,
    spatial: dict,
    regions: list[dict],
    class_probabilities: list[dict],
) -> dict:
    app = application_type if application_type in APPLICATION_CATALOG else MriApplication.brain_tumor.value
    confidence = float(spatial.get("confidence") or 0.0)
    risk = _risk_level(spatial, confidence, app)
    learning = _learning_from_analysis(app, spatial, regions, class_probabilities)
    treatment = _treatment_education(app, risk)
    profile = APPLICATION_CATALOG[app]

    return {
        "application_id": app,
        "application_title": profile["title"],
        "learning": learning,
        "risk": risk,
        "treatment": treatment,
    }
