import "./tokenTable.css";

export type TokenRow = {
  lexeme: string;
  tokenizer: string;
  token: string;
};

export type TokenStatus = "idle" | "loading" | "ready" | "error";

type TokenTableProps = {
  rows?: TokenRow[];
  status: TokenStatus;
  error?: string | null;
  lastRunAt?: Date | null;
};

export default function TokenTable({
  rows = [],
  status,
  error = null,
  lastRunAt,
}: TokenTableProps) {
  const hasRows = rows.length > 0;

  const renderTokenizer = (row: TokenRow) => {
    if (row.token !== "STRING_LITERAL") {
      return row.tokenizer;
    }
    const max = 30;
    if (row.tokenizer.length <= max) {
      return row.tokenizer;
    }
    return `${row.tokenizer.slice(0, max - 1)}…`;
  };

  return (
    <div className="tokens">
      <div className="tokens__head">
        <div className="tokens__th">Lexeme</div>
        <div className="tokens__th">Token</div>
        <div className="tokens__th">
          Token Type
          {lastRunAt && (
            <span className="tokens__meta">
            </span>
          )}
        </div>
      </div>

      <div className="tokens__body">
        {status === "loading" && (
          <div className="tokens__empty">Lexing source…</div>
        )}
        {status === "error" && (
          <div className="tokens__empty tokens__empty--error">
            {error ?? "Failed to lex source."}
          </div>
        )}
        {status === "idle" && (
          <div className="tokens__empty">Start typing to see tokens.</div>
        )}
        {status === "ready" && hasRows &&
          rows.map((r, i) => (
            <div
              key={`${r.lexeme}-${r.token}-${i}`}
              className={`tokens__row ${i % 2 === 1 ? "is-alt" : ""}`}
            >
              <div className="tokens__cell tokens__cell--lexeme">
                {r.lexeme}
              </div>
              <div className="tokens__cell tokens__cell--tokenizer">
                <span title={r.tokenizer}>{renderTokenizer(r)}</span>
              </div>
              <div className="tokens__cell tokens__cell--token">
                {r.token}
              </div>
            </div>
          ))}
        {status === "ready" && !hasRows && (
          <div className="tokens__empty">No tokens found.</div>
        )}
      </div>
    </div>
  );
}
