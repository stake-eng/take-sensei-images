"""
図解画像をつくる（1080×1350のPNG）。
  python zukai/build.py            → zukai/png/*.png を全部つくり直す
たけ先生のイラストは zukai/sensei.png があればそれを使い、なければ簡単な線画を使います。
"""
import base64, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
OUT = BASE / "png"
SPEC = json.loads((BASE / "zukai.json").read_text(encoding="utf-8"))

MASCOT_SVG = """<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg">
<path d="M18 140 Q18 98 60 96 Q102 98 102 140 Z" fill="#2E3A59"/>
<path d="M48 97 L60 118 L72 97 Z" fill="#fff"/>
<circle cx="60" cy="58" r="36" fill="#F6D7B8"/>
<path d="M24 54 Q26 18 60 20 Q94 18 96 54 Q88 36 70 38 Q56 30 40 40 Q30 42 24 54 Z" fill="#3B2F2A"/>
<circle cx="46" cy="60" r="9" fill="none" stroke="#3B2F2A" stroke-width="3"/>
<circle cx="74" cy="60" r="9" fill="none" stroke="#3B2F2A" stroke-width="3"/>
<line x1="55" y1="60" x2="65" y2="60" stroke="#3B2F2A" stroke-width="3"/>
<circle cx="46" cy="61" r="2.6" fill="#3B2F2A"/><circle cx="74" cy="61" r="2.6" fill="#3B2F2A"/>
<path d="M50 78 Q60 86 70 78" fill="none" stroke="#B5543C" stroke-width="3" stroke-linecap="round"/>
<circle cx="38" cy="72" r="5" fill="#F2B49B" opacity=".7"/><circle cx="82" cy="72" r="5" fill="#F2B49B" opacity=".7"/>
</svg>"""


def mascot() -> str:
    p = BASE / "sensei.png"
    if p.exists():
        return f'<img src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}">'
    return MASCOT_SVG


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1350px;font-family:'Noto Sans CJK JP','Noto Sans JP',sans-serif;
 background:#FBF7EF;color:#2B2B2B;position:relative;overflow:hidden}
.head{background:#2E3A59;color:#fff;padding:54px 64px 46px;border-bottom:10px solid #C8963E}
.kicker{font-size:32px;font-weight:700;color:#F3D9A6;letter-spacing:.04em}
.title{font-size:66px;font-weight:900;line-height:1.22;margin-top:12px}
.title em{font-style:normal;color:#F7C873}
.body{padding:40px 56px 0}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
.card{background:#fff;border:3px solid #E9DFCC;border-radius:22px;padding:20px 20px 18px;min-height:250px}
.card .h{display:flex;align-items:baseline;gap:10px;border-bottom:3px dotted #E9DFCC;padding-bottom:10px;margin-bottom:12px}
.card .n{font-size:44px;font-weight:900;color:#2E3A59}
.card .y{font-size:22px;color:#8A7A60;font-weight:700}
.card .t{font-size:27px;font-weight:700;line-height:1.45}
.card .s{font-size:23px;color:#5A5A5A;line-height:1.5;margin-top:8px}
.list{display:flex;flex-direction:column;gap:16px}
.row{display:flex;align-items:center;gap:22px;background:#fff;border:3px solid #E9DFCC;border-radius:22px;padding:18px 26px}
.row .no{flex:0 0 66px;height:66px;border-radius:50%;background:#E07A5F;color:#fff;font-size:34px;font-weight:900;display:flex;align-items:center;justify-content:center}
.row .big{flex:0 0 150px;font-size:46px;font-weight:900;color:#2E3A59;line-height:1.1}
.row .big small{font-size:26px}
.row .txt{font-size:30px;font-weight:700;line-height:1.4}
.row .txt span{display:block;font-size:24px;font-weight:400;color:#5A5A5A;margin-top:4px}
.steps .row .no{background:#2E3A59}
.dense .list{gap:10px}.dense .row{padding:10px 24px}.dense .row .no{flex-basis:54px;height:54px;font-size:28px}.dense .row .txt{font-size:28px}.dense .row .txt span{font-size:22px}.dense .row .big{font-size:40px}.dense .head{padding:44px 64px 36px}.dense .title{font-size:58px}.dense .card{min-height:0;padding:16px 18px}.dense .grid{gap:14px}
.foot{position:absolute;left:0;right:0;bottom:0;height:210px;display:flex;align-items:flex-end;padding:0 56px 34px;gap:24px}
.mascot{width:150px;height:175px;flex:0 0 150px}
.mascot svg,.mascot img{width:100%;height:100%;object-fit:contain}
.msg{flex:1;background:#fff;border:4px solid #C8963E;border-radius:26px;padding:22px 30px;font-size:34px;font-weight:900;line-height:1.4;margin-bottom:18px}
.msg em{font-style:normal;color:#E07A5F}
.sign{position:absolute;right:56px;bottom:14px;font-size:22px;color:#8A7A60;font-weight:700}
"""


def render(z: dict) -> str:
    if z["layout"] == "grid9":
        inner = '<div class="grid">' + "".join(
            f'<div class="card"><div class="h"><span class="n">{c["name"]}</span><span class="y">{c.get("sub","")}</span></div>'
            f'<div class="t">{c["t"]}</div>' + (f'<div class="s">{c["s"]}</div>' if c.get("s") else "") + "</div>"
            for c in z["items"]) + "</div>"
    else:
        cls = "list steps" if z["layout"] == "steps" else "list"
        rows = []
        for i, c in enumerate(z["items"], 1):
            big = f'<div class="big">{c["big"]}</div>' if c.get("big") else ""
            sub = f'<span>{c["s"]}</span>' if c.get("s") else ""
            rows.append(f'<div class="row"><div class="no">{i}</div>{big}<div class="txt">{c["t"]}{sub}</div></div>')
        inner = f'<div class="{cls}">' + "".join(rows) + "</div>"
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body class="{'dense' if z.get('dense') else ''}">
<div class="head"><div class="kicker">{z['kicker']}</div><div class="title">{z['title']}</div></div>
<div class="body">{inner}</div>
<div class="foot"><div class="mascot">{mascot()}</div><div class="msg">{z['msg']}</div></div>
<div class="sign">たけ先生 ｜ @take_sen.sei</div></body></html>"""


def main(keys):
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for z in SPEC:
            if keys and z["key"] not in keys:
                continue
            pg.set_content(render(z))
            pg.wait_for_timeout(200)
            over = pg.evaluate("document.querySelector('.body').getBoundingClientRect().bottom")
            if over > 1350 - 210:
                print(f"[注意] {z['key']} の中身が下の吹き出しに重なっています（{int(over)}px）")
            pg.screenshot(path=str(OUT / f"{z['key']}.png"))
            print("OK", z["key"])
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:])
