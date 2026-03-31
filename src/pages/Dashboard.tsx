import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Brain, FileText, Upload, Menu, X, BookOpen, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocument } from "@/context/DocumentContext";
import { useNavigate } from "react-router-dom";
import ChatInterface from "@/components/ChatInterface";
import MCQGenerator from "@/components/MCQGenerator";
import MockTestGenerator from "@/components/MockTestGenerator";
import SummaryPanel from "@/components/SummaryPanel";
import FlashcardPanel from "@/components/FlashcardPanel";

type Tab = "chat" | "mcq" | "mock" | "summary" | "flashcards";

const tabs = [
  { id: "chat" as Tab, label: "Chat", icon: MessageSquare },
  { id: "mcq" as Tab, label: "MCQ Test", icon: Brain },
  { id: "mock" as Tab, label: "Mock Test", icon: FileText },
  { id: "summary" as Tab, label: "Summary", icon: BookOpen },
  { id: "flashcards" as Tab, label: "Flashcards", icon: Layers },
];

export default function Dashboard() {
  const { document, setDocument } = useDocument();
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  if (!document) {
    navigate("/");
    return null;
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-background relative overflow-hidden">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div
          className="glow-orb w-[400px] h-[400px] bg-primary/10"
          style={{ position: "absolute", top: "-10rem", right: "-10rem" }}
        />
        <div
          className="glow-orb w-[300px] h-[300px] bg-blue-500/5"
          style={{ position: "absolute", bottom: "-8rem", left: "-8rem" }}
        />
        <div className="mesh-gradient absolute inset-0" />
      </div>

      {/* Header */}
      <header className="relative z-20 glass-subtle border-b border-white/[0.06] px-4 sm:px-5 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex items-center gap-2 flex-shrink-0 group cursor-default">
            <div className="relative w-8 h-8 sm:w-9 sm:h-9 overflow-visible">
              <img 
                src="/favicon.png" 
                alt="RAGnition Logo" 
                className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-110" 
              />
            </div>
            <h1 className="font-heading font-bold text-base sm:text-lg gradient-text text-glow transition-transform duration-300 group-hover:translate-x-0.5">RAGnition</h1>
          </div>
          <div className="hidden sm:block h-4 w-px bg-border" />
          <div className="hidden sm:flex items-center gap-2 glass-subtle px-3 py-1 rounded-full min-w-0">
            <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
            <span className="text-xs text-muted-foreground truncate max-w-[160px] md:max-w-[240px]">
              {document.fileName}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setDocument(null);
              navigate("/");
            }}
            className="text-muted-foreground hover:text-foreground text-xs sm:text-sm"
          >
            <Upload className="w-3.5 h-3.5 sm:mr-1.5" />
            <span className="hidden sm:inline">New Document</span>
          </Button>
          {/* Mobile menu toggle */}
          <button
            className="sm:hidden glass-subtle p-2 rounded-lg text-muted-foreground"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Mobile filename bar */}
      <div className="sm:hidden relative z-10 px-4 py-2 glass-subtle border-b border-white/[0.04] flex items-center gap-2">
        <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
        <span className="text-xs text-muted-foreground truncate">{document.fileName}</span>
      </div>

      {/* Mobile dropdown menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="sm:hidden absolute top-[106px] inset-x-0 z-30 glass-subtle border-b border-white/[0.06] shadow-xl"
          >
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setMenuOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-5 py-3.5 text-sm transition-colors ${
                  activeTab === tab.id
                    ? "text-primary bg-primary/5"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop Tabs */}
      <div className="hidden sm:flex relative z-10 border-b border-white/[0.06] px-5 gap-1 flex-shrink-0 glass-subtle overflow-x-auto scrollbar-hide">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative px-4 md:px-5 py-3 text-sm flex items-center gap-2 transition-all duration-300 whitespace-nowrap flex-shrink-0 ${
              activeTab === tab.id
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
            {activeTab === tab.id && (
              <motion.div
                layoutId="tab-indicator"
                className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full"
                style={{
                  background: "linear-gradient(90deg, hsl(263 92% 60%), hsl(322 92% 60%))",
                  boxShadow: "0 0 10px hsl(263 92% 60% / 0.5)",
                }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Mobile bottom tab bar */}
      <div className="sm:hidden fixed bottom-0 inset-x-0 z-20 glass-subtle border-t border-white/[0.06] flex justify-around py-2 safe-bottom">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition-all ${
              activeTab === tab.id ? "text-primary" : "text-muted-foreground"
            }`}
          >
            <tab.icon className="w-5 h-5" />
            <span className="text-[10px] font-medium">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="relative z-10 flex-1 overflow-hidden pb-[56px] sm:pb-0">
        <div className={activeTab === "chat" ? "block h-full" : "hidden h-full"}>
          <ChatInterface />
        </div>
        <div className={activeTab === "mcq" ? "block h-full overflow-y-auto" : "hidden h-full"}>
          <MCQGenerator />
        </div>
        <div className={activeTab === "mock" ? "block h-full overflow-y-auto" : "hidden h-full"}>
          <MockTestGenerator />
        </div>
        <div className={activeTab === "summary" ? "block h-full overflow-y-auto" : "hidden h-full"}>
          <SummaryPanel />
        </div>
        <div className={activeTab === "flashcards" ? "block h-full overflow-y-auto" : "hidden h-full"}>
          <FlashcardPanel />
        </div>
      </div>
    </div>
  );
}
