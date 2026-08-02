"use client";
import { useDashboardData } from '@/data/dataEngine';

export default function BarriersPage() {
  const data = useDashboardData();

  // Helper for sentiment colors
  let sentimentColor = "text-error";
  let sentimentBg = "bg-error-container text-on-error-container";
  let sentimentBorder = "border-l-error";
  let sentimentIcon = "sentiment_dissatisfied";

  if (data.overview.overallSentiment.label === 'Positive') {
    sentimentColor = "text-[#0C831F]";
    sentimentBg = "bg-[#0C831F]/20 text-[#0C831F]";
    sentimentBorder = "border-l-[#0C831F]";
    sentimentIcon = "sentiment_satisfied";
  } else if (data.overview.overallSentiment.label === 'Neutral') {
    sentimentColor = "text-surface-variant";
    sentimentBg = "bg-surface-variant/20 text-on-surface-variant";
    sentimentBorder = "border-l-surface-variant";
    sentimentIcon = "sentiment_neutral";
  }

  // Calculate Primary Barrier dynamically
  const primaryBarrier = data.barriers[0];

  return (
    <>
      {/* Page Header */}
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">Themes & Barriers</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">Deep dive into friction points and extracted themes across sources.</p>
        </div>
        <button className="flex items-center gap-2 bg-primary-container text-[#1F1F1F] font-body-sm text-body-sm font-semibold px-4 py-2 rounded-md hover:bg-primary-fixed transition-colors card-shadow">
          <span className="material-symbols-outlined text-[18px]">download</span>
          Export Report
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Total Themes Identified</h3>
            <div className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">category</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="font-display-lg text-display-lg text-on-surface font-bold tracking-tight">{data.overview.themesIdentified}</div>
          </div>
        </div>
        
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Primary Barrier</h3>
            <div className="w-8 h-8 rounded-full bg-orange-50 text-orange-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">block</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className="font-display-md text-display-md text-on-surface font-bold tracking-tight truncate max-w-full" title={primaryBarrier.label}>
              {primaryBarrier.label}
            </div>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-2">Accounts for {primaryBarrier.value}% of friction.</p>
        </div>

        <div className={`bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col justify-between border-l-4 ${sentimentBorder} hover:border-primary-container hover:-translate-y-1 transition-all duration-200 cursor-pointer`}>
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-title-sm text-title-sm text-on-surface-variant">Theme Sentiment</h3>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${sentimentBg}`}>
              <span className="material-symbols-outlined text-[18px]">{sentimentIcon}</span>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <div className={`font-display-lg text-display-lg font-bold tracking-tight ${sentimentColor}`}>{data.overview.overallSentiment.value}%</div>
            <span className={`font-body-sm text-body-sm font-medium ${sentimentColor}`}>{data.overview.overallSentiment.label} overall</span>
          </div>
        </div>
      </div>

      {/* Main Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        
        {/* Left: Detailed Themes List */}
        <div className="lg:col-span-8 bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-title-sm text-title-sm text-on-surface font-bold">Theme Prevalence</h3>
            <div className="flex gap-2">
              <button className="flex items-center gap-1 text-on-surface-variant bg-surface-container-high px-2 py-1 rounded text-body-sm font-medium hover:bg-surface-variant transition-colors">
                Sort by: Mention Volume
                <span className="material-symbols-outlined text-[14px]">expand_more</span>
              </button>
            </div>
          </div>
          
          <div className="space-y-6">
            {/* Theme 1 */}
            <div className="group cursor-pointer">
              <div className="flex justify-between items-end mb-2">
                <div>
                  <h4 className="font-body-lg text-body-lg font-bold text-on-surface">App is just for groceries</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Users do not associate the platform with non-grocery categories.</p>
                </div>
                <div className="text-right">
                  <span className="font-title-md text-title-md font-bold text-on-surface">42%</span>
                </div>
              </div>
              <div className="w-full bg-surface-container-high rounded-full h-2">
                <div className="bg-primary-container h-2 rounded-full group-hover:brightness-90 transition-all" style={{ width: '42%' }}></div>
              </div>
            </div>

            {/* Theme 2 */}
            <div className="group cursor-pointer">
              <div className="flex justify-between items-end mb-2">
                <div>
                  <h4 className="font-body-lg text-body-lg font-bold text-on-surface">Lack of trust in pharmacy/beauty</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Concerns about product authenticity for sensitive categories.</p>
                </div>
                <div className="text-right">
                  <span className="font-title-md text-title-md font-bold text-on-surface">28%</span>
                </div>
              </div>
              <div className="w-full bg-surface-container-high rounded-full h-2">
                <div className="bg-error/70 h-2 rounded-full group-hover:brightness-90 transition-all" style={{ width: '28%' }}></div>
              </div>
            </div>

            {/* Theme 3 */}
            <div className="group cursor-pointer">
              <div className="flex justify-between items-end mb-2">
                <div>
                  <h4 className="font-body-lg text-body-lg font-bold text-on-surface">Search vs Browse behavior</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Users type exactly what they want, minimizing accidental discovery.</p>
                </div>
                <div className="text-right">
                  <span className="font-title-md text-title-md font-bold text-on-surface">18%</span>
                </div>
              </div>
              <div className="w-full bg-surface-container-high rounded-full h-2">
                <div className="bg-primary-container/80 h-2 rounded-full group-hover:brightness-90 transition-all" style={{ width: '18%' }}></div>
              </div>
            </div>
            
            {/* Theme 4 */}
            <div className="group cursor-pointer">
              <div className="flex justify-between items-end mb-2">
                <div>
                  <h4 className="font-body-lg text-body-lg font-bold text-on-surface">Pricing concerns</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Perception that specialized items are marked up compared to Amazon/Nykaa.</p>
                </div>
                <div className="text-right">
                  <span className="font-title-md text-title-md font-bold text-on-surface">12%</span>
                </div>
              </div>
              <div className="w-full bg-surface-container-high rounded-full h-2">
                <div className="bg-primary-container/60 h-2 rounded-full group-hover:brightness-90 transition-all" style={{ width: '12%' }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Key Barriers */}
        <div className="lg:col-span-4 bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col">
          <h3 className="font-title-sm text-title-sm text-on-surface font-bold mb-6">Top Friction Points</h3>
          
          <div className="flex flex-col gap-4 flex-1">
            <div className="p-4 border border-outline-variant/50 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer">
              <div className="flex justify-between items-start mb-1">
                <span className="font-body-md text-body-md font-bold">Habit Loop</span>
                <span className="bg-error/10 text-error px-2 py-0.5 rounded-full font-label-caps text-label-caps">High</span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant">Users instinctively open the app only when restocking staples like milk and eggs.</p>
            </div>

            <div className="p-4 border border-outline-variant/50 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer">
              <div className="flex justify-between items-start mb-1">
                <span className="font-body-md text-body-md font-bold">Authenticity</span>
                <span className="bg-error/10 text-error px-2 py-0.5 rounded-full font-label-caps text-label-caps">High</span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant">Deep skepticism regarding cosmetics, pharmacy, and health supplements.</p>
            </div>

            <div className="p-4 border border-outline-variant/50 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer">
              <div className="flex justify-between items-start mb-1">
                <span className="font-body-md text-body-md font-bold">Visibility</span>
                <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Medium</span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant">Non-grocery categories are hidden behind sub-menus or require vertical scrolling.</p>
            </div>
            
            <div className="p-4 border border-outline-variant/50 rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer">
              <div className="flex justify-between items-start mb-1">
                <span className="font-body-md text-body-md font-bold">Price Anxiety</span>
                <span className="bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded-full font-label-caps text-label-caps">Medium</span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant">Users compare electronics and beauty directly against specialist platforms.</p>
            </div>
          </div>
        </div>

      </div>

    </>
  );
}