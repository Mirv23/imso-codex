function Sidebar({ view, onNav }) {
  const items = [
    { id: 'dashboard', label: 'Tableau de bord', icon: I.dashboard },
    { id: 'members', label: 'Membres', icon: I.users, badge: '1.2k' },
    { id: 'courses', label: 'Cours & Contenu', icon: I.book, badge: '24' },
    { id: 'room', label: 'Salle & Réservations', icon: I.building, badge: 'NEW' },
    { id: 'payments', label: 'Paiements', icon: I.cash, badge: '6' },
    { id: 'contacts', label: 'Messages', icon: I.mail, badge: '?' },
    { id: 'geis', label: 'GEI', icon: I.pin },
    { id: 'providers', label: 'Moyens de paiement', icon: I.shieldCheck, badge: 'NEW' },
    { id: 'ai', label: 'Agents IA', icon: I.ai, badge: '2' },
    { id: 'stats', label: 'Statistiques', icon: I.chart },
    { id: 'settings', label: 'Paramètres', icon: I.settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sb-top">
        <div className="sb-brand">
          <div className="sb-logo">IM</div>
          <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
            <div>
              <div className="sb-name">IMSO Haïti</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 1 }}>v2.4.1 · Production</div>
            </div>
            <span className="sb-tag" style={{ marginLeft: 'auto' }}>Admin</span>
          </div>
        </div>
      </div>

      <div className="sb-user">
        <div className="avatar">PJ</div>
        <div className="sb-user-meta" style={{ flex: 1, minWidth: 0 }}>
          <div className="sb-user-name truncate">Pasteur Joseph</div>
          <div className="sb-user-role">Super-administrateur</div>
        </div>
        <div className="ico" style={{ color: 'var(--muted)' }}><I.chevron size={14}/></div>
      </div>

      <div className="sb-section">Espace de travail</div>
      <nav className="sb-nav">
        {items.map(it => (
          <div
            key={it.id}
            className={`sb-item ${view === it.id ? 'active' : ''}`}
            onClick={() => onNav(it.id)}
          >
            <span className="ico"><it.icon/></span>
            <span style={{ flex: 1 }}>{it.label}</span>
            {it.badge && <span className="badge">{it.badge}</span>}
          </div>
        ))}
      </nav>

      <div className="sb-bottom">
        <div className="sb-item danger" onClick={() => alert('Déconnexion (démo)')}>
          <span className="ico"><I.logout/></span>
          <span>Déconnexion</span>
        </div>
      </div>
    </aside>
  );
}

window.Sidebar = Sidebar;
