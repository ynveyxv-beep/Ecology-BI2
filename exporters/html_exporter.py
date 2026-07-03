# exporters/html_exporter.py
"""
Экспорт дашборда в standalone HTML-файл.
Открывается в любом браузере без установки Python и приложения.
Графики — встроенный SVG (без CDN-зависимостей).
Карта — Leaflet.js (CDN; интерактивность требует внешней библиотеки).
"""
import json
import math
import os
import webbrowser
from datetime import datetime


# ── Цветовая схема (slate dark) ────────────────────────────────────────────────
_C = {
    'bg_deep':   '#060B18',
    'bg_dark':   '#0F172A',
    'bg_panel':  '#1E293B',
    'bg_card':   '#263347',
    'bg_hover':  '#2D3E56',
    'border':    '#334155',
    'border_lt': '#475569',
    'accent':    '#38BDF8',
    'text_pri':  '#F1F5F9',
    'text_sec':  '#94A3B8',
    'text_mut':  '#64748B',
    'ok':        '#34D399',
    'warn':      '#FBBF24',
    'crit':      '#F87171',
}

_CHART_PALETTE = [
    '#38BDF8', '#818CF8', '#FBBF24', '#F87171',
    '#34D399', '#A78BFA', '#F472B6', '#4ADE80',
]

_STATUS_COLORS = {
    'норма':       _C['ok'],
    'превышение': _C['warn'],
    'критично':    _C['crit'],
}

_STATUS_CLASS = {
    'норма':       'ok',
    'превышение': 'warn',
    'критично':    'crit',
}


# ── Вспомогательные ─────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _sample_labels(n: int = 8) -> list:
    months = ['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен','Окт','Ноя','Дек']
    return months[:n]


def _sample_values(n: int = 8, lo: int = 20, hi: int = 90) -> list:
    import random
    random.seed(42)
    return [random.randint(lo, hi) for _ in range(n)]


# ── Рендереры виджетов ────────────────────────────────────────────────────────

def _render_kpi(settings: dict, widget_id: str) -> str:
    title    = _esc(settings.get('title', 'KPI'))
    value    = _esc(settings.get('value', '—')) or '—'
    unit     = _esc(settings.get('unit', ''))
    color    = settings.get('color', _C['accent'])
    fs       = settings.get('font_size', 36)
    unit_fs  = max(11, fs // 3)
    unit_html = (
        f"<span style='font-size:{unit_fs}px;color:{color};opacity:.6;"
        f"margin-left:4px;'>{unit}</span>"
    ) if unit else ''

    return f"""
<div class="widget kpi-widget" id="{widget_id}">
  <div class="widget-title">{title}</div>
  <div class="kpi-value" style="color:{color};font-size:{fs}px">{value}{unit_html}</div>
</div>"""


def _svg_chart(color: str, style: str, values: list, labels: list,
               W: int = 320, H: int = 120) -> str:
    """Генерирует SVG-строку графика (без внешних зависимостей)."""
    mx = max(values) if values else 1
    brd = _C['border']
    tmut = _C['text_mut']
    tpri = _C['text_pri']
    shapes = ''
    axes   = ''

    if style == 'bar':
        step = W / (len(values) + 1)
        bw   = max(14, step - 8)
        for i, v in enumerate(values):
            bh = int(v / mx * (H - 22))
            x  = int(step * (i + 1) - bw / 2)
            y  = H - 4 - bh
            op = '1' if i % 2 == 0 else '0.72'
            lbl = _esc(labels[i]) if i < len(labels) else ''
            shapes += (
                f"<rect x='{x}' y='{y}' width='{int(bw)}' height='{bh}' "
                f"fill='{color}' fill-opacity='{op}' rx='2'/>"
                f"<text x='{x + int(bw)//2}' y='{H + 9}' text-anchor='middle' "
                f"font-size='8' fill='{tmut}'>{lbl}</text>"
            )
        axes = (
            f"<line x1='12' y1='2' x2='12' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
            f"<line x1='12' y1='{H-4}' x2='{W-4}' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
        )

    elif style == 'scatter':
        pts = [(int(20 + i * (W-40)/(len(values)-1)), int(H-8 - v/mx*(H-20)))
               for i, v in enumerate(values)]
        for x, y in pts:
            shapes += (
                f"<circle cx='{x}' cy='{y}' r='5' fill='{color}' fill-opacity='0.75'/>"
                f"<circle cx='{x}' cy='{y}' r='2' fill='{color}'/>"
            )
        axes = (
            f"<line x1='12' y1='2' x2='12' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
            f"<line x1='12' y1='{H-4}' x2='{W-4}' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
        )

    elif style == 'radar':
        n = min(len(values), 8)
        vals_n = values[:n]
        lbls_n = labels[:n]
        mx_n = max(vals_n) if vals_n else 1
        cx, cy = W // 2, H // 2
        r = min(W, H) // 2 - 14
        for ring in [0.33, 0.66, 1.0]:
            pts_ring = ' '.join(
                f"{cx + r*ring*math.cos(2*math.pi*i/n - math.pi/2):.1f},"
                f"{cy + r*ring*math.sin(2*math.pi*i/n - math.pi/2):.1f}"
                for i in range(n)
            )
            shapes += f"<polygon points='{pts_ring}' fill='none' stroke='{brd}' stroke-width='1'/>"
        data_r = [v / mx_n for v in vals_n]
        data_pts = ' '.join(
            f"{cx + r*data_r[i]*math.cos(2*math.pi*i/n - math.pi/2):.1f},"
            f"{cy + r*data_r[i]*math.sin(2*math.pi*i/n - math.pi/2):.1f}"
            for i in range(n)
        )
        shapes += (
            f"<polygon points='{data_pts}' fill='{color}' fill-opacity='0.2' "
            f"stroke='{color}' stroke-width='2'/>"
        )
        for i in range(n):
            lx = cx + (r+10)*math.cos(2*math.pi*i/n - math.pi/2)
            ly = cy + (r+10)*math.sin(2*math.pi*i/n - math.pi/2)
            lbl = _esc(lbls_n[i]) if i < len(lbls_n) else ''
            shapes += (
                f"<text x='{lx:.1f}' y='{ly:.1f}' text-anchor='middle' "
                f"dominant-baseline='central' font-size='7' fill='{tmut}'>{lbl}</text>"
            )

    elif style == 'heatmap':
        cols_h, rows_h = min(len(values), 7), 3
        cw = (W - 20) // cols_h
        rh = (H - 16) // rows_h
        import random; rng = random.Random(0)
        heat = [rng.uniform(0.1, 1.0) for _ in range(cols_h * rows_h)]
        for ri in range(rows_h):
            for ci in range(cols_h):
                v  = heat[ri * cols_h + ci]
                op = round(v * 0.78 + 0.22, 2)
                x  = 10 + ci * cw
                y  = 8 + ri * rh
                lbl = _esc(labels[ci]) if (ri == 0 and ci < len(labels)) else ''
                shapes += (
                    f"<rect x='{x}' y='{y}' width='{cw-2}' height='{rh-2}' "
                    f"fill='{color}' fill-opacity='{op}' rx='2'/>"
                )
                if lbl:
                    shapes += (
                        f"<text x='{x + (cw-2)//2}' y='{H+9}' text-anchor='middle' "
                        f"font-size='7' fill='{tmut}'>{lbl}</text>"
                    )

    elif style == 'treemap':
        total  = sum(values) or 1
        sorted_v = sorted(enumerate(values), key=lambda x: -x[1])
        x_cur = 4
        avail = W - 8
        for rank, (i, v) in enumerate(sorted_v[:5]):
            w_cell = int(v / total * avail)
            if w_cell < 6: continue
            op = max(0.3, 1.0 - rank * 0.18)
            shapes += (
                f"<rect x='{x_cur}' y='4' width='{w_cell-2}' height='{H-8}' "
                f"fill='{color}' fill-opacity='{op:.2f}' rx='3'/>"
                f"<text x='{x_cur + (w_cell-2)//2}' y='{H//2+4}' "
                f"text-anchor='middle' font-size='9' fill='{tpri}'>"
                f"{int(v/total*100)}%</text>"
            )
            x_cur += w_cell

    elif style == 'area':
        step_x = (W - 30) / max(len(values) - 1, 1)
        pts_str = ' '.join(
            f"{int(15 + i * step_x)},{int(H-8 - v/mx*(H-22))}"
            for i, v in enumerate(values)
        )
        last_x = int(15 + (len(values)-1) * step_x)
        fill_pts = f"{pts_str} {last_x},{H-8} 15,{H-8}"
        shapes = (
            f"<polygon points='{fill_pts}' fill='{color}' fill-opacity='0.15'/>"
            f"<polyline points='{pts_str}' fill='none' stroke='{color}' "
            f"stroke-width='2' stroke-linejoin='round' stroke-linecap='round'/>"
        )
        axes = (
            f"<line x1='12' y1='2' x2='12' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
            f"<line x1='12' y1='{H-4}' x2='{W-4}' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
        )

    else:  # line (default)
        step_x = (W - 30) / max(len(values) - 1, 1)
        pts_str = ' '.join(
            f"{int(15 + i * step_x)},{int(H-8 - v/mx*(H-22))}"
            for i, v in enumerate(values)
        )
        shapes = (
            f"<polyline points='{pts_str}' fill='none' stroke='{color}' "
            f"stroke-width='2.5' stroke-linejoin='round' stroke-linecap='round'/>"
        )
        for i, v in enumerate(values):
            px = int(15 + i * step_x)
            py = int(H - 8 - v / mx * (H - 22))
            shapes += f"<circle cx='{px}' cy='{py}' r='3' fill='{color}'/>"
        axes = (
            f"<line x1='12' y1='2' x2='12' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
            f"<line x1='12' y1='{H-4}' x2='{W-4}' y2='{H-4}' stroke='{brd}' stroke-width='1'/>"
        )

    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='100%' height='100%' "
        f"viewBox='0 0 {W} {H+14}' preserveAspectRatio='xMidYMid meet'>"
        f"{axes}{shapes}"
        f"</svg>"
    )


def _render_chart(settings: dict, widget_id: str) -> str:
    title  = _esc(settings.get('title', 'График'))
    color  = settings.get('color', _C['accent'])
    style  = settings.get('chart_style', 'bar')
    n      = min(settings.get('max_items', 8), 12)
    labels = _sample_labels(n)
    values = _sample_values(n)

    svg = _svg_chart(color, style, values, labels)

    return f"""
<div class="widget chart-widget" id="{widget_id}">
  <div class="widget-title">{title}</div>
  <div class="chart-wrap">{svg}</div>
</div>"""


def _render_table(settings: dict, widget_id: str) -> str:
    title  = _esc(settings.get('title', 'Таблица'))
    limit  = settings.get('limit', 5)
    # Генерируем сэмпл таблицы
    cols   = ['Район', 'Показатель', 'Норма', 'Статус']
    sample = [
        ['Нижегородский р-н', '42.1 мкг/м³', '50', '🟢 Норма'],
        ['Советский р-н',     '61.8 мкг/м³', '50', '🟡 Превышение'],
        ['Автозаводский р-н', '38.5 мкг/м³', '50', '🟢 Норма'],
        ['Канавинский р-н',   '79.2 мкг/м³', '50', '🔴 Критично'],
        ['Ленинский р-н',     '44.3 мкг/м³', '50', '🟢 Норма'],
    ][:min(limit, 5)]

    header = ''.join(f'<th>{_esc(c)}</th>' for c in cols)
    rows   = ''
    for i, row in enumerate(sample):
        cls = 'row-even' if i % 2 == 0 else 'row-odd'
        cells = ''.join(f'<td>{_esc(cell)}</td>' for cell in row)
        rows += f'<tr class="{cls}">{cells}</tr>'

    return f"""
<div class="widget table-widget" id="{widget_id}">
  <div class="widget-title">{title}</div>
  <div class="table-wrap">
    <table>
      <thead><tr>{header}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def _render_text(settings: dict, widget_id: str) -> str:
    content = _esc(settings.get('content', ''))
    fs      = settings.get('font_size', 14)
    return f"""
<div class="widget text-widget" id="{widget_id}">
  <div class="text-content" style="font-size:{fs}px">{content}</div>
</div>"""


def _render_image(settings: dict, widget_id: str) -> str:
    path  = settings.get('path', '')
    scale = settings.get('scale', 100)
    if path and os.path.isfile(path):
        import base64
        ext  = os.path.splitext(path)[1].lower().lstrip('.')
        mime = {'jpg':'jpeg','jpeg':'jpeg','png':'png','gif':'gif','bmp':'bmp','webp':'webp'}.get(ext,'png')
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        # scale применяется как max-width в процентах от контейнера;
        # object-fit:contain и max-height берутся из CSS класса
        scale_style = f'style="max-width:{scale}%;"' if scale != 100 else ''
        img_tag = f'<img src="data:image/{mime};base64,{b64}" {scale_style}>'
    else:
        img_tag = '<div class="img-placeholder">🖼 Изображение</div>'
    return f"""
<div class="widget image-widget" id="{widget_id}">
  <div class="image-wrap">{img_tag}</div>
</div>"""


def _render_map(settings: dict, widget_id: str) -> str:
    title           = _esc(settings.get('title', 'Карта'))
    manual_markers  = settings.get('manual_markers', [])
    center          = settings.get('center', [56.32, 44.00])
    zoom            = settings.get('zoom', 8)
    markers_json    = json.dumps(manual_markers, ensure_ascii=False)

    status_colors_json = json.dumps(_STATUS_COLORS)
    status_class_json  = json.dumps(_STATUS_CLASS)

    return f"""
<div class="widget map-widget" id="{widget_id}">
  <div class="widget-title">{title}</div>
  <div class="map-container" id="map_{widget_id}"></div>
</div>
<script>
(function(){{
  var map = L.map('map_{widget_id}', {{
    center: {json.dumps(center)},
    zoom: {zoom},
    zoomControl: true,
    attributionControl: false
  }});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
    {{ maxZoom:19, subdomains:'abcd' }}).addTo(map);

  var STATUS_COLORS = {status_colors_json};
  var STATUS_CLASS  = {status_class_json};
  var markers = {markers_json};
  var lms = [];

  markers.forEach(function(m) {{
    if (m.lat == null || m.lng == null) return;
    var color = STATUS_COLORS[m.status] || '{_C["accent"]}';
    var sc    = STATUS_CLASS[m.status]  || 'ok';
    var status = m.status || 'норма';
    var icon = L.divIcon({{
      html: '<div style="width:14px;height:14px;background:'+color+';border:2px solid rgba(255,255,255,.25);border-radius:50%;box-shadow:0 0 10px '+color+'99;"></div>',
      iconSize:[14,14], iconAnchor:[7,7], className:''
    }});
    var valHtml = (m.value !== undefined && m.value !== null && m.value !== '')
      ? '<div style="font-size:20px;font-weight:700;color:{_C["text_pri"]}">'+m.value+(m.unit?'<span style="font-size:11px;color:{_C["text_mut"]};margin-left:3px">'+m.unit+'</span>':'')+'</div>' : '';
    var popup = '<div style="background:{_C["bg_panel"]};color:{_C["text_pri"]};border-radius:8px;padding:12px;min-width:150px;">'
      + '<div style="color:{_C["accent"]};font-weight:600;font-size:13px;margin-bottom:6px;">'+(m.name||'Объект')+'</div>'
      + valHtml
      + '<div style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;margin-top:6px;background:#022C22;color:#34D399;border:1px solid #064E3B;">'+status+'</div>'
      + (m.note ? '<div style="font-size:11px;color:#94A3B8;margin-top:6px;padding-top:6px;border-top:1px solid #263347;">'+m.note+'</div>' : '')
      + '</div>';
    var mk = L.marker([m.lat,m.lng],{{icon:icon}}).addTo(map).bindPopup(popup,{{maxWidth:240}});
    lms.push(mk);
  }});
  if (lms.length > 0) {{
    try {{ map.fitBounds(L.featureGroup(lms).getBounds().pad(0.25)); }} catch(e) {{}}
  }}
}})();
</script>"""


def _render_widget(w: dict, idx: int) -> str:
    wtype    = w.get('type', '')
    settings = w.get('settings', {})
    wid      = f"w{idx}"

    if wtype == 'kpi':
        return _render_kpi(settings, wid)
    elif wtype == 'chart':
        return _render_chart(settings, wid)
    elif wtype == 'table':
        return _render_table(settings, wid)
    elif wtype == 'text':
        return _render_text(settings, wid)
    elif wtype == 'image':
        return _render_image(settings, wid)
    elif wtype == 'map':
        return _render_map(settings, wid)
    else:
        return f'<div class="widget" id="w{idx}"><div class="widget-title">{_esc(wtype)}</div></div>'


# ── Главная функция ────────────────────────────────────────────────────────────

def export_to_html(dashboard_data: dict, output_path: str,
                   open_browser: bool = True) -> str:
    """
    Генерирует standalone HTML из данных дашборда.

    :param dashboard_data: dict от DashboardGrid.serialize() или загруженный JSON
    :param output_path:    путь для сохранения .html файла
    :param open_browser:   открыть файл в браузере после экспорта
    :returns: output_path
    """
    # ── Применить тему ────────────────────────────────────────────────────────
    theme_name = dashboard_data.get('theme', 'ocean')
    try:
        from ui.theme import THEMES as _THEMES
        t = _THEMES.get(theme_name, _THEMES['ocean'])
        _C['bg_deep']   = t['BG_DEEP']
        _C['bg_dark']   = t['BG_DARK']
        _C['bg_panel']  = t['BG_PANEL']
        _C['bg_card']   = t['BG_CARD']
        _C['bg_hover']  = t['BG_HOVER']
        _C['border']    = t['BORDER']
        _C['border_lt'] = t['BORDER_LT']
        _C['accent']    = t['ACCENT']
        _C['text_pri']  = t['TEXT_PRI']
        _C['text_sec']  = t['TEXT_SEC']
        _C['text_mut']  = t['TEXT_MUT']
        global _CHART_PALETTE
        _CHART_PALETTE  = list(t.get('CHART_PALETTE', _CHART_PALETTE))
    except Exception:
        pass  # Автономный запуск — используем дефолтные значения

    pages = dashboard_data.get('pages', [])
    if not pages:
        # Старый формат (без страниц)
        pages = [{
            'name':    dashboard_data.get('name', 'Дашборд'),
            'rows':    dashboard_data.get('rows', 2),
            'columns': dashboard_data.get('columns', 3),
            'widgets': dashboard_data.get('widgets', []),
        }]

    dash_name    = _esc(dashboard_data.get('name', 'Дашборд'))
    export_date  = datetime.now().strftime('%d.%m.%Y %H:%M')
    needs_leaflet = any(
        w.get('type') == 'map'
        for p in pages for w in p.get('widgets', [])
    )

    # ── Tabs HTML ──────────────────────────────────────────────────────────
    tab_btns   = ''
    tab_panels = ''
    w_counter  = 0

    for pi, page in enumerate(pages):
        pname     = _esc(page.get('name', f'Страница {pi+1}'))
        rows      = page.get('rows', 2)
        cols      = page.get('columns', 3)
        widgets   = page.get('widgets', [])
        active    = 'active' if pi == 0 else ''
        row_sizes = page.get('row_sizes', [])
        col_sizes = page.get('col_sizes', [])

        tab_btns += f'<button class="tab-btn {active}" onclick="switchTab({pi})">{pname}</button>\n'

        # CSS grid-template размеры — пропорциональные fr-единицы
        if row_sizes and len(row_sizes) == rows:
            total_r = sum(row_sizes) or 1
            row_tpl = ' '.join(f'{s/total_r:.4f}fr' for s in row_sizes)
        else:
            row_tpl = f'repeat({rows}, 1fr)'

        if col_sizes and len(col_sizes) == cols:
            total_c = sum(col_sizes) or 1
            col_tpl = ' '.join(f'{s/total_c:.4f}fr' for s in col_sizes)
        else:
            col_tpl = f'repeat({cols}, 1fr)'

        # Build grid: place widgets at (row, col)
        grid: dict = {}
        for w in widgets:
            r, c = w.get('row', 0), w.get('col', 0)
            grid[(r, c)] = w

        cells_html = ''
        for r in range(rows):
            for c in range(cols):
                w = grid.get((r, c))
                if w:
                    w_counter += 1
                    cells_html += _render_widget(w, w_counter)
                else:
                    cells_html += f'<div class="widget widget-empty"></div>'

        tab_panels += f"""
<div class="tab-panel {active}" id="tab_{pi}">
  <div class="dashboard-grid" style="grid-template-columns:{col_tpl};grid-template-rows:{row_tpl};">
    {cells_html}
  </div>
</div>"""

    # ── CDN scripts (только Leaflet для карты; графики — встроенный SVG) ────
    leaflet_css = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>' if needs_leaflet else ''
    leaflet_js  = '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>' if needs_leaflet else ''

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{dash_name} — Ecology-BI</title>
{leaflet_css}
{leaflet_js}
<style>
:root {{
  --bg-deep:   {_C['bg_deep']};
  --bg-dark:   {_C['bg_dark']};
  --bg-panel:  {_C['bg_panel']};
  --bg-card:   {_C['bg_card']};
  --bg-hover:  {_C['bg_hover']};
  --border:    {_C['border']};
  --border-lt: {_C['border_lt']};
  --accent:    {_C['accent']};
  --text-pri:  {_C['text_pri']};
  --text-sec:  {_C['text_sec']};
  --text-mut:  {_C['text_mut']};
}}
*,*::before,*::after {{ box-sizing:border-box; margin:0; padding:0; }}
html,body {{ height:100%; background:var(--bg-deep); color:var(--text-pri); font-family:system-ui,'Segoe UI',sans-serif; }}

/* ── Header ── */
.app-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}}
.app-logo {{ color: var(--accent); font-size:18px; font-weight:700; letter-spacing:-.3px; }}
.app-meta  {{ font-size:11px; color:var(--text-mut); }}

/* ── Tabs ── */
.tabs {{
  display: flex;
  gap: 2px;
  padding: 10px 24px 0;
  background: var(--bg-dark);
  border-bottom: 1px solid var(--border);
}}
.tab-btn {{
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-mut);
  cursor: pointer;
  font-size: 13px;
  padding: 8px 18px;
  transition: color .15s, border-color .15s;
}}
.tab-btn:hover {{ color: var(--text-sec); }}
.tab-btn.active {{ color: var(--accent); border-bottom-color: var(--accent); }}

/* ── Pages ── */
.tab-panel {{ display:none; padding:16px 24px; height:calc(100vh - 105px); }}
.tab-panel.active {{ display:block; }}

/* ── Grid ── */
.dashboard-grid {{
  display: grid;
  gap: 12px;
  height: 100%;
}}

/* ── Widget base ── */
.widget {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}}
.widget-empty {{
  background: var(--bg-panel);
  border: 1px dashed var(--border);
}}
.widget-title {{
  font-size: 12px;
  font-weight: 600;
  color: var(--text-sec);
  text-transform: uppercase;
  letter-spacing: .5px;
  margin-bottom: 10px;
  flex-shrink: 0;
}}

/* ── KPI ── */
.kpi-widget {{ align-items: center; justify-content: center; text-align: center; }}
.kpi-value  {{ font-weight: 800; line-height: 1.1; }}
.kpi-sub    {{ font-size: 11px; color: var(--text-mut); margin-top: 6px; }}

/* ── Chart ── */
.chart-widget {{ }}
.chart-wrap   {{ flex: 1; min-height: 0; display:flex; align-items:stretch; }}
.chart-wrap svg {{ width:100%; height:100%; display:block; overflow:visible; }}

/* ── Table ── */
.table-wrap  {{ flex:1; overflow:auto; }}
table        {{ width:100%; border-collapse:collapse; font-size:12px; }}
th           {{ background:var(--bg-panel); color:var(--text-mut); font-weight:600;
               padding:7px 10px; text-align:left; position:sticky; top:0;
               border-bottom:1px solid var(--border); font-size:11px; text-transform:uppercase; }}
td           {{ padding:7px 10px; color:var(--text-pri); border-bottom:1px solid var(--bg-panel); }}
.row-even    {{ background:var(--bg-card); }}
.row-odd     {{ background:var(--bg-hover); }}
tr:hover td  {{ background:var(--bg-hover); }}

/* ── Text ── */
.text-widget {{ justify-content:center; }}
.text-content {{ color:var(--text-pri); line-height:1.7; }}

/* ── Image ── */
.image-wrap {{
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.image-wrap img {{
  display: block;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
}}
.img-placeholder {{ color:var(--text-mut); font-size:32px; }}

/* ── Map ── */
.map-widget {{ padding: 0; }}
.map-widget .widget-title {{ padding: 14px 16px 0; }}
.map-container {{ flex:1; min-height:0; border-radius:0 0 8px 8px; }}

/* Leaflet dark tweaks */
.leaflet-control-zoom a {{ background:var(--bg-panel)!important; color:var(--text-sec)!important; border-color:var(--border)!important; }}
.leaflet-control-zoom a:hover {{ background:var(--bg-hover)!important; color:var(--text-pri)!important; }}
.leaflet-popup-content-wrapper {{ background:var(--bg-panel); border:1px solid var(--border); border-radius:8px; color:var(--text-pri); box-shadow:0 8px 24px rgba(0,0,0,.5); }}
.leaflet-popup-tip {{ background:var(--bg-panel); }}
.leaflet-control-attribution {{ display:none; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:var(--bg-dark); }}
::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:3px; }}
::-webkit-scrollbar-thumb:hover {{ background:var(--border-lt); }}

/* ── Header right ── */
.header-right {{ display:flex; align-items:center; gap:16px; }}
.theme-select {{
  background: var(--bg-card);
  color: var(--text-pri);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  outline: none;
  transition: border-color .15s;
}}
.theme-select:hover {{ border-color: var(--border-lt); }}
.theme-select option {{ background: var(--bg-panel); }}
</style>
</head>
<body>

<header class="app-header">
  <div class="app-logo">⬡ Ecology-BI</div>
  <div class="header-right">
    <select class="theme-select" onchange="applyTheme(this.value)" title="Сменить тему">
      <option value="ocean">🌊 Ocean</option>
      <option value="emerald">🌿 Emerald</option>
      <option value="midnight">🌌 Midnight</option>
      <option value="sunset">🌅 Sunset</option>
      <option value="arctic">❄️ Arctic</option>
      <option value="slate">🔷 Slate</option>
    </select>
    <div class="app-meta">Экспортировано {export_date} · {dash_name}</div>
  </div>
</header>

<nav class="tabs">
  {tab_btns}
</nav>

{tab_panels}

<script>
// ── Переключение вкладок ─────────────────────────────────────────────────────
function switchTab(idx) {{
  document.querySelectorAll('.tab-btn').forEach(function(b,i){{
    b.classList.toggle('active', i===idx);
  }});
  document.querySelectorAll('.tab-panel').forEach(function(p,i){{
    p.classList.toggle('active', i===idx);
    if (i===idx) {{
      setTimeout(function() {{
        document.querySelectorAll('#tab_'+idx+' .map-container').forEach(function(mc){{
          if (mc._leaflet_id) {{
            window.L && L.map(mc) && L.map(mc).invalidateSize();
          }}
        }});
      }}, 50);
    }}
  }});
}}

// ── Темы ─────────────────────────────────────────────────────────────────────
var DASH_THEMES = {{
  ocean:    {{ '--bg-deep':'#060B18','--bg-dark':'#0F172A','--bg-panel':'#1E293B','--bg-card':'#263347','--bg-hover':'#2D3E56','--border':'#334155','--border-lt':'#475569','--accent':'#38BDF8','--text-pri':'#F1F5F9','--text-sec':'#94A3B8','--text-mut':'#64748B' }},
  emerald:  {{ '--bg-deep':'#030d07','--bg-dark':'#081a0f','--bg-panel':'#0e2718','--bg-card':'#153320','--bg-hover':'#1c4229','--border':'#1e5733','--border-lt':'#2d7a47','--accent':'#4ade80','--text-pri':'#f0fdf4','--text-sec':'#86efac','--text-mut':'#4d9966' }},
  midnight: {{ '--bg-deep':'#05030f','--bg-dark':'#0c0a1e','--bg-panel':'#1a1730','--bg-card':'#231f3e','--bg-hover':'#2d2855','--border':'#3b3565','--border-lt':'#524c8a','--accent':'#a78bfa','--text-pri':'#f5f3ff','--text-sec':'#c4b5fd','--text-mut':'#7c6fcd' }},
  sunset:   {{ '--bg-deep':'#0f0400','--bg-dark':'#1a0800','--bg-panel':'#2a1200','--bg-card':'#391a00','--bg-hover':'#4a2200','--border':'#7c3a00','--border-lt':'#a35000','--accent':'#fb923c','--text-pri':'#fff7ed','--text-sec':'#fed7aa','--text-mut':'#c2670f' }},
  arctic:   {{ '--bg-deep':'#dde8f5','--bg-dark':'#edf3fb','--bg-panel':'#dce8f5','--bg-card':'#ffffff','--bg-hover':'#d0e4f5','--border':'#b8cfe8','--border-lt':'#90b5d8','--accent':'#0284c7','--text-pri':'#0f172a','--text-sec':'#1e3a5f','--text-mut':'#475569' }},
  slate:    {{ '--bg-deep':'#0a0e1a','--bg-dark':'#111827','--bg-panel':'#1f2937','--bg-card':'#283444','--bg-hover':'#374151','--border':'#374151','--border-lt':'#4b5563','--accent':'#60a5fa','--text-pri':'#f9fafb','--text-sec':'#9ca3af','--text-mut':'#6b7280' }}
}};

function applyTheme(name) {{
  var t = DASH_THEMES[name];
  if (!t) return;
  var root = document.documentElement;
  for (var k in t) root.style.setProperty(k, t[k]);
  // Обновляем select
  var sel = document.querySelector('.theme-select');
  if (sel) sel.value = name;
  try {{ localStorage.setItem('ecbi-theme', name); }} catch(e) {{}}
}}

// Применить тему по умолчанию (из экспорта) или сохранённую
(function() {{
  var saved = null;
  try {{ saved = localStorage.getItem('ecbi-theme'); }} catch(e) {{}}
  applyTheme(saved || '{theme_name}');
}})();
</script>

</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    if open_browser:
        webbrowser.open(f'file:///{os.path.abspath(output_path).replace(os.sep, "/")}')

    return output_path
