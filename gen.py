def fmt(n): return f'${n:,}'

st3_items = [
  ('└ [DRS] 현물', 'GME 70,000주 확보 (Infinity)', [-2450000, -2450000, -2450000, -2450000], 'accent'),
  ('└ [Fid] 현물', 'GME 20,000주 확보 (Main)', [-700000, -700000, -700000, -700000], 'accent'),
  ('└ [Moo] 현물', 'GME 10,000주 확보 (Tactical)', [-350000, -350000, -350000, -350000], 'accent'),
  ('└ [Fid] 옵션', "'27/'28 LEAPS (초기 화력 80%)", [-2947960, -3769194, -8415870, -18957802], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Fidelity) 1/3', [-982653, -1256398, -2805290, -6319267], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Fidelity) 1/3', [-982653, -1256398, -2805290, -6319267], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Fidelity) 1/3', [-982654, -1256398, -2805290, -6319268], 'pl-indent-2'),
  ('└ [Moo] 옵션', "'27/'28 LEAPS (초기 화력 20%)", [-736990, -942298, -2103968, -4739451], 'purple'),
  ('├ Strike $40', 'LEAPS Call (Moomoo) 1/3', [-245663, -314099, -701323, -1579817], 'pl-indent-2'),
  ('├ Strike $45', 'LEAPS Call (Moomoo) 1/3', [-245663, -314099, -701323, -1579817], 'pl-indent-2'),
  ('└ Strike $50', 'LEAPS Call (Moomoo) 1/3', [-245664, -314100, -701322, -1579817], 'pl-indent-2')
]

with open('output3.html', 'w', encoding='utf-8') as f:
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
