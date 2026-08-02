import re
import os

html_path = r'c:\Users\thaku\Downloads\Nextleap Grad Project - Review Analyser\stitch_category_discovery_insights\stitch_category_discovery_insights\overview_category_discovery_insights\code.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Extract main content
main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
content = main_match.group(1)

# Convert class to className
content = content.replace('class=', 'className=')

# Convert style tags
def style_replacer(match):
    style_str = match.group(1)
    # Simple conversion for standard style string to react style object
    rules = [r.split(':') for r in style_str.split(';') if ':' in r]
    style_obj = {}
    for k, v in rules:
        k = k.strip()
        # Convert kebab case to camel case
        k_camel = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(k.split('-')))
        style_obj[k_camel] = v.strip()
    
    # Format as dict string for JSX
    style_formatted = ', '.join([f'"{k}": "{v}"' for k, v in style_obj.items()])
    return f'style={{{{ {style_formatted} }}}}'

content = re.sub(r'style="(.*?)"', style_replacer, content)

# Fix empty tags for jsx like <input ...> without closing slash
content = re.sub(r'(<input[^>]*)(?<!/)>', r'\1 />', content)
content = re.sub(r'(<img[^>]*)(?<!/)>', r'\1 />', content)

# Write to page.js
page_js_content = f'''export default function Page() {{
  return (
    <>
      {{/* Ported from HTML */}}
      {content}
    </>
  );
}}
'''

with open(r'c:\Users\thaku\Downloads\Nextleap Grad Project - Review Analyser\dashboard\src\app\page.js', 'w', encoding='utf-8') as f:
    f.write(page_js_content)
print('Done!')
