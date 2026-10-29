import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, MeshDistortMaterial, OrbitControls, PerspectiveCamera } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import * as THREE from "three";

export type SpatialData = {
  tumor_detected?: boolean;
  confidence?: number;
  center_normalized?: number[];
  tumor_volume_cm3?: number;
  surface_area_cm2?: number;
  bounding_box_voxel?: number[][];
  center_voxel?: number[];
  affected_region?: string;
};

export type OverlayMode = "brainTumor" | "tumorOnly" | "heatmap";

function BrainEnvelope({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <group scale={[1.35, 1.05, 1.55]}>
      <mesh>
        <icosahedronGeometry args={[1, 4]} />
        <meshPhysicalMaterial
          color="#6b7280"
          transparent
          opacity={0.22}
          roughness={0.35}
          metalness={0.05}
          transmission={0.55}
          thickness={0.8}
          side={THREE.DoubleSide}
        />
      </mesh>
      <mesh scale={0.92}>
        <icosahedronGeometry args={[1, 3]} />
        <meshStandardMaterial color="#374151" wireframe transparent opacity={0.12} />
      </mesh>
    </group>
  );
}

function TumorMass({
  position,
  scale,
  mode,
}: {
  position: [number, number, number];
  scale: number;
  mode: OverlayMode;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const base = Math.max(0.18, Math.min(scale, 0.55));

  useFrame(({ clock }) => {
    if (ref.current && mode === "heatmap") {
      ref.current.scale.setScalar(base * (1 + Math.sin(clock.elapsedTime * 2) * 0.04));
    } else if (ref.current) {
      ref.current.scale.setScalar(base);
    }
  });

  return (
    <group position={position}>
      <mesh ref={ref}>
        <sphereGeometry args={[1, 48, 48]} />
        {mode === "heatmap" ? (
          <meshStandardMaterial
            color="#ff6b00"
            emissive="#ff2200"
            emissiveIntensity={1.2}
            transparent
            opacity={0.85}
          />
        ) : (
          <MeshDistortMaterial
            color="#ef4444"
            emissive="#b91c1c"
            emissiveIntensity={0.9}
            distort={0.35}
            speed={2}
            roughness={0.2}
          />
        )}
      </mesh>
      <mesh scale={base * 1.35}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial color="#22c55e" transparent opacity={0.15} />
      </mesh>
      <pointLight position={[0, 0, 0]} intensity={mode === "heatmap" ? 2.5 : 1.2} color="#ff4444" distance={3} />
    </group>
  );
}

function SceneContent({
  spatial,
  overlayMode,
  controlsRef,
}: {
  spatial: SpatialData;
  overlayMode: OverlayMode;
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
}) {
  const pos = useMemo((): [number, number, number] => {
    const c = spatial.center_normalized ?? [0.15, 0.05, -0.1];
    return [c[0] * 0.55, c[1] * 0.45, c[2] * 0.35];
  }, [spatial.center_normalized]);

  const tumorScale = useMemo(() => {
    const v = spatial.tumor_volume_cm3 ?? 8;
    return Math.cbrt(v) / 6;
  }, [spatial.tumor_volume_cm3]);

  const showBrain = overlayMode !== "tumorOnly";

  return (
    <>
      <PerspectiveCamera makeDefault position={[0, 0.2, 4.2]} fov={42} />
      <color attach="background" args={["#0f172a"]} />
      <fog attach="fog" args={["#0f172a", 4, 12]} />
      <ambientLight intensity={0.45} />
      <directionalLight position={[4, 6, 5]} intensity={1.1} color="#e2e8f0" />
      <directionalLight position={[-3, -2, 2]} intensity={0.35} color="#34d399" />
      <BrainEnvelope visible={showBrain} />
      {(spatial.tumor_detected ?? true) && (
        <TumorMass position={pos} scale={tumorScale} mode={overlayMode} />
      )}
      <Environment preset="city" />
      <OrbitControls ref={controlsRef} enablePan enableZoom enableRotate minDistance={2.2} maxDistance={8} />
    </>
  );
}

export function BrainReconstruction3D({
  spatial,
  overlayMode,
  controlsRef,
}: {
  spatial: SpatialData;
  overlayMode: OverlayMode;
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
}) {
  return (
    <Canvas gl={{ antialias: true, alpha: false }} dpr={[1, 2]}>
      <SceneContent spatial={spatial} overlayMode={overlayMode} controlsRef={controlsRef} />
    </Canvas>
  );
}
