"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Download,
  Eye,
  FileText,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
  Upload as UploadIcon,
} from "lucide-react";

const MAX_PAPERS = 5;
const MIN_PAPERS = 3;
const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB

type SelectedFile = {
  // Stable client-side id so React doesn't reuse rows after a remove.
  id: string;
  file: File;
  // Object URL for the local "View PDF" preview — created lazily on
  // first View click and revoked on Remove / unmount.
  objectUrl: string | null;
};

type PipelineResult = {
  course_name?: string;
  paper_title?: string;
  exam_pattern_summary?: string;
  historical_backtest_score?: number | null;
  score_breakdown?: Record<string, number | null> | null;
  likely_topics?: Array<{
    topic?: string;
    reason?: string;
    confidence?: string;
    evidence_from_years?: string[];
  }>;
  marks_distribution?: {
    summary?: string;
    predicted_sections?: Array<{
      section?: string;
      marks?: string | number;
      notes?: string;
    }>;
  } | null;
  predicted_paper?: Array<{
    section?: string;
    question_number?: string;
    question?: string;
    marks?: string | number;
    topic?: string;
    question_type?: string;
    reason?: string;
    confidence?: string;
  }>;
  answer_guide?: Array<{
    question_ref?: string;
    answer_outline?: string;
    marking_notes?: string;
  }>;
  examiner_style_notes?: string;
  confidence_notes?: string;
  disclaimer?: string;
};

type ApiResponse = {
  ok: boolean;
  result?: PipelineResult;
  predicted_pdf_base64?: string;
  answer_pdf_base64?: string;
  error?: string;
};

const FEATURE_CHIPS = [
  { icon: Sparkles, label: "Pattern analysis" },
  { icon: Eye, label: "Backtest" },
  { icon: Download, label: "PDF export" },
];

const ANALYZED_ITEMS = [
  { label: "Repeated topics across years" },
  { label: "Marks distribution by section" },
  { label: "Question style and phrasing" },
  { label: "Skipped or weakly-tested topics" },
  { label: "Difficulty trend over time" },
  { label: "Examiner pattern and emphasis" },
];

const DISCLAIMER_TEXT =
  "This is a pattern-based mock paper, not a guaranteed future exam paper.";

const EXAM_DETAILS_PLACEHOLDER = [
  "Your university name",
  "Your course or subject name",
  "Year / semester",
  "Exam name",
  "Professor / lecturer name (optional)",
  "Exam type: final exam / midterm / quiz",
  "Topics teacher focused on (optional)",
  "Any notes (optional)",
].join("\n");

function newId(): string {
  return `f-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function base64ToBlob(b64: string, mime = "application/pdf"): Blob {
  const bytes = atob(b64);
  const len = bytes.length;
  const u8 = new Uint8Array(len);
  for (let i = 0; i < len; i++) u8[i] = bytes.charCodeAt(i);
  return new Blob([u8], { type: mime });
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revoke shortly after so the browser has time to start the download.
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

export default function ExamForecastPage() {
  const [selected, setSelected] = useState<SelectedFile[]>([]);
  const [examDetails, setExamDetails] = useState("");
  const [runBacktest, setRunBacktest] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [predictedPdfB64, setPredictedPdfB64] = useState<string>("");
  const [answerPdfB64, setAnswerPdfB64] = useState<string>("");

  // Two refs: one for the big initial dropzone's <input>, one for the
  // smaller "Add more PDFs" button that reuses the same picker handler.
  const initialPickerRef = useRef<HTMLInputElement>(null);
  const morePickerRef = useRef<HTMLInputElement>(null);

  const canSubmit = selected.length >= MIN_PAPERS && !submitting;

  useEffect(() => {
    return () => {
      // Revoke all object URLs on unmount so we don't leak handles.
      selected.forEach((s) => {
        if (s.objectUrl) URL.revokeObjectURL(s.objectUrl);
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function addFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setErrorMsg(null);
    const remaining = MAX_PAPERS - selected.length;
    if (remaining <= 0) {
      setErrorMsg(`You can upload up to ${MAX_PAPERS} past papers.`);
      return;
    }
    const incoming: SelectedFile[] = [];
    const rejects: string[] = [];
    for (let i = 0; i < files.length && incoming.length < remaining; i++) {
      const f = files[i];
      const lowerName = f.name.toLowerCase();
      const looksLikePdf =
        lowerName.endsWith(".pdf") ||
        f.type === "application/pdf" ||
        f.type === "application/x-pdf";
      if (!looksLikePdf) {
        rejects.push(`"${f.name}" is not a PDF`);
        continue;
      }
      if (f.size > MAX_FILE_BYTES) {
        rejects.push(`"${f.name}" exceeds 10 MB`);
        continue;
      }
      incoming.push({ id: newId(), file: f, objectUrl: null });
    }
    if (rejects.length > 0) {
      setErrorMsg(rejects.join(" · "));
    }
    if (incoming.length > 0) {
      setSelected((prev) => [...prev, ...incoming]);
    }
    if (files.length > remaining) {
      setErrorMsg(
        (prev) =>
          (prev ? prev + " · " : "") +
          `Only the first ${remaining} file(s) were added — limit is ${MAX_PAPERS}.`,
      );
    }
  }

  function removeAt(id: string) {
    setSelected((prev) => {
      const next: SelectedFile[] = [];
      for (const s of prev) {
        if (s.id === id) {
          if (s.objectUrl) URL.revokeObjectURL(s.objectUrl);
        } else {
          next.push(s);
        }
      }
      return next;
    });
  }

  function viewFile(s: SelectedFile) {
    // Create the object URL on demand so unviewed files don't allocate.
    let url = s.objectUrl;
    if (!url) {
      url = URL.createObjectURL(s.file);
      setSelected((prev) =>
        prev.map((row) => (row.id === s.id ? { ...row, objectUrl: url } : row)),
      );
    }
    window.open(url, "_blank", "noopener,noreferrer");
  }

  async function submit() {
    if (selected.length < MIN_PAPERS) return;
    setSubmitting(true);
    setErrorMsg(null);
    setResult(null);
    setPredictedPdfB64("");
    setAnswerPdfB64("");

    const fd = new FormData();
    for (const s of selected) {
      fd.append("past_papers", s.file, s.file.name);
    }
    if (examDetails.trim()) fd.append("exam_details", examDetails.trim());
    fd.append("run_backtest", runBacktest ? "true" : "false");

    try {
      const res = await fetch("/api/exam-forecast", {
        method: "POST",
        body: fd,
      });
      const data = (await res.json()) as ApiResponse;
      if (!res.ok || !data.ok) {
        setErrorMsg(data.error || `Request failed (${res.status}).`);
        setSubmitting(false);
        return;
      }
      setResult(data.result || null);
      setPredictedPdfB64(data.predicted_pdf_base64 || "");
      setAnswerPdfB64(data.answer_pdf_base64 || "");
      if (data.error) {
        // Partial success: pipeline ran but PDF export failed.
        setErrorMsg(data.error);
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      setErrorMsg(`Network error: ${message}`);
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    setSelected((prev) => {
      prev.forEach((s) => {
        if (s.objectUrl) URL.revokeObjectURL(s.objectUrl);
      });
      return [];
    });
    setExamDetails("");
    setRunBacktest(true);
    setResult(null);
    setPredictedPdfB64("");
    setAnswerPdfB64("");
    setErrorMsg(null);
  }

  return (
    <div
      className="min-h-screen w-full text-white"
      style={{
        background:
          "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(134,239,172,0.06), transparent 60%), #0a0a0c",
        fontFamily: "'Plus Jakarta Sans', sans-serif",
      }}
    >
      <div className="mx-auto w-full max-w-[1200px] px-5 py-10 md:px-8 md:py-14">
        <Header />

        <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          {/* ── LEFT COLUMN: inputs + result ── */}
          <div className="space-y-5">
            <PastPapersCard
              selected={selected}
              onAddFiles={addFiles}
              onRemove={removeAt}
              onView={viewFile}
              initialPickerRef={initialPickerRef}
              morePickerRef={morePickerRef}
            />

            <ExamDetailsCard
              value={examDetails}
              onChange={setExamDetails}
              runBacktest={runBacktest}
              onRunBacktestChange={setRunBacktest}
            />

            <AnimatePresence>
              {errorMsg && (
                <motion.div
                  key="err"
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="rounded-xl border px-4 py-3 text-[0.86rem]"
                  style={{
                    background: "rgba(248,113,113,0.07)",
                    borderColor: "rgba(248,113,113,0.28)",
                    color: "rgba(248,113,113,0.95)",
                  }}
                >
                  {errorMsg}
                </motion.div>
              )}
            </AnimatePresence>

            <GenerateBar
              count={selected.length}
              canSubmit={canSubmit}
              submitting={submitting}
              onSubmit={submit}
            />

            <AnimatePresence>
              {result && (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <ResultPanel
                    result={result}
                    predictedB64={predictedPdfB64}
                    answerB64={answerPdfB64}
                    onReset={reset}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── RIGHT COLUMN: explainer ── */}
          <aside className="space-y-5">
            <AnalyzedCard />
            <DisclaimerCard />
          </aside>
        </div>
      </div>
    </div>
  );
}

function Header() {
  return (
    <div>
      <h1
        className="text-[2.2rem] font-extrabold leading-[1.1] tracking-tight md:text-[2.6rem]"
        style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
      >
        Smart Exam Forecast
      </h1>
      <p
        className="mt-3 max-w-[640px] text-[1.02rem] leading-relaxed"
        style={{ color: "rgba(220,230,240,0.74)" }}
      >
        Upload past papers. Alex studies the pattern and generates a
        high-probability mock paper for your next exam.
      </p>
      <p
        className="mt-1 text-[0.92rem] italic"
        style={{ color: "rgba(200,210,220,0.5)" }}
      >
        Not mind reading. Just pattern reading.
      </p>
      <div className="mt-5 flex flex-wrap items-center gap-2">
        {FEATURE_CHIPS.map(({ icon: Icon, label }) => (
          <span
            key={label}
            className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-[0.78rem] font-medium"
            style={{
              background: "rgba(255,255,255,0.03)",
              borderColor: "rgba(255,255,255,0.08)",
              color: "rgba(220,230,240,0.78)",
            }}
          >
            <Icon size={13} className="opacity-80" />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

function PastPapersCard({
  selected,
  onAddFiles,
  onRemove,
  onView,
  initialPickerRef,
  morePickerRef,
}: {
  selected: SelectedFile[];
  onAddFiles: (files: FileList | null) => void;
  onRemove: (id: string) => void;
  onView: (s: SelectedFile) => void;
  initialPickerRef: React.RefObject<HTMLInputElement | null>;
  morePickerRef: React.RefObject<HTMLInputElement | null>;
}) {
  const [dragging, setDragging] = useState(false);
  const atCap = selected.length >= MAX_PAPERS;

  return (
    <section
      className="rounded-2xl border p-5 md:p-6"
      style={{
        background: "rgba(255,255,255,0.025)",
        borderColor: "rgba(255,255,255,0.07)",
      }}
    >
      <div className="mb-3 flex items-center gap-2">
        <SectionLabel>Past papers</SectionLabel>
        <RequiredChip />
        <div className="flex-1" />
        <span
          className="text-[0.78rem] font-medium"
          style={{ color: "rgba(200,210,220,0.55)" }}
        >
          {selected.length} / {MAX_PAPERS}
        </span>
      </div>

      {selected.length === 0 ? (
        <Dropzone
          onDrop={onAddFiles}
          dragging={dragging}
          setDragging={setDragging}
          inputRef={initialPickerRef}
          label="Drop 3–5 past paper PDFs, or click to browse"
          subLabel="PDF only · up to 10 MB each"
        />
      ) : (
        <>
          <div className="space-y-2">
            {selected.map((s) => (
              <FileCard
                key={s.id}
                file={s.file}
                onView={() => onView(s)}
                onRemove={() => onRemove(s.id)}
              />
            ))}
          </div>
          {!atCap && (
            <div className="mt-3">
              <input
                ref={morePickerRef}
                type="file"
                accept="application/pdf,.pdf"
                multiple
                className="hidden"
                onChange={(e) => {
                  onAddFiles(e.target.files);
                  // Reset so picking the same file again still fires change.
                  e.target.value = "";
                }}
              />
              <button
                type="button"
                onClick={() => morePickerRef.current?.click()}
                className="inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-[0.86rem] font-semibold transition-colors"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  borderColor: "rgba(255,255,255,0.10)",
                  color: "rgba(236,240,244,0.92)",
                  cursor: "pointer",
                }}
              >
                <Plus size={14} />
                Add more PDFs
              </button>
            </div>
          )}
          {atCap && (
            <p
              className="mt-3 text-[0.78rem]"
              style={{ color: "rgba(200,210,220,0.55)" }}
            >
              5 of 5 — remove one to add another.
            </p>
          )}
        </>
      )}
    </section>
  );
}

function Dropzone({
  onDrop,
  dragging,
  setDragging,
  inputRef,
  label,
  subLabel,
}: {
  onDrop: (files: FileList | null) => void;
  dragging: boolean;
  setDragging: (b: boolean) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  label: string;
  subLabel: string;
}) {
  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        onDrop(e.dataTransfer.files);
      }}
      className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed px-6 py-10 text-center transition-all"
      style={{
        background: dragging
          ? "rgba(134,239,172,0.04)"
          : "rgba(255,255,255,0.02)",
        borderColor: dragging
          ? "rgba(134,239,172,0.42)"
          : "rgba(255,255,255,0.14)",
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        className="hidden"
        onChange={(e) => {
          onDrop(e.target.files);
          e.target.value = "";
        }}
      />
      <div
        className="mb-3 flex h-10 w-10 items-center justify-center rounded-full"
        style={{
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.08)",
        }}
      >
        <UploadIcon size={18} style={{ color: "rgba(220,230,240,0.7)" }} />
      </div>
      <div
        className="text-[0.92rem] font-semibold"
        style={{ color: "rgba(236,240,244,0.92)" }}
      >
        {label}
      </div>
      <div
        className="mt-1 text-[0.78rem]"
        style={{ color: "rgba(200,210,220,0.55)" }}
      >
        {subLabel}
      </div>
    </div>
  );
}

function FileCard({
  file,
  onView,
  onRemove,
}: {
  file: File;
  onView: () => void;
  onRemove: () => void;
}) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl border px-3 py-2.5"
      style={{
        background: "rgba(255,255,255,0.04)",
        borderColor: "rgba(255,255,255,0.08)",
      }}
    >
      <div
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
        style={{
          background: "rgba(134,239,172,0.10)",
          border: "1px solid rgba(134,239,172,0.22)",
        }}
      >
        <FileText size={15} style={{ color: "rgba(134,239,172,0.92)" }} />
      </div>
      <div className="min-w-0 flex-1">
        <div
          className="truncate text-[0.9rem] font-medium"
          style={{ color: "rgba(236,240,244,0.94)" }}
          title={file.name}
        >
          {file.name}
        </div>
        <div
          className="mt-0.5 text-[0.74rem]"
          style={{ color: "rgba(200,210,220,0.55)" }}
        >
          {formatBytes(file.size)}
        </div>
      </div>
      <button
        type="button"
        onClick={onView}
        className="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[0.78rem] font-semibold transition-colors"
        style={{
          background: "transparent",
          borderColor: "rgba(255,255,255,0.10)",
          color: "rgba(220,230,240,0.85)",
          cursor: "pointer",
        }}
        aria-label="View PDF"
      >
        <Eye size={13} />
        View PDF
      </button>
      <button
        type="button"
        onClick={onRemove}
        className="inline-flex h-8 w-8 items-center justify-center rounded-lg transition-colors"
        style={{
          color: "rgba(255,255,255,0.5)",
          background: "transparent",
          cursor: "pointer",
        }}
        aria-label="Remove file"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

function ExamDetailsCard({
  value,
  onChange,
  runBacktest,
  onRunBacktestChange,
}: {
  value: string;
  onChange: (v: string) => void;
  runBacktest: boolean;
  onRunBacktestChange: (b: boolean) => void;
}) {
  return (
    <section
      className="rounded-2xl border p-5 md:p-6"
      style={{
        background: "rgba(255,255,255,0.025)",
        borderColor: "rgba(255,255,255,0.07)",
      }}
    >
      <SectionLabel>Exam details</SectionLabel>
      <p
        className="mt-1 mb-3 text-[0.82rem]"
        style={{ color: "rgba(200,210,220,0.62)" }}
      >
        Optional context — the more Alex knows, the sharper the forecast.
      </p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={EXAM_DETAILS_PLACEHOLDER}
        rows={9}
        className="w-full resize-y rounded-xl border px-3.5 py-3 text-[0.92rem] leading-relaxed outline-none focus:ring-2"
        style={{
          background: "rgba(255,255,255,0.02)",
          borderColor: "rgba(255,255,255,0.10)",
          color: "rgba(236,240,244,0.95)",
          fontFamily: "'Plus Jakarta Sans', sans-serif",
        }}
      />
      <label className="mt-3 inline-flex cursor-pointer items-center gap-2 select-none">
        <input
          type="checkbox"
          checked={runBacktest}
          onChange={(e) => onRunBacktestChange(e.target.checked)}
          className="h-4 w-4 cursor-pointer"
          style={{ accentColor: "#86efac" }}
        />
        <span
          className="text-[0.86rem] font-medium"
          style={{ color: "rgba(220,230,240,0.82)" }}
        >
          Historical backtest
        </span>
        <span
          className="text-[0.78rem]"
          style={{ color: "rgba(200,210,220,0.5)" }}
        >
          Score the prediction against your most recent paper.
        </span>
      </label>
    </section>
  );
}

function GenerateBar({
  count,
  canSubmit,
  submitting,
  onSubmit,
}: {
  count: number;
  canSubmit: boolean;
  submitting: boolean;
  onSubmit: () => void;
}) {
  const needed = Math.max(MIN_PAPERS - count, 0);
  return (
    <div
      className="flex flex-wrap items-center gap-3 rounded-2xl border px-5 py-4"
      style={{
        background: "rgba(255,255,255,0.025)",
        borderColor: "rgba(255,255,255,0.07)",
      }}
    >
      <div className="flex-1 min-w-0">
        <div
          className="text-[0.92rem] font-semibold"
          style={{ color: "rgba(236,240,244,0.95)" }}
        >
          {submitting
            ? "Running pattern analysis…"
            : count >= MIN_PAPERS
              ? "Ready to generate"
              : `Add ${needed} more past paper${needed === 1 ? "" : "s"}`}
        </div>
        <div
          className="mt-0.5 text-[0.78rem]"
          style={{ color: "rgba(200,210,220,0.55)" }}
        >
          {submitting
            ? "This usually takes 30–90 seconds — multiple LLM passes."
            : `Generate Forecast unlocks at ${MIN_PAPERS} PDFs.`}
        </div>
      </div>
      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSubmit}
        className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-[0.92rem] font-bold transition-all"
        style={{
          background: canSubmit
            ? "rgba(134,239,172,0.95)"
            : "rgba(255,255,255,0.06)",
          color: canSubmit ? "#0b1410" : "rgba(220,230,240,0.45)",
          cursor: canSubmit ? "pointer" : "not-allowed",
          boxShadow: canSubmit
            ? "0 1px 0 0 rgba(0,0,0,0.2), 0 8px 24px -10px rgba(134,239,172,0.4)"
            : "none",
        }}
      >
        {submitting ? (
          <RefreshCw size={15} className="animate-spin" />
        ) : (
          <Sparkles size={15} />
        )}
        Generate Forecast
      </button>
    </div>
  );
}

function ResultPanel({
  result,
  predictedB64,
  answerB64,
  onReset,
}: {
  result: PipelineResult;
  predictedB64: string;
  answerB64: string;
  onReset: () => void;
}) {
  const backtest =
    typeof result.historical_backtest_score === "number"
      ? Math.round(result.historical_backtest_score)
      : null;

  const topics = result.likely_topics ?? [];
  const predictedPaper = result.predicted_paper ?? [];

  const onDownloadPredicted = () => {
    if (!predictedB64) return;
    downloadBlob(base64ToBlob(predictedB64), "alex_predicted_paper.pdf");
  };
  const onDownloadAnswer = () => {
    if (!answerB64) return;
    downloadBlob(base64ToBlob(answerB64), "alex_answer_guide.pdf");
  };

  return (
    <section
      className="rounded-2xl border p-5 md:p-6"
      style={{
        background:
          "linear-gradient(180deg, rgba(34,197,94,0.04) 0%, rgba(255,255,255,0.025) 60%)",
        borderColor: "rgba(134,239,172,0.18)",
      }}
    >
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <SectionLabel>Forecast ready</SectionLabel>
          <div
            className="mt-1 text-[1.18rem] font-extrabold leading-tight"
            style={{ color: "rgba(236,240,244,0.97)" }}
          >
            {result.paper_title || "Predicted Mock Paper"}
          </div>
          {result.course_name && (
            <div
              className="mt-0.5 text-[0.88rem]"
              style={{ color: "rgba(200,210,220,0.68)" }}
            >
              {result.course_name}
            </div>
          )}
        </div>
        {backtest !== null && (
          <div
            className="rounded-xl border px-4 py-2 text-center"
            style={{
              background: "rgba(34,197,94,0.10)",
              borderColor: "rgba(134,239,172,0.30)",
            }}
          >
            <div
              className="text-[0.66rem] font-bold uppercase tracking-wider"
              style={{ color: "rgba(134,239,172,0.92)" }}
            >
              Backtest
            </div>
            <div
              className="text-[1.2rem] font-extrabold leading-none"
              style={{ color: "rgba(236,240,244,0.96)" }}
            >
              {backtest}
              <span
                className="ml-0.5 text-[0.86rem] font-semibold"
                style={{ color: "rgba(200,210,220,0.55)" }}
              >
                /100
              </span>
            </div>
          </div>
        )}
      </div>

      {result.exam_pattern_summary && (
        <p
          className="mt-4 text-[0.92rem] leading-relaxed"
          style={{ color: "rgba(220,230,240,0.82)" }}
        >
          {result.exam_pattern_summary}
        </p>
      )}

      <div className="mt-5 flex flex-wrap gap-2">
        <DownloadButton
          label="Predicted paper PDF"
          disabled={!predictedB64}
          onClick={onDownloadPredicted}
          primary
        />
        <DownloadButton
          label="Answer guide PDF"
          disabled={!answerB64}
          onClick={onDownloadAnswer}
        />
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-[0.84rem] font-semibold transition-colors"
          style={{
            background: "transparent",
            borderColor: "rgba(255,255,255,0.10)",
            color: "rgba(220,230,240,0.78)",
            cursor: "pointer",
          }}
        >
          <RefreshCw size={13} />
          Start over
        </button>
      </div>

      {topics.length > 0 && (
        <div className="mt-6">
          <SectionLabel>Likely topics</SectionLabel>
          <div className="mt-3 space-y-2">
            {topics.slice(0, 8).map((t, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-xl border px-3.5 py-2.5"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  borderColor: "rgba(255,255,255,0.06)",
                }}
              >
                <div className="min-w-0 flex-1">
                  <div
                    className="text-[0.92rem] font-semibold"
                    style={{ color: "rgba(236,240,244,0.94)" }}
                  >
                    {t.topic || "—"}
                  </div>
                  {t.reason && (
                    <div
                      className="mt-1 text-[0.82rem] leading-relaxed"
                      style={{ color: "rgba(200,210,220,0.68)" }}
                    >
                      {t.reason}
                    </div>
                  )}
                </div>
                {t.confidence && <ConfidenceChip level={t.confidence} />}
              </div>
            ))}
          </div>
        </div>
      )}

      {predictedPaper.length > 0 && (
        <div className="mt-6">
          <SectionLabel>Predicted questions</SectionLabel>
          <div className="mt-3 space-y-2">
            {predictedPaper.slice(0, 12).map((q, i) => (
              <div
                key={i}
                className="rounded-xl border px-3.5 py-3"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  borderColor: "rgba(255,255,255,0.06)",
                }}
              >
                <div className="flex flex-wrap items-baseline gap-2">
                  {(q.section || q.question_number) && (
                    <span
                      className="text-[0.74rem] font-bold uppercase tracking-wider"
                      style={{ color: "rgba(134,239,172,0.85)" }}
                    >
                      {[q.section, q.question_number]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  )}
                  {q.marks !== undefined && q.marks !== "" && (
                    <span
                      className="text-[0.74rem] font-semibold"
                      style={{ color: "rgba(200,210,220,0.55)" }}
                    >
                      {String(q.marks)} marks
                    </span>
                  )}
                </div>
                <div
                  className="mt-1 text-[0.92rem] leading-relaxed"
                  style={{ color: "rgba(236,240,244,0.92)" }}
                >
                  {q.question || "—"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.disclaimer && (
        <p
          className="mt-5 text-[0.78rem] italic"
          style={{ color: "rgba(200,210,220,0.55)" }}
        >
          {result.disclaimer}
        </p>
      )}
    </section>
  );
}

function DownloadButton({
  label,
  onClick,
  disabled,
  primary,
}: {
  label: string;
  onClick: () => void;
  disabled: boolean;
  primary?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-[0.86rem] font-bold transition-colors"
      style={{
        background: disabled
          ? "rgba(255,255,255,0.04)"
          : primary
            ? "rgba(134,239,172,0.92)"
            : "rgba(255,255,255,0.06)",
        color: disabled
          ? "rgba(220,230,240,0.4)"
          : primary
            ? "#0b1410"
            : "rgba(236,240,244,0.92)",
        border: primary ? "none" : "1px solid rgba(255,255,255,0.10)",
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      <Download size={14} />
      {label}
    </button>
  );
}

function ConfidenceChip({ level }: { level: string }) {
  const normalized = level.toLowerCase();
  const tone =
    normalized === "high"
      ? {
          bg: "rgba(34,197,94,0.12)",
          border: "rgba(134,239,172,0.30)",
          color: "rgba(134,239,172,0.95)",
        }
      : normalized === "medium"
        ? {
            bg: "rgba(251,191,36,0.10)",
            border: "rgba(251,191,36,0.28)",
            color: "rgba(251,191,36,0.95)",
          }
        : {
            bg: "rgba(255,255,255,0.06)",
            border: "rgba(255,255,255,0.10)",
            color: "rgba(220,230,240,0.7)",
          };
  return (
    <span
      className="inline-flex shrink-0 items-center rounded-full border px-2.5 py-0.5 text-[0.7rem] font-bold uppercase tracking-wider"
      style={{
        background: tone.bg,
        borderColor: tone.border,
        color: tone.color,
      }}
    >
      {level}
    </span>
  );
}

function AnalyzedCard() {
  return (
    <section
      className="rounded-2xl border p-5"
      style={{
        background: "rgba(255,255,255,0.025)",
        borderColor: "rgba(255,255,255,0.07)",
      }}
    >
      <SectionLabel>What Alex analyzes</SectionLabel>
      <ul className="mt-3 space-y-2.5">
        {ANALYZED_ITEMS.map((it) => (
          <li
            key={it.label}
            className="flex items-center gap-2.5 text-[0.88rem]"
            style={{ color: "rgba(220,230,240,0.82)" }}
          >
            <span
              className="inline-block h-1.5 w-1.5 rounded-full"
              style={{ background: "rgba(134,239,172,0.85)" }}
            />
            {it.label}
          </li>
        ))}
      </ul>
    </section>
  );
}

function DisclaimerCard() {
  return (
    <section
      className="rounded-2xl border p-4"
      style={{
        background: "rgba(255,255,255,0.02)",
        borderColor: "rgba(255,255,255,0.06)",
      }}
    >
      <p
        className="text-[0.78rem] leading-relaxed"
        style={{ color: "rgba(200,210,220,0.55)" }}
      >
        {DISCLAIMER_TEXT}
      </p>
    </section>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="text-[0.68rem] font-bold uppercase"
      style={{
        color: "rgba(160,170,180,0.55)",
        letterSpacing: "0.14em",
      }}
    >
      {children}
    </div>
  );
}

function RequiredChip() {
  return (
    <span
      className="inline-block rounded-full border px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wider"
      style={{
        background: "rgba(34,197,94,0.10)",
        borderColor: "rgba(134,239,172,0.30)",
        color: "rgba(134,239,172,0.92)",
      }}
    >
      Required
    </span>
  );
}
