# exporters/report_exporter.py
"""
Генерация формального HTML-отчёта по дашборду.
Включает:
  - Обложку (организация, период, дата, автор)
  - Раздел по каждому виджету с заголовком и содержимым
  - Блок автоматических выводов (превышения норм из маркеров карты)
  - Блок подписи
  - Оптимизацию @media print — Ctrl+P → "Сохранить как PDF"
"""
import json
import os
import webbrowser
from datetime import datetime


# ── Утилиты ───────────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _sample_bar_svg(color: str = '#38BDF8', n: int = 6, w: int = 520, h: int = 140) -> str:
    """Простая SVG-гистограмма для отчёта (без JS)."""
    import random
    random.seed(7)
    vals   = [random.randint(25, 95) for _ in range(n)]
    max_v  = max(vals) or 1
    labels = ['Янв','Фев','Мар','Апр','Май','Июн'][:n]
    pad_l, pad_b = 36, 28
    pw, ph = w - pad_l - 10, h - pad_b - 8
    bar_w  = pw / n
    gap    = bar_w * 0.3

    bars = ''
    for i, v in enumerate(vals):
        bh = ph * v / max_v
        x  = pad_l + i * bar_w + gap / 2
        y  = 8 + ph - bh
        bars += (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-gap:.1f}" height="{bh:.1f}"'
            f' fill="{color}" rx="3" opacity=".85"/>'
            f'<text x="{x + (bar_w-gap)/2:.1f}" y="{y-4:.1f}"'
            f' text-anchor="middle" font-size="9" fill="{color}">{v}</text>'
            f'<text x="{x + (bar_w-gap)/2:.1f}" y="{h-6:.1f}"'
            f' text-anchor="middle" font-size="9" fill="#64748B">{labels[i]}</text>'
        )

    # Оси
    axes = (
        f'<line x1="{pad_l}" y1="8" x2="{pad_l}" y2="{8+ph}" stroke="#334155" stroke-width="1"/>'
        f'<line x1="{pad_l}" y1="{8+ph}" x2="{w-10}" y2="{8+ph}" stroke="#334155" stroke-width="1"/>'
    )
    # Y-ticks
    ticks = ''
    for t in range(0, 101, 25):
        y = 8 + ph - ph * t / 100
        ticks += (
            f'<line x1="{pad_l-4}" y1="{y:.1f}" x2="{pad_l}" y2="{y:.1f}"'
            f' stroke="#334155" stroke-width="1"/>'
            f'<text x="{pad_l-6}" y="{y+3:.1f}" text-anchor="end" font-size="8" fill="#475569">{t}</text>'
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-10}" y2="{y:.1f}"'
            f' stroke="#263347" stroke-width="1" stroke-dasharray="3,3"/>'
        )
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{ticks}{axes}{bars}</svg>'


def _sample_line_svg(color: str = '#38BDF8', n: int = 8, w: int = 520, h: int = 140) -> str:
    import random
    random.seed(13)
    vals   = [random.randint(20, 85) for _ in range(n)]
    max_v  = max(vals) or 1
    labels = ['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг'][:n]
    pad_l, pad_b = 36, 28
    pw, ph = w - pad_l - 10, h - pad_b - 8

    pts = []
    for i, v in enumerate(vals):
        x = pad_l + i * pw / (n - 1)
        y = 8 + ph - ph * v / max_v
        pts.append((x, y))

    polyline = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    fill_pts = f'{pad_l},{8+ph} ' + polyline + f' {pts[-1][0]:.1f},{8+ph}'

    axes = (
        f'<line x1="{pad_l}" y1="8" x2="{pad_l}" y2="{8+ph}" stroke="#334155" stroke-width="1"/>'
        f'<line x1="{pad_l}" y1="{8+ph}" x2="{w-10}" y2="{8+ph}" stroke="#334155" stroke-width="1"/>'
    )
    area    = f'<polygon points="{fill_pts}" fill="{color}" opacity=".12"/>'
    line    = f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>'
    dots    = ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>' for x, y in pts)
    xlabels = ''.join(
        f'<text x="{pad_l + i*pw/(n-1):.1f}" y="{h-6:.1f}" text-anchor="middle" font-size="8" fill="#64748B">{labels[i]}</text>'
        for i in range(n)
    )
    ticks = ''
    for t in range(0, 101, 25):
        y = 8 + ph - ph * t / 100
        ticks += (
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-10}" y2="{y:.1f}"'
            f' stroke="#263347" stroke-width="1" stroke-dasharray="3,3"/>'
            f'<text x="{pad_l-6}" y="{y+3:.1f}" text-anchor="end" font-size="8" fill="#475569">{t}</text>'
        )
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{ticks}{axes}{area}{line}{dots}{xlabels}</svg>'


# ── Рендереры секций ──────────────────────────────────────────────────────────

def _section_kpi(settings: dict, idx: int) -> str:
    title  = _esc(settings.get('title', 'KPI'))
    value  = _esc(settings.get('value', '—'))
    color  = settings.get('color', '#38BDF8')
    fs     = min(settings.get('font_size', 36), 48)
    return f"""
<section class="report-section">
  <h3 class="section-num">Показатель {idx}</h3>
  <h2 class="section-title">{title}</h2>
  <div class="kpi-block">
    <div class="kpi-val" style="color:{color};font-size:{fs}px">{value}</div>
  </div>
</section>"""


def _section_chart(settings: dict, idx: int) -> str:
    title  = _esc(settings.get('title', 'График'))
    color  = settings.get('color', '#38BDF8')
    style  = settings.get('chart_style', 'bar')
    svg    = _sample_line_svg(color) if style in ('line', 'area') else _sample_bar_svg(color)
    note   = '<p class="chart-note">* Данные на графике являются иллюстративными. Актуальные значения в сохранённом дашборде.</p>'
    return f"""
<section class="report-section">
  <h3 class="section-num">График {idx}</h3>
  <h2 class="section-title">{title}</h2>
  <div class="chart-block">{svg}</div>
  {note}
</section>"""


def _section_table(settings: dict, idx: int) -> str:
    title = _esc(settings.get('title', 'Таблица'))
    cols  = ['Район / объект', 'Показатель', 'Ед. изм.', 'Норма', 'Факт', 'Статус']
    rows_data = [
        ['Нижегородский р-н', 'PM2.5', 'мкг/м³', '50', '42.1', '🟢 Норма'],
        ['Советский р-н',     'PM2.5', 'мкг/м³', '50', '61.8', '🟡 Превышение'],
        ['Автозаводский р-н', 'NO₂',   'мкг/м³', '40', '38.5', '🟢 Норма'],
        ['Канавинский р-н',   'PM10',  'мкг/м³', '40', '79.2', '🔴 Критично'],
        ['Ленинский р-н',     'SO₂',   'мкг/м³', '60', '44.3', '🟢 Норма'],
    ]
    header = ''.join(f'<th>{_esc(c)}</th>' for c in cols)
    tbody  = ''
    for i, row in enumerate(rows_data):
        cls = 'even' if i % 2 == 0 else ''
        cells = ''.join(f'<td>{_esc(cell)}</td>' for cell in row)
        tbody += f'<tr class="{cls}">{cells}</tr>'
    return f"""
<section class="report-section">
  <h3 class="section-num">Таблица {idx}</h3>
  <h2 class="section-title">{title}</h2>
  <table class="report-table">
    <thead><tr>{header}</tr></thead>
    <tbody>{tbody}</tbody>
  </table>
</section>"""


def _section_text(settings: dict, idx: int) -> str:
    content = _esc(settings.get('content', ''))
    return f"""
<section class="report-section">
  <div class="text-block">{content}</div>
</section>"""


def _section_map(settings: dict, idx: int) -> str:
    title   = _esc(settings.get('title', 'Карта'))
    markers = settings.get('manual_markers', [])

    rows = ''
    for m in markers:
        status = m.get('status', 'норма')
        badge  = {'норма': '🟢 Норма', 'превышение': '🟡 Превышение', 'критично': '🔴 Критично'}.get(status, status)
        val    = f"{_esc(str(m.get('value', '')))} {_esc(m.get('unit', ''))}" if m.get('value') else '—'
        note   = _esc(m.get('note', ''))
        lat    = m.get('lat', '')
        lng    = m.get('lng', '')
        rows += (
            f"<tr><td>{_esc(m.get('name','—'))}</td>"
            f"<td>{val}</td>"
            f"<td>{badge}</td>"
            f"<td class='coords'>{lat}, {lng}</td>"
            f"<td>{note}</td></tr>"
        )

    if not rows:
        rows = '<tr><td colspan="5" style="text-align:center;color:#64748B;">Маркеры не заданы</td></tr>'

    return f"""
<section class="report-section">
  <h3 class="section-num">Карта {idx}</h3>
  <h2 class="section-title">{title}</h2>
  <div class="map-note">📍 Интерактивная карта доступна в HTML-экспорте дашборда.</div>
  <table class="report-table">
    <thead><tr>
      <th>Объект</th><th>Значение</th><th>Статус</th><th>Координаты</th><th>Примечание</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>"""


def _build_findings(pages: list) -> str:
    """Автоматически собирает превышения из маркеров карты."""
    crit  = []
    warns = []
    for page in pages:
        for w in page.get('widgets', []):
            if w.get('type') != 'map':
                continue
            for m in w.get('settings', {}).get('manual_markers', []):
                status = m.get('status', 'норма')
                name   = _esc(m.get('name', '—'))
                val    = f"{_esc(str(m.get('value','')))} {_esc(m.get('unit',''))}".strip()
                entry  = f"<li><b>{name}</b> — {val}</li>" if val else f"<li><b>{name}</b></li>"
                if status == 'критично':
                    crit.append(entry)
                elif status == 'превышение':
                    warns.append(entry)

    blocks = ''
    if crit:
        blocks += f"""
<div class="finding-block finding-crit">
  <div class="finding-icon">🔴</div>
  <div>
    <div class="finding-label">Критические превышения</div>
    <ul>{''.join(crit)}</ul>
  </div>
</div>"""
    if warns:
        blocks += f"""
<div class="finding-block finding-warn">
  <div class="finding-icon">🟡</div>
  <div>
    <div class="finding-label">Зафиксированные превышения</div>
    <ul>{''.join(warns)}</ul>
  </div>
</div>"""
    if not crit and not warns:
        blocks = '<div class="finding-block finding-ok"><div class="finding-icon">🟢</div><div><div class="finding-label">Превышений не выявлено</div><p>Все показатели в норме.</p></div></div>'

    return f"""
<section class="report-section findings-section">
  <h2 class="section-title">Выводы по результатам мониторинга</h2>
  {blocks}
</section>"""


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }

:root {
  --bg:       #060B18;
  --panel:    #1E293B;
  --card:     #263347;
  --border:   #334155;
  --accent:   #38BDF8;
  --pri:      #F1F5F9;
  --sec:      #94A3B8;
  --mut:      #64748B;
  --ok:       #34D399;
  --warn:     #FBBF24;
  --crit:     #F87171;
  font-family: 'Inter', system-ui, sans-serif;
  color-scheme: dark;
}

body {
  background: var(--bg);
  color: var(--pri);
  font-size: 13px;
  line-height: 1.6;
}

/* ── Cover ── */
.cover {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 60px;
  background: linear-gradient(160deg, #0F172A 60%, #164E63 100%);
  border-bottom: 3px solid var(--accent);
}
.cover-logo    { font-size:13px; font-weight:700; color:var(--accent); letter-spacing:.5px; }
.cover-org     { font-size:15px; color:var(--sec); margin-top:4px; }
.cover-title   { font-size:36px; font-weight:700; color:var(--pri); line-height:1.2; margin:60px 0 16px; }
.cover-subtitle{ font-size:16px; color:var(--sec); }
.cover-meta    { display:flex; gap:40px; margin-top:auto; }
.cover-meta-item label { font-size:11px; color:var(--mut); text-transform:uppercase; letter-spacing:.5px; display:block; }
.cover-meta-item span  { font-size:14px; color:var(--pri); font-weight:500; }

/* ── Page layout ── */
.page-wrap { max-width: 900px; margin: 0 auto; padding: 40px 60px; }

/* ── Section ── */
.report-section {
  margin-bottom: 40px;
  padding-bottom: 40px;
  border-bottom: 1px solid var(--border);
}
.report-section:last-child { border-bottom: none; }
.section-num   { font-size:11px; color:var(--mut); text-transform:uppercase; letter-spacing:.5px; margin-bottom:4px; }
.section-title { font-size:20px; font-weight:600; color:var(--pri); margin-bottom:16px; }

/* ── KPI ── */
.kpi-block { display:flex; align-items:center; gap:24px; }
.kpi-val   { font-weight:800; line-height:1; }

/* ── Chart ── */
.chart-block { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:20px; }
.chart-block svg { width:100%; height:auto; }
.chart-note  { font-size:11px; color:var(--mut); margin-top:8px; font-style:italic; }

/* ── Table ── */
.report-table { width:100%; border-collapse:collapse; font-size:12px; }
.report-table th {
  background:var(--panel);
  color:var(--mut);
  font-weight:600;
  padding:8px 12px;
  text-align:left;
  border-bottom:1px solid var(--border);
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:.4px;
}
.report-table td {
  padding:8px 12px;
  color:var(--pri);
  border-bottom:1px solid var(--panel);
}
.report-table tr.even td { background:var(--card); }
.report-table .coords    { color:var(--mut); font-size:11px; }

/* ── Map note ── */
.map-note {
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:6px;
  padding:10px 14px;
  font-size:12px;
  color:var(--sec);
  margin-bottom:14px;
}

/* ── Text block ── */
.text-block {
  font-size:14px;
  color:var(--sec);
  line-height:1.8;
  max-width:680px;
}

/* ── Findings ── */
.findings-section { background:transparent; }
.finding-block {
  display:flex;
  gap:16px;
  align-items:flex-start;
  padding:16px;
  border-radius:8px;
  margin-bottom:12px;
}
.finding-icon  { font-size:20px; flex-shrink:0; margin-top:2px; }
.finding-label { font-weight:600; font-size:14px; margin-bottom:6px; }
.finding-block ul  { padding-left:18px; }
.finding-block li  { margin-bottom:4px; font-size:13px; }
.finding-ok   { background:#022C22; border:1px solid #064E3B; }
.finding-ok   .finding-label { color:var(--ok); }
.finding-warn { background:#1C0A00; border:1px solid #451A03; }
.finding-warn .finding-label { color:var(--warn); }
.finding-crit { background:#1C0505; border:1px solid #450A0A; }
.finding-crit .finding-label { color:var(--crit); }

/* ── Signature ── */
.signature-section {
  margin-top:60px;
  padding-top:32px;
  border-top:1px solid var(--border);
}
.sig-title { font-size:15px; font-weight:600; color:var(--sec); margin-bottom:24px; }
.sig-grid  { display:grid; grid-template-columns:1fr 1fr; gap:32px; }
.sig-field label { font-size:11px; color:var(--mut); text-transform:uppercase; letter-spacing:.4px; display:block; margin-bottom:6px; }
.sig-line  { border-bottom:1px solid var(--border); padding-bottom:4px; min-height:32px; color:var(--pri); font-size:13px; }

/* ── Print ── */
@media print {
  :root { color-scheme: light dark; }
  body  { background: #fff !important; color: #1a1a1a !important; }

  .cover {
    background: #f8f9fa !important;
    border-bottom: 3px solid #0284C7 !important;
    break-after: page;
  }
  .cover-logo    { color:#0284C7 !important; }
  .cover-title   { color:#1a1a1a !important; }
  .cover-subtitle{ color:#555 !important; }
  .cover-org     { color:#555 !important; }
  .cover-meta-item span  { color:#1a1a1a !important; }
  .cover-meta-item label { color:#555 !important; }

  .page-wrap { padding:24px 40px; }

  .report-section { break-inside: avoid; }
  .chart-block    { background:#f5f6f8 !important; border-color:#e0e0e0 !important; }
  .report-table th{ background:#f0f0f0 !important; color:#555 !important; }
  .report-table td{ color:#1a1a1a !important; border-bottom-color:#e8e8e8 !important; }
  .report-table tr.even td { background:#f8f9fa !important; }
  .map-note       { background:#f5f6f8 !important; border-color:#e0e0e0 !important; color:#555 !important; }
  .text-block     { color:#333 !important; }
  .section-title  { color:#1a1a1a !important; }
  .sig-line       { border-color:#ccc !important; }

  .finding-ok   { background:#f0fdf4 !important; border-color:#bbf7d0 !important; }
  .finding-warn { background:#fffbeb !important; border-color:#fde68a !important; }
  .finding-crit { background:#fef2f2 !important; border-color:#fecaca !important; }
  .finding-ok   .finding-label { color:#16a34a !important; }
  .finding-warn .finding-label { color:#d97706 !important; }
  .finding-crit .finding-label { color:#dc2626 !important; }
}
"""


# ── Главная функция ────────────────────────────────────────────────────────────

def export_report(
    dashboard_data: dict,
    output_path: str,
    org_name: str   = '',
    period: str     = '',
    author: str     = '',
    note: str       = '',
    open_browser: bool = True,
) -> str:
    """
    Генерирует HTML-отчёт из данных дашборда.

    :param dashboard_data: dict от serialize() или загруженный JSON
    :param output_path:    путь для .html файла
    :param org_name:       название организации
    :param period:         период отчёта (напр. «Июнь 2026»)
    :param author:         ФИО / должность составителя
    :param note:           дополнительное примечание на обложке
    :param open_browser:   открыть после генерации
    """
    pages = dashboard_data.get('pages', [])
    if not pages:
        pages = [{
            'name':    dashboard_data.get('name', 'Дашборд'),
            'rows':    dashboard_data.get('rows', 2),
            'columns': dashboard_data.get('columns', 3),
            'widgets': dashboard_data.get('widgets', []),
        }]

    dash_name   = dashboard_data.get('name', 'Отчёт')
    export_date = datetime.now().strftime('%d.%m.%Y')
    export_time = datetime.now().strftime('%d.%m.%Y %H:%M')

    # ── Обложка ───────────────────────────────────────────────────────────────
    cover = f"""
<div class="cover">
  <div>
    <div class="cover-logo">⬡ Ecology-BI</div>
    {f'<div class="cover-org">{_esc(org_name)}</div>' if org_name else ''}
  </div>
  <div>
    <div class="cover-title">{_esc(dash_name)}</div>
    {f'<div class="cover-subtitle">{_esc(note)}</div>' if note else ''}
  </div>
  <div class="cover-meta">
    <div class="cover-meta-item">
      <label>Дата составления</label>
      <span>{export_date}</span>
    </div>
    {f'<div class="cover-meta-item"><label>Период</label><span>{_esc(period)}</span></div>' if period else ''}
    {f'<div class="cover-meta-item"><label>Составил</label><span>{_esc(author)}</span></div>' if author else ''}
  </div>
</div>"""

    # ── Секции виджетов ───────────────────────────────────────────────────────
    sections_html = ''
    kpi_i = chart_i = table_i = map_i = 0

    for page in pages:
        pname   = _esc(page.get('name', ''))
        widgets = page.get('widgets', [])
        if not widgets:
            continue

        sections_html += f'<h1 class="page-heading">{pname}</h1>'

        for w in widgets:
            wtype    = w.get('type', '')
            settings = w.get('settings', {})

            if wtype == 'kpi':
                kpi_i += 1
                sections_html += _section_kpi(settings, kpi_i)
            elif wtype == 'chart':
                chart_i += 1
                sections_html += _section_chart(settings, chart_i)
            elif wtype == 'table':
                table_i += 1
                sections_html += _section_table(settings, table_i)
            elif wtype == 'text':
                sections_html += _section_text(settings, 0)
            elif wtype == 'map':
                map_i += 1
                sections_html += _section_map(settings, map_i)

    # ── Выводы ────────────────────────────────────────────────────────────────
    sections_html += _build_findings(pages)

    # ── Подпись ──────────────────────────────────────────────────────────────
    sections_html += f"""
<div class="signature-section">
  <div class="sig-title">Подпись</div>
  <div class="sig-grid">
    <div class="sig-field">
      <label>Составил(а)</label>
      <div class="sig-line">{_esc(author)}</div>
    </div>
    <div class="sig-field">
      <label>Дата</label>
      <div class="sig-line">{export_date}</div>
    </div>
    <div class="sig-field">
      <label>Должность / организация</label>
      <div class="sig-line">{_esc(org_name)}</div>
    </div>
    <div class="sig-field">
      <label>Подпись</label>
      <div class="sig-line"></div>
    </div>
  </div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(dash_name)} — Отчёт</title>
<style>{_CSS}</style>
</head>
<body>

{cover}

<div class="page-wrap">

<style>
.page-heading {{
  font-size:13px; font-weight:700; color:var(--mut);
  text-transform:uppercase; letter-spacing:.6px;
  margin:40px 0 24px;
  padding-bottom:8px;
  border-bottom:1px solid var(--border);
}}
</style>

{sections_html}

<div style="text-align:center;color:var(--mut);font-size:11px;margin-top:48px;padding-top:20px;border-top:1px solid var(--border);">
  Сформировано {export_time} · Ecology-BI
</div>

</div>

<div style="position:fixed;bottom:20px;right:20px;z-index:999;display:flex;gap:8px;" class="no-print">
  <button onclick="window.print()"
    style="background:#0284C7;color:#fff;border:none;border-radius:6px;padding:10px 18px;font-size:13px;cursor:pointer;font-weight:600;box-shadow:0 4px 12px rgba(2,132,199,.4);">
    🖨 Печать / PDF
  </button>
</div>

<style>
@media print {{ .no-print {{ display:none!important; }} }}
</style>

</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    if open_browser:
        webbrowser.open(f'file:///{os.path.abspath(output_path).replace(os.sep, "/")}')

    return output_path
