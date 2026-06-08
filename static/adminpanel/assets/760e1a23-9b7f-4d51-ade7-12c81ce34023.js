/* ===== Contacts / Messages View ===== */

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

function Contacts() {
  const { data: contacts, loading, error, refetch } = useAPI('/dashboard/api/contacts/');
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);

  const filtered = contacts
    ? contacts.filter(c => filter === 'all' ? true : filter === 'processed' ? c.is_processed : !c.is_processed)
    : [];

  const markProcessed = async (id) => {
    try {
      const res = await fetch('/dashboard/api/contacts/' + id + '/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '' },
        body: JSON.stringify({ is_processed: true })
      });
      if (!res.ok) throw new Error('Erreur');
      refetch();
      if (selected && selected.id === id) {
        setSelected({ ...selected, is_processed: true });
      }
    } catch (e) {
      alert('Erreur: ' + e.message);
    }
  };

  const unreadCount = contacts ? contacts.filter(c => !c.is_processed).length : '?';

  if (loading) {
    return (
      <div className="content">
        <div className="loading"><div className="spinner"></div><p>Chargement des messages…</p></div>
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
      <div className="filter-bar fade-in d1">
        <div className="stack">
          {[
            { id: 'all', label: 'Tous' },
            { id: 'unprocessed', label: 'Non traités' },
            { id: 'processed', label: 'Traités' },
          ].map(f => (
            <button
              key={f.id}
              className={`btn sm ${filter === f.id ? '' : 'ghost'}`}
              style={filter === f.id ? { background: 'var(--primary)', color: '#fff', borderColor: 'var(--primary)' } : {}}
              onClick={() => setFilter(f.id)}
            >{f.label}</button>
          ))}
        </div>
        <span className="pill amber dot" style={{ marginLeft: 'auto' }}>{unreadCount} non traité(s)</span>
        <button className="btn sm" onClick={refetch}><I.refresh size={14}/> Rafraîchir</button>
      </div>

      <div className="card fade-in d2">
        <div className="card-head">
          <div>
            <div className="card-title">Demandes de contact</div>
            <div className="card-sub">{filtered.length} message(s) reçu(s)</div>
          </div>
        </div>
        {filtered.length === 0 ? (
          <div className="empty">Aucun message trouvé.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Expéditeur</th>
                <th>Contact</th>
                <th>Sujet</th>
                <th>Message</th>
                <th>Date</th>
                <th>Statut</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody className="row-anim">
              {filtered.map((c, i) => (
                <tr key={c.id} style={{ animationDelay: `${0.03 * i}s`, cursor: 'pointer' }} onClick={() => setSelected(c)}>
                  <td style={{ fontWeight: 600 }}>{c.full_name}</td>
                  <td>
                    <div style={{ fontSize: 12.5 }}>{c.email}</div>
                    <div className="mono" style={{ fontSize: 11.5, color: 'var(--muted)' }}>{c.phone}</div>
                  </td>
                  <td>
                    <span className="pill gray">{c.subject}</span>
                  </td>
                  <td className="truncate" style={{ maxWidth: 200, color: 'var(--muted)' }}>{c.message}</td>
                  <td style={{ color: 'var(--muted)', fontSize: 12.5 }}>{c.created_at ? new Date(c.created_at).toLocaleDateString('fr-FR') : ''}</td>
                  <td>
                    <span className={`pill dot ${c.is_processed ? 'green' : 'amber'}`}>
                      {c.is_processed ? 'Traité' : 'Nouveau'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }} onClick={e => e.stopPropagation()}>
                    <div className="stack" style={{ justifyContent: 'flex-end' }}>
                      <button className="btn sm ghost" onClick={() => setSelected(c)}><I.eye size={14}/></button>
                      {!c.is_processed && (
                        <button className="btn sm ghost" style={{ color: 'var(--primary)' }} onClick={() => markProcessed(c.id)}>
                          <I.check size={14}/>
                        </button>
                      )}
                      <button className="btn sm ghost"><I.mail size={14}/></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selected && (
        <div className="modal-overlay open" onClick={() => setSelected(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 520 }}>
            <div style={{
              padding: '22px 24px',
              background: selected.is_processed ? 'var(--primary-light)' : '#FEF3C7',
              borderRadius: '16px 16px 0 0',
              borderBottom: '1px solid var(--border-soft)',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Message</div>
                  <div style={{ fontSize: 18, fontWeight: 700, marginTop: 2 }}>{selected.full_name}</div>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>{selected.created_at ? new Date(selected.created_at).toLocaleString('fr-FR') : ''}</div>
                </div>
                <span className={`pill dot ${selected.is_processed ? 'green' : 'amber'}`}>
                  {selected.is_processed ? 'Traité' : 'Non traité'}
                </span>
                <button className="icon-btn" onClick={() => setSelected(null)}><I.close size={18}/></button>
              </div>
            </div>
            <div className="modal-body" style={{ paddingTop: 18 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Email</div>
                  <div style={{ fontSize: 14, marginTop: 3 }}>{selected.email || '—'}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Téléphone</div>
                  <div className="mono" style={{ fontSize: 14, marginTop: 3 }}>{selected.phone || '—'}</div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Sujet</div>
                  <div style={{ fontSize: 14, marginTop: 3 }}><span className="pill">{selected.subject}</span></div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Message</div>
                  <div style={{
                    marginTop: 6, padding: 14,
                    background: '#FAFBFC', border: '1px solid var(--border-soft)',
                    borderRadius: 10, fontSize: 13.5, lineHeight: 1.6, whiteSpace: 'pre-wrap',
                  }}>{selected.message}</div>
                </div>
              </div>
            </div>
            <div className="modal-foot">
              <button className="btn" onClick={() => { window.location.href = 'mailto:' + selected.email; }}><I.mail size={14}/> Répondre</button>
              {!selected.is_processed && (
                <button className="btn primary" onClick={() => markProcessed(selected.id)}>
                  <I.check size={14}/> Marquer traité
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

window.Contacts = Contacts;
