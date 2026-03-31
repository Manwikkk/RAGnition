import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Loader2, Download, Sparkles, ListChecks, LightbulbIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocument } from "@/context/DocumentContext";
import { postJSON, API_BASE_URL } from "@/lib/ragApi";

interface SummaryData {
  overview: string;
  keyPoints: string[];
  concepts: { term: string; definition: string }[];
  studyTips: string[];
}

export default function SummaryPanel() {
  const { document } = useDocument();
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [focus, setFocus] = useState("");

  const generate = async () => {
    if (!document) return;
    setIsGenerating(true);
    setSummary(null);
    setError(null);
    try {
      const data = await postJSON<{ summary: SummaryData }>("/api/summarize", {
        docId: document.docId,
        focus: focus || undefined,
      });
      if (!data?.summary) throw new Error("No summary returned");
      setSummary(data.summary);
    } catch (err: any) {
      setError(err?.message || "Failed to generate summary. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadSummaryPDF = async () => {
    if (!summary || !document) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/summary-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ docId: document.docId, fileName: document.fileName, summary }),
      });
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `summary-${document.fileName.replace(/\s+/g, "-")}.pdf`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: any) {
      window.alert(e?.message || "Failed to download summary PDF.");
    }
  };

  return (
    <div className="p-4 sm:p-6 space-y-5 overflow-y-auto h-full">
      {/* Config */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5 sm:p-6">
        <h2 className="font-heading font-semibold text-base sm:text-lg mb-4 flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500/20 to-green-500/20 flex items-center justify-center border border-cyan-500/10">
            <BookOpen className="w-4 h-4 text-cyan-400" />
          </div>
          Smart Summary
        </h2>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            placeholder="Optional: focus topic (e.g. Machine Learning)"
            className="flex-1 bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/30 transition-all"
          />
          <Button
            onClick={generate}
            disabled={isGenerating}
            className="rounded-xl shadow-lg shadow-primary/20 whitespace-nowrap"
          >
            {isGenerating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
            Generate Summary
          </Button>
        </div>
      </motion.div>

      {error && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-destructive text-sm text-center">
          {error}
        </motion.p>
      )}

      <AnimatePresence>
        {summary && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div className="flex items-center justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={downloadSummaryPDF}
                className="glass-subtle border-white/[0.08] hover:border-white/[0.15] rounded-xl"
              >
                <Download className="w-3.5 h-3.5 mr-1.5" /> Download PDF
              </Button>
            </div>

            {/* Overview */}
            <motion.div className="glass-card p-5 sm:p-6">
              <h3 className="font-heading font-semibold text-sm uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-primary" /> Overview
              </h3>
              <p className="text-sm text-foreground/90 leading-relaxed">{summary.overview}</p>
            </motion.div>

            {/* Key Points */}
            {summary.keyPoints?.length > 0 && (
              <motion.div className="glass-card p-5 sm:p-6">
                <h3 className="font-heading font-semibold text-sm uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
                  <ListChecks className="w-3.5 h-3.5 text-primary" /> Key Points
                </h3>
                <ul className="space-y-2.5">
                  {summary.keyPoints.map((pt, i) => (
                    <li key={i} className="flex gap-3 text-sm">
                      <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-xs flex items-center justify-center flex-shrink-0 mt-0.5 font-mono">
                        {i + 1}
                      </span>
                      <span className="text-foreground/85 leading-relaxed">{pt}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Key Concepts */}
            {summary.concepts?.length > 0 && (
              <motion.div className="glass-card p-5 sm:p-6">
                <h3 className="font-heading font-semibold text-sm uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
                  <BookOpen className="w-3.5 h-3.5 text-primary" /> Key Concepts
                </h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  {summary.concepts.map((c, i) => (
                    <div key={i} className="glass-subtle p-3.5 rounded-xl">
                      <p className="text-xs font-semibold text-primary mb-1">{c.term}</p>
                      <p className="text-xs text-muted-foreground leading-relaxed">{c.definition}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Study Tips */}
            {summary.studyTips?.length > 0 && (
              <motion.div className="glass-card p-5 sm:p-6">
                <h3 className="font-heading font-semibold text-sm uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
                  <LightbulbIcon className="w-3.5 h-3.5 text-yellow-400" /> Study Tips
                </h3>
                <ul className="space-y-2">
                  {summary.studyTips.map((tip, i) => (
                    <li key={i} className="flex gap-2.5 text-sm text-foreground/80">
                      <span className="text-yellow-400 flex-shrink-0 mt-0.5">✦</span>
                      <span className="leading-relaxed">{tip}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
