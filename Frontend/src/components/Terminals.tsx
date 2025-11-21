import { useEffect, useMemo, useRef, useState } from "react";
import "./Terminals.css";

export type Command = (args: string[]) => Promise<string | void> | string | void;

export type ValidationTokenInfo = {
  lexeme?: string;
  kind?: string;
  line?: number;
  column?: number;
};

export type ValidationResult = {
  ok: boolean;
  message: string;
  code?: string;
  token?: ValidationTokenInfo;
  expected?: string[];
};

type Props = {
  commands?: Record<string, Command>;
  prompt?: string;
  validation?: ValidationResult | null;
};

export default function Terminal({
  commands = {},
  prompt = "guest",
  validation = null,
}: Props) {
  const registry = useMemo<Record<string, Command>>(
    () => ({
      help: () =>
        ["Built-ins:", "  help", "  clear", "  echo [text]", ""].join("\n"),
      clear: () => "",
      echo: (args) => args.join(" "),
      ...commands,
    }),
    [commands]
  );

  const [line, setLine] = useState("");
  const [hist, setHist] = useState<string[]>([]);
  const [idx, setIdx] = useState(-1);

  const panelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = panelRef.current;
    const focus = () => inputRef.current?.focus();
    el?.addEventListener("click", focus);
    return () => el?.removeEventListener("click", focus);
  }, []);

  const run = async (src: string) => {
    const cmdline = src.trim();
    if (!cmdline) {
      setLine("");
      return;
    }

    const [name, ...args] = splitArgs(cmdline);
    if (name === "clear") {
      setLine("");
      return;
    }

    const fn = registry[name];
    if (!fn) {
      console.warn(`command not found: ${name}`);
      setLine("");
      return;
    }

    try {
      await fn(args);
    } catch (e: any) {
      console.error(e?.message ?? String(e));
    } finally {
      setLine("");
    }
  };

  const validationLines = useMemo(() => {
    if (!validation) {
      return ['No validation run yet. Type "validate".'];
    }

    if (!validation.ok) {
      const lines: string[] = [];
      const parts: string[] = [];
      if (validation.token?.line != null && validation.token?.column != null) {
        parts.push(`line ${validation.token.line}, column ${validation.token.column}`);
      }
      if (validation.code) {
        parts.push(validation.code);
      }
      lines.push(parts.length ? `Error (${parts.join(" | ")}):` : "Error:");
      lines.push(validation.message ?? "Syntax error.");
      if (validation.token?.lexeme) {
        lines.push(`Found: ${validation.token.lexeme}`);
      }
      if (validation.expected?.length) {
        lines.push("Expected tokens:");
        validation.expected.forEach((sym, idx) =>
          lines.push(`  ${idx + 1}. ${sym}`)
        );
      }
      return lines;
    }

    const successLabel = validation.code ? `[${validation.code}] ` : "";
    return [
      `${successLabel}${validation.message ?? "Structure looks valid."}`,
    ];
  }, [validation]);

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      setHist((h) => [line, ...h]);
      setIdx(-1);
      run(line).catch(() => {});
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const next = Math.min(hist.length - 1, idx + 1);
      setIdx(next);
      setLine(next >= 0 ? hist[next] : "");
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = Math.max(-1, idx - 1);
      setIdx(next);
      setLine(next >= 0 ? hist[next] : "");
      return;
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
      setLine("");
    }
  };

  const logState = validation
    ? validation.ok
      ? "is-ok"
      : "is-error"
    : "is-idle";

  return (
    <div className="terminal-panel" ref={panelRef}>
      <div className="header">Terminal</div>
      <div className={`term-log ${logState}`} aria-live="polite">
        {validationLines.map((text, idx) => (
          <div key={`${text}-${idx}`} className="term-log__line">
            {text}
          </div>
        ))}
      </div>

      <div className="term-input-row">
        <span className="term-prompt">{prompt}$</span>
        <input
          ref={inputRef}
          className="term-input"
          value={line}
          onChange={(e) => setLine(e.target.value)}
          onKeyDown={onKey}
          spellCheck={false}
          autoCapitalize="off"
          autoCorrect="off"
          autoComplete="off"
        />
      </div>
    </div>
  );
}

/* minimal shell-style splitter: keeps quoted groups */
function splitArgs(s: string): string[] {
  const out: string[] = [];
  let buf = "",
    q: "'" | '"' | null = null;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === q) q = null;
      else buf += c;
      continue;
    }
    if (c === "'" || c === '"') {
      q = c;
      continue;
    }
    if (/\s/.test(c)) {
      if (buf) {
        out.push(buf);
        buf = "";
      }
      continue;
    }
    buf += c;
  }
  if (buf) out.push(buf);
  return out;
}
