export default function ValidationPage() {
  return (
    <>
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">Hypothesis Scorecard</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">Status of core business hypotheses against review data evidence.</p>
        </div>
        <button className="flex items-center gap-2 bg-primary-container text-[#1F1F1F] font-body-sm text-body-sm font-semibold px-4 py-2 rounded-md hover:bg-primary-fixed transition-colors card-shadow">
          <span className="material-symbols-outlined text-[18px]">download</span>
          Export Scorecard
        </button>
      </div>

      <div className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant/50">
                <th className="pb-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Hypothesis</th>
                <th className="pb-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Status</th>
                <th className="pb-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Evidence Strength</th>
                <th className="pb-4 font-label-caps text-label-caps text-on-surface-variant font-semibold">Key Metric</th>
              </tr>
            </thead>
            <tbody className="font-body-md text-body-md">
              <tr className="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors">
                <td className="py-4 pr-4">
                  <div className="font-body-lg text-body-lg font-bold text-on-surface mb-1">Users are unaware we sell electronics</div>
                  <div className="text-body-sm text-on-surface-variant">Assumption that low electronics penetration is an awareness problem.</div>
                </td>
                <td className="py-4 pr-4">
                  <span className="bg-status-green/10 text-status-green px-3 py-1 rounded-full font-label-caps text-label-caps border border-status-green/20">Validated</span>
                </td>
                <td className="py-4 pr-4">
                  <div className="flex gap-1 mb-1">
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                  </div>
                  <div className="text-body-sm text-on-surface-variant">High</div>
                </td>
                <td className="py-4 text-on-surface">
                  <span className="font-bold text-title-sm">18%</span> of low-rating reviews mention "I didn't know" or "Since when".
                </td>
              </tr>
              
              <tr className="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors">
                <td className="py-4 pr-4">
                  <div className="font-body-lg text-body-lg font-bold text-on-surface mb-1">Users prefer specialized apps for beauty products</div>
                  <div className="text-body-sm text-on-surface-variant">Assumption that users use Nykaa/Purplle out of habit.</div>
                </td>
                <td className="py-4 pr-4">
                  <span className="bg-status-green/10 text-status-green px-3 py-1 rounded-full font-label-caps text-label-caps border border-status-green/20">Validated</span>
                </td>
                <td className="py-4 pr-4">
                  <div className="flex gap-1 mb-1">
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-surface-variant rounded-sm"></div>
                  </div>
                  <div className="text-body-sm text-on-surface-variant">Medium</div>
                </td>
                <td className="py-4 text-on-surface">
                  <span className="font-bold text-title-sm">Nykaa</span> mentioned natively in 320 comparative reviews.
                </td>
              </tr>

              <tr className="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors">
                <td className="py-4 pr-4">
                  <div className="font-body-lg text-body-lg font-bold text-on-surface mb-1">Pricing is the main deterrent for new categories</div>
                  <div className="text-body-sm text-on-surface-variant">Assumption that users think our non-grocery items are more expensive.</div>
                </td>
                <td className="py-4 pr-4">
                  <span className="bg-error/10 text-error px-3 py-1 rounded-full font-label-caps text-label-caps border border-error/20">Invalidated</span>
                </td>
                <td className="py-4 pr-4">
                  <div className="flex gap-1 mb-1">
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                  </div>
                  <div className="text-body-sm text-on-surface-variant">High</div>
                </td>
                <td className="py-4 text-on-surface">
                  Pricing accounts for only <span className="font-bold text-title-sm">4%</span> of barriers. Authenticity is 6x higher.
                </td>
              </tr>

              <tr className="hover:bg-surface-container-low transition-colors">
                <td className="py-4 pr-4">
                  <div className="font-body-lg text-body-lg font-bold text-on-surface mb-1">The search interface limits discovery</div>
                  <div className="text-body-sm text-on-surface-variant">Assumption that typing "milk" prevents seeing "chargers".</div>
                </td>
                <td className="py-4 pr-4">
                  <span className="bg-surface-variant text-on-surface-variant px-3 py-1 rounded-full font-label-caps text-label-caps border border-outline-variant/50">Mixed</span>
                </td>
                <td className="py-4 pr-4">
                  <div className="flex gap-1 mb-1">
                    <div className="w-3 h-4 bg-primary-container rounded-sm"></div>
                    <div className="w-3 h-4 bg-surface-variant rounded-sm"></div>
                    <div className="w-3 h-4 bg-surface-variant rounded-sm"></div>
                  </div>
                  <div className="text-body-sm text-on-surface-variant">Low</div>
                </td>
                <td className="py-4 text-on-surface">
                  Mentioned frequently, but rarely cited as the <span className="font-bold text-title-sm">primary</span> reason for a bad experience.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}