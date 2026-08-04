"use client";

export default function InsightsPage() {
  const questions = [
    {
      q: "1. Why do users repeatedly buy from the same categories?",
      confidence: "High Confidence",
      mentions: "2,140 Mentions",
      answer: "Users view Blinkit primarily as a utility for routine restocking (habit) and speed-optimised distress purchasing. The app’s UX currently optimizes for this behavior, making repeat purchases of groceries seamless but inadvertently limiting exploration. Users don't venture into new categories because they treat the app like a digital convenience store rather than a supermarket.",
      quote: "I open the app, click my last order, add milk and eggs, and check out in 30 seconds. I don't even look at the other tabs.",
      sourceIcon: "android",
      sourceLabel: "Play Store",
      quoteColor: "border-l-primary-container"
    },
    {
      q: "2. What prevents users from exploring new categories?",
      confidence: "High Confidence",
      mentions: "1,820 Mentions",
      answer: "The primary barrier is a severe trust and authenticity gap, especially for Personal Care and Electronics. Awareness is also a secondary barrier; many users simply do not know Blinkit stocks these items. Price perception also plays a role, with users assuming specialised platforms offer better discounts.",
      quote: "Saw a Lakme serum on there but I was too scared it might be a fake. Rather wait 2 days for Nykaa to deliver the real thing.",
      sourceIcon: "forum",
      sourceLabel: "Reddit",
      quoteColor: "border-l-error"
    },
    {
      q: "3. How do users discover products today?",
      confidence: "Medium Confidence",
      mentions: "950 Mentions",
      answer: "Discovery is overwhelmingly search-driven rather than browse-driven. Users type exactly what they need in the search bar. The homepage rails (e.g., 'Bestsellers') have low engagement for category discovery because users are usually in a 'mission mode' to quickly buy a specific item.",
      quote: "I never scroll the homepage. I just search for 'bread' or 'chips' and checkout immediately.",
      sourceIcon: "phone_iphone",
      sourceLabel: "App Store",
      quoteColor: "border-l-surface-variant"
    },
    {
      q: "4. What role do habits play in shopping behaviour?",
      confidence: "High Confidence",
      mentions: "1,540 Mentions",
      answer: "Habit formation is extremely rapid. Within the first 3-4 orders, a user's repertoire calcifies. If a user only buys snacks in their first month, they are highly unlikely to independently explore household essentials in month two without a targeted intervention.",
      quote: "Blinkit is just my late-night munchies app. I've never even thought about buying my actual monthly groceries from them.",
      sourceIcon: "forum",
      sourceLabel: "Reddit",
      quoteColor: "border-l-primary-container"
    },
    {
      q: "5. What information do users need before trying a new category?",
      confidence: "High Confidence",
      mentions: "1,210 Mentions",
      answer: "For food and cosmetics, users demand expiry/freshness guarantees. For electronics, they require clear return policies, warranty details, and brand authenticity seals. This information is currently difficult to find or completely missing on product detail pages.",
      quote: "I wanted to buy a charger but couldn't find if it had a 1-year warranty or if I could return it if it didn't work. Didn't buy it.",
      sourceIcon: "android",
      sourceLabel: "Play Store",
      quoteColor: "border-l-error"
    },
    {
      q: "6. What frustrations emerge repeatedly?",
      confidence: "Medium Confidence",
      mentions: "880 Mentions",
      answer: "Users are frequently frustrated by inconsistent search results that prioritize FMCG over curated non-grocery items. Additionally, stockouts in critical 'anchor' items (like milk) often lead users to abandon the entire basket, including explored items.",
      quote: "Searched for a baby bottle and it showed me a bunch of random baby food first. The search is clearly optimized just for groceries.",
      sourceIcon: "phone_iphone",
      sourceLabel: "App Store",
      quoteColor: "border-l-surface-variant"
    },
    {
      q: "7. Which user segments are more likely to experiment?",
      confidence: "Low Confidence",
      mentions: "420 Mentions",
      answer: "Young urban professionals (especially those living alone) show a higher propensity to experiment with electronics and personal care on quick commerce. Families and older demographics are more entrenched in traditional e-commerce for non-grocery needs.",
      quote: "I live alone and work 14 hours a day. Getting a face wash delivered in 10 mins is a lifesaver, I don't care if it costs 20rs more.",
      sourceIcon: "forum",
      sourceLabel: "Reddit",
      quoteColor: "border-l-primary-container"
    },
    {
      q: "8. What unmet needs emerge consistently across discussions?",
      confidence: "Medium Confidence",
      mentions: "760 Mentions",
      answer: "There is strong latent demand for 'bundled' or 'kit' purchases for specific occasions (e.g., 'movie night kit', 'sick day kit', 'travel essentials kit'). Users want Blinkit to do the thinking for them rather than having to search for 5 different items.",
      quote: "I was sick with the flu and just wanted a 'fever kit' with meds, soup, and tissues. Instead I had to search for each thing individually while my head was pounding.",
      sourceIcon: "android",
      sourceLabel: "Play Store",
      quoteColor: "border-l-[#0C831F]"
    }
  ];

  return (
    <>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-6 gap-4 sm:gap-0">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">Research Questions</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">Core questions answered by the review analysis pipeline based on the problem statement.</p>
        </div>
      </div>

      <div className="space-y-6 mb-8">
        {questions.map((item, i) => (
          <div key={i} className="bg-surface-container-lowest rounded-xl p-6 card-shadow border border-outline-variant/30 hover:border-primary-container transition-colors">
            <h3 className="font-title-lg text-title-lg text-on-surface font-bold mb-3">{item.q}</h3>
            <div className="flex gap-2 mb-4">
              <span className={`px-3 py-1 rounded-full font-label-caps text-label-caps border ${
                item.confidence === 'High Confidence' ? 'bg-primary-container/20 text-primary border-primary-container/30' : 
                item.confidence === 'Medium Confidence' ? 'bg-surface-variant text-on-surface-variant border-outline-variant/30' :
                'bg-error/10 text-error border-error/30'
              }`}>
                {item.confidence}
              </span>
              <span className="bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full font-label-caps text-label-caps">{item.mentions}</span>
            </div>
            
            <p className="font-body-md text-body-md text-on-surface-variant mb-6">
              {item.answer}
            </p>

            <div className={`bg-background p-4 rounded-lg border border-outline-variant/30 border-l-4 ${item.quoteColor} relative`}>
              <p className="font-body-sm text-body-sm text-on-surface-variant italic relative z-10 w-11/12">"{item.quote}"</p>
              <div className="mt-3 flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px] text-on-surface-variant">{item.sourceIcon}</span>
                <span className="font-label-caps text-label-caps text-on-surface-variant">{item.sourceLabel}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
