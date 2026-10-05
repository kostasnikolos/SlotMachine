#!/usr/bin/env python3
"""Build the playable game page from the design source.

    python3 scripts/descent/dc_to_web.py

Input : slot_engine/static/descent/design/Main.dc.html  (the Claude Design canvas artboard, the visual source of truth)
Output: slot_engine/static/descent/index.html + app.js  (served at "/" by slot_engine/api/app.py)

The artboard is a template ({{holes}}, <sc-for>, <sc-if>) plus a `class Component extends DCLogic` with
renderVals(). This script turns the template into an htm/Preact template, keeps the component code as-is,
swaps canvas asset URLs for files under /static/assets/descent/, and replaces the built-in engine copy with
calls to /api/slot/spin and /api/slot/buy-bonus (the copy stays as an offline fallback).
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
STATIC = os.path.join(ROOT, 'slot_engine', 'static')
SRC = os.path.join(STATIC, 'descent', 'design', 'Main.dc.html')
OUT_DIR = os.path.join(STATIC, 'descent')
A = '/static/assets/descent/'

# canvas asset ids -> repo files
ASSETS = {
    '932e6db068e183257c71db1d184f4769': 'sym_albedo.jpg', 'ec0c40a9a29bbc7b0af8e8c64037ff4f': 'sym_normal.jpg',
    'cce5679e94efc084d333dd7f158a50da': 'sym_emissive.jpg', '30372f0d03094629ce827ea21961a81d': 'sym_aux.jpg',
    '100d5105ba6e96ab54aca5fbe184faa2': 'lev_head.json', '21dd5801039742292a30699d0100e31c': 'lev_body.json', 'b2ac6177d14560140fa96efdd0fc5dc5': 'lev_tail.json',
    '4f814afe606eee99697f9cd7fee85f18': 'lev_head_base.jpg', 'af1e3206710d6cd605c96847eca8787e': 'lev_body_base.jpg', 'b5faacba7a479dfee926a91041fea045': 'lev_tail_base.jpg',
    '7547ad7a3dfef8377b839044d631335e': 'lev_head_normal.jpg', 'a21806563808d2a8e70005605746e1aa': 'lev_body_normal.jpg', '3fd83e2fb44a53632126a532418b7b83': 'lev_tail_normal.jpg',
    'be0cae683d9ca45a5f1cc05cdd97dc5b': 'lev_head_mr.jpg', 'd461d072a19df5986dbbc445ff8f7e2f': 'lev_body_mr.jpg', '78fd80a79c667cabe34b320d96e3dc97': 'lev_tail_mr.jpg',
    '0113ddc559c3995dd6158c96a0b64174': 'lev_head_emissive.jpg', '5a969403979dc6c9c0188637d13c3a89': 'lev_body_emissive.jpg', '0d2a49d1f488a06f75b052067c478f81': 'lev_tail_emissive.jpg',
}

FETCH_METHOD = """
  // ---------- connection to the Python engine (slot_engine/api/app.py) ----------
  async fetchRound(bet, feature, dirLevel) {
    const buy = feature && feature !== 'XBET_SONAR_2X';
    try {
      const res = await fetch(buy ? '/api/slot/buy-bonus' : '/api/slot/spin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buy ? { bet, feature_type: feature } : { bet, feature_buy: feature || 'NONE' })
      });
      if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + (await res.text()));
      const outcome = await res.json();
      this.online = true;
      return outcome;
    } catch (e) {
      // keep the game playable without the server: same rules, local randomness
      console.warn('[descent] engine API unreachable, using the built-in engine copy', e);
      this.online = false;
      return this.engRound(bet, feature, feature ? 0 : dirLevel);
    }
  }

"""


def convert_template(body):
    body = re.sub(r'\s+hint-placeholder-(?:count|val)="[^"]*"', '', body)
    body = re.sub(r'<img([^>]*?)\s*/?>', r'<img\1 />', body)
    out, scope = [], []
    tag_re = re.compile(r'<sc-for\s+list="\{\{\s*([^}]+?)\s*\}\}"\s+as="(\w+)"\s*>|<sc-if\s+value="\{\{\s*([^}]+?)\s*\}\}"\s*>|</sc-for>|</sc-if>')

    def expr(path):
        path = path.strip()
        if re.fullmatch(r'true|false|null|-?\d+(\.\d+)?', path):
            return path
        head = path.split('.')[0]
        return path if head in scope or head == '$index' else '$v.' + path

    def holes(text):
        text = re.sub(r'([\w:-]+)="\{\{\s*([^}]+?)\s*\}\}"', lambda m: m.group(1) + '=${' + expr(m.group(2)) + '}', text)
        return re.sub(r'\{\{\s*([^}]+?)\s*\}\}', lambda m: '${' + expr(m.group(1)) + '}', text)

    pos, stack = 0, []
    for m in tag_re.finditer(body):
        out.append(holes(body[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith('<sc-for'):
            out.append('${(' + expr(m.group(1)) + ' || []).map((' + m.group(2) + ', $index) => html`')
            scope.append(m.group(2)); stack.append('for')
        elif tok.startswith('<sc-if'):
            out.append('${' + expr(m.group(3)) + ' ? html`')
            stack.append('if')
        elif tok == '</sc-for>':
            assert stack.pop() == 'for'; scope.pop(); out.append('`)}')
        else:
            assert stack.pop() == 'if'; out.append('` : null}')
        pos = m.end()
    out.append(holes(body[pos:]))
    assert not stack, stack
    t = ''.join(out)
    assert '`' not in body and '\\' not in body, 'template text must not contain backticks or backslashes'
    return t


def main():
    src = open(SRC, encoding='utf-8').read()
    for k, v in ASSETS.items():
        src = src.replace('/_blob/' + k, A + v)
    dc = src[src.index('<x-dc>') + 6: src.index('</x-dc>')]
    helmet = dc[dc.index('<helmet>') + 8: dc.index('</helmet>')]
    body = dc[dc.index('</helmet>') + 9:].strip()
    fonts = re.search(r'<link[^>]+>', helmet).group(0)
    css = re.search(r'<style>(.*?)</style>', helmet, re.S).group(1)
    m = re.search(r"<script type=\"text/x-dc\" data-dc-script data-props='(.*?)'>(.*?)</script>", src, re.S)
    props_meta, code = json.loads(m.group(1)), m.group(2)
    defaults = {k: v['default'] for k, v in props_meta.items() if not k.startswith('$') and 'default' in v}
    defaults['director'] = False  # the Director bar is a design/QA tool: enable with ?director=1

    anchor = '    const outcome = this.engRound(bet, feature, feature ? 0 : s.dirLevel);'
    assert code.count(anchor) == 1, 'engine call anchor not found'
    code = code.replace(anchor, '    const outcome = await this.fetchRound(bet, feature, s.dirLevel);')
    code = code.replace('    const x = total / bet;', '    const x = outcome.win_x_base_bet != null ? outcome.win_x_base_bet : total / bet;')
    i = code.index('  // ---------- local engine:')
    code = code[:i] + FETCH_METHOD.lstrip('\n') + code[i:]
    code = code.replace('class Component extends DCLogic', 'class DescentGame extends DCLogic')

    template = convert_template(body)
    app = (
        '/* GENERATED by scripts/descent/dc_to_web.py from descent/design/Main.dc.html. Edit the design file and re-run. */\n'
        "'use strict';\n"
        '(function () {\n'
        'const { html, render, Component: PreactComponent } = window.htmPreact;\n\n'
        '// minimal stand-in for the design canvas runtime: renderVals() feeds the template\n'
        'class DCLogic extends PreactComponent {\n'
        '  render() { return template(this.renderVals()); }\n'
        '}\n\n'
        + code.strip() + '\n\n'
        'function template($v) {\n  return html`' + template + '`;\n}\n\n'
        'const DEFAULTS = ' + json.dumps(defaults) + ';\n'
        'const query = new URLSearchParams(location.search);\n'
        'const props = Object.assign({}, DEFAULTS);\n'
        'for (const k in DEFAULTS) if (query.has(k)) {\n'
        '  const raw = query.get(k);\n'
        "  props[k] = typeof DEFAULTS[k] === 'boolean' ? raw !== '0' && raw !== 'false' : typeof DEFAULTS[k] === 'number' ? +raw : raw;\n"
        '}\n'
        "render(html`<${DescentGame} ...${props} />`, document.getElementById('stage'));\n"
        '})();\n'
    )
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Descent: Abyssal Leviathan</title>
<!-- GENERATED by scripts/descent/dc_to_web.py — edit descent/design/Main.dc.html and re-run -->
{fonts}
<style>
html,body{{margin:0;height:100%;overflow:hidden;background:#000}}
#stage{{position:absolute;left:50%;top:50%;width:1920px;height:1080px;transform-origin:50% 50%}}
{css.strip()}
</style>
<script src="/static/vendor/three.r128.min.js"></script>
<script src="/static/vendor/htm-preact-standalone.umd.js"></script>
</head>
<body>
<div id="stage"></div>
<script src="/static/descent/app.js"></script>
<script>
// letterbox the 1920x1080 stage into the window
(function () {{
  const st = document.getElementById('stage');
  const fit = () => {{ const k = Math.min(innerWidth / 1920, innerHeight / 1080); st.style.transform = 'translate(-50%, -50%) scale(' + k + ')'; }};
  addEventListener('resize', fit); fit();
  // Space spins
  addEventListener('keydown', (e) => {{
    if (e.code !== 'Space' || e.repeat || /input|textarea|button/i.test(document.activeElement.tagName)) return;
    e.preventDefault();
    const b = document.querySelector('.spinbtn'); if (b) b.click();
  }});
}})();
</script>
</body>
</html>
'''
    open(os.path.join(OUT_DIR, 'app.js'), 'w', encoding='utf-8').write(app)
    open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8').write(page)
    left = re.findall(r'/_blob/\w+', app + page)
    print('wrote', os.path.join(OUT_DIR, 'index.html'), 'and app.js', len(app) // 1024, 'KB;', 'unmapped assets:', left or 'none')


if __name__ == '__main__':
    main()
