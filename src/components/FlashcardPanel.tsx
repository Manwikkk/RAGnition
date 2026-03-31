import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, Loader2, ChevronLeft, ChevronRight, RotateCcw, Sparkles, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocument } from "@/context/DocumentContext";
import { postJSON } from "@/lib/ragApi";

interface Flashcard {
  front: string;
  back: string;
  hint?: string;
}

export default function FlashcardPanel() {
  const { document } = useDocument();
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(10);
  const [topic, setTopic] = useState("");
  const [known, setKnown] = useState<Set<number>>(new Set());
  const [showHint, setShowHint] = useState(false);

  const generate = async () => {
    if (!document) return;
    setIsGenerating(true);
    setCards([]);
    setError(null);
    setCurrent(0);
    setFlipped(false);
    setKnown(new Set());
    setShowHint(false);
    try {
      const data = await postJSON<{ flashcards: Flashcard[] }>("/api/flashcards", {
        docId: document.docId,
        count,
        topic: topic || undefined,
      });
      if (!data?.flashcards?.length) throw new Error("No flashcards returned");
      setCards(data.flashcards);
    } catch (err: any) {
      setError(err?.message || "Failed to generate flashcards.");
    } finally {
      setIsGenerating(false);
    }
  };

  const next = () => {
    if (current < cards.length - 1) {
      setCurrent((c) => c + 1);
      setFlipped(false);
      setShowHint(false);
    }
  };

  const prev = () => {
    if (current > 0) {
      setCurrent((c) => c - 1);
      setFlipped(false);
      setShowHint(false);
    }
  };

  const toggleKnown = () => {
    setKnown((prev) => {
      const next = new Set(prev);
      if (next.has(current)) next.delete(current);
      else next.add(current);
      return next;
    });
  };

  const resetAll = () => {
    setCurrent(0);
    setFlipped(false);
    setKnown(new Set());
    setShowHint(false);
  };

  const card = cards[current];

  return (
    <div className="p-4 sm:p-6 space-y-5 overflow-y-auto h-full">
      {/* Config */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5 sm:p-6">
        <h2 className="font-heading font-semibold text-base sm:text-lg mb-4 flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-pink-500/20 to-orange-500/20 flex items-center justify-center border border-pink-500/10">
            <Layers className="w-4 h-4 text-pink-400" />
          </div>
          Flashcards
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block uppercase tracking-wider">Cards</label>
            <input
              type="number"
              min={3}
              max={30}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && generate()}
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block uppercase tracking-wider">Topic</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !isGenerating && generate()}
              placeholder="e.g. Chapter 3"
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
            />
          </div>
          <div className="flex items-end">
            <Button onClick={generate} disabled={isGenerating} className="w-full rounded-xl shadow-lg shadow-primary/20">
              {isGenerating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
              Generate
            </Button>
          </div>
        </div>
      </motion.div>

      {error && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-destructive text-sm text-center">
          {error}
        </motion.p>
      )}

      <AnimatePresence>
        {cards.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {/* Progress */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Card {current + 1} of {cards.length}</span>
              <span className="text-green-400">{known.size} known</span>
              <button onClick={resetAll} className="flex items-center gap-1 hover:text-foreground transition-colors">
                <RotateCcw className="w-3 h-3" /> Reset
              </button>
            </div>
            <div className="w-full bg-white/[0.04] rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-gradient-to-r from-primary to-primary/60 transition-all duration-500"
                style={{ width: `${((current + 1) / cards.length) * 100}%` }}
              />
            </div>

            {/* Card — pure CSS 3D flip for smooth, glitch-free animation */}
            <div
              className="relative h-56 sm:h-64 cursor-pointer select-none"
              style={{ perspective: "1200px" }}
              onClick={() => setFlipped((v) => !v)}
            >
              <div
                style={{
                  position: "relative",
                  width: "100%",
                  height: "100%",
                  transformStyle: "preserve-3d",
                  transition: "transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1.0)",
                  transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
                }}
              >
                {/* Front face */}
                <div
                  className="absolute inset-0 rounded-2xl flex flex-col items-center justify-center p-6 sm:p-8 border border-white/10"
                  style={{
                    backfaceVisibility: "hidden",
                    WebkitBackfaceVisibility: "hidden",
                    background: "linear-gradient(135deg, hsl(230 40% 12%) 0%, hsl(260 40% 10%) 100%)",
                    boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
                  }}
                >
                  <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                    <Layers className="w-5 h-5 text-blue-400" />
                  </div>
                  <span className="text-xs uppercase tracking-[0.2em] text-blue-400/80 mb-2 font-semibold">Question</span>
                  <p className="text-lg sm:text-xl text-foreground text-center leading-relaxed font-medium">
                    {card.front}
                  </p>
                  {card.hint && (
                    <button
                      onClick={(e) => { e.stopPropagation(); setShowHint((v) => !v); }}
                      className="mt-5 text-xs text-muted-foreground/60 hover:text-muted-foreground flex items-center gap-1.5 transition-colors bg-white/5 px-3 py-1.5 rounded-full"
                    >
                      {showHint ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      {showHint ? "Hide Hint" : "Show Hint"}
                    </button>
                  )}
                  {showHint && card.hint && (
                    <p className="mt-3 text-sm text-blue-200/60 italic max-w-sm text-center">{card.hint}</p>
                  )}
                  <div className="absolute bottom-5 flex items-center gap-2 text-xs text-muted-foreground/50">
                    <RotateCcw className="w-3 h-3" />
                    <span>Click to reveal answer</span>
                  </div>
                </div>

                {/* Back face — rotated 180° in place, visible when card is flipped */}
                <div
                  className="absolute inset-0 rounded-2xl flex flex-col items-center justify-center p-6 sm:p-8 border border-primary/20"
                  style={{
                    backfaceVisibility: "hidden",
                    WebkitBackfaceVisibility: "hidden",
                    transform: "rotateY(180deg)",
                    background: "linear-gradient(135deg, hsl(280 60% 12%) 0%, hsl(320 60% 10%) 100%)",
                    boxShadow: "0 8px 32px 0 rgba(0, 0, 0, 0.4), 0 0 0 1px hsl(263 92% 60% / 0.1) inset",
                  }}
                >
                  <div className="w-10 h-10 rounded-full bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-4">
                    <Sparkles className="w-5 h-5 text-pink-400" />
                  </div>
                  <span className="text-xs uppercase tracking-[0.2em] text-pink-400/80 mb-2 font-semibold">Answer</span>
                  <p className="text-lg sm:text-xl text-foreground text-center leading-relaxed font-medium">
                    {card.back}
                  </p>
                  <div className="absolute bottom-5 flex items-center gap-2 text-xs text-muted-foreground/50">
                    <RotateCcw className="w-3 h-3" />
                    <span>Click to flip back</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between gap-3">
              <Button variant="outline" size="sm" onClick={prev} disabled={current === 0} className="glass-subtle border-white/[0.08] rounded-xl">
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant={known.has(current) ? "default" : "outline"}
                size="sm"
                onClick={toggleKnown}
                className={`rounded-xl flex-1 sm:flex-none sm:px-8 ${
                  known.has(current)
                    ? "bg-green-500/20 text-green-400 border-green-500/30 hover:bg-green-500/30"
                    : "glass-subtle border-white/[0.08]"
                }`}
              >
                {known.has(current) ? "✓ Known" : "Mark as Known"}
              </Button>
              <Button variant="outline" size="sm" onClick={next} disabled={current === cards.length - 1} className="glass-subtle border-white/[0.08] rounded-xl">
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>

            {/* Completion */}
            {current === cards.length - 1 && (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card p-4 text-center">
                <p className="text-sm font-semibold text-foreground mb-1">
                  🎉 You've reviewed all {cards.length} cards!
                </p>
                <p className="text-xs text-muted-foreground">
                  {known.size}/{cards.length} marked as known.{" "}
                  {known.size === cards.length ? "Amazing! You've got this." : "Keep reviewing the ones you missed."}
                </p>
                <Button variant="outline" size="sm" onClick={resetAll} className="mt-3 glass-subtle rounded-xl">
                  <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Review Again
                </Button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
