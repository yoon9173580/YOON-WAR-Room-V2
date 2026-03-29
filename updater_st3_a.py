import math

def fmt(n): return f'${int(n):,}'

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

html_snippet = ""
bal = [8128430, 9454972, 15963318, 30140733] # starting balances from ST2

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
    print("ST3 Re-rendered with Option A!")
else:
    print("Markers not found.")
