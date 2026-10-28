import { createContext, useContext, useMemo, useState } from "react";
import type { SegmentationResponse, UploadResponse } from "@/lib/api";

type SessionState = {
  upload?: UploadResponse;
  segmentation?: SegmentationResponse;
  setUpload: (u?: UploadResponse) => void;
  setSegmentation: (s?: SegmentationResponse) => void;
};

const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [upload, setUpload] = useState<UploadResponse>();
  const [segmentation, setSegmentation] = useState<SegmentationResponse>();
  const value = useMemo(
    () => ({ upload, segmentation, setUpload, setSegmentation }),
    [upload, segmentation],
  );
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
