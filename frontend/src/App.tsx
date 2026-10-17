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

  if (screen === "upload") {
    return (
      <AppShell screen={screen}>
        <Upload
          onSubmit={(file, prompt, region) => {
            setUploadedFile(file);
            setUploadPrompt(prompt);
            setUploadRegion(region);
            setScreen("processing");
          }}
        />
      </AppShell>
    );
  }

  if (screen === "processing") {
    return (
      <AppShell screen={screen} onNewScout={() => setScreen("upload")}>
        <Processing
          file={uploadedFile}
          prompt={uploadPrompt}
          initialRegion={uploadRegion}
          onBack={() => setScreen("upload")}
          onComplete={(resultPlan, report, runId) => {
            if (resultPlan) setPlan(resultPlan);
            setAgentReport(report);
            setCurrentRunId(runId);
            setScreen("dashboard");
          }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell screen={screen} onNewScout={() => setScreen("upload")}>
      <Dashboard
        plan={plan}
        agentReport={agentReport}
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
