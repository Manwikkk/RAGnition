import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  try {
    const { messages, chunks, fileName } = await req.json();
    const GROQ_API_KEY = Deno.env.get("GROQ_API_KEY");
    if (!GROQ_API_KEY) throw new Error("GROQ_API_KEY is not configured");

    // Simple retrieval: pick top chunks based on keyword overlap with last user message
    const lastMsg = messages[messages.length - 1]?.content || "";
    const keywords = lastMsg.toLowerCase().split(/\s+/).filter((w: string) => w.length > 3);
    
    const scoredChunks = (chunks || []).map((chunk: string, i: number) => {
      const lower = chunk.toLowerCase();
      const score = keywords.reduce((acc: number, kw: string) => acc + (lower.includes(kw) ? 1 : 0), 0);
      return { chunk, score, index: i };
    });
    
    scoredChunks.sort((a: any, b: any) => b.score - a.score);
    const topChunks = scoredChunks.slice(0, 3).map((c: any) => c.chunk);
    const context = topChunks.join("\n\n---\n\n");

    const systemPrompt = `You are an intelligent study assistant analyzing the document "${fileName}". 
Use the following document excerpts to answer questions accurately. If the answer isn't in the excerpts, say so.

Document excerpts:
${context}`;

    const groqMessages = [
      { role: "system", content: systemPrompt },
      ...messages.map((m: any) => ({ role: m.role, content: m.content })),
    ];

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: groqMessages,
        temperature: 0.3,
        max_tokens: 2048,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Groq error:", response.status, errText);
      throw new Error(`Groq API error: ${response.status}`);
    }

    const data = await response.json();
    const reply = data.choices[0]?.message?.content || "No response generated.";

    return new Response(JSON.stringify({ reply }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    console.error("Chat error:", e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Unknown error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
