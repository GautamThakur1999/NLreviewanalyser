"use client";
import React, { useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://nlreviewanalyser-production.up.railway.app';

export default function ReviewTester() {
  const [review, setReview] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!review.trim()) return;
    
    setLoading(true);
    setError(null);
    setResult(null);

    // Simulate AI workflow steps for the demo
    const steps = [
      "Ingesting customer review data...",
      "Running Gemini sentiment analysis...",
      "Extracting key friction points...",
      "Mapping to core category themes...",
      "Generating actionable product summary..."
    ];
    
    let stepIndex = 0;
    setLoadingStep(steps[0]);
    const stepInterval = setInterval(() => {
      stepIndex = (stepIndex + 1);
      if (stepIndex < steps.length) {
        setLoadingStep(steps[stepIndex]);
      }
    }, 700);

    try {
      // Use internal Next.js API route instead of unreliable Railway backend
      const response = await fetch(`/api/analyze-review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ review_text: review })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze review');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      // Robust Fallback: If API is offline or throwing CORS errors, show mock data
      console.warn("API Error:", err.message);
      setResult({
        sentiment: review.toLowerCase().includes('good') || review.toLowerCase().includes('great') ? 'Positive' : (review.toLowerCase().includes('bad') || review.toLowerCase().includes('not') ? 'Negative' : 'Neutral'),
        actionable_summary: '[Mock Data - Backend Offline] This is an auto-generated fallback response because the Railway API is unreachable. Action: Please check the Railway deployment status.',
        identified_themes: ['System Offline Fallback']
      });
    } finally {
      clearInterval(stepInterval);
      setLoading(false);
    }
  };

  // Helper to get sentiment styling
  const getSentimentStyle = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'bg-[#0C831F]/10 text-[#0C831F] border border-[#0C831F]/20';
      case 'negative':
        return 'bg-error-container/30 text-error border border-error/20';
      default:
        return 'bg-surface-variant/30 text-on-surface border border-outline-variant/50';
    }
  };

  return (
    <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30">
      <h3 className="font-title-sm text-title-sm text-on-surface font-bold mb-4 flex items-center gap-2">
        <span className="material-symbols-outlined text-[20px] text-primary">psychology</span>
        Live AI Review Analysis
      </h3>
      <p className="font-body-sm text-body-sm text-on-surface-variant mb-4">
        Type a custom review below to see how the Gemini AI models categorize it and generate actionable summaries in real-time.
      </p>

      <div className="flex flex-col gap-4">
        <textarea
          value={review}
          onChange={(e) => setReview(e.target.value)}
          placeholder="e.g., 'I ordered a trimmer but it came with a broken seal. Very disappointed in the quality control.'"
          className="w-full h-24 p-3 rounded-md border border-outline-variant/50 bg-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-body-sm text-body-sm text-on-surface resize-none"
        />
        
        <div className="flex justify-end">
          <button
            onClick={handleAnalyze}
            disabled={loading || !review.trim()}
            className="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-md font-label-lg font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
            ) : (
              <span className="material-symbols-outlined text-[18px]">magic_button</span>
            )}
            {loading ? 'Analyzing...' : 'Run AI Analysis'}
          </button>
        </div>

        {loading && (
          <div className="mt-2 p-4 border border-primary/20 bg-primary/5 rounded-lg flex items-center gap-4 animate-in fade-in duration-300">
            <span className="material-symbols-outlined animate-spin text-primary text-[28px]">model_training</span>
            <div className="flex flex-col">
              <span className="font-title-sm text-primary font-bold">AI Engine Active</span>
              <span className="font-body-sm text-on-surface-variant animate-pulse">{loadingStep}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-error/10 text-error rounded-md font-body-sm text-body-sm flex items-start gap-2">
            <span className="material-symbols-outlined text-[18px]">error</span>
            {error}
          </div>
        )}

        {result && (
          <div className="mt-2 p-4 border border-outline-variant/30 bg-surface-container-low rounded-lg animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-center gap-3 mb-4">
              <span className="font-title-sm text-title-sm font-semibold text-on-surface">AI Sentiment:</span>
              <span className={`px-3 py-1 rounded-full font-label-caps text-label-caps ${getSentimentStyle(result.sentiment)}`}>
                {result.sentiment}
              </span>
            </div>
            
            {result.identified_themes && result.identified_themes.length > 0 && (
              <div className="mb-4">
                <span className="font-title-sm text-title-sm font-semibold text-on-surface block mb-2">Identified Themes & Barriers:</span>
                <div className="flex flex-wrap gap-2">
                  {result.identified_themes.map((theme, i) => (
                    <span key={i} className="bg-primary-container/30 text-primary-fixed-variant px-3 py-1 rounded-md font-body-sm text-body-sm border border-primary-container">
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <div className="pt-2 border-t border-outline-variant/30">
              <span className="font-title-sm text-title-sm font-semibold text-on-surface block mb-1">Actionable Summary:</span>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                {result.actionable_summary}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
