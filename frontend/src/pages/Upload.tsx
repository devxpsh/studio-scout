import { useState } from "react";

const REGION_SUGGESTIONS = [
  "New Jersey",
  "Bay Area, California",
  "Los Angeles, California",
  "New York City, New York",
  "Atlanta, Georgia",
  "Chicago, Illinois",
  "London, UK",
  "Mumbai, India",
  "Vancouver, Canada",
];

export function Upload({
  onSubmit,
}: {
  onSubmit: (file: File, prompt: string, region: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [region, setRegion] = useState("");
  const [prompt, setPrompt] = useState("");
  return (
    <main
      id="intake"
      className="mx-auto grid max-w-6xl gap-12 px-5 py-14 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-24"
    >
      <section>
        <p className="section-kicker">01 / New production brief</p>
        <h1 className="mt-5 max-w-xl font-display text-5xl leading-[0.98] text-(--color-paper) sm:text-6xl">
          Find every location your script needs.
        </h1>
        <p className="mt-6 max-w-md text-base leading-7 text-(--color-meta)">
          Turn a screenplay into a source-backed scouting plan, with agent
          reasoning and production risks in one desk.
        </p>
        <div className="mt-10 grid max-w-md grid-cols-3 border-y border-(--color-line) py-4 font-mono text-[9px] uppercase tracking-widest text-(--color-meta)">
          <span>
            <strong className="block text-lg text-(--color-paper)">01</strong>{" "}
            PDF intake
          </span>
          <span>
            <strong className="block text-lg text-(--color-paper)">03</strong>{" "}
            agents
          </span>
          <span>
            <strong className="block text-lg text-(--color-paper)">∞</strong>{" "}
            evidence
          </span>
        </div>
      </section>

      <form
        className="border border-(--color-line) bg-(--color-surface)/70 p-5 sm:p-7"
        onSubmit={(e) => {
          e.preventDefault();
          if (file) onSubmit(file, prompt, region);
        }}
      >
        <div className="mb-6 flex items-center justify-between border-b border-(--color-line) pb-4">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-widest text-(--color-paper)">
              Scout intake
            </p>
            <p className="mt-1 font-mono text-[10px] text-(--color-meta)">
              Upload a screenplay to begin
            </p>
          </div>
          <span className="font-mono text-[10px] text-(--color-amber)">
            PDF / 01
          </span>
        </div>
        <label className="group flex min-h-40 cursor-pointer flex-col items-center justify-center border border-dashed border-(--color-meta) px-5 text-center transition-colors hover:border-(--color-amber)">
          <span className="mb-3 flex h-10 w-10 items-center justify-center border border-(--color-line) font-mono text-lg text-(--color-amber)">
            +
          </span>
          <span className="font-mono text-sm text-(--color-paper)">
            Drop a screenplay PDF, or browse
          </span>
          <span className="mt-2 font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            PDF files only
          </span>
          <input
            type="file"
            name="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
        {file && (
          <p className="mt-3 truncate font-mono text-xs text-(--color-amber)">
            Selected / {file.name}
          </p>
        )}
        <label className="mt-5 block">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Target region
          </span>
          <input
            type="text"
            name="region"
            list="region-suggestions"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder="e.g. New Jersey, Bay Area, or Mumbai"
            className="mt-2 w-full rounded-sm border border-(--color-line) bg-transparent px-3 py-2.5 font-mono text-sm text-(--color-paper) outline-none placeholder:text-(--color-meta) focus:border-(--color-amber)"
          />
          <datalist id="region-suggestions">
            {REGION_SUGGESTIONS.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
        </label>
        <label className="mt-4 block">
          <span className="font-mono text-[10px] uppercase tracking-widest text-(--color-meta)">
            Scout instruction (optional)
          </span>
          <textarea
            name="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: prioritize industrial warehouses and low-permit-friction exteriors"
            rows={2}
            className="mt-2 w-full rounded-sm border border-(--color-line) bg-transparent px-3 py-2.5 font-mono text-sm text-(--color-paper) outline-none placeholder:text-(--color-meta) focus:border-(--color-amber)"
          />
        </label>
        <button
          type="submit"
          disabled={!file}
          className="mt-5 flex w-full items-center justify-between rounded-sm bg-(--color-amber) px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-(--color-ink) transition-colors hover:bg-(--color-paper) disabled:cursor-not-allowed disabled:opacity-40"
        >
          Start location scout <span aria-hidden="true">↗</span>
        </button>
      </form>
    </main>
  );
}
