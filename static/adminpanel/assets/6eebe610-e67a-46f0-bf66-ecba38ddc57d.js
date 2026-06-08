// Tabler-style stroked icons. 1.75 stroke, 20px default.
const Icon = ({ size = 20, stroke = 1.75, children, style }) => (
  <svg
    width={size} height={size} viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth={stroke}
    strokeLinecap="round" strokeLinejoin="round"
    style={style}
  >{children}</svg>
);

const I = {
  dashboard: (p) => <Icon {...p}><path d="M4 4h6v8H4z"/><path d="M14 4h6v4h-6z"/><path d="M14 12h6v8h-6z"/><path d="M4 16h6v4H4z"/></Icon>,
  users: (p) => <Icon {...p}><path d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/><path d="M16 3.5a4 4 0 0 1 0 7"/><path d="M21 21v-2a4 4 0 0 0-3-3.85"/></Icon>,
  book: (p) => <Icon {...p}><path d="M3 4.5A2.5 2.5 0 0 1 5.5 2H20v18H5.5a2.5 2.5 0 0 0-2.5 2.5z"/><path d="M3 19.5A2.5 2.5 0 0 1 5.5 17H20"/></Icon>,
  cash: (p) => <Icon {...p}><path d="M3 6h18v12H3z"/><circle cx="12" cy="12" r="2.5"/><path d="M6 9v.01"/><path d="M18 15v.01"/></Icon>,
  ai: (p) => <Icon {...p}><path d="M12 3v2"/><path d="M12 19v2"/><path d="M5 12H3"/><path d="M21 12h-2"/><rect x="7" y="7" width="10" height="10" rx="2"/><path d="M10 10h.01"/><path d="M14 10h.01"/><path d="M10 14h4"/></Icon>,
  chart: (p) => <Icon {...p}><path d="M4 19V5"/><path d="M9 19V11"/><path d="M14 19V8"/><path d="M19 19V14"/><path d="M3 21h18"/></Icon>,
  settings: (p) => <Icon {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 1 1-4 0v-.08A1.7 1.7 0 0 0 9 19.4a1.7 1.7 0 0 0-1.87.34l-.06.06A2 2 0 1 1 4.24 16.97l.06-.06A1.7 1.7 0 0 0 4.64 15a1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 1 1 0-4h.08A1.7 1.7 0 0 0 4.64 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06A2 2 0 1 1 7.07 4.24l.06.06a1.7 1.7 0 0 0 1.87.34H9a1.7 1.7 0 0 0 1.03-1.56V3a2 2 0 1 1 4 0v.08A1.7 1.7 0 0 0 15 4.64a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9v0c.6.23 1 .8 1 1.45V11a2 2 0 1 1 0 4h-.08A1.7 1.7 0 0 0 19.4 15z"/></Icon>,
  logout: (p) => <Icon {...p}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></Icon>,
  search: (p) => <Icon {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></Icon>,
  bell: (p) => <Icon {...p}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/></Icon>,
  chevron: (p) => <Icon {...p}><path d="m6 9 6 6 6-6"/></Icon>,
  chevronR: (p) => <Icon {...p}><path d="m9 18 6-6-6-6"/></Icon>,
  chevronL: (p) => <Icon {...p}><path d="m15 18-6-6 6-6"/></Icon>,
  trend: (p) => <Icon {...p}><path d="m3 17 6-6 4 4 8-8"/><path d="M14 7h7v7"/></Icon>,
  trendDown: (p) => <Icon {...p}><path d="m3 7 6 6 4-4 8 8"/><path d="M14 17h7v-7"/></Icon>,
  filter: (p) => <Icon {...p}><path d="M4 4h16l-6 8v6l-4 2v-8L4 4z"/></Icon>,
  plus: (p) => <Icon {...p}><path d="M12 5v14"/><path d="M5 12h14"/></Icon>,
  close: (p) => <Icon {...p}><path d="M18 6 6 18"/><path d="m6 6 12 12"/></Icon>,
  eye: (p) => <Icon {...p}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></Icon>,
  upload: (p) => <Icon {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/></Icon>,
  download: (p) => <Icon {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/></Icon>,
  more: (p) => <Icon {...p}><circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/></Icon>,
  spark: (p) => <Icon {...p}><path d="M12 3v3"/><path d="M12 18v3"/><path d="m4.93 4.93 2.12 2.12"/><path d="m16.95 16.95 2.12 2.12"/><path d="M3 12h3"/><path d="M18 12h3"/><path d="m4.93 19.07 2.12-2.12"/><path d="m16.95 7.05 2.12-2.12"/></Icon>,
  calendar: (p) => <Icon {...p}><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/></Icon>,
  mail: (p) => <Icon {...p}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></Icon>,
  arrow: (p) => <Icon {...p}><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></Icon>,
  sortUp: (p) => <Icon size={12} {...p}><path d="m6 15 6-6 6 6"/></Icon>,
  sortDown: (p) => <Icon size={12} {...p}><path d="m6 9 6 6 6-6"/></Icon>,
  sort: (p) => <Icon size={12} {...p}><path d="m8 9 4-4 4 4"/><path d="m16 15-4 4-4-4"/></Icon>,
  play: (p) => <Icon {...p}><path d="M6 4l14 8L6 20z" fill="currentColor"/></Icon>,
  video: (p) => <Icon {...p}><rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10 5-3v10l-5-3z"/></Icon>,
  music: (p) => <Icon {...p}><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/><path d="M9 18V6l12-2v12"/></Icon>,
  fileText: (p) => <Icon {...p}><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M9 13h6"/><path d="M9 17h6"/></Icon>,
  check: (p) => <Icon {...p}><path d="m5 12 5 5L20 7"/></Icon>,
  pin: (p) => <Icon {...p}><circle cx="12" cy="10" r="3"/><path d="M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12z"/></Icon>,
  building: (p) => <Icon {...p}><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M8 10h.01"/><path d="M12 10h.01"/><path d="M16 10h.01"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/></Icon>,
  chair: (p) => <Icon {...p}><path d="M6 19v2"/><path d="M18 19v2"/><path d="M5 10V6a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v4"/><path d="M3 10h18"/><path d="M5 19h14a2 2 0 0 0 2-2v-7H3v7a2 2 0 0 0 2 2z"/></Icon>,
  table: (p) => <Icon {...p}><path d="M3 9h18"/><path d="M3 9v10"/><path d="M21 9v10"/><path d="M9 9v5"/><path d="M15 9v5"/><path d="M3 14h18"/><path d="M5 6h14a2 2 0 0 1 2 2v0H3v0a2 2 0 0 1 2-2z"/></Icon>,
  heart2: (p) => <Icon {...p}><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"/></Icon>,
  mic: (p) => <Icon {...p}><rect x="9" y="2" width="6" height="11" rx="3"/><path d="M19 10a7 7 0 0 1-14 0"/><path d="M12 17v4"/><path d="M8 21h8"/></Icon>,
  briefcase: (p) => <Icon {...p}><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/></Icon>,
  clock2: (p) => <Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></Icon>,
  ban: (p) => <Icon {...p}><circle cx="12" cy="12" r="9"/><path d="m5.5 5.5 13 13"/></Icon>,
  key: (p) => <Icon {...p}><circle cx="7.5" cy="15.5" r="3.5"/><path d="m10 13 9-9"/><path d="m15 8 3 3"/><path d="m13 10 3 3"/></Icon>,
  shield: (p) => <Icon {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></Icon>,
  shieldCheck: (p) => <Icon {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></Icon>,
  link: (p) => <Icon {...p}><path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.41 1.41"/><path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.41-1.41"/></Icon>,
  globe: (p) => <Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18"/><path d="M12 3a14 14 0 0 0 0 18"/></Icon>,
  palette: (p) => <Icon {...p}><circle cx="7.5" cy="11" r="1.2" fill="currentColor"/><circle cx="11.5" cy="7" r="1.2" fill="currentColor"/><circle cx="16.5" cy="9" r="1.2" fill="currentColor"/><circle cx="17" cy="14.5" r="1.2" fill="currentColor"/><path d="M12 22a10 10 0 1 1 10-10c0 2.5-2 3.5-4 3.5-1.5 0-3 1-3 2.5s1 4-3 4z"/></Icon>,
  copy: (p) => <Icon {...p}><rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></Icon>,
  info: (p) => <Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M12 8h.01"/><path d="M11 12h1v5h1"/></Icon>,
  refresh: (p) => <Icon {...p}><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/></Icon>,
  database: (p) => <Icon {...p}><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></Icon>,
  trash: (p) => <Icon {...p}><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></Icon>,
  edit: (p) => <Icon {...p}><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"/></Icon>,
  phone: (p) => <Icon {...p}><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></Icon>,
  qr: (p) => <Icon {...p}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3z"/><path d="M20 14v3"/><path d="M14 20h3"/><path d="M20 20v.01"/></Icon>,
};

window.I = I;
