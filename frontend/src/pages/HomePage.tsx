import { Link } from "react-router-dom";
import {
  Activity,
  Box,
  BrainCircuit,
  FileText,
  Layers,
  Microscope,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    icon: BrainCircuit,
    title: "3D U-Net Segmentation",
    text: "MONAI-powered volumetric inference with necrotic core, edema, and enhancing tumor labels.",
  },
  {
    icon: Layers,
    title: "Multi-planar Review",
    text: "Axial slice previews with color-coded overlays for rapid qualitative assessment.",
  },
  {
    icon: Box,
    title: "3D Tumor Context",
    text: "Interactive WebGL scene summarizing segmented regions in spatial context.",
  },
  {
    icon: Activity,
    title: "Model Evaluation",
    text: "Dice and IoU tracking on synthetic validation data with reproducible training scripts.",
  },
  {
    icon: FileText,
    title: "Downloadable Reports",
    text: "Export plain-text summaries with inference timing and region volumes.",
  },
  {
    icon: ShieldAlert,
    title: "Research Safeguards",
    text: "Clear non-clinical disclaimers and validation workflows for academic use.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="grid items-center gap-10 lg:grid-cols-2">
        <div className="space-y-6 text-left">
          <p className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">
            Brain MRI Research Platform
          </p>
          <h1 className="text-4xl font-semibold leading-tight text-emerald-950 md:text-5xl">
            AI-Powered Brain Tumor Segmentation
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-slate-600">
            NeuroScan AI is a college-level research prototype for uploading brain MRI volumes,
            running 3D deep learning segmentation, exploring results interactively, and evaluating
            model performance with standard metrics.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/analyze">Analyze MRI</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link to="/performance">Explore Model</Link>
            </Button>
          </div>
        </div>
        <div className="relative overflow-hidden rounded-3xl border border-emerald-100 bg-gradient-to-br from-emerald-900 via-emerald-800 to-teal-900 p-8 shadow-2xl">
          <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-emerald-400/20 blur-2xl" />
          <div className="relative mx-auto flex max-w-sm flex-col items-center gap-4 text-emerald-50">
            <div className="grid grid-cols-3 gap-2 rounded-2xl bg-emerald-950/40 p-4 ring-1 ring-emerald-400/20">
              {Array.from({ length: 9 }).map((_, i) => (
                <div
                  key={i}
                  className="aspect-square rounded-lg bg-gradient-to-br from-slate-700 via-slate-600 to-emerald-700/80"
                  style={{ opacity: 0.45 + (i % 3) * 0.15 }}
                />
              ))}
            </div>
            <p className="text-center text-sm text-emerald-100/90">
              Illustrative MRI grid — replace with your institution&apos;s licensed data in production.
            </p>
            <Microscope className="h-10 w-10 text-emerald-300" />
          </div>
        </div>
      </section>

      <section className="space-y-6">
        <h2 className="text-left text-2xl font-semibold text-emerald-950">Platform capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title} className="text-left">
              <CardHeader>
                <f.icon className="mb-2 h-8 w-8 text-emerald-600" />
                <CardTitle>{f.title}</CardTitle>
                <CardDescription>{f.text}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-6 rounded-3xl border border-emerald-100 bg-white p-8 shadow-sm lg:grid-cols-2">
        <div className="text-left">
          <h2 className="text-2xl font-semibold text-emerald-950">Workflow</h2>
          <ol className="mt-4 space-y-3 text-slate-600">
            <li>1. Upload NIfTI or a complete DICOM series (or load bundled sample data).</li>
            <li>2. Validate metadata and preview axial slices.</li>
            <li>3. Run MONAI 3D U-Net segmentation on CPU or GPU.</li>
            <li>4. Review overlays, 3D summary, metrics, and download the report.</li>
          </ol>
        </div>
        <div className="text-left">
          <h2 className="text-2xl font-semibold text-emerald-950">Technology stack</h2>
          <CardContent className="mt-4 grid grid-cols-2 gap-2 p-0 text-sm text-slate-700">
            <span>React + TypeScript + Vite</span>
            <span>Tailwind CSS + shadcn-style UI</span>
            <span>FastAPI + Uvicorn</span>
            <span>PyTorch + MONAI 3D U-Net</span>
            <span>NiBabel / SimpleITK / pydicom</span>
            <span>React Three Fiber</span>
          </CardContent>
        </div>
      </section>
    </div>
  );
}
