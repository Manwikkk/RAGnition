import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Bot, User, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocument } from "@/context/DocumentContext";
import ReactMarkdown from "react-markdown";
import { API_BASE_URL, postJSON } from "@/lib/ragApi";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatInterface() {
  const { document } = useDocument();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const downloadChatHistoryPDF = async () => {
    if (!document || messages.length === 0) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          docId: document.docId,
          fileName: document.fileName,
          messages,
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
      a.download = `chat-history-${document.fileName.replace(/\s+/g, "-").toLowerCase()}.pdf`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: any) {
      console.error(e);
      window.alert(e?.message || "Failed to download chat PDF.");
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !document) return;
    const userMsg: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const data = await postJSON<{ reply: string }>("/api/chat", {
        docId: document.docId,
        messages: [...messages, userMsg],
      });
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.length > 0 && (
          <div className="flex items-center justify-end">
            <Button
              onClick={downloadChatHistoryPDF}
              variant="outline"
              size="sm"
              className="glass-subtle border-white/[0.08] hover:border-white/[0.15] rounded-xl"
            >
              Download Chat (PDF)
            </Button>
          </div>
        )}
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="relative"
            >
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-6 mx-auto border border-primary/10 animate-glow-ring">
                <Bot className="w-9 h-9 text-primary/60" />
              </div>
            </motion.div>
            <h3 className="font-heading font-semibold text-foreground mb-2 text-lg">Start a conversation</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Ask anything about <span className="text-primary font-medium">{document?.fileName}</span>
            </p>
            <div className="flex flex-wrap gap-2 mt-6 justify-center max-w-md">
              {["Summarize this document", "Key takeaways", "Explain the main concepts"].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="glass-subtle px-3 py-1.5 rounded-full text-xs text-muted-foreground hover:text-foreground hover:border-white/[0.12] transition-all duration-300"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center flex-shrink-0 mt-1 border border-primary/10">
                  <Sparkles className="w-4 h-4 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-lg shadow-primary/20"
                    : "glass-card"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="prose-chat">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-xl bg-secondary/80 flex items-center justify-center flex-shrink-0 mt-1 border border-white/[0.06]">
                  <User className="w-4 h-4 text-secondary-foreground" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-primary/10">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <div className="glass-card rounded-2xl px-4 py-3 flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/[0.06]">
        <div className="flex gap-2 items-end glass-subtle rounded-2xl p-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your document..."
            rows={1}
            className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="rounded-xl h-10 w-10 bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
