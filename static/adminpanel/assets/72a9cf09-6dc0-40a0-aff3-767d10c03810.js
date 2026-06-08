function Members() {
  const [q, setQ] = useState('');
  const [geiFilter, setGeiFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState({ k: 'joined_at', dir: 'desc' });

  const perPage = 10;

  const params = new URLSearchParams();
  if (q) params.set('search', q);
  if (geiFilter) params.set('gei', geiFilter);
  if (statusFilter) params.set('status', statusFilter);
  const apiUrl = '/dashboard/api/members/?' + params.toString();

  const { data: raw, loading, error, refetch } = useAPIDebounced(apiUrl, 350);

  const allMembers = Array.isArray(raw) ? raw : [];

  const actifs = allMembers.filter(m => m.status === 'Actif').length;
  const attente = allMembers.filter(m => m.status === 'Attente').length;
  const suspendus = allMembers.filter(m => m.status === 'Suspendu').length;

  let filtered = [...allMembers].sort((a, b) => {
    const getVal = (m, k) => {
      if (k === 'name') return (m.first_name+' '+m.last_name).trim().toLowerCase();
      if (k === 'gei') return (typeof m.gei === 'object' && m.gei ? m.gei.name||m.gei.code||m.gei : m.gei||'').toLowerCase();
      if (k === 'status') return (m.status||'').toLowerCase();
      return '';
    };
    const av = getVal(a, sort.k), bv = getVal(b, sort.k);
    if (av < bv) return sort.dir === 'asc' ? -1 : 1;
    if (av > bv) return sort.dir === 'asc' ? 1 : -1;
    return 0;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const pageRows = filtered.slice((page - 1) * perPage, page * perPage);

  useEffect(() => { setPage(1); }, [q, geiFilter, statusFilter]);

  const Sort = ({ k, l, align }) => (
    <th
      className={sort.k === k ? 'sorted' : ''}
      style={align ? { textAlign: align } : {}}
      onClick={() => setSort(s => ({ k, dir: s.k === k && s.dir === 'asc' ? 'desc' : 'asc' }))}
    >
      {l}
      <span className="sort-ind">
        {sort.k === k ? (sort.dir === 'asc' ? <I.sortUp/> : <I.sortDown/>) : <I.sort/>}
      </span>
    </th>
  );

  if (error) return (
    <div className="content">
      <div className="card" style={{ padding: 48, textAlign: 'center' }}>
        <div style={{ color: 'var(--danger)', marginBottom: 12 }}>Erreur de chargement</div>
        <button className="btn primary" onClick={refetch}>Réessayer</button>
      </div>
    </div>
  );

  return (
    <div className="content">
      <div className="filter-bar fade-in d1">
        <div className="search">
          <I.search size={16}/>
          <input placeholder="Rechercher par nom ou email…" value={q} onChange={e => setQ(e.target.value)}/>
          <kbd>⌘K</kbd>
        </div>
        <div className={`chip-select ${geiFilter ? 'active' : ''}`}>
          <I.pin size={13}/> {geiFilter || 'Tous GEI'}
          <I.chevron size={12}/>
          <select value={geiFilter} onChange={e => setGeiFilter(e.target.value)}>
            <option value="">Tous GEI</option>
            <option>PAP</option><option>CAP</option><option>JAC</option>
            <option>LGN</option><option>GON</option><option>CYS</option>
          </select>
        </div>
        <div className={`chip-select ${statusFilter ? 'active' : ''}`}>
          <I.spark size={13}/> {statusFilter || 'Tous statuts'}
          <I.chevron size={12}/>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">Tous statuts</option>
            <option>Actif</option><option>Attente</option><option>Suspendu</option>
          </select>
        </div>
        <div className="chip-select">
          <I.calendar size={13}/> Toutes dates <I.chevron size={12}/>
        </div>
        <div style={{ flex: 1 }}/>
        <button className="btn"><I.download size={14}/> Exporter CSV</button>
        <button className="btn primary"><I.plus size={14} stroke={2.5}/> Inviter</button>
      </div>

      <div className="card fade-in d2">
        <div className="card-head" style={{ paddingBottom: 14, borderBottom: '1px solid var(--border-soft)' }}>
          <div>
            <div className="card-title">Tous les membres</div>
            <div className="card-sub">{loading ? 'Chargement...' : filtered.length + ' membres correspondants'}</div>
          </div>
          <div className="stack">
            <span className="pill green">{actifs} actifs</span>
            <span className="pill amber">{attente} en attente</span>
            <span className="pill red">{suspendus} suspendus</span>
          </div>
        </div>
        <table className="table">
          <thead>
            <tr>
              <Sort k="name" l="Membre"/>
              <th>Contact</th>
              <Sort k="gei" l="GEI"/>
              <th>Inscription</th>
              <Sort k="status" l="Statut"/>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody className="row-anim">
            {loading ? (
              <tr><td colSpan="6" className="empty">Chargement...</td></tr>
            ) : pageRows.length === 0 ? (
              <tr><td colSpan="6" className="empty">Aucun membre ne correspond à ces filtres.</td></tr>
            ) : pageRows.map((m, i) => {
              const name = (m.first_name+' '+m.last_name).trim();
              const geiName = typeof m.gei === 'object' && m.gei ? m.gei.name||m.gei.code||m.gei : m.gei||'';
              return (
              <tr key={m.id} style={{ animationDelay: `${0.03 * i}s` }}>
                <td>
                  <div className="name-cell">
                    <div className={`avatar sm ${avatarColor(name)}`}>{initials(m.first_name, m.last_name)}</div>
                    <div className="name-meta">
                      <div className="nm">{name}</div>
                      <div className="em">ID #{m.id}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div style={{ fontSize: 12.5 }}>{m.email}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--muted)' }} className="mono">{m.phone}</div>
                </td>
                <td><span className={`gei`}>{geiName}</span></td>
                <td style={{ color: 'var(--muted)' }}>{fmtDate(m.joined_at)}</td>
                <td>
                  <span className={`pill dot ${m.status === 'Actif' ? 'green' : m.status === 'Attente' ? 'amber' : 'red'}`}>
                    {m.status}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <div className="stack" style={{ justifyContent: 'flex-end' }}>
                    <button className="btn sm ghost" onClick={() => alert(`Profil de ${name}`)}><I.eye size={14}/></button>
                    <button className="btn sm ghost"><I.mail size={14}/></button>
                    <button className="btn sm ghost"><I.more size={14}/></button>
                  </div>
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
        <div className="pager">
          <div className="pager-info">
            {!loading && `Affichage ${(page - 1) * perPage + 1}–${Math.min(page * perPage, filtered.length)} sur ${filtered.length} membres`}
          </div>
          <div className="pager-nav">
            <button className="pager-btn" disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))}><I.chevronL size={14}/></button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
              <button key={p} className={`pager-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
            ))}
            <button className="pager-btn" disabled={page === totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))}><I.chevronR size={14}/></button>
          </div>
        </div>
      </div>
    </div>
  );
}

window.Members = Members;
