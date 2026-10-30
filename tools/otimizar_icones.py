"""Gera a versão reduzida dos ícones do site: só os ícones Phosphor que as páginas realmente usam.

Por quê: o pacote completo tem milhares de ícones (173 KB de CSS e mais de 270 KB de fontes), e o site usa
cerca de trinta. Carregar tudo atrasa a primeira exibição da página.

Uso (na raiz do repositório), depois de usar um ícone novo no site:
    python tools/otimizar_icones.py

Precisa dos pacotes:  pip install fonttools brotli
Os arquivos completos ficam em tools/icones-completos (a Vercel ignora a pasta tools). O script gera:
    assets/icons/phosphor-site.css, phosphor-site.woff2 e phosphor-fill-site.woff2
Para usar um ícone que ainda não existe, escreva a classe normalmente (ex.: ph-airplane) e rode o comando de novo.
"""
import re
import sys
from pathlib import Path

from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
COMPLETOS = ROOT / 'tools' / 'icones-completos'
SAIDA = ROOT / 'assets' / 'icons'

# onde procurar classes ph-*: páginas, scripts do site e os geradores que montam páginas
ARQUIVOS = (
    list(ROOT.glob('*.html')) + list(ROOT.glob('blog/**/*.html')) + list(ROOT.glob('assets/*.js'))
    + [ROOT / 'tools' / 'gerar_eventos.py', ROOT / 'tools' / 'gerar_blog.py']
)


def icones_usados():
    nomes = set()
    for arq in ARQUIVOS:
        if arq.is_file():
            nomes |= set(re.findall(r'\bph-([a-z0-9]+(?:-[a-z0-9]+)*)', arq.read_text(encoding='utf-8')))
    nomes.discard('fill')
    return sorted(nomes)


def ler_css():
    css = re.sub(r'/\*.*?\*/', '', (COMPLETOS / 'phosphor.css').read_text(encoding='utf-8'), flags=re.S)
    blocos = re.findall(r'([^{}]+)\{([^{}]*)\}', css)
    base, regular, fill = [], {}, {}
    for seletor, corpo in blocos:
        seletor = seletor.strip()
        m = re.fullmatch(r'\.ph(-fill)?\.ph-([a-z0-9-]+):before', seletor)
        if not m:
            base.append((seletor, corpo))
            continue
        codigo = re.search(r'content:\s*"\\([0-9a-fA-F]+)"', corpo)
        if codigo:
            (fill if m.group(1) else regular)[m.group(2)] = codigo.group(1).lower()
    return base, regular, fill


def reduzir_fonte(origem, destino, codigos):
    opcoes = subset.Options()
    opcoes.flavor = 'woff2'
    opcoes.layout_features = []
    opcoes.name_IDs = []
    opcoes.notdef_outline = True
    fonte = subset.load_font(str(origem), opcoes)
    corte = subset.Subsetter(opcoes)
    corte.populate(unicodes=[int(c, 16) for c in codigos])
    corte.subset(fonte)
    subset.save_font(fonte, str(destino), opcoes)


def compacto(corpo):
    return ';'.join(p.strip() for p in corpo.replace('\n', ' ').split(';') if p.strip())


def main():
    usados = icones_usados()
    base, regular, fill = ler_css()
    faltando = [n for n in usados if n not in regular and n not in fill]
    if faltando:
        print('AVISO: ícones que não existem no pacote Phosphor:', ', '.join(faltando))
    cod_regular = sorted({regular[n] for n in usados if n in regular})
    cod_fill = sorted({fill[n] for n in usados if n in fill})

    reduzir_fonte(COMPLETOS / 'Phosphor.woff2', SAIDA / 'phosphor-site.woff2', cod_regular)
    reduzir_fonte(COMPLETOS / 'Phosphor-Fill.woff2', SAIDA / 'phosphor-fill-site.woff2', cod_fill)

    trocas = {'Phosphor.woff2': 'phosphor-site.woff2', 'Phosphor-Fill.woff2': 'phosphor-fill-site.woff2'}
    linhas = []
    for seletor, corpo in base:
        for velho, novo in trocas.items():
            corpo = corpo.replace(velho, novo)
        linhas.append(f'{seletor}{{{compacto(corpo)}}}')
    for n in usados:
        if n in regular:
            linhas.append(f'.ph.ph-{n}:before{{content:"\\{regular[n]}"}}')
        if n in fill:
            linhas.append(f'.ph-fill.ph-{n}:before{{content:"\\{fill[n]}"}}')
    (SAIDA / 'phosphor-site.css').write_text('\n'.join(linhas) + '\n', encoding='utf-8')

    for nome in ('phosphor-site.css', 'phosphor-site.woff2', 'phosphor-fill-site.woff2'):
        print(f'{nome}: {(SAIDA / nome).stat().st_size / 1024:.1f} KB')
    print(f'{len(usados)} ícones usados no site')


if __name__ == '__main__':
    sys.exit(main())
