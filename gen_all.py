def fmt(n): return f'${n:,}'

st4_mult = 1.5 # GME STCG 방어를 위한 하드코딩 볼륨 증폭 배수!

st1_totals = [8705430, 10031972, 16540318, 30717733]

st2_items = [
  ('└ 모빌리티 (본인)', 'Aston Martin / MC20 / Ferrari F430', [-400000, -400000, -400000, -400000], 'pl-indent'),
  ('└ 모빌리티 (아빠)', 'Mercedes-Maybach S-Class', [-120000, -120000, -120000, -120000], 'pl-indent'),
  ('└ 가족 조공 (엄마)', '구찌 에르메스 & 롤렉스', [-22000, -22000, -22000, -22000], 'pl-indent'),
  ('└ 가족 조공 (동생)', '샤넬 VCA & 오메가 샷건', [-22000, -22000, -22000, -22000], 'pl-indent'),
  ('└ 지인 하사 (은혜)', '고마운 분들 명품 선물', [-13000, -13000, -13000, -13000], 'pl-indent')
]

st3_items = [
  ('└ [DRS] 현물', 'GME 70,000주 확보 (Infinity)', [-2450000, -2450000, -2450000, -2450000], 'accent'),
  ('└ [Fid] 현물', 'GME 20,000주 확보 (Main)', [-700000, -700000, -700000, -700000], 'accent'),
  ('└ [Moo] 현물', 'GME 10,000주 확보 (Tactical)', [-350000, -350000, -350000, -350000], 'accent'),
  ('└ [Fid] 옵션', "'27/'28 LEAPS (초기 화력 80%)", [-2800000, -3600000, -8400000, -18800000], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Fidelity) 1/3', [-933333, -1200000, -2800000, -6266666], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Fidelity) 1/3', [-933333, -1200000, -2800000, -6266667], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Fidelity) 1/3', [-933334, -1200000, -2800000, -6266667], 'pl-indent-2'),
  ('└ [Moo] 옵션', "'27/'28 LEAPS (초기 화력 20%)", [-700000, -900000, -2100000, -4700000], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Moomoo) 1/3', [-233333, -300000, -700000, -1566666], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Moomoo) 1/3', [-233333, -300000, -700000, -1566667], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Moomoo) 1/3', [-233334, -300000, -700000, -1566667], 'pl-indent-2')
]

st4_items = [
  ('└ GME Partial Sell', '180일 내 LEAPS/현물 부분 청산', [int(3500000*st4_mult), int(4000000*st4_mult), int(7500000*st4_mult), int(14000000*st4_mult)], 'bull', True),
  ('└ O&G (Energy)', 'IDC 100% 공제 (에너지 유정 WI)', [int(-1500000*st4_mult), int(-1500000*st4_mult), int(-3250000*st4_mult), int(-6000000*st4_mult)], '', False),
  ('└ QOF Housing', 'QOZ 다세대 주택 (10년 면세)', [int(-1500000*st4_mult), int(-1500000*st4_mult), int(-3250000*st4_mult), int(-6000000*st4_mult)], '', False),
  ('└ CLAT (Trust)', '자선 소득 신탁 (즉시 소득 공제)', [int(-500000*st4_mult), int(-1000000*st4_mult), int(-1000000*st4_mult), int(-2000000*st4_mult)], '', False)
]

with open('output_all.html', 'w', encoding='utf-8') as f:
    # ST 2
    f.write('<!-- ST 2 ITEMS -->\n')
    bal = list(st1_totals)
    
    st2_tot = [-577000, -577000, -577000, -577000]
    row = '                <tr class="st-main">\n                  <td>ST 2. 즉시 집행금</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Immediate Rewards)]</td>\n'
    for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(st2_tot[i]))}</td>\n'
    row += '                </tr>\n'
    f.write(row)
    
    for name, det, vals, cls in st2_items:
        row = f'                <tr class="st-sub">\n                  <td class="{cls}">{name}</td>\n                  <td class="det">{det}</td>\n'
        for i in range(4):
            bal[i] += vals[i]
            row += f'                  <td class="r neg">-{fmt(abs(vals[i]))}<br><span class="bal">BAL {fmt(bal[i])}</span></td>\n'
        row += '                </tr>\n'
        f.write(row)
        
    row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [현금 잔고]</td>\n                  <td class="det-cash">즉시 집행 후 유동 현금</td>\n'
    for i in range(4): row += f'                  <td class="r pos">{fmt(bal[i])}</td>\n'
    row += '                </tr>\n'
    f.write(row)

    # ST 3
    # GME Totals: 7000000, 8000000, 14000000, 27000000
    gme_tot = [-7000000, -8000000, -14000000, -27000000]
    row = '                <tr class="st-main">\n                  <td>ST 3. 초기 GME 투입</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Clean Millions Target)]</td>\n'
    for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(gme_tot[i]))}</td>\n'
    row += '                </tr>\n'
    f.write(row)
    
    for name, det, vals, cls in st3_items:
        if "옵션" in name and "LEAPS" in det:
            row = f'                <tr class="st-sub">\n                  <td class="pl-indent" style="color:var(--{cls});">{name}</td>\n                  <td class="det">{det}</td>\n'
            for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(vals[i]))}</td>\n'
            row += '                </tr>\n'
            f.write(row)
            continue
            
        td_cls = cls if "-2" in cls else "pl-indent"
        td_style = f'style="color:var(--{cls});"' if "accent" in cls else ""
        row = f'                <tr class="st-sub">\n                  <td class="{td_cls}" {td_style}>{name}</td>\n                  <td class="det">{det}</td>\n'
        for i in range(4):
            bal[i] += vals[i]
            row += f'                  <td class="r neg">-{fmt(abs(vals[i]))}<br><span class="bal">BAL {fmt(bal[i])}</span></td>\n'
        row += '                </tr>\n'
        f.write(row)

    row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [현금 잔고]</td>\n                  <td class="det-cash">Reserve & 남은 여유 캐시</td>\n'
    for i in range(4): row += f'                  <td class="r pos">{fmt(bal[i])}</td>\n'
    row += '                </tr>\n'
    f.write(row)
    
    # ST 4
    st4_tot = [int(-3500000*st4_mult), int(-4000000*st4_mult), int(-7500000*st4_mult), int(-14000000*st4_mult)]
    row = '                <tr class="st-main">\n                  <td>ST 4. 절세 제국 스케일업</td>\n                  <td style="color:var(--textD)">[SECTION TOTAL (Includes GME STCG)]</td>\n'
    for i in range(4): row += f'                  <td class="r neg">-{fmt(abs(st4_tot[i]))}</td>\n'
    row += '                </tr>\n'
    f.write(row)
    
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
        f.write(row)
        
    row = '                <tr class="st-cash">\n                  <td class="pl-indent" style="color:var(--accent);">💵 [최종 현금 잔고]</td>\n                  <td class="det-cash">Tax Shield 방어 후 생존 Cash</td>\n'
    for i in range(4): row += f'                  <td class="r pos" style="color:var(--bull); font-weight:900;">{fmt(bal[i])}</td>\n'
    row += '                </tr>\n'
    f.write(row)
