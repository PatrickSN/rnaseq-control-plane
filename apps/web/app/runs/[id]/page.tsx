"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { ArtifactRead, RunRead, RunTaskRead } from "@rnaseq/contracts";
import { runArtifacts, runDetail, runLog, runTasks } from "@/lib/api";

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [run, setRun] = useState<RunRead | null>(null);
  const [tasks, setTasks] = useState<RunTaskRead[]>([]);
  const [artifacts, setArtifacts] = useState<ArtifactRead[]>([]);
  const [log, setLog] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([runDetail(id), runTasks(id), runArtifacts(id), runLog(id, "stdout")])
      .then(([loadedRun, loadedTasks, loadedArtifacts, loadedLog]) => {
        setRun(loadedRun);
        setTasks(loadedTasks);
        setArtifacts(loadedArtifacts);
        setLog(loadedLog);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Load failed"));
  }, [id]);

  if (error) {
    return <p className="error">{error}</p>;
  }
  if (!run) {
    return <p>Loading...</p>;
  }

  return (
    <section className="stack">
      <div className="panel stack">
        <div className="row">
          <h1>{run.name ?? run.id}</h1>
          <span className="status">{run.status}</span>
        </div>
        <div className="grid">
          <span>Profile: {run.profile}</span>
          <span>Session: {run.session_id ?? "-"}</span>
          <span>Exit: {run.exit_code ?? "-"}</span>
          <span>Output: {run.output_dir}</span>
        </div>
      </div>

      <div className="split">
        <div className="panel stack">
          <h2>Artifacts</h2>
          {artifacts.map((artifact) => (
            <div key={artifact.id}>
              <strong>{artifact.label}</strong>
              <div className="muted">{artifact.relative_path}</div>
            </div>
          ))}
        </div>
        <div className="panel stack">
          <h2>Tasks</h2>
          {tasks.map((task) => (
            <div className="row" key={task.id}>
              <span>{task.name}</span>
              <span className="status">{task.status ?? "-"}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="panel stack">
        <h2>stdout</h2>
        <pre className="code">{log || "No stdout captured yet."}</pre>
      </div>
    </section>
  );
}

