"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { PipelineRead } from "@rnaseq/contracts";
import { createRun, pipelines } from "@/lib/api";

const DEFAULT_PARAMS = JSON.stringify(
  {
    samplesheet: "samplesheet.csv",
    genome_fasta: "/path/to/genome.fa",
    genome_gff3: "/path/to/annotation.gff3"
  },
  null,
  2
);

export default function NewRunPage() {
  const router = useRouter();
  const [pipelineItems, setPipelineItems] = useState<PipelineRead[]>([]);
  const [pipelineId, setPipelineId] = useState("");
  const [name, setName] = useState("");
  const [profile, setProfile] = useState("local");
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [inputPaths, setInputPaths] = useState("{}");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    pipelines()
      .then((loaded) => {
        setPipelineItems(loaded);
        setPipelineId(loaded[0]?.id ?? "");
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      const run = await createRun({
        pipeline_id: pipelineId,
        name: name || null,
        profile,
        executor: "local",
        params: JSON.parse(params) as Record<string, unknown>,
        input_paths: JSON.parse(inputPaths) as Record<string, string>
      });
      router.push(`/runs/${run.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run creation failed");
    }
  }

  return (
    <section className="panel stack">
      <h1>New run</h1>
      <form className="stack" onSubmit={onSubmit}>
        <div className="split">
          <label>
            Pipeline
            <select value={pipelineId} onChange={(event) => setPipelineId(event.target.value)}>
              {pipelineItems.map((pipeline) => (
                <option key={pipeline.id} value={pipeline.id}>
                  {pipeline.display_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Profile
            <select value={profile} onChange={(event) => setProfile(event.target.value)}>
              <option value="local">local</option>
              <option value="test">test</option>
              <option value="slurm">slurm</option>
            </select>
          </label>
        </div>
        <label>
          Name
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <div className="split">
          <label>
            Params JSON
            <textarea value={params} onChange={(event) => setParams(event.target.value)} />
          </label>
          <label>
            Input paths JSON
            <textarea value={inputPaths} onChange={(event) => setInputPaths(event.target.value)} />
          </label>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Create run</button>
      </form>
    </section>
  );
}

