#!/usr/bin/env python3
"""Metrocable de contribuciones: una cabina del metrocable de Medellín cruza el gráfico de
contribuciones del último año y enciende cada día que programé; otra cabina va de regreso.
Con el estilo "Mapa de los Andes". Lo ejecuta .github/workflows/gusano.yml todos los días.
Solo usa la biblioteca estándar."""
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
    W, H = 1200, 360
    fechas = sorted(dias)
    n = lambda f: dias.get(f, (0, 0))[0]
    hoy = dt.date.fromisoformat(fechas[-1])
    total = sum(n(f) for f in fechas); activos = sum(1 for f in fechas if n(f))
    mejor = max(fechas, key=n)
    racha = larga = 0
    for f in fechas:
        racha = racha + 1 if n(f) else 0; larga = max(larga, racha)
    ini = dt.date.fromisoformat(fechas[0]); ini_dom = ini - dt.timedelta(days=(ini.weekday() + 1) % 7)
    sem = (hoy - ini_dom).days // 7 + 1
    cs, gp = 13.4, 3.6
    x0 = (W - sem * (cs + gp)) / 2 + 10; y0 = 214
    col = ['#14261F', '#2F5446', '#4F7A66', '#8DB89C', '#C9E3CF']
    DUR = 11.0
    o = []
    # montañas al fondo con luces de la ciudad
    o.append(f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A1312"/><stop offset="1" stop-color="#10241F"/></linearGradient>'
             f'<linearGradient id="cono" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F0CB7A" stop-opacity=".22"/><stop offset="1" stop-color="#F0CB7A" stop-opacity="0"/></linearGradient></defs>'
             f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    far = ' '.join(f'{x},{150 - 30*math.sin(x/170+1.4) - 12*math.sin(x/53)}' for x in range(0, W + 20, 20))
    near = ' '.join(f'{x},{176 - 34*math.sin(x/140+.6) - 14*math.sin(x/47)}' for x in range(0, W + 20, 20))
    o.append(f'<polygon points="0,{H} {far} {W},{H}" fill="#0E1D1A"/><polygon points="0,{H} {near} {W},{H}" fill="#11241F"/>')
    rnd = 7
    for k in range(70):
        rnd = (rnd * 16807) % 2147483647; x = rnd % W
        rnd = (rnd * 16807) % 2147483647; yy = 176 - 34 * math.sin(x / 140 + .6) - 14 * math.sin(x / 47) + 6 + rnd % 26
        rnd = (rnd * 16807) % 2147483647
        o.append(f'<circle cx="{x}" cy="{yy:.0f}" r="1.1" fill="#F0CB7A" class="luz" style="animation-delay:-{rnd % 40 / 10:.1f}s"/>')
    for k in range(46):
        rnd = (rnd * 16807) % 2147483647; sx_ = rnd % W
        rnd = (rnd * 16807) % 2147483647; sy_ = 90 + rnd % 50
        rnd = (rnd * 16807) % 2147483647
        o.append(f'<circle cx="{sx_}" cy="{sy_}" r="{.5 + (rnd % 10)/14:.1f}" fill="#C9D6CF" class="luz" style="animation-delay:-{rnd % 30 / 10:.1f}s;animation-duration:{1.6 + rnd % 20 / 10:.1f}s"/>')
    for k, (cy_, rx_, dur_, op_) in enumerate([(150, 160, 46, .05), (176, 220, 64, .045), (132, 120, 38, .04)]):
        o.append(f'<ellipse cx="0" cy="{cy_}" rx="{rx_}" ry="{rx_*.12:.0f}" fill="#C9E3CF" opacity="{op_}" class="nube" style="animation-duration:{dur_}s;animation-delay:-{k*15}s"/>')
    # cabecera con cifras
    o.append(T(48, 56, 'MIS CONTRIBUCIONES', 12.5, C['gold'], 'b f', extra=' letter-spacing="2.4"'))
    o.append(T(48, 78, f'Mi metrocable recorre el último año · se actualiza cada día ({hoy.day} {MESES[hoy.month-1]})', 13, C['mut'], 'f'))
    x = W - 48
    for v, t in reversed([(total, 'contribuciones'), (activos, 'días activos'), (larga, 'días de racha'), (n(mejor), 'en mi mejor día')]):
        w = len(str(v)) * 13 + len(t) * 6.6 + 34
        x -= w
        o.append(f'<g class="f"><rect x="{x:.0f}" y="38" width="{w:.0f}" height="32" rx="16" fill="{C["panel"]}" stroke="{C["line"]}" stroke-width="1.5"/>'
                 + odometro(x + 14, 61, v, 19, .3 + (x % 7) * .08, f'k{len(o)}') + T(x + 20 + len(str(v)) * 11.5, 59, t, 12, C['mut'], 'md') + '</g>')
        x -= 10
    # torres y cable (catenaria)
    xa, xb = x0 - 26, x0 + sem * (cs + gp) + 16
    torres = [xa, (xa + xb) / 2, xb]; top = 118
    ida = f'M{torres[0]:.0f} {top} Q{(torres[0]+torres[1])/2:.0f} {top+40} {torres[1]:.0f} {top} Q{(torres[1]+torres[2])/2:.0f} {top+40} {torres[2]:.0f} {top}'
    vuelta = f'M{torres[2]:.0f} {top-8} Q{(torres[1]+torres[2])/2:.0f} {top+32} {torres[1]:.0f} {top-8} Q{(torres[0]+torres[1])/2:.0f} {top+32} {torres[0]:.0f} {top-8}'
    for tx in torres:
        o.append(f'<path d="M{tx-8:.0f} {y0-10}L{tx-2:.0f} {top-10}M{tx+8:.0f} {y0-10}L{tx+2:.0f} {top-10}M{tx-6:.0f} {y0-50}L{tx+6:.0f} {y0-50}M{tx-4:.0f} {y0-80}L{tx+4:.0f} {y0-80}" fill="none" stroke="#2F5446" stroke-width="2.4" stroke-linecap="round"/>'
                 f'<rect x="{tx-14:.0f}" y="{top-14}" width="28" height="6" rx="3" fill="#4F7A66"/><circle cx="{tx:.0f}" cy="{top-17}" r="2.4" fill="#D98B6A" class="luz"/>')
    o.append(f'<path d="{ida}" fill="none" stroke="{C["mut"]}" stroke-width="1.4" opacity=".9"/><path d="{vuelta}" fill="none" stroke="{C["mut"]}" stroke-width="1.1" opacity=".45"/>'
             f'<path d="{ida}" fill="none" stroke="{C["gold2"]}" stroke-width="2" pathLength="100" stroke-dasharray="4 96" class="cb"/>')
    def cabina(path, dur, delay, principal):
        c1 = C['gold'] if principal else '#4F7A66'
        cono = f'<path d="M-16 44L16 44L46 {y0 + 7*(cs+gp) - top - 4}L-46 {y0 + 7*(cs+gp) - top - 4}Z" fill="url(#cono)"/>' if principal else ''
        return (f'<g opacity="{1 if principal else .75}"><animateMotion dur="{dur}s" begin="{delay}s" repeatCount="indefinite" path="{path}"/>'
                f'{cono}<g class="sway"><line x1="0" y1="0" x2="0" y2="14" stroke="{C["mut"]}" stroke-width="1.6"/><rect x="-6" y="-3" width="12" height="5" rx="2" fill="{C["mut"]}"/>'
                f'<rect x="-17" y="14" width="34" height="28" rx="8" fill="{c1}"/><rect x="-17" y="34" width="34" height="8" rx="4" fill="#000" opacity=".18"/>'
                f'<rect x="-12" y="19" width="10" height="10" rx="2.5" fill="#0C1615" opacity=".8"/><rect x="2" y="19" width="10" height="10" rx="2.5" fill="#0C1615" opacity=".8"/>'
                + (f'<rect x="-12" y="19" width="10" height="10" rx="2.5" fill="#F0CB7A" class="ven"/><rect x="2" y="19" width="10" height="10" rx="2.5" fill="#F0CB7A" class="ven" style="animation-delay:.7s"/>' if principal else '')
                + '</g>' + (''.join(f'<circle cx="{dx}" cy="46" r="1.8" fill="#FFE7A8" class="chispa" style="animation-delay:{dl}s"/>' for dx, dl in [(-8, 0), (4, .35), (10, .7), (-2, 1.05), (-12, 1.4)]) if principal else '') + '</g>')
    # cuadrícula de días
    for w in range(sem):
        f0 = ini_dom + dt.timedelta(days=w * 7)
        for d in range(7):
            f = (f0 + dt.timedelta(days=d)).isoformat()
            if f not in dias: continue
            c, lvl = dias[f]; xx, yy = x0 + w * (cs + gp), y0 + d * (cs + gp)
            fill = C['gold'] if f == mejor and c else col[min(lvl, 4) if c else 0]
            o.append(f'<rect class="pop" x="{xx:.1f}" y="{yy:.1f}" width="{cs}" height="{cs}" rx="3.5" fill="{fill}" style="animation-delay:{.2 + w*.015 + d*.02:.2f}s"/>')
            if c:
                t0 = (xx + cs / 2 - torres[0]) / (torres[2] - torres[0]) * DUR
                base = o.pop()
                o.append(f'<g class="jp" style="animation-delay:{t0 + 1.0:.2f}s">{base}<rect class="wv" x="{xx:.1f}" y="{yy:.1f}" width="{cs}" height="{cs}" rx="3.5" fill="#FFF1CF" style="animation-delay:{t0 + 1.0:.2f}s"/></g>')
            if f == mejor and c:
                o.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{cs}" height="{cs}" rx="3.5" fill="none" stroke="{C["gold"]}" stroke-width="2" class="pk"/>')
    mprev = None
    for w in range(sem):
        f0 = ini_dom + dt.timedelta(days=w * 7)
        if f0.month != mprev and f0.day <= 7:
            o.append(T(x0 + w * (cs + gp), y0 + 7 * (cs + gp) + 16, MESES[f0.month - 1], 10.5, C['dim'], 'm f')); mprev = f0.month
    for d, t in [(1, 'lun'), (3, 'mié'), (5, 'vie')]:
        o.append(T(x0 - 10, y0 + d * (cs + gp) + 10, t, 10, C['dim'], 'm f', 'end'))
    o.append(cabina(vuelta, DUR * 1.15, 0, False))
    o.append(cabina(ida, DUR, 1.0, True))
    css = (f'.wv{{opacity:0;animation:wv {DUR}s linear infinite}}@keyframes wv{{0%{{opacity:.9}}12%{{opacity:0}}100%{{opacity:0}}}}'
           f'.jp{{animation:jp {DUR}s cubic-bezier(.3,1.6,.5,1) infinite}}@keyframes jp{{0%{{transform:translateY(-7px)}}4%,100%{{transform:none}}}}'
           f'.cb{{animation:cb {DUR}s linear 1s infinite}}@keyframes cb{{from{{stroke-dashoffset:4}}to{{stroke-dashoffset:-96}}}}'
           '.chispa{opacity:0;animation:chispa 1.75s ease-in infinite}@keyframes chispa{0%{opacity:0;transform:translateY(0)}15%{opacity:1}100%{opacity:0;transform:translateY(60px)}}'
           '.ven{opacity:0;animation:ven 1.4s ease-in-out infinite alternate}@keyframes ven{to{opacity:.55}}'
           f'.nube{{animation:nube 50s linear infinite}}@keyframes nube{{from{{transform:translateX(-260px)}}to{{transform:translateX({W+260}px)}}}}'
           '.od{animation:od 10s cubic-bezier(.2,.8,.2,1) infinite both}@keyframes od{0%{transform:translateY(0);opacity:0}3%{opacity:1}22%{transform:translateY(var(--t))}94%{transform:translateY(var(--t));opacity:1}100%{transform:translateY(var(--t));opacity:0}}'
           '.pop{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.3,1.6,.5,1) both}@keyframes pop{from{transform:scale(0)}}'
           '.sway{animation:sway 2.6s ease-in-out infinite alternate}@keyframes sway{from{transform:rotate(-4deg)}to{transform:rotate(4deg)}}'
           '.luz{animation:luz 2.4s ease-in-out infinite alternate}@keyframes luz{from{opacity:.2}to{opacity:1}}'
           '.f{animation:f 1.2s ease both}@keyframes f{from{opacity:0}}'
           '.pk{transform-box:fill-box;transform-origin:center;animation:pk 2.4s ease-out infinite}@keyframes pk{from{transform:scale(.6);opacity:.9}to{transform:scale(2.6);opacity:0}}'
           '@media (prefers-reduced-motion:reduce){*{animation:none!important}}')
    ff = ''
    for fam, file, extra in [('Fr', 'fr6.woff2', 'font-weight:600;'), ('In', 'i5.woff2', 'font-weight:500;'), ('In', 'i4.woff2', 'font-weight:400;'), ('Mo', 'm4.woff2', '')]:
        b = fuente(file)
        if b: ff += f"@font-face{{font-family:{fam};{extra}src:url(data:font/woff2;base64,{b}) format('woff2')}}"
    style = (ff + 'text{font-family:In,"Segoe UI",system-ui,sans-serif;white-space:pre}.s{font-family:Fr,Georgia,serif;font-weight:600}'
             '.m{font-family:Mo,ui-monospace,monospace}.b,.md{font-weight:500}' + css)
    label = (f'Mis contribuciones en GitHub del último año: una cabina del metrocable de Medellín cruza la cuadrícula y enciende cada día que programé. '
             f'{total} contribuciones, {activos} días activos, racha de {larga} días y {n(mejor)} contribuciones en mi mejor día.')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(label)}">'
            f'<title>{html.escape(label)}</title><style>{style}</style><defs><clipPath id="cl"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>'
            f'<g clip-path="url(#cl)">{"".join(o)}</g>'
            f'<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="18" fill="none" stroke="{C["line"]}" stroke-width="1.5"/></svg>')

if __name__ == '__main__':
    s = svg(leer())
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(s)
    print('ok', OUT, len(s))
