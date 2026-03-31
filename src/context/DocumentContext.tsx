import React, { createContext, useContext, useState } from "react";

interface DocumentState {
  fileName: string;
  docId: string;
}

interface DocumentContextType {
  document: DocumentState | null;
  setDocument: (doc: DocumentState | null) => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;
}

const DocumentContext = createContext<DocumentContextType | null>(null);

export function DocumentProvider({ children }: { children: React.ReactNode }) {
  const [document, setDocument] = useState<DocumentState | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  return (
    <DocumentContext.Provider value={{ document, setDocument, isProcessing, setIsProcessing }}>
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocument() {
  const ctx = useContext(DocumentContext);
  if (!ctx) throw new Error("useDocument must be used within DocumentProvider");
  return ctx;
}
