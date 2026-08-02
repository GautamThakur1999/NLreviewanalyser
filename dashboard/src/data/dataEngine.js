"use client";
import { useFilter } from '@/context/FilterContext';
import { useState, useEffect } from 'react';

const RAILWAY_API = process.env.NEXT_PUBLIC_API_URL || 'https://nlreviewanalyser-production.up.railway.app';

// ─── Fallback mock data (used while fetching or if API is unreachable) ────────
function getMockData(filters) {
  const baseReviews = 8240;
  const baseSourceBreakdown = { 'Play Store': 4120, 'App Store': 3100, 'Reddit': 680, 'Forum': 340 };
  const baseSentimentBreakdown = { Negative: 58, Neutral: 22, Positive: 20 };
  const baseBarriers = [
    { label: 'Reorder habit loop', value: 31 },
    { label: 'Low category awareness', value: 24 },
    { label: 'Trust & authenticity concerns', value: 18 },
    { label: 'No browsing/discovery', value: 14 },
    { label: 'Missing product info', value: 9 },
    { label: 'Price anxiety vs specialists', value: 4 },
  ];

  let scale = 1.0;
  if (filters.dateRange === 'Last 7 Days') scale *= 0.23;
  if (filters.dateRange === 'Last 90 Days') scale *= 2.8;
  if (filters.dateRange === 'All Time') scale *= 8.5;
  if (filters.category === 'Personal Care') scale *= 0.35;
  if (filters.category === 'Electronics') scale *= 0.18;
  if (filters.category === 'Grocery') scale *= 0.42;
  if (filters.category === 'Baby Care') scale *= 0.05;

  let sourceScale = 1.0;
  let activeSources = 4;
  let currentSourceBreakdown = { ...baseSourceBreakdown };
  if (filters.source && filters.source !== 'All') {
    sourceScale = (baseSourceBreakdown[filters.source] || 0) / baseReviews;
    activeSources = 1;
    Object.keys(currentSourceBreakdown).forEach(k => {
      if (k !== filters.source) currentSourceBreakdown[k] = 0;
    });
  }

  const totalScale = scale * sourceScale;
  Object.keys(currentSourceBreakdown).forEach(k => {
    currentSourceBreakdown[k] = Math.round(currentSourceBreakdown[k] * scale);
  });

  const sentimentBreakdown = { ...baseSentimentBreakdown };
  const topSentiment = Object.entries(sentimentBreakdown).sort((a, b) => b[1] - a[1])[0];

  return {
    overview: {
      reviewsAnalyzed: Math.round(baseReviews * totalScale).toLocaleString(),
      sources: activeSources,
      themesIdentified: Math.max(3, Math.round(11 * Math.min(1, totalScale * 1.5))),
      overallSentiment: { value: topSentiment[1], label: topSentiment[0] },
    },
    barriers: baseBarriers,
    sourceBreakdown: currentSourceBreakdown,
    sentimentBreakdown,
  };
}

// ─── Build query string from active filters ───────────────────────────────────
function buildParams(filters) {
  const params = new URLSearchParams();
  if (filters.source && filters.source !== 'All') params.set('source', filters.source);
  if (filters.dateRange) params.set('dateRange', filters.dateRange);
  if (filters.category && filters.category !== 'All') params.set('category', filters.category);
  return params.toString();
}

// ─── Main hook ────────────────────────────────────────────────────────────────
export function useDashboardData() {
  const { filters } = useFilter();
  const [data, setData] = useState(() => getMockData(filters));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    
    // OPTIMISTIC UPDATE: instantly show local calculations so there is 0 latency
    setData(getMockData(filters));
    setLoading(true);

    const qs = buildParams(filters);

    Promise.all([
      fetch(`${RAILWAY_API}/api/overview?${qs}`).then(r => r.json()),
      fetch(`${RAILWAY_API}/api/barriers?${qs}`).then(r => r.json()),
    ])
      .then(([overview, barriers]) => {
        if (cancelled) return;
        setData({
          overview: {
            reviewsAnalyzed: overview.reviews_analyzed.toLocaleString(),
            sources: overview.sources,
            themesIdentified: overview.themes_identified,
            overallSentiment: {
              value: overview.overall_sentiment.value,
              label: overview.overall_sentiment.label,
            },
          },
          barriers: barriers.barriers,
          sourceBreakdown: overview.source_breakdown,
          sentimentBreakdown: overview.sentiment_breakdown,
        });
      })
      .catch(() => {
        // API unreachable — silently keep mock data
        if (!cancelled) setData(getMockData(filters));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [filters.source, filters.dateRange, filters.category]);

  return { ...data, loading };
}
