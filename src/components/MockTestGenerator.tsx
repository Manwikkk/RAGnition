import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Loader2, Download, Sparkles, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocument } from "@/context/DocumentContext";
import { API_BASE_URL, postJSON } from "@/lib/ragApi";

interface MockTest {
  title: string;
  totalMarks: number;
  sections: {
    name: string;
    marksPerQuestion: number;
    questions: { question: string; answer: string }[];
  }[];
}

export default function MockTestGenerator() {
  const { document } = useDocument();
  const [totalMarks, setTotalMarks] = useState(50);
  const [topic, setTopic] = useState("");
  const [test, setTest] = useState<MockTest | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showAnswers, setShowAnswers] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const generateTest = async () => {
    if (!document) return;
    setIsGenerating(true);
    setTest(null);
    setError(null);

    try {
      const data = await postJSON<{ test: MockTest }>("/api/generate-mock-test", {
        docId: document.docId,
        totalMarks,
        topic: topic || undefined,
      });
      if (!data?.test) {
        setError("No mock test returned. Try a different topic.");
        return;
      }
      setTest(data.test);
    } catch (err) {
      console.error(err);
      setError("Failed to generate mock test. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadTest = async (withAnswers: boolean) => {
    if (!test || !document) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/mock-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          docId: document.docId,
          fileName: document.fileName,
          topic,
          test,
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
      a.download = withAnswers ? "mock-test-with-answers.pdf" : "mock-test-questions.pdf";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: any) {
      console.error(e);
      window.alert(e?.message || "Failed to download mock test PDF.");
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Config */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 shimmer">
        <h2 className="font-heading font-semibold text-lg mb-5 flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-primary/10">
            <BookOpen className="w-4 h-4 text-primary" />
          </div>
          Generate Mock Test
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block uppercase tracking-wider">Total Marks</label>
            <input
              type="number"
              min={20}
              max={100}
              value={totalMarks}
              onChange={(e) => setTotalMarks(Math.min(100, Number(e.target.value)))}
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && generateTest()}
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/30 transition-all"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block uppercase tracking-wider">Topic Focus</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && generateTest()}
              placeholder="e.g. Machine Learning"
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/30 transition-all"
            />
          </div>
          <div className="flex items-end">
            <Button onClick={generateTest} disabled={isGenerating} variant="hero" className="w-full rounded-xl shadow-lg shadow-primary/20">
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

      {/* Generated Test */}
      <AnimatePresence>
        {test && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="font-heading font-semibold">{test.title}</h3>
                <span className="glass-subtle px-2.5 py-1 rounded-full text-xs text-muted-foreground">
                  {test.totalMarks} marks
                </span>
              </div>
                <div className="flex items-center gap-2 flex-wrap justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => downloadTest(false)}
                    className="glass-subtle border-white/[0.08] hover:border-white/[0.15] rounded-xl"
                  >
                    <Download className="w-3.5 h-3.5 mr-1.5" /> Questions PDF
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => downloadTest(true)}
                    className="glass-subtle border-white/[0.08] hover:border-white/[0.15] rounded-xl"
                  >
                    <Download className="w-3.5 h-3.5 mr-1.5" /> With Answers PDF
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAnswers((v) => !v)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    {showAnswers ? "Hide Answers" : "Show Answers"}
                  </Button>
                </div>
            </div>

            {test.sections.map((section, si) => (
              <motion.div
                key={si}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: si * 0.1 }}
                className="glass-card p-6"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-2">
                    <div className="w-1 h-5 rounded-full bg-gradient-to-b from-primary to-primary/30" />
                    <h4 className="font-heading font-semibold text-sm text-foreground">{section.name}</h4>
                  </div>
                  <span className="glass-subtle px-2.5 py-1 rounded-full text-xs text-muted-foreground">
                    {section.marksPerQuestion} marks each
                  </span>
                </div>
                <div className="space-y-4">
                  {section.questions.map((q, qi) => (
                    <div key={qi} className="flex gap-3 text-sm group">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-lg bg-white/[0.04] text-muted-foreground text-xs font-mono flex-shrink-0 mt-0.5 group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                        {qi + 1}
                      </span>
                      <div className="space-y-2">
                        <p className="text-foreground/90 leading-relaxed">{q.question}</p>
                        {showAnswers && (
                          <p className="text-sm text-muted-foreground leading-relaxed glass-subtle p-3 rounded-xl">
                            {q.answer}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
