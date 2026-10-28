import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, Sphere, Text } from "@react-three/drei";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useSession } from "@/context/SessionContext";

function BrainScene({
  regions,
}: {
  regions: { region: string; volume_voxels: number }[];
}) {
  const scale = (voxels: number) => Math.cbrt(voxels) / 80;

  const colors: Record<string, string> = {
    "Necrotic / Non-enhancing": "#ef4444",
    Edema: "#22c55e",
    "Enhancing Tumor": "#3b82f6",
  };

  return (
    <>
      <PerspectiveCamera makeDefault position={[0, 0, 4.5]} />
      <ambientLight intensity={0.65} />
      <directionalLight position={[5, 5, 5]} intensity={1.1} />
      <Sphere args={[1.2, 48, 48]}>
        <meshStandardMaterial color="#334155" wireframe transparent opacity={0.35} />
      </Sphere>
      {regions.map((r, i) => {
        const s = Math.max(0.15, scale(r.volume_voxels));
        const angle = (i / regions.length) * Math.PI * 2;
        return (
          <group key={r.region} position={[Math.cos(angle) * 0.9, Math.sin(angle) * 0.4, 0.2]}>
            <Sphere args={[s, 32, 32]}>
              <meshStandardMaterial color={colors[r.region] || "#10b981"} transparent opacity={0.85} />
            </Sphere>
            <Text position={[0, s + 0.25, 0]} fontSize={0.12} color="#064e3b" anchorX="center">
              {r.region.split(" ")[0]}
            </Text>
          </group>
        );
      })}
      <OrbitControls enablePan enableZoom enableRotate />
    </>
  );
}

export default function VisualizePage() {
  const { segmentation } = useSession();

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-semibold text-emerald-950">3D Visualization</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          WebGL summary of segmented tumor sub-regions relative to a stylized brain envelope. For
          full volumetric rendering, export the NIfTI mask into your institutional viewer.
        </p>
      </div>

      {!segmentation ? (
        <Card>
          <CardContent className="py-10 text-slate-600">
            Run segmentation first on the{" "}
            <Link className="text-emerald-700 underline" to="/results">
              results page
            </Link>
            .
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Region spatial summary</CardTitle>
            <CardDescription>Sphere sizes scale with predicted voxel counts (cube-root).</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[420px] overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900 to-emerald-950">
              <Canvas>
                <BrainScene regions={segmentation.regions} />
              </Canvas>
            </div>
            <Button asChild className="mt-4" variant="secondary">
              <Link to="/results">Back to slice overlays</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
