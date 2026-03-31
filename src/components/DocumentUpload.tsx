import React, { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, Loader2, MessageSquare, Brain, Zap, BookOpen, Sparkles, Github, Linkedin, ExternalLink } from "lucide-react";
import { useDocument } from "@/context/DocumentContext";
import { useNavigate } from "react-router-dom";
import { postMultipart } from "@/lib/ragApi";
import CursorTiltGlassCard from "@/components/CursorTiltGlassCard";

const features = [
  {
    icon: MessageSquare,
    title: "Document Chat",
    desc: "Have intelligent conversations about your uploaded materials",
    gradient: "from-purple-500/20 to-indigo-500/20",
    border: "hover:border-purple-500/30",
    glow: "hover:shadow-purple-500/10",
  },
  {
    icon: Brain,
    title: "MCQ Generator",
    desc: "Generate custom quizzes with instant scoring & explanations",
    gradient: "from-indigo-500/20 to-cyan-500/20",
    border: "hover:border-indigo-500/30",
    glow: "hover:shadow-indigo-500/10",
  },
  {
    icon: Zap,
    title: "Mock Tests",
    desc: "Create full exam papers with varied question types",
    gradient: "from-purple-500/20 to-pink-500/20",
    border: "hover:border-pink-500/30",
    glow: "hover:shadow-pink-500/10",
  },
  {
    icon: BookOpen,
    title: "Smart Summary",
    desc: "Get AI-generated summaries and key takeaways instantly",
    gradient: "from-cyan-500/20 to-green-500/20",
    border: "hover:border-cyan-500/30",
    glow: "hover:shadow-cyan-500/10",
  },
  {
    icon: Sparkles,
    title: "Flashcards",
    desc: "Auto-generate revision flashcards from your documents",
    gradient: "from-pink-500/20 to-orange-500/20",
    border: "hover:border-orange-500/30",
    glow: "hover:shadow-orange-500/10",
  },
];

export default function DocumentUpload() {
  const { setDocument, isProcessing, setIsProcessing } = useDocument();
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isPdfFile = (file: File) => {
    const mimeOk = (file.type || "").toLowerCase() === "application/pdf";
    const extOk = (file.name || "").toLowerCase().endsWith(".pdf");
    return mimeOk || extOk;
  };

  const processFile = useCallback(
    async (file: File) => {
      setError(null);
      setIsProcessing(true);
      try {
        const form = new FormData();
        form.append("file", file);
        const data = await postMultipart<{ docId: string }>("/api/upload", form);
        setDocument({ fileName: file.name, docId: data.docId });
        navigate("/dashboard");
      } catch (err: any) {
        const msg = err?.message || "Failed to process document";
        if (msg.includes("fetch") || msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
          setError("Cannot connect to backend. Make sure the Python server is running: cd backend && uvicorn main:app --reload");
        } else {
          setError(msg);
        }
      } finally {
        setIsProcessing(false);
      }
    },
    [setDocument, setIsProcessing, navigate]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file && isPdfFile(file)) {
        processFile(file);
      } else {
        setError("Please upload a PDF file");
      }
    },
    [processFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      if (!isPdfFile(file)) {
        setError("Please select a valid .pdf file");
        return;
      }
      processFile(file);
      e.target.value = "";
    },
    [processFile]
  );

  const handleCardClick = () => {
    if (!isProcessing) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Animated background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <motion.div
          animate={{ x: [0, 30, -20, 0], y: [0, -20, 15, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="glow-orb w-[500px] h-[500px] bg-primary/20"
          style={{ position: "absolute", top: "-12rem", left: "-12rem" }}
        />
        <motion.div
          animate={{ x: [0, -30, 20, 0], y: [0, 25, -15, 0] }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          className="glow-orb w-[400px] h-[400px] bg-blue-500/10"
          style={{ position: "absolute", bottom: "-10rem", right: "-10rem" }}
        />
        <motion.div
          animate={{ x: [0, 15, -25, 0], y: [0, -30, 10, 0] }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
          className="glow-orb w-[300px] h-[300px] bg-purple-500/10"
          style={{ position: "absolute", top: "40%", right: "20%" }}
        />
      </div>

      {/* Mesh gradient overlay */}
      <div className="fixed inset-0 mesh-gradient pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-16">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-10 max-w-2xl w-full"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-subtle mb-8"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
            </span>
            <span className="text-xs font-medium text-muted-foreground">AI-Powered Study Companion</span>
          </motion.div>

          <h1 className="text-5xl sm:text-6xl md:text-7xl font-heading font-bold mb-6 tracking-tight">
            <span className="gradient-text text-glow">RAGnition</span>
          </h1>
          <p className="text-muted-foreground text-lg sm:text-xl md:text-2xl leading-relaxed max-w-xl mx-auto px-4">
            Upload your study materials, chat with your documents, generate MCQs and mock tests —{" "}
            <span className="text-foreground font-medium">all powered by AI</span>.
          </p>
        </motion.div>

        {/* Upload Area */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-lg px-4"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileSelect}
            className="hidden"
            disabled={isProcessing}
          />

          <CursorTiltGlassCard
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={handleCardClick}
            className={`glass-card shimmer noise-overlay p-10 sm:p-14 text-center cursor-pointer transition-all duration-500 group overflow-hidden ${
              dragOver ? "border-primary/40 scale-[1.02]" : "hover:border-white/[0.12]"
            }`}
            style={dragOver ? { boxShadow: "0 0 60px -10px hsl(263 92% 60% / 0.2)" } : {}}
          >
            <AnimatePresence mode="wait">
              {isProcessing ? (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex flex-col items-center gap-5"
                >
                  <div className="relative">
                    <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center animate-glow-ring">
                      <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    </div>
                  </div>
                  <div>
                    <p className="font-heading font-semibold text-foreground mb-1">Processing document...</p>
                    <p className="text-xs text-muted-foreground">Extracting text & building AI index</p>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="upload"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="flex flex-col items-center gap-5"
                >
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-primary/10 group-hover:border-primary/20 transition-all duration-500"
                  >
                    <Upload className="w-7 h-7 text-primary" />
                  </motion.div>
                  <div>
                    <p className="font-heading font-semibold text-foreground mb-1.5">Drop your PDF here</p>
                    <p className="text-sm text-muted-foreground">or click to browse files</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground/60 glass-subtle px-3 py-1.5 rounded-full">
                    <FileText className="w-3 h-3" />
                    <span>PDF files supported</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </CursorTiltGlassCard>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-4 glass-card border-destructive/30 p-4 rounded-xl"
              >
                <p className="text-destructive text-sm text-center">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mt-16 max-w-4xl w-full px-4"
        >
          {features.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              whileHover={{ y: -7, scale: 1.06 }}
              className={`feature-card p-4 sm:p-6 text-center group cursor-default border border-white/[0.06] transition-shadow duration-300 hover:shadow-2xl ${feature.border} ${feature.glow}`}
            >
              <div
                className={`w-11 h-11 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mx-auto mb-3 group-hover:scale-110 group-hover:brightness-125 transition-all duration-300`}
              >
                <feature.icon className="w-5 h-5 text-foreground" />
              </div>
              <h3 className="font-heading font-semibold text-xs sm:text-sm mb-1.5 group-hover:text-foreground transition-colors duration-300">{feature.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed hidden sm:block group-hover:text-muted-foreground/80 transition-colors duration-300">{feature.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Bottom tagline */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-12 text-base sm:text-lg text-muted-foreground/75 text-center max-w-2xl px-4 leading-relaxed"
        >
          RAGnition helps you study smarter with retrieval-augmented answers, MCQ practice, and mock exam generation — all grounded in your own documents.
        </motion.p>

        {/* Socials */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1 }}
          className="mt-10 flex flex-col items-center gap-5"
        >
          <p className="text-sm text-muted-foreground/60 uppercase tracking-widest font-medium">Check out more projects</p>
          <div className="flex items-center gap-3">
            <motion.a
              whileHover={{ y: -7, scale: 1.06 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              href="https://www.linkedin.com/in/manvik-siddhpura-7822852b3/"
              target="_blank"
              rel="noopener noreferrer"
              className="feature-card group flex items-center gap-2.5 border border-white/[0.08] hover:border-blue-500/40 px-5 py-3 rounded-xl transition-shadow duration-300 hover:shadow-xl hover:shadow-blue-500/20"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center group-hover:bg-blue-600/30 transition-colors duration-300">
                <Linkedin className="w-4 h-4 text-blue-400" />
              </div>
              <span className="text-base font-medium text-muted-foreground group-hover:text-foreground transition-colors duration-300">LinkedIn</span>
              <ExternalLink className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-muted-foreground/70 transition-colors duration-300" />
            </motion.a>
            <motion.a
              whileHover={{ y: -7, scale: 1.06 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              href="https://github.com/Manwikkk"
              target="_blank"
              rel="noopener noreferrer"
              className="feature-card group flex items-center gap-2.5 border border-white/[0.08] hover:border-purple-500/40 px-5 py-3 rounded-xl transition-shadow duration-300 hover:shadow-xl hover:shadow-purple-500/20"
            >
              <div className="w-8 h-8 rounded-lg bg-purple-600/20 flex items-center justify-center group-hover:bg-purple-600/30 transition-colors duration-300">
                <Github className="w-4 h-4 text-purple-400" />
              </div>
              <span className="text-base font-medium text-muted-foreground group-hover:text-foreground transition-colors duration-300">GitHub</span>
              <ExternalLink className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-muted-foreground/70 transition-colors duration-300" />
            </motion.a>
          </div>
          <p className="text-sm text-muted-foreground/50 text-center px-4">
            Explore more AI projects and experiments by <span className="text-muted-foreground/70 font-semibold">Manvik Siddhpura</span>
          </p>
        </motion.div>

        {/* Copyright Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-8 pb-6 text-center px-4"
        >
          <div className="h-px w-40 mx-auto bg-gradient-to-r from-transparent via-white/10 to-transparent mb-5" />
          <p className="text-sm text-muted-foreground/50">
            © {new Date().getFullYear()} RAGnition. All rights reserved.
          </p>
          <p className="text-xs text-muted-foreground/35 mt-1.5">
            Upload any PDF (notes, chapters, study guides). For best results use text-based PDFs.
          </p>
        </motion.footer>
      </div>
    </div>
  );
}
