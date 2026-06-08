/* ===== Payments View ===== */

const PAY_METHODS = [
  { id:'moncash',    name:'MonCash',     sub:'Digicel · Mobile money',          logo:'logos/moncash.webp',     color:'#E5202C', text:'#E5202C', share:38, fee:'2.0%', txns:412 },
  { id:'natcash',    name:'NatCash',     sub:'Natcom · Mobile money',           logo:'logos/natcash.png',      color:'#F39322', text:'#F39322', share:18, fee:'1.8%', txns:198 },
  { id:'sogebank',   name:'Sogebank',    sub:'Virement bancaire · Sogexpress',  logo:'logos/sogebank.png',     color:'#1849A9', text:'#1849A9', share:14, fee:'1.5%', txns:154 },
  { id:'unibank',    name:'Unibank',     sub:'Virement bancaire · UniTransfert', logo:'logos/unibank.png',     color:'#0E4A9E', text:'#0E4A9E', share:11, fee:'1.5%', txns:121 },
  { id:'capitalbank',name:'Capital Bank',sub:'Virement bancaire · CapitalConnect', logo:'logos/capitalbank.png', color:'#E2231A', text:'#E2231A', share:9,  fee:'1.5%', txns:99  },
  { id:'cash',       name:'Cash',        sub:'Espèces · Sur place IMSO',        logo:null,                     color:'#2D6A4F', text:'#2D6A4F', share:10, fee:'0%',   txns:108 },
];

const PM = Object.fromEntries(PAY_METHODS.map(m => [m.id, m]));

const TRANSACTIONS = [
  { id:'TX-208411', ref:'imso_inv_4421', date:'21 mai 2026 · 14:32', client:'Marie-Claude Joseph', item:'Théologie pratique I',         method:'moncash',     amount:7500,  fee:150,  status:'Réussi',     channel:'App mobile' },
  { id:'TX-208410', ref:'imso_inv_4420', date:'21 mai 2026 · 13:18', client:'Jean-Robert Pierre',  item:'Leadership chrétien',          method:'sogebank',    amount:12000, fee:180,  status:'Réussi',     channel:'Virement' },
  { id:'TX-208409', ref:'imso_inv_4419', date:'21 mai 2026 · 11:47', client:'Wilkenson Auguste',   item:'Salle · 4h (mariage)',          method:'moncash',     amount:15000, fee:300,  status:'Réussi',     channel:'Réception' },
  { id:'TX-208408', ref:'imso_inv_4418', date:'21 mai 2026 · 10:22', client:'Roselène Bélizaire',  item:'Étude de Romains',              method:'natcash',     amount:9000,  fee:162,  status:'En attente', channel:'App mobile' },
  { id:'TX-208407', ref:'imso_inv_4417', date:'21 mai 2026 · 09:05', client:'Frantz Cadet',        item:'Théologie pratique I',         method:'capitalbank', amount:7500,  fee:113,  status:'Réussi',     channel:'Virement' },
  { id:'TX-208406', ref:'imso_inv_4416', date:'20 mai 2026 · 18:42', client:'Patrick Théodore',    item:'Discipulat',                    method:'unibank',     amount:6500,  fee:98,   status:'Réussi',     channel:'Virement' },
  { id:'TX-208405', ref:'imso_inv_4415', date:'20 mai 2026 · 17:11', client:'Carline Estimé',      item:'Salle · 3h (séminaire)',        method:'cash',        amount:11250, fee:0,    status:'Réussi',     channel:'Caisse' },
  { id:'TX-208404', ref:'imso_inv_4414', date:'20 mai 2026 · 15:48', client:'Yvon Gabriel',        item:'Évangélisation moderne',       method:'moncash',     amount:5500,  fee:110,  status:'Échoué',     channel:'App mobile', failReason:'Solde insuffisant' },
  { id:'TX-208403', ref:'imso_inv_4413', date:'20 mai 2026 · 14:30', client:'Sophonie Vincent',    item:'Leadership chrétien',          method:'sogebank',    amount:12000, fee:180,  status:'Réussi',     channel:'Virement' },
  { id:'TX-208402', ref:'imso_inv_4412', date:'20 mai 2026 · 13:05', client:'Marlène Charles',     item:'Théologie pratique I',         method:'natcash',     amount:7500,  fee:135,  status:'Remboursé', channel:'App mobile' },
  { id:'TX-208401', ref:'imso_inv_4411', date:'20 mai 2026 · 11:54', client:'Daniel Pétion',       item:'Salle · 6h (conférence)',       method:'capitalbank', amount:22500, fee:338,  status:'Réussi',     channel:'Virement' },
  { id:'TX-208400', ref:'imso_inv_4410', date:'20 mai 2026 · 10:21', client:'Berthony Lamour',     item:'Apologétique',                  method:'moncash',     amount:8500,  fee:170,  status:'Réussi',     channel:'App mobile' },
];

const REVENUE_30 = [
  18, 22, 19, 24, 28, 31, 26,
  29, 33, 35, 30, 38, 41, 39,
  42, 45, 48, 44, 51, 54, 49,
  56, 62, 58, 65, 71, 68, 74, 78, 82,
].map((v, i) => ({ day: i + 1, v: v * 1000 }));

/* Logo with graceful fallback (initial letter inside a colored circle) */
function MethodLogo({ method, size = 28, square = false }) {
  const m = typeof method === 'string' ? PM[method] : method;
  if (!m) return null;
  const [failed, setFailed] = useState(false);

  if (m.id === 'cash' || !m.logo || failed) {
    return (
      <div style={{
        width: size, height: size,
        borderRadius: square ? Math.round(size/4) : 999,
        background: m.color, color: '#fff',
        display: 'grid', placeItems: 'center',
        fontWeight: 800, fontSize: Math.round(size * 0.42),
        letterSpacing: '0.02em',
        flexShrink: 0,
      }}>
        {m.id === 'cash' ? <I.cash size={Math.round(size * 0.55)}/> : m.name.slice(0, 2).toUpperCase()}
      </div>
    );
  }
  return (
    <div style={{
      width: size, height: size,
      borderRadius: square ? Math.round(size/4) : 999,
      background: '#fff',
      border: '1px solid var(--border-soft)',
      display: 'grid', placeItems: 'center',
      flexShrink: 0,
      overflow: 'hidden',
      padding: 3,
    }}>
      <img
        src={m.logo}
        alt={m.name}
        onError={() => setFailed(true)}
        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
      />
    </div>
  );
}

function PaymentKPIs() {
  const total = TRANSACTIONS.filter(t => t.status === 'Réussi').reduce((s, t) => s + t.amount, 0);
  const fees = TRANSACTIONS.filter(t => t.status === 'Réussi').reduce((s, t) => s + t.fee, 0);
  const success = TRANSACTIONS.filter(t => t.status === 'Réussi').length;
  const fail = TRANSACTIONS.filter(t => t.status === 'Échoué').length;
  const rate = Math.round((success / TRANSACTIONS.length) * 100);

  return (
    <div className="metric-grid">
      <div className="metric fade-in d1">
        <div className="metric-ico green"><I.cash size={20}/></div>
        <div className="metric-label">Revenus encaissés (30j)</div>
        <div className="metric-value num">{fmtNum(1247500)}</div>
        <div className="metric-foot">
          <span className="pill green"><I.trend size={11} stroke={2.5}/> +24.3%</span>
          <Sparkline data={REVENUE_30.slice(-12).map(d => d.v)} color="#10B981"/>
        </div>
      </div>
      <div className="metric fade-in d2">
        <div className="metric-ico blue"><I.fileText size={20}/></div>
        <div className="metric-label">Transactions (30j)</div>
        <div className="metric-value num">{fmtNum(1092)}</div>
        <div className="metric-foot">
          <span className="pill green"><I.trend size={11} stroke={2.5}/> +18%</span>
          <Sparkline data={[64,72,78,82,89,94,101,108]} color="#3B82F6"/>
        </div>
      </div>
      <div className="metric fade-in d3">
        <div className="metric-ico violet"><I.check size={20}/></div>
        <div className="metric-label">Taux de réussite</div>
        <div className="metric-value num">{rate}<span style={{ fontSize:18, color:'var(--muted)', fontWeight:500 }}>%</span></div>
        <div className="metric-foot">
          <span className="pill amber dot">{fail} échec(s) à analyser</span>
        </div>
      </div>
      <div className="metric fade-in d4">
        <div className="metric-ico orange"><I.trend size={20}/></div>
        <div className="metric-label">Frais opérateurs</div>
        <div className="metric-value num">{fmtNum(22480)}</div>
        <div className="metric-foot">
          <span className="pill gray">≈ 1.8% du volume</span>
          <Sparkline data={[10,12,14,15,18,20,21,22]} color="#F4A261"/>
        </div>
      </div>
    </div>
  );
}

function MethodBreakdown({ active, onSelect }) {
  return (
    <div className="card fade-in d5" style={{ marginTop: 18 }}>
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Moyens de paiement locaux</div>
          <div className="card-sub">Tous les paiements traités via opérateurs haïtiens · Cliquez pour filtrer la table</div>
        </div>
        <div className="stack">
          <button className={`btn sm ${!active ? '' : 'ghost'}`} onClick={() => onSelect(null)}>Tous</button>
          <button className="btn sm"><I.settings size={14}/> Configurer</button>
        </div>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap: 14, padding: 18 }}>
        {PAY_METHODS.map(m => {
          const isSel = active === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onSelect(isSel ? null : m.id)}
              style={{
                background: isSel ? '#fff' : '#FAFBFC',
                border: isSel ? `1.5px solid ${m.color}` : '1.5px solid var(--border-soft)',
                borderRadius: 14,
                padding: '16px 16px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all .18s',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {isSel && (
                <div style={{
                  position:'absolute', top:0, right:0,
                  background: m.color, color:'#fff',
                  fontSize: 10, fontWeight:700, letterSpacing:'0.06em',
                  padding:'3px 9px',
                  borderRadius:'0 12px 0 10px',
                }}>ACTIF</div>
              )}
              <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom: 14 }}>
                <MethodLogo method={m} size={44} square/>
                <div style={{ minWidth:0, flex:1 }}>
                  <div style={{ fontSize:14, fontWeight:700, letterSpacing:'-0.01em' }}>{m.name}</div>
                  <div style={{ fontSize:11.5, color:'var(--muted)', marginTop:1 }} className="truncate">{m.sub}</div>
                </div>
                <div style={{
                  fontSize: 10, fontWeight: 700,
                  color: m.color,
                  background: `${m.color}1a`,
                  padding: '3px 7px',
                  borderRadius: 999,
                  letterSpacing: '0.04em',
                }}>FRAIS {m.fee}</div>
              </div>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize:18, fontWeight:800, letterSpacing:'-0.02em' }} className="num">
                    {m.share}<span style={{ fontSize:13, color:'var(--muted)', fontWeight:500 }}>%</span>
                  </div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>du volume</div>
                </div>
                <div style={{ textAlign:'right' }}>
                  <div style={{ fontSize:14, fontWeight:700 }} className="num">{m.txns}</div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>transactions</div>
                </div>
              </div>
              <div style={{ height: 6, background:'#F3F4F6', borderRadius:999, overflow:'hidden' }}>
                <div style={{
                  height:'100%',
                  width: `${m.share * 2.5}%`,
                  maxWidth: '100%',
                  background: m.color,
                  borderRadius: 999,
                  transition: 'width 1.1s cubic-bezier(.2,.7,.2,1)',
                }}/>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function RevenueArea({ data }) {
  const wrapRef = useRef(null);
  const [size, setSize] = useState({ w: 600, h: 240 });
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: 240 }));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);
  const w = size.w, h = size.h;
  const pad = { t: 16, r: 16, b: 30, l: 50 };
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const max = Math.max(...data.map(d => d.v)) * 1.1;
  const step = innerW / (data.length - 1);

  const pts = data.map((d, i) => ({ x: pad.l + i * step, y: pad.t + innerH - (d.v / max) * innerH, ...d }));
  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
  const area = `${path} L${pts.at(-1).x},${pad.t + innerH} L${pts[0].x},${pad.t + innerH} Z`;
  const ticks = 4;
  return (
    <div ref={wrapRef} style={{ padding:'4px 22px 18px' }}>
      <svg width={w} height={h}>
        <defs>
          <linearGradient id="payArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2D6A4F" stopOpacity="0.20"/>
            <stop offset="100%" stopColor="#2D6A4F" stopOpacity="0"/>
          </linearGradient>
        </defs>
        {Array.from({ length: ticks + 1 }, (_, i) => {
          const v = (max * i) / ticks;
          const y = pad.t + innerH - (v / max) * innerH;
          return (
            <g key={i}>
              <line x1={pad.l} x2={w - pad.r} y1={y} y2={y} stroke="#EEF0F3" strokeDasharray={i === 0 ? '0' : '4 4'}/>
              <text x={pad.l - 8} y={y + 4} fontSize="10.5" fill="#9CA3AF" textAnchor="end">{Math.round(v/1000)}k</text>
            </g>
          );
        })}
        {[0, 7, 14, 21, 29].map(i => (
          <text key={i} x={pad.l + i * step} y={h - 10} fontSize="10.5" fill="#6B7280" textAnchor="middle">J-{29 - i}</text>
        ))}
        <path d={area} fill="url(#payArea)"/>
        <path d={path} fill="none" stroke="#2D6A4F" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx={pts.at(-1).x} cy={pts.at(-1).y} r="5" fill="#fff" stroke="#2D6A4F" strokeWidth="2.5"/>
      </svg>
    </div>
  );
}

function TransactionsTable({ filter, onRow }) {
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const rows = TRANSACTIONS.filter(t => {
    if (filter && t.method !== filter) return false;
    if (status && t.status !== status) return false;
    if (q && !(`${t.client} ${t.id} ${t.item}`.toLowerCase().includes(q.toLowerCase()))) return false;
    return true;
  });

  return (
    <div className="card fade-in d6" style={{ marginTop: 18 }}>
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Transactions</div>
          <div className="card-sub">{rows.length} transaction(s) · Filtré par {filter ? PM[filter].name : 'tous les opérateurs'}</div>
        </div>
        <div className="stack">
          <div className="search" style={{ width: 240 }}>
            <I.search size={16}/>
            <input placeholder="Rechercher TX, client, cours…" value={q} onChange={e => setQ(e.target.value)}/>
          </div>
          <div className="chip-select">
            <I.filter size={13}/> {status || 'Tous statuts'} <I.chevron size={12}/>
            <select value={status} onChange={e => setStatus(e.target.value)}>
              <option value="">Tous statuts</option>
              <option>Réussi</option><option>En attente</option><option>Échoué</option><option>Remboursé</option>
            </select>
          </div>
          <button className="btn sm"><I.download size={14}/> CSV</button>
        </div>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Transaction</th>
            <th>Client & article</th>
            <th>Opérateur</th>
            <th style={{ textAlign:'right' }}>Montant</th>
            <th style={{ textAlign:'right' }}>Frais</th>
            <th>Statut</th>
            <th style={{ textAlign:'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody className="row-anim">
          {rows.length === 0 ? (
            <tr><td colSpan="7" className="empty">Aucune transaction ne correspond.</td></tr>
          ) : rows.map((t, i) => {
            const m = PM[t.method];
            return (
              <tr key={t.id} style={{ animationDelay: `${0.03 * i}s`, cursor:'pointer' }} onClick={() => onRow(t)}>
                <td>
                  <div className="mono" style={{ fontSize:12, fontWeight:600 }}>{t.id}</div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>{t.date}</div>
                </td>
                <td>
                  <div style={{ fontWeight:600 }}>{t.client}</div>
                  <div style={{ fontSize:11.5, color:'var(--muted)' }}>{t.item}</div>
                </td>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <MethodLogo method={m} size={28} square/>
                    <div style={{ minWidth:0 }}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{m.name}</div>
                      <div style={{ fontSize:11, color:'var(--muted)' }}>{t.channel}</div>
                    </div>
                  </div>
                </td>
                <td className="num mono" style={{ textAlign:'right', fontWeight:700 }}>
                  {fmtNum(t.amount)} <span style={{ color:'var(--muted)', fontWeight:500, fontSize:11 }}>HTG</span>
                </td>
                <td className="num mono" style={{ textAlign:'right', color:'var(--muted)' }}>
                  {t.fee ? fmtNum(t.fee) : '—'}
                </td>
                <td>
                  <span className={`pill dot ${
                    t.status === 'Réussi' ? 'green' :
                    t.status === 'En attente' ? 'amber' :
                    t.status === 'Échoué' ? 'red' : 'violet'
                  }`}>{t.status}</span>
                  {t.failReason && <div style={{ fontSize:10.5, color:'var(--danger)', marginTop:2 }}>{t.failReason}</div>}
                </td>
                <td style={{ textAlign:'right' }} onClick={e => e.stopPropagation()}>
                  <div className="stack" style={{ justifyContent:'flex-end' }}>
                    <button className="btn sm ghost"><I.eye size={14}/></button>
                    <button className="btn sm ghost"><I.download size={14}/></button>
                    <button className="btn sm ghost"><I.more size={14}/></button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="pager">
        <div className="pager-info">Affichage <b>1</b>–<b>{rows.length}</b> sur <b>1 092</b> transactions du mois</div>
        <div className="pager-nav">
          <button className="pager-btn" disabled><I.chevronL size={14}/></button>
          <button className="pager-btn active">1</button>
          <button className="pager-btn">2</button>
          <button className="pager-btn">3</button>
          <button className="pager-btn">…</button>
          <button className="pager-btn">91</button>
          <button className="pager-btn"><I.chevronR size={14}/></button>
        </div>
      </div>
    </div>
  );
}

function TxDetail({ tx, onClose }) {
  if (!tx) return null;
  const m = PM[tx.method];
  return (
    <div className="modal-overlay open" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 480 }}>
        <div style={{ padding:'22px 24px', background: `linear-gradient(135deg, ${m.color}18, ${m.color}08)`, borderRadius:'16px 16px 0 0' }}>
          <div style={{ display:'flex', alignItems:'center', gap:14 }}>
            <MethodLogo method={m} size={48} square/>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontSize:11, fontWeight:700, color: m.color, letterSpacing:'0.06em' }}>{m.name.toUpperCase()}</div>
              <div className="mono" style={{ fontSize:15, fontWeight:700, marginTop:1 }}>{tx.id}</div>
              <div style={{ fontSize:11.5, color:'var(--muted)' }}>{tx.date}</div>
            </div>
            <button className="icon-btn" onClick={onClose}><I.close size={18}/></button>
          </div>
        </div>
        <div className="modal-body" style={{ paddingTop:18 }}>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Client</div>
              <div style={{ fontSize:14, fontWeight:600, marginTop:3 }}>{tx.client}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Article</div>
              <div style={{ fontSize:13, marginTop:3 }}>{tx.item}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Référence</div>
              <div className="mono" style={{ fontSize:12.5, marginTop:3 }}>{tx.ref}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Canal</div>
              <div style={{ fontSize:13, marginTop:3 }}>{tx.channel}</div>
            </div>
          </div>
          <div style={{
            marginTop:18, padding:14,
            background:'var(--primary-light)', borderRadius:10,
          }}>
            <div style={{ display:'flex', justifyContent:'space-between', fontSize:13, marginBottom:6 }}>
              <span style={{ color:'var(--muted)' }}>Brut</span>
              <span className="num mono" style={{ fontWeight:600 }}>{fmtNum(tx.amount)} HTG</span>
            </div>
            <div style={{ display:'flex', justifyContent:'space-between', fontSize:13, marginBottom:6 }}>
              <span style={{ color:'var(--muted)' }}>Frais {m.fee}</span>
              <span className="num mono" style={{ color:'var(--danger)' }}>− {fmtNum(tx.fee)} HTG</span>
            </div>
            <div style={{ display:'flex', justifyContent:'space-between', paddingTop:8, borderTop:'1px solid rgba(45,106,79,0.2)' }}>
              <span style={{ fontWeight:600 }}>Net encaissé</span>
              <span className="num mono" style={{ fontWeight:800, color:'var(--primary)', fontSize:16 }}>{fmtNum(tx.amount - tx.fee)} HTG</span>
            </div>
          </div>
        </div>
        <div className="modal-foot">
          <button className="btn"><I.download size={14}/> Reçu PDF</button>
          {tx.status === 'Réussi' && <button className="btn"><I.ban size={14}/> Rembourser</button>}
          <button className="btn primary"><I.mail size={14}/> Renvoyer au client</button>
        </div>
      </div>
    </div>
  );
}

function Payments() {
  const [filter, setFilter] = useState(null);
  const [tx, setTx] = useState(null);

  return (
    <div className="content">
      <PaymentKPIs/>

      <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:18, marginTop:18 }}>
        <div className="card fade-in d5">
          <div className="card-head">
            <div>
              <div className="card-title">Revenus quotidiens (30 jours)</div>
              <div className="card-sub">Tous opérateurs confondus · Net après frais</div>
            </div>
            <div className="stack">
              <span className="pill green dot">+24.3%</span>
              <button className="btn sm">30j <I.chevron size={12}/></button>
            </div>
          </div>
          <RevenueArea data={REVENUE_30}/>
        </div>

        <div className="card fade-in d5">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Réconciliation</div>
              <div className="card-sub">Soldes à virer · Mardi 21 mai</div>
            </div>
            <button className="btn sm primary"><I.download size={14}/> Tout virer</button>
          </div>
          <div style={{ padding:'8px 18px 18px' }}>
            {PAY_METHODS.map(m => (
              <div key={m.id} style={{
                display:'flex', alignItems:'center', gap:12,
                padding:'12px 0',
                borderBottom:'1px solid var(--border-soft)',
              }}>
                <MethodLogo method={m} size={32} square/>
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ fontSize:13, fontWeight:600 }}>{m.name}</div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>{m.txns} transactions ce mois</div>
                </div>
                <div style={{ textAlign:'right' }}>
                  <div className="num mono" style={{ fontSize:14, fontWeight:700 }}>{fmtNum(Math.round(m.share * 12000))} <span style={{ color:'var(--muted)', fontSize:11, fontWeight:500 }}>HTG</span></div>
                  <div style={{ fontSize:10.5, color: m.color, fontWeight:600 }}>EN ATTENTE</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <MethodBreakdown active={filter} onSelect={setFilter}/>
      <TransactionsTable filter={filter} onRow={setTx}/>
      {tx && <TxDetail tx={tx} onClose={() => setTx(null)}/>}
    </div>
  );
}

window.Payments = Payments;
