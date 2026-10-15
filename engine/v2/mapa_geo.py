"""Geografia da peça `mapa` do perfil viral: lê TopoJSON local (us-atlas / world-atlas em ~/projetos/biblioteca-mapas),
projeta em Mercator e devolve caminhos SVG prontos + câmera e pinos já projetados. Sem rede, sem API.

Shot `mapa` (visual JSON):
  "base": "eua" | "mundo" | "brasil" | "brasil-uf" (brasil-uf = 27 estados com nome completo; eua = estados dos EUA + países vizinhos),
  "destaques": [{"nome": "Texas", "at": "deixa"}],          regiões que acendem em âmbar
  "camera": [{"at": "deixa", "centro": [lon, lat], "zoom": 1}],   zoom 1 = enquadra a área toda
  "pinos": [{"lon": -95.98, "lat": 30.4, "txt": "TERAFAB", "at": "deixa", "sub": "...", "sub_at": "deixa"}]
"""
import json
import math
from pathlib import Path

BIB = Path.home() / 'projetos/biblioteca-mapas'
BASES = {
    'eua': [('us-atlas-3.0.1/states-10m.json', 'states', None),
            ('world-atlas-2.0.2/countries-50m.json', 'countries', {'Mexico', 'Canada', 'Cuba', 'Guatemala', 'Belize', 'Bahamas'})],
    'mundo': [('world-atlas-2.0.2/countries-110m.json', 'countries', None)],
    'brasil': [('world-atlas-2.0.2/countries-50m.json', 'countries', None)],
    # brasil-uf (15/10/2026): países vizinhos (world-atlas) + as 27 UFs (GeoJSON local brasil-uf/uf.geojson, nomes completos)
    'brasil-uf': [('world-atlas-2.0.2/countries-50m.json', 'countries', {'Argentina', 'Bolivia', 'Paraguay', 'Uruguay', 'Peru', 'Colombia',
                                                                          'Venezuela', 'Guyana', 'Suriname', 'Chile', 'Ecuador'}),
                  ('brasil-uf/uf.geojson', 'geojson', None)],
}
EXTENT = {'eua': (-127, 22, -64, 51), 'mundo': (-180, -58, 180, 80), 'brasil': (-80, -36, -32, 7), 'brasil-uf': (-80, -36, -32, 7)}
_cache = {}


def _topo(path):
    if path not in _cache:
        _cache[path] = json.loads((BIB / path).read_text())
    return _cache[path]


def _arcs(t):
    tr = t.get('transform')
    out = []
    for arc in t['arcs']:
        x = y = 0
        pts = []
        for p in arc:
            if tr:
                x += p[0]; y += p[1]
                pts.append((x * tr['scale'][0] + tr['translate'][0], y * tr['scale'][1] + tr['translate'][1]))
            else:
                pts.append((p[0], p[1]))
        out.append(pts)
    return out


def _ring(arcs, idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a[1:] if pts else a)
    return pts


def merc(lon, lat):
    lat = max(-85, min(85, lat))
    return lon / 360 + 0.5, 0.5 - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) / (2 * math.pi)


def geo(shot, W, H):
    base = shot.get('base', 'eua')
    lon0, lat0, lon1, lat1 = shot.get('extent', EXTENT[base])
    x0, y1 = merc(lon0, lat0)
    x1, y0 = merc(lon1, lat1)
    s = min(W / (x1 - x0), H / (y1 - y0))          # px por unidade Mercator (zoom 1 = área inteira)
    ox, oy = (W - (x1 - x0) * s) / 2 - x0 * s, (H - (y1 - y0) * s) / 2 - y0 * s
    P = lambda lon, lat: (lambda m: (m[0] * s + ox, m[1] * s + oy))(merc(lon, lat))
    hl = {d['nome'] for d in shot.get('destaques', [])}
    feats, hl_ids = [], set()
    for path, obj, filtro in BASES[base]:
        t = _topo(path)
        if obj == 'geojson':   # anéis já em lon/lat (sem arcos TopoJSON)
            for ft in t['features']:
                nome, gm = ft['properties'].get('name', ''), ft['geometry']
                polys = gm['coordinates'] if gm['type'] == 'MultiPolygon' else [gm['coordinates']]
                d = []
                for poly in polys:
                    for ring in poly:
                        pts, last = [], None
                        for lon, lat in ring:
                            x, y = P(lon, lat)
                            if last and abs(x - last[0]) + abs(y - last[1]) < 1.2:
                                continue
                            pts.append(f'{x:.1f},{y:.1f}'); last = (x, y)
                        if len(pts) > 2:
                            d.append('M' + 'L'.join(pts) + 'Z')
                if d:
                    feats.append({'n': nome, 'd': ''.join(d), 'hl': nome in hl})
            continue
        arcs = _arcs(t)
        for g in t['objects'][obj]['geometries']:
            nome = (g.get('properties') or {}).get('name', '')
            if filtro is not None and nome not in filtro:
                continue
            polys = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']] if g['type'] == 'Polygon' else []
            d = []
            for poly in polys:
                for ring in poly:
                    pts, last = [], None
                    for lon, lat in _ring(arcs, ring):
                        x, y = P(lon, lat)
                        if last and abs(x - last[0]) + abs(y - last[1]) < 1.2:
                            continue
                        pts.append(f'{x:.1f},{y:.1f}'); last = (x, y)
                    if len(pts) > 2:
                        d.append('M' + 'L'.join(pts) + 'Z')
            if d:
                feats.append({'n': nome, 'd': ''.join(d), 'hl': nome in hl})
                if nome in hl and obj == 'states':
                    hl_ids.add(str(g.get('id')))
    # condados do estado destacado (só EUA): linhas finas que dão textura e escala quando a câmera aproxima
    cond = []
    if hl_ids and shot.get('condados', True):
        t = _topo('us-atlas-3.0.1/counties-10m.json')
        arcs = _arcs(t)
        for g in t['objects']['counties']['geometries']:
            if str(g.get('id', ''))[:2] not in hl_ids:
                continue
            polys = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
            for poly in polys:
                pts = [f'{x:.1f},{y:.1f}' for x, y in (P(lon, lat) for lon, lat in _ring(arcs, poly[0]))]
                if len(pts) > 2:
                    cond.append('M' + 'L'.join(pts) + 'Z')
    cam = [{'at': c['at'], 'xy': P(*c['centro']), 'z': c.get('zoom', 1)} for c in shot.get('camera', [])]
    pinos = [dict(p, xy=P(p['lon'], p['lat'])) for p in shot.get('pinos', [])]
    return {'feats': feats, 'cam': cam, 'pinos': pinos, 'cond': ''.join(cond)}
