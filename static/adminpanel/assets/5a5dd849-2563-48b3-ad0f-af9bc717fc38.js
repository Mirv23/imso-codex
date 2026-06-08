// Helpers API
async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error('Erreur ' + res.status);
  return res.json();
}

async function apiPut(url, data) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Erreur ' + res.status);
  return res.json();
}

async function apiPost(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Erreur ' + res.status);
  return res.json();
}

function useAPI(url) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  React.useEffect(() => {
    setLoading(true);
    setError(null);
    apiGet(url).then(setData).catch(setError).finally(() => setLoading(false));
  }, [url]);
  return { data, loading, error, refetch: () => apiGet(url).then(setData).catch(setError) };
}

function useAPIDebounced(url, delay) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  React.useEffect(() => {
    if (!url) return;
    const timer = setTimeout(() => {
      setLoading(true);
      setError(null);
      apiGet(url).then(setData).catch(setError).finally(() => setLoading(false));
    }, delay || 400);
    return () => clearTimeout(timer);
  }, [url, delay]);
  return { data, loading, error, refetch: () => apiGet(url).then(setData).catch(setError) };
}

const fmtNum = (n) => (n || 0).toLocaleString('fr-FR');
const fmtHTG = (n) => (n || 0).toLocaleString('fr-FR') + ' HTG';

const AVATAR_COLORS = ['warm', 'blue', 'purple', 'teal', 'rose', 'amber'];
function avatarColor(str) {
  let hash = 0;
  for (let i = 0; i < (str||'').length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function initials(first, last) {
  return ((first||'')[0]||'') + ((last||'')[0]||'');
}

function fmtDate(d) {
  if (!d) return '';
  try { return new Date(d).toLocaleDateString('fr-FR', { day:'numeric', month:'short', year:'numeric' }); } catch { return ''; }
}

function fmtTime(d) {
  if (!d) return '';
  try { return new Date(d).toLocaleTimeString('fr-FR', { hour:'2-digit', minute:'2-digit' }); } catch { return ''; }
}

function fmtDateTime(d) {
  if (!d) return '';
  try {
    const dt = new Date(d);
    return dt.toLocaleDateString('fr-FR', { day:'numeric', month:'short', year:'numeric' }) + ' · ' + dt.toLocaleTimeString('fr-FR', { hour:'2-digit', minute:'2-digit' });
  } catch { return ''; }
}

Object.assign(window, {
  fmtNum, fmtHTG, apiGet, apiPut, apiPost, useAPI, useAPIDebounced,
  avatarColor, initials, fmtDate, fmtTime, fmtDateTime,
});
