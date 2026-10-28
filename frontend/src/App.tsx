import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/Shell";
import { SessionProvider } from "@/context/SessionContext";
import AboutPage from "@/pages/AboutPage";
import AnalyzePage from "@/pages/AnalyzePage";
import HomePage from "@/pages/HomePage";
import PerformancePage from "@/pages/PerformancePage";
import ResultsPage from "@/pages/ResultsPage";
import VisualizePage from "@/pages/VisualizePage";

export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <AppShell>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/visualize" element={<VisualizePage />} />
            <Route path="/performance" element={<PerformancePage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </AppShell>
      </SessionProvider>
    </BrowserRouter>
  );
}
