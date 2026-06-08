/* ===== GEI / Groupes d'Entraide Intégrée View ===== */

const { useState, useEffect } = React;

function useAPI(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const refetch = () => {
    setLoading(true);
    setError(null);
    fetch(url)
      .then(r => r.ok ? r.json() : Promise.reject('Erreur ' + r.status))
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e); setLoading(false); });
  };
  useEffect(refetch, [url]);
  return { data, loading, error, refetch };
}

function Geis() {
  const { data: geis, loading, error, refetch } = useAPI('/dashboard/api/geis/');
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState({ name: '', city: '', coordinator: '' });

  const openNew = () => {
    setForm({ name: '', city: '', coordinator: '' });
    setModal('new');
  };

  const openEdit = (g) => {
    setForm({ name: g.name, city: g.city, coordinator: g.coordinator || '' });
    setModal(g);
  };

  const handleSave = async () => {
    try {
      const isNew = modal === 'new';
      const url = isNew ? '/dashboard/api/geis/create/' : '/dashboard/api/geis/' + modal.id + '/';
      const method = isNew ? 'POST' : 'PUT';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error('Erreur lors de la sauvegarde');
      setModal(null);
      refetch();
    } catch (e) {
      alert(e.message);
    }
  };

  const toggleActive = async (g) => {
    try {
      const res = await fetch('/dashboard/api/geis/' + g.id + '/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '' },
        body: JSON.stringify({ is_active: !g.is_active }),
      });
      if (!res.ok) throw new Error('Erreur');
      refetch();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleDelete = async (g) => {
    if (!confirm('Supprimer le GEI "' + g.name + '" ? Cette action est irréversible.')) return;
    try {
      const res = await fetch('/dashboard/api/geis/' + g.id + '/', {
        method: 'DELETE',
        headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '' },
      });
      if (!res.ok) throw new Error('Erreur lors de la suppression');
      refetch();
    } catch (e) {
      alert(e.message);
    }
  };

  if (loading) {
    return (
      <div className="content">
        <div className="loading"><div className="spinner"></div><p>Chargement des GEI…</p></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="content">
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>⚠️</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>Erreur de chargement</div>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 6 }}>{error}</div>
          <button className="btn primary" style={{ marginTop: 16 }} onClick={refetch}>Réessayer</button>
        </div>
      </div>
    );
  }

  return (
    <div className="content">
      <div className="between fade-in d1" style={{ marginBottom: 18 }}>
        <div>
          <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Total GEI</div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }} className="num">{geis ? geis.length : 0}</div>
        </div>
        <button className="btn primary" onClick={openNew}>
          <I.plus size={14} stroke={2.5}/> Nouveau GEI
        </button>
      </div>

      {(!geis || geis.length === 0) ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🗺️</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>Aucun GEI</div>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 6 }}>Créez votre premier groupe d'entraide.</div>
          <button className="btn primary" style={{ marginTop: 16 }} onClick={openNew}><I.plus size={14}/> Créer un GEI</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18 }}>
          {geis.map((g, i) => (
            <div key={g.id} className="card fade-in" style={{ animationDelay: `${0.04 * i}s` }}>
              <div style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, letterSpacing: '-0.01em' }}>{g.name}</div>
                    <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 5 }}>
                      <I.pin size={12}/> {g.city}
                    </div>
                  </div>
                  <label className="toggle" onClick={e => e.stopPropagation()}>
                    <input type="checkbox" checked={g.is_active} onChange={() => toggleActive(g)}/>
                    <span className="track"></span>
                  </label>
                </div>

                <div style={{ marginTop: 16, padding: 14, background: '#FAFBFC', borderRadius: 10, border: '1px solid var(--border-soft)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Coordinateur</div>
                      <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2 }}>{g.coordinator || '—'}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Membres</div>
                      <div style={{ fontSize: 20, fontWeight: 700 }} className="num">{g.member_count}</div>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: 4 }}>
                  <span className={`pill dot ${g.is_active ? 'green' : 'gray'}`}>
                    {g.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </div>

                <div className="stack" style={{ marginTop: 16, justifyContent: 'flex-end' }}>
                  <button className="btn sm ghost" onClick={() => openEdit(g)}><I.edit size={14}/> Modifier</button>
                  <button className="btn sm ghost" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(g)}><I.trash size={14}/> Supprimer</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <div className="modal-overlay open" onClick={() => setModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-head">
              <div style={{ fontSize: 17, fontWeight: 700 }}>{modal === 'new' ? 'Nouveau GEI' : 'Modifier le GEI'}</div>
              <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>Groupe d'Entraide Intégrée</div>
            </div>
            <div className="modal-body">
              <div className="field">
                <label>Nom du GEI</label>
                <input className="input" placeholder="ex: PAP" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}/>
              </div>
              <div className="field">
                <label>Ville</label>
                <input className="input" placeholder="ex: Port-au-Prince" value={form.city} onChange={e => setForm(f => ({ ...f, city: e.target.value }))}/>
              </div>
              <div className="field">
                <label>Coordinateur</label>
                <input className="input" placeholder="Nom du coordinateur" value={form.coordinator} onChange={e => setForm(f => ({ ...f, coordinator: e.target.value }))}/>
              </div>
            </div>
            <div className="modal-foot">
              <button className="btn" onClick={() => setModal(null)}>Annuler</button>
              <button className="btn primary" onClick={handleSave}>
                <I.check size={14}/> {modal === 'new' ? 'Créer' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

window.Geis = Geis;
