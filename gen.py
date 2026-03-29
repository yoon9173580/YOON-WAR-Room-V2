def fmt(n): return f'${n:,}'

st2_items = [
  ('모빌리티 (본인)', 'Aston Martin / MC20 / Ferrari F430', [-800000, -800000, -800000, -800000]),
  ('모빌리티 (아빠)', 'BMW 740i', [-120000, -120000, -120000, -120000]),
  ('기프트 (아빠)', 'Omega Seamaster Diver 300M', [-22320, -22320, -22320, -22320]),
  ('기프트 (엄마)', 'Cartier Tank Louis & LV M27335', [-22548, -22548, -22548, -22548]),
  ('기프트 (진이)', 'Omega Aqua Terra & Dior Bag', [-13920, -13920, -13920, -13920]),
  ('Reserve & 여비 (통합)', '은행 Checking 현금 파킹 / 체류/여비', [-541692, -841692, -1541692, -2541692])
]

st3_items = [
  ('└ [DRS] 현물', 'GME 100,000주 집중 확보 (Infinity)', [-3500000, -3500000, -3500000, -3500000], 'accent'),
  ('└ [Fid] 옵션', "'27/'28 LEAPS (초기 화력 80%)", [-2947960, -3769194, -8415870, -18957802], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Fidelity) 1/3', [-982653, -1256398, -2805290, -6319267], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Fidelity) 1/3', [-982653, -1256398, -2805290, -6319267], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Fidelity) 1/3', [-982654, -1256398, -2805290, -6319268], 'pl-indent-2'),
  ('└ [Moo] 옵션', "'27/'28 LEAPS (초기 화력 20%)", [-736990, -942298, -2103968, -4739451], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Moomoo) 1/3', [-245663, -314099, -701323, -1579817], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Moomoo) 1/3', [-245663, -314099, -701323, -1579817], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Moomoo) 1/3', [-245664, -314100, -701322, -1579817], 'pl-indent-2')
]

st4_items = [
  ('└ GME Partial Sell', '180일 내 LEAPS/현물 부분 청산', [3500000, 4000000, 7500000, 14000000], 'bull', True),
  ('└ O&G (Energy)', 'IDC 100% 공제 (에너지 유정 WI)', [-1500000, -1500000, -3250000, -6000000], 'pl-indent', False),
  ('└ QOF Housing', 'QOZ 다세대 주택 (10년 면세)', [-1500000, -1500000, -3250000, -6000000], 'pl-indent', False),
  ('└ CLAT (Trust)', '자선 소득 신탁 (즉시 소득 공제)', [-500000, -1000000, -1000000, -2000000], 'pl-indent', False)
]

with open('output.html', 'w', encoding='utf-8') as f:
    bal = [8705430, 10031972, 16540318, 30717733]

    f.write('<!-- ST 2 ITEMS -->\n')
    for name, det, vals in st2_items:
        row = "                <tr class=\"st-sub\">\n                  <td class=\"pl-indent\">└ " + name + "</td>\n                  <td class=\"det\">" + det + "</td>\n"
        for i in range(4):
            bal[i] += vals[i]
            row += "                  <td class=\"r neg\">-" + fmt(abs(vals[i])) + "<br><span class=\"bal\">BAL " + fmt(bal[i]) + "</span></td>\n"
        row += "                </tr>\n"
        f.write(row)

    f.write('<!-- ST 3 ITEMS -->\n')
    bal = [7184950, 8211492, 14019838, 27197253]
    for name, det, vals, cls in st3_items:
        if "옵션" in name:
            row = "                <tr class=\"st-sub\">\n                  <td class=\"pl-indent\" style=\"color:var(--" + cls + ");\">" + name + "</td>\n                  <td class=\"det\">" + det + "</td>\n"
            for i in range(4):
                row += "                  <td class=\"r neg\">-" + fmt(abs(vals[i])) + "</td>\n"
            row += "                </tr>\n"
            f.write(row)
            continue

        td_cls = cls if "-2" in cls else "pl-indent"
        td_style = "style=\"color:var(--" + cls + ");\"" if "accent" in cls else ""
        row = "                <tr class=\"st-sub\">\n                  <td class=\"" + td_cls + "\" " + td_style + ">" + name + "</td>\n                  <td class=\"det\">" + det + "</td>\n"
        for i in range(4):
            bal[i] += vals[i]
            row += "                  <td class=\"r neg\">-" + fmt(abs(vals[i])) + "<br><span class=\"bal\">BAL " + fmt(bal[i]) + "</span></td>\n"
        row += "                </tr>\n"
        f.write(row)

    f.write('<!-- ST 4 ITEMS -->\n')
    bal = [0,0,0,0]
    for name, det, vals, cls, ispos in st4_items:
        c = "bull" if ispos else "neg"
        sym = "+" if ispos else "-"
        td_cls = cls if "bull" not in cls else "pl-indent"
        td_style = "style=\"color:var(--" + cls + ");\"" if "bull" in cls else ""
        row = "                <tr class=\"st-sub\">\n                  <td class=\"" + td_cls + "\" " + td_style + ">" + name + "</td>\n                  <td class=\"det\">" + det + "</td>\n"
        for i in range(4):
            bal[i] += vals[i]
            row += "                  <td class=\"r " + c + "\">" + sym + fmt(abs(vals[i])) + "<br><span class=\"bal\">BAL " + fmt(bal[i]) + "</span></td>\n"
        row += "                </tr>\n"
        f.write(row)
