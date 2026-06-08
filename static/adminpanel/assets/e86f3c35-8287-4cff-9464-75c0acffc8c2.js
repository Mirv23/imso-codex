/* ===== Salle & Réservations ===== */
/* Mock bookings (current week starting Monday) */
const ROOM_PRICE = 3750; // HTG / heure
const ROOM_CAP = { sans: 60, avec: 40 };

const EVENT_TYPES = [
  { id: 'mariage',     label: 'Mariage',          color: '#EC4899', ico: 'heart2' },
  { id: 'conference',  label: 'Conférence',       color: '#2D6A4F', ico: 'mic' },
  { id: 'seminaire',   label: 'Séminaire',        color: '#3B82F6', ico: 'briefcase' },
  { id: 'culte',       label: 'Culte / Veillée',  color: '#8B5CF6', ico: 'spark' },
  { id: 'autre',       label: 'Autre',            color: '#F59E0B', ico: 'building' },
];
const ET_MAP = Object.fromEntries(EVENT_TYPES.map(e => [e.id, e]));

/* Build current week (Monday based) */
function getWeek(offset = 0) {
  const now = new Date(2026, 4, 11); // pinned Monday 11 May 2026 for stable demo
  now.setDate(now.getDate() + offset * 7);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(now);
    d.setDate(now.getDate() + i);
    return d;
  });
}

const DAY_NAMES = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
const MONTHS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
const HOURS = Array.from({ length: 14 }, (_, i) => 8 + i); // 08h → 21h

/* Bookings on the current pinned week (week of 11 May 2026) */
const ROOM_BOOKINGS = [
  // day 0..6 corresponds to that week
  { id:'r1', day:0, start:9,  end:12, type:'seminaire', config:'avec', client:'Cabinet KPMG Haïti',           org:'Séminaire trimestriel',     people:38, status:'Confirmé', payment:'Stripe',  contact:'+509 3811 4527' },
  { id:'r2', day:1, start:14, end:17, type:'conference', config:'sans', client:'Église Évangélique de PAP',   org:'Conférence pastorale',      people:55, status:'Confirmé', payment:'MonCash', contact:'+509 3742 0918' },
  { id:'r3', day:2, start:18, end:21, type:'culte',     config:'sans', client:'Ministère Bethel',            org:'Veillée de prière',         people:50, status:'Confirmé', payment:'MonCash', contact:'+509 4220 7733' },
  { id:'r4', day:3, start:8,  end:11, type:'seminaire', config:'avec', client:'IMSO Haïti',                  org:'Formation interne',          people:30, status:'Confirmé', payment:'Interne', contact:'admin@imso.ht' },
  { id:'r5', day:4, start:16, end:21, type:'mariage',   config:'avec', client:'Famille Joseph–Pierre',       org:'Cérémonie de mariage',      people:40, status:'Confirmé', payment:'Stripe',  contact:'+509 3699 1284' },
  { id:'r6', day:5, start:10, end:14, type:'mariage',   config:'avec', client:'Famille Désir–Cadet',         org:'Réception civile',          people:40, status:'En attente', payment:'MonCash', contact:'+509 3404 5566' },
  { id:'r7', day:5, start:15, end:18, type:'autre',     config:'sans', client:'Comité jeunesse Cap-Haïtien', org:'Soirée culturelle',         people:48, status:'Confirmé', payment:'MonCash', contact:'+509 3955 4012' },
  { id:'r8', day:6, start:13, end:17, type:'conference', config:'sans', client:'Coopérative Agricole Sud',   org:'Assemblée générale',        people:60, status:'Option',   payment:'À régler', contact:'+509 3722 9911' },
  { id:'r9', day:0, start:18, end:21, type:'seminaire', config:'avec', client:'Wealth Academy Haïti',        org:'Atelier finance',           people:32, status:'Confirmé', payment:'Stripe',  contact:'+509 3677 8800' },
];

/* Upcoming reservations (next 30 days, mixed) */
const UPCOMING = [
  { id:'u1', date:'22 mai 2026', start:'14:00', end:'18:00', client:'Famille Bélizaire',          type:'mariage',    config:'avec', amount:15000, status:'Confirmé',  payment:'Stripe' },
  { id:'u2', date:'24 mai 2026', start:'09:00', end:'12:00', client:'Banque Nationale de Crédit', type:'seminaire',  config:'avec', amount:11250, status:'Confirmé',  payment:'Stripe' },
  { id:'u3', date:'27 mai 2026', start:'18:00', end:'21:00', client:'Église Bonne Nouvelle',      type:'culte',      config:'sans', amount:11250, status:'En attente', payment:'MonCash' },
  { id:'u4', date:'29 mai 2026', start:'10:00', end:'17:00', client:'Forum jeunesse Haïti',       type:'conference', config:'sans', amount:26250, status:'Confirmé',  payment:'MonCash' },
  { id:'u5', date:'05 juin 2026',start:'15:00', end:'22:00', client:'Famille Théodore–Auguste',   type:'mariage',    config:'avec', amount:26250, status:'Option',    payment:'À régler' },
];

const fmtDay = (d) => `${d.getDate()} ${MONTHS[d.getMonth()]}`;
const fmtPad = (n) => String(n).padStart(2, '0') + 'h';

function bookingColor(type) { return ET_MAP[type].color; }

function RoomKPIs() {
  const totalHours = ROOM_BOOKINGS.reduce((s, b) => s + (b.end - b.start), 0);
  const revenueWeek = totalHours * ROOM_PRICE;
  const slotsAvail = 7 * HOURS.length - totalHours;
  const occupancy = Math.round((totalHours / (7 * HOURS.length)) * 100);

  return (
    <div className="metric-grid">
      <div className="metric fade-in d1">
        <div className="metric-ico green"><I.calendar size={20}/></div>
        <div className="metric-label">Réservations cette semaine</div>
        <div className="metric-value num">{ROOM_BOOKINGS.length}</div>
        <div className="metric-foot">
          <span className="pill green"><I.trend size={11} stroke={2.5}/> +3 vs sem. dernière</span>
          <Sparkline data={[3,4,5,6,7,8,9]} color="#10B981"/>
        </div>
      </div>
      <div className="metric fade-in d2">
        <div className="metric-ico orange"><I.clock2 size={20}/></div>
        <div className="metric-label">Heures louées</div>
        <div className="metric-value num">{totalHours}<span style={{ fontSize: 16, color: 'var(--muted)', fontWeight:500 }}>h</span></div>
        <div className="metric-foot">
          <span className="pill amber dot">{occupancy}% taux d'occupation</span>
          <Sparkline data={[12,15,18,22,26,28,29]} color="#F59E0B"/>
        </div>
      </div>
      <div className="metric fade-in d3">
        <div className="metric-ico blue"><I.cash size={20}/></div>
        <div className="metric-label">Revenus semaine (HTG)</div>
        <div className="metric-value num">{fmtNum(revenueWeek)}</div>
        <div className="metric-foot">
          <span className="pill green"><I.trend size={11} stroke={2.5}/> {fmtNum(ROOM_PRICE)} HTG/h</span>
          <Sparkline data={[45,58,72,84,92,98,109]} color="#10B981"/>
        </div>
      </div>
      <div className="metric fade-in d4">
        <div className="metric-ico violet"><I.spark size={20}/></div>
        <div className="metric-label">Créneaux libres</div>
        <div className="metric-value num">{slotsAvail}<span style={{ fontSize: 16, color: 'var(--muted)', fontWeight:500 }}>h</span></div>
        <div className="metric-foot">
          <span className="pill gray">sur {7 * HOURS.length}h disponibles</span>
        </div>
      </div>
    </div>
  );
}

function WeekCalendar({ weekOffset, onWeekChange, onSlotClick, onBookingClick }) {
  const week = getWeek(weekOffset);
  const today = new Date(2026, 4, 21); // pinned "today"
  const isSameDay = (a, b) => a.getDate() === b.getDate() && a.getMonth() === b.getMonth();

  // Group bookings by day
  const bookingsByDay = Array.from({ length: 7 }, () => []);
  ROOM_BOOKINGS.forEach(b => bookingsByDay[b.day].push(b));

  const slotH = 52; // px per hour

  return (
    <div className="card fade-in d5" style={{ marginTop: 18, overflow: 'hidden' }}>
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Calendrier hebdomadaire</div>
          <div className="card-sub">
            Semaine du {fmtDay(week[0])} au {fmtDay(week[6])} 2026
            · Cliquez sur un créneau libre pour réserver
          </div>
        </div>
        <div className="stack">
          <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:12, color:'var(--muted)', marginRight:8 }}>
            {EVENT_TYPES.slice(0,4).map(e => (
              <span key={e.id} style={{ display:'inline-flex', alignItems:'center', gap:4 }}>
                <span style={{ width:9, height:9, borderRadius:3, background:e.color }}/>
                {e.label}
              </span>
            ))}
          </div>
          <div style={{ display:'flex', alignItems:'center', border:'1px solid var(--border)', borderRadius:9 }}>
            <button className="pager-btn" style={{ border:0, borderRight:'1px solid var(--border)', borderRadius:'8px 0 0 8px' }} onClick={() => onWeekChange(weekOffset - 1)}><I.chevronL size={14}/></button>
            <button className="btn sm ghost" style={{ borderRadius:0 }} onClick={() => onWeekChange(0)}>Aujourd'hui</button>
            <button className="pager-btn" style={{ border:0, borderLeft:'1px solid var(--border)', borderRadius:'0 8px 8px 0' }} onClick={() => onWeekChange(weekOffset + 1)}><I.chevronR size={14}/></button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '56px repeat(7, 1fr)', borderBottom:'1px solid var(--border-soft)', background:'#FAFBFC' }}>
        <div></div>
        {week.map((d, i) => {
          const isToday = isSameDay(d, today);
          return (
            <div key={i} style={{ padding:'12px 8px', textAlign:'center', borderLeft:'1px solid var(--border-soft)' }}>
              <div style={{ fontSize:10.5, fontWeight:600, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em' }}>{DAY_NAMES[i]}</div>
              <div style={{
                fontSize: 17, fontWeight: 700, marginTop: 2, letterSpacing:'-0.02em',
                color: isToday ? '#fff' : 'var(--text)',
                background: isToday ? 'var(--primary)' : 'transparent',
                width: isToday ? 28 : 'auto', height: isToday ? 28 : 'auto',
                borderRadius: isToday ? 999 : 0,
                display: 'inline-grid', placeItems: 'center',
              }}>{d.getDate()}</div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '56px repeat(7, 1fr)', position:'relative' }}>
        {/* Hour gutter */}
        <div>
          {HOURS.map(h => (
            <div key={h} style={{ height: slotH, padding:'4px 8px', borderTop:'1px solid var(--border-soft)', textAlign:'right' }}>
              <span className="mono" style={{ fontSize:10.5, color:'var(--muted)', fontWeight:600 }}>{fmtPad(h)}</span>
            </div>
          ))}
        </div>

        {/* Day columns */}
        {week.map((d, dayIdx) => (
          <div key={dayIdx} style={{ position:'relative', borderLeft:'1px solid var(--border-soft)' }}>
            {HOURS.map(h => {
              const isBooked = bookingsByDay[dayIdx].some(b => h >= b.start && h < b.end);
              return (
                <div
                  key={h}
                  style={{
                    height: slotH,
                    borderTop: '1px solid var(--border-soft)',
                    cursor: isBooked ? 'default' : 'pointer',
                    transition: 'background .15s',
                  }}
                  onClick={() => !isBooked && onSlotClick({ day: dayIdx, hour: h, date: d })}
                  onMouseEnter={(e) => { if (!isBooked) e.currentTarget.style.background = 'var(--primary-light)'; }}
                  onMouseLeave={(e) => { if (!isBooked) e.currentTarget.style.background = ''; }}
                />
              );
            })}
            {bookingsByDay[dayIdx].map(b => {
              const top = (b.start - HOURS[0]) * slotH + 1;
              const height = (b.end - b.start) * slotH - 2;
              const et = ET_MAP[b.type];
              return (
                <div
                  key={b.id}
                  onClick={() => onBookingClick(b)}
                  style={{
                    position: 'absolute',
                    top, left: 4, right: 4,
                    height,
                    background: `linear-gradient(135deg, ${et.color}22, ${et.color}11)`,
                    borderLeft: `3px solid ${et.color}`,
                    borderRadius: 6,
                    padding: '5px 7px',
                    fontSize: 11,
                    overflow: 'hidden',
                    cursor: 'pointer',
                    transition: 'transform .12s, box-shadow .15s',
                    color: 'var(--text)',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.transform = 'translateX(1px)'; e.currentTarget.style.boxShadow = '0 4px 12px -4px rgba(0,0,0,0.10)'; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
                >
                  <div style={{ fontWeight:700, color: et.color, fontSize: 10.5, letterSpacing:'0.02em', textTransform:'uppercase' }}>
                    {fmtPad(b.start)}–{fmtPad(b.end)}
                  </div>
                  <div style={{ fontWeight:600, marginTop:2, lineHeight:1.25, color:'var(--text)' }} className="truncate">
                    {b.client}
                  </div>
                  {height > 60 && (
                    <div style={{ fontSize:10.5, color:'var(--muted)', marginTop:3, display:'flex', alignItems:'center', gap:4 }}>
                      <I.users size={10}/> {b.people} pers · {b.config === 'avec' ? 'avec tables' : 'sans tables'}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function RoomSetupCard() {
  const [setup, setSetup] = useState('sans');
  return (
    <div className="card fade-in d6">
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Configuration de la salle</div>
          <div className="card-sub">Capacité selon la disposition · Tarif horaire fixe</div>
        </div>
        <button className="btn sm"><I.settings size={14}/> Modifier</button>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14, padding: 18 }}>
        <button
          onClick={() => setSetup('sans')}
          style={{
            background: setup==='sans' ? 'var(--primary-light)' : '#FAFBFC',
            border: setup==='sans' ? '1.5px solid var(--primary)' : '1.5px solid var(--border-soft)',
            borderRadius: 14, padding: '18px 16px',
            display:'flex', flexDirection:'column', alignItems:'flex-start', gap:10,
            cursor:'pointer', transition:'all .15s',
            textAlign:'left',
          }}
        >
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: setup==='sans' ? 'var(--primary)' : '#fff',
            color: setup==='sans' ? '#fff' : 'var(--primary)',
            display:'grid', placeItems:'center',
            border: setup==='sans' ? '0' : '1px solid var(--border)',
          }}>
            <I.chair size={20}/>
          </div>
          <div>
            <div style={{ fontSize:13, color:'var(--muted)', fontWeight:500 }}>Sans tables</div>
            <div style={{ fontSize:28, fontWeight:800, letterSpacing:'-0.02em', color: setup==='sans' ? 'var(--primary)' : 'var(--text)' }} className="num">
              {ROOM_CAP.sans}<span style={{ fontSize:14, fontWeight:500, color:'var(--muted)' }}> places</span>
            </div>
            <div style={{ fontSize:11.5, color:'var(--muted)', marginTop:2 }}>Conférences, cultes, séminaires</div>
          </div>
        </button>

        <button
          onClick={() => setSetup('avec')}
          style={{
            background: setup==='avec' ? 'var(--primary-light)' : '#FAFBFC',
            border: setup==='avec' ? '1.5px solid var(--primary)' : '1.5px solid var(--border-soft)',
            borderRadius: 14, padding: '18px 16px',
            display:'flex', flexDirection:'column', alignItems:'flex-start', gap:10,
            cursor:'pointer', transition:'all .15s',
            textAlign:'left',
          }}
        >
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: setup==='avec' ? 'var(--primary)' : '#fff',
            color: setup==='avec' ? '#fff' : 'var(--primary)',
            display:'grid', placeItems:'center',
            border: setup==='avec' ? '0' : '1px solid var(--border)',
          }}>
            <I.table size={20}/>
          </div>
          <div>
            <div style={{ fontSize:13, color:'var(--muted)', fontWeight:500 }}>Avec tables</div>
            <div style={{ fontSize:28, fontWeight:800, letterSpacing:'-0.02em', color: setup==='avec' ? 'var(--primary)' : 'var(--text)' }} className="num">
              {ROOM_CAP.avec}<span style={{ fontSize:14, fontWeight:500, color:'var(--muted)' }}> places</span>
            </div>
            <div style={{ fontSize:11.5, color:'var(--muted)', marginTop:2 }}>Mariages, réceptions, ateliers</div>
          </div>
        </button>
      </div>

      <div style={{ padding: '4px 18px 18px' }}>
        <div style={{
          background: 'linear-gradient(135deg, var(--primary-light), #f8f5ec)',
          borderRadius: 12, padding: 14,
          display:'flex', alignItems:'center', gap: 14,
        }}>
          <div style={{
            width:42, height:42, borderRadius:10, background:'var(--primary)',
            color:'#fff', display:'grid', placeItems:'center', flexShrink:0,
          }}>
            <I.cash size={20}/>
          </div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:11.5, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Tarif</div>
            <div style={{ fontSize:20, fontWeight:700, letterSpacing:'-0.02em', color:'var(--primary)' }} className="num">
              {fmtNum(ROOM_PRICE)} HTG<span style={{ fontSize:13, fontWeight:500, color:'var(--muted)' }}> / heure</span>
            </div>
          </div>
          <button className="btn sm">Ajuster</button>
        </div>

        <div style={{ marginTop:14 }}>
          <div style={{ fontSize:11.5, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600, marginBottom:8 }}>Équipements inclus</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
            {['Climatisation','Sono pro','2 micros sans fil','Projecteur 4K','Wi-Fi fibre','Parking 30 places','Cuisine traiteur','Générateur'].map(e => (
              <span key={e} className="pill gray" style={{ fontSize:11 }}>{e}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function EventDistribution() {
  const counts = EVENT_TYPES.map(t => ({
    ...t,
    count: ROOM_BOOKINGS.filter(b => b.type === t.id).length,
  }));
  const total = counts.reduce((s, c) => s + c.count, 0) || 1;
  return (
    <div className="card fade-in d6">
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Types d'événements</div>
          <div className="card-sub">Répartition cette semaine</div>
        </div>
      </div>
      <div style={{ padding: '14px 18px 18px', display:'flex', flexDirection:'column', gap: 12 }}>
        {counts.map(c => (
          <div key={c.id}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom: 5 }}>
              <div style={{ display:'flex', alignItems:'center', gap:8, fontSize:13 }}>
                <div style={{ width: 24, height: 24, borderRadius: 6, background: `${c.color}1a`, color: c.color, display:'grid', placeItems:'center' }}>
                  {I[c.ico] ? I[c.ico]({ size: 14 }) : <I.spark size={14}/>}
                </div>
                <span style={{ fontWeight:500 }}>{c.label}</span>
              </div>
              <span className="num" style={{ fontSize:13, fontWeight:700 }}>{c.count}</span>
            </div>
            <div style={{ height: 6, background:'#F3F4F6', borderRadius:999, overflow:'hidden' }}>
              <div style={{
                height:'100%',
                width: `${(c.count/total)*100}%`,
                background: c.color,
                borderRadius:999,
                transition: 'width 1.1s cubic-bezier(.2,.7,.2,1)',
              }}/>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function UpcomingTable({ onNew }) {
  return (
    <div className="card fade-in d7" style={{ marginTop: 18 }}>
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 14 }}>
        <div>
          <div className="card-title">Réservations à venir</div>
          <div className="card-sub">{UPCOMING.length} prochaines locations · Mis à jour il y a quelques secondes</div>
        </div>
        <div className="stack">
          <button className="btn sm"><I.filter size={14}/> Filtrer</button>
          <button className="btn sm"><I.download size={14}/> Exporter</button>
          <button className="btn primary sm" onClick={onNew}><I.plus size={14} stroke={2.5}/> Nouvelle réservation</button>
        </div>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Client & événement</th>
            <th>Date</th>
            <th>Créneau</th>
            <th>Configuration</th>
            <th style={{ textAlign:'right' }}>Montant</th>
            <th>Paiement</th>
            <th>Statut</th>
            <th style={{ textAlign:'right' }}>Actions</th>
          </tr>
        </thead>
        <tbody className="row-anim">
          {UPCOMING.map((u, i) => {
            const et = ET_MAP[u.type];
            return (
              <tr key={u.id} style={{ animationDelay: `${0.04 * i}s` }}>
                <td>
                  <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                    <div style={{
                      width: 34, height: 34, borderRadius: 9,
                      background: `${et.color}1a`, color: et.color,
                      display:'grid', placeItems:'center',
                    }}>
                      {I[et.ico] ? I[et.ico]({ size: 16 }) : <I.spark size={16}/>}
                    </div>
                    <div>
                      <div style={{ fontWeight:600 }}>{u.client}</div>
                      <div style={{ fontSize:11.5, color:'var(--muted)' }}>{et.label}</div>
                    </div>
                  </div>
                </td>
                <td style={{ color:'var(--muted)' }}>{u.date}</td>
                <td className="mono" style={{ fontWeight:600 }}>{u.start} – {u.end}</td>
                <td>
                  <span className="pill" style={{ background: u.config==='avec' ? 'rgba(244,162,97,0.12)' : 'rgba(45,106,79,0.10)', color: u.config==='avec' ? '#B45309' : '#047857' }}>
                    {u.config==='avec' ? <><I.table size={11} stroke={2.2}/> Avec tables · {ROOM_CAP.avec}</> : <><I.chair size={11} stroke={2.2}/> Sans tables · {ROOM_CAP.sans}</>}
                  </span>
                </td>
                <td className="num mono" style={{ textAlign:'right', fontWeight:700 }}>
                  {fmtNum(u.amount)} <span style={{ color:'var(--muted)', fontSize:11, fontWeight:500 }}>HTG</span>
                </td>
                <td>
                  <span className={`pill ${u.payment==='MonCash' ? 'amber' : u.payment==='Stripe' ? 'violet' : 'gray'}`}>{u.payment}</span>
                </td>
                <td>
                  <span className={`pill dot ${u.status==='Confirmé' ? 'green' : u.status==='En attente' ? 'amber' : 'blue'}`}>{u.status}</span>
                </td>
                <td style={{ textAlign:'right' }}>
                  <div className="stack" style={{ justifyContent:'flex-end' }}>
                    <button className="btn sm ghost"><I.eye size={14}/></button>
                    <button className="btn sm ghost"><I.mail size={14}/></button>
                    <button className="btn sm ghost"><I.more size={14}/></button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BookingDrawer({ open, onClose, preset }) {
  const [type, setType] = useState('mariage');
  const [config, setConfig] = useState('sans');
  const [start, setStart] = useState('09:00');
  const [end, setEnd] = useState('12:00');
  const [date, setDate] = useState('22 mai 2026');
  const [client, setClient] = useState('');

  useEffect(() => {
    if (preset && open) {
      setDate(fmtDay(preset.date) + ' 2026');
      setStart(String(preset.hour).padStart(2,'0') + ':00');
      setEnd(String(preset.hour + 3).padStart(2,'0') + ':00');
    }
  }, [preset, open]);

  const hStart = parseInt(start.split(':')[0]);
  const hEnd = parseInt(end.split(':')[0]);
  const dur = Math.max(0, hEnd - hStart);
  const total = dur * ROOM_PRICE;

  return (
    <React.Fragment>
      <div className={`drawer-overlay ${open ? 'open' : ''}`} onClick={onClose}/>
      <div className={`drawer ${open ? 'open' : ''}`}>
        <div className="drawer-head">
          <div>
            <div style={{ fontSize: 17, fontWeight: 700, letterSpacing:'-0.015em' }}>Nouvelle réservation</div>
            <div style={{ fontSize: 12.5, color:'var(--muted)', marginTop:2 }}>Salle IMSO · {fmtNum(ROOM_PRICE)} HTG/h</div>
          </div>
          <button className="icon-btn" onClick={onClose}><I.close size={18}/></button>
        </div>
        <div className="drawer-body">
          <div className="field">
            <label>Type d'événement</label>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:8 }}>
              {EVENT_TYPES.map(t => (
                <button
                  key={t.id}
                  onClick={() => setType(t.id)}
                  style={{
                    padding: '10px 8px',
                    border: type===t.id ? `1.5px solid ${t.color}` : '1.5px solid var(--border-soft)',
                    background: type===t.id ? `${t.color}10` : '#fff',
                    borderRadius: 10,
                    cursor: 'pointer',
                    color: type===t.id ? t.color : 'var(--text)',
                    fontSize: 12, fontWeight: 600,
                    display:'flex', flexDirection:'column', alignItems:'center', gap:6,
                    transition: 'all .15s',
                  }}
                >
                  {I[t.ico] ? I[t.ico]({ size: 16 }) : <I.spark size={16}/>}
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>Client / Organisation</label>
            <input className="input" placeholder="ex: Famille Joseph–Pierre" value={client} onChange={e => setClient(e.target.value)}/>
          </div>

          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap: 12 }}>
            <div className="field">
              <label>Date</label>
              <input className="input" value={date} onChange={e => setDate(e.target.value)}/>
            </div>
            <div className="field">
              <label>Début</label>
              <input className="input mono" value={start} onChange={e => setStart(e.target.value)}/>
            </div>
            <div className="field">
              <label>Fin</label>
              <input className="input mono" value={end} onChange={e => setEnd(e.target.value)}/>
            </div>
          </div>

          <div className="field">
            <label>Configuration de la salle</label>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
              <button
                onClick={() => setConfig('sans')}
                style={{
                  padding: '14px',
                  border: config==='sans' ? '1.5px solid var(--primary)' : '1.5px solid var(--border-soft)',
                  background: config==='sans' ? 'var(--primary-light)' : '#fff',
                  borderRadius: 10, cursor: 'pointer',
                  textAlign: 'left', display:'flex', alignItems:'center', gap:10,
                }}
              >
                <I.chair size={20} style={{ color: config==='sans' ? 'var(--primary)' : 'var(--muted)' }}/>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Sans tables</div>
                  <div style={{ fontSize: 11.5, color:'var(--muted)' }}>{ROOM_CAP.sans} places</div>
                </div>
              </button>
              <button
                onClick={() => setConfig('avec')}
                style={{
                  padding: '14px',
                  border: config==='avec' ? '1.5px solid var(--primary)' : '1.5px solid var(--border-soft)',
                  background: config==='avec' ? 'var(--primary-light)' : '#fff',
                  borderRadius: 10, cursor: 'pointer',
                  textAlign: 'left', display:'flex', alignItems:'center', gap:10,
                }}
              >
                <I.table size={20} style={{ color: config==='avec' ? 'var(--primary)' : 'var(--muted)' }}/>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Avec tables</div>
                  <div style={{ fontSize: 11.5, color:'var(--muted)' }}>{ROOM_CAP.avec} places</div>
                </div>
              </button>
            </div>
          </div>

          <div className="field">
            <label>Contact (téléphone / email)</label>
            <input className="input" placeholder="+509 3742 0918"/>
          </div>

          <div className="field">
            <label>Notes</label>
            <textarea className="textarea" placeholder="Demandes particulières (sono, traiteur, etc.)"></textarea>
          </div>

          <div style={{
            background:'linear-gradient(135deg, var(--primary-light), #f8f5ec)',
            borderRadius: 12,
            padding: 16,
            marginTop: 8,
          }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline' }}>
              <div>
                <div style={{ fontSize:11.5, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Récapitulatif</div>
                <div style={{ fontSize:13, color:'var(--text)', marginTop:4 }}>
                  <b className="num">{dur}h</b> × {fmtNum(ROOM_PRICE)} HTG
                </div>
              </div>
              <div style={{ textAlign:'right' }}>
                <div style={{ fontSize:11, color:'var(--muted)' }}>TOTAL</div>
                <div style={{ fontSize:26, fontWeight:800, letterSpacing:'-0.02em', color:'var(--primary)' }} className="num">
                  {fmtNum(total)} <span style={{ fontSize:13, color:'var(--muted)', fontWeight:500 }}>HTG</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="drawer-foot">
          <button className="btn" onClick={onClose}>Enregistrer en option</button>
          <button className="btn primary" onClick={() => { alert('Réservation confirmée (démo)'); onClose(); }}>
            <I.check size={14}/> Confirmer & encaisser
          </button>
        </div>
      </div>
    </React.Fragment>
  );
}

function BookingDetailModal({ booking, onClose }) {
  if (!booking) return null;
  const et = ET_MAP[booking.type];
  const total = (booking.end - booking.start) * ROOM_PRICE;
  return (
    <div className="modal-overlay open" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 480 }}>
        <div style={{
          padding: '22px 24px',
          background: `linear-gradient(135deg, ${et.color}22, ${et.color}11)`,
          borderRadius: '16px 16px 0 0',
          borderBottom: `1px solid ${et.color}33`,
        }}>
          <div style={{ display:'flex', alignItems:'center', gap:12 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 11,
              background: et.color, color:'#fff',
              display:'grid', placeItems:'center',
            }}>{I[et.ico] ? I[et.ico]({ size: 20 }) : <I.spark size={20}/>}</div>
            <div>
              <div style={{ fontSize:11, color:et.color, fontWeight:700, textTransform:'uppercase', letterSpacing:'0.08em' }}>{et.label}</div>
              <div style={{ fontSize:18, fontWeight:700, letterSpacing:'-0.02em' }}>{booking.client}</div>
              <div style={{ fontSize:12.5, color:'var(--muted)', marginTop:1 }}>{booking.org}</div>
            </div>
            <button className="icon-btn" onClick={onClose} style={{ marginLeft:'auto' }}><I.close size={18}/></button>
          </div>
        </div>
        <div className="modal-body" style={{ paddingTop:18 }}>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Créneau</div>
              <div className="mono" style={{ fontSize:15, fontWeight:700, marginTop:4 }}>{fmtPad(booking.start)} – {fmtPad(booking.end)}</div>
              <div style={{ fontSize:12, color:'var(--muted)' }}>{booking.end - booking.start} heures</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Configuration</div>
              <div style={{ fontSize:15, fontWeight:700, marginTop:4, display:'flex', alignItems:'center', gap:6 }}>
                {booking.config==='avec' ? <I.table size={16}/> : <I.chair size={16}/>}
                {booking.config==='avec' ? 'Avec tables' : 'Sans tables'}
              </div>
              <div style={{ fontSize:12, color:'var(--muted)' }}>{booking.people} personnes attendues</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Contact</div>
              <div className="mono" style={{ fontSize:13, fontWeight:600, marginTop:4 }}>{booking.contact}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--muted)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>Paiement</div>
              <div style={{ marginTop:6 }}>
                <span className={`pill ${booking.payment==='MonCash' ? 'amber' : booking.payment==='Stripe' ? 'violet' : 'gray'}`}>{booking.payment}</span>
                <span className={`pill dot ${booking.status==='Confirmé' ? 'green' : booking.status==='En attente' ? 'amber' : 'blue'}`} style={{ marginLeft:4 }}>{booking.status}</span>
              </div>
            </div>
          </div>
          <div style={{
            marginTop:18, padding:14,
            background:'var(--primary-light)', borderRadius:10,
            display:'flex', justifyContent:'space-between', alignItems:'baseline'
          }}>
            <div style={{ fontSize:12, color:'var(--muted)' }}>{booking.end - booking.start}h × {fmtNum(ROOM_PRICE)} HTG</div>
            <div style={{ fontSize:22, fontWeight:800, color:'var(--primary)', letterSpacing:'-0.02em' }} className="num">{fmtNum(total)} HTG</div>
          </div>
        </div>
        <div className="modal-foot">
          <button className="btn"><I.ban size={14}/> Annuler la réservation</button>
          <button className="btn"><I.mail size={14}/> Contacter</button>
          <button className="btn primary"><I.check size={14}/> Marquer encaissé</button>
        </div>
      </div>
    </div>
  );
}

function Room() {
  const [weekOffset, setWeekOffset] = useState(0);
  const [drawer, setDrawer] = useState(false);
  const [preset, setPreset] = useState(null);
  const [detail, setDetail] = useState(null);

  const openSlot = (info) => { setPreset(info); setDrawer(true); };
  const closeDrawer = () => { setDrawer(false); setPreset(null); };

  return (
    <div className="content">
      <RoomKPIs/>

      <div style={{ display:'grid', gridTemplateColumns:'1.6fr 1fr', gap: 18, marginTop: 18 }}>
        <WeekCalendar weekOffset={weekOffset} onWeekChange={setWeekOffset} onSlotClick={openSlot} onBookingClick={setDetail}/>
        <div style={{ display:'flex', flexDirection:'column', gap: 18 }}>
          <RoomSetupCard/>
          <EventDistribution/>
        </div>
      </div>

      <UpcomingTable onNew={() => { setPreset(null); setDrawer(true); }}/>

      <BookingDrawer open={drawer} onClose={closeDrawer} preset={preset}/>
      {detail && <BookingDetailModal booking={detail} onClose={() => setDetail(null)}/>}
    </div>
  );
}

window.Room = Room;
