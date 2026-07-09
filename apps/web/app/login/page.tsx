"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      const token = await login(email, password);
      setToken(token.access_token);
      router.push("/pipelines");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <section className="panel stack" style={{ maxWidth: 460 }}>
      <h1>Login</h1>
      <form className="stack" onSubmit={onSubmit}>
        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Sign in</button>
      </form>
    </section>
  );
}

