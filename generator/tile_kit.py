# -*- coding: utf-8 -*-
"""
Reusable DEWALT PDP-asset page generator.

This module is the packaged, reusable version of the one-off scripts used to
build the first page (DWST60436): the same visual system (brand colors,
Archivo Expanded Black / Work Sans, yellow-bar tile system, hero/foot bands,
lightbox export, briefing + notes, base/suggested panels) but parameterized
so a new SKU's page can be built by calling these functions with real,
freshly-researched content instead of hand-authoring a new script each time.

Nothing in here does research (no web search/fetch) -- that part requires
judgment (which photo is the hero shot, what the technical/marketing brief
says, whether a comparative claim has real data or must be flagged pending)
and is expected to be done by whoever calls this module (an agent with
WebSearch/WebFetch, doing the same process used for DWST60436).

Usage sketch (see GENERATOR_GUIDE.md for the full step-by-step process):

    from tile_kit import *

    tile1 = tile(bg_img(hero_b64, "dw-bg-contain"), field="white", id="tile1")
    row1 = spec_row(1, "Hero Shot", "2000x2000 - JPG", "...", badge("ok","Pronto"),
                     "tile1", tile1, tech="...", mkt="...", single=True,
                     filename_stub="HeroShot")
    ...
    html = render_page(sku="XYZ123", product_name="...", meta_chips=[...],
                        rows_html=[row1, row2, ...], ep_rows_html=[...])
    open("../pages/xyz123.html", "w", encoding="utf-8").write(html)
"""
import base64
import html as htmlmod
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(HERE, "fonts")
INSPIRATION_DIR = os.path.join(HERE, "inspiration")

DW_YELLOW = "#FEBD17"
DW_BLACK = "#231E20"
DW_OFFWHITE = "#FCF5DE"


def _font_b64(fname, mime="font/woff2"):
    with open(os.path.join(FONTS_DIR, fname), "rb") as f:
        data = f.read()
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


FONT_ARCHIVO_B64 = _font_b64("archivo_black_expanded.woff2")
FONT_WORKSANS_B64 = _font_b64("worksans_variable.woff2")


def image_to_b64_jpeg(path, max_dim=1500, quality=84, bg=(255, 255, 255)):
    """Resize/compress an image file (any Pillow-readable format, incl. webp)
    to a base64 JPEG data URI. Use for every downloaded product photo before
    embedding it in a tile -- keeps the final page a reasonable size."""
    from PIL import Image
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        canvas = Image.new("RGB", im.size, bg)
        canvas.paste(im, mask=im.split()[-1])
        im = canvas
    else:
        im = im.convert("RGB")
    w, h = im.size
    scale = max_dim / max(w, h)
    if scale < 1:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def esc(s):
    return htmlmod.escape(s, quote=True)


# ---------------------------------------------------------------------------
# Inspiration references -- real DEWALT (mostly) ad examples that show the
# STYLE each asset type should aim for. These are fixed, generic style
# references (not this SKU's own content), reused across every generated
# page for the matching asset type. Do not research/replace these per-SKU.
# ---------------------------------------------------------------------------
INSPIRATION_MAP = {
    "hero": ("hero.jpg", "Referência de estilo: still de produto limpo em fundo branco."),
    "kit": ("kit.jpg", "Referência de estilo: grade \"o que vem na caixa\" com cada item rotulado."),
    "diferenciais_infografico": ("diferenciais_infografico.jpg", "Referência de estilo: diagrama com múltiplos recursos indicados no próprio produto."),
    "familia": ("familia.jpg", "Referência de estilo: lockup oficial de sub-linha/família."),
    "diferencial_tecnico_1": ("diferencial_tecnico_1.jpg", "Referência de estilo: foto real de uso + estatística em destaque."),
    "diferencial_tecnico_2": ("diferencial_tecnico_2.jpg", "Referência de estilo: comparação de peso/tamanho com estatística em destaque."),
    "diferencial_tecnico_3": ("diferencial_tecnico_3.jpg", "Referência de estilo: foto de aplicação real + benefício em destaque."),
    "comparativo_tecnico": ("comparativo_tecnico.jpg", "Referência de estilo: comparação direta com concorrente sem citar a marca (silhueta/cor genérica)."),
    "comparativo_diferenciadores": ("comparativo_diferenciadores.jpg", "Referência de estilo: comparação interna entre modelos da própria linha."),
    "aplicacao_1": ("aplicacao_1.jpg", "Referência de estilo: uso real em obra, sem encenação de estúdio."),
    "aplicacao_2": ("aplicacao_2.jpg", "Referência de estilo: uso real com texto/benefício sobreposto."),
    "linha_compativel": ("linha_compativel.jpg", "Referência de estilo: vitrine de todo o sistema/linha de produtos."),
}


def inspiration_image_b64(key):
    fname, _ = INSPIRATION_MAP[key]
    path = os.path.join(INSPIRATION_DIR, fname)
    with open(path, "rb") as f:
        data = f.read()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")


def inspiration_panel(key, wide=False):
    """key: one of INSPIRATION_MAP's keys. Renders the fixed reference image
    for that asset type as a third stage panel, alongside base/sugerido."""
    _, caption = INSPIRATION_MAP[key]
    frame_cls = "base-frame wide" if wide else "base-frame"
    img_uri = inspiration_image_b64(key)
    frame = f'<div class="stage-frame {frame_cls}"><img class="base-photo" src="{img_uri}" alt="Imagem de inspiracao" /></div>'
    cap = f'<div class="save-hint">{esc(caption)}</div>'
    return f'''<div class="stage-panel">
      <div class="panel-label">Inspiração DEWALT (referência de estilo)</div>
      {frame}
      {cap}
    </div>'''


# ---------------------------------------------------------------------------
# Tile building blocks (one "asset" = one .dw-tile, either square 1:1 or the
# wide 1200:628 enriched-page layout). These mirror the DWST60436 page 1:1 --
# do not change the CSS class names/behavior here without also updating
# BASE_CSS below, they're tightly coupled.
# ---------------------------------------------------------------------------

def bar(pos, with_logo=False):
    logo = '<span class="tile-logo">DEWALT</span>' if with_logo else ""
    return f'<div class="dw-bar dw-bar-{pos}">{logo}</div>'


def headline(l1, l2, pos="bl", size="md"):
    return (f'<div class="dw-headline dw-headline-{pos} dw-headline-{size}">'
            f'<span class="l1">{esc(l1)}</span><span class="l2">{esc(l2)}</span></div>')


def scrim(pos="bottom"):
    return f'<div class="dw-scrim dw-scrim-{pos}"></div>'


def bg_img(data_uri, extra=""):
    """data_uri: a data:image/...;base64,... string, e.g. from image_to_b64_jpeg()."""
    return f'<img class="dw-bg {extra}" src="{data_uri}" alt="" />'


def badge_stack(items, pos="right"):
    lis = "".join(
        f'<div class="dw-badge"><span class="dw-badge-sku">{esc(sku)}</span>'
        f'<span class="dw-badge-txt">{esc(txt)}</span></div>' for sku, txt in items
    )
    return f'<div class="dw-badgestack dw-badgestack-{pos}">{lis}</div>'


def chip_list(items):
    """items: list of (number_or_check, text) tuples."""
    lis = "".join(
        f'<div class="dw-chip"><span class="dw-chip-n">{n}</span><span class="dw-chip-t">{esc(t)}</span></div>'
        for n, t in items
    )
    return f'<div class="dw-chiplist">{lis}</div>'


def compare_table(rows, cols):
    """Flexible comparison table -- supports 2 to 4 value columns (e.g. one
    or two competitors/sibling SKUs plus the current SKU).

    cols: ordered list of column header labels, 2-4 items. The LAST column
    is always the highlighted one (yellow) -- put the current SKU/DEWALT
    there.
    rows: list of tuples (label, value_for_col0, value_for_col1, ...),
    each with len(cols) values after the label.
    """
    n = len(cols)
    grid = f"1.15fr repeat({n}, 1fr)"

    def cells(values):
        out = ""
        for i, v in enumerate(values):
            cls = "cmp-val cmp-highlight" if i == n - 1 else "cmp-val"
            out += f'<div class="{cls}">{esc(v)}</div>'
        return out

    head = (f'<div class="cmp-row cmp-head" style="grid-template-columns:{grid}">'
            f'<div class="cmp-label"></div>{cells(cols)}</div>')
    body = "".join(
        f'<div class="cmp-row" style="grid-template-columns:{grid}">'
        f'<div class="cmp-label">{esc(r[0])}</div>{cells(r[1:])}</div>'
        for r in rows
    )
    return f'<div class="dw-compare">{head}{body}</div>'


def pending_ribbon(text):
    return f'<div class="dw-pending-ribbon">{esc(text)}</div>'


def eyebrow(text):
    return f'<div class="dw-eyebrow">{esc(text)}</div>'


def tag(text):
    return f'<div class="dw-tag">{esc(text)}</div>'


def tile(inner, extra_class="", field="white", id=""):
    idattr = f' id="{id}"' if id else ""
    return f'<div{idattr} class="dw-tile dw-field-{field} {extra_class}">{inner}</div>'


def wide_tile(inner, extra_class="", id=""):
    idattr = f' id="{id}"' if id else ""
    return f'<div{idattr} class="dw-tile dw-tile-wide {extra_class}">{inner}</div>'


def ep_media(bg_html, field=None):
    cls = f"ep-media dw-field-{field}" if field else "ep-media"
    return f'<div class="{cls}">{bg_html}</div>'


def ep_copy(kicker, heading, chips_html, field=None):
    cls = f"ep-copy dw-field-{field}" if field else "ep-copy"
    return (f'<div class="{cls}"><div class="ep-kicker">{esc(kicker)}</div>'
            f'<div class="ep-h">{esc(heading)}</div>{chips_html}</div>')


# ---------------------------------------------------------------------------
# Spec-row: the meta panel (name/format/instruction/status/brief/notes) +
# base-image / suggested-asset stage, exactly as built for DWST60436.
# ---------------------------------------------------------------------------

def badge(kind, label):
    """kind: 'ok' | 'info' | 'warn' | 'crit'."""
    return f'<span class="badge {kind}">{label}</span>'


def _stage_panel(label, frame_html, dl_html):
    return f'''<div class="stage-panel">
      <div class="panel-label">{label}</div>
      <div class="stage-frame">{frame_html}</div>
      {dl_html}
    </div>'''


def base_panel(tile_id, wide=False, note=None):
    """tile_id: the id="" of the .dw-tile whose img.dw-bg should be mirrored
    here as the raw, unedited source photo. note: pass a short string instead
    (e.g. 'Sem imagem-base -- asset informativo, sem fotografia.') for tiles
    with no real photo (pure black-field / informational assets)."""
    if note:
        cls = "placeholder-box wide" if wide else "placeholder-box"
        return _stage_panel("Imagem-base", f'<div class="{cls}">{note}</div>', "")
    frame_cls = "base-frame wide" if wide else "base-frame"
    frame = f'<div class="stage-frame {frame_cls}"><img class="base-photo" data-src-from="{tile_id}" alt="Foto original, sem edicao" /></div>'
    view_btn = (f'<button class="dl-btn cta dl-base-view" data-view-from="{tile_id}">'
                f'<span class="ic">&#8681;</span> Ver / salvar imagem-base</button>')
    hint = '<div class="save-hint">Abre numa janela grande, salve com botão direito &rarr; "Salvar imagem como...".</div>'
    return f'''<div class="stage-panel">
      <div class="panel-label">Imagem-base (sem edição)</div>
      {frame}
      {view_btn}
      {hint}
    </div>'''


def export_panel(tile_id, tile_html, w, h, filename, label="Asset sugerido"):
    dl = (f'<button class="dl-btn cta dl-export" data-export-id="{tile_id}" data-w="{w}" data-h="{h}" '
          f'data-filename="{filename}"><span class="ic">&#8681;</span> Gerar imagem para salvar ({w}x{h})</button>')
    hint = '<div class="save-hint">Abre numa janela com a imagem pronta, salve com botão direito &rarr; "Salvar imagem como...".</div>'
    return _stage_panel(label, tile_html, dl + hint)


def brief_notes_block(asset_id, tech, mkt):
    """tech/mkt: short paragraphs -- the *specific* technical and marketing
    reasoning for THIS asset's photo/layout choice. Never generic filler --
    see GENERATOR_GUIDE.md for the standard this has to meet."""
    return f'''<div class="brief">
      <div class="brief-item"><b>Por que essa foto/layout (técnico)</b><p>{tech}</p></div>
      <div class="brief-item"><b>Por que essa abordagem (marketing)</b><p>{mkt}</p></div>
      <div class="notes-block">
        <label class="notes-label" for="notes-{asset_id}">Comentário da equipe</label>
        <textarea class="notes-area" id="notes-{asset_id}" data-note-id="{asset_id}" placeholder="Deixe um comentário sobre esta peça..."></textarea>
        <div class="notes-status" data-note-status="{asset_id}"></div>
      </div>
    </div>'''


def spec_row(n, name, fmt, instr, status_badge_html, tile_id, tile_html, tech, mkt,
             w=2000, h=2000, wide=False, flag=None, base_tile_id=None, base_note=None,
             single=False, filename_stub="", sku="", inspiration=None):
    """Builds one full asset row: meta panel (name/format/instruction/status/
    flag/briefing/notes) + stage (base-image panel + suggested-asset panel,
    or a single panel when single=True for assets with zero added text/
    editing, like Hero Shot or an untouched official Family asset).

    inspiration: a key from INSPIRATION_MAP, or None. When given, a third
    panel with the fixed real-DEWALT style reference is shown alongside
    base/sugerido."""
    flag_html = f'<div class="flag">{flag}</div>' if flag else ""
    cap = f"{w} x {h} px · JPG" if not wide else f"{w} x {h} px · JPG (módulo enriquecido, confirmar spec do marketplace)"
    export_fn = f"{sku}_{n:02d}_{filename_stub}.jpg" if sku else f"{n:02d}_{filename_stub}.jpg"
    asset_id = f"asset-{n:02d}"

    if single:
        panels = export_panel(tile_id, tile_html, w, h, export_fn, label="Asset (idêntico ao original oficial)")
        panels_cls = "stage-panels single"
        if inspiration:
            panels += inspiration_panel(inspiration, wide=wide)
            panels_cls = "stage-panels"  # no longer "single" -- now 2 columns (sugerido + inspiracao)
    else:
        left = base_panel(base_tile_id or tile_id, wide=wide, note=base_note)
        right = export_panel(tile_id, tile_html, w, h, export_fn)
        panels = left + right
        panels_cls = "stage-panels"
        if inspiration:
            panels += inspiration_panel(inspiration, wide=wide)
            panels_cls += " with-inspiration"

    return f"""
<div class="spec-row">
  <div class="meta">
    <div class="num">Asset {n:02d}</div>
    <h3>{esc(name)}</h3>
    <div class="fmt">{esc(fmt)}</div>
    <div class="instr"><i>Instrução:</i> {instr}</div>
    {flag_html}
    {status_badge_html}
    {brief_notes_block(asset_id, tech, mkt)}
  </div>
  <div class="stage">
    <div class="{panels_cls}">{panels}</div>
    <div class="stage-cap">{cap}</div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Full-page CSS (hero/foot bands, cards, tile system, lightbox) -- identical
# design language to dwst60436.html. Edit with care: the export pipeline
# clones a .dw-tile and re-injects this exact CSS into an SVG foreignObject,
# so class names here must stay in sync with the functions above.
# ---------------------------------------------------------------------------
BASE_CSS = """
@font-face {
  font-family: 'Archivo Expanded Black';
  font-style: normal; font-weight: 900;
  src: url('""" + FONT_ARCHIVO_B64 + """') format('woff2');
}
@font-face {
  font-family: 'Work Sans';
  font-style: normal; font-weight: 100 900;
  src: url('""" + FONT_WORKSANS_B64 + """') format('woff2');
}

:root{
  --bg:#F4F2ED; --surface:#FFFFFF; --surface-2:#FBFAF7; --text:#201F1C; --text-dim:#6B685F; --border:#E3DFD4;
  --accent:#8C5A16; --accent-soft:#F1E4CE;
  --ok:#2E6B40; --ok-soft:#E4F0E3; --warn:#8A5A0F; --warn-soft:#F5E9D2; --crit:#9A2E1F; --crit-soft:#F7E0DA; --info:#2C567E; --info-soft:#E2ECF3;
  --dw-yellow:#FEBD17; --dw-black:#231E20; --dw-offwhite:#FCF5DE;
  --radius:14px;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#17181A; --surface:#1E2023; --surface-2:#232528; --text:#ECE8E0; --text-dim:#9E9A90; --border:#34363A;
    --accent:#D9A54E; --accent-soft:#3A2E17;
    --ok:#5FBE79; --ok-soft:#1E2E20; --warn:#E0A83E; --warn-soft:#332711; --crit:#E5695A; --crit-soft:#3A211C; --info:#79B0DE; --info-soft:#1D2A35;
  }
}
:root[data-theme="dark"]{
  --bg:#17181A; --surface:#1E2023; --surface-2:#232528; --text:#ECE8E0; --text-dim:#9E9A90; --border:#34363A;
  --accent:#D9A54E; --accent-soft:#3A2E17;
  --ok:#5FBE79; --ok-soft:#1E2E20; --warn:#E0A83E; --warn-soft:#332711; --crit:#E5695A; --crit-soft:#3A211C; --info:#79B0DE; --info-soft:#1D2A35;
}
:root[data-theme="light"]{
  --bg:#F4F2ED; --surface:#FFFFFF; --surface-2:#FBFAF7; --text:#201F1C; --text-dim:#6B685F; --border:#E3DFD4;
  --accent:#8C5A16; --accent-soft:#F1E4CE;
  --ok:#2E6B40; --ok-soft:#E4F0E3; --warn:#8A5A0F; --warn-soft:#F5E9D2; --crit:#9A2E1F; --crit-soft:#F7E0DA; --info:#2C567E; --info-soft:#E2ECF3;
}

*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{
  background:var(--bg); color:var(--text);
  font-family:'Work Sans', system-ui, sans-serif;
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1280px; margin:0 auto; padding:48px 28px 70px;}

.hero-band{ background:var(--dw-black); color:#fff; border-bottom:6px solid var(--dw-yellow); }
.hero-inner{ max-width:1280px; margin:0 auto; padding:40px 28px 34px; display:flex; flex-direction:column; gap:16px; }
.masthead{display:flex; flex-direction:column; gap:16px;}
.masthead .eyebrow{
  display:inline-flex; align-items:center; gap:8px; width:fit-content;
  background:var(--dw-yellow); color:var(--dw-black); font-family:'Archivo Expanded Black'; font-weight:900;
  font-size:11px; letter-spacing:.08em; text-transform:uppercase; padding:6px 12px; border-radius:2px;
}
.masthead h1{
  font-family:'Archivo Expanded Black'; font-weight:900; text-transform:uppercase; letter-spacing:-0.01em;
  line-height:.94; font-size:clamp(28px,4.2vw,46px); margin:0; text-wrap:balance;
}
.masthead h1 .accent{ color:var(--dw-yellow); }
.masthead .sub{color:#C7C3BB; font-size:15.5px; max-width:64ch;}
.sku-row{
  display:flex; flex-wrap:wrap; align-items:flex-end; gap:18px 30px; margin-top:4px; padding-top:18px; border-top:1px solid rgba(255,255,255,.16);
}
.sku-item{display:flex; flex-direction:column; gap:2px;}
.sku-item .k{font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:#948F86;}
.sku-item .v{font-size:15px; font-weight:600; font-variant-numeric:tabular-nums; color:#fff;}

.intro{
  margin:34px 0 6px; padding:18px 20px; background:var(--surface-2); border:1px solid var(--border);
  border-radius:var(--radius); color:var(--text-dim); font-size:14.5px; max-width:none;
}
.intro b{color:var(--text); font-weight:600;}

.section-label{ margin:52px 0 20px; display:flex; align-items:center; gap:12px; }
.section-label .tag{ width:9px; height:9px; background:var(--dw-yellow); flex:none; }
.section-label h2{
  font-family:'Archivo Expanded Black'; font-weight:900; font-size:14.5px; letter-spacing:.05em;
  text-transform:uppercase; color:var(--text); margin:0;
}
.section-label .line{flex:1; height:2px; background:var(--dw-yellow); opacity:.4;}

.spec-row{
  display:grid; grid-template-columns: 300px 1fr; gap:28px;
  background:var(--surface); border:1px solid var(--border); border-radius:14px;
  padding:26px; margin-bottom:20px; box-shadow:0 1px 2px rgba(0,0,0,.04);
}
@media (max-width:860px){ .spec-row{grid-template-columns:1fr;} }

.meta{display:flex; flex-direction:column; gap:14px;}
.meta .num{font-size:13px; color:var(--text-dim); font-variant-numeric:tabular-nums; letter-spacing:.06em;}
.meta h3{font-size:19px; margin:0; font-weight:700; letter-spacing:-0.005em;}
.meta .fmt{font-size:13px; color:var(--text-dim); font-variant-numeric:tabular-nums;}
.meta .instr{font-size:13.5px; color:var(--text-dim); border-left:2px solid var(--border); padding-left:10px;}
.meta .instr i{color:var(--text); font-style:normal; font-weight:500;}
.meta .flag{font-size:12.5px; color:var(--warn); background:var(--warn-soft); padding:6px 9px; border-radius:8px; display:inline-block; width:fit-content;}

.brief{ display:flex; flex-direction:column; gap:12px; margin-top:6px; padding-top:16px; border-top:1px dashed var(--border); }
.brief-item b{ display:block; font-size:10.5px; text-transform:uppercase; letter-spacing:.08em; color:var(--accent); margin-bottom:3px; }
.brief-item p{ margin:0; font-size:13px; color:var(--text-dim); line-height:1.5; }
.notes-block{ margin-top:2px; }
.notes-label{ display:block; font-size:10.5px; text-transform:uppercase; letter-spacing:.08em; color:var(--text-dim); margin-bottom:6px; }
.notes-area{
  width:100%; min-height:64px; padding:9px 11px; border:1px solid var(--border); border-radius:8px;
  background:var(--surface); color:var(--text); font-family:inherit; font-size:13px; resize:vertical; line-height:1.4;
}
.notes-area:focus-visible{ outline:2px solid var(--accent); outline-offset:1px; }
.notes-status{ font-size:11px; color:var(--text-dim); margin-top:4px; min-height:14px; }

.badge{
  display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:700; text-transform:uppercase;
  letter-spacing:.06em; padding:5px 10px; border-radius:999px; width:fit-content;
}
.badge.ok{color:var(--ok); background:var(--ok-soft);}
.badge.info{color:var(--info); background:var(--info-soft);}
.badge.warn{color:var(--warn); background:var(--warn-soft);}
.badge.crit{color:var(--crit); background:var(--crit-soft);}
.badge::before{content:''; width:6px; height:6px; border-radius:50%; background:currentColor;}

.stage{ display:flex; flex-direction:column; gap:10px; }
.stage-panels{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.stage-panels.single{ grid-template-columns:1fr; max-width:480px; }
.stage-panels.with-inspiration{ grid-template-columns:1fr 1fr 1fr; }
@media (max-width:900px){ .stage-panels.with-inspiration{ grid-template-columns:1fr 1fr; } }
@media (max-width:600px){ .stage-panels{grid-template-columns:1fr;} }

.stage-panel{ display:flex; flex-direction:column; gap:9px; min-width:0; }
.panel-label{ font-size:11px; text-transform:uppercase; letter-spacing:.08em; color:var(--text-dim); font-weight:700; }

.stage-frame{
  width:100%; border-radius:10px; overflow:hidden; box-shadow:0 1px 2px rgba(0,0,0,.06), 0 12px 32px -16px rgba(0,0,0,.35);
  border:1px solid var(--border); background:var(--surface-2);
}
.stage-frame.base-frame{ aspect-ratio:1/1; display:flex; align-items:center; justify-content:center; }
.stage-frame.base-frame.wide{ aspect-ratio:1200/628; }
.base-photo{ width:100%; height:100%; object-fit:contain; display:block; }
.placeholder-box{
  width:100%; aspect-ratio:1/1; display:flex; align-items:center; justify-content:center; text-align:center;
  padding:18px; color:var(--text-dim); font-size:12.5px; box-sizing:border-box;
}
.placeholder-box.wide{ aspect-ratio:1200/628; }

.dl-btn{
  display:inline-flex; align-items:center; gap:7px; font-size:12.5px; font-weight:600; padding:9px 13px; border-radius:8px;
  border:1px solid var(--border); background:var(--surface); color:var(--text); cursor:pointer; text-decoration:none;
  width:fit-content; font-family:inherit;
}
.dl-btn:hover{ border-color:var(--accent); color:var(--accent); }
.dl-btn:focus-visible{ outline:2px solid var(--dw-yellow); outline-offset:2px; }
.dl-btn .ic{ font-size:14px; line-height:1; }
.dl-btn.busy{ opacity:.6; pointer-events:none; }
.dl-btn.cta{
  background:var(--dw-yellow); border:none; color:var(--dw-black); font-weight:800;
  text-transform:uppercase; letter-spacing:.03em; font-size:12px;
}
.dl-btn.cta:hover{ background:#FFCB3D; color:var(--dw-black); }

.save-hint{ font-size:11.5px; color:var(--text-dim); }

.stage-cap{font-size:12px; color:var(--text-dim); font-variant-numeric:tabular-nums;}

.lightbox-overlay{
  position:fixed; inset:0; background:rgba(12,12,13,.86); z-index:1000; padding:28px;
  display:none; align-items:center; justify-content:center; flex-direction:column; gap:16px;
}
.lightbox-overlay.open{ display:flex; }
.lightbox-img{ max-width:92vw; max-height:74vh; border-radius:6px; box-shadow:0 24px 64px rgba(0,0,0,.5); background:#fff; }
.lightbox-hint{ color:#fff; font-size:14px; text-align:center; max-width:56ch; }
.lightbox-hint b{ color:var(--dw-yellow); }
.lightbox-close{
  position:absolute; top:22px; right:26px; background:rgba(255,255,255,.12); color:#fff;
  border:1px solid rgba(255,255,255,.32); border-radius:8px; padding:8px 15px; font-size:13px; cursor:pointer; font-family:inherit;
}
.lightbox-close:hover{ background:rgba(255,255,255,.22); }

/* ============ DEWALT TILE SYSTEM (fixed brand world, not theme-aware) ============ */
.dw-tile{
  position:relative; width:100%; aspect-ratio:1/1; overflow:hidden;
  font-family:'Work Sans', sans-serif;
  container-type: inline-size; container-name: dwtile;
}
.dw-tile-wide{ aspect-ratio: 1200/628; }
.dw-field-white .dw-bg{ background:#fff; }
.dw-tile.dw-field-white{ background:#ffffff; }
.dw-tile.dw-field-black{ background:var(--dw-black); }

.dw-bg{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; }
.dw-bg.dw-bg-contain{ object-fit:contain; }
.dw-bg.dw-bg-pad{ padding: 14cqw 10cqw; box-sizing:border-box; background:#fff; }

.dw-scrim{ position:absolute; left:0; right:0; height:55%; z-index:1; }
.dw-scrim-bottom{ bottom:0; background:linear-gradient(to top, rgba(0,0,0,.72), rgba(0,0,0,0)); }

/* Yellow LINES (thin rule), not thick bars -- a deliberate brand-system
   refinement for PDP assets. The logo no longer sits inside the line (it's
   too thin to hold text); it floats as its own small badge just beneath the
   top line instead. All the percentage offsets below (headline, chiplist,
   badgestack, compare, pending-ribbon, eyebrow) were retuned to reclaim the
   space the old ~10%-tall bar used to occupy. */
.dw-bar{ position:absolute; left:0; right:0; height:0.7%; background:var(--dw-yellow); z-index:3; }
.dw-bar-top{ top:0; } .dw-bar-bottom{ bottom:0; }
.tile-logo{
  position:absolute; z-index:4; top:2.2%; left:3.7%;
  font-family:'Archivo Expanded Black'; font-weight:900; color:var(--dw-yellow); text-transform:uppercase;
  font-size:2.6cqw; letter-spacing:-0.01em; background:rgba(35,30,32,.72); padding:0.9cqw 1.6cqw; border-radius:2px;
}

.dw-headline{ position:absolute; z-index:3; font-family:'Archivo Expanded Black'; font-weight:900; text-transform:uppercase; line-height:.86; letter-spacing:-0.015em; }
.dw-headline span{display:block;}
.dw-headline .l1{color:#fff;} .dw-headline .l2{color:var(--dw-yellow);}
.dw-headline-md{ font-size:8.6cqw; }
.dw-headline-sm{ font-size:6.6cqw; }
.dw-headline-bl{ left:3.7%; bottom:5%; max-width:80%; }
.dw-headline-tl{ left:3.7%; top:9%; max-width:78%; }
.dw-field-white .dw-headline .l1{ color:var(--dw-black); }

.dw-tag{ position:absolute; z-index:3; left:3.7%; bottom:3%; background:var(--dw-yellow); color:var(--dw-black);
  font-weight:800; font-size:2.9cqw; text-transform:uppercase; letter-spacing:.02em; padding:1.4cqw 2.6cqw; border-radius:2px; }

.dw-eyebrow{ position:absolute; z-index:3; left:3.7%; top:9%; color:var(--dw-offwhite); text-transform:uppercase;
  font-size:2.6cqw; letter-spacing:.08em; font-weight:700; opacity:.85; }

.dw-badgestack{ position:absolute; z-index:3; right:3.7%; top:11%; display:flex; flex-direction:column; gap:2.6cqw; width:46%; }
.dw-badgestack-right{ align-items:flex-end; }
.dw-badge{ background:var(--dw-black); color:#fff; border-left:.9cqw solid var(--dw-yellow); padding:1.6cqw 2.4cqw; text-align:left; }
.dw-badge-sku{ display:block; font-weight:800; font-size:2.5cqw; color:var(--dw-yellow); letter-spacing:.03em; }
.dw-badge-txt{ display:block; font-size:2.35cqw; line-height:1.25; margin-top:.4cqw; }

.dw-chiplist{ position:absolute; z-index:3; left:3.7%; right:3.7%; display:flex; flex-direction:column; gap:2cqw; }
.dw-tile-chips-bottom .dw-chiplist{ bottom:5%; }
.dw-tile:not(.dw-tile-chips-bottom) .dw-chiplist{ top:11%; }
.dw-chip{ display:flex; align-items:center; gap:2.2cqw; background:rgba(35,30,32,.9); padding:1.7cqw 2.2cqw; border-radius:3px; }
.dw-field-white .dw-chip{ background:var(--dw-black); }
.dw-chip-n{ font-family:'Archivo Expanded Black'; color:var(--dw-yellow); font-size:3.1cqw; font-weight:900; min-width:5.5cqw; }
.dw-chip-t{ color:#fff; font-size:2.35cqw; line-height:1.3; }

.dw-pending-ribbon{ position:absolute; z-index:4; left:0; right:0; top:9%; background:#9A2E1F; color:#fff;
  font-weight:800; font-size:2.3cqw; text-transform:uppercase; letter-spacing:.03em; text-align:center; padding:1.6cqw 3%; }

.dw-compare{ position:absolute; z-index:3; left:3.7%; right:3.7%; top:11%; bottom:5%; display:flex; flex-direction:column; }
.cmp-row{ display:grid; gap:2cqw; padding:2.4cqw 0; border-bottom:1px solid rgba(255,255,255,.14); align-items:center; }
.dw-field-white .cmp-row{ border-bottom:1px solid rgba(35,30,32,.14); }
.cmp-row.cmp-head{ border-bottom:2px solid var(--dw-yellow); padding-bottom:1.8cqw; }
.cmp-label{ font-size:2.15cqw; color:#cfcac6; }
.dw-field-white .cmp-label{ color:#57524f; }
.cmp-val{ font-size:2.15cqw; font-weight:700; text-align:center; color:#fff; }
.dw-field-white .cmp-val{ color:var(--dw-black); }
.cmp-val.cmp-highlight{ color:var(--dw-yellow); }
.cmp-row.cmp-head .cmp-val{ color:#B9B4AE; text-transform:uppercase; font-weight:800; letter-spacing:.02em; }
.cmp-row.cmp-head .cmp-val.cmp-highlight{ color:var(--dw-yellow); }

/* Enriched (wide) module layout */
.dw-tile-wide{ display:grid; grid-template-columns: 1.05fr 1fr; }
.ep-media{ position:relative; overflow:hidden; background:#fff; }
.ep-media .dw-bg{ position:absolute; inset:0; }
.ep-media.dw-field-black{ background:var(--dw-black); }
.ep-copy{
  position:relative; background:var(--dw-offwhite); padding:6.2cqw 5.4cqw; display:flex; flex-direction:column;
  gap:2.6cqw; justify-content:center; overflow:hidden;
  container-type: inline-size; container-name: epcopy;
}
.ep-copy.dw-field-black{ background:var(--dw-black); color:#fff; }
.ep-kicker{ font-family:'Archivo Expanded Black'; font-weight:900; font-size:2.4cqw; letter-spacing:.05em; color:var(--dw-black); text-transform:uppercase; }
.ep-copy.dw-field-black .ep-kicker{ color:var(--dw-yellow); }
.ep-h{ font-family:'Archivo Expanded Black'; font-weight:900; font-size:4.6cqw; line-height:.98; text-transform:uppercase; letter-spacing:-0.01em; color:var(--dw-black); }
.ep-copy.dw-field-black .ep-h{ color:#fff; }
.ep-copy .dw-chiplist{ position:static; margin-top:1.4cqw; }
.ep-copy .dw-chip{ background:var(--dw-black); }
.ep-copy.dw-field-black .dw-chip{ background:rgba(255,255,255,.1); }

.foot-band{ background:var(--dw-black); border-top:6px solid var(--dw-yellow); margin-top:64px; color:#C7C3BB; font-size:13.5px; }
.foot-inner{ max-width:1280px; margin:0 auto; padding:40px 28px 52px; }
.foot-inner h4{ color:var(--dw-yellow); font-family:'Archivo Expanded Black'; font-weight:900; font-size:12.5px; text-transform:uppercase; letter-spacing:.07em; margin:0 0 12px; }
.foot-inner ul{ margin:0 0 22px; padding-left:18px; }
.foot-inner li{ margin-bottom:7px; }
.foot-inner .foot-grid{ display:grid; grid-template-columns:1fr 1fr; gap:36px; }
@media (max-width:700px){ .foot-inner .foot-grid{grid-template-columns:1fr;} }
"""

# The client-side script is identical across every generated page (base
# image mirroring, SVG->canvas export via lightbox, notes persistence).
# Notes are stored server-side (Supabase table `asset_notes`, keyed by
# page_sku + asset_id) -- NOT localStorage -- so a comment written by anyone,
# on any device, is visible to everyone who opens this same page.
SUPABASE_URL = "https://cyxhcnrfabtxusbzaokj.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5eGhjbnJmYWJ0eHVzYnphb2tqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ4Mjk5MDgsImV4cCI6MjEwMDQwNTkwOH0.DFli12gONPoxJXLPB3M0q2cVHDAKTe3MmN4mZfKZGi0"


def render_script(sku):
    page_sku = sku.lower()
    return """
<script type="module">
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
const supabase = createClient('""" + SUPABASE_URL + """', '""" + SUPABASE_ANON_KEY + """');
const PAGE_SKU = '""" + page_sku + """';

(function(){
  var TILE_CSS = `""" + BASE_CSS.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${") + """`;

  function q(sel, root){ return (root||document).querySelectorAll(sel); }

  function initBaseImages(){
    q('.base-photo[data-src-from]').forEach(function(img){
      var srcTile = document.getElementById(img.getAttribute('data-src-from'));
      var srcImg = srcTile && srcTile.querySelector('img.dw-bg');
      if (srcImg && srcImg.src) img.src = srcImg.src;
    });
  }

  function buildExportSVG(tileEl, w, h){
    var svgNS = 'http://www.w3.org/2000/svg';
    var xhtmlNS = 'http://www.w3.org/1999/xhtml';
    var clone = tileEl.cloneNode(true);
    clone.removeAttribute('id');
    clone.style.width = w + 'px';
    clone.style.height = h + 'px';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('xmlns', svgNS);
    svg.setAttribute('width', w);
    svg.setAttribute('height', h);
    var fo = document.createElementNS(svgNS, 'foreignObject');
    fo.setAttribute('width', '100%');
    fo.setAttribute('height', '100%');
    var wrapper = document.createElementNS(xhtmlNS, 'div');
    wrapper.setAttribute('style', 'width:' + w + 'px;height:' + h + 'px;');
    var styleEl = document.createElementNS(xhtmlNS, 'style');
    styleEl.textContent = TILE_CSS;
    wrapper.appendChild(styleEl);
    wrapper.appendChild(clone);
    fo.appendChild(wrapper);
    svg.appendChild(fo);
    return new XMLSerializer().serializeToString(svg);
  }

  function rasterizeToDataURL(svgStr, w, h){
    return new Promise(function(resolve, reject){
      var img = new Image();
      img.onload = function(){
        try {
          var canvas = document.createElement('canvas');
          canvas.width = w; canvas.height = h;
          var ctx = canvas.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, w, h);
          ctx.drawImage(img, 0, 0, w, h);
          resolve(canvas.toDataURL('image/jpeg', 0.92));
        } catch (e) { reject(e); }
      };
      img.onerror = function(){ reject(new Error('SVG failed to rasterize')); };
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgStr);
    });
  }

  function openLightbox(dataUrl, filename){
    var overlay = document.getElementById('lightbox');
    var img = document.getElementById('lightbox-img');
    img.src = dataUrl;
    overlay.classList.add('open');
    try {
      var a = document.createElement('a');
      a.href = dataUrl;
      a.download = filename || 'asset.jpg';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) { /* ignore -- lightbox is the reliable fallback */ }
  }

  function closeLightbox(){ document.getElementById('lightbox').classList.remove('open'); }

  function exportTile(id, w, h, filename, btn){
    var src = document.getElementById(id);
    if (!src) return;
    if (btn) btn.classList.add('busy');
    try {
      var svgStr = buildExportSVG(src, w, h);
      rasterizeToDataURL(svgStr, w, h).then(function(dataUrl){
        openLightbox(dataUrl, filename);
        if (btn) btn.classList.remove('busy');
      }).catch(function(e){
        console.error('export failed', id, e);
        if (btn) btn.classList.remove('busy');
        alert('Nao foi possivel gerar este asset neste navegador.');
      });
    } catch (e) {
      console.error('export setup failed', id, e);
      if (btn) btn.classList.remove('busy');
      alert('Nao foi possivel gerar este asset neste navegador.');
    }
  }

  function initExportButtons(){
    q('.dl-export').forEach(function(btn){
      btn.addEventListener('click', function(){
        exportTile(btn.getAttribute('data-export-id'), parseInt(btn.getAttribute('data-w'),10),
                   parseInt(btn.getAttribute('data-h'),10), btn.getAttribute('data-filename'), btn);
      });
    });
  }

  function initBaseViewButtons(){
    q('.dl-base-view').forEach(function(btn){
      btn.addEventListener('click', function(){
        var tileId = btn.getAttribute('data-view-from');
        var srcTile = document.getElementById(tileId);
        var srcImg = srcTile && srcTile.querySelector('img.dw-bg');
        if (srcImg && srcImg.src) openLightbox(srcImg.src, tileId + '_base.jpg');
      });
    });
  }

  function initLightbox(){
    var closeBtn = document.getElementById('lightbox-close');
    var overlay = document.getElementById('lightbox');
    if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
    if (overlay) overlay.addEventListener('click', function(e){ if (e.target === overlay) closeLightbox(); });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeLightbox(); });
  }

  async function initNotes(){
    var notesById = {};
    try {
      var { data, error } = await supabase.from('asset_notes').select('asset_id, note').eq('page_sku', PAGE_SKU);
      if (!error && data) data.forEach(function(r){ notesById[r.asset_id] = r.note; });
    } catch (e) { /* fall through -- textareas just start empty */ }

    q('.notes-area[data-note-id]').forEach(function(area){
      var id = area.getAttribute('data-note-id');
      var statusEl = document.querySelector('[data-note-status="' + id + '"]');
      if (notesById[id]) area.value = notesById[id];
      var timer = null;
      area.addEventListener('input', function(){
        if (statusEl) statusEl.textContent = 'Salvando...';
        if (timer) clearTimeout(timer);
        timer = setTimeout(async function(){
          try {
            var { error } = await supabase.from('asset_notes')
              .upsert({ page_sku: PAGE_SKU, asset_id: id, note: area.value }, { onConflict: 'page_sku,asset_id' });
            if (statusEl) statusEl.textContent = error ? 'Nao foi possivel salvar.' : (area.value ? 'Salvo -- visivel pra qualquer pessoa.' : '');
          } catch (e) { if (statusEl) statusEl.textContent = 'Nao foi possivel salvar.'; }
        }, 500);
      });
    });
  }

  function ready(fn){
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  ready(function(){
    initBaseImages(); initExportButtons(); initBaseViewButtons(); initLightbox(); initNotes();
  });
})();
</script>
"""


def render_page(sku, product_name, meta_chips, rows_html, ep_rows_html, source_note=""):
    """meta_chips: list of (label, value) tuples for the hero sku-row (e.g.
    [('SKU','DWST60436'), ('Vedacao','IP65'), ...]).
    rows_html / ep_rows_html: lists of already-built spec_row() strings.
    source_note: one sentence naming where specs/photos came from."""
    chips = "".join(
        f'<div class="sku-item"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span></div>'
        for k, v in meta_chips
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(sku)} — Kit de Assets PDP</title>
<style>{BASE_CSS}</style>
</head>
<body>
<div class="hero-band">
  <div class="hero-inner">
    <div class="masthead">
      <div class="eyebrow">DEWALT · Template PDP</div>
      <h1>{esc(sku)} — <span class="accent">{esc(product_name)}</span></h1>
      <div class="sub">Kit de assets de PDP gerado automaticamente a partir de fontes oficiais. {source_note}</div>
      <div class="sku-row">{chips}</div>
    </div>
  </div>
</div>

<div class="wrap">
  <div class="intro">
    <b>Como ler isto:</b> cada asset mostra a <b>imagem-base</b> (foto oficial sem edição) ao lado do <b>asset sugerido</b> — clique com o botão direito em qualquer imagem e escolha "Salvar imagem como..." pra baixar.
    Abaixo de cada imagem há um <b>briefing da peça</b> e um campo de <b>comentário</b> salvo neste navegador.
    Copy (headlines/bullets) é rascunho e precisa de aprovação de marketing antes de publicar. Comparativos com dado externo pendente estão marcados — nenhum número foi inventado.
  </div>

  <div class="section-label"><h2>Assets principais</h2><div class="line"></div></div>
  {''.join(rows_html)}

  {'<div class="section-label"><h2>Paginas enriquecidas</h2><div class="line"></div></div>' + ''.join(ep_rows_html) if ep_rows_html else ''}
</div>

<div class="foot-band">
  <div class="foot-inner">
    <div class="foot-grid">
      <div>
        <h4>O que ainda precisa de revisão</h4>
        <ul>
          <li>Aprovação de marketing para headlines/bullets marcados "copy em revisão".</li>
          <li>Qualquer asset marcado "dado externo pendente" precisa do valor real antes de publicar.</li>
        </ul>
      </div>
      <div>
        <h4>Sobre esta geração</h4>
        <ul>
          <li>Gerado automaticamente pela rotina do gerador de assets PDP.</li>
          <li>Fontes/fotos: ver briefing de cada peça para a fonte específica.</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<div class="lightbox-overlay" id="lightbox">
  <button class="lightbox-close" id="lightbox-close">Fechar</button>
  <img class="lightbox-img" id="lightbox-img" alt="Asset gerado" />
  <div class="lightbox-hint">Clique com o botão direito na imagem acima e escolha <b>"Salvar imagem como..."</b>.</div>
</div>

{render_script(sku)}
</body>
</html>
"""
