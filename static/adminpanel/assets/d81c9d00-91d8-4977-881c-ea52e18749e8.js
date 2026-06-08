// Charts: count-up hook, sparkline, line chart, donut chart.

const { useState, useEffect, useRef } = React;

function useCountUp(target, duration = 1500, start = true) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!start) return;
    let raf, t0;
    const step = (t) => {
      if (!t0) t0 = t;
      const p = Math.min((t - t0) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * ease));
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration, start]);
  return val;
}

// Sparkline
function Sparkline({ data, color = '#2D6A4F', width = 60, height = 22 }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const r = max - min || 1;
  const step = width / (data.length - 1);
  const pts = data.map((v, i) => [i * step, height - ((v - min) / r) * (height - 2) - 1]);
  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
  const area = `${path} L${width},${height} L0,${height} Z`;
  const gid = 'sg' + Math.random().toString(36).slice(2, 7);
  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

// Smooth line chart with hover tooltip
function LineChart({ data, color = '#2D6A4F' }) {
  const wrapRef = useRef(null);
  const [hover, setHover] = useState(null);
  const [size, setSize] = useState({ w: 600, h: 260 });
  const padding = { t: 24, r: 20, b: 36, l: 50 };

  useEffect(() => {
    const ro = new ResizeObserver(([e]) => {
      setSize({ w: e.contentRect.width, h: 260 });
    });
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const w = size.w, h = size.h;
  const innerW = w - padding.l - padding.r;
  const innerH = h - padding.t - padding.b;
  const max = Math.max(...data.map(d => d.v)) * 1.1;
  const xStep = innerW / (data.length - 1);

  const pts = data.map((d, i) => ({
    x: padding.l + i * xStep,
    y: padding.t + innerH - (d.v / max) * innerH,
    v: d.v,
    m: d.m,
  }));

  // Catmull-Rom -> Bezier for smooth curve
  const smoothPath = () => {
    let d = `M${pts[0].x},${pts[0].y}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i - 1] || pts[i];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[i + 2] || p2;
      const c1x = p1.x + (p2.x - p0.x) / 6;
      const c1y = p1.y + (p2.y - p0.y) / 6;
      const c2x = p2.x - (p3.x - p1.x) / 6;
      const c2y = p2.y - (p3.y - p1.y) / 6;
      d += ` C${c1x},${c1y} ${c2x},${c2y} ${p2.x},${p2.y}`;
    }
    return d;
  };
  const path = smoothPath();
  const area = `${path} L${pts[pts.length - 1].x},${padding.t + innerH} L${pts[0].x},${padding.t + innerH} Z`;

  // y axis ticks
  const ticks = 4;
  const tickVals = Array.from({ length: ticks + 1 }, (_, i) => (max * i) / ticks);

  // path length animation
  const pathRef = useRef(null);
  const [len, setLen] = useState(0);
  useEffect(() => {
    if (pathRef.current) setLen(pathRef.current.getTotalLength());
  }, [path]);

  const handleMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    let idx = Math.round((x - padding.l) / xStep);
    if (idx < 0) idx = 0;
    if (idx > pts.length - 1) idx = pts.length - 1;
    setHover(idx);
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative', padding: '0 22px 18px' }}>
      <svg width={w} height={h} onMouseMove={handleMove} onMouseLeave={() => setHover(null)}>
        <defs>
          <linearGradient id="lineFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.18"/>
            <stop offset="100%" stopColor={color} stopOpacity="0"/>
          </linearGradient>
        </defs>
        {tickVals.map((v, i) => {
          const y = padding.t + innerH - (v / max) * innerH;
          return (
            <g key={i}>
              <line x1={padding.l} x2={w - padding.r} y1={y} y2={y} stroke="#EEF0F3" strokeDasharray={i === 0 ? '0' : '4 4'}/>
              <text x={padding.l - 10} y={y + 4} fontSize="10.5" fill="#9CA3AF" textAnchor="end">
                {v >= 1000 ? `${Math.round(v / 1000)}k` : v}
              </text>
            </g>
          );
        })}
        {pts.map((p, i) => (
          <text key={i} x={p.x} y={h - 12} fontSize="11.5" fill="#6B7280" textAnchor="middle" fontWeight="500">{p.m}</text>
        ))}
        <path d={area} fill="url(#lineFill)" style={{ opacity: len ? 1 : 0, transition: 'opacity .6s .4s' }}/>
        <path
          ref={pathRef} d={path}
          fill="none" stroke={color} strokeWidth="2.5"
          strokeLinecap="round" strokeLinejoin="round"
          style={{
            strokeDasharray: len, strokeDashoffset: len,
            animation: len ? 'dash 1.4s cubic-bezier(.2,.7,.2,1) forwards' : 'none',
          }}
        />
        {hover != null && (
          <g>
            <line x1={pts[hover].x} x2={pts[hover].x} y1={padding.t} y2={padding.t + innerH} stroke={color} strokeDasharray="3 3" strokeOpacity="0.5"/>
          </g>
        )}
        {pts.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={hover === i ? 5.5 : 0}
            fill="#fff" stroke={color} strokeWidth="2.5"
            style={{ transition: 'r .15s' }}
          />
        ))}
        <style>{`@keyframes dash { to { stroke-dashoffset: 0; } }`}</style>
      </svg>
      {hover != null && (
        <div
          className="chart-tip show"
          style={{ left: pts[hover].x, top: pts[hover].y }}
        >
          <div style={{ fontWeight: 600 }}>{fmtHTG(pts[hover].v)}</div>
          <div style={{ fontSize: 10.5, opacity: .8 }}>{pts[hover].m} 2026</div>
        </div>
      )}
    </div>
  );
}

// Donut chart
function DonutChart({ data, size = 200, thickness = 28 }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const r = size / 2 - thickness / 2 - 2;
  const c = 2 * Math.PI * r;
  const cx = size / 2, cy = size / 2;
  let acc = 0;
  const [mounted, setMounted] = useState(false);
  const [hover, setHover] = useState(null);
  useEffect(() => { const t = setTimeout(() => setMounted(true), 80); return () => clearTimeout(t); }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '6px 0 0' }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="#F3F4F6" strokeWidth={thickness}/>
          {data.map((d, i) => {
            const dash = (d.value / total) * c;
            const gap = c - dash;
            const offset = -acc;
            acc += dash;
            return (
              <circle
                key={i} cx={cx} cy={cy} r={r}
                fill="none"
                stroke={d.color}
                strokeWidth={hover === i ? thickness + 4 : thickness}
                strokeDasharray={`${mounted ? dash : 0} ${gap + (mounted ? 0 : dash)}`}
                strokeDashoffset={offset}
                style={{
                  transition: 'stroke-dasharray 1.1s cubic-bezier(.2,.7,.2,1), stroke-width .15s',
                  cursor: 'pointer',
                }}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
              />
            );
          })}
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
              {hover != null ? data[hover].name : 'Total cours'}
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em', marginTop: 2 }}>
              {hover != null ? `${data[hover].value}%` : total + '%'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { useCountUp, Sparkline, LineChart, DonutChart });
