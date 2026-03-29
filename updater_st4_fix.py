import re

st4_mult = 1.5 # GME STCG 방어를 위한 하드코딩 볼륨 증폭 배수!

st4_items = [
  ('└ GME Partial Sell', '180일 내 LEAPS/현물 부분 청산', [int(3500000*st4_mult), int(4000000*st4_mult), int(7500000*st4_mult), int(14000000*st4_mult)], 'bull', True),
  ('└ O&G (Energy)', 'IDC 100% 공제 (에너지 유정 WI)', [int(-2000000*st4_mult), int(-2000000*st4_mult), int(-4500000*st4_mult), int(-8000000*st4_mult)], '', False),
  ('└ QOF Housing', 'QOZ 다세대 주택 (10년 면세)', [int(-1000000*st4_mult), int(-1000000*st4_mult), int(-2000000*st4_mult), int(-4000000*st4_mult)], '', False),
  ('└ CLAT (Trust)', '자선 소득 신탁 (즉시 소득 공제)', [int(-500000*st4_mult), int(-1000000*st4_mult), int(-1000000*st4_mult), int(-2000000*st4_mult)], '', False)
]

def fmt(n): return f'${n:,}'

html_snippet = ""
bal = [2223000, 3183000, 7893000, 18153000] # NEW starting balances from ST3 (Option A)

st4_tot = [int(-3500000*st4_mult), int(-4000000*st4_mult), int(-7500000*st4_mult), int(-14000000*st4_mult)]
row = '                <tr class="st-main">\n                  <td>ST 4. 절세 제국 스케일업</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Includes GME STCG)]</td>\n'
for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(st4_tot[i]))}</td>\n'
row += '                </tr>\n'
html_snippet += row

for name, det, vals, cls, ispos in st4_items:
    c = "bull" if ispos else "neg"
    sym = "+" if ispos else "-"
    td_cls = cls if "bull" not in cls else "pl-indent"
    td_style = f'style="color:var(--{cls});"' if "bull" in cls else ""
    row = f'                <tr class="st-sub">\n                  <td class="{td_cls}" {td_style}>{name}</td>\n                  <td class="det">{det}</td>\n'
    for i in range(4):
        bal[i] += vals[i]
        row += f'                  <td class="r {c}">{sym}{fmt(abs(vals[i]))}<br><span class="bal">BAL {fmt(bal[i])}</span></td>\n'
    row += '                </tr>\n'
    html_snippet += row
    
row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [최종 현금 잔고]</td>\n                  <td class="det-cash">Tax Shield 방어 후 생존 잔고</td>\n'
for i in range(4): row += f'                  <td class="r pos" style="color:var(--bull); font-weight:900;">{fmt(bal[i])}</td>\n'
row += '                </tr>\n'
html_snippet += row

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = '<tr class="st-main">\n                  <td>ST 4. 절세 제국 스케일업</td>'
end_marker = '                <!-- ST 5 -->'

if start_marker in text and end_marker in text:
    pre = text[:text.find(start_marker)]
    post_idx = text.find(end_marker)
    post = text[post_idx:]
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(pre + html_snippet + post)
    print("ST4 perfectly re-rendered to align with Option A balances")
else:
    print("Markers not found.")
