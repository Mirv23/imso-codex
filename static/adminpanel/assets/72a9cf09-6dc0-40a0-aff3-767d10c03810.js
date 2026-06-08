function Members() {
  const [q, setQ] = useState('');
  const [gei, setGei] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState({ k: 'date', dir: 'desc' });

  const perPage = 10;

  let filtered = MEMBERS.filter(m => {
    if (q && !(`${m.name} ${m.email}`.toLowerCase().includes(q.toLowerCase()))) return false;
    if (gei && m.gei !== gei) return false;
    if (status && m.status !== status) return false;
    return true;
  });

  filtered = [...filtered].sort((a, b) => {
    if (sort.k === 'name') return sort.dir === 'asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
    if (sort.k === 'gei') return sort.dir === 'asc' ? a.gei.localeCompare(b.gei) : b.gei.localeCompare(a.gei);
    if (sort.k === 'status') return sort.dir === 'asc' ? a.status.localeCompare(b.status) : b.status.localeCompare(a.status);
    return 0;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
  const pageRows = filtered.slice((page - 1) * perPage, page * perPage);

  useEffect(() => { setPage(1); }, [q, gei, status]);

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

  return (
    <div className="content">
      <div className="filter-bar fade-in d1">
        <div className="search">
          <I.search size={16}/>
          <input placeholder="Rechercher par nom ou email…" value={q} onChange={e => setQ(e.target.value)}/>
          <kbd>⌘K</kbd>
        </div>
        <div className={`chip-select ${gei ? 'active' : ''}`}>
          <I.pin size={13}/> {gei || 'Tous GEI'}
          <I.chevron size={12}/>
          <select value={gei} onChange={e => setGei(e.target.value)}>
            <option value="">Tous GEI</option>
            <option>PAP</option><option>CAP</option><option>JAC</option>
            <option>LGN</option><option>GON</option><option>CYS</option>
          </select>
        </div>
        <div className={`chip-select ${status ? 'active' : ''}`}>
          <I.spark size={13}/> {status || 'Tous statuts'}
          <I.chevron size={12}/>
          <select value={status} onChange={e => setStatus(e.target.value)}>
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
            <div className="card-sub">{filtered.length} membres correspondants · Mis à jour il y a quelques secondes</div>
          </div>
          <div className="stack">
            <span className="pill green">{MEMBERS.filter(m => m.status === 'Actif').length} actifs</span>
            <span className="pill amber">{MEMBERS.filter(m => m.status === 'Attente').length} en attente</span>
            <span className="pill red">{MEMBERS.filter(m => m.status === 'Suspendu').length} suspendus</span>
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
            {pageRows.length === 0 ? (
              <tr><td colSpan="6" className="empty">Aucun membre ne correspond à ces filtres.</td></tr>
            ) : pageRows.map((m, i) => (
              <tr key={m.id} style={{ animationDelay: `${0.03 * i}s` }}>
                <td>
                  <div className="name-cell">
                    <div className={`avatar sm ${m.avatar}`}>{m.initials}</div>
                    <div className="name-meta">
                      <div className="nm">{m.name}</div>
                      <div className="em">ID #{m.id.replace('m', '00')}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div style={{ fontSize: 12.5 }}>{m.email}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--muted)' }} className="mono">{m.phone}</div>
                </td>
                <td><span className={`gei ${m.gei}`}>{m.gei}</span></td>
                <td style={{ color: 'var(--muted)' }}>{m.date}</td>
                <td>
                  <span className={`pill dot ${m.status === 'Actif' ? 'green' : m.status === 'Attente' ? 'amber' : 'red'}`}>
                    {m.status}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <div className="stack" style={{ justifyContent: 'flex-end' }}>
                    <button className="btn sm ghost" onClick={() => alert(`Profil de ${m.name}`)}><I.eye size={14}/></button>
                    <button className="btn sm ghost"><I.mail size={14}/></button>
                    <button className="btn sm ghost"><I.more size={14}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="pager">
          <div className="pager-info">
            Affichage <b>{(page - 1) * perPage + 1}</b>–<b>{Math.min(page * perPage, filtered.length)}</b> sur <b>{filtered.length}</b> membres
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
