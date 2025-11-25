import "./tokenTable.css";

export type TokenRow = {
  lexeme: string;
  token: string;
  tokenType: string;
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
  error: _error = null,
  lastRunAt,
}: TokenTableProps) {
  const hasRows = rows.length > 0;

  const renderToken = (row: TokenRow) => {
    if (!row.tokenType.includes("STRING")) {
      return row.token;
    }
    const max = 30;
    if (row.token.length <= max) {
      return row.token;
    }
    return `${row.token.slice(0, max - 1)}…`;
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
        {status === "idle" && (
          <div className="tokens__empty">Start typing to see tokens.</div>
        )}
        {hasRows &&
          rows.map((r, i) => (
            <div
              key={`${r.lexeme}-${r.token}-${i}`}
              className={`tokens__row ${i % 2 === 1 ? "is-alt" : ""}`}
            >
              <div className="tokens__cell tokens__cell--lexeme">
                {r.lexeme}
              </div>
              <div className="tokens__cell tokens__cell--token-value">
                <span title={r.token}>{renderToken(r)}</span>
              </div>
              <div className="tokens__cell tokens__cell--token-type">
                {r.tokenType.toUpperCase()}
              </div>
            </div>
          ))}
        {status !== "loading" && !hasRows && (
          <div className="tokens__empty">No tokens found.</div>
        )}
      </div>
    </div>
  );
}
