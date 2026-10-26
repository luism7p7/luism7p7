#!/usr/bin/env python3
"""Contribuciones en 3D: cada día del último año es un bloque sobre una cuadrícula isométrica;
la altura es el número de contribuciones. Los bloques crecen en ola, una luz recorre la
cuadrícula sin parar y el día récord late en dorado. Con el estilo "Mapa de los Andes".
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
    ini = dt.date.fromisoformat(fechas[0])
    ini_dom = ini - dt.timedelta(days=(ini.weekday() + 1) % 7)  # semanas de domingo a sábado
    semanas = (hoy - ini_dom).days // 7 + 1
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
    # proyección oblicua: las semanas avanzan a la derecha y los días bajan hacia el frente
    wx, wy, dx, dy = 14.0, 2.8, -9.5, 8.6
    ox, oy = 340 + 7 * 9.5, 205
    P = lambda w, d: (ox + w * wx + d * dx, oy + w * wy + d * dy)
    celdas = []
    for w in range(semanas):
        for d in range(7):
            f = (ini_dom + dt.timedelta(days=w * 7 + d)).isoformat()
            if f not in dias: continue
            celdas.append((w, d, f))
    celdas.sort(key=lambda c: (c[0] * wy + c[1] * dy, c[0]))
    o = [f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>']
    # resplandor de fondo
    o.append(f'<defs><radialGradient id="gw" cx=".62" cy=".55" r=".55"><stop offset="0" stop-color="#1A3A31" stop-opacity=".9"/><stop offset="1" stop-color="{C["bg"]}" stop-opacity="0"/></radialGradient></defs><rect width="{W}" height="{H}" fill="url(#gw)"/>')
    bloques = []
    for (w, d, f) in celdas:
        c, lvl = dias[f]
        lvl = 4 if f == mejor and c > 0 else min(lvl, 3) if c > 0 else 0
        h = 3 + (92 * math.log1p(c) / math.log1p(nmax) if c else 0)
        x, y = P(w, d)
        top, lf, rt = NIV[lvl]
        # vértices de la celda: atrás-izq a, atrás-der b, frente-der cc, frente-izq e
        a = P(w + .1, d + .1); b = P(w + .9, d + .1); cc = P(w + .9, d + .9); e = P(w + .1, d + .9)
        up = lambda p: (p[0], p[1] - h)
        pts = lambda *ps: ' '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in ps)
        dl = .15 + w * .028 + d * .01
        g = (f'<g class="up" style="animation-delay:{dl:.2f}s">'
             f'<polygon points="{pts(e, cc, up(cc), up(e))}" fill="{lf}"/>'
             f'<polygon points="{pts(cc, b, up(b), up(cc))}" fill="{rt}"/>'
             f'<polygon points="{pts(up(a), up(b), up(cc), up(e))}" fill="{top}"/>')
        if c:
            g += f'<polygon class="gl" points="{pts(up(a), up(b), up(cc), up(e))}" fill="#FFF4D6" style="animation-delay:{w*.09:.2f}s"/>'
        g += '</g>'
        bloques.append(g)
        if f == mejor and c:
            bx, by = (up(a)[0] + up(cc)[0]) / 2, (up(a)[1] + up(cc)[1]) / 2
    o.append(''.join(bloques))
    # meses a lo largo del borde frontal
    mprev = None
    for w in range(semanas):
        f0 = ini_dom + dt.timedelta(days=w * 7)
        if f0.month != mprev and f0.day <= 7:
            x, y = P(w, 7)
            o.append(T(x + 2, y + 18, MESES[f0.month - 1], 10.5, C['dim'], 'm f'))
            mprev = f0.month
    # día récord
    if n(mejor):
        fd = dt.date.fromisoformat(mejor)
        o.append(f'<g class="f" style="animation-delay:2.4s"><line x1="{bx:.1f}" y1="{by-6:.1f}" x2="{bx:.1f}" y2="{by-46:.1f}" stroke="{C["gold"]}" stroke-width="1.2"/>'
                 f'<circle cx="{bx:.1f}" cy="{by-50:.1f}" r="4" fill="{C["gold"]}"/><circle cx="{bx:.1f}" cy="{by-50:.1f}" r="4" fill="none" stroke="{C["gold"]}" class="pk"/>'
                 + T(bx - 10, by - 62, f'Día récord · {fd.day} {MESES[fd.month-1]} · {n(mejor)}', 12, C['gold2'], 'md', 'end') + '</g>')
    # partícula de luz que recorre el frente
    x1, y1 = P(0, 7); x2, y2 = P(semanas, 7)
    o.append(f'<circle r="3" fill="{C["gold2"]}" opacity=".9"><animateMotion dur="7s" repeatCount="indefinite" path="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}"/>'
             f'<animate attributeName="opacity" values="0;.9;.9;0" keyTimes="0;.1;.9;1" dur="7s" repeatCount="indefinite"/></circle>')
    # columna de cifras
    o.append(T(48, 62, 'MIS CONTRIBUCIONES', 12.5, C['gold'], 'b f', extra=' letter-spacing="2.4"'))
    o.append(T(48, 84, 'Último año en GitHub', 13.5, C['mut'], 'f'))
    stats = [(total, 'contribuciones'), (activos, 'días con actividad'), (larga, 'días de racha más larga'), (actual, 'días de racha actual')]
    for i, (v, t) in enumerate(stats):
        y = 120 + i * 92; dl = .3 + i * .2
        o.append(f'<g class="f" style="animation-delay:{dl:.2f}s"><rect x="48" y="{y}" width="230" height="78" rx="12" fill="{C["panel"]}" stroke="{C["line"]}" stroke-width="1.5"/>'
                 f'<rect x="48" y="{y}" width="230" height="78" rx="12" fill="none" stroke="{C["gold"]}" stroke-width="1.6" pathLength="100" stroke-dasharray="16 84" class="tr" style="animation-delay:-{i*1.4:.1f}s"/>'
                 + odometro(68, y + 50, v, 36, dl + .2, i) + T(68 + len(str(v)) * 21.6 + 12, y + 47, t, 13, C['ivory'], 'md') + '</g>')
    o.append(f'<defs><linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#F0CB7A" stop-opacity="0"/><stop offset=".5" stop-color="#F0CB7A" stop-opacity=".06"/><stop offset="1" stop-color="#F0CB7A" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="cl"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>')
    o.append(f'<rect class="sc" x="0" y="0" width="240" height="{H}" fill="url(#sw)"/>')
    o.append(T(W - 40, 62, f'Se actualiza cada día · {hoy.day} {MESES[hoy.month-1]} {hoy.year}', 10.5, C['dim'], 'm f', 'end'))
    css = ('.up{transform-box:fill-box;transform-origin:50% 100%;animation:up 1s cubic-bezier(.2,.9,.3,1.2) both}@keyframes up{from{transform:scaleY(0);opacity:0}}'
           '.gl{opacity:0;animation:gl 6s ease-in-out infinite}@keyframes gl{0%,100%{opacity:0}8%{opacity:.45}18%{opacity:0}}'
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
    label = (f'Mis contribuciones en GitHub durante el último año, en 3D: {total} contribuciones, {activos} días con actividad, '
             f'racha más larga de {larga} días y racha actual de {actual} días.')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(label)}">'
            f'<title>{html.escape(label)}</title><style>{style}</style><g clip-path="url(#cl)">{"".join(o)}</g>'
            f'<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="18" fill="none" stroke="{C["line"]}" stroke-width="1.5"/></svg>')

if __name__ == '__main__':
    s = svg(leer())
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(s)
    print('ok', OUT, len(s))
