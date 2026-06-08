/* ===== AI Agents View ===== */

const AGENTS = [
  {
    id: 'content',
    name: 'Agent Créateur de Contenu',
    role: 'Génération de posts pour les réseaux sociaux',
    color: '#2D6A4F',
    model: 'Claude Haiku 4.5',
    status: 'Actif',
    icon: 'spark',
    metrics: [
      { l: 'Posts publiés (30j)', v: '186' },
      { l: 'Portée totale', v: '42.8k' },
      { l: 'Taux d\'engagement', v: '4.8%' },
      { l: 'Économie de temps', v: '38h' },
    ],
  },
  {
    id: 'leads',
    name: 'Agent Qualificateur de Leads',
    role: 'Qualifie les leads venant des publicités',
    color: '#F4A261',
    model: 'Claude Haiku 4.5',
    status: 'Actif',
    icon: 'ai',
    metrics: [
      { l: 'Leads qualifiés (30j)', v: '412' },
      { l: 'Taux de conversion', v: '18.4%' },
      { l: 'Leads chauds', v: '74' },
      { l: 'Temps de réponse', v: '< 90s' },
    ],
  },
];

/* ============ Content Agent data ============ */
const CONTENT_QUEUE = [
  { id:1, time:'aujourd\'hui · 18:00', status:'À publier',  platforms:['fb','ig','wa'], topic:'Témoignage GEI Cap-Haïtien', length:'court' },
  { id:2, time:'aujourd\'hui · 20:30', status:'À valider',  platforms:['fb','ig'],      topic:'Annonce séminaire leadership', length:'moyen' },
  { id:3, time:'demain · 08:00',       status:'À publier',  platforms:['fb'],            topic:'Verset du jour + réflexion',   length:'court' },
  { id:4, time:'demain · 12:30',       status:'Brouillon',  platforms:['ig','wa'],      topic:'Recette du nouveau cours Romains', length:'long' },
  { id:5, time:'jeu 23 mai · 19:00',   status:'À publier',  platforms:['fb','ig','wa'], topic:'Histoire de Marie-Claude (témoignage)', length:'moyen' },
];

const RECENT_POSTS = [
  {
    id:1, time:'il y a 2h', platforms:['fb','ig','wa'],
    text:'Le discipulat n\'est pas un programme, c\'est une marche. Aujourd\'hui, IMSO Haïti accompagne 1 247 frères et sœurs sur ce chemin — et notre nouveau module sur Romains ouvre demain. 🇭🇹',
    reach: '12.4k', engagement: '4.8%', comments: 187, likes: 894, status: 'Publié',
  },
  {
    id:2, time:'il y a 8h', platforms:['fb','ig'],
    text:'Saviez-vous ? 73% des Haïtiens qui rejoignent un GEI réussissent à constituer une épargne en moins de 6 mois. Découvrez notre formation gratuite cette semaine.',
    reach: '8.2k', engagement: '5.2%', comments: 94, likes: 612, status: 'Publié',
  },
  {
    id:3, time:'hier', platforms:['fb','wa'],
    text:'Mariage, conférence, séminaire — notre salle de 60 places est disponible toute la semaine prochaine. Réservez en quelques clics, à partir de 3 750 HTG/h.',
    reach: '6.1k', engagement: '6.1%', comments: 53, likes: 421, status: 'Publié',
  },
];

const PLATFORM = {
  fb: { name:'Facebook',  bg:'#1877F2', letter:'f' },
  ig: { name:'Instagram', bg:'linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045)', letter:'IG' },
  wa: { name:'WhatsApp',  bg:'#25D366', letter:'W' },
  tk: { name:'TikTok',    bg:'#000', letter:'tk' },
};

/* ============ Leads Agent data ============ */
const LEADS = [
  { id:1, name:'Patrick Lamothe',     phone:'+509 3811 4527', source:'Facebook Ads · "Discipulat 2026"', score:92, status:'Chaud',  intent:'Inscription cours', tags:['Pasteur','PAP'],     time:'il y a 4 min', summary:'Pasteur de 38 ans à PAP, dirige une église de 120 membres. Très intéressé par la formation Discipulat, prêt à payer cette semaine.' },
  { id:2, name:'Nadège Auguste',      phone:'+509 4220 7733', source:'Instagram Ads · "Finances"',       score:78, status:'Chaud',  intent:'Inscription cours', tags:['Famille','CAP'],     time:'il y a 12 min', summary:'Mère de famille, cherche à mieux gérer son épargne. A demandé le prix du module "Finances personnelles".' },
  { id:3, name:'Wilkenson Joseph',    phone:'+509 3699 1284', source:'Google Ads · "salle réception"',   score:88, status:'Chaud',  intent:'Réserver salle',   tags:['Mariage','LGN'],     time:'il y a 22 min', summary:'Cherche une salle pour mariage de 70 personnes en juin. Budget OK, attend une visite virtuelle.' },
  { id:4, name:'Stéphanie Désir',     phone:'+509 3404 5566', source:'TikTok Ads · "Leadership"',        score:64, status:'Tiède',  intent:'En réflexion',     tags:['Étudiante','PAP'],   time:'il y a 1h', summary:'Étudiante, hésite encore. A demandé un échantillon gratuit du module Leadership.' },
  { id:5, name:'Frantz Cadet',        phone:'+509 3722 9911', source:'Facebook Ads · "Cours gratuits"',  score:58, status:'Tiède',  intent:'En réflexion',     tags:['Entrepreneur','GON'], time:'il y a 2h', summary:'Entrepreneur agricole, intéressé mais sans budget immédiat. Sera relancé dans 2 semaines.' },
  { id:6, name:'Roselène Bélizaire',  phone:'+509 4811 3322', source:'Instagram Ads · "GEI"',            score:36, status:'Froid',  intent:'Info générale',    tags:['Curieuse'],          time:'il y a 4h', summary:'Curiosité générale sur les GEI. Pas de projet concret pour le moment.' },
  { id:7, name:'Daniel Pétion',       phone:'+509 4567 1212', source:'Facebook Ads · "Salle conférence"', score:81, status:'Chaud',  intent:'Réserver salle',   tags:['Pro','CYS'],         time:'il y a 5h', summary:'Cabinet de consulting, cherche salle pour séminaire trimestriel (40 pers, avec tables). Engagement fort.' },
  { id:8, name:'Sophonie Vincent',    phone:'+509 4123 6677', source:'Google Ads · "formation pastorale"', score:71, status:'Tiède', intent:'Inscription cours', tags:['Pastoral','CAP'],   time:'hier', summary:'Veut comparer les options de formation pastorale avant de s\'engager.' },
];

function PlatformDots({ platforms, size = 22 }) {
  return (
    <div style={{ display:'flex', gap:-4, marginRight:0 }}>
      {platforms.map((p, i) => (
        <div key={p} style={{
          width: size, height: size, borderRadius: 6,
          background: PLATFORM[p].bg,
          color: '#fff',
          display:'grid', placeItems:'center',
          fontSize: 10, fontWeight: 700,
          border: '1.5px solid #fff',
          marginLeft: i > 0 ? -6 : 0,
          zIndex: platforms.length - i,
        }}>{PLATFORM[p].letter}</div>
      ))}
    </div>
  );
}

function AgentCard({ a, active, onClick }) {
  const isActive = active === a.id;
  return (
    <button
      onClick={onClick}
      style={{
        background: isActive ? '#fff' : '#FAFBFC',
        border: isActive ? `1.5px solid ${a.color}` : '1.5px solid var(--border-soft)',
        borderRadius: 16,
        padding: 20,
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'all .2s',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {isActive && (
        <div style={{
          position:'absolute', top:0, right:0,
          background: a.color, color:'#fff',
          fontSize:10, fontWeight:700, letterSpacing:'0.08em',
          padding:'4px 10px',
          borderRadius:'0 14px 0 12px',
        }}>SÉLECTIONNÉ</div>
      )}
      <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:14 }}>
        <div style={{
          width:48, height:48, borderRadius:12,
          background: `linear-gradient(135deg, ${a.color}, ${a.color}cc)`,
          color:'#fff', display:'grid', placeItems:'center',
          boxShadow:`0 6px 14px -4px ${a.color}55`,
        }}>
          {I[a.icon] ? I[a.icon]({ size:22 }) : <I.ai size={22}/>}
        </div>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ display:'flex', alignItems:'center', gap:6 }}>
            <div style={{ fontSize:15, fontWeight:700, letterSpacing:'-0.01em' }}>{a.name}</div>
            <span className="pill green dot" style={{ fontSize:10 }}>{a.status}</span>
          </div>
          <div style={{ fontSize:12, color:'var(--muted)', marginTop:2 }}>{a.role}</div>
          <div style={{ fontSize:10.5, color:'var(--muted)', marginTop:3, fontFamily:'JetBrains Mono, monospace' }}>{a.model}</div>
        </div>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:10, paddingTop:14, borderTop:'1px solid var(--border-soft)' }}>
        {a.metrics.map((m, i) => (
          <div key={i}>
            <div style={{ fontSize:17, fontWeight:700, letterSpacing:'-0.015em' }} className="num">{m.v}</div>
            <div style={{ fontSize:10.5, color:'var(--muted)', marginTop:1 }}>{m.l}</div>
          </div>
        ))}
      </div>
    </button>
  );
}

/* ============ Content Agent UI ============ */
function ContentAgentView() {
  const [tone, setTone] = useState('Pastoral chaleureux');
  const [auto, setAuto] = useState(true);
  const [validate, setValidate] = useState(true);
  return (
    <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:18, marginTop:18 }}>
      {/* Recent posts */}
      <div className="card fade-in d5">
        <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
          <div>
            <div className="card-title">Publications récentes</div>
            <div className="card-sub">Posts générés et publiés par l'agent · 30 derniers jours</div>
          </div>
          <div className="stack">
            <span className="pill green dot">Agent actif</span>
            <button className="btn sm primary"><I.plus size={14} stroke={2.5}/> Générer un post</button>
          </div>
        </div>
        <div style={{ padding:'12px 22px 18px', display:'flex', flexDirection:'column', gap:12 }}>
          {RECENT_POSTS.map(p => (
            <div key={p.id} style={{
              padding:16,
              background:'#FAFBFC',
              border:'1px solid var(--border-soft)',
              borderRadius: 14,
            }}>
              <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:10 }}>
                <PlatformDots platforms={p.platforms}/>
                <span style={{ fontSize:11.5, color:'var(--muted)' }}>{p.time}</span>
                <span className="pill green" style={{ marginLeft:'auto' }}>{p.status}</span>
              </div>
              <div style={{ fontSize:13.5, lineHeight:1.55, color:'var(--text)', marginBottom:12 }}>{p.text}</div>
              <div style={{
                display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:0,
                paddingTop:12, borderTop:'1px solid var(--border)',
                fontSize:11.5,
              }}>
                <div>
                  <div style={{ color:'var(--muted)' }}>Portée</div>
                  <div className="num" style={{ fontWeight:700, fontSize:14 }}>{p.reach}</div>
                </div>
                <div>
                  <div style={{ color:'var(--muted)' }}>Engagement</div>
                  <div className="num" style={{ fontWeight:700, fontSize:14, color:'var(--primary)' }}>{p.engagement}</div>
                </div>
                <div>
                  <div style={{ color:'var(--muted)' }}>J'aime</div>
                  <div className="num" style={{ fontWeight:700, fontSize:14 }}>{fmtNum(p.likes)}</div>
                </div>
                <div>
                  <div style={{ color:'var(--muted)' }}>Commentaires</div>
                  <div className="num" style={{ fontWeight:700, fontSize:14 }}>{p.comments}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right column */}
      <div style={{ display:'flex', flexDirection:'column', gap:18 }}>
        {/* Queue */}
        <div className="card fade-in d5">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">File de publication</div>
              <div className="card-sub">{CONTENT_QUEUE.length} posts programmés</div>
            </div>
            <button className="btn sm ghost"><I.calendar size={14}/></button>
          </div>
          <div style={{ padding:'4px 6px' }}>
            {CONTENT_QUEUE.map(q => (
              <div key={q.id} style={{
                padding:'10px 14px',
                borderBottom:'1px solid var(--border-soft)',
                display:'flex', alignItems:'center', gap:10,
              }}>
                <div style={{
                  width:32, height:32, borderRadius:8,
                  background: q.status === 'Brouillon' ? '#F3F4F6' : q.status === 'À valider' ? '#FEF3C7' : 'var(--primary-light)',
                  color: q.status === 'Brouillon' ? 'var(--muted)' : q.status === 'À valider' ? '#92400E' : 'var(--primary)',
                  display:'grid', placeItems:'center', flexShrink:0,
                }}>{q.status === 'Brouillon' ? <I.fileText size={14}/> : q.status === 'À valider' ? <I.eye size={14}/> : <I.calendar size={14}/>}</div>
                <div style={{ minWidth:0, flex:1 }}>
                  <div style={{ fontSize:12.5, fontWeight:600 }} className="truncate">{q.topic}</div>
                  <div style={{ fontSize:11, color:'var(--muted)', marginTop:1 }}>{q.time}</div>
                </div>
                <PlatformDots platforms={q.platforms} size={18}/>
              </div>
            ))}
          </div>
          <div style={{ padding:'10px 14px', borderTop:'1px solid var(--border-soft)', textAlign:'center' }}>
            <button className="btn sm ghost" style={{ width:'100%' }}>Voir le calendrier complet <I.arrow size={12}/></button>
          </div>
        </div>

        {/* Config */}
        <div className="card fade-in d6">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Configuration</div>
              <div className="card-sub">Paramètres de l'agent</div>
            </div>
          </div>
          <div style={{ padding:18 }}>
            <div className="field">
              <label>Ton éditorial</label>
              <select className="select" value={tone} onChange={e => setTone(e.target.value)}>
                <option>Pastoral chaleureux</option>
                <option>Inspirant & motivant</option>
                <option>Pédagogique & clair</option>
                <option>Informel & jeune</option>
              </select>
            </div>
            <div className="field">
              <label>Fréquence</label>
              <select className="select" defaultValue="3-par-jour">
                <option value="1-par-jour">1 post par jour</option>
                <option value="3-par-jour">3 posts par jour</option>
                <option value="5-par-jour">5 posts par jour</option>
              </select>
            </div>
            <div className="toggle-row">
              <div className="meta">
                <div className="t">Publication automatique</div>
                <div className="s">L'agent publie sans validation manuelle</div>
              </div>
              <label className="toggle">
                <input type="checkbox" checked={auto} onChange={() => setAuto(v => !v)}/>
                <span className="track"></span>
              </label>
            </div>
            <div className="toggle-row">
              <div className="meta">
                <div className="t">Validation humaine pour les témoignages</div>
                <div className="s">Posts citant un membre passent par toi</div>
              </div>
              <label className="toggle">
                <input type="checkbox" checked={validate} onChange={() => setValidate(v => !v)}/>
                <span className="track"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============ Leads Agent UI ============ */
function LeadsAgentView() {
  const [filter, setFilter] = useState('Tous');
  const counts = {
    'Tous': LEADS.length,
    'Chaud': LEADS.filter(l => l.status === 'Chaud').length,
    'Tiède': LEADS.filter(l => l.status === 'Tiède').length,
    'Froid': LEADS.filter(l => l.status === 'Froid').length,
  };
  const filtered = filter === 'Tous' ? LEADS : LEADS.filter(l => l.status === filter);
  const sourceCounts = {};
  LEADS.forEach(l => {
    const platform = l.source.split(' · ')[0];
    sourceCounts[platform] = (sourceCounts[platform] || 0) + 1;
  });

  return (
    <div style={{ marginTop:18 }}>
      {/* Funnel + sources */}
      <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:18 }}>
        <div className="card fade-in d5">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Pipeline de qualification</div>
              <div className="card-sub">Tous les leads des publicités, qualifiés en temps réel</div>
            </div>
            <div className="stack">
              <span className="pill green dot">Agent actif</span>
              <span style={{ fontSize:12, color:'var(--muted)' }} className="mono">Dernière conv. il y a 4 min</span>
            </div>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', padding:0 }}>
            {[
              { l:'Leads reçus',   v:412, color:'#6B7280', sub:'depuis les ads' },
              { l:'Engagés',       v:298, color:'#3B82F6', sub:'ont répondu à l\'agent' },
              { l:'Qualifiés',     v:174, color:'#F4A261', sub:'profil + intention OK' },
              { l:'Convertis',     v:76,  color:'#2D6A4F', sub:'paiement effectué' },
            ].map((s, i, arr) => (
              <div key={i} style={{
                padding:'20px 18px',
                borderRight: i < arr.length - 1 ? '1px solid var(--border-soft)' : 0,
                position:'relative',
              }}>
                <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>{s.l}</div>
                <div style={{ fontSize:26, fontWeight:800, letterSpacing:'-0.02em', marginTop:4, color: s.color }} className="num">{s.v}</div>
                <div style={{ fontSize:11.5, color:'var(--muted)', marginTop:2 }}>{s.sub}</div>
                {i < arr.length - 1 && (
                  <div style={{ position:'absolute', right:-10, top:'50%', transform:'translateY(-50%)', zIndex:2 }}>
                    <div style={{
                      width:20, height:20, borderRadius:999,
                      background:'#fff', border:'1px solid var(--border-soft)',
                      display:'grid', placeItems:'center', color:'var(--muted)',
                    }}><I.chevronR size={12}/></div>
                  </div>
                )}
                {i < arr.length - 1 && (
                  <div style={{
                    position:'absolute', bottom:14, left:18, right:18,
                    height:4, background:'#F3F4F6', borderRadius:999, overflow:'hidden',
                  }}>
                    <div style={{
                      height:'100%',
                      width: `${(arr[i+1].v / s.v) * 100}%`,
                      background: s.color,
                      transition:'width 1.1s cubic-bezier(.2,.7,.2,1)',
                    }}/>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="card fade-in d5">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Sources des leads</div>
              <div className="card-sub">Plateformes publicitaires</div>
            </div>
          </div>
          <div style={{ padding:'12px 18px 18px', display:'flex', flexDirection:'column', gap:12 }}>
            {[
              { p:'Facebook Ads',  v:184, color:'#1877F2', emoji:'f' },
              { p:'Instagram Ads', v:108, color:'#E1306C', emoji:'IG' },
              { p:'Google Ads',    v:78,  color:'#4285F4', emoji:'G' },
              { p:'TikTok Ads',    v:42,  color:'#000000', emoji:'tk' },
            ].map(s => (
              <div key={s.p}>
                <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:5 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <div style={{
                      width:24, height:24, borderRadius:6,
                      background: s.color, color:'#fff',
                      display:'grid', placeItems:'center', fontSize:10, fontWeight:700,
                    }}>{s.emoji}</div>
                    <span style={{ fontSize:13, fontWeight:500 }}>{s.p}</span>
                  </div>
                  <span className="num" style={{ fontSize:13, fontWeight:700 }}>{s.v}</span>
                </div>
                <div style={{ height:5, background:'#F3F4F6', borderRadius:999, overflow:'hidden' }}>
                  <div style={{ height:'100%', width: `${(s.v / 412) * 100}%`, background:s.color, borderRadius:999, transition:'width 1s' }}/>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Leads table */}
      <div className="card fade-in d6" style={{ marginTop:18 }}>
        <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
          <div>
            <div className="card-title">Leads qualifiés</div>
            <div className="card-sub">{filtered.length} lead(s) · Triés par score décroissant · Conversations gérées par l'agent</div>
          </div>
          <div className="stack">
            {['Tous','Chaud','Tiède','Froid'].map(t => (
              <button
                key={t}
                onClick={() => setFilter(t)}
                className={`btn sm ${filter === t ? '' : 'ghost'}`}
                style={filter === t ? {
                  background: t === 'Chaud' ? '#EF4444' : t === 'Tiède' ? '#F59E0B' : t === 'Froid' ? '#3B82F6' : 'var(--primary)',
                  color: '#fff', borderColor: 'transparent',
                } : {}}
              >{t} <span style={{ marginLeft:5, opacity:.8, fontSize:11 }}>{counts[t]}</span></button>
            ))}
          </div>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Lead</th>
              <th>Source publicitaire</th>
              <th>Intention détectée</th>
              <th>Score IA</th>
              <th>Statut</th>
              <th style={{ textAlign:'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody className="row-anim">
            {filtered.sort((a, b) => b.score - a.score).map((l, i) => (
              <tr key={l.id} style={{ animationDelay: `${0.03 * i}s` }}>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <div style={{
                      width:34, height:34, borderRadius:999,
                      background:'linear-gradient(135deg, var(--primary), #3a8862)',
                      color:'#fff', display:'grid', placeItems:'center',
                      fontWeight:700, fontSize:12,
                    }}>{l.name.split(' ').map(w => w[0]).slice(0, 2).join('')}</div>
                    <div style={{ minWidth:0 }}>
                      <div style={{ fontWeight:600 }}>{l.name}</div>
                      <div style={{ fontSize:11.5, color:'var(--muted)' }} className="mono">{l.phone}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div style={{ fontSize:12.5 }}>{l.source.split(' · ')[0]}</div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>{l.source.split(' · ')[1]}</div>
                </td>
                <td>
                  <div style={{ fontSize:13, fontWeight:500 }}>{l.intent}</div>
                  <div style={{ display:'flex', gap:4, marginTop:4 }}>
                    {l.tags.map(t => <span key={t} className="pill gray" style={{ fontSize:10 }}>{t}</span>)}
                  </div>
                </td>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <div style={{
                      fontSize:14, fontWeight:800, letterSpacing:'-0.01em',
                      color: l.score >= 80 ? '#EF4444' : l.score >= 60 ? '#F59E0B' : '#6B7280',
                    }} className="num">{l.score}</div>
                    <div style={{ width:70, height:6, background:'#F3F4F6', borderRadius:999, overflow:'hidden' }}>
                      <div style={{
                        height:'100%',
                        width: `${l.score}%`,
                        background: l.score >= 80 ? '#EF4444' : l.score >= 60 ? '#F59E0B' : '#6B7280',
                        transition:'width 1.1s cubic-bezier(.2,.7,.2,1)',
                      }}/>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`pill dot ${l.status === 'Chaud' ? 'red' : l.status === 'Tiède' ? 'amber' : 'blue'}`}>{l.status}</span>
                  <div style={{ fontSize:10.5, color:'var(--muted)', marginTop:3 }}>{l.time}</div>
                </td>
                <td style={{ textAlign:'right' }}>
                  <div className="stack" style={{ justifyContent:'flex-end' }}>
                    <button className="btn sm">Voir conv.</button>
                    <button className="btn sm ghost"><I.mail size={14}/></button>
                    <button className="btn sm primary"><I.check size={14}/> Convertir</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Agent settings */}
      <div className="card fade-in d7" style={{ marginTop:18 }}>
        <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
          <div>
            <div className="card-title">Critères de qualification</div>
            <div className="card-sub">Comment l'agent évalue chaque lead · Sur 100 points</div>
          </div>
          <button className="btn sm">Ajuster les pondérations</button>
        </div>
        <div style={{ padding:18, display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:14 }}>
          {[
            { l:'Budget exprimé',         w:30, color:'#2D6A4F' },
            { l:'Urgence du besoin',      w:25, color:'#F4A261' },
            { l:'Adéquation à l\'offre',  w:25, color:'#3B82F6' },
            { l:'Engagement conversationnel', w:20, color:'#8B5CF6' },
          ].map((c, i) => (
            <div key={i} style={{
              padding:16,
              background:'#FAFBFC', borderRadius:12,
              border:'1px solid var(--border-soft)',
            }}>
              <div style={{ fontSize:11.5, color:'var(--muted)', fontWeight:600, textTransform:'uppercase', letterSpacing:'0.04em' }}>Pondération</div>
              <div style={{ fontSize:22, fontWeight:800, letterSpacing:'-0.02em', color:c.color, marginTop:4 }} className="num">{c.w}%</div>
              <div style={{ fontSize:13, marginTop:6 }}>{c.l}</div>
              <div style={{ height:4, background:'#F3F4F6', borderRadius:999, marginTop:10, overflow:'hidden' }}>
                <div style={{ height:'100%', width:`${c.w * 3}%`, maxWidth:'100%', background:c.color, borderRadius:999 }}/>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AgentIA() {
  const [active, setActive] = useState('content');
  return (
    <div className="content">
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:18 }}>
        {AGENTS.map(a => (
          <AgentCard key={a.id} a={a} active={active} onClick={() => setActive(a.id)}/>
        ))}
      </div>

      {active === 'content' && <ContentAgentView/>}
      {active === 'leads' && <LeadsAgentView/>}
    </div>
  );
}

window.AgentIA = AgentIA;
