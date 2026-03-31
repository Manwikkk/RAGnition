import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { DocumentProvider } from "@/context/DocumentContext";
import Index from "./pages/Index.tsx";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound.tsx";
import GlassCursor from "@/components/GlassCursor";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <DocumentProvider>
        <Toaster />
        <Sonner />
        <GlassCursor />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </DocumentProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
