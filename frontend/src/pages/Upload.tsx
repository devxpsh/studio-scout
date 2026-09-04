import { useState } from "react";

export function Upload({
  onSubmit,
}: {
  onSubmit: (file: File, prompt: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6">
      <p className="mb-3 font-mono text-xs tracking-widest uppercase text-(--color-meta)">
        Studio Scout
      </p>
      <h1 className="font-display text-5xl text-[var(--color-paper)] mb-8 text-center max-w-xl">
        Find every location your script needs
      </h1>

      <label
        className="border border-dashed border-[var(--color-meta)] rounded-sm px-10 py-12
                   flex flex-col items-center gap-3 cursor-pointer
                   hover:border-[var(--color-amber)] transition-colors"
      >
        <span className="font-mono text-sm text-[var(--color-paper)]">
          Drop a screenplay PDF, or click to browse
        </span>
        <span className="font-mono text-xs text-(--color-meta)">.pdf</span>
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {file && (
        <p className="mt-3 max-w-xl truncate font-mono text-xs text-(--color-amber)">
          Selected: {file.name}
        </p>
      )}
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="What should we find? Example: scout every scene in New Jersey"
        rows={3}
        className="mt-5 w-full max-w-xl resize-none rounded-sm border border-(--color-meta)/60 bg-transparent px-4 py-3 font-mono text-sm text-(--color-paper) outline-none placeholder:text-(--color-meta) focus:border-(--color-amber)"
      />
      <button
        type="button"
        disabled={!file}
        onClick={() => file && onSubmit(file, prompt)}
        className="mt-4 rounded-sm border border-(--color-amber) px-5 py-2 font-mono text-xs uppercase tracking-widest text-(--color-amber) transition-colors hover:bg-(--color-amber) hover:text-(--color-ink) disabled:cursor-not-allowed disabled:opacity-40"
      >
        Start location scout
      </button>
    </main>
  );
}
