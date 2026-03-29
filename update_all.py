import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

with open('output_all.html', 'r', encoding='utf-8') as f:
    replacement = f.read()

start_marker = '<tr class="st-main">\n                  <td>ST 2. 즉시 집행금</td>'
end_marker = '              </tbody>'

if start_marker in text and end_marker in text:
    pre = text[:text.find(start_marker)]
    # Look for the last row before ST5 begins.
    # Wait, ST 5 starts after ST 4. Let's find ST 5.
    st5_marker = '<tr class="st-main">\n                  <td>ST 5. 최종 완성</td>'
    if st5_marker in text:
        post_idx = text.find(st5_marker)
        post = text[post_idx:]
        
        # New replacement must be injected correctly right before ST 5
        new_text = pre + replacement + post
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Successfully replaced ST2-ST4 chunks.")
    else:
        print("ST 5 Marker not found!")
else:
    print("Start or End Markers not found!")
