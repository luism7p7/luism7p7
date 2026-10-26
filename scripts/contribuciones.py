#!/usr/bin/env python3
"""Radar de contribuciones: el último año da una vuelta completa alrededor de un círculo, con un
rayo por día cuyo largo es el número de contribuciones. Un barrido gira sin parar y enciende
cada día al pasar; el día récord late en dorado. Con el estilo "Mapa de los Andes".
Lo ejecuta .github/workflows/gusano.yml todos los días. Solo usa la biblioteca estándar."""
import base64, datetime as dt, html, math, os, re, sys, urllib.request

USER = os.environ.get('GH_USER', 'luism7p7')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'dist/contribuciones.svg'
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'andes', 'fonts')
C = dict(bg='#0C1615', panel='#0F1C1A', line='#1E302C', gold='#E2B04B', gold2='#F0CB7A', ivory='#F3ECDD', mut='#A7B5AD', dim='#6F817A')
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
# colores por nivel: (tapa, cara izquierda, cara derecha)
NIV = {0: ('#16302A', '#0F211D', '#122723'), 1: ('#3E6B5A', '#25443A', '#2E5246'), 2: ('#5E8574', '#3A5A4D', '#466B5B'),
       3: ('#8DB89C', '#5B8569', '#6E9A7D'), 4: ('#E2B04B', '#9C7426', '#B8892F')}

def leer():
    dias = {}
    raw = os.environ.get('CONTRIB_DATA')  # pruebas locales: "aaaa-mm-dd:n:nivel,..."
    if raw:
        ini = dt.date.fromisoformat(os.environ.get('CONTRIB_FROM'))
        for i in range(366): dias[(ini + dt.timedelta(days=i)).isoformat()] = (0, 0)
        for item in raw.split(','):
            f, n, l = item.split(':'); dias[f] = (int(n), int(l))
        return dias
    req = urllib.request.Request(f'https://github.com/users/{USER}/contributions', headers={'User-Agent': 'contribuciones-script'})
    page = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    tips = {t.group(1): t.group(2) for t in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page)}
    for m in re.finditer(r'<td[^>]*?data-date="(\d{4}-\d\d-\d\d)"[^>]*>', page):
        tag = m.group(0)
        idm = re.search(r'id="([^"]+)"', tag); lv = re.search(r'data-level="(\d)"', tag)
        n = re.match(r'\s*(\d+)', tips.get(idm.group(1) if idm else '', ''))
        lvl = int(lv.group(1)) if lv else 0
        dias[m.group(1)] = (int(n.group(1)) if n else (lvl and 1), lvl)
    if not dias: raise SystemExit('No se encontraron contribuciones')
    return dias

def fuente(nombre):
    try: return base64.b64encode(open(os.path.join(FONTS, nombre), 'rb').read()).decode()
    except OSError: return None

def T(x, y, s, size, fill, cls='', anchor=None, extra=''):
    a = f' text-anchor="{anchor}"' if anchor else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" class="{cls}"{a}{extra}>{html.escape(str(s))}</text>'

def odometro(x, y, valor, size, delay, uid):
    lh = size * 1.15; o = []; cx = x; cw = size * .6
    for k, ch in enumerate(str(valor)):
        d = int(ch)
        col = ''.join(T(0, i * lh, i % 10, size, C['gold2'], 's') for i in range(10 + d + 1))
        o.append(f'<g transform="translate({cx:.1f} {y})"><g class="od" style="--t:-{(10+d)*lh:.1f}px;animation-delay:{delay+k*.12:.2f}s">{col}</g></g>')
        cx += cw
    return f'<clipPath id="oc{uid}"><rect x="{x-4}" y="{y-size*.8:.0f}" width="{cx-x+30:.0f}" height="{size*1.02:.0f}"/></clipPath><g clip-path="url(#oc{uid})">{"".join(o)}</g>'

def svg(dias):
    W, H = 1200, 520
    fechas = sorted(dias)
    hoy = dt.date.fromisoformat(fechas[-1])
    N = len(fechas)
    n = lambda f: dias.get(f, (0, 0))[0]
    total = sum(v[0] for v in dias.values())
    activos = sum(1 for v in dias.values() if v[0] > 0)
    mejor = max(fechas, key=n); nmax = max(1, n(mejor))
    racha = larga = 0
    for f in fechas:
        racha = racha + 1 if n(f) > 0 else 0; larga = max(larga, racha)
    actual = 0
    for f in reversed(fechas):
        if n(f) > 0: actual += 1
        elif f == fechas[-1]: continue
        else: break
    # radar: el año da una vuelta completa en el sentido del reloj, empezando arriba
    cx, cy, r0, r1 = 790, 262, 82, 206
    VUELTA = 8.0  # segundos por vuelta del barrido
    ang = lambda i: -math.pi / 2 + 2 * math.pi * i / N
    pol = lambda a, r: (cx + r * math.cos(a), cy + r * math.sin(a))
    o = [f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>']
    o.append(f'<defs><radialGradient id="gw" cx="{cx/W:.3f}" cy=".5" r=".42"><stop offset="0" stop-color="#173A30" stop-opacity=".95"/><stop offset="1" stop-color="{C["bg"]}" stop-opacity="0"/></radialGradient>'
             f'<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#F0CB7A" stop-opacity="0"/><stop offset=".5" stop-color="#F0CB7A" stop-opacity=".05"/><stop offset="1" stop-color="#F0CB7A" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="cl"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs><rect width="{W}" height="{H}" fill="url(#gw)"/>')
    # anillos guía
    for k, r in enumerate([r0, (r0 + r1) / 2, r1]):
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="none" stroke="{C["line"]}" stroke-width="{1.5 if k != 1 else 1}" stroke-dasharray="{"none" if k != 1 else "2 6"}" class="f"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r1+14}" fill="none" stroke="{C["line"]}" stroke-width="1" pathLength="100" stroke-dasharray="1 2" class="spin"/>')
    # barrido que gira (cuña con degradado hecha de franjas)
    cuña = []
    for k in range(18):
        a0 = -math.pi / 2 - k * math.radians(2.2); a1 = a0 - math.radians(2.3)
        p0, p1, q0, q1 = pol(a0, r0 - 6), pol(a0, r1 + 8), pol(a1, r1 + 8), pol(a1, r0 - 6)
        cuña.append(f'<path d="M{p0[0]:.1f} {p0[1]:.1f}L{p1[0]:.1f} {p1[1]:.1f}A{r1+8} {r1+8} 0 0 0 {q0[0]:.1f} {q0[1]:.1f}L{q1[0]:.1f} {q1[1]:.1f}A{r0-6} {r0-6} 0 0 1 {p0[0]:.1f} {p0[1]:.1f}Z" fill="{C["gold2"]}" opacity="{.20*(1-k/18)**1.6:.3f}"/>')
    e = pol(-math.pi / 2, r1 + 8)
    o.append(f'<g class="sweep">{"".join(cuña)}<line x1="{cx}" y1="{cy - r0 + 6}" x2="{e[0]:.1f}" y2="{e[1]:.1f}" stroke="{C["gold2"]}" stroke-width="2" opacity=".85"/></g>')
    # un rayo por día
    rayos = []
    for i, f in enumerate(fechas):
        c, lvl = dias[f]
        a = ang(i + .5)
        dl = i / N * VUELTA
        if c == 0:
            p, q = pol(a, r0 + 2), pol(a, r0 + 7)
            rayos.append(f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="#1E3A33" stroke-width="1.6"/>')
            continue
        L = 14 + (r1 - r0 - 14) * math.log1p(c) / math.log1p(nmax)
        p, q = pol(a, r0 + 2), pol(a, r0 + 2 + L)
        col = C['gold'] if f == mejor else ['#3E6B5A', '#5E8574', '#8DB89C', '#A9D3B6'][min(lvl, 4) - 1 if lvl else 0]
        rayos.append(f'<g class="grow" style="animation-delay:{.3 + i/N*1.6:.2f}s"><line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{col}" stroke-width="3.2" stroke-linecap="round"/>'
                     f'<line class="hit" x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="#FFF1CF" stroke-width="3.2" stroke-linecap="round" style="animation-delay:{dl:.2f}s"/>'
                     f'<circle class="hit" cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="3.2" fill="#FFF1CF" style="animation-delay:{dl:.2f}s"/></g>')
    o.append(''.join(rayos))
    # meses alrededor
    mprev = None
    for i, f in enumerate(fechas):
        fd = dt.date.fromisoformat(f)
        if fd.month != mprev and fd.day == 1:
            a = ang(i); p = pol(a, r1 + 30); t1, t2 = pol(a, r1 + 4), pol(a, r1 + 12)
            o.append(f'<line x1="{t1[0]:.1f}" y1="{t1[1]:.1f}" x2="{t2[0]:.1f}" y2="{t2[1]:.1f}" stroke="{C["dim"]}" stroke-width="1"/>')
            o.append(T(p[0], p[1] + 4, MESES[fd.month - 1], 11, C['dim'], 'm f', 'middle'))
            mprev = fd.month
    # día récord y hoy
    im = fechas.index(mejor)
    if n(mejor):
        a = ang(im + .5)
        L = r1 - r0 - 12
        q = pol(a, r0 + 2 + L)
        fd = dt.date.fromisoformat(mejor)
        o.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="5" fill="{C["gold"]}"/><circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="5" fill="none" stroke="{C["gold"]}" class="pk"/>')
    # centro: total que gira como odómetro
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r0-8}" fill="{C["panel"]}" stroke="{C["line"]}" stroke-width="1.5"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r0-8}" fill="none" stroke="{C["gold"]}" stroke-width="1.5" pathLength="100" stroke-dasharray="12 88" class="tr"/>')
    tw = len(str(total)) * 40 * .6
    o.append(odometro(cx - tw / 2, cy + 12, total, 40, .5, 'c'))
    o.append(T(cx, cy + 34, 'contribuciones', 11.5, C['mut'], 'md', 'middle'))
    # columna de cifras
    o.append(T(48, 62, 'MIS CONTRIBUCIONES', 12.5, C['gold'], 'b f', extra=' letter-spacing="2.4"'))
    o.append(T(48, 84, 'Último año en GitHub · un rayo por día', 13.5, C['mut'], 'f'))
    stats = [(activos, 'días con actividad'), (larga, 'días de racha más larga'), (actual, 'días de racha actual'), (n(mejor), f'en mi mejor día · {dt.date.fromisoformat(mejor).day} {MESES[dt.date.fromisoformat(mejor).month-1]}')]
    for i, (v, t) in enumerate(stats):
        y = 120 + i * 92; dl = .3 + i * .2
        o.append(f'<g class="f" style="animation-delay:{dl:.2f}s"><rect x="48" y="{y}" width="300" height="78" rx="12" fill="{C["panel"]}" stroke="{C["line"]}" stroke-width="1.5"/>'
                 f'<rect x="48" y="{y}" width="300" height="78" rx="12" fill="none" stroke="{C["gold"]}" stroke-width="1.6" pathLength="100" stroke-dasharray="14 86" class="tr" style="animation-delay:-{i*1.4:.1f}s"/>'
                 + odometro(68, y + 50, v, 36, dl + .2, i) + T(68 + len(str(v)) * 21.6 + 12, y + 47, t, 13, C['ivory'], 'md') + '</g>')
    o.append(f'<rect class="sc" x="0" y="0" width="240" height="{H}" fill="url(#sw)"/>')
    o.append(T(W - 40, 40, f'Se actualiza cada día · {hoy.day} {MESES[hoy.month-1]} {hoy.year}', 10.5, C['dim'], 'm f', 'end'))
    css = (f'.sweep{{transform-origin:{cx}px {cy}px;animation:sweep {VUELTA}s linear infinite}}@keyframes sweep{{to{{transform:rotate(360deg)}}}}'
           f'.spin{{transform-origin:{cx}px {cy}px;animation:sweep 40s linear infinite reverse}}'
           f'.hit{{opacity:0;animation:hit {VUELTA}s linear infinite}}@keyframes hit{{0%{{opacity:.95}}14%{{opacity:0}}100%{{opacity:0}}}}'
           f'.grow{{transform-origin:{cx}px {cy}px;animation:grow 1.1s cubic-bezier(.2,.9,.3,1.2) both}}@keyframes grow{{from{{transform:scale(.38);opacity:0}}}}'
           '.f{animation:f 1.2s ease both}@keyframes f{from{opacity:0}}'
           '.od{animation:od 10s cubic-bezier(.2,.8,.2,1) infinite both}@keyframes od{0%{transform:translateY(0);opacity:0}3%{opacity:1}22%{transform:translateY(var(--t))}94%{transform:translateY(var(--t));opacity:1}100%{transform:translateY(var(--t));opacity:0}}'
           '.tr{animation:tr 6s linear infinite}@keyframes tr{to{stroke-dashoffset:-100}}'
           '.pk{transform-box:fill-box;transform-origin:center;animation:pk 2.4s ease-out infinite}@keyframes pk{from{transform:scale(.4);opacity:.9}to{transform:scale(3);opacity:0}}'
           '.sc{animation:sc 9s ease-in-out 3s infinite}@keyframes sc{0%{transform:translateX(-260px)}55%,100%{transform:translateX(1460px)}}'
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}}')
    ff = ''
    for fam, file, extra in [('Fr', 'fr6.woff2', 'font-weight:600;'), ('In', 'i5.woff2', 'font-weight:500;'), ('In', 'i4.woff2', 'font-weight:400;'), ('Mo', 'm4.woff2', '')]:
        b = fuente(file)
        if b: ff += f"@font-face{{font-family:{fam};{extra}src:url(data:font/woff2;base64,{b}) format('woff2')}}"
    style = (ff + 'text{font-family:In,"Segoe UI",system-ui,sans-serif;white-space:pre}.s{font-family:Fr,Georgia,serif;font-weight:600}'
             '.m{font-family:Mo,ui-monospace,monospace}.b{font-weight:500}.md{font-weight:500}' + css)
    label = (f'Radar de mis contribuciones en GitHub durante el último año: un rayo por día alrededor de un círculo. {total} contribuciones, '
             f'{activos} días con actividad, racha más larga de {larga} días, racha actual de {actual} días y {n(mejor)} contribuciones en mi mejor día.')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(label)}">'
            f'<title>{html.escape(label)}</title><style>{style}</style><g clip-path="url(#cl)">{"".join(o)}</g>'
            f'<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="18" fill="none" stroke="{C["line"]}" stroke-width="1.5"/></svg>')

if __name__ == '__main__':
    s = svg(leer())
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(s)
    print('ok', OUT, len(s))
