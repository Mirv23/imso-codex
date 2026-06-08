function CourseCard({ c, i, onToggle }) {
  const ico = c.category === 'Théologie' ? <I.book size={28}/> :
              c.category === 'Bible' ? <I.fileText size={28}/> :
              c.category === 'Leadership' ? <I.spark size={28}/> :
              c.category === 'Ministère' ? <I.users size={28}/> :
              c.category === 'Évangélisation' ? <I.mail size={28}/> :
              <I.ai size={28}/>;
  const revenue = (c.enrollments_count || 0) * (c.price_htg || 0);
  return (
    <div className="course-card fade-in" style={{ animationDelay: `${0.04 * i}s` }}>
      <div className="course-thumb green">
        <span className="ttag">{c.category}</span>
        <span className="duration">{c.instructor || ''}</span>
        <div style={{ position: 'relative', zIndex: 1, opacity: 0.88 }}>
          {ico}
        </div>
      </div>
      <div className="course-body">
        <div className="course-title">{c.title}</div>
        <div className="course-meta-row">
          <div className="m"><I.users size={14}/> <b>{fmtNum(c.enrollments_count || 0)}</b> inscrits</div>
          <div className="m"><I.cash size={14}/> <b>{fmtNum(revenue)}</b> HTG</div>
        </div>
        <div className="course-foot">
          <label className="toggle">
            <input type="checkbox" checked={c.is_active} onChange={() => onToggle(c)}/>
            <span className="track"></span>
            <span className="lbl" style={{ color: c.is_active ? 'var(--primary)' : 'var(--muted)', fontWeight: 600 }}>
              {c.is_active ? 'Publié' : 'Brouillon'}
            </span>
          </label>
          <button className="btn sm ghost"><I.more size={16}/></button>
        </div>
      </div>
    </div>
  );
}

function CourseDrawer({ open, onClose }) {
  const [drag, setDrag] = useState(false);
  const [aiSum, setAiSum] = useState(true);
  const [aiPdf, setAiPdf] = useState(true);
  return (
    <React.Fragment>
      <div className={`drawer-overlay ${open ? 'open' : ''}`} onClick={onClose}/>
      <div className={`drawer ${open ? 'open' : ''}`}>
        <div className="drawer-head">
          <div>
            <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.015em' }}>Nouveau cours</div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>Créer un cours et programmer sa publication</div>
          </div>
          <button className="icon-btn" onClick={onClose}><I.close size={18}/></button>
        </div>
        <div className="drawer-body">
          <div className="field">
            <label>Titre du cours</label>
            <input className="input" placeholder="ex: Le ministère pastoral aujourd'hui" defaultValue=""/>
          </div>
          <div className="field">
            <label>Description</label>
            <textarea className="textarea" placeholder="Décrivez les objectifs pédagogiques, les modules abordés et le public visé…"></textarea>
            <div className="hint">L'IA enrichira automatiquement la description si laissée vide.</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="field">
              <label>Prix</label>
              <div className="input-prefix">
                <span className="pre">HTG</span>
                <input className="input num" placeholder="7 500" defaultValue=""/>
              </div>
            </div>
            <div className="field">
              <label>Catégorie</label>
              <select className="select">
                <option>Théologie</option>
                <option>Bible</option>
                <option>Leadership</option>
                <option>Ministère</option>
                <option>Évangélisation</option>
                <option>Apologétique</option>
              </select>
            </div>
          </div>

          <div className="field">
            <label>Contenu du cours</label>
            <div
              className={`dropzone ${drag ? 'drag' : ''}`}
              onDragOver={e => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={e => { e.preventDefault(); setDrag(false); alert('Fichier accepté (démo)'); }}
            >
              <div className="dropzone-ico"><I.upload size={20}/></div>
              <div className="dropzone-title">Glissez vos fichiers ici</div>
              <div className="dropzone-sub">Audio MP3 / WAV — Vidéo MP4 / MOV · max 2 Go</div>
            </div>
          </div>

          <div className="field">
            <label style={{ marginBottom: 8 }}>Génération IA</label>
            <div className="toggle-row">
              <div className="meta">
                <div className="t">Générer un résumé IA</div>
                <div className="s">Résumé écrit + bullet points par module, généré après transcription.</div>
              </div>
              <label className="toggle">
                <input type="checkbox" checked={aiSum} onChange={() => setAiSum(v => !v)}/>
                <span className="track"></span>
              </label>
            </div>
            <div className="toggle-row">
              <div className="meta">
                <div className="t">Générer un ebook PDF</div>
                <div className="s">Format A4, illustré, prêt à téléverser dans la bibliothèque membre.</div>
              </div>
              <label className="toggle">
                <input type="checkbox" checked={aiPdf} onChange={() => setAiPdf(v => !v)}/>
                <span className="track"></span>
              </label>
            </div>
          </div>
        </div>
        <div className="drawer-foot">
          <button className="btn" onClick={onClose}>Enregistrer en brouillon</button>
          <button className="btn primary" onClick={() => { alert('Cours publié (démo)'); onClose(); }}>
            <I.check size={14}/> Publier
          </button>
        </div>
      </div>
    </React.Fragment>
  );
}

function Courses() {
  const { data: courses, loading, error, refetch } = useAPI('/dashboard/api/courses/');
  const [open, setOpen] = useState(false);
  const list = Array.isArray(courses) ? courses : [];

  const toggle = (c) => {
    apiPut('/dashboard/api/courses/' + c.id + '/', { is_active: !c.is_active })
      .then(() => refetch())
      .catch(() => alert('Erreur lors de la mise à jour'));
  };

  const totalRevenue = list.reduce((s, c) => s + (c.enrollments_count || 0) * (c.price_htg || 0), 0);
  const totalStudents = list.reduce((s, c) => s + (c.enrollments_count || 0), 0);

  if (loading) return <div className="content"><div className="loading" style={{ padding: 48, textAlign: 'center', color: 'var(--muted)' }}>Chargement...</div></div>;
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
      <div className="between fade-in d1" style={{ marginBottom: 8 }}>
        <div className="stack" style={{ gap: 20 }}>
          <div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Total inscrits</div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }} className="num">{fmtNum(totalStudents)}</div>
          </div>
          <div style={{ width: 1, height: 32, background: 'var(--border)' }}/>
          <div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Revenus totaux</div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }} className="num">{fmtNum(totalRevenue)} HTG</div>
          </div>
          <div style={{ width: 1, height: 32, background: 'var(--border)' }}/>
          <div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Publiés</div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }} className="num">
              {list.filter(c => c.is_active).length}<span style={{ color: 'var(--muted)', fontWeight: 500 }}>/{list.length}</span>
            </div>
          </div>
        </div>
        <div className="stack">
          <div className="search" style={{ width: 240 }}>
            <I.search size={16}/>
            <input placeholder="Rechercher un cours…"/>
          </div>
          <button className="btn"><I.filter size={14}/> Filtrer</button>
          <button className="btn primary" onClick={() => setOpen(true)}>
            <I.plus size={14} stroke={2.5}/> Nouveau cours
          </button>
        </div>
      </div>

      <div className="course-grid">
        {list.map((c, i) => <CourseCard key={c.id} c={c} i={i} onToggle={toggle}/>)}
      </div>

      <CourseDrawer open={open} onClose={() => setOpen(false)}/>
    </div>
  );
}

window.Courses = Courses;
