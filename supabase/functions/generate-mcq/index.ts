import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  try {
    const { chunks, count, topic } = await req.json();
    const GROQ_API_KEY = Deno.env.get("GROQ_API_KEY");
    if (!GROQ_API_KEY) throw new Error("GROQ_API_KEY is not configured");

    const context = (chunks || []).slice(0, 5).join("\n\n---\n\n");
    const topicInstruction = topic ? `Focus the questions on the topic: "${topic}".` : "";

    const prompt = `Based on the following study material, generate exactly ${count} multiple choice questions. ${topicInstruction}

Study Material:
${context}

Return a JSON array of objects with this exact structure:
[
  {
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 0,
    "explanation": "Why the correct answer is right and why others are wrong"
  }
]

The "correct" field is the 0-based index of the correct option.
Make the questions challenging but fair. Ensure all 4 options are plausible.
Return ONLY the JSON array, no other text.`;

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [
          { role: "system", content: "You are a quiz generator. Return only valid JSON." },
          { role: "user", content: prompt },
        ],
        temperature: 0.5,
        max_tokens: 4096,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Groq error:", response.status, errText);
      throw new Error(`Groq API error: ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices[0]?.message?.content || "[]";
    
    // Parse JSON from response (handle markdown code blocks)
    let mcqs;
    try {
      const jsonStr = content.replace(/```json?\n?/g, "").replace(/```/g, "").trim();
      mcqs = JSON.parse(jsonStr);
    } catch {
      mcqs = [];
    }

    return new Response(JSON.stringify({ mcqs }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    console.error("MCQ error:", e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Unknown error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
