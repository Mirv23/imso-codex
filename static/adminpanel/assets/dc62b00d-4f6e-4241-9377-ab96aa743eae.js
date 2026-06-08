function MetricCard({ ico, color, label, value, prefix = '', suffix = '', trend, trendUp, spark, delay }) {
  const animated = useCountUp(value, 1500);
  return (
    <div className={`metric fade-in d${delay}`}>
      <div className={`metric-ico ${color}`}>{ico}</div>
      <div className="metric-label">{label}</div>
      <div className="metric-value num">{prefix}{fmtNum(animated)}{suffix}</div>
      <div className="metric-foot">
        <span className={`pill ${trendUp ? 'green' : 'red'}`}>
          {trendUp ? <I.trend size={11} stroke={2.5}/> : <I.trendDown size={11} stroke={2.5}/>}
          {trend}
        </span>
        <Sparkline data={spark} color={trendUp ? '#10B981' : '#EF4444'}/>
      </div>
    </div>
  );
}

function MembersTable() {
  const { data: members, loading } = useAPI('/dashboard/api/members/?per_page=6');
  const [sort, setSort] = useState({ k: 'joined_at', dir: 'desc' });
  const rows = Array.isArray(members) ? members.slice(0, 6) : [];
  const sorted = [...rows].sort((a, b) => {
    if (sort.k === 'name') {
      const aN = (a.first_name+' '+a.last_name).trim();
      const bN = (b.first_name+' '+b.last_name).trim();
      return sort.dir === 'asc' ? aN.localeCompare(bN) : bN.localeCompare(aN);
    }
    return 0;
  });
  const headers = [
    { k: 'name', l: 'Membre' },
    { k: 'gei', l: 'GEI' },
    { k: 'status', l: 'Statut' },
    { k: 'joined_at', l: 'Inscription' },
    { k: 'act', l: '' },
  ];
  if (loading) return <div className="loading" style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>Chargement...</div>;
  return (
    <table className="table">
      <thead>
        <tr>
          {headers.map(h => (
            <th key={h.k}
              className={sort.k === h.k ? 'sorted' : ''}
              onClick={() => h.k !== 'act' && setSort(s => ({ k: h.k, dir: s.k === h.k && s.dir === 'asc' ? 'desc' : 'asc' }))}
            >
              {h.l}
              {h.k !== 'act' && (
                <span className="sort-ind">
                  {sort.k === h.k ? (sort.dir === 'asc' ? <I.sortUp/> : <I.sortDown/>) : <I.sort/>}
                </span>
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="row-anim">
        {sorted.map((m, i) => {
          const name = (m.first_name+' '+m.last_name).trim();
          const geiName = typeof m.gei === 'object' && m.gei ? m.gei.name || m.gei.code || m.gei : m.gei || '';
          return (
            <tr key={m.id} style={{ animationDelay: `${0.05 * i}s` }}>
              <td>
                <div className="name-cell">
                  <div className={`avatar sm ${avatarColor(name)}`}>{initials(m.first_name, m.last_name)}</div>
                  <div className="name-meta">
                    <div className="nm">{name}</div>
                    <div className="em">{m.email}</div>
                  </div>
                </div>
              </td>
              <td><span className={`gei`}>{geiName}</span></td>
              <td>
                <span className={`pill dot ${m.status === 'Actif' ? 'green' : m.status === 'Attente' ? 'amber' : 'red'}`}>
                  {m.status}
                </span>
              </td>
              <td style={{ color: 'var(--muted)' }}>{fmtDate(m.joined_at)}</td>
              <td><button className="btn sm ghost" onClick={() => alert(`Profil de ${name}`)}>Voir <I.chevronR size={12}/></button></td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function PaymentsTable() {
  const { data: payments, loading } = useAPI('/dashboard/api/payments/?per_page=6');
  const rows = Array.isArray(payments) ? payments.slice(0, 6) : [];
  if (loading) return <div className="loading" style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>Chargement...</div>;
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Client</th>
          <th>Motif</th>
          <th style={{ textAlign: 'right' }}>Montant</th>
          <th>Opérateur</th>
          <th>Statut</th>
        </tr>
      </thead>
      <tbody className="row-anim">
        {rows.map((p, i) => {
          const provider = typeof p.provider === 'object' && p.provider ? p.provider.name || p.provider : p.provider__name || '';
          return (
            <tr key={p.id} style={{ animationDelay: `${0.05 * i}s` }}>
              <td>
                <div style={{ fontWeight: 600 }}>{p.payer_name}</div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>{fmtDateTime(p.created_at)}</div>
              </td>
              <td style={{ color: 'var(--muted)' }} className="truncate">{p.purpose || p.reference}</td>
              <td className="num mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                {fmtNum(p.amount_htg)}
                <span style={{ color: 'var(--muted)', fontWeight: 500, fontSize: 11, marginLeft: 3 }}>HTG</span>
              </td>
              <td>
                <span className={`pill ${provider === 'MonCash' ? 'amber' : 'violet'}`}>{provider}</span>
              </td>
              <td>
                <span className={`pill dot ${p.status === 'Réussi' || p.status === 'Confirmé' ? 'green' : p.status === 'En attente' ? 'amber' : 'red'}`}>
                  {p.status}
                </span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

const DASHBOARD_SUMMARY_FALLBACK = {
  active_members: 1247,
  active_gei: 5,
  active_courses: 24,
  pending_contacts: 0,
  pending_bookings: 0,
  savings_htg: 847500,
};

function useDashboardSummary() {
  const [summary, setSummary] = useState(window.IMSO_DASHBOARD_SUMMARY || DASHBOARD_SUMMARY_FALLBACK);

  useEffect(() => {
    fetch('/dashboard/api/summary/')
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (data) setSummary({ ...DASHBOARD_SUMMARY_FALLBACK, ...data });
      })
      .catch(() => {});
  }, []);

  return { ...DASHBOARD_SUMMARY_FALLBACK, ...summary };
}

function Dashboard() {
  const summary = useDashboardSummary();
  const openRequests = summary.pending_contacts + summary.pending_bookings;
  return (
    <div className="content">
      <div className="metric-grid">
        <MetricCard
          ico={<I.users size={20}/>} color="green"
          label="Membres actifs" value={summary.active_members}
          trend="Base Django" trendUp={true}
          spark={[42,48,55,53,62,68,74,82]} delay={1}
        />
        <MetricCard
          ico={<I.book size={20}/>} color="orange"
          label="Cours actifs" value={summary.active_courses}
          trend={`${summary.active_gei} GEI actifs`} trendUp={true}
          spark={[10,12,14,15,18,20,22,24]} delay={2}
        />
        <MetricCard
          ico={<I.cash size={20}/>} color="blue"
          label="Epargne mensuelle (HTG)" value={summary.savings_htg}
          trend="Membres actifs" trendUp={true}
          spark={[412,485,528,601,723,802,830,847]} delay={3}
        />
        <MetricCard
          ico={<I.mail size={20}/>} color="violet"
          label="Demandes ouvertes" value={openRequests}
          trend={`${summary.pending_contacts} contact · ${summary.pending_bookings} salle`} trendUp={openRequests === 0}
          spark={[28,32,30,34,29,27,25,24]} delay={4}
        />
      </div>

      <div className="chart-grid">
        <div className="card fade-in d4">
          <div className="card-head">
            <div>
              <div className="card-title">Revenus des 6 derniers mois</div>
              <div className="card-sub">Total HTG sur la période · Mise à jour il y a 4 min</div>
            </div>
            <div className="stack">
              <span className="pill green dot">+18.4%</span>
              <button className="btn sm">6 mois <I.chevron size={12}/></button>
            </div>
          </div>
          <LineChart data={[]} color="#2D6A4F"/>
        </div>

        <div className="card fade-in d5">
          <div className="card-head">
            <div>
              <div className="card-title">Répartition par catégorie</div>
              <div className="card-sub">Sur 24 cours publiés</div>
            </div>
            <button className="btn sm ghost"><I.more size={16}/></button>
          </div>
          <DonutChart data={[]}/>
        </div>
      </div>

      <div className="tables-grid">
        <div className="card fade-in d6">
          <div className="card-head">
            <div>
              <div className="card-title">Membres récents</div>
              <div className="card-sub">Derniers inscrits sur la plateforme</div>
            </div>
            <button className="btn sm ghost">Voir tous <I.arrow size={14}/></button>
          </div>
          <MembersTable/>
        </div>

        <div className="card fade-in d7">
          <div className="card-head">
            <div>
              <div className="card-title">Derniers paiements</div>
              <div className="card-sub">Transactions des dernières 24h</div>
            </div>
            <button className="btn sm ghost">Tout voir <I.arrow size={14}/></button>
          </div>
          <PaymentsTable/>
        </div>
      </div>

      <div className="ai-card fade-in d7">
        <div style={{ position: 'relative', zIndex: 1 }}>
          <span className="ai-tag">
            <I.ai size={11} stroke={2.5}/> Agent IA · Auto-publication
          </span>
          <div className="ai-quote">
            "Le discipulat n'est pas un programme, c'est une marche. Aujourd'hui, IMSO Haïti accompagne 1 247 frères et sœurs sur ce chemin — et notre nouveau module sur Romains ouvre demain. Inscrivez-vous, la place vous attend. 🇭🇹"
          </div>
          <div className="ai-meta">
            <span style={{ color: 'var(--muted)' }}>Publié il y a 2h sur :</span>
            <div className="stack" style={{ gap: 6 }}>
              <div className="platform-ico" style={{ background: '#1877F2' }}>f</div>
              <div className="platform-ico" style={{ background: 'linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045)' }}>IG</div>
              <div className="platform-ico" style={{ background: '#25D366' }}>W</div>
            </div>
            <span style={{ color: 'var(--muted)' }}>· Modèle Haiku 4.5</span>
          </div>
        </div>
        <div className="stat-row" style={{ position: 'relative', zIndex: 1 }}>
          <div>
            <div className="v">12.4k</div>
            <div className="l">Portée</div>
          </div>
          <div>
            <div className="v">4.8%</div>
            <div className="l">Engagement</div>
          </div>
          <div>
            <div className="v">187</div>
            <div className="l">Commentaires</div>
          </div>
        </div>
        <button className="btn primary" style={{ position: 'relative', zIndex: 1 }}>
          Gérer l'agent IA <I.arrow size={14}/>
        </button>
      </div>
    </div>
  );
}

window.Dashboard = Dashboard;
