import { createContext, useContext, useMemo, useState } from "react";
import type { SegmentationResponse, UploadResponse } from "@/lib/api";

export type PlatformMode = "education" | "clinical";

type SessionState = {
  upload?: UploadResponse;
  segmentation?: SegmentationResponse;
  applicationType: string;
  platformMode: PlatformMode;
  setUpload: (u?: UploadResponse) => void;
  setSegmentation: (s?: SegmentationResponse) => void;
  setApplicationType: (id: string) => void;
  setPlatformMode: (mode: PlatformMode) => void;
};

const SessionContext = createContext<SessionState | null>(null);

const MODE_KEY = "neuroscan_platform_mode";

function readStoredMode(): PlatformMode {
  try {
    const v = localStorage.getItem(MODE_KEY);
    if (v === "clinical" || v === "education") return v;
  } catch {
    /* ignore */
  }
  return "education";
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [upload, setUpload] = useState<UploadResponse>();
  const [segmentation, setSegmentation] = useState<SegmentationResponse>();
  const [applicationType, setApplicationType] = useState("brain_tumor");
  const [platformMode, setPlatformModeState] = useState<PlatformMode>(readStoredMode);

  const setPlatformMode = (mode: PlatformMode) => {
    setPlatformModeState(mode);
    try {
      localStorage.setItem(MODE_KEY, mode);
    } catch {
      /* ignore */
    }
  };

  const value = useMemo(
    () => ({
      upload,
      segmentation,
      applicationType,
      platformMode,
      setUpload,
      setSegmentation,
      setApplicationType,
      setPlatformMode,
    }),
    [upload, segmentation, applicationType, platformMode],
  );
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
