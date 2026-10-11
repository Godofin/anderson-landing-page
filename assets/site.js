/* Anderson Viagem e Turismo: comportamento compartilhado (home e páginas de evento). */
(() => {
    const WHATSAPP = '5516988332631';
    const PHONE_TEXT = '(16) 98833-2631';

    const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const tidy = (s) => String(s ?? '').replace(/\s*[—–]\s*/g, ' - ');
    const safeUrl = (u) => {
        if (typeof u !== 'string' || !u.trim()) return '';
        try {
            const url = new URL(u, location.href);
            return (url.protocol === 'https:' || url.protocol === 'http:') ? url.href : '';
        } catch (e) { return ''; }
    };
    const waLink = (topic) => {
        const text = topic
            ? `Olá! Tenho interesse na excursão para o evento "${topic}". Gostaria de mais informações.`
            : 'Olá! Gostaria de mais informações sobre as excursões.';
        return `https://api.whatsapp.com/send?phone=${WHATSAPP}&text=${encodeURIComponent(text)}`;
    };
    const today = () => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; };

    window.Site = { WHATSAPP, PHONE_TEXT, esc, tidy, safeUrl, waLink, today };

    // Anos de empresa: fundada em 12/10/2017. A cada 12/10 soma mais um, sozinho.
    // O piso de 9 vale só na véspera do aniversário de 9 anos (11/10/2026); depois o cálculo já dá 9.
    const anosDeEmpresa = () => {
        const agora = new Date();
        const jaFezAniversario = agora.getMonth() > 9 || (agora.getMonth() === 9 && agora.getDate() >= 12);
        return Math.max(9, agora.getFullYear() - 2017 - (jaFezAniversario ? 0 : 1));
    };
    document.querySelectorAll('[data-anos]').forEach((el) => { el.textContent = anosDeEmpresa(); });
    window.Site.anosDeEmpresa = anosDeEmpresa;

    // Links de WhatsApp: data-wa="" abre conversa geral; data-wa="Evento" já cita o evento
    document.querySelectorAll('[data-wa]').forEach((a) => { a.href = waLink(a.dataset.wa); });
    document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });

    // Tema: escolha salva vence; sem escolha, segue o sistema
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const root = document.documentElement;
            const current = root.dataset.theme || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
            const next = current === 'light' ? 'dark' : 'light';
            root.dataset.theme = next;
            try { localStorage.setItem('color-theme', next); } catch (e) {}
        });
    }

    // Menu mobile
    const menuBtn = document.getElementById('menu-btn');
    const mobileNav = document.getElementById('mobile-nav');
    if (menuBtn && mobileNav) {
        const setMenu = (open) => {
            mobileNav.hidden = !open;
            menuBtn.setAttribute('aria-expanded', String(open));
            menuBtn.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
            menuBtn.querySelector('.ph').className = `ph ${open ? 'ph-x' : 'ph-list'}`;
        };
        menuBtn.addEventListener('click', () => setMenu(mobileNav.hidden));
        mobileNav.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !mobileNav.hidden) { setMenu(false); menuBtn.focus(); }
        });
    }

    // Copiar número
    const copyBtn = document.getElementById('copy-phone');
    if (copyBtn) {
        copyBtn.addEventListener('click', async () => {
            const label = copyBtn.querySelector('span');
            try {
                await navigator.clipboard.writeText(PHONE_TEXT);
                label.textContent = 'Número copiado';
            } catch (err) {
                const phone = document.getElementById('phone');
                const range = document.createRange();
                range.selectNodeContents(phone);
                const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
                label.textContent = 'Número selecionado';
            }
            setTimeout(() => { label.textContent = 'Copiar número'; }, 2400);
        });
    }

    // Imagens quebradas viram um bloco listrado com o nome do evento
    document.addEventListener('error', (e) => {
        const img = e.target;
        if (!img || img.tagName !== 'IMG') return;
        const media = img.closest('.media, .poster-frame');
        if (!media) return;
        img.remove();
        media.classList.add('media', 'noimg');
    }, true);
})();
