/* Páginas de evento: marca datas encerradas, conta os dias e puxa as cidades de embarque da API. */
(() => {
    const { today, esc } = window.Site;
    const body = document.body;
    const DAY_MS = 86400000;
    const parseISO = (s) => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };

    const now = today();
    const dates = (body.dataset.dates || '').split(',').filter(Boolean).map(parseISO);
    const upcoming = dates.filter((d) => d >= now);

    // Cada bilhete de data fica "encerrado" quando o dia já passou
    document.querySelectorAll('.date-card[data-date]').forEach((card) => {
        if (parseISO(card.dataset.date) < now) card.classList.add('is-past');
    });

    // Todas as datas passaram: a página troca as chamadas de reserva por "ver agenda"
    if (dates.length && !upcoming.length) body.classList.add('is-past');

    // O título final troca de texto quando a viagem já passou (só um título no HTML)
    const closing = document.getElementById('contato-title');
    if (closing && closing.dataset.pastText && body.classList.contains('is-past')) closing.textContent = closing.dataset.pastText;

    const eta = document.querySelector('[data-eta]');
    if (eta) {
        if (!upcoming.length) {
            eta.textContent = 'Encerrada';
        } else {
            const diff = Math.round((upcoming[0] - now) / DAY_MS);
            eta.textContent = diff === 0 ? 'É hoje' : diff === 1 ? 'Amanhã' : `${diff} dias`;
        }
    }

    // Cidades de embarque: vêm do cadastro do evento na API; sem resposta, fica o texto padrão
    const id = Number(body.dataset.eventId);
    const citiesEl = document.querySelector('[data-cities]');
    if (!id || !citiesEl) return;
    const fix = { araraqura: 'Araraquara' };
    fetch('https://fast-api-anderson.vercel.app/api/v1/events')
        .then((r) => (r.ok ? r.json() : []))
        .then((events) => {
            const ev = (Array.isArray(events) ? events : []).find((e) => e && e.id === id);
            if (!ev || !Array.isArray(ev.cities)) return;
            const out = [];
            ev.cities.forEach((c) => String(c).split(/,|\s+e\s+/).forEach((part) => {
                const clean = part.replace(/[!.]+$/, '').trim();
                if (!clean) return;
                const name = fix[clean.toLowerCase()] || clean;
                if (!out.includes(name)) out.push(name);
            }));
            if (!out.length) return;
            citiesEl.innerHTML = esc(out.length > 1 ? `${out.slice(0, -1).join(', ')} e ${out[out.length - 1]}` : out[0]);
        })
        .catch(() => {});
})();
