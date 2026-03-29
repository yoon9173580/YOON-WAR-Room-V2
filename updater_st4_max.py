import math

st4_mult = 1.5 # GME STCG 방어를 위한 증폭 배수!

# ST 1 Gross Totals
st1_val = [8705430, 10031972, 16540318, 30717733]

# Base values (100% of ST 1)
def calc_bases(tot):
    clat = int(tot / 7)
    qof = clat * 2
    og = tot - qof - clat # remainder goes to O&G (which is 4/7)
    return og, qof, clat

bases = [calc_bases(v) for v in st1_val]

og_base = [b[0] for b in bases]
qof_base = [b[1] for b in bases]
clat_base = [b[2] for b in bases]

st4_items = [
  ('└ GME Partial Sell', '180일 내 LEAPS/현물 부분 청산', [int(v*st4_mult) for v in st1_val], 'bull', True),
  ('└ O&G (Energy)', 'IDC 100% 공제 (에너지 유정 WI)', [int(-v*st4_mult) for v in og_base], '', False),
  ('└ QOF Housing', 'QOZ 다세대 주택 (10년 면세)', [int(-v*st4_mult) for v in qof_base], '', False),
  ('└ CLAT (Trust)', '자선 소득 신탁 (즉시 소득 공제)', [int(-v*st4_mult) for v in clat_base], '', False)
]

def fmt(n): return f'${n:,}'

html_snippet = ""
bal = [2223000, 3183000, 7893000, 18153000] # Option A starting balances from ST3

st4_tot = [int(-v*st4_mult) for v in st1_val]
row = '                <tr class="st-main">\n                  <td>ST 4. 절세 제국 스케일업</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (BBBY + GME STCG Offset)]</td>\n'
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
    print("ST4 Max Shield successfully generated to 100% of ST 1 income!")
else:
    print("Markers not found.")
