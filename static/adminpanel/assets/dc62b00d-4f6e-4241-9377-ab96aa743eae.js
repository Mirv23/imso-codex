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
  const [sort, setSort] = useState({ k: 'date', dir: 'desc' });
  const rows = MEMBERS.slice(0, 6);
  const sorted = [...rows].sort((a, b) => {
    if (sort.k === 'name') return sort.dir === 'asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
    return 0;
  });
  const headers = [
    { k: 'name', l: 'Membre' },
    { k: 'gei', l: 'GEI' },
    { k: 'status', l: 'Statut' },
    { k: 'date', l: 'Inscription' },
    { k: 'act', l: '' },
  ];
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
        {sorted.map((m, i) => (
          <tr key={m.id} style={{ animationDelay: `${0.05 * i}s` }}>
            <td>
              <div className="name-cell">
                <div className={`avatar sm ${m.avatar}`}>{m.initials}</div>
                <div className="name-meta">
                  <div className="nm">{m.name}</div>
                  <div className="em">{m.email}</div>
                </div>
              </div>
            </td>
            <td><span className={`gei ${m.gei}`}>{m.gei}</span></td>
            <td>
              <span className={`pill dot ${m.status === 'Actif' ? 'green' : m.status === 'Attente' ? 'amber' : 'red'}`}>
                {m.status}
              </span>
            </td>
            <td style={{ color: 'var(--muted)' }}>{m.date}</td>
            <td><button className="btn sm ghost" onClick={() => alert(`Profil de ${m.name}`)}>Voir <I.chevronR size={12}/></button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PaymentsTable() {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Membre</th>
          <th>Cours</th>
          <th style={{ textAlign: 'right' }}>Montant</th>
          <th>Méthode</th>
          <th>Statut</th>
        </tr>
      </thead>
      <tbody className="row-anim">
        {PAYMENTS.map((p, i) => (
          <tr key={p.id} style={{ animationDelay: `${0.05 * i}s` }}>
            <td>
              <div style={{ fontWeight: 600 }}>{p.member}</div>
              <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>{p.date}</div>
            </td>
            <td style={{ color: 'var(--muted)' }} className="truncate" >{p.course}</td>
            <td className="num mono" style={{ textAlign: 'right', fontWeight: 600 }}>
              {fmtNum(p.amount)}
              <span style={{ color: 'var(--muted)', fontWeight: 500, fontSize: 11, marginLeft: 3 }}>HTG</span>
            </td>
            <td>
              <span className={`pill ${p.method === 'MonCash' ? 'amber' : 'violet'}`}>{p.method}</span>
            </td>
            <td>
              <span className={`pill dot ${p.status === 'Réussi' ? 'green' : p.status === 'En attente' ? 'amber' : 'red'}`}>
                {p.status}
              </span>
            </td>
          </tr>
        ))}
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
          <LineChart data={REVENUE} color="#2D6A4F"/>
        </div>

        <div className="card fade-in d5">
          <div className="card-head">
            <div>
              <div className="card-title">Répartition par catégorie</div>
              <div className="card-sub">Sur 24 cours publiés</div>
            </div>
            <button className="btn sm ghost"><I.more size={16}/></button>
          </div>
          <DonutChart data={CATEGORIES}/>
          <div className="donut-legend">
            {CATEGORIES.map((c, i) => (
              <div key={i} className="legend-row">
                <div className="sw" style={{ background: c.color }}/>
                <div className="lbl">{c.name}</div>
                <div className="pct">{c.value}%</div>
              </div>
            ))}
          </div>
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
