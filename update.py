import re

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

with open('output3.html', 'r', encoding='utf-8') as f:
    replacement = f.read()

# The ST 3 header is:
#                   <td>ST 3. 초기 GME 투입</td>
# We want to replace from the first <tr class="st-sub"> after that up to the end of ST 3 which is right before <tr class="st-cash">

start_marker = '<tr class="st-main">\n                  <td>ST 3. 초기 GME 투입</td>'
end_marker = '<tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [현금 잔고]</td>\n                  <td class="det-cash">풀-디플로이 후 잔존 금액</td>'

if start_marker in text and end_marker in text:
    pre = text[:text.find(start_marker)]
    mid_start = text.find(start_marker)
    # find where st-sub starts after mid_start
    first_st_sub = text.find('<tr class="st-sub">', mid_start)
    
    post_idx = text.find(end_marker)
    post = text[post_idx:]
    
    new_text = text[:first_st_sub] + replacement + post
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Successfully replaced ST 3 chunk.")
else:
    print("Markers not found!")
