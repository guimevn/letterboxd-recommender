const MAX_SLOTS = 4;
const API_BASE = (window.API_BASE_URL || '').replace(/\/$/, '');

const I18N = {
  pt: {
    heroTitle: 'O que assistir hoje?',
    heroSubtitle: 'Digite seu username e descubra quatro filmes novos baseados no seu gosto.',
    placeholder: 'seu username',
    search: 'Buscar',
    profile: 'Perfil',
    sync: 'Sincronizar',
    importZip: 'Importar .zip',
    importTip: 'Opcional: envie o .zip exportado do Letterboxd para incluir 100% do histórico e watchlist',
    mood_all: 'Qualquer mood',
    mood_light: 'Leve',
    mood_intense: 'Tenso',
    mood_thoughtful: 'Reflexivo',
    mood_epic: 'Épico',
    src_all: 'Mundo todo',
    src_watchlist: 'Watchlist',
    disc_popular: 'Popular',
    disc_balanced: 'Equilibrado',
    disc_cult: 'Cult',
    rt_any: 'Qualquer duração',
    rt_100: 'Até 1h40',
    rt_125: 'Até 2h05',
    rt_150: 'Até 2h30',
    refreshAll: 'Atualizar 4 opções',
    refreshN: (n) => `Atualizar ${n} ${n === 1 ? 'opção' : 'opções'}`,
    allLocked: 'Todas as 4 fixadas',
    lockedHint: (n) => `${n} ${n === 1 ? 'filme fixado' : 'filmes fixados'} com Gostei.`,
    loadingBatch: (u) => `Analisando seu perfil e buscando 4 filmes para @${u}...`,
    loadingSub: 'Na primeira vez pode levar alguns segundos.',
    loadingMore: 'Buscando novas opções...',
    syncing: (u) => `Sincronizando @${u} no Letterboxd...`,
    importing: 'Importando histórico completo do .zip...',
    watched: 'assistidos',
    logsAnalyzed: 'logs analisados',
    avg: 'Média',
    like: 'Gostei',
    locked: 'Fixado',
    dislike: 'Não gostei',
    seen: 'Já vi',
    skip: 'Pular',
    noPoster: 'Sem pôster',
    noResults: 'Nenhum filme novo encontrado com esses filtros. Tente mudar o mood ou relaxar a duração.',
    footer: 'Dados fornecidos pelo TMDB e Letterboxd',
  },
  en: {
    heroTitle: 'What to watch tonight?',
    heroSubtitle: 'Enter your username and discover four new movies tailored to your taste.',
    placeholder: 'your username',
    search: 'Search',
    profile: 'Profile',
    sync: 'Sync',
    importZip: 'Import .zip',
    importTip: 'Optional: upload your Letterboxd .zip export for 100% history and watchlist',
    mood_all: 'Any mood',
    mood_light: 'Light',
    mood_intense: 'Intense',
    mood_thoughtful: 'Thoughtful',
    mood_epic: 'Epic',
    src_all: 'Worldwide',
    src_watchlist: 'Watchlist',
    disc_popular: 'Popular',
    disc_balanced: 'Balanced',
    disc_cult: 'Cult',
    rt_any: 'Any runtime',
    rt_100: 'Up to 1h40',
    rt_125: 'Up to 2h05',
    rt_150: 'Up to 2h30',
    refreshAll: 'Refresh 4 picks',
    refreshN: (n) => `Refresh ${n} ${n === 1 ? 'pick' : 'picks'}`,
    allLocked: 'All 4 locked',
    lockedHint: (n) => `${n} ${n === 1 ? 'movie locked' : 'movies locked'} with Like.`,
    loadingBatch: (u) => `Analyzing your profile and finding 4 movies for @${u}...`,
    loadingSub: 'First load may take a few seconds.',
    loadingMore: 'Finding new picks...',
    syncing: (u) => `Syncing @${u} on Letterboxd...`,
    importing: 'Importing full history from .zip...',
    watched: 'watched',
    logsAnalyzed: 'logs analyzed',
    avg: 'Avg',
    like: 'Like',
    locked: 'Locked',
    dislike: 'Dislike',
    seen: 'Seen',
    skip: 'Skip',
    noPoster: 'No poster',
    noResults: 'No new movies matched these filters. Try changing the mood or runtime.',
    footer: 'Data provided by TMDB and Letterboxd',
  },
  es: {
    heroTitle: '¿Qué ver hoy?',
    heroSubtitle: 'Ingresa tu usuario y descubre cuatro películas nuevas según tus gustos.',
    placeholder: 'tu usuario',
    search: 'Buscar',
    profile: 'Perfil',
    sync: 'Sincronizar',
    importZip: 'Importar .zip',
    importTip: 'Opcional: sube el .zip exportado de Letterboxd para analizar el 100% y tu watchlist',
    mood_all: 'Cualquier mood',
    mood_light: 'Ligero',
    mood_intense: 'Tenso',
    mood_thoughtful: 'Reflexivo',
    mood_epic: 'Épico',
    src_all: 'Todo el mundo',
    src_watchlist: 'Watchlist',
    disc_popular: 'Popular',
    disc_balanced: 'Equilibrado',
    disc_cult: 'Culto',
    rt_any: 'Cualquier duración',
    rt_100: 'Hasta 1h40',
    rt_125: 'Hasta 2h05',
    rt_150: 'Hasta 2h30',
    refreshAll: 'Actualizar 4 opciones',
    refreshN: (n) => `Actualizar ${n} ${n === 1 ? 'opción' : 'opciones'}`,
    allLocked: 'Las 4 fijadas',
    lockedHint: (n) => `${n} ${n === 1 ? 'película fijada' : 'películas fijadas'} con Me gusta.`,
    loadingBatch: (u) => `Analizando tu perfil y buscando 4 películas para @${u}...`,
    loadingSub: 'La primera vez puede tardar unos segundos.',
    loadingMore: 'Buscando nuevas opciones...',
    syncing: (u) => `Sincronizando @${u} en Letterboxd...`,
    importing: 'Importando historial completo del .zip...',
    watched: 'vistas',
    logsAnalyzed: 'registros analizados',
    avg: 'Media',
    like: 'Me gusta',
    locked: 'Fijada',
    dislike: 'No me gusta',
    seen: 'Ya la vi',
    skip: 'Saltar',
    noPoster: 'Sin póster',
    noResults: 'No se encontraron películas nuevas con estos filtros. Prueba cambiar el mood o la duración.',
    footer: 'Datos proporcionados por TMDB y Letterboxd',
  },
  fr: {
    heroTitle: 'Quel film regarder ?',
    heroSubtitle: 'Entrez votre pseudo et découvrez quatre nouveaux films adaptés à vos goûts.',
    placeholder: 'votre pseudo',
    search: 'Chercher',
    profile: 'Profil',
    sync: 'Synchroniser',
    importZip: 'Importer .zip',
    importTip: 'Optionnel : importez le .zip Letterboxd pour 100% de votre historique et watchlist',
    mood_all: 'Tout mood',
    mood_light: 'Léger',
    mood_intense: 'Tendu',
    mood_thoughtful: 'Réfléchi',
    mood_epic: 'Épique',
    src_all: 'Monde entier',
    src_watchlist: 'Watchlist',
    disc_popular: 'Populaire',
    disc_balanced: 'Équilibré',
    disc_cult: 'Culte',
    rt_any: 'Toute durée',
    rt_100: 'Max 1h40',
    rt_125: 'Max 2h05',
    rt_150: 'Max 2h30',
    refreshAll: 'Actualiser 4 choix',
    refreshN: (n) => `Actualiser ${n} choix`,
    allLocked: 'Les 4 épinglés',
    lockedHint: (n) => `${n} ${n === 1 ? 'film épinglé' : 'films épinglés'}.`,
    loadingBatch: (u) => `Analyse du profil et recherche de 4 films pour @${u}...`,
    loadingSub: 'Le premier chargement peut prendre quelques secondes.',
    loadingMore: 'Recherche de nouveaux choix...',
    syncing: (u) => `Synchronisation de @${u} sur Letterboxd...`,
    importing: 'Importation complète depuis le .zip...',
    watched: 'vus',
    logsAnalyzed: 'films analysés',
    avg: 'Moy.',
    like: 'Aimer',
    locked: 'Épinglé',
    dislike: 'Pas fan',
    seen: 'Déjà vu',
    skip: 'Passer',
    noPoster: 'Sans affiche',
    noResults: 'Aucun nouveau film trouvé avec ces filtres. Essayez un autre mood ou durée.',
    footer: 'Données fournies par TMDB et Letterboxd',
  },
};

function detectLocale() {
  const savedLang = localStorage.getItem('lb_lang');
  const nav = (navigator.language || 'en-US').toLowerCase();
  const parts = nav.split('-');
  const navLang = ['pt', 'en', 'es', 'fr'].includes(parts[0]) ? parts[0] : 'en';
  const lang = savedLang && I18N[savedLang] ? savedLang : navLang;

  const defaultRegionByLang = { pt: 'BR', en: 'US', es: 'ES', fr: 'FR' };
  const navRegion = parts[1] ? parts[1].toUpperCase() : null;
  const region = savedLang && savedLang !== navLang
    ? defaultRegionByLang[lang]
    : (navRegion && navRegion.length === 2 ? navRegion : defaultRegionByLang[lang]);

  return { lang, region };
}

const initialLocale = detectLocale();

const state = {
  username: localStorage.getItem('lb_username') || '',
  lang: initialLocale.lang,
  region: initialLocale.region,
  source: 'all',
  mood: 'all',
  discovery: 'balanced',
  max_runtime: '',
  slots: [],
  lockedIds: new Set(),
  shownIds: new Set(),
  dislikedIds: [],
  seenIds: [],
  skippedIds: [],
  lastUser: null,
  lastProfile: null,
};

const els = {
  logoHomeBtn: document.getElementById('logoHomeBtn'),
  langSelect: document.getElementById('langSelect'),
  heroTitle: document.getElementById('heroTitle'),
  heroSubtitle: document.getElementById('heroSubtitle'),
  submitBtn: document.getElementById('submitBtn'),
  form: document.getElementById('searchForm'),
  input: document.getElementById('usernameInput'),
  syncBtn: document.getElementById('syncBtn'),
  importZipLabel: document.getElementById('importZipLabel'),
  importZipText: document.getElementById('importZipText'),
  importZipInput: document.getElementById('importZipInput'),
  refreshBtn: document.getElementById('refreshBtn'),
  refreshBtnText: document.getElementById('refreshBtnText'),
  lockedHint: document.getElementById('lockedHint'),
  emptyState: document.getElementById('emptyState'),
  loadingState: document.getElementById('loadingState'),
  loadingText: document.getElementById('loadingText'),
  loadingSub: document.getElementById('loadingSub'),
  errorState: document.getElementById('errorState'),
  errorText: document.getElementById('errorText'),
  dashboard: document.getElementById('dashboard'),
  userAvatar: document.getElementById('userAvatar'),
  userDisplayName: document.getElementById('userDisplayName'),
  userLbLink: document.getElementById('userLbLink'),
  userStats: document.getElementById('userStats'),
  moviesGrid: document.getElementById('moviesGrid'),
  noResultsMsg: document.getElementById('noResultsMsg'),
  runtimeSelect: document.getElementById('runtimeSelect'),
  footerText: document.getElementById('footerText'),
};

function t(key, arg) {
  const dict = I18N[state.lang] || I18N.en;
  const val = dict[key];
  return typeof val === 'function' ? val(arg) : (val || key);
}

function applyTranslations() {
  document.documentElement.lang = state.lang;
  els.langSelect.value = state.lang;
  els.heroTitle.textContent = t('heroTitle');
  els.heroSubtitle.textContent = t('heroSubtitle');
  els.input.placeholder = t('placeholder');
  els.submitBtn.textContent = t('search');
  els.userLbLink.textContent = t('profile');
  els.syncBtn.textContent = t('sync');
  els.importZipText.textContent = t('importZip');
  els.importZipLabel.title = t('importTip');
  els.loadingSub.textContent = t('loadingSub');
  els.noResultsMsg.textContent = t('noResults');
  els.footerText.textContent = t('footer');

  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });

  if (state.lastProfile) renderProfile();
  if (state.slots.length) renderSlots();
}

if (state.username) {
  els.input.value = state.username;
}
applyTranslations();

function showView(view) {
  els.emptyState.classList.toggle('hidden', view !== 'empty');
  els.loadingState.classList.toggle('hidden', view !== 'loading');
  els.errorState.classList.toggle('hidden', view !== 'error');
  els.dashboard.classList.toggle('hidden', view !== 'dashboard');
}

function formatRuntime(mins) {
  if (!mins) return '';
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h ? `${h}h${m.toString().padStart(2, '0')}` : `${m}min`;
}

function buildParams(limit, includeSessionExcludes = true) {
  const params = new URLSearchParams({
    source: state.source,
    mood: state.mood,
    discovery: state.discovery,
    limit: String(limit),
    lang: state.lang,
    region: state.region,
  });
  if (state.max_runtime) params.set('max_runtime', state.max_runtime);

  const excludeSet = new Set();
  if (includeSessionExcludes) {
    state.shownIds.forEach(id => excludeSet.add(id));
  }
  state.slots.forEach(m => excludeSet.add(m.tmdb_id));
  if (excludeSet.size) params.set('exclude_ids', Array.from(excludeSet).join(','));

  if (state.lockedIds.size) params.set('liked_ids', Array.from(state.lockedIds).join(','));
  if (state.dislikedIds.length) params.set('disliked_ids', state.dislikedIds.slice(-12).join(','));
  if (state.seenIds.length) params.set('seen_ids', state.seenIds.slice(-10).join(','));
  if (state.skippedIds.length) params.set('skipped_ids', state.skippedIds.slice(-10).join(','));
  return params;
}

function updateRefreshButton() {
  const lockedCount = state.slots.filter(m => state.lockedIds.has(m.tmdb_id)).length;
  const toReplace = MAX_SLOTS - lockedCount;
  if (toReplace <= 0) {
    els.refreshBtnText.textContent = t('allLocked');
    els.refreshBtn.disabled = true;
    els.refreshBtn.classList.add('opacity-50');
  } else {
    els.refreshBtnText.textContent = lockedCount > 0 ? t('refreshN', toReplace) : t('refreshAll');
    els.refreshBtn.disabled = false;
    els.refreshBtn.classList.remove('opacity-50');
  }

  if (lockedCount > 0) {
    els.lockedHint.textContent = t('lockedHint', lockedCount);
    els.lockedHint.classList.remove('hidden');
  } else {
    els.lockedHint.classList.add('hidden');
  }
}

async function fetchBatch({ resetSession = false, keepLocked = false } = {}) {
  if (!state.username) return;

  if (resetSession) {
    state.slots = [];
    state.lockedIds.clear();
    state.shownIds.clear();
  }

  const lockedMovies = keepLocked
    ? state.slots.filter(m => state.lockedIds.has(m.tmdb_id))
    : [];
  const needed = MAX_SLOTS - lockedMovies.length;
  if (needed <= 0) {
    updateRefreshButton();
    return;
  }

  if (!state.slots.length) {
    showView('loading');
    els.loadingText.textContent = t('loadingBatch', state.username);
  } else {
    els.refreshBtn.disabled = true;
    els.refreshBtnText.textContent = t('loadingMore');
  }

  try {
    let params = buildParams(needed, !resetSession);
    let res = await fetch(`${API_BASE}/api/recommendations/${encodeURIComponent(state.username)}?${params}`);
    let data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');

    let incoming = data.recommendations || [];

    if (incoming.length < needed && state.shownIds.size > 0) {
      state.shownIds.clear();
      const topUpParams = buildParams(needed, false);
      const topUpRes = await fetch(`${API_BASE}/api/recommendations/${encodeURIComponent(state.username)}?${topUpParams}`);
      const topUpData = await topUpRes.json();
      if (topUpRes.ok) {
        const existingIds = new Set(incoming.map(m => m.tmdb_id));
        for (const m of (topUpData.recommendations || [])) {
          if (!existingIds.has(m.tmdb_id) && incoming.length < needed) {
            incoming.push(m);
            existingIds.add(m.tmdb_id);
          }
        }
      }
    }

    state.lastUser = data.user;
    state.lastProfile = data.profile;
    incoming.forEach(m => state.shownIds.add(m.tmdb_id));

    if (keepLocked && state.slots.length) {
      let incIdx = 0;
      const nextSlots = [];
      for (let i = 0; i < MAX_SLOTS; i++) {
        const cur = state.slots[i];
        if (cur && state.lockedIds.has(cur.tmdb_id)) {
          nextSlots.push(cur);
        } else if (incIdx < incoming.length) {
          nextSlots.push(incoming[incIdx++]);
        }
      }
      state.slots = nextSlots;
    } else {
      state.slots = incoming.slice(0, MAX_SLOTS);
    }

    renderProfile();
    renderSlots();
    showView('dashboard');
  } catch (err) {
    els.errorText.textContent = err.message;
    showView('error');
  }
}

let replaceQueue = Promise.resolve();

function replaceSingleSlot(slotIndex, tmdbId, reason) {
  const cardEl = els.moviesGrid.children[slotIndex];
  if (cardEl) cardEl.style.opacity = '0.35';

  replaceQueue = replaceQueue.then(async () => {
    const currentIdx = state.slots.findIndex(m => m && m.tmdb_id === tmdbId);
    if (currentIdx === -1) return;

    if (reason === 'seen') {
      state.seenIds.push(tmdbId);
    } else if (reason === 'disliked') {
      state.dislikedIds.push(tmdbId);
    } else {
      state.skippedIds.push(tmdbId);
    }
    state.lockedIds.delete(tmdbId);
    state.shownIds.add(tmdbId);

    fetch(`${API_BASE}/api/dismiss/${encodeURIComponent(state.username)}/${tmdbId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    }).catch(() => {});

    try {
      let params = buildParams(1, true);
      let res = await fetch(`${API_BASE}/api/recommendations/${encodeURIComponent(state.username)}?${params}`);
      let data = await res.json();
      let replacement = (data.recommendations || [])[0];

      if (!replacement && state.shownIds.size > 0) {
        state.shownIds.clear();
        params = buildParams(1, false);
        res = await fetch(`${API_BASE}/api/recommendations/${encodeURIComponent(state.username)}?${params}`);
        data = await res.json();
        replacement = (data.recommendations || [])[0];
      }

      const activeIds = new Set(state.slots.map(m => m.tmdb_id));
      if (replacement && !activeIds.has(replacement.tmdb_id)) {
        state.shownIds.add(replacement.tmdb_id);
        state.slots[currentIdx] = replacement;
      } else {
        state.slots.splice(currentIdx, 1);
      }
      renderSlots();
    } catch {
      state.slots.splice(currentIdx, 1);
      renderSlots();
    }
  });
}

async function syncProfile() {
  if (!state.username) return;
  showView('loading');
  els.loadingText.textContent = t('syncing', state.username);

  try {
    const res = await fetch(`${API_BASE}/api/sync/${encodeURIComponent(state.username)}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    await fetchBatch({ resetSession: true });
  } catch (err) {
    els.errorText.textContent = err.message;
    showView('error');
  }
}

async function importZipFile(file) {
  if (!state.username || !file) return;
  showView('loading');
  els.loadingText.textContent = t('importing');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/api/import/${encodeURIComponent(state.username)}`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    await fetchBatch({ resetSession: true });
  } catch (err) {
    els.errorText.textContent = err.message;
    showView('error');
  }
}

function renderProfile() {
  const user = state.lastUser;
  const profile = state.lastProfile;
  if (!user || !profile) return;

  els.userDisplayName.textContent = user.display_name || user.username;
  els.userLbLink.href = `https://letterboxd.com/${user.username}/`;
  if (user.avatar_url) {
    els.userAvatar.src = user.avatar_url;
    els.userAvatar.classList.remove('hidden');
  } else {
    els.userAvatar.classList.add('hidden');
  }

  const avgText = profile.avg_rating ? ` | ${t('avg')} ${profile.avg_rating}` : '';
  const wlText = profile.total_watchlist > 0 ? ` | ${profile.total_watchlist} watchlist` : '';
  const watchedLabel = profile.total_watchlist > 0 ? t('watched') : t('logsAnalyzed');
  els.userStats.textContent = `${profile.total_watched} ${watchedLabel}${wlText}${avgText}`;
}

function renderSlots() {
  const uniqueSlots = [];
  const seenInSlots = new Set();
  for (const m of state.slots) {
    if (m && !seenInSlots.has(m.tmdb_id)) {
      seenInSlots.add(m.tmdb_id);
      uniqueSlots.push(m);
    }
  }
  state.slots = uniqueSlots;

  els.moviesGrid.innerHTML = '';
  updateRefreshButton();

  if (!state.slots.length) {
    els.noResultsMsg.classList.remove('hidden');
    return;
  }
  els.noResultsMsg.classList.add('hidden');

  state.slots.forEach((m, idx) => {
    const isLocked = state.lockedIds.has(m.tmdb_id);
    const card = document.createElement('article');
    card.className = `poster-card rounded-xl bg-lb-card border border-lb-border overflow-hidden flex flex-col ${isLocked ? 'card-locked' : ''}`;

    const posterHtml = m.poster_path
      ? `<img src="${m.poster_path}" alt="${m.title}" class="w-24 sm:w-28 h-full object-cover shrink-0 bg-slate-900" loading="lazy" />`
      : `<div class="w-24 sm:w-28 bg-slate-800 flex items-center justify-center text-xs text-lb-muted shrink-0">${t('noPoster')}</div>`;

    const directors = (m.directors || []).map(d => d.name).join(', ');
    const genres = (m.genres || []).slice(0, 3).map(g => g.name).join(' · ');
    const runtime = formatRuntime(m.runtime);
    const meta = [m.year, runtime].filter(Boolean).join(' · ');

    const ratingParts = [];
    if (m.letterboxd_rating) ratingParts.push(`<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 font-semibold">Letterboxd ${m.letterboxd_rating}/5</span>`);
    if (!ratingParts.length && m.vote_average) ratingParts.push(`<span class="px-1.5 py-0.5 rounded bg-slate-700 text-slate-200 font-semibold">TMDB ${m.vote_average}</span>`);
    const ratingsHtml = `<div class="flex flex-wrap items-center gap-1.5 mt-1 text-[10px]">${ratingParts.join('')}</div>`;

    const wlBadge = m.in_watchlist
      ? `<span class="px-1.5 py-0.5 rounded bg-lb-blue/20 text-lb-blue text-[10px] font-semibold shrink-0">Watchlist</span>`
      : '';

    const reasonsHtml = (m.reasons || [])
      .slice(0, 1)
      .map(r => `<div class="text-[11px] text-emerald-300/90 truncate">${r}</div>`)
      .join('');

    const providers = m.providers || m.providers_br || [];
    const regionLabel = m.provider_region || state.region;
    const providersHtml = providers.length
      ? `<div class="flex items-center gap-1 mt-1.5 flex-wrap">
          <span class="text-[10px] text-lb-muted">${regionLabel}:</span>
          ${providers.map(p => p.logo_path
            ? `<img src="${p.logo_path}" title="${p.name}" alt="${p.name}" class="w-4 h-4 rounded" />`
            : `<span class="text-[10px] text-slate-300">${p.name}</span>`
          ).join('')}
        </div>`
      : '';

    const likeBtnClass = isLocked
      ? 'bg-lb-green text-slate-950 font-semibold border-lb-green'
      : 'bg-lb-bg text-slate-200 border-lb-border hover:border-lb-green';

    card.innerHTML = `
      <div class="flex flex-1">
        ${posterHtml}
        <div class="p-2.5 flex flex-col justify-between flex-1 min-w-0">
          <div>
            <div class="flex items-start justify-between gap-1.5">
              <a href="${m.letterboxd_url}" target="_blank" class="font-bold text-white hover:text-lb-green text-xs sm:text-sm leading-tight line-clamp-1">
                ${m.title}
              </a>
              ${wlBadge}
            </div>
            <p class="text-[11px] text-lb-muted mt-0.5 truncate">${meta}${directors ? ` · ${directors}` : ''}</p>
            ${genres ? `<p class="text-[10px] text-lb-muted truncate">${genres}</p>` : ''}
            ${ratingsHtml}
            <div class="mt-1">${reasonsHtml}</div>
            ${providersHtml}
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-1 pt-2 mt-2 border-t border-lb-border/60 text-[10px]">
            <button class="btn-like px-1.5 py-1 rounded-md border transition cursor-pointer truncate ${likeBtnClass}">
              ${isLocked ? t('locked') : t('like')}
            </button>
            <button class="btn-dislike px-1.5 py-1 rounded-md bg-lb-bg border border-lb-border text-lb-muted hover:text-red-400 hover:border-red-400/60 transition cursor-pointer truncate">
              ${t('dislike')}
            </button>
            <button class="btn-seen px-1.5 py-1 rounded-md bg-lb-bg border border-lb-border text-lb-muted hover:text-white transition cursor-pointer truncate">
              ${t('seen')}
            </button>
            <button class="btn-skip px-1.5 py-1 rounded-md bg-lb-bg border border-lb-border text-lb-muted hover:text-slate-200 transition cursor-pointer truncate">
              ${t('skip')}
            </button>
          </div>
        </div>
      </div>
    `;

    card.querySelector('.btn-like').addEventListener('click', () => {
      if (state.lockedIds.has(m.tmdb_id)) {
        state.lockedIds.delete(m.tmdb_id);
      } else {
        state.lockedIds.add(m.tmdb_id);
      }
      renderSlots();
    });

    card.querySelector('.btn-dislike').addEventListener('click', () => replaceSingleSlot(idx, m.tmdb_id, 'disliked'));
    card.querySelector('.btn-seen').addEventListener('click', () => replaceSingleSlot(idx, m.tmdb_id, 'seen'));
    card.querySelector('.btn-skip').addEventListener('click', () => replaceSingleSlot(idx, m.tmdb_id, 'not_interested'));

    els.moviesGrid.appendChild(card);
  });
}

els.logoHomeBtn.addEventListener('click', () => {
  showView('empty');
  els.input.focus();
});

els.langSelect.addEventListener('change', (e) => {
  const newLang = e.target.value;
  const defaultRegion = { pt: 'BR', en: 'US', es: 'ES', fr: 'FR' };
  state.lang = newLang;
  state.region = defaultRegion[newLang] || 'US';
  localStorage.setItem('lb_lang', newLang);
  applyTranslations();
  if (state.username && !els.dashboard.classList.contains('hidden')) {
    fetchBatch({ resetSession: true });
  }
});

els.form.addEventListener('submit', (e) => {
  e.preventDefault();
  const uname = els.input.value.trim().replace(/^@/, '');
  if (!uname) return;
  state.username = uname;
  state.dislikedIds = [];
  state.seenIds = [];
  state.skippedIds = [];
  localStorage.setItem('lb_username', uname);
  fetchBatch({ resetSession: true });
});

els.syncBtn.addEventListener('click', syncProfile);
els.importZipInput.addEventListener('change', (e) => {
  const file = e.target.files && e.target.files[0];
  if (file) importZipFile(file);
  e.target.value = '';
});
els.refreshBtn.addEventListener('click', () => fetchBatch({ keepLocked: true }));

document.querySelectorAll('.filter-pill').forEach(btn => {
  btn.addEventListener('click', () => {
    const filter = btn.dataset.filter;
    state[filter] = btn.dataset.val;
    document.querySelectorAll(`.filter-pill[data-filter="${filter}"]`).forEach(b => b.classList.remove('pill-active'));
    btn.classList.add('pill-active');
    fetchBatch({ resetSession: true });
  });
});

els.runtimeSelect.addEventListener('change', (e) => {
  state.max_runtime = e.target.value;
  fetchBatch({ resetSession: true });
});
