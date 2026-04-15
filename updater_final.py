import re

def fmt(n): return f'${int(n):,}'

st1_totals = [8705430, 10031972, 16540318, 30717733]

st2_items = [
  ('└ 모빌리티 (본인)', 'Aston Martin / MC20 / Ferrari F430', [-400000]*4, 'pl-indent'),
  ('└ 모빌리티 (아빠)', 'Mercedes-Maybach S-Class', [-120000]*4, 'pl-indent'),
  ('└ 기프트 (아빠)', 'Omega Seamaster Diver 300M', [-22320]*4, 'pl-indent'),
  ('└ 기프트 (엄마)', 'Cartier Tank Louis & LV M27335', [-22548]*4, 'pl-indent'),
  ('└ 기프트 (진이)', 'Omega Aqua Terra & Dior Bag', [-13920]*4, 'pl-indent')
]
st2_tot = sum([400000, 120000, 22320, 22548, 13920]) 

# ST 3 values
fid_val = [904560, 1042400, 1718665, 3191806]
moo_val = [1500870, 1729572, 2851653, 5295927]
cs_val = [-3500000, -3500000, -3500000, -3500000]

def split_3(amt):
    base = amt // 3
    return [base, base, amt - (base * 2)]

fid_splits = [split_3(v) for v in fid_val]
moo_splits = [split_3(v) for v in moo_val]

st3_items = [
  ('└ [CS] 현물', 'GME 100,000주 집중 확보 (Infinity)', cs_val, 'accent'),
  ('└ [Fid] 옵션', "'27/'28 LEAPS (잔고 100% 풀매수)", [-x for x in fid_val], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Fidelity) 1/3', [-fid_splits[0][0], -fid_splits[1][0], -fid_splits[2][0], -fid_splits[3][0]], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Fidelity) 1/3', [-fid_splits[0][1], -fid_splits[1][1], -fid_splits[2][1], -fid_splits[3][1]], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Fidelity) 1/3', [-fid_splits[0][2], -fid_splits[1][2], -fid_splits[2][2], -fid_splits[3][2]], 'pl-indent-2'),
  ('└ [Moo] 옵션', "'27/'28 LEAPS (잔고 100% 풀매수)", [-x for x in moo_val], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Moomoo) 1/3', [-moo_splits[0][0], -moo_splits[1][0], -moo_splits[2][0], -moo_splits[3][0]], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Moomoo) 1/3', [-moo_splits[0][1], -moo_splits[1][1], -moo_splits[2][1], -moo_splits[3][1]], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Moomoo) 1/3', [-moo_splits[0][2], -moo_splits[1][2], -moo_splits[2][2], -moo_splits[3][2]], 'pl-indent-2')
]

# ST 4 Values
st4_mult = 1.5 
def calc_bases(tot):
    clat = int(tot / 7)
    qof = clat * 2
    og = tot - qof - clat
    return og, qof, clat

bases = [calc_bases(v) for v in st1_totals]

og_base = [b[0] for b in bases]
qof_base = [b[1] for b in bases]
clat_base = [b[2] for b in bases]

st4_items = [
  ('└ GME Partial Sell', '180일 내 LEAPS/현물 부분 청산', [int(v*st4_mult) for v in st1_totals], 'bull', True),
  ('└ O&G (Energy)', 'IDC 100% 공제 (에너지 유정 WI)', [int(-v*st4_mult) for v in og_base], '', False),
  ('└ QOF Housing', 'QOZ 다세대 주택 (10년 면세)', [int(-v*st4_mult) for v in qof_base], '', False),
  ('└ CLAT (Trust)', '자선 소득 신탁 (즉시 소득 공제)', [int(-v*st4_mult) for v in clat_base], '', False)
]

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

html_snippet = ""
bal = list(st1_totals)

# ST 2
html_snippet += '<!-- ST 2 ITEMS -->\n'
row = '                <tr class="st-main">\n                  <td>ST 2. 즉시 집행금</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Immediate Rewards)]</td>\n'
for i in range(4): row += f'                  <td class="r neg">-{fmt(st2_tot)}</td>\n'
row += '                </tr>\n'
html_snippet += row

for name, det, vals, cls in st2_items:
    row = f'                <tr class="st-sub">\n                  <td class="{cls}">{name}</td>\n                  <td class="det">{det}</td>\n'
    for i in range(4):
        bal[i] += vals[i]
        row += f'                  <td class="r neg">-{fmt(abs(vals[i]))}<br><span class="bal">BAL {fmt(bal[i])}</span></td>\n'
    row += '                </tr>\n'
    html_snippet += row
    
row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [현금 잔고]</td>\n                  <td class="det-cash">즉시 집행 후 유동 현금</td>\n'
for i in range(4): row += f'                  <td class="r pos">{fmt(bal[i])}</td>\n'
row += '                </tr>\n'
html_snippet += row

# ST 3
gme_tot = [cs_val[i] - fid_val[i] - moo_val[i] for i in range(4)]
row = '                <tr class="st-main">\n                  <td>ST 3. 브로커 전액 GME 투입</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Broker-Isolated Pipeline)]</td>\n'
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

row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [최종 잔고]</td>\n                  <td class="det-cash">CS 잔존 캐쉬 (은행 브릿지 이체용)</td>\n'
for i in range(4): row += f'                  <td class="r pos">{fmt(bal[i])}</td>\n'
row += '                </tr>\n'
html_snippet += row

# ST 4
st4_tot = [int(-v*st4_mult) for v in st1_totals]
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

start_marker = '<!-- ST 2 ITEMS -->'
end_marker = '                <!-- ST 5 -->'

if start_marker in text and end_marker in text:
    pre = text[:text.find(start_marker)]
    post_idx = text.find(end_marker)
    post = text[post_idx:]
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(pre + html_snippet + post)
    print("ST2-ST4 successfully fully updated!")
else:
    print("Markers not found.")
