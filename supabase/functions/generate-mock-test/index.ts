import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  try {
    const { chunks, totalMarks, topic } = await req.json();
    const GROQ_API_KEY = Deno.env.get("GROQ_API_KEY");
    if (!GROQ_API_KEY) throw new Error("GROQ_API_KEY is not configured");

    const context = (chunks || []).slice(0, 5).join("\n\n---\n\n");
    const topicInstruction = topic ? `Focus on the topic: "${topic}".` : "";

    const prompt = `Based on the following study material, generate an exam paper worth ${totalMarks} marks total. ${topicInstruction}

Study Material:
${context}

Create a well-structured exam with multiple sections. Distribute marks appropriately:
- Short answer questions (2-3 marks each)
- Medium answer questions (5 marks each) 
- Long/essay questions (10 marks each)

Return a JSON object with this exact structure:
{
  "title": "Mock Examination Paper",
  "totalMarks": ${totalMarks},
  "sections": [
    {
      "name": "Section A - Short Answer Questions",
      "marksPerQuestion": 2,
      "questions": ["question1", "question2"]
    },
    {
      "name": "Section B - Medium Answer Questions", 
      "marksPerQuestion": 5,
      "questions": ["question1"]
    },
    {
      "name": "Section C - Long Answer Questions",
      "marksPerQuestion": 10,
      "questions": ["question1"]
    }
  ]
}

Make sure total marks add up to approximately ${totalMarks}.
Make questions challenging and comprehensive.
Return ONLY the JSON object, no other text.`;

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [
          { role: "system", content: "You are an exam paper generator. Return only valid JSON." },
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
    const content = data.choices[0]?.message?.content || "{}";
    
    let test;
    try {
      const jsonStr = content.replace(/```json?\n?/g, "").replace(/```/g, "").trim();
      test = JSON.parse(jsonStr);
    } catch {
      test = { title: "Mock Test", totalMarks, sections: [] };
    }

    return new Response(JSON.stringify({ test }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    console.error("Mock test error:", e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Unknown error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
