import os

pages = ['barriers', 'validation', 'insights', 'segments']
base_dir = r'c:\Users\thaku\Downloads\Nextleap Grad Project - Review Analyser\dashboard\src\app'

for page in pages:
    page_name = page.capitalize().replace('-', ' ')
    if page == 'barriers': page_name = 'Themes & Barriers'
    if page == 'validation': page_name = 'Hypothesis Scorecard'
    if page == 'insights': page_name = 'Research Questions'
    if page == 'segments': page_name = 'Segments'
    
    content = f"""export default function Page() {{
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-center">
      <span className="material-symbols-outlined text-[64px] text-outline-variant mb-6">construction</span>
      <h2 className="font-headline-md text-headline-md font-bold text-on-surface mb-2">{page_name}</h2>
      <p className="font-body-md text-body-md text-on-surface-variant max-w-md">
        This page was not included in the original HTML template provided. It is currently under construction.
      </p>
    </div>
  );
}}"""
    
    os.makedirs(os.path.join(base_dir, page), exist_ok=True)
    with open(os.path.join(base_dir, page, 'page.js'), 'w', encoding='utf-8') as f:
        f.write(content)

print("Created placeholder pages.")
