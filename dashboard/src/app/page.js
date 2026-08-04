"use client";
import { useDashboardData } from '@/data/dataEngine';

export default function Page() {
  const data = useDashboardData();

  // Helper to determine background/colors for sentiment
  let sentimentColor = "text-error";
  let sentimentBg = "bg-error-container text-on-error-container";
  let sentimentBorder = "border-l-error";
  let sentimentIcon = "sentiment_dissatisfied";
  let sentimentPieColors = "conic-gradient(#ba1a1a 0% 58%, #eae7e7 58% 80%, #0C831F 80% 100%)";

  if (data.overview.overallSentiment.label === 'Positive') {
    sentimentColor = "text-[#0C831F]";
    sentimentBg = "bg-[#0C831F]/20 text-[#0C831F]";
    sentimentBorder = "border-l-[#0C831F]";
    sentimentIcon = "sentiment_satisfied";
    sentimentPieColors = `conic-gradient(#0C831F 0% ${data.overview.overallSentiment.value}%, #eae7e7 ${data.overview.overallSentiment.value}% 80%, #ba1a1a 80% 100%)`;
  } else if (data.overview.overallSentiment.label === 'Neutral') {
    sentimentColor = "text-surface-variant";
    sentimentBg = "bg-surface-variant/20 text-on-surface-variant";
    sentimentBorder = "border-l-surface-variant";
    sentimentIcon = "sentiment_neutral";
    sentimentPieColors = `conic-gradient(#eae7e7 0% ${data.overview.overallSentiment.value}%, #ba1a1a ${data.overview.overallSentiment.value}% 80%, #0C831F 80% 100%)`;
  } else {
    sentimentPieColors = `conic-gradient(#ba1a1a 0% ${data.overview.overallSentiment.value}%, #eae7e7 ${data.overview.overallSentiment.value}% ${data.overview.overallSentiment.value + data.sentimentBreakdown.Neutral}%, #0C831F ${data.overview.overallSentiment.value + data.sentimentBreakdown.Neutral}% 100%)`;
  }

  // Helper to calculate height of source bars based on max value
  const sourceKeys = Object.keys(data.sourceBreakdown);
  const maxSourceVal = Math.max(...sourceKeys.map(k => data.sourceBreakdown[k]));
  
  return (
    <>
      {/*  Page Header  */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-6 gap-4 sm:gap-0">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">Overview</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">High-level insights across all sources for the selected period.</p>
        </div>
        <button className="flex items-center gap-2 bg-primary-container text-[#1F1F1F] font-body-sm text-body-sm font-semibold px-4 py-2 rounded-md hover:bg-primary-fixed transition-colors card-shadow">
          <span className="material-symbols-outlined text-[18px]">download</span>
          Export Report
        </button>
      </div>

      {/*  1. KPI Stat Cards (Row of 4)  */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/*  Card 1  */}
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Reviews Analyzed</h3>
            <div className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">chat</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="font-display-lg text-display-lg text-on-surface font-bold tracking-tight">{data.overview.reviewsAnalyzed}</div>
          </div>
        </div>

        {/*  Card 2  */}
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Sources</h3>
            <div className="w-8 h-8 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">source</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="font-display-lg text-display-lg text-on-surface font-bold tracking-tight">{data.overview.sources}</div>
          </div>
        </div>

        {/*  Card 3  */}
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Themes Identified</h3>
            <div className="w-8 h-8 rounded-full bg-orange-50 text-orange-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">category</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="font-display-lg text-display-lg text-on-surface font-bold tracking-tight">{data.overview.themesIdentified}</div>
          </div>
        </div>

        {/*  Card 4  */}
        <div className={`bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between border-l-4 ${sentimentBorder} hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer`}>
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Overall Sentiment</h3>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${sentimentBg}`}>
              <span className="material-symbols-outlined text-[18px]">{sentimentIcon}</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className={`font-display-lg text-display-lg font-bold tracking-tight ${sentimentColor}`}>{data.overview.overallSentiment.value}%</div>
            <span className={`font-body-sm text-body-sm font-medium ${sentimentColor}`}>{data.overview.overallSentiment.label}</span>
          </div>
        </div>
      </div>

      {/*  2. Visualization Row  */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/*  Left Card: Top Barriers (2/3)  */}
        <div className="lg:col-span-2 bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-title-sm text-title-sm text-on-surface font-bold">Top Barriers to Category Exploration</h3>
            <button className="text-on-surface-variant hover:text-primary transition-colors">
              <span className="material-symbols-outlined text-[20px]">more_horiz</span>
            </button>
          </div>
          <div className="space-y-4">
            {data.barriers.map((barrier, i) => (
              <div key={i} className="group/bar cursor-pointer flex flex-col gap-1">
                <div className="flex justify-between font-body-sm text-body-sm mb-1">
                  <span className="font-medium">{barrier.label}</span>
                  <span className="font-bold">{barrier.value}%</span>
                </div>
                <div className="w-full bg-surface-container-high rounded-full h-2">
                  <div className="bg-primary-container h-2 rounded-full group-hover/bar:brightness-90 transition-all" style={{ width: `${barrier.value}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/*  Right Card: Sentiment Breakdown (1/3)  */}
        <div className="lg:col-span-1 bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-title-sm text-title-sm text-on-surface font-bold">Sentiment Breakdown</h3>
            <span className="material-symbols-outlined text-on-surface-variant text-[20px]">pie_chart</span>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center relative mb-6">
            <div className="w-32 h-32 rounded-full relative" style={{ background: sentimentPieColors }}>
              <div className="absolute inset-0 m-auto w-24 h-24 bg-surface-container-lowest rounded-full flex items-center justify-center flex-col">
                <span className={`font-display-lg text-display-lg font-bold leading-none ${sentimentColor}`}>{data.overview.overallSentiment.value}%</span>
                <span className={`font-label-caps text-label-caps ${sentimentColor}`}>{data.overview.overallSentiment.label}</span>
              </div>
            </div>
          </div>
          <div className="flex justify-center gap-6 pt-4 border-t border-outline-variant/30">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-error"></div>
              <span className="font-body-sm text-body-sm font-medium">Negative {data.sentimentBreakdown.Negative}%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-surface-container-highest"></div>
              <span className="font-body-sm text-body-sm font-medium">Neutral {data.sentimentBreakdown.Neutral}%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-[#0C831F]"></div>
              <span className="font-body-sm text-body-sm font-medium">Positive {data.sentimentBreakdown.Positive}%</span>
            </div>
          </div>
        </div>
      </div>

      {/*  3. Source Breakdown & 4. Key Themes (Grid Row)  */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/*  Source Breakdown Card (Span 4)  */}
        <div className="lg:col-span-4 bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col">
          <h3 className="font-title-sm text-title-sm text-on-surface font-bold mb-8">Source Breakdown</h3>
          <div className="flex-1 flex items-end justify-between px-2 gap-4 h-48 mt-auto mb-4 border-b border-outline-variant/30 pb-4">
            
            {sourceKeys.map((source, i) => {
              const val = data.sourceBreakdown[source];
              const heightPercent = maxSourceVal === 0 ? 0 : Math.max(2, (val / maxSourceVal) * 100);
              
              return (
                <div key={source} className="flex flex-col items-center w-full h-full justify-end group">
                  <div className="font-label-caps text-label-caps text-on-surface-variant mb-2 opacity-0 group-hover:opacity-100 transition-opacity">{val.toLocaleString()}</div>
                  <div className={`w-full max-w-[32px] bg-primary-container rounded-t-sm opacity-${100 - (i*20)}`} style={{ height: `${heightPercent}%` }}></div>
                  <div className="font-body-sm text-body-sm mt-3 text-center text-on-surface-variant truncate w-full">{source.replace(' Store', '')}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/*  Key Themes List Card (Span 8)  */}
        <div className="lg:col-span-8 bg-surface-container-lowest rounded-lg p-card-padding card-shadow border border-outline-variant/30 rounded-xl p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-title-sm text-title-sm text-on-surface font-bold">Key Themes &amp; Customer Verbatims</h3>
            <div className="flex gap-2">

            </div>
          </div>
          <div className="space-y-4">
            {/*  Row 1  */}
            <div className="border border-outline-variant/50 rounded-md p-4 hover:bg-surface-container-low transition-colors">
              <div className="flex justify-between gap-4 mb-2 items-center">
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Users treat the app purely as a weekly restock tool</h4>
                <div className="flex gap-2 shrink-0">
                  <span className="bg-error/10 text-error px-2 py-0.5 rounded-full font-label-caps text-label-caps">Negative</span>
                  <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">High Prev.</span>
                  <span className="bg-primary-container/20 text-primary px-2 py-0.5 rounded-full font-label-caps text-label-caps border border-primary-container/30">High Priority</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">android</span> Play Store</span>
                <span className="text-outline-variant text-[10px]">•</span>
                <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">forum</span> Reddit</span>
              </div>
              <div className="bg-background p-3 rounded border border-outline-variant/30 border-l-2 border-l-primary-container relative border-l-4 border-l-error">
                <p className="font-body-sm text-body-sm text-on-surface-variant italic relative z-10">"I only order milk, bread and eggs — didn't even know they sell dog food"</p>
              </div>
            </div>

            {/*  Row 2  */}
            <div className="border border-outline-variant/50 rounded-md p-4 hover:bg-surface-container-low transition-colors">
              <div className="flex justify-between gap-4 mb-2 items-center">
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Unaware the app sells pet, baby &amp; personal care</h4>
                <div className="flex gap-2 shrink-0">
                  <span className="bg-surface-variant text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Neutral</span>
                  <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Med Prev.</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">phone_iphone</span> App Store</span>
              </div>
              <div className="bg-background p-3 rounded border border-outline-variant/30 border-l-2 border-l-primary-container relative border-l-4 border-l-surface-variant">
                <p className="font-body-sm text-body-sm text-on-surface-variant italic relative z-10">"The search is weird when looking for shampoos, it only shows grocery brands"</p>
              </div>
            </div>
            {/*  Row 3  */}
            <div className="border border-outline-variant/50 rounded-md p-4 hover:bg-surface-container-low transition-colors">
              <div className="flex justify-between gap-4 mb-2 items-center">
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Surprised and delighted by the electronics selection</h4>
                <div className="flex gap-2 shrink-0">
                  <span className="bg-[#0C831F]/10 text-[#0C831F] px-2 py-0.5 rounded-full font-label-caps text-label-caps">Positive</span>
                  <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Low Prev.</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">android</span> Play Store</span>
              </div>
              <div className="bg-background p-3 rounded border border-outline-variant/30 border-l-2 border-l-primary-container relative border-l-4 border-l-[#0C831F]">
                <p className="font-body-sm text-body-sm text-on-surface-variant italic relative z-10">"Got my iPhone charger in 10 minutes when my old one broke right before a meeting. Didn't even know they delivered electronics so fast! Lifesaver."</p>
              </div>
            </div>

            {/*  Row 4  */}
            <div className="border border-outline-variant/50 rounded-md p-4 hover:bg-surface-container-low transition-colors">
              <div className="flex justify-between gap-4 mb-2 items-center">
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Perception that non-grocery items are overpriced</h4>
                <div className="flex gap-2 shrink-0">
                  <span className="bg-error/10 text-error px-2 py-0.5 rounded-full font-label-caps text-label-caps">Negative</span>
                  <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Med Prev.</span>
                  <span className="bg-primary-container/20 text-primary px-2 py-0.5 rounded-full font-label-caps text-label-caps border border-primary-container/30">Med Priority</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">forum</span> Reddit</span>
              </div>
              <div className="bg-background p-3 rounded border border-outline-variant/30 border-l-2 border-l-primary-container relative border-l-4 border-l-error">
                <p className="font-body-sm text-body-sm text-on-surface-variant italic relative z-10">"Why would I buy a trimmer from here when Amazon or Nykaa gives me a 30% discount? You only use this app when you are desperate."</p>
              </div>
            </div>

            {/*  Row 5  */}
            <div className="border border-outline-variant/50 rounded-md p-4 hover:bg-surface-container-low transition-colors">
              <div className="flex justify-between gap-4 mb-2 items-center">
                <h4 className="font-body-md text-body-md font-semibold text-on-surface">Missing detailed product information for beauty products</h4>
                <div className="flex gap-2 shrink-0">
                  <span className="bg-surface-variant text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Neutral</span>
                  <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">High Prev.</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <span className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">phone_iphone</span> App Store</span>
              </div>
              <div className="bg-background p-3 rounded border border-outline-variant/30 border-l-2 border-l-primary-container relative border-l-4 border-l-surface-variant">
                <p className="font-body-sm text-body-sm text-on-surface-variant italic relative z-10">"I tried to buy face wash but there are no ingredient lists or skin type recommendations. It's fine for basic stuff but risky for skincare."</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Appendix: Data Explanation */}
      <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 mb-6">
        <h3 className="font-title-sm text-title-sm text-on-surface font-bold mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px] text-primary">info</span>
          Appendix: Sentiment Classification Criteria
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-error-container/30 border border-error/20">
            <h4 className="font-body-sm text-body-sm font-bold text-error mb-2">Negative Review</h4>
            <p className="font-body-sm text-body-sm text-on-surface-variant">The customer explicitly expresses frustration, disappointment, or states a critical barrier preventing them from exploring new categories. (e.g., missing products, high prices, poor search experience).</p>
          </div>
          <div className="p-4 rounded-lg bg-surface-variant/30 border border-outline-variant/50">
            <h4 className="font-body-sm text-body-sm font-bold text-on-surface mb-2">Neutral Review</h4>
            <p className="font-body-sm text-body-sm text-on-surface-variant">The customer shares an observation, a feature request, or states their current usage behavior without strong negative emotion or high praise. (e.g., "I only use the app for groceries").</p>
          </div>
          <div className="p-4 rounded-lg bg-[#0C831F]/10 border border-[#0C831F]/20">
            <h4 className="font-body-sm text-body-sm font-bold text-[#0C831F] mb-2">Positive Review</h4>
            <p className="font-body-sm text-body-sm text-on-surface-variant">The customer praises the app's convenience, selection, or successfully discovered and purchased a product from a new non-grocery category.</p>
          </div>
        </div>
      </div>
    </>
  );
}
