"""Gera as páginas "Saiba mais" de cada evento a partir dos dados abaixo.

Uso (na raiz do repositório):
    python tools/gerar_eventos.py

Para criar uma página nova: copie um bloco de EVENTOS, ajuste os campos e rode o script.
O arquivo sai como <slug>.html, ao lado do index.html.

O script também gera robots.txt, sitemap.xml, os dados estruturados (JSON-LD) e os links de
"Excursões abertas" da home. Páginas encerradas (todas as datas no passado, ou encerrado=True)
saem com noindex e ficam fora do sitemap. Rode de novo depois de cada mudança de data.
"""
import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
MESES_CURTOS = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
DIAS_SEMANA = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

UNSPLASH = 'https://images.unsplash.com/photo-{id}?w={w}&q=70&auto=format&fit=crop'

SITE = 'https://www.andersonviagemeturismo.com.br'
HOJE = date.today()

AGENCIA = {
    '@type': 'TravelAgency',
    '@id': f'{SITE}/#agencia',
    'name': 'Anderson Viagem e Turismo',
    'url': f'{SITE}/',
    'logo': f'{SITE}/assets/logo-claro.png',
    'image': f'{SITE}/assets/img/og.jpg',
    'description': 'Excursões de ida e volta para shows e festivais saindo de Araraquara, São Carlos, Ibaté, Rio Claro e Limeira, com guia credenciado e seguro viagem.',
    'telephone': '+55-16-98833-2631',
    'address': {
        '@type': 'PostalAddress',
        'streetAddress': 'Av. Guanabara, 87, Jardim Brasil (Vila Xavier)',
        'addressLocality': 'Araraquara',
        'addressRegion': 'SP',
        'postalCode': '14811-108',
        'addressCountry': 'BR',
    },
    'areaServed': [{'@type': 'City', 'name': c} for c in ['Araraquara', 'São Carlos', 'Ibaté', 'Rio Claro', 'Limeira']],
    'openingHoursSpecification': [{
        '@type': 'OpeningHoursSpecification',
        'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        'opens': '13:00',
        'closes': '19:00',
    }],
    'sameAs': ['https://www.instagram.com/andersonviagemeturismo/'],
}

EVENTOS = [
    {
        'slug': 'bts',
        'event_id': 57,
        'titulo_pagina': 'Excursão BTS 2026 saindo de Araraquara | Anderson Turismo',
        'descricao': 'Excursão ida e volta para o BTS no MorumBIS (28, 30 e 31 de outubro) saindo de Araraquara, São Carlos e região. Guia credenciado e Cadastur.',
        'nome_link': 'Excursão BTS no MorumBIS',
        'keywords': 'excursão ida e volta BTS, excursão BTS Araraquara, van show BTS Araraquara e cidades, transporte ida e volta show BTS, caravana BTS interior SP, Anderson Turismo, ônibus show MorumBIS, viagem show BTS São Carlos Matão',
        'assunto_whatsapp': 'BTS World Tour Arirang (2026)',
        'nome_curto': 'BTS',
        'h1': ['BTS no Brasil', 'Arirang 2026'],
        'lede': 'O maior retorno da história. Excursão ida e volta para o MorumBIS saindo de Araraquara e região.',
        'hero_img': 'https://billboard-com-br.s3.amazonaws.com/wp-content/uploads/2026/03/27082354/BTS-11.jpg',
        'hero_alt': 'Os sete integrantes do BTS lado a lado',
        'hero_wh': (1200, 630),
        'local': 'MorumBIS, São Paulo',
        'datas': [
            {'dia': date(2026, 10, 28)},
            {'dia': date(2026, 10, 30), 'destaque': 'Data mais procurada'},
            {'dia': date(2026, 10, 31)},
        ],
        'sobre_titulo': 'O retorno mais aguardado da história',
        'sobre': [
            'Depois de concluírem o serviço militar, <strong>RM, Jin, SUGA, j-hope, Jimin, V e Jung Kook</strong> estão de volta aos palcos juntos. A turnê de 2026 marca o reencontro do septeto com o <strong>ARMY</strong> em uma celebração histórica.',
            'Mais do que um grupo musical, o <strong>BTS</strong> quebrou recordes e virou referência do pop no século 21. Espere uma superprodução no MorumBIS, coreografias impecáveis e os maiores sucessos da carreira.',
        ],
        'stats': [('+40 bilhões', 'de streams no Spotify'), ('7 anos', 'de espera do ARMY BR')],
        'sobre_img': 'https://cdn.getcrowder.com/images/a83dd21d-fd6a-4caf-9a3f-8c634e8ecbc7-bts1920x720landing.gif',
        'sobre_alt': 'Arte oficial da BTS World Tour Arirang',
        'sobre_wh': (1920, 720),
        'sobre_contain': False,
        'ingresso_canal': 'nos canais oficiais (Ticketmaster)',
        'ingresso_colunas': ['Setor', 'Inteira', 'Meia'],
        'ingressos': [
            ('Arquibancada', 'R$ 680,00', 'R$ 340,00'),
            ('Cadeira Superior', 'R$ 980,00', 'R$ 490,00'),
            ('Cadeira Inferior', 'R$ 1.080,00', 'R$ 540,00'),
            ('Pista', 'R$ 1.250,00', 'R$ 625,00'),
        ],
        'ingresso_nota': 'Valores oficiais de referência. Confira sempre no canal de venda.',
        'datas_intro': 'Bate-volta com segurança, conforto e a melhor galera. Escolha a data do seu ingresso e reserve seu assento.',
        'inclui': ['Transporte ida e volta', 'Veículo executivo com ar-condicionado e poltronas reclináveis', 'Guia credenciado Cadastur'],
    },
    {
        'slug': 'luan_santana',
        'event_id': 32,
        'titulo_pagina': 'Excursão Luan Santana em Ribeirão Preto | Anderson Turismo',
        'descricao': 'Excursão ida e volta para o show do Luan Santana em Ribeirão Preto, dia 19 de setembro, saindo de Araraquara e São Carlos.',
        'nome_link': 'Excursão Luan Santana',
        'keywords': 'excursão Luan Santana, excursão Luan Santana Ribeirão Preto, van show Luan Santana Araraquara, transporte ida e volta show Luan Santana, Anderson Turismo',
        'assunto_whatsapp': 'Luan Santana em Ribeirão Preto',
        'nome_curto': 'Luan',
        'h1': ['Luan Santana', 'em Ribeirão Preto'],
        'lede': 'A turnê que está parando o Brasil. Excursão ida e volta saindo de Araraquara e região.',
        'hero_img': 'https://billboard-com-br.s3.amazonaws.com/wp-content/uploads/2025/12/15114956/luan-santana-3.jpg',
        'hero_alt': 'Luan Santana cantando no palco',
        'hero_wh': (1200, 630),
        'local': 'Ribeirão Preto, SP',
        'datas': [{'dia': date(2026, 9, 19)}],
        'sobre_titulo': 'Uma noite inesquecível em Ribeirão Preto',
        'sobre': [
            'Comandando multidões por onde passa, <strong>Luan Santana</strong> desembarca em Ribeirão Preto para um show grandioso, com os maiores sucessos da carreira e os hits novos que não saem do topo das paradas.',
            'Espere uma estrutura digna dos maiores festivais. Cante junto os clássicos românticos e as músicas que embalam o Brasil. A festa está garantida, e a gente te leva até lá com segurança.',
        ],
        'stats': [('+2 bilhões', 'de streams e visualizações'), ('Top 1', 'nas paradas do Brasil')],
        'sobre_img': 'https://billboard.com.br/wp-content/uploads/2024/05/IMG_3206-3-1024x725.jpg',
        'sobre_alt': 'Luan Santana durante um show',
        'sobre_wh': (1024, 725),
        'sobre_contain': False,
        'ingresso_canal': 'nos canais e ticketeiras oficiais do evento',
        'ingresso_colunas': ['Setor', 'Inteira', 'Meia/Solidário'],
        'ingressos': [
            ('Pista', 'R$ 140,00', 'R$ 70,00'),
            ('Área VIP', 'R$ 260,00', 'R$ 130,00'),
            ('Camarote / Premium', 'R$ 450,00', 'R$ 225,00'),
        ],
        'ingresso_nota': 'Preços de referência sujeitos a virada de lote pelos organizadores.',
        'datas_intro': 'Bate-volta de Araraquara e região com segurança, conforto e a melhor galera. Reserve seu assento para a grande noite.',
        'inclui': ['Transporte ida e volta', 'Veículo executivo premium', 'Guia credenciado Cadastur', 'Pontualidade garantida'],
    },
    {
        'slug': 'korn',
        'event_id': None,
        'titulo_pagina': 'Excursão Korn em São Paulo | Anderson Turismo',
        'descricao': 'Excursão ida e volta para o show do Korn em São Paulo, saindo de Araraquara e região. Transporte executivo com guia credenciado.',
        'nome_link': 'Excursão Korn',
        'keywords': 'excursão Korn, excursão Korn São Paulo, van show Korn Araraquara, transporte ida e volta show Korn, excursão rock interior SP, Anderson Turismo',
        'assunto_whatsapp': 'Korn em São Paulo',
        'nome_curto': 'Korn',
        'h1': ['Korn', 'no Brasil'],
        'lede': 'Os pioneiros do nu metal estão de volta. Excursão ida e volta saindo de Araraquara e região.',
        'hero_img': UNSPLASH.format(id='1493225457124-a3eb161ffa5f', w=1400),
        'hero_alt': 'Fã com o braço erguido no meio da fumaça de um show',
        'hero_wh': (1400, 934),
        'local': 'São Paulo, SP',
        'datas': [{'dia': date(2026, 5, 16)}],
        'sobre_titulo': 'O peso e a energia do nu metal',
        'sobre': [
            'Com riffs pesados, linhas de baixo inconfundíveis e os vocais insanos de <strong>Jonathan Davis</strong>, o Korn revolucionou o metal nos anos 90 e continua arrastando multidões em shows que viram catarse coletiva.',
            'Prepare-se para bater cabeça e gritar clássicos em uma noite histórica. Vá com a nossa excursão, deixe o estresse de dirigir com a gente e foque nas rodas e na energia da banda.',
        ],
        'stats': [('30 anos', 'de carreira'), ('+40 milhões', 'de álbuns vendidos')],
        'sobre_img': 'https://preview.redd.it/what-is-the-opinion-on-korn-v0-j7jdcgfwayyd1.jpeg?auto=webp&s=361fb22cf8df7e7dc40908a7f2e26449144610ef',
        'sobre_alt': 'Logotipo da banda Korn',
        'sobre_wh': (900, 900),
        'sobre_contain': True,
        'ingresso_canal': 'nos canais oficiais do evento',
        'ingresso_colunas': ['Setor', 'Inteira', 'Meia'],
        'ingressos': [
            ('Cadeira Superior', 'R$ 365,00', 'R$ 182,50'),
            ('Cadeira Inferior', 'R$ 645,00', 'R$ 322,50'),
            ('Pista', 'R$ 495,00', 'R$ 247,50'),
            ('Pista Premium', 'R$ 995,00', 'R$ 497,50'),
        ],
        'ingresso_nota': 'Preços e setores de referência. Sujeito à organização oficial do evento.',
        'datas_intro': 'Bate-volta de Araraquara e região direto para o show. Reserve seu assento e preocupe-se só em bater cabeça.',
        'inclui': ['Transporte ida e volta', 'Veículo executivo premium', 'Guia credenciado Cadastur', 'Chegada cedo no local'],
    },
    {
        # Festival vendido em combos (transporte + ingresso), sem data publicada na página
        'slug': 'joao_rock',
        'event_id': None,
        'titulo_pagina': 'Excursão João Rock em Ribeirão Preto | Anderson Turismo',
        'descricao': 'Excursão para o festival João Rock em Ribeirão Preto, saindo de Araraquara e São Carlos. Combos com transporte e ingresso.',
        'nome_link': 'Excursão João Rock',
        'keywords': 'excursão João Rock, excursão Ribeirão Preto, van João Rock Araraquara, transporte ida e volta festival, Anderson Turismo, ônibus João Rock interior SP',
        'encerrado': True,  # festival de 2026 já aconteceu; tire esta linha quando houver nova data
        'assunto_whatsapp': 'João Rock 2026',
        'nome_curto': 'João Rock',
        'chamada_final': 'Bora pro João Rock?',
        'h1': ['João Rock', '2026'],
        'lede': 'Paz, música e energia em Ribeirão Preto. Bate-volta seguro e confortável saindo de Araraquara e São Carlos.',
        'hero_img': 'https://www.sucessosa.com.br/miniatura.php?src=rod5.jpg&x=600&q=80',
        'hero_alt': 'Palco do festival com fogos de artifício e telões',
        'hero_wh': (600, 399),
        'local': 'Parque Permanente de Exposições, Ribeirão Preto',
        'datas': [],
        'fatos': [
            ('Festival', 'João Rock 2026', 'amber'),
            ('Local', 'Parque de Exposições, Ribeirão Preto', 'small'),
            ('Embarque em', 'Araraquara e São Carlos', 'small'),
            ('Retorno', '45 min após o último show', 'amber'),
        ],
        'sobre_titulo': 'Música, paz e atitude',
        'sobre': [
            'Nascido em 2002, o <strong>João Rock</strong> virou o maior ponto de encontro da música brasileira no interior paulista. É o dia do ano em que Ribeirão Preto respira rock nacional, rap, reggae e MPB.',
            'São vários palcos, como o Palco João Rock, com estrutura dupla para shows sem intervalo, o Palco Brasil e o Fortalecendo a Cena. Evite o cansaço do trânsito e aproveite o festival ao máximo com a nossa excursão.',
        ],
        'stats': [('14h', 'de música sem parar'), ('Desde 2002', 'no interior paulista')],
        'sobre_img': 'https://images.stockcake.com/public/3/8/d/38dcdced-6883-439e-949a-629c0a525236_large/rock-concert-energy-stockcake.jpg',
        'sobre_alt': 'Banda tocando para o público com as mãos para cima',
        'sobre_wh': (384, 672),
        'sobre_contain': False,
        'pacotes_titulo': 'Pacotes e combos',
        'datas_intro': 'Curta o festival sem se preocupar com trânsito, estacionamento ou direção na volta. Escolha seu pacote e a gente cuida da viagem.',
        'datas_nota': 'Vagas limitadas. Os combos incluem o ingresso do festival; o pacote Somente transporte não inclui.',
        'pacotes': [
            {'nome': 'Somente transporte', 'sub': 'Bate e volta', 'preco': 'R$ 110', 'preco_nota': 'à vista no Pix',
             'itens': ['Ônibus de turismo com ar-condicionado e banheiro', 'Seguro viagem individual', '50% de entrada e o restante até 20/07', 'Cartão em até 12x (com taxa)', 'Ingresso não incluso'],
             'botao': 'Reservar transporte'},
            {'nome': 'Pista Meia', 'sub': 'Viagem + ingresso', 'preco': 'R$ 360', 'preco_nota': 'no Pix (mais de 10% off)',
             'itens': ['Ingresso Pista (meia)', 'Excursão completa, ida e volta', 'Cartão: R$ 411 (6x de R$ 68,50)'],
             'botao': 'Reservar combo'},
            {'nome': 'Pista Solidária', 'sub': 'Viagem + ingresso', 'destaque': 'Mais vendido', 'preco': 'R$ 385', 'preco_nota': 'no Pix (mais de 10% off)',
             'itens': ['Ingresso Pista Solidária', 'Excursão completa, ida e volta', 'Levar 1 kg de alimento no dia do evento', 'Cartão: R$ 439,50 (6x de R$ 73,25)'],
             'botao': 'Reservar combo'},
            {'nome': 'Camarote JR Meia', 'sub': 'Viagem + ingresso premium', 'preco': 'R$ 670', 'preco_nota': 'no Pix (mais de 10% off)',
             'itens': ['Ingresso Camarote JR (meia)', 'Excursão completa, ida e volta', 'Cartão: R$ 765 (6x de R$ 127,50)'],
             'botao': 'Reservar camarote'},
        ],
        'embarques_titulo': 'Embarques e retorno',
        'embarques': [
            ('ph-map-pin', 'Araraquara', 'Praça Pedro de Toledo'),
            ('ph-map-pin', 'São Carlos', 'Hospital Universitário'),
            ('ph-flag-checkered', 'João Rock', 'Parque Permanente de Exposições, Ribeirão Preto. Viagem direta.'),
            ('ph-arrow-u-up-left', 'Retorno', 'Saída 45 minutos após o último show, para os mesmos locais de embarque.'),
        ],
        'regras_titulo': 'Informações importantes',
        'regras': [
            ('ph-receipt-x', 'Sem devolução por desistência', 'Não devolvemos valores em caso de desistência do passageiro.'),
            ('ph-user-switch', 'Troca de titular até 7 dias antes', 'A reserva pode passar para outra pessoa até 7 dias antes do evento.'),
            ('ph-calendar-check', 'Evento adiado, excursão mantida', 'A viagem vai automaticamente para a nova data, sem direito a reembolso.'),
            ('ph-arrow-counter-clockwise', 'Reembolso só com cancelamento', 'Devolvemos o valor apenas se a organização cancelar o evento de vez.'),
        ],
    },
]

REGRAS_PADRAO = [
    ('ph-clock', 'Tolerância de 10 minutos', 'Chegue com antecedência. O transporte sai no horário combinado, sem esperar.'),
    ('ph-bus', 'Volta 45 minutos após o show', 'A saída de volta é no mesmo ponto onde você desceu, 45 minutos após o fim oficial.'),
    ('ph-calendar-check', 'Show adiado, excursão mantida', 'A viagem acontece na nova data do show. Adiamento não gera reembolso.'),
]


def e(s):
    return escape(str(s), quote=True)


def lista_pt(itens):
    return itens[0] if len(itens) == 1 else f"{', '.join(itens[:-1])} e {itens[-1]}"


def resumo_datas(datas):
    dias = [d['dia'] for d in datas]
    if len({(d.year, d.month) for d in dias}) == 1:
        numeros = [f'{d.day:02d}' for d in dias]
        return f"{lista_pt(numeros)} {MESES_CURTOS[dias[0].month - 1]} {dias[0].year}"
    return lista_pt([f'{d.day:02d} {MESES_CURTOS[d.month - 1]} {d.year}' for d in dias])


def data_extenso(d):
    return f'{d.day} de {MESES[d.month - 1]}'


WA_ICON = '<i class="ph-fill ph-whatsapp-logo" aria-hidden="true"></i>'


def encerrado(ev):
    if ev.get('encerrado'):
        return True
    return bool(ev['datas']) and all(d['dia'] < HOJE for d in ev['datas'])


def jsonld(*nodes):
    corpo = json.dumps({'@context': 'https://schema.org', '@graph': list(nodes)}, ensure_ascii=False, indent=2)
    return '<script type="application/ld+json">\n' + corpo.replace('</', '<\\/') + '\n    </script>'


def jsonld_evento(ev):
    url = f"{SITE}/{ev['slug']}.html"
    viagem = {
        '@type': 'TouristTrip',
        '@id': f'{url}#excursao',
        'name': ev['titulo_pagina'].split(' | ')[0],
        'description': ev['descricao'],
        'url': url,
        'image': ev['hero_img'],
        'touristType': 'Fãs de shows e festivais',
        'provider': {'@id': AGENCIA['@id']},
    }
    migalhas = {
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': f'{SITE}/'},
            {'@type': 'ListItem', 'position': 2, 'name': ev['titulo_pagina'].split(' | ')[0], 'item': url},
        ],
    }
    return jsonld(AGENCIA, viagem, migalhas)


def jsonld_home():
    site = {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': f'{SITE}/', 'name': 'Anderson Viagem e Turismo',
            'inLanguage': 'pt-BR', 'publisher': {'@id': AGENCIA['@id']}}
    return jsonld(AGENCIA, site)


def pagina(ev):
    multi = len(ev['datas']) > 1
    assunto = ev['assunto_whatsapp']
    hero_w, hero_h = ev['hero_wh']
    sobre_w, sobre_h = ev['sobre_wh']
    datas_iso = ','.join(d['dia'].isoformat() for d in ev['datas'])
    url_pagina = f"{SITE}/{ev['slug']}.html"
    robots = 'noindex, follow' if encerrado(ev) else 'index, follow, max-image-preview:large'

    cards = []
    tem_destaque = any(d.get('destaque') for d in ev['datas'])
    for d in ev['datas']:
        dia = d['dia']
        topo = d.get('destaque')
        itens = ''.join(f'<li><i class="ph ph-check-circle" aria-hidden="true"></i><span>{e(i)}</span></li>' for i in ev['inclui'])
        rotulo = 'Reservar esta data' if multi else 'Reservar vaga'
        cards.append(f'''
                    <article class="date-card{' is-top' if topo else ''}" data-date="{dia.isoformat()}">
                        <div class="date-head">
                            {f'<p class="tag-top">{e(topo)}</p>' if topo else ('<p class="tag-top" aria-hidden="true">&nbsp;</p>' if tem_destaque else '')}
                            <h3 class="day">{dia.day:02d} {MESES_CURTOS[dia.month - 1]}</h3>
                            <p class="weekday">{DIAS_SEMANA[dia.weekday()]}, {dia.year}</p>
                        </div>
                        <div class="tear" aria-hidden="true"></div>
                        <div class="date-body">
                            <ul class="includes">{itens}</ul>
                            <a class="btn btn-wa" data-wa="{e(assunto)}, dia {data_extenso(dia)}" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}{rotulo}</a>
                            <p class="closed">Data encerrada</p>
                        </div>
                    </article>''')

    pacotes = ev.get('pacotes') or []
    tem_destaque_pacote = any(p.get('destaque') for p in pacotes)
    for pk in pacotes:
        topo = pk.get('destaque')
        itens = ''.join(f'<li><i class="ph ph-check-circle" aria-hidden="true"></i><span>{e(i)}</span></li>' for i in pk['itens'])
        marca = f'<p class="tag-top">{e(topo)}</p>' if topo else ('<p class="tag-top" aria-hidden="true">&nbsp;</p>' if tem_destaque_pacote else '')
        cards.append(f'''
                    <article class="date-card pkg{' is-top' if topo else ''}">
                        <div class="date-head">
                            {marca}
                            <h3 class="day">{e(pk['nome'])}</h3>
                            <p class="weekday">{e(pk['sub'])}</p>
                            <p class="price"><b>{e(pk['preco'])}</b><span>{e(pk['preco_nota'])}</span></p>
                        </div>
                        <div class="tear" aria-hidden="true"></div>
                        <div class="date-body">
                            <ul class="includes">{itens}</ul>
                            <a class="btn btn-wa" data-wa="{e(assunto)}, pacote {e(pk['nome'])}" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}{e(pk['botao'])}</a>
                        </div>
                    </article>''')

    if ev.get('fatos'):
        fatos = ev['fatos']
    else:
        fatos = [
            ('Datas' if multi else 'Data', resumo_datas(ev['datas']), 'amber'),
            ('Local do show', ev['local'], None),
            ('Embarque em', 'Araraquara, São Carlos e região', 'cities'),
            ('Faltam', '-', 'eta'),
        ]
    attrs = {'amber': ' class="amber"', 'small': ' class="small"', 'cities': ' class="small" data-cities', 'eta': ' class="amber" data-eta', None: ''}
    fatos_html = ''.join(f'<div><dt>{e(t)}</dt><dd{attrs[k]}>{e(v)}</dd></div>' for t, v, k in fatos)

    ingressos_html = ''
    if ev.get('ingressos'):
        linhas = ''.join(f'<tr><td>{e(s)}</td><td>{e(a)}</td><td>{e(b)}</td></tr>' for s, a, b in ev['ingressos'])
        colunas = ''.join(f'<th scope="col">{e(c)}</th>' for c in ev['ingresso_colunas'])
        ingressos_html = f'''
        <section class="section ev-tickets" aria-labelledby="ingressos-title">
            <div class="wrap ev-tickets-grid">
                <div>
                    <div class="section-head">
                        <h2 id="ingressos-title">Ingressos</h2>
                        <p>A gente cuida da estrada. O ingresso do show você compra à parte.</p>
                    </div>
                    <div class="callout">
                        <i class="ph ph-info" aria-hidden="true"></i>
                        <p>A Anderson Viagem e Turismo vende <strong>apenas o transporte (excursão)</strong>. Os ingressos do show são comprados {e(ev['ingresso_canal'])}.</p>
                    </div>
                </div>
                <div class="table-wrap">
                    <table class="price-table">
                        <caption>Preços de referência dos ingressos</caption>
                        <thead><tr>{colunas}</tr></thead>
                        <tbody>{linhas}</tbody>
                    </table>
                    <p class="table-note">{e(ev['ingresso_nota'])}</p>
                </div>
            </div>
        </section>'''

    embarques_html = ''
    if ev.get('embarques'):
        paradas = ''.join(
            f'<li><span class="stop-mark"><i class="ph {ic}" aria-hidden="true"></i></span><strong>{e(t)}</strong><span>{e(d)}</span></li>'
            for ic, t, d in ev['embarques']
        )
        embarques_html = f'''
        <section class="section route" aria-labelledby="embarques-title">
            <div class="wrap">
                <div class="section-head">
                    <h2 id="embarques-title">{e(ev['embarques_titulo'])}</h2>
                </div>
                <ol class="stops">{paradas}</ol>
            </div>
        </section>'''

    regras = ev.get('regras') or REGRAS_PADRAO
    regras_html = ''.join(f'<li><i class="ph {ic}" aria-hidden="true"></i><strong>{e(t)}</strong><span>{e(d)}</span></li>' for ic, t, d in regras)
    regras_bg = '' if ev.get('embarques') else ' route'
    if pacotes:
        titulo_datas = ev.get('pacotes_titulo', 'Pacotes')
        cta_hero = 'Ver pacotes'
    else:
        titulo_datas = 'Escolha sua data' if multi else 'Garanta sua vaga'
        cta_hero = 'Escolher data' if multi else 'Ver pacote'
    datas_nota = ev.get('datas_nota', 'Valores cobrados apenas pela excursão de ida e volta. Ingressos do show não inclusos. Sujeito à lotação do veículo.')
    chamada_final = ev.get('chamada_final') or f"Bora pro show do {ev['nome_curto']}?"
    grade_classe = 'dates' if (multi or len(pacotes) > 1) else 'dates single'
    paragrafos = '\n'.join(f'                        <p>{p}</p>' for p in ev['sobre'])
    stats = ''.join(f'<div><b>{e(n)}</b><span>{e(t)}</span></div>' for n, t in ev['stats'])
    ratio = f'{sobre_w} / {sobre_h}'

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>{e(ev['titulo_pagina'])}</title>
    <meta name="description" content="{e(ev['descricao'])}">
    <meta name="robots" content="{robots}">
    <link rel="canonical" href="{e(url_pagina)}">
    <meta name="author" content="Anderson Viagem e Turismo">
    <meta name="theme-color" content="#0F1217" media="(prefers-color-scheme: dark)">
    <meta name="theme-color" content="#EEF0F3" media="(prefers-color-scheme: light)">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Anderson Viagem e Turismo">
    <meta property="og:locale" content="pt_BR">
    <meta property="og:url" content="{e(url_pagina)}">
    <meta property="og:title" content="{e(ev['titulo_pagina'])}">
    <meta property="og:description" content="{e(ev['descricao'])}">
    <meta property="og:image" content="{e(ev['hero_img'])}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{e(ev['titulo_pagina'])}">
    <meta name="twitter:description" content="{e(ev['descricao'])}">
    <meta name="twitter:image" content="{e(ev['hero_img'])}">
    <link rel="icon" href="assets/favicon.png" type="image/png">

    {jsonld_evento(ev)}

    <!-- Página gerada por tools/gerar_eventos.py. Edite os dados lá e rode o script de novo. -->

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

    <link rel="preload" href="assets/fonts/big-shoulders-display-latin-1.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="assets/fonts/instrument-sans-latin-3.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" as="image" href="{e(ev['hero_img'])}" fetchpriority="high">
    <link rel="stylesheet" href="assets/fonts.css">
    <link rel="stylesheet" href="assets/icons/phosphor.css">
    <link rel="stylesheet" href="assets/site.css">
</head>
<body data-dates="{datas_iso}"{f' data-event-id="{ev["event_id"]}"' if ev['event_id'] else ''}>
    <a class="skip-link" href="#conteudo">Pular para o conteúdo</a>

    <header class="topbar">
        <div class="wrap topbar-inner">
            <a class="logo" href="/" aria-label="Anderson Viagem e Turismo, página inicial" translate="no">
                <img class="logo-dark" src="assets/logo-escuro.png" alt="Anderson Viagem e Turismo" width="120" height="58">
                <img class="logo-light" src="assets/logo-claro.png" alt="Anderson Viagem e Turismo" width="120" height="58">
            </a>
            <nav class="nav" aria-label="Principal">
                <a class="back" href="/#agenda"><i class="ph ph-arrow-left" aria-hidden="true"></i>Todas as viagens</a>
                <a href="/#como-funciona">Como funciona</a>
                <a href="/#duvidas">Dúvidas</a>
                <a href="/blog/">Blog</a>
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
                <a class="btn btn-wa" data-wa="{e(assunto)}" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
                <button class="icon-btn menu-btn" id="menu-btn" type="button" aria-label="Abrir menu" aria-expanded="false" aria-controls="mobile-nav">
                    <i class="ph ph-list" aria-hidden="true"></i>
                </button>
            </div>
        </div>
        <nav class="wrap mobile-nav" id="mobile-nav" aria-label="Menu" hidden>
            <a href="/#agenda">Todas as viagens</a>
            <a href="/#como-funciona">Como funciona</a>
            <a href="/#duvidas">Dúvidas</a>
            <a href="/blog/">Blog</a>
            <a href="#contato">Contato</a>
            <a class="btn btn-wa" data-wa="{e(assunto)}" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
        </nav>
    </header>

    <main id="topo">
        <section class="ev-hero" aria-labelledby="ev-title">
            <div class="wrap ev-hero-grid">
                <div class="ev-hero-copy">
                    <h1 id="ev-title" class="rise"><span class="eyebrow">Excursão saindo de Araraquara, São Carlos e região</span> <span>{e(ev['h1'][0])}</span> <span class="hl">{e(ev['h1'][1])}</span></h1>
                    <p class="lede rise">{e(ev['lede'])}</p>
                    <div class="cta-row rise" data-open-only>
                        <a class="btn btn-primary" href="#datas">{cta_hero}<i class="ph ph-arrow-down" aria-hidden="true"></i></a>
                        <a class="btn btn-wa" data-wa="{e(assunto)}" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Reservar vaga</a>
                    </div>
                    <div class="cta-row" data-past-only>
                        <a class="btn btn-primary" href="/#agenda">Ver agenda<i class="ph ph-arrow-right" aria-hidden="true"></i></a>
                        <a class="btn btn-wa" data-wa="" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
                    </div>
                </div>
                <div class="media" data-label="{e(ev['h1'][0])}">
                    <img src="{e(ev['hero_img'])}" alt="{e(ev['hero_alt'])}" width="{hero_w}" height="{hero_h}" fetchpriority="high" decoding="async" referrerpolicy="no-referrer">
                </div>
            </div>
        </section>

        <section id="conteudo" aria-label="Dados da viagem">
            <div class="wrap">
                <dl class="ev-facts">{fatos_html}</dl>
                <div class="notice" data-past-only>
                    <p><i class="ph ph-calendar-x" aria-hidden="true"></i><span>Essa excursão já aconteceu. As próximas saídas estão na agenda.</span></p>
                    <a class="btn btn-ghost" href="/#agenda">Ver agenda</a>
                </div>
            </div>
        </section>

        <section class="section" aria-labelledby="sobre-title">
            <div class="wrap ev-about-grid">
                <div class="media{' contain' if ev['sobre_contain'] else ''}" style="--ratio: {ratio}" data-label="{e(ev['h1'][0])}">
                    <img src="{e(ev['sobre_img'])}" alt="{e(ev['sobre_alt'])}" width="{sobre_w}" height="{sobre_h}" loading="lazy" decoding="async" referrerpolicy="no-referrer">
                </div>
                <div class="ev-about-copy">
                    <h2 id="sobre-title">{e(ev['sobre_titulo'])}</h2>
{paragrafos}
                    <div class="stats">{stats}</div>
                </div>
            </div>
        </section>

{ingressos_html}

        <section class="section" id="datas" aria-labelledby="datas-title">
            <div class="wrap">
                <div class="section-head">
                    <h2 id="datas-title">{e(titulo_datas)}</h2>
                    <p>{e(ev['datas_intro'])}</p>
                </div>
                <div class="{grade_classe}">{''.join(cards)}
                </div>
                <p class="dates-note">{e(datas_nota)}</p>
            </div>
        </section>

{embarques_html}
        <section class="section{regras_bg}" aria-labelledby="regras-title">
            <div class="wrap">
                <div class="section-head">
                    <h2 id="regras-title">{e(ev.get('regras_titulo', 'Antes de embarcar'))}</h2>
                </div>
                <ul class="rules">{regras_html}</ul>
                <div class="rules-foot">
                    <a class="btn btn-ghost" href="/#duvidas">Ver todas as dúvidas<i class="ph ph-arrow-right" aria-hidden="true"></i></a>
                </div>
            </div>
        </section>

        <section class="closing" id="contato" aria-labelledby="contato-title">
            <div class="media">
                <img src="assets/img/closing-1920.jpg" srcset="assets/img/closing-800.jpg 800w, assets/img/closing-1920.jpg 1920w" sizes="100vw" width="1920" height="1280" loading="lazy" decoding="async" alt="Fãs fazendo coração com as mãos durante um show">
            </div>
            <div class="wrap">
                <div class="closing-inner">
                    <h2 id="contato-title" data-past-text="Bora pro próximo show?">{e(chamada_final)}</h2>
                    <p>Chame a gente para reservar sua vaga ou tirar qualquer dúvida sobre a viagem.</p>
                    <div class="phone-row">
                        <span class="phone" id="phone">(16)&nbsp;98833-2631</span>
                        <button class="copy-btn" type="button" id="copy-phone"><i class="ph ph-copy" aria-hidden="true"></i><span>Copiar número</span></button>
                    </div>
                    <div class="cta-row">
                        <a class="btn btn-wa" data-wa="{e(assunto)}" href="#" target="_blank" rel="noopener noreferrer">{WA_ICON}Chamar no WhatsApp</a>
                        <a class="btn btn-ghost" href="https://www.instagram.com/andersonviagemeturismo/" target="_blank" rel="noopener noreferrer"><i class="ph ph-instagram-logo" aria-hidden="true"></i>Seguir no Instagram</a>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="wrap">
        <div class="footer-grid">
            <div>
                <h4>Atendimento</h4>
                <p>Segunda a sábado, 13h às 19h</p>
                <p>Domingos e feriados: fechado</p>
            </div>
            <div>
                <h4>Contato</h4>
                <p><a data-wa="" href="#" target="_blank" rel="noopener noreferrer">WhatsApp (16)&nbsp;98833-2631</a></p>
                <p><a href="https://www.instagram.com/andersonviagemeturismo/" target="_blank" rel="noopener noreferrer">@andersonviagemeturismo</a></p>
            </div>
            <div>
                <h4>Onde estamos</h4>
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
            <p>Desenvolvido por <a href="https://godofin.github.io/portfolio-lavezzo/" target="_blank" rel="noopener noreferrer">Guilherme Lavezzo</a></p>
        </div>
    </footer>

    <a class="wa-float" data-wa="{e(assunto)}" href="#" target="_blank" rel="noopener noreferrer" aria-label="Chamar no WhatsApp">
        <i class="ph-fill ph-whatsapp-logo" aria-hidden="true"></i>
    </a>

    <script src="assets/site.js"></script>
    <script src="assets/evento.js"></script>
</body>
</html>
'''


def trocar_marcadores(texto, nome, novo):
    padrao = re.compile(rf'(<!--seo:{nome}-->).*?(<!--/seo:{nome}-->)', re.S)
    assert padrao.search(texto), f'marcador seo:{nome} não encontrado no index.html'
    return padrao.sub(lambda m: f'{m.group(1)}{novo}{m.group(2)}', texto)


def gerar_site():
    abertas = []
    for ev in EVENTOS:
        destino = ROOT / f"{ev['slug']}.html"
        destino.write_text(pagina(ev), encoding='utf-8')
        estado = 'noindex (encerrada)' if encerrado(ev) else 'indexável'
        print(f"gerado: {destino.name:<20} {estado} | título {len(ev['titulo_pagina'])} | descrição {len(ev['descricao'])}")
        if not encerrado(ev):
            abertas.append(ev)

    home = ROOT / 'index.html'
    html = home.read_text(encoding='utf-8')
    html = trocar_marcadores(html, 'jsonld', '\n    ' + jsonld_home() + '\n    ')
    links = ''.join(f'\n                <p><a href="{ev["slug"]}.html">{e(ev["nome_link"])}</a></p>' for ev in abertas)
    html = trocar_marcadores(html, 'links', links + ('\n                ' if links else ''))
    home.write_text(html, encoding='utf-8')

    urls = [(f'{SITE}/', HOJE)] + [(f"{SITE}/{ev['slug']}.html", HOJE) for ev in abertas]
    try:  # o blog tem as próprias datas (última atualização de cada artigo)
        from gerar_blog import urls_do_blog
        urls += urls_do_blog()
    except ImportError:
        pass
    corpo = ''.join(f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{d.isoformat()}</lastmod>\n  </url>\n' for u, d in urls)
    (ROOT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + corpo + '</urlset>\n',
        encoding='utf-8')
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
    print(f'sitemap.xml com {len(urls)} URLs, robots.txt e index.html atualizados')


if __name__ == '__main__':
    gerar_site()
