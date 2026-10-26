#!/usr/bin/env python3
"""Relieve de contribuciones: convierte el gráfico de contribuciones del último año en
una cordillera (una cresta por día de la semana), con el mismo estilo del perfil.
Lo ejecuta .github/workflows/gusano.yml todos los días. Solo usa la biblioteca estándar."""
import base64, datetime as dt, html, math, os, re, sys, urllib.request

USER = os.environ.get('GH_USER', 'luism7p7')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'dist/relieve.svg'
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'andes', 'fonts')
C = dict(bg='#0C1615', line='#1E302C', contour='#5E8574', contour2='#8DB89C', gold='#E2B04B', gold2='#F0CB7A',
         ivory='#F3ECDD', mut='#A7B5AD', dim='#6F817A')
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
DIAS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb']

def leer(src=None):
    if src:
        page = open(src, encoding='utf-8').read()
    else:
        req = urllib.request.Request(f'https://github.com/users/{USER}/contributions', headers={'User-Agent': 'relieve-script'})
        page = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    dias = {}
    for m in re.finditer(r'<td[^>]*?data-date="(\d{4}-\d\d-\d\d)"[^>]*>', page):
        tag = m.group(0)
        idm = re.search(r'id="([^"]+)"', tag); lv = re.search(r'data-level="(\d)"', tag)
        dias[m.group(1)] = {'id': idm.group(1) if idm else None, 'level': int(lv.group(1)) if lv else 0, 'n': None}
    tips = {t.group(1): t.group(2) for t in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page)}
    for d in dias.values():
        t = tips.get(d['id'] or '', '')
        n = re.match(r'\s*(\d+)', t)
        d['n'] = int(n.group(1)) if n else (0 if 'No contribution' in t else None)
    return dias

def fuente(nombre):
    try:
        return base64.b64encode(open(os.path.join(FONTS, nombre), 'rb').read()).decode()
    except OSError:
        return None

def svg(dias):
    W, H = 1200, 480
    fechas = sorted(dias)
    if not fechas:
        raise SystemExit('No se encontraron contribuciones')
    inicio = dt.date.fromisoformat(fechas[0])
    semanas = (dt.date.fromisoformat(fechas[-1]) - inicio).days // 7 + 1
    tiene_n = any(d['n'] is not None for d in dias.values())
    val = lambda d: (d['n'] if (tiene_n and d['n'] is not None) else d['level'])
    total = sum(d['n'] or 0 for d in dias.values()) if tiene_n else None
    vmax = max(1, max(val(d) for d in dias.values()))
    mejor = max(fechas, key=lambda f: val(dias[f]))
    x0, x1, base0, gap, amp = 140, W - 60, 196, 33, 78
    o = []
    css = ['.r{stroke-dasharray:1;stroke-dashoffset:1;animation:d 2.4s cubic-bezier(.65,0,.35,1) forwards}@keyframes d{to{stroke-dashoffset:0}}',
           '.f{animation:f 1.2s ease both}@keyframes f{from{opacity:0}}',
           '.sc{animation:sc 8s ease-in-out 3s infinite}@keyframes sc{0%{transform:translateX(-300px)}60%,100%{transform:translateX(1500px)}}',
           '.pk{transform-box:fill-box;transform-origin:center;animation:pk 2.6s ease-out infinite}@keyframes pk{from{transform:scale(.4);opacity:.9}to{transform:scale(2.6);opacity:0}}',
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}.r{stroke-dashoffset:0}}']
    ff = ''
    for fam, file, extra in [('Fr', 'fr6.woff2', 'font-weight:600;'), ('In', 'i5.woff2', 'font-weight:500;'), ('In', 'i4.woff2', 'font-weight:400;'), ('Mo', 'm4.woff2', '')]:
        b = fuente(file)
        if b: ff += f"@font-face{{font-family:{fam};{extra}src:url(data:font/woff2;base64,{b}) format('woff2')}}"
    def T(x, y, s, size, fill, cls='', anchor=None, extra=''):
        a = f' text-anchor="{anchor}"' if anchor else ''
        return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" class="{cls}"{a}{extra}>{html.escape(s)}</text>'
    o.append(f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>')
    o.append(T(56, 58, 'ACTIVIDAD EN GITHUB', 12.5, C['gold'], 'b f', extra=' letter-spacing="2.4"'))
    o.append(T(56, 94, 'Relieve de mis contribuciones', 32, C['ivory'], 's f'))
    sub = (f'{total} contribuciones en el último año' if total is not None else 'Último año') + ' · cada cresta es un día de la semana'
    o.append(T(56, 120, sub, 13.5, C['mut'], 'f'))
    picos = []
    # de atrás (domingo) hacia adelante (sábado): cada cresta tapa a la anterior
    for wd in range(7):
        base = base0 + 40 + wd * gap
        pts = []
        for w in range(semanas):
            f = (inicio + dt.timedelta(days=w * 7 + wd)).isoformat()
            v = val(dias[f]) if f in dias else 0
            h = amp * (math.log1p(v) / math.log1p(vmax)) if v else 0
            pts.append((x0 + w * (x1 - x0) / max(1, semanas - 1), base - h, f, v))
        d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
        for i in range(1, len(pts)):
            (xa, ya, *_), (xb, yb, *_) = pts[i - 1], pts[i]
            cx = (xa + xb) / 2
            d += f'C{cx:.1f} {ya:.1f} {cx:.1f} {yb:.1f} {xb:.1f} {yb:.1f}'
        area = d + f'L{x1:.1f} {base+gap+40:.1f}L{x0:.1f} {base+gap+40:.1f}Z'
        op = .45 + .55 * wd / 6
        col = C['contour2'] if wd % 3 == 0 else C['contour']
        o.append(f'<path d="{area}" fill="{C["bg"]}"/>')
        o.append(f'<path d="{d}" pathLength="1" fill="none" stroke="{col}" stroke-width="{1.2 + .25*wd:.2f}" stroke-linejoin="round" opacity="{op:.2f}" class="r" style="animation-delay:{.2 + wd*.22:.2f}s"/>')
        o.append(T(x0 - 14, base + 4, DIAS[wd], 11, C['dim'], 'm f', 'end'))
        picos += [p for p in pts if p[2] == mejor]
    # meses
    m_prev = None
    for w in range(semanas):
        f = inicio + dt.timedelta(days=w * 7)
        if f.month != m_prev and f.day <= 7:
            x = x0 + w * (x1 - x0) / max(1, semanas - 1)
            o.append(T(x, H - 18, MESES[f.month - 1], 11, C['dim'], 'm f'))
            m_prev = f.month
    # pico del año
    if picos and val(dias[mejor]):
        px, py, f, v = picos[0]
        fd = dt.date.fromisoformat(f)
        txt = f'Cumbre del año: {fd.day} {MESES[fd.month-1]} {fd.year}' + (f' · {v} contribuciones' if tiene_n else '')
        o.append(f'<g class="f" style="animation-delay:2.6s"><circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{C["gold"]}"/>'
                 f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="none" stroke="{C["gold"]}" class="pk"/>'
                 f'<line x1="{px:.1f}" y1="{py-8:.1f}" x2="{px:.1f}" y2="{py-34:.1f}" stroke="{C["gold"]}" stroke-width="1"/>'
                 + T(min(px, W - 330), py - 40, txt, 12, C['gold2'], 'md') + '</g>')
    o.append(f'<defs><linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#F0CB7A" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="cl"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>')
    o.append(f'<rect class="sc" x="0" y="0" width="260" height="{H}" fill="url(#sw)"/>')
    hoy = dt.date.today()
    o.append(T(W - 56, 58, f'Actualizado {hoy.day} {MESES[hoy.month-1]} {hoy.year}', 11, C['dim'], 'm f', 'end'))
    label = f'Relieve de contribuciones de {USER} en GitHub durante el último año' + (f': {total} contribuciones.' if total is not None else '.')
    style = (ff + 'text{font-family:In,"Segoe UI",system-ui,sans-serif;white-space:pre}.s{font-family:Fr,Georgia,serif;font-weight:600}'
             '.m{font-family:Mo,ui-monospace,monospace}.b{font-weight:600}.md{font-weight:500}' + ''.join(css))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(label)}">'
            f'<title>{html.escape(label)}</title><style>{style}</style><g clip-path="url(#cl)">{"".join(o)}</g>'
            f'<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="18" fill="none" stroke="{C["line"]}" stroke-width="1.5"/></svg>')

if __name__ == '__main__':
    src = os.environ.get('CONTRIB_HTML')
    s = svg(leer(src))
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(s)
    print('ok', OUT, len(s))
