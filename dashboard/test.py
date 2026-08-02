import re
import json

with open(r'c:\Users\thaku\Downloads\Nextleap Grad Project - Review Analyser\dashboard\local_dom.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Since it's a Next.js hydrated page, the classes are in the JSON chunks.
classnames = re.findall(r'className\\":\\"([^\\"]*)\\"', html)
classnames2 = re.findall(r'className":"([^"]*)"', html)
class_attr = re.findall(r'class="([^"]*)"', html)

all_classes = set(classnames + classnames2 + class_attr)

# Print some of them
print(f"Total unique class strings: {len(all_classes)}")
for c in list(all_classes)[:20]:
    print(c)

if any('bg-surface-container-lowest' in c for c in all_classes):
    print("bg-surface-container-lowest IS FOUND!")
else:
    print("bg-surface-container-lowest IS MISSING!")

