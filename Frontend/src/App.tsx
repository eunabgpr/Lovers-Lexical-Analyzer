import { useCallback, useEffect, useMemo, useState } from "react";
import Header from "./components/Header";
import Editor, { type FileTab } from "./components/Editor";
import TokenTable from "./components/TokenTable";
import Terminal, { type Command } from "./components/Terminals";
import "./App.css";

type TokenRow = { lexeme: string; token: string; tokenType: string };
type TokenStatus = "idle" | "loading" | "ready" | "error";

const TOKEN_STATUS_LABEL: Record<TokenStatus, string> = {
  idle: "Idle",
  loading: "Lexing…",
  ready: "Synced",
  error: "Error",
};

const DEFAULT_SOURCE = `love main() {
  express << "hello, lover";
}
`;

const DEFAULT_FILE: FileTab = {
  id: "main-love",
  name: "main.love",
  content: DEFAULT_SOURCE,
};

const LEX_ENDPOINT = import.meta.env.VITE_LEX_ENDPOINT?.trim() || "/lex";

export default function App() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [rows, setRows] = useState<TokenRow[]>([]);
  const [status, setStatus] = useState<TokenStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);

  const lexSource = useCallback(async (text: string) => {
    const body = text ?? "";
    if (!body.trim()) {
      setRows([]);
      setStatus("idle");
      setError(null);
      setLastRunAt(null);
      return [];
    }

    setStatus("loading");
    setError(null);

    try {
      const resp = await fetch(LEX_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: body }),
      });

      const payload = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(payload?.error ?? `Request failed (${resp.status})`);
      }

      const nextRows = Array.isArray(payload?.rows)
        ? (payload.rows as TokenRow[])
        : [];

      setRows(nextRows);
      setStatus("ready");
      setLastRunAt(new Date());
      return nextRows;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to lex source.";
      setError(message);
      setStatus("error");
      return [];
    }
  }, []);

  useEffect(() => {
    const handle = setTimeout(() => {
      void lexSource(source);
    }, 400);
    return () => clearTimeout(handle);
  }, [lexSource, source]);

  const terminalCommands = useMemo<Record<string, Command>>(
    () => ({
      lex: async () => {
        const tokens = await lexSource(source);
        if (!tokens.length) return "No tokens produced (empty source?).";
        const count = tokens.length;
        return `Lexed ${count} token${count === 1 ? "" : "s"}.`;
      },
    }),
    [lexSource, source]
  );

  const handleEditorChange = useCallback(
    (files: FileTab[], activeId: string) => {
      const active = files.find(f => f.id === activeId);
      if (active) setSource(active.content);
    },
    []
  );

  return (
    <>
      <Header
        label="main.love"
        right={<span className={`status status--${status}`}>{TOKEN_STATUS_LABEL[status]}</span>}
      />
      <main className="app">
        <div className="top-row">
          <section className="panel panel--editor">
            <Editor initialFiles={[DEFAULT_FILE]} onChangeFiles={handleEditorChange} />
          </section>
          <section className="panel panel--tokens">
            <TokenTable rows={rows} status={status} error={error} lastRunAt={lastRunAt} />
          </section>
        </div>
        <section className="panel panel--terminal">
          <Terminal prompt="lover" commands={terminalCommands} />
        </section>
      </main>
    </>
  );
}
