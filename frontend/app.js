const MAX_SLOTS = 4;
const API_BASE = (window.API_BASE_URL || '').replace(/\/$/, '');

const state = {
  username: localStorage.getItem('lb_username') || '',
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
  form: document.getElementById('searchForm'),
  input: document.getElementById('usernameInput'),
  syncBtn: document.getElementById('syncBtn'),
  refreshBtn: document.getElementById('refreshBtn'),
  refreshBtnText: document.getElementById('refreshBtnText'),
  lockedHint: document.getElementById('lockedHint'),
  emptyState: document.getElementById('emptyState'),
  loadingState: document.getElementById('loadingState'),
  loadingText: document.getElementById('loadingText'),
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
};

if (state.username) {
  els.input.value = state.username;
}

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
    els.refreshBtnText.textContent = 'Todas as 4 fixadas';
    els.refreshBtn.disabled = true;
    els.refreshBtn.classList.add('opacity-50');
  } else {
    els.refreshBtnText.textContent =
      lockedCount > 0
        ? `Atualizar ${toReplace} ${toReplace === 1 ? 'opção' : 'opções'}`
        : 'Atualizar 4 opções';
    els.refreshBtn.disabled = false;
    els.refreshBtn.classList.remove('opacity-50');
  }

  if (lockedCount > 0) {
    els.lockedHint.textContent = `${lockedCount} ${lockedCount === 1 ? 'filme fixado' : 'filmes fixados'} com Gostei. As novas opções vão seguir essa vibe.`;
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
    els.loadingText.textContent = `Analisando seu perfil e buscando 4 filmes para @${state.username}...`;
  } else {
    els.refreshBtn.disabled = true;
    els.refreshBtnText.textContent = 'Buscando novas opções...';
  }

  try {
    let params = buildParams(needed, !resetSession);
    let res = await fetch(`${API_BASE}/api/recommendations/${encodeURIComponent(state.username)}?${params}`);
    let data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Erro ao buscar recomendações.');

    let incoming = data.recommendations || [];

    // If session exclusions exhausted the pool and returned < needed, reset shownIds and top up
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

  // Serialize replacements so rapid clicks can NEVER insert the same movie twice
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
  els.loadingText.textContent = `Sincronizando @${state.username} no Letterboxd...`;

  try {
    const res = await fetch(`${API_BASE}/api/sync/${encodeURIComponent(state.username)}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Erro ao sincronizar perfil.');
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

  const avgText = profile.avg_rating ? ` | Média ${profile.avg_rating}` : '';
  els.userStats.textContent = `${profile.total_watched} assistidos | ${profile.total_watchlist} watchlist${avgText}`;
}

function renderSlots() {
  // Final safety dedup so 2 identical movies can NEVER render
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
      : `<div class="w-24 sm:w-28 bg-slate-800 flex items-center justify-center text-xs text-lb-muted shrink-0">Sem pôster</div>`;

    const directors = (m.directors || []).map(d => d.name).join(', ');
    const genres = (m.genres || []).slice(0, 3).map(g => g.name).join(' · ');
    const runtime = formatRuntime(m.runtime);
    const meta = [m.year, runtime].filter(Boolean).join(' · ');

    const ratingParts = [];
    if (m.imdb_rating) ratingParts.push(`<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 font-semibold">IMDb ${m.imdb_rating}</span>`);
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

    const providersHtml = (m.providers_br || []).length
      ? `<div class="flex items-center gap-1 mt-1.5 flex-wrap">
          <span class="text-[10px] text-lb-muted">BR:</span>
          ${m.providers_br.map(p => p.logo_path
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
              ${isLocked ? 'Fixado' : 'Gostei'}
            </button>
            <button class="btn-dislike px-1.5 py-1 rounded-md bg-lb-bg border border-lb-border text-lb-muted hover:text-red-400 hover:border-red-400/60 transition cursor-pointer truncate">
              Não gostei
            </button>
            <button class="btn-seen px-1.5 py-1 rounded-md bg-lb-bg border border-lb-border text-lb-muted hover:text-white transition cursor-pointer truncate">
              Já vi
            </button>
            <button class="btn-skip px-1.5 py-1 rounded-md bg-lb-bg border border-lb-border text-lb-muted hover:text-slate-200 transition cursor-pointer truncate">
              Pular
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
