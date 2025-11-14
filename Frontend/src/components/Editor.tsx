import { useMemo, useState, useRef } from "react";
import MonacoEditor from "@monaco-editor/react";
import "./editor.css";

export type FileTab = {
  id: string;
  name: string;
  content: string;
};

type EditorProps = {
  initialFiles?: FileTab[];
  onChangeFiles?: (files: FileTab[], activeId: string) => void;
};

export default function Editor({ initialFiles, onChangeFiles }: EditorProps) {
  const seed: FileTab[] = useMemo(
    () =>
      initialFiles?.length
        ? initialFiles
        : [{ id: makeId(), name: "index.love", content: "" }],
    [] // run once
  );

  const [files, setFiles] = useState<FileTab[]>(seed);
  const [activeId, setActiveId] = useState<string>(seed[0].id);
  const active = files.find(f => f.id === activeId)!;
  

  const setState = (next: FileTab[], nextActive = activeId) => {
    setFiles(next);
    setActiveId(nextActive);
    onChangeFiles?.(next, nextActive);
  };


  const updateActiveContent = (v: string) =>
    setState(files.map(f => (f.id === activeId ? { ...f, content: v } : f)));
  // Monaco editor ref
  const editorRef = useRef<any>(null);

  function handleMount(editor: any, _monaco: any) {
    editorRef.current = editor;
  }

  function handleEditorDidMount(editor: any, monaco: any) {
    handleMount(editor, monaco);
    try {
      const s = getComputedStyle(document.documentElement);
      const panel = (s.getPropertyValue("--panel") || "#2b1414").trim() || "#2b1414";
      const text = (s.getPropertyValue("--text") || "#f7eaea").trim() || "#f7eaea";
      const muted = (s.getPropertyValue("--muted") || "rgba(255,255,255,0.45)").trim() || "rgba(255,255,255,0.45)";
      const accent = (s.getPropertyValue("--accent") || "#ffbfbf").trim() || "#ffbfbf";
      const border = (s.getPropertyValue("--border") || "rgba(255,255,255,0.06)").trim() || "rgba(255,255,255,0.06)";

      monaco.editor.defineTheme("loversDark", {
        base: "vs-dark",
        inherit: true,
        rules: [],
        colors: {
          "editor.background": panel,
          "editor.foreground": text,
          "editorLineNumber.foreground": muted,
          "editorLineNumber.activeForeground": accent,
          "editorCursor.foreground": accent,
          "editorLineHighlight.background": "rgba(255,255,255,0.02)",
          "editorGutter.background": panel,
          "editorIndentGuide.background": border,
          "editorIndentGuide.activeBackground": border,
        },
      });

      monaco.editor.setTheme("loversDark");
    } catch (e) {
      console.warn("Failed to set Monaco theme", e);
    }
  }

  return (
    <div className="editor">
      {/* Tabs removed — single-file editor view */}

      <div className="editor__body">
        <MonacoEditor
          height="100%"
          defaultValue={active.content}
          value={active.content}
          onChange={(v) => updateActiveContent(v ?? "")}
          onMount={handleEditorDidMount}
          theme={"loversDark"}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: 'Fira Code, Consolas, "Courier New", monospace',
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            wordWrap: "on",
            automaticLayout: true,
            lineNumbers: "on",
            renderLineHighlight: "line",
            scrollbar: {
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
              // prefer a visible, thin scrollbar so our CSS styling is visible
              useShadows: false,
              verticalHasArrows: false,
              horizontalHasArrows: false,
              handleMouseWheel: true,
              // 'renderVerticalScrollbar' prefers 'auto' or 'visible' at runtime;
              // cast to any below so TypeScript doesn't complain about shape differences.
            },
          } as any}
        />
      </div>
    </div>
  );
}

/* --- helpers/types --- */
function makeId() {
  return (globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2, 10));
}
// Tabs and related helpers removed on purpose — editor simplified to single textarea
