import { useEffect, useMemo, useRef, useState } from "react";
import './Terminals.css';

export type Command = (args: string[]) => Promise<string> | string;

type Props = {
	commands?: Record<string, Command>; // extend with your own commands
	prompt?: string;                    // label before input
};
export default function Terminal({ commands = {}, prompt = "guest" }: Props) {
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

	const [out, setOut] = useState<string[]>(["Lexi Terminal — type `help`"]);
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
	if (!cmdline) return setLine("");

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
			if (res) setOut((o) => [...o, res]);
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
			return void run(line);
		}
		if (e.key === "ArrowUp") {
	e.preventDefault();
	const n = Math.min(hist.length - 1, idx + 1);
	setIdx(n);
			setLine(n >= 0 ? hist[n] : "");
		}
		if (e.key === "ArrowDown") {
	e.preventDefault();
	const n = Math.max(-1, idx - 1);
	setIdx(n);
			setLine(n >= 0 ? hist[n] : "");
		}
		if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
			setLine(""); // Ctrl/Cmd + C clears current line
		}
	};
	return (
		<div className="panel terminal" style={{ display: "grid", gridTemplateRows: "auto 1fr auto" }}>
			<div className="header">Terminal</div>
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
	let buf = "", q: "'" | '"' | null = null;
	for (let i = 0; i < s.length; i++) {
		const c = s[i];
		if (q) { if (c === q) q = null; else buf += c; continue; }
		if (c === "'" || c === '"') { q = c; continue; }
		if (/\s/.test(c)) { if (buf) { out.push(buf); buf = ""; } continue; }
		buf += c;
	}
	if (buf) out.push(buf);
	return out;
}
// import { useEffect, useMemo, useRef, useState } from "react";
// import './Terminals.css';


// export type Command = (args: string[]) => Promise<string> | string;

// type Props = {
//   commands?: Record<string, Command>; // extend with your own commands
//   prompt?: string;                    // label before input
// };

// export default function Terminal({ commands = {}, prompt = "guest" }: Props) {
//   const registry = useMemo<Record<string, Command>>(
//     () => ({
//       help: () =>
//         ["Built-ins:", "  help", "  clear", "  echo [text]", ""].join("\n"),
//       clear: () => "",
//       echo: (args) => args.join(" "),
//       ...commands,
//     }),
//     [commands]
//   );

//   const [out, setOut] = useState<string[]>(["Lexi Terminal — type `help`"]);
//   const [line, setLine] = useState("");
//   const [hist, setHist] = useState<string[]>([]);
//   const [idx, setIdx] = useState(-1);

//   const scrollRef = useRef<HTMLDivElement>(null);
//   const inputRef = useRef<HTMLInputElement>(null);

//   useEffect(() => {
//     scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
//   }, [out]);

//   useEffect(() => {
//     const el = scrollRef.current?.parentElement;
//     const focus = () => inputRef.current?.focus();
//     el?.addEventListener("click", focus);
//     return () => el?.removeEventListener("click", focus);
//   }, []);

//   const run = async (src: string) => {
//     setOut((o) => [...o, `$ ${src}`]);
//     const cmdline = src.trim();
//     if (!cmdline) return setLine("");

//     const [name, ...args] = splitArgs(cmdline);

//     if (name === "clear") {
//       setOut([]);
//       setLine("");
//       return;
//     }

//     const fn = registry[name];
//     if (!fn) {
//       setOut((o) => [...o, `command not found: ${name}`]);
//       setLine("");
//       return;
//     }

//     try {
//       const res = await fn(args);
//       if (res) setOut((o) => [...o, res]);
//     } catch (e: any) {
//       setOut((o) => [...o, `error: ${e?.message ?? String(e)}`]);
//     } finally {
//       setLine("");
//     }
//   };

//   const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
//     if (e.key === "Enter") {
//       setHist((h) => [line, ...h]);
//       setIdx(-1);
//       return void run(line);
//     }
//     if (e.key === "ArrowUp") {
//       e.preventDefault();
//       const n = Math.min(hist.length - 1, idx + 1);
//       setIdx(n);
//       setLine(n >= 0 ? hist[n] : "");
//     }
//     if (e.key === "ArrowDown") {
//       e.preventDefault();
//       const n = Math.max(-1, idx - 1);
//       setIdx(n);
//       setLine(n >= 0 ? hist[n] : "");
//     }
//     if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
//       setLine(""); // Ctrl/Cmd + C clears current line
//     }
//   };

//   return (
//     <div className="panel terminal" style={{ display: "grid", gridTemplateRows: "auto 1fr auto" }}>
//       <div className="header">Terminal</div>

//       <div ref={scrollRef} className="term-out" aria-live="polite">
//         {out.map((t, i) => (
//           <div key={i}>{t}</div>
//         ))}
//       </div>

//       <div className="term-input-row">
//         <span className="term-prompt">{prompt}$</span>
//         <input
//           ref={inputRef}
//           className="term-input"
//           value={line}
//           onChange={(e) => setLine(e.target.value)}
//           onKeyDown={onKey}
//           spellCheck={false}
//           autoCapitalize="off"
//           autoCorrect="off"
//           autoComplete="off"
//         />
//       </div>
//     </div>
//   );
// }

// /* minimal shell-style splitter: keeps quoted groups */
// function splitArgs(s: string): string[] {
//   const out: string[] = [];
//   let buf = "", q: "'" | '"' | null = null;
//   for (let i = 0; i < s.length; i++) {
//     const c = s[i];
//     if (q) { if (c === q) q = null; else buf += c; continue; }
//     if (c === "'" || c === '"') { q = c; continue; }
//     if (/\s/.test(c)) { if (buf) { out.push(buf); buf = ""; } continue; }
//     buf += c;
//   }
//   if (buf) out.push(buf);
//   return out;
// }
