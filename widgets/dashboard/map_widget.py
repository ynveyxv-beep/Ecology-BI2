# widgets/dashboard/map_widget.py
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QLabel, QSizePolicy
from widgets.dashboard.base_widget import BaseDashboardWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False

_NNO_LAT  = 56.33
_NNO_LON  = 44.00

_VIEW_ZOOM = {
    'point':      14,
    'settlement': 11,
    'district':    9,
    'region':      7,
    'radius':     13,
    'polygon':    13,
}

_STATUS_COLORS = {
    'норма':      '#4caf50',
    'превышение': '#fbbf24',
    'критично':   '#f87171',
}


def _icon_js(style: str, color: str) -> str:
    """
    Возвращает JS-выражение L.divIcon.
    ВАЖНО: HTML внутри использует одинарные кавычки, чтобы не конфликтовать
    с внешними двойными кавычками JS-строки.
    """
    c = color or '#4caf50'

    if style == 'circle':
        h = (f"<div style='width:16px;height:16px;border:3px solid {c};"
             f"border-radius:50%;box-shadow:0 0 5px {c}77;"
             f"background:transparent;'></div>")
        sz, an = '[16,16]', '[8,8]'
    elif style == 'pulse':
        h = (f"<div style='position:relative;width:22px;height:22px;'>"
             f"<div style='position:absolute;inset:7px;background:{c};"
             f"border-radius:50%;'></div>"
             f"<div style='position:absolute;inset:0;border-radius:50%;"
             f"border:2px solid {c};"
             f"animation:pulseRing 1.6s ease-out infinite;'></div></div>")
        sz, an = '[22,22]', '[11,11]'
    elif style == 'star':
        h = (f"<div style='font-size:20px;line-height:1;color:{c};"
             f"text-shadow:0 0 6px {c}99;'>&#9733;</div>")
        sz, an = '[20,20]', '[10,10]'
    elif style == 'flag':
        h = (f"<div style='position:relative;width:14px;height:20px;'>"
             f"<div style='position:absolute;left:0;top:0;width:2px;"
             f"height:20px;background:{c};'></div>"
             f"<div style='position:absolute;left:2px;top:0;width:12px;"
             f"height:10px;background:{c};"
             f"clip-path:polygon(0 0,100% 40%,0 80%);'></div></div>")
        sz, an = '[14,20]', '[1,20]'
    elif style == 'dot':
        h = (f"<div style='width:8px;height:8px;background:{c};"
             f"border-radius:50%;border:1.5px solid #fff;"
             f"box-shadow:0 0 3px {c}88;'></div>")
        sz, an = '[8,8]', '[4,4]'
    else:  # pin (default)
        h = (f"<div style='width:14px;height:14px;background:{c};"
             f"border:2px solid #fff;border-radius:50%;"
             f"box-shadow:0 0 7px {c}cc;'></div>")
        sz, an = '[14,14]', '[7,7]'

    # Экранируем одинарные кавычки для передачи в JS-строку с одинарными кавычками
    h_esc = h.replace("'", "\\'")
    return (f"L.divIcon({{className:'',html:'{h_esc}',"
            f"iconSize:{sz},iconAnchor:{an},popupAnchor:[0,-12]}})")


def _popup_html(m: dict) -> str:
    """Строит HTML содержимого всплывающего окна маркера."""
    name   = m.get('name', '')
    value  = m.get('value', '')
    unit   = m.get('unit', '')
    note   = m.get('note', '')
    status = m.get('status', 'норма')
    sc     = _STATUS_COLORS.get(status, '#4caf50')

    parts = []
    if name:
        parts.append(f"<b style='font-size:13px;'>{name}</b>")
    if value:
        v_str = f"{value} {unit}".strip()
        parts.append(f"<div style='margin-top:3px;font-size:12px;color:{sc};'>{v_str}</div>")
    if note:
        parts.append(f"<div style='margin-top:4px;font-size:11px;color:#aaa;'>{note}</div>")
    if not parts:
        return ''
    return '<br>'.join(parts)


def _build_map_html(markers=None, territories=None, editable=False,
                    view_mode='point', area_radius=1000,
                    default_label_mode='name',
                    default_icon='pin', default_color='#4caf50',
                    # legacy compat
                    lat=None, lon=None, address_label='',
                    **_kw):
    """Строит полный Leaflet HTML."""

    # ── Нормализуем маркеры ──────────────────────────────────────────────────
    all_markers = []

    # Новый формат: список маркеров с полными данными
    for m in (markers or []):
        mlat = m.get('lat')
        mlon = m.get('lon') or m.get('lng')
        if mlat is not None and mlon is not None:
            all_markers.append(dict(m, lon=mlon))

    # Legacy: одиночный lat/lon
    if not all_markers and lat is not None and lon is not None:
        all_markers.append({
            'name':       address_label,
            'lat':        lat,
            'lon':        lon,
            'label_mode': default_label_mode,
            'icon':       default_icon,
            'color':      default_color,
        })

    # ── Центр и зум ──────────────────────────────────────────────────────────
    zoom = _VIEW_ZOOM.get(view_mode, 14)
    if all_markers:
        center_lat = all_markers[0]['lat']
        center_lon = all_markers[0]['lon']
    else:
        center_lat, center_lon = _NNO_LAT, _NNO_LON
        zoom = 7

    # ── JS маркеров ───────────────────────────────────────────────────────────
    markers_js = ''
    latlngs_for_fit = []

    for i, m in enumerate(all_markers):
        mlat  = m['lat']
        mlon  = m['lon']
        color = m.get('color', default_color) or default_color
        icon  = m.get('icon', default_icon) or default_icon
        lmode = m.get('label_mode', default_label_mode) or default_label_mode

        icon_expr = _icon_js(icon, color)

        if lmode == 'coords':
            popup_text = f'{mlat:.5f}, {mlon:.5f}'
            popup_html_str = f"<b>{popup_text}</b>"
        elif lmode == 'none':
            popup_html_str = ''
        else:
            popup_html_str = _popup_html(m)

        # Escape for JS string
        safe_popup = (popup_html_str
                      .replace('\\', '\\\\')
                      .replace("'", "\\'")
                      .replace('\n', ''))

        if popup_html_str:
            open_pop = '.openPopup()' if (i == 0 and len(all_markers) == 1) else ''
            markers_js += (
                f"L.marker([{mlat},{mlon}],{{icon:{icon_expr}}})"
                f".addTo(map).bindPopup('{safe_popup}'){open_pop};\n"
            )
        else:
            markers_js += f"L.marker([{mlat},{mlon}],{{icon:{icon_expr}}}).addTo(map);\n"

        latlngs_for_fit.append(f"[{mlat},{mlon}]")

        # Радиус зоны вокруг маркера
        radius = int(m.get('radius', 0))
        if radius > 0:
            r_color = f"'{color}'"
            markers_js += (
                f"L.circle([{mlat},{mlon}],"
                f"{{radius:{radius},color:{r_color},fillColor:{r_color},"
                f"fillOpacity:0.07,weight:1.5,dashArray:'6,4'}}).addTo(map);\n"
            )

    # Auto-fit если несколько маркеров
    fit_js = ''
    if len(all_markers) > 1:
        fit_js = (
            f"map.fitBounds([{','.join(latlngs_for_fit)}],"
            f"{{padding:[30,30],maxZoom:{zoom}}});\n"
        )

    # ── Подсветка области по виду карты ──────────────────────────────────────
    area_js = ''
    if all_markers and view_mode in ('settlement', 'district', 'region', 'radius', 'polygon'):
        clat = all_markers[0]['lat']
        clon = all_markers[0]['lon']
        clr  = "'#4caf50'"
        opts = "color:{c},fillColor:{c},fillOpacity:0.07,weight:1.5,dashArray:'6,5'".replace('{c}', clr)
        if view_mode == 'settlement':
            area_js = f"L.circle([{clat},{clon}],{{radius:2000,{opts}}}).addTo(map);\n"
        elif view_mode == 'district':
            area_js = f"L.circle([{clat},{clon}],{{radius:20000,{opts}}}).addTo(map);\n"
        elif view_mode == 'region':
            # Приближённый контур Нижегородской области
            nno = ("[58.85,44.30],[58.60,45.80],[58.20,46.60],[57.50,47.10],"
                   "[56.90,47.20],[56.30,46.80],[55.80,46.40],[55.30,46.00],"
                   "[54.90,45.20],[54.70,44.20],[54.65,43.30],[54.90,42.50],"
                   "[55.30,42.00],[55.80,41.90],[56.30,42.20],[56.80,42.30],"
                   "[57.30,42.80],[57.80,43.30],[58.30,43.80],[58.85,44.30]")
            area_js = (f"L.polygon([{nno}],"
                       f"{{color:{clr},fillColor:{clr},fillOpacity:0.07,"
                       f"weight:2,dashArray:'7,5'}}).addTo(map);\n")
        elif view_mode == 'radius':
            r = max(1, int(area_radius))
            area_js = (
                f"L.circle([{clat},{clon}],"
                f"{{radius:{r},color:{clr},fillColor:{clr},"
                f"fillOpacity:0.10,weight:2,dashArray:'7,4'}}).addTo(map);\n"
            )
        # 'polygon' — территории рисуются через territories_js ниже

    # ── Территории ───────────────────────────────────────────────────────────
    territories_js = 'var drawnItems = new L.FeatureGroup().addTo(map);\n'
    for poly in (territories or []):
        if not poly:
            continue
        coords = ', '.join(f'[{p["lat"]},{p["lon"]}]' for p in poly if 'lat' in p)
        if coords:
            territories_js += (
                f"L.polygon([{coords}],"
                f"{{color:'#4caf50',fillColor:'#4caf50',fillOpacity:0.18,weight:2}})"
                f".addTo(drawnItems);\n"
            )

    # ── Leaflet.draw ─────────────────────────────────────────────────────────
    draw_css = draw_script = draw_init = ''
    toolbar_html = ''
    if editable:
        draw_css = (
            '<link rel="stylesheet" href="'
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css"/>'
        )
        draw_script = (
            '<script src="'
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>'
        )
        draw_init = """
  var drawControl = new L.Control.Draw({
    edit: { featureGroup: drawnItems },
    draw: {
      polygon:      { allowIntersection:false, showArea:true,
                      shapeOptions:{color:'#4caf50',fillOpacity:0.18} },
      rectangle:    { shapeOptions:{color:'#4caf50',fillOpacity:0.18} },
      polyline:false, circle:false, circlemarker:false, marker:false
    }
  });
  map.addControl(drawControl);
  window._drawnPolygons = [];
  function _syncPoly(){
    window._drawnPolygons=[];
    drawnItems.eachLayer(function(l){
      if(l.getLatLngs){
        var r=l.getLatLngs()[0];
        window._drawnPolygons.push(r.map(function(ll){return{lat:ll.lat,lon:ll.lng};}));
      }
    });
  }
  map.on(L.Draw.Event.CREATED,function(e){drawnItems.addLayer(e.layer);_syncPoly();});
  map.on(L.Draw.Event.EDITED,_syncPoly);
  map.on(L.Draw.Event.DELETED,_syncPoly);

  // ── Click-to-polygon Leaflet Control ─────────────────────────────────────
  var _clickMode = false;
  var _clickPoints = [];
  var _clickDots = [];
  var _previewLine = null;
  var _previewPoly = null;
  var _dblClickTimer = null;
  var _cpBtnMain, _cpBtnFinish, _cpBtnCancel, _cpHint;

  var ClickPolyControl = L.Control.extend({
    options: { position: 'topright' },
    onAdd: function(m) {
      var div = L.DomUtil.create('div','');
      div.style.cssText = 'display:flex;flex-direction:column;gap:5px;pointer-events:auto;';
      L.DomEvent.disableClickPropagation(div);
      L.DomEvent.disableScrollPropagation(div);

      _cpBtnMain = L.DomUtil.create('button','',div);
      _cpBtnMain.textContent = '✏ Выделение по точкам';
      _cpBtnMain.style.cssText = (
        'background:#1e2d1e;border:1px solid #4caf50;color:#4caf50;'
        'border-radius:6px;padding:6px 12px;font-size:12px;cursor:pointer;'
        'font-weight:600;white-space:nowrap;font-family:sans-serif;'
      );
      L.DomEvent.on(_cpBtnMain,'click',toggleClickMode);

      _cpBtnFinish = L.DomUtil.create('button','',div);
      _cpBtnFinish.textContent = '✓ Завершить';
      _cpBtnFinish.style.cssText = (
        'display:none;background:#1a3a1a;border:1px solid #4caf50;color:#86efac;'
        'border-radius:6px;padding:5px 12px;font-size:11px;cursor:pointer;font-family:sans-serif;'
      );
      L.DomEvent.on(_cpBtnFinish,'click',finishClickPolygon);

      _cpBtnCancel = L.DomUtil.create('button','',div);
      _cpBtnCancel.textContent = '✕ Отмена';
      _cpBtnCancel.style.cssText = (
        'display:none;background:#2d1e1e;border:1px solid #f87171;color:#f87171;'
        'border-radius:6px;padding:5px 12px;font-size:11px;cursor:pointer;font-family:sans-serif;'
      );
      L.DomEvent.on(_cpBtnCancel,'click',cancelClickMode);

      _cpHint = L.DomUtil.create('div','',div);
      _cpHint.innerHTML = 'Кликайте на карте.<br>Двойной клик &mdash; замкнуть.';
      _cpHint.style.cssText = (
        'display:none;background:rgba(17,27,17,0.88);border:1px solid #2d3d2d;'
        'border-radius:5px;padding:4px 8px;font-size:10px;color:#6b8c6b;'
        'text-align:center;font-family:sans-serif;'
      );
      return div;
    }
  });
  map.addControl(new ClickPolyControl());

  function toggleClickMode(){
    if(_clickMode){ cancelClickMode(); return; }
    _clickMode = true;
    _clickPoints = [];
    _cpBtnMain.textContent = '✏ Режим активен';
    _cpBtnMain.style.background = '#2a4a2a';
    _cpBtnFinish.style.display = 'block';
    _cpBtnCancel.style.display = 'block';
    _cpHint.style.display = 'block';
    map.on('click', _onClickMapPoint);
    map.on('dblclick', _onDblClick);
    map.doubleClickZoom.disable();
  }

  function _onClickMapPoint(e){
    if(!_clickMode) return;
    if(_dblClickTimer){ return; }
    _dblClickTimer = setTimeout(function(){ _dblClickTimer = null; }, 300);
    var ll = e.latlng;
    _clickPoints.push([ll.lat, ll.lng]);
    var dot = L.circleMarker([ll.lat, ll.lng],{
      radius:5,color:'#4caf50',fillColor:'#4caf50',fillOpacity:0.9,weight:2
    }).addTo(map);
    _clickDots.push(dot);
    _updatePreview();
  }

  function _onDblClick(e){
    clearTimeout(_dblClickTimer);
    _dblClickTimer = null;
    if(_clickPoints.length > 0){
      _clickPoints.pop();
      var last = _clickDots.pop();
      if(last) map.removeLayer(last);
    }
    if(_clickPoints.length >= 3){ finishClickPolygon(); }
  }

  function _updatePreview(){
    if(_previewLine){ map.removeLayer(_previewLine); _previewLine=null; }
    if(_previewPoly){ map.removeLayer(_previewPoly); _previewPoly=null; }
    if(_clickPoints.length < 2) return;
    if(_clickPoints.length === 2){
      _previewLine = L.polyline(_clickPoints,{
        color:'#4caf50',weight:2,dashArray:'5,4',opacity:0.7
      }).addTo(map);
    } else {
      _previewPoly = L.polygon(_clickPoints,{
        color:'#4caf50',fillColor:'#4caf50',fillOpacity:0.10,weight:2,dashArray:'5,4'
      }).addTo(map);
    }
  }

  function finishClickPolygon(){
    if(!_clickMode) return;
    if(_clickPoints.length < 3){
      _cpHint.textContent = '⚠ Нужно минимум 3 точки';
      return;
    }
    L.polygon(_clickPoints,{
      color:'#4caf50',fillColor:'#4caf50',fillOpacity:0.18,weight:2
    }).addTo(drawnItems);
    _syncPoly();
    cancelClickMode();
  }

  function cancelClickMode(){
    _clickMode = false;
    map.off('click', _onClickMapPoint);
    map.off('dblclick', _onDblClick);
    map.doubleClickZoom.enable();
    _clickPoints = [];
    _clickDots.forEach(function(d){ map.removeLayer(d); });
    _clickDots = [];
    if(_previewLine){ map.removeLayer(_previewLine); _previewLine=null; }
    if(_previewPoly){ map.removeLayer(_previewPoly); _previewPoly=null; }
    _cpBtnMain.textContent = '✏ Выделение по точкам';
    _cpBtnMain.style.background = '#1e2d1e';
    _cpBtnFinish.style.display = 'none';
    _cpBtnCancel.style.display = 'none';
    _cpHint.style.display = 'none';
    _cpHint.innerHTML = 'Кликайте на карте.<br>Двойной клик &mdash; замкнуть.';
  }
"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
{draw_css}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
{draw_script}
<style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  html,body,#map{{width:100%;height:100%;background:#111b11;}}
  @keyframes pulseRing{{
    0%  {{transform:scale(0.4);opacity:0.9;}}
    80% {{transform:scale(2.2);opacity:0;}}
    100%{{transform:scale(2.2);opacity:0;}}
  }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  var map = L.map('map',{{
    center:[{center_lat},{center_lon}],
    zoom:{zoom},
    zoomControl:true,
    attributionControl:false
  }});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
    {{subdomains:'abcd',maxZoom:19}}).addTo(map);
  {area_js}
  {territories_js}
  {markers_js}
  {fit_js}
  {draw_init}
</script>
</body>
</html>"""


class MapWidget(BaseDashboardWidget):

    def __init__(self, settings: dict = None, parent=None):
        self._view           = None
        self._fallback_label = None
        super().__init__(settings, parent)

        if self._view is None and self._fallback_label is None:
            if _HAS_WEBENGINE:
                self._view = QWebEngineView()
                self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self._view.setMinimumHeight(80)
                self._content_layout.addWidget(self._view)
            else:
                self._fallback_label = QLabel()
                self._fallback_label.setAlignment(Qt.AlignCenter)
                self._fallback_label.setWordWrap(True)
                self._fallback_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self._fallback_label.setTextFormat(Qt.RichText)
                self._content_layout.addWidget(self._fallback_label)

        self._apply_settings()

    def _apply_settings(self):
        if self._view is None and self._fallback_label is None:
            return
        try:
            s = self._settings
            if _HAS_WEBENGINE and self._view is not None:
                html = _build_map_html(
                    markers            = s.get('markers', []),
                    territories        = s.get('territories', []),
                    view_mode          = s.get('view_mode', 'point'),
                    area_radius        = s.get('area_radius', 1000),
                    default_label_mode = s.get('label_mode', 'name'),
                    default_icon       = s.get('icon_style', 'pin'),
                    default_color      = s.get('marker_color', '#4caf50'),
                    # legacy compat
                    lat            = s.get('lat'),
                    lon            = s.get('lon'),
                    address_label  = ', '.join(
                        p for p in [s.get('house',''), s.get('street',''), s.get('city','')] if p
                    ),
                    manual_markers = s.get('manual_markers', []),
                )
                self._view.setHtml(html, QUrl("about:blank"))
            elif self._fallback_label is not None:
                markers = s.get('markers', [])
                n = len(markers)
                if n:
                    body = (f"<div style='font-size:22px;'>📍</div>"
                            f"<div style='font-size:12px;color:#7fb87f;'>{markers[0].get('name','')}</div>"
                            f"<div style='font-size:10px;color:#6b7a8a;margin-top:4px;'>{n} маркер(ов)</div>"
                            f"<div style='font-size:10px;color:#555;margin-top:6px;'>pip install PySide6-WebEngine</div>")
                else:
                    body = "<div style='font-size:22px;'>🗺️</div><div style='font-size:11px;color:#6b7a8a;'>Маркеры не добавлены</div>"
                self._fallback_label.setText(
                    f"<div style='text-align:center;padding:12px;'>{body}</div>"
                )
        except Exception:
            import traceback; traceback.print_exc()

    def refresh(self):
        self._apply_settings()
