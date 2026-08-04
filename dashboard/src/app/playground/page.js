import ReviewTester from '@/components/ReviewTester';

export const metadata = {
  title: 'Live Workflow Tester | Category Discovery',
};

export default function PlaygroundPage() {
  return (
    <>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-6 gap-4 sm:gap-0">
        <div>
          <h2 className="font-headline-md text-headline-md font-bold text-on-surface">Live Workflow Tester</h2>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">
            Test the AI engine in real-time. Input a custom review and watch the model extract sentiment, actionable summaries, and map it to core themes.
          </p>
        </div>
      </div>

      <div className="max-w-4xl">
        <ReviewTester />
      </div>
    </>
  );
}
