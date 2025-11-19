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

  const [out, setOut] = useState<string[]>([
    'Lexi Terminal - type "help" for available commands.',
  ]);
  const [line, setLine] = useState("");
  const [hist, setHist] = useState<string[]>([]);
  const [idx, setIdx] = useState(-1);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [out]);

  useEffect(() => {
    const el = scrollRef.current?.parentElement;
    const focus = () => inputRef.current?.focus();
    el?.addEventListener("click", focus);
    return () => el?.removeEventListener("click", focus);
  }, []);

  const run = async (src: string) => {
    setOut((o) => [...o, `$ ${src}`]);
    const cmdline = src.trim();
    if (!cmdline) {
      setLine("");
      return;
    }

    const [name, ...args] = splitArgs(cmdline);
    if (name === "clear") {
      setOut([]);
      setLine("");
      return;
    }

    const fn = registry[name];
    if (!fn) {
      setOut((o) => [...o, `command not found: ${name}`]);
      setLine("");
      return;
    }

    try {
      const res = await fn(args);
      if (typeof res === "string" && res.length) {
        setOut((o) => [...o, res]);
      }
    } catch (e: any) {
      setOut((o) => [...o, `error: ${e?.message ?? String(e)}`]);
    } finally {
      setLine("");
    }
  };

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

  const renderValidation = () => {
    if (!validation) {
      return (
        <div className="term-validation term-validation--placeholder">
          No validation run yet. Type <code>validate</code>.
        </div>
      );
    }
    const isError = !validation.ok;
    const position =
      validation.token?.line != null && validation.token?.column != null
        ? `at line ${validation.token.line}, column ${validation.token.column}`
        : null;

    return (
      <div className={`term-validation ${isError ? "is-error" : "is-ok"}`}>
        <div className="term-validation__row">
          <span className="term-validation__badge">
            {isError ? "SYNTAX ERROR" : "SYNTAX"}
          </span>
          <span className="term-validation__message">
            {isError ? "Syntax error" : "Structure OK"}
            {position && (
              <span className="term-validation__pos"> {position}</span>
            )}
            : {validation.message}
          </span>
        </div>
        {isError &&
          validation.expected &&
          validation.expected.length > 0 && (
            <div className="term-validation__expected">
              <span className="term-validation__expected-label">
                Expected tokens:
              </span>
              <div className="term-validation__chips">
                {validation.expected.map((sym, idx) => (
                  <span key={`${sym}-${idx}`} className="term-validation__chip">
                    {sym}
                  </span>
                ))}
              </div>
            </div>
          )}
      </div>
    );
  };

  return (
    <div
      className="panel terminal"
      style={{ display: "grid", gridTemplateRows: "auto 1fr auto" }}
    >
      <div className="header">Terminal</div>
      {renderValidation()}
      <div ref={scrollRef} className="term-out" aria-live="polite">
        {out.map((t, i) => (
          <div key={i}>{t}</div>
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
