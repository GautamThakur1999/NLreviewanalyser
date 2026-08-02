export default function SegmentsPage() {
  return (
    <>
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">User Segments</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">Behavioral segmentation based on category exploration patterns.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Segment 1 */}
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col hover:-translate-y-1 transition-all duration-200 cursor-default">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="font-title-lg text-title-lg text-on-surface font-bold">The Restocker</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">High frequency, low discovery</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">shopping_basket</span>
            </div>
          </div>
          
          <div className="flex justify-center mb-6">
            <div className="relative w-32 h-32 rounded-full flex items-center justify-center" style={{ background: 'conic-gradient(#ffd67a 0% 55%, transparent 55% 100%)', backgroundColor: '#f3f4f6' }}>
              <div className="w-24 h-24 bg-surface-container-lowest rounded-full flex items-center justify-center card-shadow">
                <span className="font-title-lg text-title-lg font-bold text-on-surface">55%</span>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            <h4 className="font-label-caps text-label-caps text-on-surface-variant font-semibold mb-3">Key Characteristics</h4>
            <ul className="space-y-2 mb-6 flex-1">
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Opens app with a specific list
              </li>
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Repeats previous orders heavily
              </li>
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Rarely scrolls past the first fold
              </li>
            </ul>
            
            <h4 className="font-label-caps text-label-caps text-on-surface-variant font-semibold mb-3 mt-auto">Primary Friction Point</h4>
            <div className="p-3 bg-error/10 text-error rounded-md text-body-sm font-medium border border-error/20">
              Habitual blindness to new categories.
            </div>
          </div>
        </div>

        {/* Segment 2 */}
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col hover:-translate-y-1 transition-all duration-200 cursor-default">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="font-title-lg text-title-lg text-on-surface font-bold">The Skeptic</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Interested, but lacks trust</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-orange-50 text-orange-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">policy</span>
            </div>
          </div>
          
          <div className="flex justify-center mb-6">
            <div className="relative w-32 h-32 rounded-full flex items-center justify-center" style={{ background: 'conic-gradient(#ffd67a 0% 30%, transparent 30% 100%)', backgroundColor: '#f3f4f6' }}>
              <div className="w-24 h-24 bg-surface-container-lowest rounded-full flex items-center justify-center card-shadow">
                <span className="font-title-lg text-title-lg font-bold text-on-surface">30%</span>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            <h4 className="font-label-caps text-label-caps text-on-surface-variant font-semibold mb-3">Key Characteristics</h4>
            <ul className="space-y-2 mb-6 flex-1">
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Browses electronics & beauty
              </li>
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                High cart abandonment rate
              </li>
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Checks return policies frequently
              </li>
            </ul>
            
            <h4 className="font-label-caps text-label-caps text-on-surface-variant font-semibold mb-3 mt-auto">Primary Friction Point</h4>
            <div className="p-3 bg-error/10 text-error rounded-md text-body-sm font-medium border border-error/20">
              Fear of counterfeit products.
            </div>
          </div>
        </div>

        {/* Segment 3 */}
        <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 flex flex-col hover:-translate-y-1 transition-all duration-200 cursor-default">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="font-title-lg text-title-lg text-on-surface font-bold">The Browser</h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Looking for deals & gifts</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">search</span>
            </div>
          </div>
          
          <div className="flex justify-center mb-6">
            <div className="relative w-32 h-32 rounded-full flex items-center justify-center" style={{ background: 'conic-gradient(#ffd67a 0% 15%, transparent 15% 100%)', backgroundColor: '#f3f4f6' }}>
              <div className="w-24 h-24 bg-surface-container-lowest rounded-full flex items-center justify-center card-shadow">
                <span className="font-title-lg text-title-lg font-bold text-on-surface">15%</span>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            <h4 className="font-label-caps text-label-caps text-on-surface-variant font-semibold mb-3">Key Characteristics</h4>
            <ul className="space-y-2 mb-6 flex-1">
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Uses generic search terms
              </li>
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Spends more time per session
              </li>
              <li className="flex gap-2 text-body-md text-on-surface">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                Highly responsive to banners
              </li>
            </ul>
            
            <h4 className="font-label-caps text-label-caps text-on-surface-variant font-semibold mb-3 mt-auto">Primary Friction Point</h4>
            <div className="p-3 bg-error/10 text-error rounded-md text-body-sm font-medium border border-error/20">
              Poor discovery & exact-match search.
            </div>
          </div>
        </div>

      </div>
    </>
  );
}