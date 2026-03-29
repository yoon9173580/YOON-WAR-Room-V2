import re

st4_mult = 1.5 # GME STCG 방어를 위한 하드코딩 볼륨 증폭 배수!

st3_items = [
  ('└ [CS] 현물', 'GME 100,000주 집중 확보 (Infinity)', [-3500000, -3500000, -3500000, -3500000], 'accent'),
  ('└ [Fid] 옵션', "'27/'28 LEAPS (초기 화력 80%)", [-2800000, -3600000, -8400000, -18800000], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Fidelity) 1/3', [-933333, -1200000, -2800000, -6266666], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Fidelity) 1/3', [-933333, -1200000, -2800000, -6266667], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Fidelity) 1/3', [-933334, -1200000, -2800000, -6266667], 'pl-indent-2'),
  ('└ [Moo] 옵션', "'27/'28 LEAPS (초기 화력 20%)", [-700000, -900000, -2100000, -4700000], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Moomoo) 1/3', [-233333, -300000, -700000, -1566666], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Moomoo) 1/3', [-233333, -300000, -700000, -1566667], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Moomoo) 1/3', [-233334, -300000, -700000, -1566667], 'pl-indent-2')
]

def fmt(n): return f'${n:,}'

html_snippet = ""
bal = [int(8128430), int(9454972), int(15963318), int(30140733)] # starting balances from ST2

gme_tot = [-7000000, -8000000, -14000000, -27000000]
row = '                <tr class="st-main">\n                  <td>ST 3. 초기 GME 투입</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Clean Millions Target)]</td>\n'
for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(gme_tot[i]))}</td>\n'
row += '                </tr>\n'
html_snippet += row

for name, det, vals, cls in st3_items:
    if "옵션" in name and "LEAPS" in det:
        row = f'                <tr class="st-sub">\n                  <td class="pl-indent" style="color:var(--{cls});">{name}</td>\n                  <td class="det">{det}</td>\n'
        for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(vals[i]))}</td>\n'
        row += '                </tr>\n'
        html_snippet += row
        continue
        
    td_cls = cls if "-2" in cls else "pl-indent"
    td_style = f'style="color:var(--{cls});"' if "accent" in cls else ""
    row = f'                <tr class="st-sub">\n                  <td class="{td_cls}" {td_style}>{name}</td>\n                  <td class="det">{det}</td>\n'
    for i in range(4):
        bal[i] += vals[i]
        row += f'                  <td class="r neg">-{fmt(abs(vals[i]))}<br><span class="bal">BAL {fmt(bal[i])}</span></td>\n'
    row += '                </tr>\n'
    html_snippet += row

row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [현금 잔고]</td>\n                  <td class="det-cash">Reserve & 남은 여유 캐시</td>\n'
for i in range(4): row += f'                  <td class="r pos">{fmt(bal[i])}</td>\n'
row += '                </tr>\n'
html_snippet += row

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = '<tr class="st-main">\n                  <td>ST 3. 초기 GME 투입</td>'
end_marker = '                <tr class="st-main">\n                  <td>ST 4. 절세 제국 스케일업</td>'

if start_marker in text and end_marker in text:
    pre = text[:text.find(start_marker)]
    post_idx = text.find(end_marker)
    post = text[post_idx:]
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(pre + html_snippet + post)
    print("ST3 perfectly re-rendered collapsing shares into Computershare")
else:
    print("Markers not found.")
