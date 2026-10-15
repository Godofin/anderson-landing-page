"""Gera o blog do site a partir de arquivos Markdown.

Uso (na raiz do repositório):
    python tools/gerar_blog.py

Como publicar um artigo novo:
  1. Crie um arquivo em tools/blog/posts/ (copie um existente) com o cabeçalho (frontmatter) e o texto.
  2. Rode o comando acima. Ele gera blog/index.html e blog/<slug>/index.html, atualiza o sitemap
     e as páginas de evento (o mesmo script de tools/gerar_eventos.py roda no final).
  3. Confira no navegador (python -m http.server) e só então faça o commit.

Cabeçalho de cada artigo (entre linhas "---"):
    titulo: título do artigo, que aparece como H1 (pode ser mais longo que 60 caracteres)
    titulo_seo: título para o Google e as abas (até 60 caracteres; se faltar, usa o titulo)
    descricao: resumo para o Google e as redes (120 a 160 caracteres)
    slug: endereço do artigo, minúsculas e hífens. Não mude depois de publicar.
    data: 2026-10-14
    atualizado: 2026-10-20          (opcional)
    categoria: Guia
    imagem: /assets/img/blog/exemplo-capa-1600.webp      (capa 16:10, 1600x1000, até 200 KB)
    imagem_card: /assets/img/blog/exemplo-capa-800.webp  (mesma capa em 800x500, até 50 KB)
    imagem_credito: Foto: Nome/Agência               (opcional; aparece sob a capa)
    imagem_foco: 50% 20%                             (opcional; parte da foto que fica em foco nos cartões)
    imagem_alt: descrição da imagem
    og_imagem: /assets/img/blog/exemplo-og.jpg   (1200x630, uma por artigo; para redes sociais)
    autor: Guilherme Lavezzo        (opcional; é o padrão se faltar)
    autor_url: https://www.guilhermelavezzo.com.br/   (opcional; link do autor)
    resumo:                         (opcional; vira a caixa "Resumo rápido", no topo)
      - primeiro ponto
      - segundo ponto
    destaque: sim                   (opcional; fixa o artigo em primeiro na página do blog)
    rascunho: sim                   (opcional; artigo com rascunho não é publicado)

No texto, comece pelos títulos de seção (##). O título (H1) é o do cabeçalho. Perguntas e respostas
de uma seção chamada "Perguntas frequentes" (cada pergunta em ###) viram dados estruturados de FAQ.

Precisa do pacote "markdown":  pip install markdown
"""
import json
import math
import re
import sys
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_eventos import AGENCIA, MESES, SITE, WA_ICON, jsonld  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / 'tools' / 'blog' / 'posts'
SAIDA = ROOT / 'blog'
NOME_BLOG = 'Blog Anderson Viagem e Turismo'
OG_PADRAO = '/assets/img/og.jpg'
AUTOR_PADRAO = 'Guilherme Lavezzo'
AUTOR_URL_PADRAO = 'https://www.guilhermelavezzo.com.br/'
e = escape


# ---------------------------------------------------------------- leitura dos artigos
def ler_cabecalho(texto):
    """Cabeçalho simples: 'chave: valor' e listas com '- item'. Sem dependências."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', texto, re.S)
    if not m:
        raise ValueError('o arquivo precisa começar com o cabeçalho entre linhas ---')
    dados, chave = {}, None
    for linha in m.group(1).splitlines():
        if not linha.strip():
            continue
        item = re.match(r'^\s+-\s+(.*)$', linha)
        if item and chave:
            dados.setdefault(chave, []).append(item.group(1).strip())
            continue
        par = re.match(r'^([a-z_]+):\s*(.*)$', linha)
        if par:
            chave = par.group(1)
            dados[chave] = par.group(2).strip().strip('"') if par.group(2).strip() else []
    return dados, m.group(2)


def tirar_acentos(t):
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')


def slugify(valor, separador='-'):
    t = re.sub(r'[^a-z0-9]+', separador, tirar_acentos(valor).lower()).strip(separador)
    return t or 'secao'


def data_extenso(d):
    return f'{d.day} de {MESES[d.month - 1]} de {d.year}'


def carregar_posts():
    import markdown  # só aqui: o sitemap não precisa do pacote

    posts, avisos = [], []
    for arq in sorted(POSTS.glob('*.md')):
        dados, corpo = ler_cabecalho(arq.read_text(encoding='utf-8'))
        if str(dados.get('rascunho', '')).lower() in ('sim', 'true', 'yes'):
            print(f'  (rascunho ignorado: {arq.name})')
            continue
        obrigatorios = ['titulo', 'descricao', 'slug', 'data', 'categoria', 'imagem', 'imagem_alt']
        faltam = [c for c in obrigatorios if not dados.get(c)]
        if faltam:
            raise ValueError(f'{arq.name}: faltam no cabeçalho: {", ".join(faltam)}')
        md = markdown.Markdown(extensions=['extra', 'toc', 'sane_lists'],
                               extension_configs={'toc': {'slugify': lambda v, s: slugify(v), 'toc_depth': '2-3'}})
        html_corpo = md.convert(corpo)
        post = {
            **dados,
            'arquivo': arq.name,
            'data': date.fromisoformat(dados['data']),
            'atualizado': date.fromisoformat(dados['atualizado']) if dados.get('atualizado') else date.fromisoformat(dados['data']),
            'html': html_corpo,
            'secoes': [(t['id'], t['name']) for t in md.toc_tokens if t['level'] == 2],
            'faq': extrair_faq(html_corpo),
            'palavras': len(re.findall(r'\w+', re.sub(r'<[^>]+>', ' ', html_corpo))),
        }
        post['minutos'] = max(1, math.ceil(post['palavras'] / 200))
        post['url'] = f"{SITE}/blog/{post['slug']}/"
        avisos += validar(post, corpo)
        posts.append(post)
    # artigos com 'destaque: sim' ficam no topo; depois, os mais recentes primeiro
    posts.sort(key=lambda p: (str(p.get('destaque', '')).lower() in ('sim', 'true'), p['data'], p['slug']), reverse=True)
    slugs = [p['slug'] for p in posts]
    if len(slugs) != len(set(slugs)):
        raise ValueError('há dois artigos com o mesmo slug')
    return posts, avisos


def extrair_faq(html_corpo):
    """Perguntas (H3) e respostas da seção 'Perguntas frequentes', para os dados estruturados."""
    m = re.search(r'<h2[^>]*>\s*Perguntas frequentes\s*</h2>(.*)$', html_corpo, re.S | re.I)
    if not m:
        return []
    pares = re.findall(r'<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|$)', m.group(1), re.S)
    return [(re.sub(r'<[^>]+>', '', q).strip(), a.strip()) for q, a in pares]


def kb_do_arquivo(url_local):
    arq = ROOT / url_local.lstrip('/')
    return arq.stat().st_size / 1024 if arq.is_file() else None


def validar(p, corpo_md):
    """Checagens de SEO das skills blog-seo e seo-images. Só avisa; quem decide é você."""
    a = []
    t = p.get('titulo_seo') or p['titulo']
    if len(t) > 60:
        a.append(f"título para o Google com {len(t)} caracteres (ideal até 60); use titulo_seo")
    if len(t) < 20:
        a.append('título para o Google muito curto')
    d = len(p['descricao'])
    if not 110 <= d <= 165:
        a.append(f'descrição com {d} caracteres (ideal entre 120 e 160)')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', p['slug']):
        a.append('slug deve ter só minúsculas, números e hífens')
    if re.search(r'^# ', corpo_md, re.M):
        a.append('o texto tem um título "#" (H1); o H1 já vem do cabeçalho, comece pelos "##"')
    if re.search(r'^###\s', corpo_md, re.M) and not re.search(r'^##\s', corpo_md, re.M):
        a.append('há "###" sem nenhum "##" antes')
    internos = len(re.findall(r'\]\((/(?!/)[^)]*)\)', corpo_md))
    minimo = max(3, round(3 * p['palavras'] / 1000))
    if internos < minimo:
        a.append(f'só {internos} links internos (a skill pede de 3 a 5 por 1000 palavras; aqui, pelo menos {minimo})')
    if p['palavras'] < 350:
        a.append(f"texto curto ({p['palavras']} palavras)")
    # imagens (seo-images)
    textos_alt = [('capa', p['imagem_alt'])] + [('imagem do texto', m) for m in re.findall(r'<img[^>]*\salt="([^"]*)"', p['html'])]
    for onde, alt in textos_alt:
        if not 10 <= len(alt.strip()) <= 125:
            a.append(f'texto alternativo da {onde} com {len(alt.strip())} caracteres (ideal de 10 a 125)')
    for chave, limite, nome in (('imagem', 300, 'capa'), ('imagem_card', 100, 'miniatura'), ('og_imagem', 300, 'imagem de redes sociais')):
        if not p.get(chave):
            a.append(f'falta {chave} no cabeçalho ({nome})')
            continue
        kb = kb_do_arquivo(p[chave])
        if kb is None:
            a.append(f'{nome}: arquivo {p[chave]} não existe')
        elif kb > limite:
            a.append(f'{nome} com {kb:.0f} KB (acima de {limite} KB)')
    if p.get('og_imagem') and p['og_imagem'] == '/assets/img/og.jpg':
        a.append('a imagem de redes sociais deve ser única por artigo, não a padrão do site')
    return [f"{p['arquivo']}: {x}" for x in a]


# ---------------------------------------------------------------- peças de HTML
def pos_processar(html_corpo):
    """Links externos seguros, imagens com carregamento preguiçoso e tabelas que rolam no celular."""
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener noreferrer"', html_corpo)
    h = re.sub(r'<img (?![^>]*\bloading=)', '<img loading="lazy" ', h)
    h = re.sub(r'<img (?![^>]*\bdecoding=)', '<img decoding="async" ', h)
    h = re.sub(r'<table>(.*?)</table>', r'<div class="tabela"><table>\1</table></div>', h, flags=re.S)
    return h


def cabecalho_pagina(titulo_pagina, descricao, url, imagem_og, tipo, extra_meta, ld, imagem_preload=None):
    og = imagem_og if imagem_og.startswith('http') else SITE + imagem_og
    preload = ''
    if imagem_preload:
        href, srcset_, sizes_ = imagem_preload
        preload = (f'\n    <link rel="preload" as="image" href="{e(href)}" imagesrcset="{e(srcset_)}" '
                   f'imagesizes="{e(sizes_)}" fetchpriority="high">')
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{e(titulo_pagina)}</title>
    <meta name="description" content="{e(descricao)}">
    <meta name="robots" content="index, follow, max-image-preview:large">
    <link rel="canonical" href="{e(url)}">
    <meta name="author" content="Anderson Viagem e Turismo">
    <meta name="theme-color" content="#0F1217" media="(prefers-color-scheme: dark)">
    <meta name="theme-color" content="#EEF0F3" media="(prefers-color-scheme: light)">
    <meta property="og:type" content="{tipo}">
    <meta property="og:site_name" content="{e(NOME_BLOG)}">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:url" content="{e(url)}">
    <meta property="og:title" content="{e(titulo_pagina)}">
    <meta property="og:description" content="{e(descricao)}">
    <meta property="og:image" content="{e(og)}">{extra_meta}
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{e(titulo_pagina[:70])}">
    <meta name="twitter:description" content="{e(descricao[:200])}">
    <meta name="twitter:image" content="{e(og)}">
    <link rel="icon" href="/assets/favicon.png" type="image/png">
    <link rel="alternate" type="application/rss+xml" title="{e(NOME_BLOG)}" href="/blog/feed.xml">

    {ld}

    <!-- Página gerada por tools/gerar_blog.py. Edite o Markdown em tools/blog/posts e rode o script de novo. -->

    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-4ZXGBNM724"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-4ZXGBNM724');
    </script>

    <script>
        try {{
            var saved = localStorage.getItem('color-theme');
            if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved;
        }} catch (e) {{}}
    </script>

    <link rel="preload" href="/assets/fonts/big-shoulders-display-latin-1.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="/assets/fonts/instrument-sans-latin-3.woff2" as="font" type="font/woff2" crossorigin>{preload}
    <link rel="stylesheet" href="/assets/fonts.css">
    <link rel="stylesheet" href="/assets/icons/phosphor.css">
    <link rel="stylesheet" href="/assets/site.css">
    <link rel="stylesheet" href="/assets/blog.css">
</head>
'''


TOPO = f'''<body>
    <a class="skip-link" href="#conteudo">Pular para o conteúdo</a>

    <header class="topbar">
        <div class="wrap topbar-inner">
            <a class="logo" href="/" aria-label="Anderson Viagem e Turismo, página inicial" translate="no">
                <img class="logo-dark" src="/assets/logo-escuro.png" alt="Anderson Viagem e Turismo" width="120" height="58">
                <img class="logo-light" src="/assets/logo-claro.png" alt="Anderson Viagem e Turismo" width="120" height="58">
            </a>
            <nav class="nav" aria-label="Principal">
                <a href="/#agenda">Agenda</a>
                <a href="/#como-funciona">Como funciona</a>
                <a href="/#duvidas">Dúvidas</a>
                <a href="/blog/" aria-current="page">Blog</a>
                <a href="#contato">Contato</a>
            </nav>
            <div class="top-actions">
                <button class="icon-btn theme-toggle" id="theme-toggle" type="button" aria-label="Alternar tema claro e escuro">
                    <i class="ph ph-moon" aria-hidden="true"></i>
                    <i class="ph ph-sun" aria-hidden="true"></i>
                </button>
                <a class="icon-btn" href="https://www.instagram.com/andersonviagemeturismo/" target="_blank" rel="noopener noreferrer" aria-label="Instagram da Anderson Turismo">
                    <i class="ph ph-instagram-logo" aria-hidden="true"></i>
                </a>
                <a class="btn btn-wa" data-wa="" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
                <button class="icon-btn menu-btn" id="menu-btn" type="button" aria-label="Abrir menu" aria-expanded="false" aria-controls="mobile-nav">
                    <i class="ph ph-list" aria-hidden="true"></i>
                </button>
            </div>
        </div>
        <nav class="wrap mobile-nav" id="mobile-nav" aria-label="Menu" hidden>
            <a href="/#agenda">Agenda</a>
            <a href="/#como-funciona">Como funciona</a>
            <a href="/#duvidas">Dúvidas</a>
            <a href="/blog/" aria-current="page">Blog</a>
            <a href="#contato">Contato</a>
            <a class="btn btn-wa" data-wa="" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
        </nav>
    </header>
'''

CTA = f'''
        <section class="blog-cta" id="contato" aria-labelledby="cta-title">
            <div class="wrap">
                <div class="blog-cta-box">
                    <div>
                        <h2 id="cta-title">Bora pro próximo show?</h2>
                        <p>Veja as próximas saídas de Araraquara, São Carlos e região, ou chame a gente no WhatsApp para reservar a sua vaga.</p>
                    </div>
                    <div class="cta-row">
                        <a class="btn btn-primary" href="/#agenda">Ver próximas viagens<i class="ph ph-arrow-right" aria-hidden="true"></i></a>
                        <a class="btn btn-wa" data-wa="Vi o blog e quero reservar" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
                    </div>
                </div>
            </div>
        </section>
'''

RODAPE = f'''
    <footer class="wrap">
        <div class="footer-grid">
            <div>
                <h3>Atendimento</h3>
                <p>Segunda a sábado, 13h às 19h</p>
                <p>Domingos e feriados: fechado</p>
            </div>
            <div>
                <h3>Contato</h3>
                <p><a data-wa="" href="#" target="_blank" rel="noopener noreferrer">WhatsApp (16)&nbsp;98833-2631</a></p>
                <p><a href="https://www.instagram.com/andersonviagemeturismo/" target="_blank" rel="noopener noreferrer">@andersonviagemeturismo</a></p>
            </div>
            <div>
                <h3>Onde estamos</h3>
                <address>
                    <p>Av. Guanabara, 87</p>
                    <p>Jardim Brasil (Vila Xavier)</p>
                    <p>Araraquara, SP, 14811-108</p>
                    <p><a href="https://www.google.com/maps/search/?api=1&amp;query=Anderson+Viagem+e+Turismo+Av.+Guanabara+87+Araraquara+SP" target="_blank" rel="noopener noreferrer">Ver no mapa</a></p>
                </address>
            </div>
        </div>
        <div class="legal">
            <p>© <span data-year>2026</span> <span translate="no">Anderson Viagem e Turismo</span>. Todos os direitos reservados.</p>
            <p>Desenvolvido por <a href="https://www.guilhermelavezzo.com.br/" target="_blank" rel="noopener noreferrer">Guilherme Lavezzo</a></p>
        </div>
    </footer>

    <a class="wa-float" data-wa="" href="#" target="_blank" rel="noopener noreferrer" aria-label="Chamar no WhatsApp">
        <i class="ph-fill ph-whatsapp-logo" aria-hidden="true"></i>
    </a>

    <script src="/assets/site.js"></script>
</body>
</html>
'''


def miniatura(p):
    return p.get('imagem_card') or p['imagem']


def foco(p):
    """Atributo que escolhe a parte da foto que fica visível quando o cartão corta a imagem."""
    valor = p.get('imagem_foco', '')
    return f' style="object-position: {e(valor)}"' if re.fullmatch(r'\d{1,3}% \d{1,3}%', valor) else ''


def cartao(p, destaque=False, nivel=2):
    return f'''<article class="post-card{' is-first' if destaque else ''}">
                    <a class="post-card-media" href="/blog/{e(p['slug'])}/" tabindex="-1" aria-hidden="true">
                        <img src="{e(miniatura(p))}" alt="" width="800" height="500" loading="{'eager' if destaque else 'lazy'}" decoding="async"{foco(p)}>
                    </a>
                    <div class="post-card-body">
                        <p class="post-cat">{e(p['categoria'])}</p>
                        <h{nivel}><a href="/blog/{e(p['slug'])}/">{e(p['titulo'])}</a></h{nivel}>
                        <p class="post-card-desc">{e(p['descricao'])}</p>
                        <p class="post-meta"><time datetime="{p['data'].isoformat()}">{data_extenso(p['data'])}</time><span aria-hidden="true">·</span>{p['minutos']} min de leitura</p>
                        <span class="post-more" aria-hidden="true">Ler artigo<i class="ph ph-arrow-right"></i></span>
                    </div>
                </article>'''


# ---------------------------------------------------------------- páginas
def pagina_indice(posts):
    titulo = 'Blog: dicas de excursão para shows | Anderson Viagem e Turismo'
    descricao = ('Guias e dicas para ir a shows e festivais de excursão saindo de Araraquara, São Carlos e região: '
                 'como reservar, o que levar e como funciona a viagem.')
    url = f'{SITE}/blog/'
    blog = {'@type': 'Blog', '@id': f'{url}#blog', 'url': url, 'name': NOME_BLOG, 'description': descricao,
            'inLanguage': 'pt-BR', 'publisher': {'@id': AGENCIA['@id']},
            'blogPost': [{'@type': 'BlogPosting', 'headline': p['titulo'], 'url': p['url'],
                          'datePublished': p['data'].isoformat()} for p in posts]}
    migalhas = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': f'{SITE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': url}]}
    cartoes = '\n                '.join(cartao(p, i == 0) for i, p in enumerate(posts))
    vazio = '<p class="blog-vazio">Os primeiros artigos chegam em breve.</p>' if not posts else ''
    corpo = f'''
    <main id="conteudo">
        <section class="blog-hero" aria-labelledby="blog-title">
            <div class="wrap">
                <nav class="crumbs" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><span aria-current="page">Blog</span></nav>
                <h1 id="blog-title">Blog <span class="hl">Anderson Turismo</span></h1>
                <p class="lede">Guias e dicas para ir ao show de excursão, saindo de Araraquara, São Carlos e região.</p>
            </div>
        </section>
        <section class="blog-lista" aria-label="Artigos">
            <div class="wrap">
                {vazio}
                <div class="post-grid">
                {cartoes}
                </div>
            </div>
        </section>
{CTA}    </main>
'''
    cab = cabecalho_pagina(titulo, descricao, url, OG_PADRAO, 'website', '', jsonld(AGENCIA, blog, migalhas))
    return cab + TOPO + corpo + RODAPE


def pagina_post(p, todos):
    # o nome da empresa entra no título da aba só se couber (o Google corta perto de 60 a 65 caracteres)
    base = p.get('titulo_seo') or p['titulo']
    com_marca = f"{base} | Anderson Turismo"
    titulo_pagina = com_marca if len(com_marca) <= 65 else base
    og_imagem = p.get('og_imagem') or OG_PADRAO
    img_abs = p['imagem'] if p['imagem'].startswith('http') else SITE + p['imagem']
    og_abs = og_imagem if og_imagem.startswith('http') else SITE + og_imagem
    card = miniatura(p)
    srcset = f"{card} 800w, {p['imagem']} 1600w"
    tamanhos = '(max-width: 960px) 100vw, 940px'
    credito = f'<figcaption class="post-credito">{e(p["imagem_credito"])}</figcaption>' if p.get('imagem_credito') else ''
    autor = p.get('autor') or AUTOR_PADRAO
    autor_url = p.get('autor_url') or (AUTOR_URL_PADRAO if autor == AUTOR_PADRAO else '')
    pessoa = bool(autor_url) or not autor.lower().startswith('equipe')
    autor_no = {'@type': 'Person' if pessoa else 'Organization', 'name': autor}
    if autor_url:
        autor_no['url'] = autor_url
    autor_html = (f'<a href="{e(autor_url)}" target="_blank" rel="noopener noreferrer author">{e(autor)}</a>'
                  if autor_url else e(autor))
    artigo = {
        '@type': 'BlogPosting',
        '@id': f"{p['url']}#artigo",
        'headline': p['titulo'],
        'description': p['descricao'],
        'image': [img_abs, og_abs],
        'datePublished': p['data'].isoformat(),
        'dateModified': p['atualizado'].isoformat(),
        'inLanguage': 'pt-BR',
        'wordCount': p['palavras'],
        'author': autor_no,
        'publisher': {'@type': 'Organization', '@id': AGENCIA['@id'], 'name': 'Anderson Viagem e Turismo',
                      'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/logo-claro.png'}},
        'mainEntityOfPage': p['url'],
    }
    migalhas = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': f'{SITE}/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': f'{SITE}/blog/'},
        {'@type': 'ListItem', 'position': 3, 'name': p['titulo'], 'item': p['url']}]}
    nos = [AGENCIA, artigo, migalhas]
    if p['faq']:
        nos.append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q,
             'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', a)).strip()}}
            for q, a in p['faq']]})
    extra_meta = (f'\n    <meta property="article:published_time" content="{p["data"].isoformat()}">'
                  f'\n    <meta property="article:modified_time" content="{p["atualizado"].isoformat()}">'
                  f'\n    <meta property="article:section" content="{e(p["categoria"])}">')

    resumo = ''
    if p.get('resumo'):
        itens = ''.join(f'<li>{e(i)}</li>' for i in p['resumo'])
        resumo = f'<aside class="resumo" aria-label="Resumo rápido"><p class="resumo-titulo">Resumo rápido</p><ul>{itens}</ul></aside>\n'
    sumario = ''
    if len(p['secoes']) >= 3:
        links = ''.join(f'<li><a href="#{i}">{e(n)}</a></li>' for i, n in p['secoes'])
        sumario = f'<nav class="toc" aria-label="Neste artigo"><p class="toc-titulo">Neste artigo</p><ol>{links}</ol></nav>'

    relacionados = [x for x in todos if x['slug'] != p['slug']]
    relacionados.sort(key=lambda x: (x['categoria'] != p['categoria'], -x['data'].toordinal()))
    rel_html = ''
    if relacionados:
        rel_html = f'''
        <section class="relacionados" aria-labelledby="rel-title">
            <div class="wrap">
                <h2 id="rel-title">Continue lendo</h2>
                <div class="post-grid">
                {chr(10).join(cartao(x, nivel=3) for x in relacionados[:3])}
                </div>
            </div>
        </section>
'''
    atualizado = ''
    if p['atualizado'] != p['data']:
        atualizado = f'<span aria-hidden="true">·</span>atualizado em <time datetime="{p["atualizado"].isoformat()}">{data_extenso(p["atualizado"])}</time>'
    corpo = f'''
    <main id="conteudo">
        <article class="post">
            <header class="post-head wrap">
                <nav class="crumbs" aria-label="Você está em"><a href="/">Início</a><span aria-hidden="true">/</span><a href="/blog/">Blog</a><span aria-hidden="true">/</span><span aria-current="page">{e(p['categoria'])}</span></nav>
                <p class="post-cat">{e(p['categoria'])}</p>
                <h1>{e(p['titulo'])}</h1>
                <p class="lede">{e(p['descricao'])}</p>
                <p class="post-meta"><time datetime="{p['data'].isoformat()}">{data_extenso(p['data'])}</time>{atualizado}<span aria-hidden="true">·</span>{p['minutos']} min de leitura<span aria-hidden="true">·</span>Por {autor_html}</p>
            </header>
            <figure class="post-cover wrap">
                <img src="{e(p['imagem'])}" srcset="{e(srcset)}" sizes="{tamanhos}" alt="{e(p['imagem_alt'])}" width="1600" height="1000" fetchpriority="high" decoding="async">
                {credito}
            </figure>
            <div class="post-layout wrap">
                {sumario}
                <div class="prose">
{resumo}{pos_processar(p['html'])}
                </div>
            </div>
        </article>
{rel_html}{CTA}    </main>
'''
    cab = cabecalho_pagina(titulo_pagina, p['descricao'], p['url'], og_imagem, 'article', extra_meta, jsonld(*nos),
                           imagem_preload=(p['imagem'], srcset, tamanhos))
    return cab + TOPO + corpo + RODAPE


def data_curta(d):
    return f"{d.day} de {MESES[d.month - 1][:3]} de {d.year}"


def cartao_home(p, principal=False):
    return f'''<article class="hb-card{' is-main' if principal else ''}">
                    <a class="hb-media" href="/blog/{e(p['slug'])}/" tabindex="-1" aria-hidden="true">
                        <img src="{e(miniatura(p))}" alt="" width="800" height="500" loading="lazy" decoding="async"{foco(p)}>
                        <span class="hb-chip">{e(p['categoria'])}</span>
                    </a>
                    <div class="hb-body">
                        <p class="hb-meta"><time datetime="{p['data'].isoformat()}">{data_curta(p['data'])}</time><span aria-hidden="true">·</span>{p['minutos']} min de leitura</p>
                        <h3><a href="/blog/{e(p['slug'])}/">{e(p['titulo'])}</a></h3>
                        <p class="hb-desc">{e(p['descricao'])}</p>
                        <span class="hb-more" aria-hidden="true">Ler artigo<i class="ph ph-arrow-right"></i></span>
                    </div>
                </article>'''


def bloco_home(posts):
    """Seção da home: um cartão grande e até dois pequenos (destaque primeiro, depois os mais recentes)."""
    if not posts:
        return ''
    mostrados = posts[:3]
    cartoes = '\n                '.join(cartao_home(p, i == 0) for i, p in enumerate(mostrados))
    return f'''        <section class="section home-blog" id="blog" aria-labelledby="blog-home-title">
            <div class="wrap">
                <h2 class="hb-title" id="blog-home-title"><a href="/blog/">Direto do blog<i class="ph ph-arrow-right" aria-hidden="true"></i></a></h2>
                <div class="hb-grid" data-n="{len(mostrados)}">
                {cartoes}
                </div>
            </div>
        </section>
'''


def atualizar_home(posts):
    """Preenche a seção do blog na home (entre os marcadores). Sem artigos, a seção some."""
    home = ROOT / 'index.html'
    html = home.read_text(encoding='utf-8')
    padrao = re.compile(r'(<!--blog:inicio-->).*?(<!--/blog:inicio-->)', re.S)
    assert padrao.search(html), 'marcadores blog:inicio não encontrados no index.html'
    bloco = bloco_home(posts)
    html = padrao.sub(lambda m: f"{m.group(1)}\n{bloco}        {m.group(2)}", html)
    home.write_text(html, encoding='utf-8')


def feed_rss(posts):
    itens = ''.join(
        f"<item><title>{e(p['titulo'])}</title><link>{p['url']}</link><guid isPermaLink=\"true\">{p['url']}</guid>"
        f"<pubDate>{p['data'].strftime('%a, %d %b %Y')} 12:00:00 GMT</pubDate><description>{e(p['descricao'])}</description></item>\n"
        for p in posts)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f'<title>{e(NOME_BLOG)}</title><link>{SITE}/blog/</link>'
            '<description>Dicas de excursão para shows saindo de Araraquara, São Carlos e região.</description>'
            f'<language>pt-BR</language>\n{itens}</channel></rss>\n')


def urls_do_blog():
    """Endereços do blog para o sitemap (usado por tools/gerar_eventos.py). Lê só os cabeçalhos."""
    achados = []
    for arq in sorted(POSTS.glob('*.md')):
        dados, _ = ler_cabecalho(arq.read_text(encoding='utf-8'))
        if str(dados.get('rascunho', '')).lower() in ('sim', 'true', 'yes'):
            continue
        achados.append((f"{SITE}/blog/{dados['slug']}/", date.fromisoformat(dados.get('atualizado') or dados['data'])))
    if not achados:
        return []
    return [(f'{SITE}/blog/', max(d for _, d in achados))] + achados


def gerar_blog(atualizar_site=True):
    posts, avisos = carregar_posts()
    SAIDA.mkdir(exist_ok=True)
    # remove páginas de artigos que não existem mais
    for pasta in SAIDA.iterdir():
        if pasta.is_dir() and pasta.name not in {p['slug'] for p in posts}:
            for f in pasta.rglob('*'):
                if f.is_file():
                    f.unlink()
            for d in sorted([x for x in pasta.rglob('*') if x.is_dir()], reverse=True) + [pasta]:
                d.rmdir()
    (SAIDA / 'index.html').write_text(pagina_indice(posts), encoding='utf-8')
    for p in posts:
        pasta = SAIDA / p['slug']
        pasta.mkdir(exist_ok=True)
        (pasta / 'index.html').write_text(pagina_post(p, posts), encoding='utf-8')
        print(f"gerado: blog/{p['slug']}/  | {p['palavras']} palavras, {p['minutos']} min | título {len(p['titulo'])} | descrição {len(p['descricao'])}")
    (SAIDA / 'feed.xml').write_text(feed_rss(posts), encoding='utf-8')
    atualizar_home(posts)
    print(f'blog/index.html, feed.xml, home e {len(posts)} artigo(s) gerados')
    if avisos:
        print('\nAvisos de SEO (não impedem a geração):')
        for a in avisos:
            print('  -', a)
    if atualizar_site:  # sitemap e páginas de evento (inclui os endereços do blog)
        from gerar_eventos import gerar_site
        gerar_site()


if __name__ == '__main__':
    gerar_blog()
