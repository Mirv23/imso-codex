/* ===== Payment Providers / Moyens de paiement View ===== */

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

const PROVIDER_TYPES = [
  { id: 'moncash', label: 'MonCash', icon: '📱', color: '#E5202C' },
  { id: 'natcash', label: 'NatCash', icon: '📱', color: '#F39322' },
  { id: 'bank', label: 'Virement bancaire', icon: '🏦', color: '#1849A9' },
  { id: 'cash', label: 'Espèces', icon: '💰', color: '#2D6A4F' },
  { id: 'stripe', label: 'Carte bancaire', icon: '💳', color: '#6D28D9' },
  { id: 'manual', label: 'Autre manuel', icon: '📄', color: '#6B7280' },
];

const PT_MAP = Object.fromEntries(PROVIDER_TYPES.map(t => [t.id, t]));

function Providers() {
  const { data: providers, loading, error, refetch } = useAPI('/dashboard/api/providers/');
  const [modal, setModal] = useState(null);
  const [preview, setPreview] = useState(null);
  const [form, setForm] = useState({
    name: '', provider_type: 'moncash', is_active: true, sort_order: 0,
    instructions: '', checkout_url: '', api_public_key: '',
    account_holder: '', account_number: '',
  });

  const openNew = () => {
    setForm({
      name: '', provider_type: 'moncash', is_active: true, sort_order: 0,
      instructions: '', checkout_url: '', api_public_key: '',
      account_holder: '', account_number: '',
    });
    setModal('new');
  };

  const openEdit = (p) => {
    setForm({
      name: p.name,
      provider_type: p.provider_type,
      is_active: p.is_active,
      sort_order: p.sort_order || 0,
      instructions: p.instructions || '',
      checkout_url: p.checkout_url || '',
      api_public_key: p.api_public_key || '',
      account_holder: '',
      account_number: '',
    });
    setModal(p);
  };

  const buildInstructions = () => {
    const pt = PT_MAP[form.provider_type];
    const lines = [];
    if (form.account_number) lines.push('Numéro: ' + form.account_number);
    if (form.account_holder) lines.push('Titulaire: ' + form.account_holder);
    if (form.instructions) lines.push(form.instructions);
    return lines.join('\n');
  };

  const handleSave = async () => {
    try {
      const isNew = modal === 'new';
      const url = isNew ? '/dashboard/api/providers/create/' : '/dashboard/api/providers/' + modal.id + '/';
      const method = isNew ? 'POST' : 'PUT';
      const payload = {
        name: form.name,
        provider_type: form.provider_type,
        is_active: form.is_active,
        sort_order: form.sort_order,
        instructions: buildInstructions(),
        checkout_url: form.checkout_url,
        api_public_key: form.api_public_key,
      };
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Erreur lors de la sauvegarde');
      setModal(null);
      refetch();
    } catch (e) {
      alert(e.message);
    }
  };

  const toggleActive = async (p) => {
    try {
      const res = await fetch('/dashboard/api/providers/' + p.id + '/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '' },
        body: JSON.stringify({ is_active: !p.is_active }),
      });
      if (!res.ok) throw new Error('Erreur');
      refetch();
    } catch (e) {
      alert(e.message);
    }
  };

  const handleDelete = async (p) => {
    if (!confirm('Supprimer "' + p.name + '" ? Cette action est irréversible.')) return;
    try {
      const res = await fetch('/dashboard/api/providers/' + p.id + '/', {
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
        <div className="loading"><div className="spinner"></div><p>Chargement des moyens de paiement…</p></div>
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
        <div className="stack" style={{ gap: 20 }}>
          <div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Moyens configurés</div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }} className="num">{providers ? providers.length : 0}</div>
          </div>
          <div style={{ width: 1, height: 32, background: 'var(--border)' }}/>
          <div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Actifs</div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }} className="num">
              {providers ? providers.filter(p => p.is_active).length : 0}
            </div>
          </div>
        </div>
        <button className="btn primary" onClick={openNew}>
          <I.plus size={14} stroke={2.5}/> Ajouter un moyen
        </button>
      </div>

      {(!providers || providers.length === 0) ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>💳</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>Aucun moyen de paiement</div>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 6 }}>Ajoutez MonCash, NatCash, virement bancaire ou espèces.</div>
          <button className="btn primary" style={{ marginTop: 16 }} onClick={openNew}><I.plus size={14}/> Configurer</button>
        </div>
      ) : (
        <div className="card fade-in d2">
          <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
            <div>
              <div className="card-title">Moyens de paiement</div>
              <div className="card-sub">{providers.length} opérateurs configurés</div>
            </div>
          </div>
          <div style={{ padding: 14 }}>
            {providers.map((p, i) => {
              const pt = PT_MAP[p.provider_type] || PT_MAP.manual;
              return (
                <div key={p.id} style={{
                  display: 'grid', gridTemplateColumns: 'auto 1fr auto auto',
                  gap: 14, alignItems: 'center',
                  padding: '14px 16px',
                  border: '1px solid var(--border-soft)',
                  borderRadius: 12,
                  background: '#FAFBFC',
                  marginBottom: 8,
                  transition: 'box-shadow .15s',
                }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: pt.color + '18',
                    display: 'grid', placeItems: 'center',
                    fontSize: 20, flexShrink: 0,
                  }}>{pt.icon}</div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ fontSize: 14.5, fontWeight: 700 }}>{p.name}</div>
                      <span className="pill" style={{ fontSize: 10, background: pt.color + '18', color: pt.color, fontWeight: 600 }}>{pt.label}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 3 }} className="truncate">
                      {p.instructions ? p.instructions.slice(0, 80) + (p.instructions.length > 80 ? '…' : '') : 'Aucune instruction'}
                    </div>
                    <div className="stack" style={{ marginTop: 6, gap: 6 }}>
                      {p.checkout_url && <span className="pill gray" style={{ fontSize: 10 }}>API externe</span>}
                      {p.api_public_key && <span className="pill gray" style={{ fontSize: 10 }}>Clé API configurée</span>}
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <span className={`pill dot ${p.is_active ? 'green' : 'gray'}`}>
                      {p.is_active ? 'Actif' : 'Inactif'}
                    </span>
                    <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 2 }}>Ordre: {p.sort_order}</div>
                  </div>
                  <div className="stack" style={{ gap: 4 }}>
                    <button className="btn sm ghost" onClick={() => setPreview(p)} title="Aperçu client"><I.eye size={14}/></button>
                    <label className="toggle" onClick={e => e.stopPropagation()}>
                      <input type="checkbox" checked={p.is_active} onChange={() => toggleActive(p)}/>
                      <span className="track"></span>
                    </label>
                    <button className="btn sm ghost" onClick={() => openEdit(p)}><I.edit size={14}/></button>
                    <button className="btn sm ghost" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(p)}><I.trash size={14}/></button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {modal && (
        <div className="modal-overlay open" onClick={() => setModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 520 }}>
            <div className="modal-head">
              <div style={{ fontSize: 17, fontWeight: 700 }}>{modal === 'new' ? 'Ajouter un moyen de paiement' : 'Modifier le moyen de paiement'}</div>
              <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>Configurez un opérateur de paiement</div>
            </div>
            <div className="modal-body" style={{ maxHeight: 400, overflowY: 'auto' }}>
              <div className="field">
                <label>Type de provider</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                  {PROVIDER_TYPES.map(t => (
                    <button
                      key={t.id}
                      onClick={() => setForm(f => ({ ...f, provider_type: t.id }))}
                      style={{
                        padding: '9px 6px',
                        border: form.provider_type === t.id ? `1.5px solid ${t.color}` : '1.5px solid var(--border-soft)',
                        background: form.provider_type === t.id ? t.color + '12' : '#fff',
                        borderRadius: 9, cursor: 'pointer',
                        fontSize: 11.5, fontWeight: 600,
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                        transition: 'all .15s',
                      }}
                    >
                      <span style={{ fontSize: 18 }}>{t.icon}</span>
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="field">
                <label>Nom du provider</label>
                <input className="input" placeholder="ex: MonCash IMSO" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}/>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="field">
                  <label>Numéro de compte</label>
                  <input className="input mono" placeholder="ex: 509 3742 0918" value={form.account_number} onChange={e => setForm(f => ({ ...f, account_number: e.target.value }))}/>
                  <div className="hint">Non sauvegardé en DB. Sert à construire les instructions.</div>
                </div>
                <div className="field">
                  <label>Titulaire du compte</label>
                  <input className="input" placeholder="ex: John Doe" value={form.account_holder} onChange={e => setForm(f => ({ ...f, account_holder: e.target.value }))}/>
                  <div className="hint">Non sauvegardé en DB. Sert à construire les instructions.</div>
                </div>
              </div>

              <div className="field">
                <label>Instructions de paiement</label>
                <textarea className="textarea" placeholder="Instructions affichées au client lors du paiement..." value={form.instructions} onChange={e => setForm(f => ({ ...f, instructions: e.target.value }))} style={{ minHeight: 80 }}/>
                <div className="hint">Ces instructions seront affichées au client sur la page de paiement.</div>
              </div>

              <div className="field" style={{
                padding: 14, background: '#FFFBEB', borderRadius: 10,
                border: '1px solid #FDE68A',
              }}>
                <label style={{ color: '#92400E', marginBottom: 6 }}>Aperçu des instructions qui seront sauvées :</label>
                <div style={{ fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap', color: '#92400E' }}>
                  {buildInstructions() || '(aucune instruction générée)'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="field">
                  <label>URL de checkout externe</label>
                  <input className="input" placeholder="https://..." value={form.checkout_url} onChange={e => setForm(f => ({ ...f, checkout_url: e.target.value }))}/>
                  <div className="hint">Laissez vide pour un paiement manuel.</div>
                </div>
                <div className="field">
                  <label>Clé publique API</label>
                  <input className="input mono" placeholder="pk_..." value={form.api_public_key} onChange={e => setForm(f => ({ ...f, api_public_key: e.target.value }))}/>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="field">
                  <label>Ordre d'affichage</label>
                  <input className="input mono" type="number" value={form.sort_order} onChange={e => setForm(f => ({ ...f, sort_order: parseInt(e.target.value) || 0 }))}/>
                </div>
                <div className="field">
                  <label>Actif</label>
                  <div style={{ marginTop: 8 }}>
                    <label className="toggle">
                      <input type="checkbox" checked={form.is_active} onChange={() => setForm(f => ({ ...f, is_active: !f.is_active }))}/>
                      <span className="track"></span>
                      <span className="lbl">{form.is_active ? 'Actif' : 'Inactif'}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-foot">
              <button className="btn" onClick={() => setModal(null)}>Annuler</button>
              <button className="btn primary" onClick={handleSave}>
                <I.check size={14}/> {modal === 'new' ? 'Ajouter' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {preview && (
        <div className="modal-overlay open" onClick={() => setPreview(null)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 460 }}>
            <div style={{
              padding: '22px 24px',
              background: 'linear-gradient(135deg, #F0F8F3, #FDF7EE)',
              borderRadius: '16px 16px 0 0',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: (PT_MAP[preview.provider_type] || PT_MAP.manual).color + '18',
                    display: 'grid', placeItems: 'center', fontSize: 20,
                  }}>{(PT_MAP[preview.provider_type] || PT_MAP.manual).icon}</div>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Aperçu client</div>
                    <div style={{ fontSize: 16, fontWeight: 700 }}>{preview.name}</div>
                  </div>
                </div>
                <span className="pill green dot">Visible client</span>
                <button className="icon-btn" onClick={() => setPreview(null)}><I.close size={18}/></button>
              </div>
            </div>
            <div className="modal-body">
              <div style={{ padding: 16, border: '1px solid var(--border)', borderRadius: 10, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, marginBottom: 8 }}>Instructions</div>
                <div style={{ fontSize: 13.5, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {preview.instructions || 'Aucune instruction.'}
                </div>
              </div>
              <div style={{ padding: 14, background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#92400E', marginBottom: 4 }}>💡 Ce que le client voit</div>
                <div style={{ fontSize: 12.5, color: '#92400E', lineHeight: 1.5 }}>
                  Le client sélectionne ce moyen de paiement, voit les instructions ci-dessus, effectue le virement, puis télécharge la preuve (screenshot + ID transaction).
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

window.Providers = Providers;
