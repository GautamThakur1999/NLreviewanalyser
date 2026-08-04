import { GoogleGenAI } from '@google/genai';
import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const { review_text } = await request.json();
    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey) {
      if (review_text.toLowerCase().includes('bad') || review_text.toLowerCase().includes('not')) {
        return NextResponse.json({
          sentiment: 'Negative',
          actionable_summary: '[Mock Data - API Key Missing] This review indicates friction with the core experience. Action: Investigate root cause.',
          identified_themes: ['Trust & authenticity concerns', 'Missing product info']
        });
      }
      return NextResponse.json({
        sentiment: 'Neutral',
        actionable_summary: '[Mock Data - API Key Missing] This review shares general feedback without strong emotion. Action: Monitor for trending patterns.',
        identified_themes: ['Reorder habit loop']
      });
    }

    const ai = new GoogleGenAI({ apiKey: apiKey });

    const prompt = `You are an expert product analyst for a quick-commerce app (like Blinkit).
Analyze the following customer review and provide:
1. The sentiment (must be exactly one of: Positive, Negative, Neutral).
2. A very brief, actionable summary (1-2 sentences) of what the product team should do based on this feedback.
3. A list of 1-3 identified themes or barriers from the review (e.g., "Trust & authenticity", "Missing product info", "App is just for groceries", "Search vs Browse", "Pricing concerns").

Review: "${review_text}"`;

    const response = await ai.models.generateContent({
      model: 'gemini-3.5-flash',
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: "OBJECT",
          properties: {
            sentiment: {
              type: "STRING",
              enum: ["Positive", "Negative", "Neutral"]
            },
            actionable_summary: {
              type: "STRING",
              description: "A 1-2 sentence actionable summary for the product team"
            },
            identified_themes: {
              type: "ARRAY",
              description: "A list of 1-3 core themes or barriers identified in the review",
              items: {
                type: "STRING"
              }
            }
          },
          required: ["sentiment", "actionable_summary", "identified_themes"]
        },
        temperature: 0.1,
      }
    });

    const result = JSON.parse(response.text);

    return NextResponse.json({
      sentiment: result.sentiment || 'Neutral',
      actionable_summary: result.actionable_summary || 'Failed to generate summary.',
      identified_themes: result.identified_themes || []
    });

  } catch (error) {
    console.error("Gemini API Error:", error);
    return NextResponse.json(
      { error: "Error communicating with the AI model." },
      { status: 502 }
    );
  }
}
