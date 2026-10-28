import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 text-left">
      <h1 className="text-3xl font-semibold text-emerald-950">About NeuroScan AI</h1>
      <p className="leading-relaxed text-slate-600">
        NeuroScan AI is an academic research prototype demonstrating an end-to-end workflow for brain
        tumor MRI segmentation: ingestion of NIfTI and DICOM studies, deep learning inference with a
        MONAI 3D U-Net, interactive review, and reproducible training/evaluation scripts.
      </p>
      <Card>
        <CardHeader>
          <CardTitle>Medical disclaimer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-700">
          <p>
            This software is not a medical device. Outputs may be inaccurate, especially when using
            untrained weights or out-of-distribution data. Do not use for diagnosis, staging, or
            treatment planning.
          </p>
          <p>
            Synthetic and sample volumes are provided for demonstration. Replace with properly licensed
            clinical datasets under IRB-approved protocols for real research.
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Credits & stack</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-700">
          Built with React, FastAPI, PyTorch, MONAI, NiBabel, SimpleITK, and React Three Fiber. Slice
          viewing uses server-rendered PNG previews; integrate Cornerstone3D or Niivue for full DICOM
          hanging protocols in production deployments.
        </CardContent>
      </Card>
    </div>
  );
}
