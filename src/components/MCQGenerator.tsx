import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Loader2, Download, CheckCircle2, XCircle, ChevronDown, ChevronUp, Trophy, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocument } from "@/context/DocumentContext";
import { API_BASE_URL, postJSON } from "@/lib/ragApi";

interface MCQ {
  question: string;
  options: string[];
  correct: number;
  explanations: string[];
}

export default function MCQGenerator() {
  const { document } = useDocument();
  const [count, setCount] = useState(5);
  const [topic, setTopic] = useState("");
  const [mcqs, setMcqs] = useState<MCQ[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);
  const [showExplanations, setShowExplanations] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const generateMCQs = async () => {
    if (!document) return;
    setIsGenerating(true);
    setMcqs([]);
    setSelectedAnswers({});
    setSubmitted(false);
    setShowExplanations({});
    setError(null);

    try {
      const data = await postJSON<{ mcqs: MCQ[] }>("/api/generate-mcq", {
        docId: document.docId,
        count,
        topic: topic || undefined,
      });
      if (!data?.mcqs || data.mcqs.length === 0) {
        setError("No MCQs returned. Try a different topic or increase the count.");
        return;
      }
      setMcqs(data.mcqs);
    } catch (err) {
      console.error(err);
      setError("Failed to generate MCQs. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = () => setSubmitted(true);

  const score = submitted
    ? mcqs.reduce((acc, mcq, i) => acc + (selectedAnswers[i] === mcq.correct ? 1 : 0), 0)
    : 0;

  const downloadPDF = (withAnswers: boolean) => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/mcq-pdf`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            docId: document?.docId,
            fileName: document?.fileName,
            topic,
            mcqs,
            withAnswers,
          }),
        });
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(text || `Failed to download PDF (${res.status})`);
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = window.document.createElement("a");
        a.href = url;
        a.download = withAnswers ? "mcq-with-answers.pdf" : "mcq-questions.pdf";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      } catch (e: any) {
        console.error(e);
        window.alert(e?.message || "Failed to download MCQ PDF.");
      }
    })();
  };

  const scorePercentage = mcqs.length > 0 ? (score / mcqs.length) * 100 : 0;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Config */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 shimmer">
        <h2 className="font-heading font-semibold text-lg mb-5 flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-primary/10">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          Generate MCQ Test
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block uppercase tracking-wider">Questions</label>
            <input
              type="number"
              min={1}
              max={50}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && generateMCQs()}
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/30 transition-all"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block uppercase tracking-wider">Topic Focus</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && generateMCQs()}
              placeholder="e.g. Neural Networks"
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/30 transition-all"
            />
          </div>
          <div className="flex items-end">
            <Button onClick={generateMCQs} disabled={isGenerating} variant="hero" className="w-full rounded-xl shadow-lg shadow-primary/20">
              {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Generate"}
            </Button>
          </div>
        </div>
      </motion.div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="text-destructive text-sm text-center"
        >
          {error}
        </motion.p>
      )}

      {/* MCQs */}
      <AnimatePresence>
        {mcqs.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {/* Download Buttons */}
            <div className="flex gap-2 flex-wrap">
              <Button variant="outline" size="sm" onClick={() => downloadPDF(false)} className="glass-subtle border-white/[0.08] hover:border-white/[0.15] rounded-xl">
                <Download className="w-3.5 h-3.5 mr-1.5" /> Questions Only
              </Button>
              <Button variant="outline" size="sm" onClick={() => downloadPDF(true)} className="glass-subtle border-white/[0.08] hover:border-white/[0.15] rounded-xl">
                <Download className="w-3.5 h-3.5 mr-1.5" /> With Answers
              </Button>
            </div>

            {/* Questions */}
            {mcqs.map((mcq, qi) => {
              const isCorrect = submitted && selectedAnswers[qi] === mcq.correct;
              const isWrong = submitted && selectedAnswers[qi] !== undefined && selectedAnswers[qi] !== mcq.correct;
              const selectedIndex = selectedAnswers[qi];
              const correctExplanation = mcq.explanations?.[mcq.correct] || "";
              const selectedExplanation = selectedIndex !== undefined ? mcq.explanations?.[selectedIndex] || "" : "";
              return (
                <motion.div
                  key={qi}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: qi * 0.05 }}
                  className={`glass-card p-6 transition-all duration-500 ${
                    submitted
                      ? isCorrect
                        ? "border-green-500/20 shadow-[0_0_30px_-10px_rgba(34,197,94,0.15)]"
                        : isWrong
                        ? "border-destructive/20 shadow-[0_0_30px_-10px_rgba(239,68,68,0.15)]"
                        : ""
                      : ""
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <p className="font-medium text-sm leading-relaxed">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-lg bg-primary/10 text-primary text-xs font-bold mr-2">
                        {qi + 1}
                      </span>
                      {mcq.question}
                    </p>
                    {submitted && (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                        {isCorrect ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                        ) : isWrong ? (
                          <XCircle className="w-5 h-5 text-destructive flex-shrink-0" />
                        ) : null}
                      </motion.div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {mcq.options.map((opt, oi) => {
                      const isSelected = selectedAnswers[qi] === oi;
                      const isCorrectOption = submitted && oi === mcq.correct;
                      return (
                        <motion.button
                          key={oi}
                          whileHover={!submitted ? { scale: 1.01 } : {}}
                          whileTap={!submitted ? { scale: 0.99 } : {}}
                          onClick={() => !submitted && setSelectedAnswers((prev) => ({ ...prev, [qi]: oi }))}
                          disabled={submitted}
                          className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-all duration-300 border ${
                            submitted
                              ? isCorrectOption
                                ? "border-green-500/30 bg-green-500/10 text-foreground"
                                : isSelected
                                ? "border-destructive/30 bg-destructive/10 text-foreground"
                                : "border-white/[0.06] bg-white/[0.02] text-muted-foreground"
                              : isSelected
                              ? "border-primary/30 bg-primary/10 text-foreground shadow-[0_0_20px_-5px_hsl(263_92%_60%/0.15)]"
                              : "border-white/[0.06] bg-white/[0.02] text-foreground hover:border-white/[0.12] hover:bg-white/[0.04]"
                          }`}
                        >
                          <span className="font-semibold mr-2 text-muted-foreground">{String.fromCharCode(65 + oi)}.</span>
                          {opt}
                        </motion.button>
                      );
                    })}
                  </div>
                  {submitted && (
                    <div className="mt-4">
                      <button
                        onClick={() => setShowExplanations((prev) => ({ ...prev, [qi]: !prev[qi] }))}
                        className="text-xs text-primary flex items-center gap-1.5 hover:underline font-medium"
                      >
                        {showExplanations[qi] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        View Explanation
                      </button>
                      <AnimatePresence>
                        {showExplanations[qi] && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                                <div className="mt-3 glass-subtle p-4 rounded-xl leading-relaxed">
                                  {submitted && isWrong && (
                                    <div className="space-y-3">
                                      <div>
                                        <p className="text-xs font-semibold text-primary mb-1">Correct answer explanation</p>
                                        <p className="text-base text-muted-foreground">{correctExplanation}</p>
                                      </div>
                                      <div>
                                        <p className="text-xs font-semibold text-primary mb-1">Your selected answer explanation</p>
                                        <p className="text-base text-muted-foreground">{selectedExplanation}</p>
                                      </div>
                                    </div>
                                  )}
                                  {submitted && isCorrect && (
                                    <div>
                                      <p className="text-xs font-semibold text-primary mb-1">Explanation</p>
                                      <p className="text-base text-muted-foreground">{correctExplanation}</p>
                                    </div>
                                  )}
                                </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </motion.div>
              );
            })}

            {/* Submit / Score */}
            {!submitted ? (
              <Button
                onClick={handleSubmit}
                variant="hero"
                className="w-full rounded-xl shadow-lg shadow-primary/20"
                disabled={Object.keys(selectedAnswers).length < mcqs.length}
              >
                <Target className="w-4 h-4 mr-2" />
                Submit Answers
              </Button>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-card p-8 text-center relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent" />
                <div className="relative z-10">
                  <Trophy className="w-10 h-10 text-primary mx-auto mb-4" />
                  <h3 className="font-heading font-bold text-3xl mb-1">
                    {score} / {mcqs.length}
                  </h3>
                  <div className="w-32 h-1.5 rounded-full bg-white/[0.06] mx-auto mt-3 mb-4 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${scorePercentage}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className="h-full rounded-full bg-gradient-to-r from-primary to-primary/60"
                    />
                  </div>
                  <p className="text-muted-foreground text-sm">
                    {score === mcqs.length
                      ? "Perfect score! 🎉"
                      : score >= mcqs.length * 0.7
                      ? "Great job! 💪"
                      : "Keep studying! 📚"}
                  </p>
                  <Button onClick={generateMCQs} variant="outline" className="mt-5 glass-subtle border-white/[0.08] rounded-xl">
                    Generate New Test
                  </Button>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
