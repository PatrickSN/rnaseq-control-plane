export type RunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled"
  | "parsing_failed";

export type ProfileName = "local" | "slurm" | "test";
export type ExecutorKind = "local" | "slurm";
export type ArtifactKind =
  | "nextflow_report"
  | "nextflow_timeline"
  | "nextflow_dag"
  | "nextflow_trace"
  | "nextflow_log"
  | "stdout_log"
  | "stderr_log"
  | "params"
  | "result_table";

export interface TokenRead {
  access_token: string;
  token_type: "bearer";
}

export interface UserRead {
  id: string;
  email: string;
  full_name: string | null;
  role: "admin" | "user";
  is_active: boolean;
  created_at: string;
}

export interface PipelineVersionRead {
  id: string;
  pipeline_id: string;
  version: string;
  pipeline_path: string;
  main_script: string;
  params_template_path: string;
  default_profile: ProfileName;
  supported_profiles: ProfileName[];
  fingerprint: string | null;
  is_default: boolean;
  created_at: string;
}

export interface PipelineRead {
  id: string;
  slug: string;
  display_name: string;
  organism: string;
  description: string | null;
  is_active: boolean;
  versions: PipelineVersionRead[];
}

export interface RunCreate {
  pipeline_id: string;
  pipeline_version_id?: string | null;
  name?: string | null;
  profile: ProfileName;
  executor: ExecutorKind;
  params: Record<string, unknown>;
  input_paths: Record<string, string>;
}

export interface RunRead {
  id: string;
  user_id: string;
  pipeline_id: string;
  pipeline_version_id: string;
  resumed_from_run_id: string | null;
  name: string | null;
  status: RunStatus;
  profile: ProfileName;
  executor: ExecutorKind;
  pipeline_path: string;
  pipeline_fingerprint: string | null;
  work_dir: string;
  output_dir: string;
  params_path: string;
  command: string[];
  session_id: string | null;
  exit_code: number | null;
  error_message: string | null;
  environment: Record<string, unknown>;
  inputs: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface RunTaskRead {
  id: string;
  run_id: string;
  task_id: string | null;
  hash: string | null;
  name: string;
  process: string | null;
  status: string | null;
  exit_code: number | null;
  submit: string | null;
  start: string | null;
  complete: string | null;
  duration: string | null;
  realtime: string | null;
  cpu_percent: string | null;
  memory: string | null;
  raw: Record<string, unknown>;
}

export interface ArtifactRead {
  id: string;
  run_id: string;
  kind: ArtifactKind;
  label: string;
  path: string;
  relative_path: string;
  mime_type: string | null;
  size_bytes: number | null;
  sha256: string | null;
  created_at: string;
}

