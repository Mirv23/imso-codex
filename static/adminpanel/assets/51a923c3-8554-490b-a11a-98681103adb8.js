/* ===== Statistics View ===== */

const STAT_REVENUE_12M = [
  { m:'Juin 25',  v: 285000 }, { m:'Juil 25', v: 312000 },
  { m:'Août 25',  v: 298000 }, { m:'Sept 25', v: 345000 },
  { m:'Oct 25',   v: 412000 }, { m:'Nov 25',  v: 485000 },
  { m:'Déc 25',   v: 528000 }, { m:'Jan 26',  v: 601000 },
  { m:'Fév 26',   v: 723000 }, { m:'Mar 26',  v: 847500 },
  { m:'Avr 26',   v: 1085000 }, { m:'Mai 26',  v: 1247500 },
];

const STAT_MEMBERS_12M = [
  { m:'Juin 25', v: 412 }, { m:'Juil 25', v: 478 },
  { m:'Août 25', v: 545 }, { m:'Sept 25', v: 612 },
  { m:'Oct 25',  v: 698 }, { m:'Nov 25',  v: 784 },
  { m:'Déc 25',  v: 856 }, { m:'Jan 26',  v: 942 },
  { m:'Fév 26',  v: 1024 }, { m:'Mar 26', v: 1108 },
  { m:'Avr 26',  v: 1182 }, { m:'Mai 26', v: 1247 },
];

const GEI_DISTRIBUTION = [
  { gei:'PAP', name:'Port-au-Prince', count: 482, color:'#2D6A4F', pct: 38 },
  { gei:'CAP', name:'Cap-Haïtien',    count: 218, color:'#F4A261', pct: 18 },
  { gei:'JAC', name:'Jacmel',         count: 156, color:'#3B82F6', pct: 12 },
  { gei:'LGN', name:'Léogâne',        count: 134, color:'#8B5CF6', pct: 11 },
  { gei:'GON', name:'Gonaïves',       count: 112, color:'#EC4899', pct: 9  },
  { gei:'CYS', name:'Côtes-de-fer',   count: 89,  color:'#14B8A6', pct: 7  },
  { gei:'PDS', name:'Petit-Goâve',    count: 56,  color:'#EF4444', pct: 5  },
];

const TOP_COURSES_STATS = [
  { title:'Théologie pratique — Module I',          students:142, rating:4.9, revenue:1065000 },
  { title:'Évangélisation à l\'ère numérique',       students:201, rating:4.7, revenue:1105500 },
  { title:'Leadership chrétien et gestion d\'équipe', students:89,  rating:4.9, revenue:1068000 },
  { title:'Le ministère du discipulat',              students:124, rating:4.8, revenue:806000  },
  { title:'Étude approfondie de Romains',            students:67,  rating:4.8, revenue:603000  },
];

const COHORT_DATA = [
  // last 6 cohorts, retention week-by-week
  { cohort:'Déc',  size: 86,  weeks:[100, 92, 84, 78, 72, 68, 65, 62] },
  { cohort:'Jan',  size: 94,  weeks:[100, 90, 81, 75, 70, 66, 63, 60] },
  { cohort:'Fév',  size: 112, weeks:[100, 94, 87, 81, 76, 72, 68, null] },
  { cohort:'Mar',  size: 134, weeks:[100, 95, 88, 82, 77, 73, null, null] },
  { cohort:'Avr',  size: 156, weeks:[100, 96, 90, 84, 79, null, null, null] },
  { cohort:'Mai',  size: 178, weeks:[100, 97, 91, null, null, null, null, null] },
];

function MultiLineChart({ datasets, height = 280, formatY = (v) => Math.round(v/1000)+'k' }) {
  const wrapRef = useRef(null);
  const [size, setSize] = useState({ w: 600, h: height });
  const [hover, setHover] = useState(null);
  const pad = { t: 16, r: 24, b: 30, l: 56 };
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: height }));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, [height]);
  const w = size.w, h = size.h;
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const allVals = datasets.flatMap(d => d.data.map(p => p.v));
  const max = Math.max(...allVals) * 1.1;
  const n = datasets[0].data.length;
  const step = innerW / (n - 1);

  const toPath = (data) => data.map((d, i) => `${i === 0 ? 'M' : 'L'}${pad.l + i*step},${pad.t + innerH - (d.v/max)*innerH}`).join(' ');

  return (
    <div ref={wrapRef} style={{ padding:'4px 22px 18px', position:'relative' }}
      onMouseLeave={() => setHover(null)}
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left - pad.l;
        let idx = Math.round(x / step);
        if (idx < 0) idx = 0; if (idx > n - 1) idx = n - 1;
        setHover(idx);
      }}
    >
      <svg width={w} height={h}>
        <defs>
          {datasets.map((d, i) => (
            <linearGradient key={i} id={`mlc-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={d.color} stopOpacity="0.12"/>
              <stop offset="100%" stopColor={d.color} stopOpacity="0"/>
            </linearGradient>
          ))}
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((t, i) => {
          const v = max * t;
          const y = pad.t + innerH - t * innerH;
          return (
            <g key={i}>
              <line x1={pad.l} x2={w-pad.r} y1={y} y2={y} stroke="#EEF0F3" strokeDasharray={i === 0 ? '0' : '4 4'}/>
              <text x={pad.l - 8} y={y+4} fontSize="10.5" fill="#9CA3AF" textAnchor="end">{formatY(v)}</text>
            </g>
          );
        })}
        {datasets[0].data.map((p, i) => (
          (i % 2 === 0) ? <text key={i} x={pad.l + i*step} y={h-10} fontSize="10.5" fill="#6B7280" textAnchor="middle">{p.m}</text> : null
        ))}
        {datasets.map((d, di) => {
          const path = toPath(d.data);
          const area = `${path} L${pad.l + (n-1)*step},${pad.t + innerH} L${pad.l},${pad.t + innerH} Z`;
          return (
            <g key={di}>
              <path d={area} fill={`url(#mlc-${di})`}/>
              <path d={path} fill="none" stroke={d.color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
              {d.data.map((p, i) => (
                <circle key={i}
                  cx={pad.l + i*step} cy={pad.t + innerH - (p.v/max)*innerH}
                  r={hover === i ? 5 : 0} fill="#fff" stroke={d.color} strokeWidth="2.2"
                  style={{ transition:'r .15s' }}
                />
              ))}
            </g>
          );
        })}
        {hover != null && (
          <line x1={pad.l + hover*step} x2={pad.l + hover*step} y1={pad.t} y2={pad.t+innerH} stroke="#D1D5DB" strokeDasharray="3 3"/>
        )}
      </svg>
      {hover != null && (
        <div style={{
          position:'absolute',
          left: pad.l + hover*step + 22 + 'px',
          top: pad.t + 8,
          background:'#111827', color:'#fff',
          padding:'8px 12px', borderRadius:8,
          fontSize:12, minWidth:140,
          boxShadow:'0 6px 16px rgba(0,0,0,0.2)',
          pointerEvents:'none',
        }}>
          <div style={{ fontSize:10.5, opacity:.8, marginBottom:4, fontWeight:600 }}>{datasets[0].data[hover].m}</div>
          {datasets.map((d, i) => (
            <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', gap:12 }}>
              <span style={{ display:'flex', alignItems:'center', gap:6, opacity:.85 }}>
                <span style={{ width:8, height:8, borderRadius:999, background:d.color }}/> {d.label}
              </span>
              <b className="num">{d.format ? d.format(d.data[hover].v) : d.data[hover].v}</b>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BarChart({ data, height = 260, color = '#2D6A4F', formatV = (v) => v.toLocaleString('fr-FR') }) {
  const wrapRef = useRef(null);
  const [size, setSize] = useState({ w: 600, h: height });
  const pad = { t: 16, r: 16, b: 30, l: 56 };
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: height }));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, [height]);
  const w = size.w, h = size.h;
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const max = Math.max(...data.map(d => d.v)) * 1.1;
  const gap = 8;
  const bw = (innerW / data.length) - gap;
  const [mounted, setMounted] = useState(false);
  useEffect(() => { const t = setTimeout(() => setMounted(true), 60); return () => clearTimeout(t); }, []);

  return (
    <div ref={wrapRef} style={{ padding:'4px 22px 18px' }}>
      <svg width={w} height={h}>
        {[0, 0.25, 0.5, 0.75, 1].map((t, i) => {
          const v = max * t;
          const y = pad.t + innerH - t * innerH;
          return (
            <g key={i}>
              <line x1={pad.l} x2={w-pad.r} y1={y} y2={y} stroke="#EEF0F3" strokeDasharray={i === 0 ? '0' : '4 4'}/>
              <text x={pad.l - 8} y={y+4} fontSize="10.5" fill="#9CA3AF" textAnchor="end">{formatV(v)}</text>
            </g>
          );
        })}
        {data.map((d, i) => {
          const x = pad.l + i * (bw + gap) + gap/2;
          const targetH = (d.v / max) * innerH;
          const barH = mounted ? targetH : 0;
          const y = pad.t + innerH - barH;
          return (
            <g key={i}>
              <rect
                x={x} y={y} width={bw} height={barH}
                fill={d.color || color}
                rx={6}
                style={{ transition: 'height .9s cubic-bezier(.2,.7,.2,1), y .9s cubic-bezier(.2,.7,.2,1)' }}
              />
              <text x={x + bw/2} y={h-10} fontSize="10.5" fill="#6B7280" textAnchor="middle">{d.m}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function HeatMap({ rows }) {
  const cellColor = (v) => {
    if (v === null) return '#F3F4F6';
    if (v >= 90) return '#2D6A4F';
    if (v >= 80) return '#3a8862';
    if (v >= 70) return '#67a587';
    if (v >= 60) return '#9bc3ad';
    return '#cfe2d7';
  };
  const textColor = (v) => (v === null ? '#9CA3AF' : v >= 70 ? '#fff' : '#1c4633');
  return (
    <div style={{ padding:'12px 22px 18px' }}>
      <div style={{
        display:'grid',
        gridTemplateColumns: '80px repeat(8, 1fr) 70px',
        gap: 4,
        fontSize:11,
      }}>
        <div></div>
        {Array.from({ length: 8 }, (_, i) => (
          <div key={i} style={{ textAlign:'center', color:'var(--muted)', fontWeight:600, fontSize:10.5 }}>S{i + 1}</div>
        ))}
        <div style={{ textAlign:'right', color:'var(--muted)', fontWeight:600, fontSize:10.5, paddingRight:4 }}>Taille</div>
        {rows.map((r, i) => (
          <React.Fragment key={i}>
            <div style={{ display:'flex', alignItems:'center', fontSize:12, fontWeight:600, color:'var(--text)' }}>Cohorte {r.cohort}</div>
            {r.weeks.map((w, j) => (
              <div key={j} style={{
                aspectRatio: '1.6 / 1',
                background: cellColor(w),
                color: textColor(w),
                borderRadius: 6,
                display:'grid', placeItems:'center',
                fontSize: 11, fontWeight: 700,
                fontFeatureSettings: '"tnum"',
                transition: 'transform .12s',
                cursor: w === null ? 'default' : 'pointer',
              }}
              title={w === null ? '—' : `${w}% rétention en semaine ${j + 1}`}
              >{w === null ? '—' : `${w}%`}</div>
            ))}
            <div style={{ textAlign:'right', fontSize:12, fontWeight:700, color:'var(--text)', paddingRight:4, alignSelf:'center' }} className="num">{r.size}</div>
          </React.Fragment>
        ))}
      </div>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'flex-end', gap:8, marginTop:12, fontSize:11, color:'var(--muted)' }}>
        <span>Moins</span>
        {[0.2, 0.4, 0.6, 0.8, 1].map(t => (
          <div key={t} style={{ width:18, height:14, background: cellColor(t * 100), borderRadius:3 }}/>
        ))}
        <span>Plus</span>
      </div>
    </div>
  );
}

function Stats() {
  const [range, setRange] = useState('12m');

  return (
    <div className="content">
      {/* Filter toolbar */}
      <div className="filter-bar fade-in d1">
        <div style={{ fontSize:13, fontWeight:600, padding:'0 4px' }}>Période :</div>
        <div className="stack">
          {[
            { id:'7j', l:'7 jours' },
            { id:'30j', l:'30 jours' },
            { id:'3m', l:'3 mois' },
            { id:'12m', l:'12 mois' },
            { id:'all', l:'Tout' },
          ].map(r => (
            <button
              key={r.id}
              onClick={() => setRange(r.id)}
              className={`btn sm ${range === r.id ? '' : 'ghost'}`}
              style={range === r.id ? { background:'var(--primary)', color:'#fff', borderColor:'var(--primary)' } : {}}
            >{r.l}</button>
          ))}
        </div>
        <div className="chip-select"><I.calendar size={13}/> Comparer à période préc. <I.chevron size={12}/></div>
        <div style={{ flex:1 }}/>
        <button className="btn"><I.download size={14}/> Exporter CSV</button>
        <button className="btn"><I.download size={14}/> Exporter PDF</button>
        <button className="btn primary"><I.mail size={14}/> Programmer un rapport</button>
      </div>

      {/* KPIs */}
      <div className="metric-grid">
        <div className="metric fade-in d1">
          <div className="metric-ico green"><I.cash size={20}/></div>
          <div className="metric-label">Revenus totaux (12 mois)</div>
          <div className="metric-value num">{fmtNum(7168500)}</div>
          <div className="metric-foot">
            <span className="pill green"><I.trend size={11} stroke={2.5}/> +247%</span>
            <Sparkline data={STAT_REVENUE_12M.map(d => d.v)} color="#10B981"/>
          </div>
        </div>
        <div className="metric fade-in d2">
          <div className="metric-ico blue"><I.users size={20}/></div>
          <div className="metric-label">Membres actifs</div>
          <div className="metric-value num">{fmtNum(1247)}</div>
          <div className="metric-foot">
            <span className="pill green"><I.trend size={11} stroke={2.5}/> +202%</span>
            <Sparkline data={STAT_MEMBERS_12M.map(d => d.v)} color="#3B82F6"/>
          </div>
        </div>
        <div className="metric fade-in d3">
          <div className="metric-ico orange"><I.book size={20}/></div>
          <div className="metric-label">Valeur moyenne par membre</div>
          <div className="metric-value num">{fmtNum(5749)}</div>
          <div className="metric-foot">
            <span className="pill green"><I.trend size={11} stroke={2.5}/> +14.8%</span>
          </div>
        </div>
        <div className="metric fade-in d4">
          <div className="metric-ico violet"><I.spark size={20}/></div>
          <div className="metric-label">Taux de rétention 90j</div>
          <div className="metric-value num">68<span style={{ fontSize:18, color:'var(--muted)', fontWeight:500 }}>%</span></div>
          <div className="metric-foot">
            <span className="pill amber dot">Objectif : 75%</span>
          </div>
        </div>
      </div>

      {/* Main chart */}
      <div className="card fade-in d5" style={{ marginTop: 18 }}>
        <div className="card-head">
          <div>
            <div className="card-title">Croissance — Revenus & Membres</div>
            <div className="card-sub">Évolution mensuelle sur les 12 derniers mois · Échelle indexée</div>
          </div>
          <div className="stack">
            <div style={{ display:'flex', alignItems:'center', gap:14, fontSize:12 }}>
              <span style={{ display:'inline-flex', alignItems:'center', gap:5 }}>
                <span style={{ width:10, height:10, borderRadius:3, background:'#2D6A4F' }}/> Revenus
              </span>
              <span style={{ display:'inline-flex', alignItems:'center', gap:5 }}>
                <span style={{ width:10, height:10, borderRadius:3, background:'#F4A261' }}/> Membres
              </span>
            </div>
          </div>
        </div>
        <MultiLineChart
          datasets={[
            { label:'Revenus (HTG)', color:'#2D6A4F', data: STAT_REVENUE_12M, format: (v) => fmtNum(Math.round(v)) + ' HTG' },
            { label:'Membres',       color:'#F4A261', data: STAT_MEMBERS_12M.map(d => ({ m: d.m, v: d.v * 1000 })), format: (v) => fmtNum(Math.round(v / 1000)) },
          ]}
        />
      </div>

      {/* GEI distribution + payment mix */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:18, marginTop:18 }}>
        <div className="card fade-in d6">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Répartition par GEI</div>
              <div className="card-sub">Membres actifs par groupe d'épargne et d'investissement</div>
            </div>
            <button className="btn sm ghost"><I.download size={14}/></button>
          </div>
          <div style={{ padding:'14px 22px 18px', display:'flex', flexDirection:'column', gap:11 }}>
            {GEI_DISTRIBUTION.map(g => (
              <div key={g.gei}>
                <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:5 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                    <span className={`gei ${g.gei}`}>{g.gei}</span>
                    <span style={{ fontSize:13, fontWeight:500 }}>{g.name}</span>
                  </div>
                  <div style={{ display:'flex', alignItems:'baseline', gap:8 }}>
                    <span className="num" style={{ fontSize:14, fontWeight:700 }}>{g.count}</span>
                    <span style={{ fontSize:11, color:'var(--muted)', minWidth: 28, textAlign:'right' }}>{g.pct}%</span>
                  </div>
                </div>
                <div style={{ height:6, background:'#F3F4F6', borderRadius:999, overflow:'hidden' }}>
                  <div style={{
                    height:'100%',
                    width: `${g.pct * 2.6}%`,
                    maxWidth: '100%',
                    background: g.color,
                    borderRadius:999,
                    transition:'width 1.1s cubic-bezier(.2,.7,.2,1)',
                  }}/>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card fade-in d6">
          <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
            <div>
              <div className="card-title">Mix des moyens de paiement</div>
              <div className="card-sub">Part de chaque opérateur sur les 30 derniers jours</div>
            </div>
          </div>
          <BarChart
            data={[
              { m:'MonCash',     v: 38, color:'#E5202C' },
              { m:'NatCash',     v: 18, color:'#F39322' },
              { m:'Sogebank',    v: 14, color:'#1849A9' },
              { m:'Unibank',     v: 11, color:'#0E4A9E' },
              { m:'Cash',        v: 10, color:'#2D6A4F' },
              { m:'CapitalBank', v: 9,  color:'#E2231A' },
            ]}
            height={260}
            formatV={(v) => Math.round(v) + '%'}
          />
        </div>
      </div>

      {/* Top courses */}
      <div className="card fade-in d7" style={{ marginTop:18 }}>
        <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
          <div>
            <div className="card-title">Top des cours</div>
            <div className="card-sub">Classés par revenu généré · {STAT_REVENUE_12M.length} mois glissants</div>
          </div>
          <button className="btn sm"><I.download size={14}/> Exporter</button>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: 50 }}>#</th>
              <th>Cours</th>
              <th>Inscrits</th>
              <th>Note moyenne</th>
              <th style={{ textAlign:'right' }}>Revenu</th>
              <th style={{ width: '20%' }}>Évolution (6 mois)</th>
            </tr>
          </thead>
          <tbody className="row-anim">
            {TOP_COURSES_STATS.map((c, i) => (
              <tr key={c.title} style={{ animationDelay: `${0.04 * i}s` }}>
                <td>
                  <div style={{
                    width:28, height:28, borderRadius:8,
                    background: i === 0 ? 'linear-gradient(135deg,#F59E0B,#F4A261)' :
                                i === 1 ? '#E5E7EB' : i === 2 ? '#FDE68A' : 'var(--bg)',
                    color: i < 3 ? '#fff' : 'var(--muted)',
                    display:'grid', placeItems:'center',
                    fontSize:12, fontWeight:700,
                  }}>{i + 1}</div>
                </td>
                <td style={{ fontWeight:600 }}>{c.title}</td>
                <td className="num">{fmtNum(c.students)}</td>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:5 }}>
                    <I.spark size={13} style={{ color:'var(--star, #F59E0B)' }}/>
                    <span className="num" style={{ fontWeight:600 }}>{c.rating.toFixed(1)}</span>
                  </div>
                </td>
                <td className="num mono" style={{ textAlign:'right', fontWeight:700 }}>
                  {fmtNum(c.revenue)} <span style={{ color:'var(--muted)', fontWeight:500, fontSize:11 }}>HTG</span>
                </td>
                <td>
                  <Sparkline data={[20,28,32,40,52, 58 + i*4, 65 - i*3, 70 + i*2]} color={i === 0 ? '#10B981' : i === 1 ? '#3B82F6' : '#F4A261'} width={120} height={30}/>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cohort retention heatmap */}
      <div className="card fade-in d7" style={{ marginTop:18 }}>
        <div className="card-head" style={{ borderBottom:'1px solid var(--border-soft)', paddingBottom:14 }}>
          <div>
            <div className="card-title">Rétention par cohorte</div>
            <div className="card-sub">Pourcentage de membres encore actifs chaque semaine après inscription</div>
          </div>
          <span className="pill green dot">Tendance positive</span>
        </div>
        <HeatMap rows={COHORT_DATA}/>
      </div>

      {/* Bottom insights */}
      <div className="card fade-in d7" style={{ marginTop:18, background:'linear-gradient(135deg, #F0F8F3 0%, #FDF7EE 100%)', border:'1px solid var(--border)' }}>
        <div style={{ padding: 22, display:'grid', gridTemplateColumns:'auto 1fr', gap:18, alignItems:'flex-start' }}>
          <div style={{
            width:46, height:46, borderRadius:12,
            background:'var(--primary)', color:'#fff',
            display:'grid', placeItems:'center', flexShrink:0,
          }}><I.ai size={22}/></div>
          <div>
            <div style={{ fontSize:11, fontWeight:700, color:'var(--primary)', letterSpacing:'0.08em', textTransform:'uppercase' }}>Insights de l'IA</div>
            <div style={{ fontSize:15, fontWeight:600, letterSpacing:'-0.01em', marginTop:4, marginBottom:10 }}>3 observations sur le mois</div>
            <ul style={{ margin:0, padding:0, listStyle:'none', display:'flex', flexDirection:'column', gap:10 }}>
              <li style={{ display:'flex', gap:10, fontSize:13.5, lineHeight:1.5 }}>
                <div style={{
                  width:22, height:22, borderRadius:999,
                  background:'rgba(45,106,79,0.15)', color:'var(--primary)',
                  display:'grid', placeItems:'center', flexShrink:0,
                  marginTop:1,
                }}><I.trend size={12} stroke={3}/></div>
                <span>Les revenus ont bondi de <b>+38% en mai</b> par rapport à avril, porté à 71% par <b>MonCash</b> et NatCash combinés.</span>
              </li>
              <li style={{ display:'flex', gap:10, fontSize:13.5, lineHeight:1.5 }}>
                <div style={{
                  width:22, height:22, borderRadius:999,
                  background:'rgba(244,162,97,0.20)', color:'#B45309',
                  display:'grid', placeItems:'center', flexShrink:0,
                  marginTop:1,
                }}><I.users size={12} stroke={2.5}/></div>
                <span>La cohorte <b>d'avril</b> retient 79% à la semaine 5 — le meilleur score des 6 derniers mois. Continue ce parcours d'onboarding.</span>
              </li>
              <li style={{ display:'flex', gap:10, fontSize:13.5, lineHeight:1.5 }}>
                <div style={{
                  width:22, height:22, borderRadius:999,
                  background:'rgba(239,68,68,0.12)', color:'var(--danger)',
                  display:'grid', placeItems:'center', flexShrink:0,
                  marginTop:1,
                }}><I.trendDown size={12} stroke={3}/></div>
                <span>Seulement <b>5%</b> des membres viennent du <b>Sud (PDS)</b> — opportunité d'ouvrir un GEI à Petit-Goâve si la demande continue.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

window.Stats = Stats;
