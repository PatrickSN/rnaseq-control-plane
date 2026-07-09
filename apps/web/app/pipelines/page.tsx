"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { PipelineRead } from "@rnaseq/contracts";
import { pipelines } from "@/lib/api";

export default function PipelinesPage() {
  const [items, setItems] = useState<PipelineRead[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    pipelines().then(setItems).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load pipelines");
    });
  }, []);

  return (
    <section className="stack">
      <div className="row">
        <h1>Pipelines</h1>
        <Link href="/runs/new">
          <button>New run</button>
        </Link>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <div className="grid">
        {items.map((pipeline) => {
          const defaultVersion = pipeline.versions.find((version) => version.is_default);
          return (
            <article className="card stack" key={pipeline.id}>
              <div>
                <h2>{pipeline.display_name}</h2>
                <p className="muted">{pipeline.organism}</p>
              </div>
              <p>{pipeline.description}</p>
              <div className="stack">
                <span>Slug: {pipeline.slug}</span>
                <span>Version: {defaultVersion?.version ?? "-"}</span>
                <span>Profiles: {defaultVersion?.supported_profiles.join(", ") ?? "-"}</span>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

