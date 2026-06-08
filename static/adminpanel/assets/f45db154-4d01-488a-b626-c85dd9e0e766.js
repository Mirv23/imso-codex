const TITLES = {
  dashboard: { t: 'Tableau de bord', s: 'Vue d\'ensemble de votre plateforme' },
  members: { t: 'Membres', s: 'Gérez les inscriptions et les statuts des apprenants' },
  courses: { t: 'Cours & Contenu', s: 'Publiez vos cours, ebooks et ressources pédagogiques' },
  room: { t: 'Salle & Réservations', s: 'Gérez les locations de la salle IMSO' },
  payments: { t: 'Paiements', s: 'Tous les paiements traités via opérateurs haïtiens' },
  contacts: { t: 'Messages', s: 'Demandes de contact des visiteurs' },
  geis: { t: 'GEI', s: 'Groupes d\'Entraide Intégrée' },
  providers: { t: 'Moyens de paiement', s: 'Configurez les opérateurs de paiement' },
  ai: { t: 'Agents IA', s: 'Créateur de contenu & Qualificateur de leads' },
  stats: { t: 'Statistiques', s: 'Analyses détaillées, rétention par cohorte et exports' },
  settings: { t: 'Paramètres', s: 'Configurations de la plateforme' },
};

function Header({ view }) {
  const [notif, setNotif] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const meta = TITLES[view] || TITLES.dashboard;
  const ref = useRef(null);
  const { data: notifs, loading: notifLoading, refetch } = useAPI('/dashboard/api/notifications/');
  const lastSince = useRef(new Date().toISOString());

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setNotif(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  // Poll for new notifications every 15s
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/dashboard/api/notifications/check/?since=' + encodeURIComponent(lastSince.current));
        const data = await res.json();
        if (data.notifications && data.notifications.length > 0) {
          lastSince.current = new Date().toISOString();
          refetch();
        }
        if (data.unread_count !== undefined) setUnreadCount(data.unread_count);
      } catch {}
    }, 15000);
    return () => clearInterval(interval);
  }, [refetch]);

  const list = Array.isArray(notifs) ? notifs : [];

  const markAllRead = () => {
    apiPost('/dashboard/api/notifications/read-all/', {}).then(() => refetch()).catch(() => {});
  };

  const markRead = (id) => {
    apiPost('/dashboard/api/notifications/' + id + '/read/', {}).then(() => refetch()).catch(() => {});
  };

  return (
    <header className="header">
      <div>
        <div className="hd-title" data-screen-label={`${view}`}>{meta.t}</div>
        <div className="hd-sub">{meta.s}</div>
      </div>
      <div className="hd-right">
        <div className="search">
          <I.search size={16}/>
          <input placeholder="Rechercher membres, cours, paiements…"/>
          <kbd>⌘K</kbd>
        </div>
        <div ref={ref} style={{ position: 'relative' }}>
          <button className="icon-btn" onClick={() => setNotif(v => !v)}>
            <I.bell size={18}/>
            {unreadCount > 0 && <span className="dot"></span>}
          </button>
          {notif && (
            <div className="pop">
              <div className="pop-head">
                <span>Notifications</span>
                <button className="btn sm ghost" onClick={markAllRead}>Tout marquer lu</button>
              </div>
              <div className="pop-list">
                {notifLoading ? (
                  <div className="pop-item" style={{ justifyContent: 'center', color: 'var(--muted)' }}>Chargement...</div>
                ) : list.length === 0 ? (
                  <div className="pop-item" style={{ justifyContent: 'center', color: 'var(--muted)' }}>Aucune notification</div>
                ) : list.map(n => (
                  <div key={n.id} className={`pop-item ${n.is_read ? 'read' : ''}`} onClick={() => !n.is_read && markRead(n.id)} style={{ cursor: !n.is_read ? 'pointer' : 'default' }}>
                    <div className="pop-dot" style={{ opacity: n.is_read ? 0 : 1 }}/>
                    <div style={{ flex: 1 }}>
                      <div className="pop-msg">{n.message}</div>
                      <div className="pop-time">{fmtDateTime(n.created_at)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="stack" style={{ gap: 8, padding: '4px 10px 4px 4px', border: '1px solid var(--border)', borderRadius: 10, cursor: 'pointer' }}>
          <div className="avatar sm">PJ</div>
          <div style={{ lineHeight: 1.2 }}>
            <div style={{ fontSize: 12.5, fontWeight: 600 }}>Pasteur Joseph</div>
            <div style={{ fontSize: 11, color: 'var(--muted)' }}>admin@imso.ht</div>
          </div>
          <I.chevron size={14} style={{ color: 'var(--muted)' }}/>
        </div>
      </div>
    </header>
  );
}

function PlaceholderView({ view }) {
  const t = TITLES[view] || {};
  return (
    <div className="content">
      <div className="card fade-in d1" style={{ padding: 48, textAlign: 'center' }}>
        <div style={{
          width: 56, height: 56, borderRadius: 14,
          background: 'var(--primary-light)', color: 'var(--primary)',
          display: 'grid', placeItems: 'center', margin: '0 auto 16px'
        }}>
          {view === 'payments' && <I.cash size={26}/>}
          {view === 'ai' && <I.ai size={26}/>}
          {view === 'stats' && <I.chart size={26}/>}
          {view === 'settings' && <I.settings size={26}/>}
        </div>
        <div style={{ fontSize: 18, fontWeight: 600, letterSpacing: '-0.015em' }}>{t.t}</div>
        <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 6, maxWidth: 420, margin: '6px auto 0' }}>
          Cette section est connectée au backend mais n'a pas encore d'écran de démo dans ce prototype.
          Naviguez vers <b>Tableau de bord</b>, <b>Membres</b> ou <b>Cours & Contenu</b> pour voir l'expérience complète.
        </div>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState('dashboard');
  return (
    <div className="app">
      <Sidebar view={view} onNav={setView}/>
      <div className="main">
        <Header view={view}/>
        <div key={view}>
          {view === 'dashboard' && <Dashboard/>}
          {view === 'members' && <Members/>}
          {view === 'courses' && <Courses/>}
          {view === 'room' && <Room/>}
          {view === 'payments' && <Payments/>}
          {view === 'contacts' && <window.Contacts/>}
          {view === 'geis' && <window.Geis/>}
          {view === 'providers' && <window.Providers/>}
          {view === 'ai' && <AgentIA/>}
          {view === 'stats' && <Stats/>}
          {view === 'settings' && <Settings/>}
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
