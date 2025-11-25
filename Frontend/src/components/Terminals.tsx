import "./Terminals.css";

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
  validation?: ValidationResult | null;
  lexError?: string | null;
};

export default function Terminal({ validation = null, lexError = null }: Props) {
  const lines: string[] = [];

  if (lexError) {
    lines.push("Lexing error:");
    lexError.split(/\r?\n/).forEach((line) => {
      if (line.trim().length) {
        lines.push(line);
      }
    });
  } else if (validation && !validation.ok) {
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
      validation.expected.forEach((sym, idx) => lines.push(`  ${idx + 1}. ${sym}`));
    }
  }

  const logState = validation
    ? validation.ok
      ? "is-ok"
      : "is-error"
    : "is-idle";

  return (
    <div className="terminal-panel">
      <div className="header">Terminal</div>
      <div className={`term-log ${logState}`} aria-live="polite">
        {lines.map((text, idx) => (
          <div key={`${text}-${idx}`} className="term-log__line">
            {text}
          </div>
        ))}
      </div>
    </div>
  );
}
