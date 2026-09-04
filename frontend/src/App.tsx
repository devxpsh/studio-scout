import { useState } from "react";
import { Upload } from "./pages/Upload";
import { Processing } from "./pages/Processing";
import { Dashboard } from "./pages/Dashboard";
import { sampleShootPlan } from "./lib/fixtures/sampleShootPlan";
import { fetchRecommendations } from "./lib/api";
import type { ShootPlan } from "./lib/types";

type Screen = "upload" | "processing" | "dashboard";

function App() {
  const [screen, setScreen] = useState<Screen>("upload");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadPrompt, setUploadPrompt] = useState("");
  // Starts as fixture data so there's never a blank dashboard state, but
  // this is only ever shown before a real upload completes — the screen
  // machine below never routes to 'dashboard' before 'processing' finishes.
  const [plan, setPlan] = useState<ShootPlan>(sampleShootPlan);

  if (screen === "upload") {
    return (
      <Upload
        onSubmit={(file, prompt) => {
          setUploadedFile(file);
          setUploadPrompt(prompt);
          setScreen("processing");
        }}
      />
    );
  }

  if (screen === "processing") {
    return (
      <Processing
        file={uploadedFile}
        prompt={uploadPrompt}
        onComplete={(resultPlan) => {
          if (resultPlan) setPlan(resultPlan);
          setScreen("dashboard");
        }}
      />
    );
  }

  return (
    <Dashboard
      plan={plan}
      onPlanRefresh={() => {
        fetchRecommendations()
          .then(setPlan)
          .catch((err) => console.error("Refresh failed:", err));
      }}
    />
  );
}

export default App;
