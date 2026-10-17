import { useState } from "react";
import { Upload } from "./pages/Upload";
import { Processing } from "./pages/Processing";
import { Dashboard } from "./pages/Dashboard";
import { AppShell } from "./components/AppShell/AppShell";
import { sampleShootPlan } from "./lib/fixtures/sampleShootPlan";
import { fetchRecommendations } from "./lib/api";
import type { ShootPlan, StudioScoutReport } from "./lib/types";

type Screen = "upload" | "processing" | "dashboard";

function App() {
  const [screen, setScreen] = useState<Screen>("upload");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadPrompt, setUploadPrompt] = useState("");
  const [uploadRegion, setUploadRegion] = useState("");
  const [currentRunId, setCurrentRunId] = useState<string | undefined>(
    undefined,
  );
  const [plan, setPlan] = useState<ShootPlan>(sampleShootPlan);
  const [agentReport, setAgentReport] = useState<StudioScoutReport | null>(
    null,
  );

  const openSampleDossier = () => {
    setScreen("dashboard");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const goHome = () => {
    setScreen("upload");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (screen === "upload") {
    return (
      <AppShell
        screen={screen}
        onNewScout={goHome}
        onOpenReport={openSampleDossier}
      >
        <Upload
          onOpenSample={openSampleDossier}
          onSubmit={(file, prompt, region) => {
            setUploadedFile(file);
            setUploadPrompt(prompt);
            setUploadRegion(region);
            setScreen("processing");
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        />
      </AppShell>
    );
  }

  if (screen === "processing") {
    return (
      <AppShell
        screen={screen}
        onNewScout={goHome}
        onOpenReport={openSampleDossier}
      >
        <Processing
          file={uploadedFile}
          prompt={uploadPrompt}
          initialRegion={uploadRegion}
          onBack={goHome}
          onComplete={(resultPlan, report, runId) => {
            if (resultPlan) setPlan(resultPlan);
            setAgentReport(report);
            setCurrentRunId(runId);
            setScreen("dashboard");
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell
      screen={screen}
      onNewScout={goHome}
      onOpenReport={openSampleDossier}
    >
      <Dashboard
        plan={plan}
        agentReport={agentReport}
        onNewScout={goHome}
        onPlanRefresh={() => {
          fetchRecommendations(currentRunId)
            .then(setPlan)
            .catch((err) => console.error("Refresh failed:", err));
        }}
      />
    </AppShell>
  );
}

export default App;
