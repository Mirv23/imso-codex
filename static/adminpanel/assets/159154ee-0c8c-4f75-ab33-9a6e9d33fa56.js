/* ===== Payments View ===== */

/* Logo with graceful fallback (initial letter inside a colored circle) */
function MethodLogo({ provider, method, size = 28, square = false }) {
  const prov = provider || method;
  if (!prov) return null;
  const [failed, setFailed] = useState(false);
  const isCash = prov.id === 'cash' || !prov.logo || failed;
  return (
    <div style={{
      width: size, height: size,
      borderRadius: square ? Math.round(size/4) : 999,
      background: isCash ? prov.color : '#fff',
      color: isCash ? '#fff' : prov.color,
      display: 'grid', placeItems: 'center',
      fontWeight: 800, fontSize: Math.round(size * 0.42),
      letterSpacing: '0.02em',
      flexShrink: 0,
      border: isCash ? 'none' : '1px solid var(--border-soft)',
      overflow: 'hidden',
      padding: isCash ? 0 : 3,
    }}>
      {isCash
        ? (prov.id === 'cash' ? <I.cash size={Math.round(size * 0.55)}/> : prov.name.slice(0, 2).toUpperCase())
        : <img src={prov.logo} alt={prov.name} onError={() => setFailed(true)} style={{ width:'100%', height:'100%', objectFit:'contain' }}/>
      }
    </div>
  );
}

function PaymentKPIs({ transactions }) {
  const txns = Array.isArray(transactions) ? transactions : [];
  const totalRevenu = txns.filter(t => t.status === 'Réussi' || t.status === 'Confirmé').reduce((s, t) => s + (t.amount_htg || 0), 0);
  const success = txns.filter(t => t.status === 'Réussi' || t.status === 'Confirmé').length;
  const fail = txns.filter(t => t.status === 'Échoué').length;
  const rate = txns.length ? Math.round((success / txns.length) * 100) : 0;

  return (
    <div className="metric-grid">
      <div className="metric fade-in d1">
        <div className="metric-ico green"><I.cash size={20}/></div>
        <div className="metric-label">Revenus encaissés</div>
        <div className="metric-value num">{fmtNum(totalRevenu)}</div>
        <div className="metric-foot">
          <span className="pill green"><I.trend size={11} stroke={2.5}/> Base de données</span>
          <Sparkline data={[4,8,12,16,20,24,28,32].map(v => Math.round(totalRevenu * v/100))} color="#10B981"/>
        </div>
      </div>
      <div className="metric fade-in d2">
        <div className="metric-ico blue"><I.fileText size={20}/></div>
        <div className="metric-label">Transactions</div>
        <div className="metric-value num">{fmtNum(txns.length)}</div>
        <div className="metric-foot">
          <span className="pill green"><I.trend size={11} stroke={2.5}/> Total</span>
          <Sparkline data={[10,20,30,40,50,60,70,80,90,100].slice(0, Math.min(txns.length, 10))} color="#3B82F6"/>
        </div>
      </div>
      <div className="metric fade-in d3">
        <div className="metric-ico violet"><I.check size={20}/></div>
        <div className="metric-label">Taux de réussite</div>
        <div className="metric-value num">{rate}<span style={{ fontSize:18, color:'var(--muted)', fontWeight:500 }}>%</span></div>
        <div className="metric-foot">
          <span className="pill amber dot">{fail} échec(s)</span>
        </div>
      </div>
      <div className="metric fade-in d4">
        <div className="metric-ico orange"><I.trend size={20}/></div>
        <div className="metric-label">Volume total (HTG)</div>
        <div className="metric-value num">{fmtNum(totalRevenu)}</div>
        <div className="metric-foot">
          <span className="pill gray">Toutes transactions</span>
          <Sparkline data={[5,10,15,20,25,30,35,40].map(v => Math.round(totalRevenu * v/100))} color="#F4A261"/>
        </div>
      </div>
    </div>
  );
}

function MethodBreakdown({ methods, active, onSelect }) {
  const list = Array.isArray(methods) ? methods : [];
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
        {list.map(m => {
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
                <MethodLogo provider={m} size={44} square/>
                <div style={{ minWidth:0, flex:1 }}>
                  <div style={{ fontSize:14, fontWeight:700, letterSpacing:'-0.01em' }}>{m.name}</div>
                  <div style={{ fontSize:11.5, color:'var(--muted)', marginTop:1 }} className="truncate">{m.sub || ''}</div>
                </div>
                <div style={{
                  fontSize: 10, fontWeight: 700,
                  color: m.color,
                  background: `${m.color}1a`,
                  padding: '3px 7px',
                  borderRadius: 999,
                  letterSpacing: '0.04em',
                }}>FRAIS {m.fee || '—'}</div>
              </div>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize:18, fontWeight:800, letterSpacing:'-0.02em' }} className="num">
                    {m.share || 0}<span style={{ fontSize:13, color:'var(--muted)', fontWeight:500 }}>%</span>
                  </div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>du volume</div>
                </div>
                <div style={{ textAlign:'right' }}>
                  <div style={{ fontSize:14, fontWeight:700 }} className="num">{m.txns || 0}</div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>transactions</div>
                </div>
              </div>
              <div style={{ height: 6, background:'#F3F4F6', borderRadius:999, overflow:'hidden' }}>
                <div style={{
                  height:'100%',
                  width: `${Math.min((m.share || 0) * 2.5, 100)}%`,
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
  if (!data || data.length < 2) return <div ref={wrapRef} style={{ padding:'4px 22px 18px', color:'var(--muted)', textAlign:'center', fontSize:13 }}>Données insuffisantes pour le graphique</div>;
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
        {data.map((_, i) => {
          if (i % Math.ceil(data.length / 6) !== 0 && i !== 0 && i !== data.length - 1) return null;
          return <text key={i} x={pad.l + i * step} y={h - 10} fontSize="10.5" fill="#6B7280" textAnchor="middle">{data[i].l || ''}</text>;
        })}
        <path d={area} fill="url(#payArea)"/>
        <path d={path} fill="none" stroke="#2D6A4F" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx={pts.at(-1).x} cy={pts.at(-1).y} r="5" fill="#fff" stroke="#2D6A4F" strokeWidth="2.5"/>
      </svg>
    </div>
  );
}

function TransactionsTable({ filter, onRow, transactions, providers }) {
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('');
  const pmMap = Object.fromEntries((providers || []).map(m => [m.id, m]));

  const rows = (transactions || []).filter(t => {
    const tProvider = typeof t.provider === 'object' && t.provider ? t.provider.id || t.provider.name : t.provider__name || '';
    if (filter && tProvider !== filter && tProvider !== pmMap[filter]?.name) return false;
    if (status && t.status !== status) return false;
    const search = `${t.payer_name||''} ${t.reference||''} ${t.purpose||''}`.toLowerCase();
    if (q && !search.includes(q.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="card fade-in d6" style={{ marginTop: 18 }}>
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Transactions</div>
          <div className="card-sub">{rows.length} transaction(s) · {filter ? 'Filtré' : 'Tous les opérateurs'}</div>
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
              <option>Réussi</option><option>Confirmé</option><option>En attente</option><option>Échoué</option><option>Remboursé</option>
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
            const providerName = typeof t.provider === 'object' && t.provider ? t.provider.name||t.provider.id : t.provider__name || '';
            const provider = Object.values(pmMap).find(p => p.name === providerName || p.id === providerName);
            return (
              <tr key={t.id} style={{ animationDelay: `${0.03 * i}s`, cursor:'pointer' }} onClick={() => onRow(t)}>
                <td>
                  <div className="mono" style={{ fontSize:12, fontWeight:600 }}>{t.reference || t.id}</div>
                  <div style={{ fontSize:11, color:'var(--muted)' }}>{fmtDateTime(t.created_at)}</div>
                </td>
                <td>
                  <div style={{ fontWeight:600 }}>{t.payer_name}</div>
                  <div style={{ fontSize:11.5, color:'var(--muted)' }}>{t.purpose || ''}</div>
                </td>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <MethodLogo provider={provider} size={28} square/>
                    <div style={{ minWidth:0 }}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{providerName}</div>
                      <div style={{ fontSize:11, color:'var(--muted)' }}>{t.entry_mode || ''}</div>
                    </div>
                  </div>
                </td>
                <td className="num mono" style={{ textAlign:'right', fontWeight:700 }}>
                  {fmtNum(t.amount_htg)} <span style={{ color:'var(--muted)', fontWeight:500, fontSize:11 }}>HTG</span>
                </td>
                <td className="num mono" style={{ textAlign:'right', color:'var(--muted)' }}>
                  {t.fee ? fmtNum(t.fee) : '—'}
                </td>
                <td>
                  <span className={`pill dot ${
                    t.status === 'Réussi' || t.status === 'Confirmé' ? 'green' :
                    t.status === 'En attente' ? 'amber' :
                    t.status === 'Échoué' ? 'red' : 'violet'
                  }`}>{t.status}</span>
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
        <div className="pager-info">Affichage <b>1</b>–<b>{rows.length}</b> sur <b>{transactions ? transactions.length : 0}</b> transactions</div>
        <div className="pager-nav">
          <button className="pager-btn" disabled><I.chevronL size={14}/></button>
          <button className="pager-btn active">1</button>
        </div>
      </div>
    </div>
  );
}

function TxDetail({ tx, onClose, providers }) {
  if (!tx) return null;
  const providerName = typeof tx.provider === 'object' && tx.provider ? tx.provider.name||tx.provider.id : tx.provider__name || '';
  const pmMap = Object.fromEntries((providers || []).map(m => [m.id, m]));
  const provider = Object.values(pmMap).find(p => p.name === providerName || p.id === providerName) || { id:providerName, name:providerName, color:'#6B7280' };
  return (
    <div className="modal-overlay open" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 480 }}>
        <div style={{ padding:'22px 24px', background: `linear-gradient(135deg, ${provider.color}18, ${provider.color}08)`, borderRadius:'16px 16px 0 0' }}>
          <div style={{ display:'flex', alignItems:'center', gap:14 }}>
            <MethodLogo provider={provider} size={48} square/>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontSize:11, fontWeight:700, color: provider.color, letterSpacing:'0.06em' }}>{providerName.toUpperCase()}</div>
              <div className="mono" style={{ fontSize:15, fontWeight:700, marginTop:1 }}>{tx.reference || tx.id}</div>
              <div style={{ fontSize:11.5, color:'var(--muted)' }}>{fmtDateTime(tx.created_at)}</div>
            </div>
            <button className="icon-btn" onClick={onClose}><I.close size={18}/></button>
          </div>
        </div>
        <div className="modal-body" style={{ paddingTop:18 }}>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Client</div>
              <div style={{ fontSize:14, fontWeight:600, marginTop:3 }}>{tx.payer_name}</div>
              <div style={{ fontSize:11.5, color:'var(--muted)', marginTop:1 }}>{tx.payer_email || ''}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Motif</div>
              <div style={{ fontSize:13, marginTop:3 }}>{tx.purpose || ''}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Référence</div>
              <div className="mono" style={{ fontSize:12.5, marginTop:3 }}>{tx.reference}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Canal</div>
              <div style={{ fontSize:13, marginTop:3 }}>{tx.entry_mode || ''}</div>
            </div>
          </div>
          <div style={{
            marginTop:18, padding:14,
            background:'var(--primary-light)', borderRadius:10,
          }}>
            <div style={{ display:'flex', justifyContent:'space-between', fontSize:13, marginBottom:6 }}>
              <span style={{ color:'var(--muted)' }}>Montant</span>
              <span className="num mono" style={{ fontWeight:600 }}>{fmtNum(tx.amount_htg)} HTG</span>
            </div>
            <div style={{ display:'flex', justifyContent:'space-between', paddingTop:8, borderTop:'1px solid rgba(45,106,79,0.2)' }}>
              <span style={{ fontWeight:600 }}>Statut</span>
              <span className={`pill dot ${tx.status === 'Réussi' || tx.status === 'Confirmé' ? 'green' : tx.status === 'En attente' ? 'amber' : 'red'}`}>{tx.status}</span>
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
  const { data: payments, loading, error, refetch } = useAPI('/dashboard/api/payments/');
  const { data: providers } = useAPI('/dashboard/api/providers/');
  const [filter, setFilter] = useState(null);
  const [tx, setTx] = useState(null);

  const transactions = Array.isArray(payments) ? payments : [];
  const payMethods = Array.isArray(providers) ? providers : [];

  // Compute daily revenue for chart (last 30 days)
  const revenue30 = (() => {
    const days = {};
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0,10);
      days[key] = { l: String(d.getDate()), v: 0 };
    }
    transactions.forEach(t => {
      if (!t.created_at) return;
      const key = t.created_at.slice(0,10);
      if (days[key]) days[key].v += (t.amount_htg || 0);
    });
    return Object.values(days);
  })();

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
      <PaymentKPIs transactions={transactions}/>

      <div style={{ display:'grid', gridTemplateColumns:'1.5fr 1fr', gap:18, marginTop:18 }}>
        <div className="card fade-in d5">
          <div className="card-head">
            <div>
              <div className="card-title">Revenus quotidiens (30 jours)</div>
              <div className="card-sub">Tous opérateurs confondus</div>
            </div>
            <div className="stack">
              <span className="pill green dot">Base de données</span>
              <button className="btn sm">30j <I.chevron size={12}/></button>
            </div>
          </div>
          <RevenueArea data={revenue30}/>
        </div>

        <div className="card fade-in d5">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Réconciliation</div>
              <div className="card-sub">Soldes par opérateur</div>
            </div>
            <button className="btn sm primary"><I.download size={14}/> Tout virer</button>
          </div>
          <div style={{ padding:'8px 18px 18px' }}>
            {payMethods.map(m => {
              const txCount = transactions.filter(t => {
                const pn = typeof t.provider === 'object' && t.provider ? t.provider.name||t.provider.id : t.provider__name || '';
                return pn === m.name || pn === m.id;
              }).length;
              const total = transactions.filter(t => {
                const pn = typeof t.provider === 'object' && t.provider ? t.provider.name||t.provider.id : t.provider__name || '';
                return (pn === m.name || pn === m.id) && (t.status === 'Réussi' || t.status === 'Confirmé');
              }).reduce((s, t) => s + (t.amount_htg || 0), 0);
              return (
                <div key={m.id} style={{
                  display:'flex', alignItems:'center', gap:12,
                  padding:'12px 0',
                  borderBottom:'1px solid var(--border-soft)',
                }}>
                  <MethodLogo provider={m} size={32} square/>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontSize:13, fontWeight:600 }}>{m.name}</div>
                    <div style={{ fontSize:11, color:'var(--muted)' }}>{txCount} transactions</div>
                  </div>
                  <div style={{ textAlign:'right' }}>
                    <div className="num mono" style={{ fontSize:14, fontWeight:700 }}>{fmtNum(total)} <span style={{ color:'var(--muted)', fontSize:11, fontWeight:500 }}>HTG</span></div>
                    <div style={{ fontSize:10.5, color: m.color, fontWeight:600 }}>EN ATTENTE</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <MethodBreakdown methods={payMethods} active={filter} onSelect={setFilter}/>
      <TransactionsTable filter={filter} onRow={setTx} transactions={transactions} providers={payMethods}/>
      {tx && <TxDetail tx={tx} onClose={() => setTx(null)} providers={payMethods}/>}
    </div>
  );
}

window.Payments = Payments;
