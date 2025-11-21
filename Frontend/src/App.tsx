import { useCallback, useEffect, useMemo, useState } from "react";
import Header from "./components/Header";
import Editor, { type FileTab } from "./components/Editor";
import TokenTable from "./components/TokenTable";
import Terminal, {
  type Command,
  type ValidationResult,
} from "./components/Terminals";
import "./App.css";

type TokenRow = { lexeme: string; token: string; tokenType: string };
type TokenStatus = "idle" | "loading" | "ready" | "error";

const TOKEN_STATUS_LABEL: Record<TokenStatus, string> = {
  idle: "Idle",
  loading: "Lexing…",
  ready: "Synced",
  error: "Error",
};

const DEFAULT_SOURCE = `love () {
  express << "hello, lover";
}
`;

const DEFAULT_FILE: FileTab = {
  id: "main-love",
  name: "main.love",
  content: DEFAULT_SOURCE,
};

const LEX_ENDPOINT = import.meta.env.VITE_LEX_ENDPOINT?.trim() || "/lex";
const VALIDATE_ENDPOINT =
  import.meta.env.VITE_VALIDATE_ENDPOINT?.trim() || "/validate";

async function parseResponseBody(
  resp: Response
): Promise<{ data: any; raw: string | null }> {
  const text = await resp.text();
  if (!text) {
    return { data: {}, raw: null };
  }
  try {
    return { data: JSON.parse(text), raw: null };
  } catch {
    return { data: {}, raw: text };
  }
}

export default function App() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [rows, setRows] = useState<TokenRow[]>([]);
  const [status, setStatus] = useState<TokenStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);

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

      const { data: payload, raw } = await parseResponseBody(resp);
      if (!resp.ok) {
        const detail =
          (payload?.error as string | undefined) ??
          (payload?.message as string | undefined) ??
          raw?.trim();
        throw new Error(detail || `Request failed (${resp.status})`);
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

  const validateSource = useCallback(async (): Promise<ValidationResult> => {
    const body = source ?? "";
    if (!body.trim()) {
      const res: ValidationResult = {
        ok: false,
        message: "Source is empty. Expected `love main() { ... }`.",
        code: "ERR_EMPTY",
        expected: ["love"],
      };
      setValidation(res);
      return res;
    }

    try {
      const resp = await fetch(VALIDATE_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: body }),
      });
      const { data: payload, raw } = await parseResponseBody(resp);

      if (resp.ok && payload?.ok) {
        const success: ValidationResult = {
          ok: true,
          message: (payload?.message as string) ?? "Structure looks valid.",
          code: payload?.code as string | undefined,
        };
        setValidation(success);
        return success;
      }

      const failureMessage =
        (payload?.message as string | undefined) ??
        (payload?.error as string | undefined) ??
        raw?.trim() ??
        `Validation failed (HTTP ${resp.status})`;
      const failure: ValidationResult = {
        ok: false,
        message: failureMessage,
        code: payload?.code as string | undefined,
        token: payload?.token as ValidationResult["token"],
        expected: Array.isArray(payload?.expected)
          ? (payload.expected as string[])
          : undefined,
      };
      setValidation(failure);
      return failure;
    } catch (err) {
      const failure: ValidationResult = {
        ok: false,
        message:
          err instanceof Error ? err.message : "Failed to reach validator.",
      };
      setValidation(failure);
      return failure;
    }
  }, [source]);

  const terminalCommands = useMemo<Record<string, Command>>(
    () => ({
      lex: async () => {
        const tokens = await lexSource(source);
        if (!tokens.length) return "No tokens produced (empty source?).";
        const count = tokens.length;
        return `Lexed ${count} token${count === 1 ? "" : "s"}.`;
      },
      validate: async () => {
        const result = await validateSource();
        if (!result.ok) {
          const pos = result.token
            ? ` at line ${result.token.line}, column ${result.token.column}`
            : "";
          const expected =
            result.expected && result.expected.length
              ? ` Expected: ${result.expected.join(" ")}`
              : "";
          throw new Error(`Syntax error${pos}: ${result.message}.${expected}`);
        }
        return result.message ?? "Structure looks valid.";
      },
    }),
    [lexSource, source, validateSource]
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
        <section className="panel panel--editor">
          <Editor initialFiles={[DEFAULT_FILE]} onChangeFiles={handleEditorChange} />
        </section>
        <section className="panel panel--tokens">
          <TokenTable rows={rows} status={status} error={error} lastRunAt={lastRunAt} />
        </section>
        <section className="panel panel--terminal">
          <Terminal
            prompt="lover"
            commands={terminalCommands}
            validation={validation}
          />
        </section>
      </main>
    </>
  );
}
