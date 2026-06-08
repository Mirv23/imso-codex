/* ===== Settings View ===== */

const SETTINGS_TABS = [
  { id: 'general',       label: 'Général',              icon: I.building,    group: 'Organisation' },
  { id: 'branding',      label: 'Marque & apparence',   icon: I.palette,     group: 'Organisation' },
  { id: 'team',          label: 'Équipe & rôles',       icon: I.users,       group: 'Organisation' },
  { id: 'payments',      label: 'Paiements',            icon: I.cash,        group: 'Plateforme' },
  { id: 'room',          label: 'Salle & tarifs',       icon: I.chair,       group: 'Plateforme' },
  { id: 'notifications', label: 'Notifications',       icon: I.bell,        group: 'Plateforme' },
  { id: 'security',      label: 'Sécurité',             icon: I.shield,      group: 'Système' },
  { id: 'integrations',  label: 'Intégrations & API',   icon: I.link,        group: 'Système' },
  { id: 'backup',        label: 'Sauvegardes',          icon: I.database,    group: 'Système' },
  { id: 'danger',        label: 'Zone de danger',       icon: I.ban,         group: 'Système', danger: true },
];

/* ---------- Reusable bricks ---------- */
function Section({ title, sub, icon: Ic, actions, children }) {
  return (
    <div className="card fade-in d1" style={{ marginBottom: 18 }}>
      <div className="card-head" style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {Ic && (
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'var(--primary-light)', color: 'var(--primary)',
              display: 'grid', placeItems: 'center',
            }}><Ic size={18}/></div>
          )}
          <div>
            <div className="card-title">{title}</div>
            {sub && <div className="card-sub">{sub}</div>}
          </div>
        </div>
        {actions && <div className="stack">{actions}</div>}
      </div>
      <div style={{ padding: 22 }}>{children}</div>
    </div>
  );
}

function FieldRow({ label, hint, children, span = 1 }) {
  return (
    <div className="field" style={{ gridColumn: `span ${span}`, marginBottom: 0 }}>
      <label>{label}</label>
      {children}
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}

function ToggleRow({ title, desc, defaultOn = false, badge }) {
  const [on, setOn] = useState(defaultOn);
  return (
    <div className="toggle-row" style={{ marginBottom: 0 }}>
      <div className="meta" style={{ flex: 1, minWidth: 0 }}>
        <div className="t" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {title}
          {badge && <span className="pill gray" style={{ fontSize: 10 }}>{badge}</span>}
        </div>
        {desc && <div className="s">{desc}</div>}
      </div>
      <label className="toggle">
        <input type="checkbox" checked={on} onChange={() => setOn(v => !v)}/>
        <span className="track"></span>
      </label>
    </div>
  );
}

function Grid({ cols = 2, gap = 18, children, style }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${cols}, 1fr)`,
      gap, ...style,
    }}>{children}</div>
  );
}

/* ---------- 1. Général ---------- */
function PaneGeneral() {
  return (
    <>
      <Section
        title="Identité de l'institution"
        sub="Ces informations apparaissent sur les reçus, les certificats et les emails."
        icon={I.building}
        actions={<button className="btn primary sm"><I.check size={14}/> Enregistrer</button>}
      >
        <Grid cols={2}>
          <FieldRow label="Nom officiel">
            <input className="input" defaultValue="Institut Méthodiste de Sciences et d'Œuvres — IMSO Haïti"/>
          </FieldRow>
          <FieldRow label="Nom court (affiché)">
            <input className="input" defaultValue="IMSO Haïti"/>
          </FieldRow>
          <FieldRow label="Slogan">
            <input className="input" defaultValue="Former, équiper, envoyer."/>
          </FieldRow>
          <FieldRow label="Site web public">
            <div className="input-prefix">
              <span className="pre">https://</span>
              <input className="input" defaultValue="imso.ht"/>
            </div>
          </FieldRow>
          <FieldRow label="Email de contact">
            <input className="input" type="email" defaultValue="contact@imso.ht"/>
          </FieldRow>
          <FieldRow label="Téléphone">
            <input className="input" defaultValue="+509 2812 4500"/>
          </FieldRow>
          <FieldRow label="Adresse" span={2}>
            <input className="input" defaultValue="12, Rue Capois · Pacot · Port-au-Prince · Haïti"/>
            <div className="hint">Géo-localisé : 18.5392° N, 72.3370° W · Apparait sur la fiche Google Maps des paiements.</div>
          </FieldRow>
        </Grid>
      </Section>

      <Section
        title="Région & format"
        sub="Devise, fuseau et langues utilisés par défaut sur toute la plateforme."
        icon={I.globe}
      >
        <Grid cols={3}>
          <FieldRow label="Langue par défaut">
            <select className="select" defaultValue="fr">
              <option value="fr">🇫🇷 Français</option>
              <option value="ht">🇭🇹 Kreyòl ayisyen</option>
              <option value="en">🇺🇸 English</option>
            </select>
          </FieldRow>
          <FieldRow label="Devise">
            <select className="select" defaultValue="HTG">
              <option value="HTG">HTG — Gourde haïtienne</option>
              <option value="USD">USD — Dollar US</option>
            </select>
          </FieldRow>
          <FieldRow label="Fuseau horaire">
            <select className="select" defaultValue="PAP">
              <option value="PAP">America/Port-au-Prince (UTC−05:00)</option>
              <option value="NY">America/New_York (UTC−05:00)</option>
            </select>
          </FieldRow>
          <FieldRow label="Format de date">
            <select className="select" defaultValue="long">
              <option value="long">21 mai 2026</option>
              <option value="iso">2026-05-21</option>
              <option value="us">May 21, 2026</option>
            </select>
          </FieldRow>
          <FieldRow label="Premier jour de semaine">
            <select className="select" defaultValue="lun">
              <option value="lun">Lundi</option><option value="dim">Dimanche</option>
            </select>
          </FieldRow>
          <FieldRow label="Taux de change manuel" hint="Utilisé pour les exports en USD.">
            <div className="input-prefix">
              <span className="pre">1 USD =</span>
              <input className="input mono" defaultValue="132.50 HTG"/>
            </div>
          </FieldRow>
        </Grid>

        <div style={{ marginTop: 20, padding: 14, background: '#F0F8F3', borderRadius: 10, display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ color: 'var(--primary)', marginTop: 2 }}><I.info size={18}/></div>
          <div style={{ fontSize: 12.5, lineHeight: 1.5 }}>
            <b>Trilingue :</b> les apprenants peuvent basculer entre <b>Français</b>, <b>Kreyòl</b> et <b>English</b> dans leur profil. Les certificats et reçus sont générés dans la langue choisie par l'apprenant.
          </div>
        </div>
      </Section>

      <Section title="Année académique" sub="Définit les périodes pour les cohortes et la facturation." icon={I.calendar}>
        <Grid cols={4}>
          <FieldRow label="Année en cours"><input className="input mono" defaultValue="2025 — 2026"/></FieldRow>
          <FieldRow label="Début du trimestre"><input className="input" defaultValue="3 février 2026"/></FieldRow>
          <FieldRow label="Fin du trimestre"><input className="input" defaultValue="15 juin 2026"/></FieldRow>
          <FieldRow label="Semaine de pause"><input className="input" defaultValue="6–13 avril 2026"/></FieldRow>
        </Grid>
      </Section>
    </>
  );
}

/* ---------- 2. Marque ---------- */
function PaneBranding() {
  const [color, setColor] = useState('#2D6A4F');
  const palette = [
    { name: 'Vert IMSO',  v: '#2D6A4F' },
    { name: 'Sapin',      v: '#1B4332' },
    { name: 'Ocre',       v: '#C2410C' },
    { name: 'Indigo',     v: '#3730A3' },
    { name: 'Vin',        v: '#9F1239' },
    { name: 'Anthracite', v: '#1F2937' },
  ];
  return (
    <>
      <Section title="Logo & favicon" sub="Téléchargez vos visuels — utilisés sur le site, l'app mobile et les certificats." icon={I.palette}>
        <Grid cols={3}>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 6 }}>Logo principal</label>
            <div className="dropzone" style={{ padding: 18 }}>
              <div style={{
                width: 80, height: 80, borderRadius: 14,
                background: 'linear-gradient(135deg, #2D6A4F, #3a8862)',
                margin: '0 auto 10px', display: 'grid', placeItems: 'center',
                color: '#fff', fontWeight: 800, fontSize: 22, letterSpacing: '0.04em',
              }}>IM</div>
              <div className="dropzone-title">imso-logo.svg</div>
              <div className="dropzone-sub">512 × 512 · 14 Ko</div>
              <button className="btn sm" style={{ marginTop: 10 }}><I.upload size={13}/> Remplacer</button>
            </div>
          </div>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 6 }}>Logo monochrome</label>
            <div className="dropzone" style={{ padding: 18 }}>
              <div style={{
                width: 80, height: 80, borderRadius: 14,
                background: '#111827', margin: '0 auto 10px',
                display: 'grid', placeItems: 'center', color: '#fff',
                fontWeight: 800, fontSize: 22, letterSpacing: '0.04em',
              }}>IM</div>
              <div className="dropzone-title">imso-mono.svg</div>
              <div className="dropzone-sub">Pour fonds clairs · 11 Ko</div>
              <button className="btn sm" style={{ marginTop: 10 }}><I.upload size={13}/> Remplacer</button>
            </div>
          </div>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 6 }}>Favicon</label>
            <div className="dropzone" style={{ padding: 18 }}>
              <div style={{
                width: 80, height: 80, borderRadius: 14,
                background: '#FAFBFC', border: '1px solid var(--border)',
                margin: '0 auto 10px', display: 'grid', placeItems: 'center',
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 6,
                  background: 'var(--primary)', color: '#fff',
                  display: 'grid', placeItems: 'center',
                  fontWeight: 800, fontSize: 13,
                }}>IM</div>
              </div>
              <div className="dropzone-title">favicon.ico</div>
              <div className="dropzone-sub">32 × 32 · 2 Ko</div>
              <button className="btn sm" style={{ marginTop: 10 }}><I.upload size={13}/> Remplacer</button>
            </div>
          </div>
        </Grid>
      </Section>

      <Section title="Couleurs de marque" sub="La couleur primaire est utilisée pour les boutons, liens et accents.">
        <Grid cols={2} gap={28}>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 10 }}>Couleur primaire</label>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {palette.map(p => (
                <button key={p.v} onClick={() => setColor(p.v)} style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '6px 10px 6px 6px',
                  border: color === p.v ? `1.5px solid ${p.v}` : '1.5px solid var(--border)',
                  borderRadius: 999, background: '#fff', cursor: 'pointer',
                  fontSize: 12, fontWeight: 600,
                }}>
                  <span style={{ width: 22, height: 22, borderRadius: 999, background: p.v, display: 'inline-block' }}/>
                  {p.name}
                </button>
              ))}
            </div>
            <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="color" value={color} onChange={e => setColor(e.target.value)} style={{ width: 44, height: 36, border: '1px solid var(--border)', borderRadius: 8, padding: 2, background: '#fff' }}/>
              <input className="input mono" value={color.toUpperCase()} onChange={e => setColor(e.target.value)} style={{ width: 130 }}/>
              <span className="pill green dot">AAA · Contraste 7.2</span>
            </div>
          </div>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 10 }}>Aperçu</label>
            <div style={{
              background: '#fff', border: '1px solid var(--border)', borderRadius: 12,
              padding: 18, display: 'flex', flexDirection: 'column', gap: 12,
            }}>
              <div style={{
                background: color, color: '#fff', padding: '10px 14px',
                borderRadius: 9, fontSize: 13, fontWeight: 600, display: 'inline-flex',
                alignItems: 'center', gap: 7, alignSelf: 'flex-start',
              }}><I.plus size={14}/> Bouton primaire</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{
                  fontSize: 11.5, fontWeight: 600, color,
                  background: `${color}1a`, padding: '3px 9px',
                  borderRadius: 999,
                }}>● Pill primaire</span>
                <a style={{ fontSize: 13, color, fontWeight: 600 }}>Un lien</a>
              </div>
              <div style={{ height: 6, background: '#F3F4F6', borderRadius: 999, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: '72%', background: color, borderRadius: 999 }}/>
              </div>
            </div>
          </div>
        </Grid>
      </Section>

      <Section title="Polices" sub="Utilisées dans toute l'application et sur les certificats PDF.">
        <Grid cols={2}>
          <FieldRow label="Police de titre">
            <select className="select" defaultValue="inter">
              <option value="inter">Inter (par défaut)</option>
              <option value="dm">DM Serif Display</option>
              <option value="manrope">Manrope</option>
            </select>
            <div style={{ marginTop: 10, padding: '14px 16px', background: '#FAFBFC', border: '1px solid var(--border-soft)', borderRadius: 10, fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>
              Former, équiper, envoyer.
            </div>
          </FieldRow>
          <FieldRow label="Police de corps">
            <select className="select" defaultValue="inter">
              <option value="inter">Inter (par défaut)</option>
              <option value="lora">Lora</option>
              <option value="ibm">IBM Plex Sans</option>
            </select>
            <div style={{ marginTop: 10, padding: '14px 16px', background: '#FAFBFC', border: '1px solid var(--border-soft)', borderRadius: 10, fontSize: 13.5, lineHeight: 1.55 }}>
              L'enseignement de la doctrine biblique au service de l'Église haïtienne contemporaine.
            </div>
          </FieldRow>
        </Grid>
      </Section>
    </>
  );
}

/* ---------- 3. Équipe ---------- */
const TEAM = [
  { name: 'Pasteur Joseph',    email: 'joseph@imso.ht',     role: 'Super-administrateur', last: 'En ligne', avatar: 'PJ', tint: 'green',  active: true,  twofa: true  },
  { name: 'Marie-Claude Joseph', email: 'marieclaude@imso.ht', role: 'Administrateur',     last: 'il y a 12 min', avatar: 'MC', tint: 'rose', active: true,  twofa: true  },
  { name: 'Wilkenson Auguste',  email: 'wilkenson@imso.ht', role: 'Comptable',            last: 'il y a 3 h',    avatar: 'WA', tint: 'blue', active: true,  twofa: false },
  { name: 'Roselène Bélizaire', email: 'roselene@imso.ht',  role: 'Pédagogue',            last: 'il y a 1 j',    avatar: 'RB', tint: 'amber',active: true,  twofa: true  },
  { name: 'Frantz Cadet',       email: 'frantz@imso.ht',    role: 'Modérateur contenu',   last: 'il y a 5 j',    avatar: 'FC', tint: 'purple',active: false, twofa: false },
];

const ROLES = [
  { id: 'super', name: 'Super-administrateur', count: 1, perms: ['Tout faire', 'Facturation', 'Suppression définitive'] },
  { id: 'admin', name: 'Administrateur',       count: 1, perms: ['Gérer membres', 'Gérer cours', 'Gérer paiements'] },
  { id: 'compt', name: 'Comptable',            count: 1, perms: ['Voir paiements', 'Exporter CSV', 'Réconciliation'] },
  { id: 'peda',  name: 'Pédagogue',            count: 1, perms: ['Publier cours', 'Modérer commentaires', 'Voir progression'] },
  { id: 'mod',   name: 'Modérateur contenu',   count: 1, perms: ['Modérer commentaires', 'Voir membres'] },
];

function PaneTeam() {
  return (
    <>
      <Section
        title="Équipe administrative"
        sub="5 membres · Toute personne ayant un accès à ce dashboard."
        icon={I.users}
        actions={<button className="btn primary sm"><I.plus size={14}/> Inviter un membre</button>}
      >
        <table className="table" style={{ margin: '-22px -22px -22px', width: 'calc(100% + 44px)' }}>
          <thead>
            <tr>
              <th>Membre</th>
              <th>Rôle</th>
              <th>2FA</th>
              <th>Dernière activité</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody className="row-anim">
            {TEAM.map((m, i) => (
              <tr key={m.email} style={{ animationDelay: `${0.03 * i}s` }}>
                <td>
                  <div className="name-cell">
                    <div className={`avatar sm ${m.tint}`}>{m.avatar}</div>
                    <div className="name-meta">
                      <div className="nm">{m.name}</div>
                      <div className="em">{m.email}</div>
                    </div>
                  </div>
                </td>
                <td><span className="pill gray">{m.role}</span></td>
                <td>
                  {m.twofa
                    ? <span className="pill green dot">Activée</span>
                    : <span className="pill amber dot">Désactivée</span>}
                </td>
                <td>
                  <div style={{ fontSize: 12.5 }}>{m.last}</div>
                  {!m.active && <div style={{ fontSize: 10.5, color: 'var(--muted)' }}>Compte suspendu</div>}
                </td>
                <td style={{ textAlign: 'right' }}>
                  <div className="stack" style={{ justifyContent: 'flex-end' }}>
                    <button className="btn sm ghost"><I.edit size={13}/></button>
                    <button className="btn sm ghost"><I.key size={13}/></button>
                    <button className="btn sm ghost"><I.more size={14}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Rôles & permissions" sub="Définissez ce que chaque type de compte peut faire." icon={I.shieldCheck}
        actions={<button className="btn sm"><I.plus size={13}/> Nouveau rôle</button>}>
        <Grid cols={2} gap={14}>
          {ROLES.map(r => (
            <div key={r.id} style={{
              border: '1px solid var(--border)', borderRadius: 12,
              padding: 16, background: '#FAFBFC',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <div style={{ fontSize: 14, fontWeight: 700 }}>{r.name}</div>
                <span className="pill gray">{r.count} membre{r.count > 1 ? 's' : ''}</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {r.perms.map(p => (
                  <span key={p} style={{
                    fontSize: 11, color: 'var(--text)',
                    background: '#fff', border: '1px solid var(--border-soft)',
                    padding: '3px 9px', borderRadius: 999,
                  }}>{p}</span>
                ))}
              </div>
              <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                <button className="btn sm"><I.edit size={12}/> Modifier</button>
                {r.id !== 'super' && <button className="btn sm ghost" style={{ color: 'var(--danger)' }}><I.trash size={12}/></button>}
              </div>
            </div>
          ))}
        </Grid>
      </Section>
    </>
  );
}

/* ---------- 4. Paiements ---------- */
function PanePayments() {
  return (
    <>
      <Section
        title="Opérateurs de paiement"
        sub="Activez et configurez les API de chaque opérateur haïtien."
        icon={I.cash}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {PAY_METHODS.map(m => (
            <div key={m.id} style={{
              display: 'grid', gridTemplateColumns: 'auto 1fr auto auto auto',
              gap: 14, alignItems: 'center',
              padding: '14px 16px',
              border: '1px solid var(--border-soft)', borderRadius: 12,
              background: '#FAFBFC',
            }}>
              <MethodLogo method={m} size={40} square/>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700 }}>{m.name}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>{m.sub}</div>
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--muted)' }}>
                Frais opérateur<br/>
                <span style={{ color: m.color, fontWeight: 700, fontSize: 13 }}>{m.fee}</span>
              </div>
              <span className={`pill ${m.id === 'cash' ? 'gray' : 'green'} dot`}>
                {m.id === 'cash' ? 'Manuel' : 'Connecté'}
              </span>
              <div className="stack">
                <button className="btn sm"><I.key size={13}/> Clés API</button>
                <label className="toggle">
                  <input type="checkbox" defaultChecked/>
                  <span className="track"></span>
                </label>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Identifiants API MonCash" sub="Identifiants OAuth obtenus auprès de Digicel." icon={I.key}
        actions={<span className="pill green dot">Sandbox</span>}>
        <Grid cols={2}>
          <FieldRow label="Client ID">
            <div className="input-prefix">
              <span className="pre">PROD</span>
              <input className="input mono" defaultValue="cli_5fa3d8e2c4b9a1f7e8d3"/>
            </div>
          </FieldRow>
          <FieldRow label="Client Secret">
            <input className="input mono" type="password" defaultValue="sk_live_••••••••••••••••3df9"/>
          </FieldRow>
          <FieldRow label="URL Webhook" hint="Endpoint qui reçoit les confirmations de paiement.">
            <div className="input-prefix">
              <span className="pre">POST</span>
              <input className="input mono" defaultValue="https://api.imso.ht/v1/webhooks/moncash"/>
            </div>
          </FieldRow>
          <FieldRow label="Environnement">
            <select className="select" defaultValue="prod">
              <option value="prod">Production</option>
              <option value="sand">Sandbox</option>
            </select>
          </FieldRow>
        </Grid>

        <div style={{ marginTop: 16, padding: 14, background: '#FEF3C7', borderRadius: 10, display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ color: '#B45309', marginTop: 2 }}><I.shield size={18}/></div>
          <div style={{ fontSize: 12.5, color: '#92400E', lineHeight: 1.5 }}>
            <b>Ne partagez jamais ces clés.</b> Elles donnent un accès total à votre compte marchand MonCash. Régénérez-les immédiatement si elles ont été exposées.
          </div>
        </div>

        <div className="stack" style={{ marginTop: 14, justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn sm"><I.refresh size={13}/> Tester la connexion</button>
          <button className="btn sm"><I.refresh size={13}/> Régénérer secret</button>
        </div>
      </Section>

      <Section title="Facturation & reçus" sub="Modèles de reçus automatiques envoyés à chaque transaction.">
        <Grid cols={2}>
          <FieldRow label="Préfixe des reçus">
            <input className="input mono" defaultValue="IMSO-2026-"/>
          </FieldRow>
          <FieldRow label="Numéro fiscal (NIF)">
            <input className="input mono" defaultValue="009-345-872-1"/>
          </FieldRow>
          <FieldRow label="TVA applicable" hint="0% pour les institutions reconnues d'utilité publique.">
            <div className="input-prefix">
              <span className="pre">%</span>
              <input className="input mono" defaultValue="0"/>
            </div>
          </FieldRow>
          <FieldRow label="Délai de remboursement (jours)">
            <input className="input mono" defaultValue="14"/>
          </FieldRow>
          <FieldRow label="Mention bas de page" span={2}>
            <textarea className="textarea" defaultValue="Merci pour votre confiance. Ce reçu fait foi de paiement intégral. Pour toute question, écrivez à comptabilite@imso.ht."/>
          </FieldRow>
        </Grid>
      </Section>
    </>
  );
}

/* ---------- 5. Salle ---------- */
function PaneRoom() {
  const slots = [
    { from: '06:00', to: '12:00', label: 'Matinée', rate: 3500 },
    { from: '12:00', to: '18:00', label: 'Après-midi', rate: 3750 },
    { from: '18:00', to: '23:00', label: 'Soirée', rate: 4500 },
    { from: '00:00', to: '06:00', label: 'Nuit (mariages)', rate: 6000 },
  ];
  return (
    <>
      <Section
        title="Tarification de la salle"
        sub="Salle Bétharam · 320 places · Climatisée · Avec scène et sonorisation"
        icon={I.chair}
      >
        <Grid cols={3}>
          <FieldRow label="Tarif de base (par heure)">
            <div className="input-prefix">
              <span className="pre">HTG</span>
              <input className="input mono" defaultValue="3 750"/>
            </div>
          </FieldRow>
          <FieldRow label="Tarif weekend (+%)">
            <div className="input-prefix">
              <span className="pre">+%</span>
              <input className="input mono" defaultValue="25"/>
            </div>
          </FieldRow>
          <FieldRow label="Caution requise (HTG)">
            <input className="input mono" defaultValue="15 000"/>
          </FieldRow>
          <FieldRow label="Durée minimum (heures)">
            <input className="input mono" defaultValue="2"/>
          </FieldRow>
          <FieldRow label="Durée maximum (heures)">
            <input className="input mono" defaultValue="12"/>
          </FieldRow>
          <FieldRow label="Délai de préavis (jours)">
            <input className="input mono" defaultValue="3"/>
          </FieldRow>
        </Grid>

        <div style={{ marginTop: 22 }}>
          <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>Tarifs par tranche horaire</span>
            <button className="btn sm ghost"><I.plus size={13}/> Ajouter une tranche</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {slots.map((s, i) => (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '110px 1fr 1fr 1fr auto',
                gap: 12, alignItems: 'center',
                padding: '12px 14px',
                background: '#FAFBFC', border: '1px solid var(--border-soft)',
                borderRadius: 10,
              }}>
                <div className="mono" style={{ fontSize: 13, fontWeight: 700 }}>{s.from} → {s.to}</div>
                <div style={{ fontSize: 13 }}>{s.label}</div>
                <div className="mono" style={{ fontSize: 13, fontWeight: 600 }}>{s.rate.toLocaleString('fr-FR')} HTG/h</div>
                <div style={{ height: 6, background: '#F3F4F6', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${(s.rate / 6000) * 100}%`, background: 'var(--primary)', borderRadius: 999 }}/>
                </div>
                <button className="btn sm ghost"><I.edit size={13}/></button>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section title="Disponibilité & règles" sub="Jours et heures où la salle peut être réservée par les membres.">
        <Grid cols={2}>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 8 }}>Jours d'ouverture</label>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map((d, i) => (
                <label key={d} style={{
                  padding: '7px 12px',
                  border: i === 6 ? '1px solid var(--border)' : '1.5px solid var(--primary)',
                  background: i === 6 ? '#fff' : 'var(--primary-light)',
                  color: i === 6 ? 'var(--muted)' : 'var(--primary)',
                  borderRadius: 9, fontSize: 12.5, fontWeight: 600, cursor: 'pointer',
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                }}>
                  <input type="checkbox" defaultChecked={i !== 6} style={{ display: 'none' }}/>
                  {i !== 6 && <I.check size={12}/>}
                  {d}
                </label>
              ))}
            </div>
            <div className="hint" style={{ marginTop: 8 }}>Dimanche réservé aux cultes IMSO uniquement.</div>
          </div>
          <div>
            <label style={{ fontSize: 12.5, fontWeight: 600, display: 'block', marginBottom: 8 }}>Plage horaire générale</label>
            <div className="stack">
              <input className="input mono" defaultValue="06:00" style={{ width: 90 }}/>
              <span style={{ color: 'var(--muted)' }}>→</span>
              <input className="input mono" defaultValue="23:00" style={{ width: 90 }}/>
            </div>
            <div className="hint" style={{ marginTop: 8 }}>Mariages et veillées : autorisations spéciales sur demande.</div>
          </div>
        </Grid>

        <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <ToggleRow defaultOn title="Confirmation manuelle des réservations" desc="Les nouvelles demandes doivent être validées par un admin."/>
          <ToggleRow defaultOn title="Paiement obligatoire à la réservation" desc="50% d'acompte exigé avant validation."/>
          <ToggleRow title="Accepter les annulations gratuites < 48h" desc="Sinon, la caution est retenue."/>
          <ToggleRow defaultOn title="Bloquer les réservations multiples le même jour" desc="Une seule réservation par créneau."/>
        </div>
      </Section>
    </>
  );
}

/* ---------- 6. Notifications ---------- */
function PaneNotifications() {
  const channels = [
    { title: 'Email — comptabilite@imso.ht',  desc: 'Reçus, factures, rappels',         on: true,  ico: I.mail,  badge: 'Resend' },
    { title: 'SMS — Twilio',                   desc: 'Confirmations, codes 2FA',         on: true,  ico: I.phone, badge: 'Twilio' },
    { title: 'Push (App mobile)',              desc: 'Notifications iOS & Android',      on: true,  ico: I.bell,  badge: 'OneSignal' },
    { title: 'WhatsApp Business',              desc: 'Annonces de cours',                 on: false, ico: I.phone, badge: 'Meta' },
  ];
  const triggers = [
    { t: 'Nouveau membre inscrit',         email: true,  sms: false, push: true,  group: 'Membres' },
    { t: 'Paiement réussi',                 email: true,  sms: true,  push: true,  group: 'Paiements' },
    { t: 'Paiement échoué',                 email: true,  sms: true,  push: true,  group: 'Paiements' },
    { t: 'Remboursement émis',              email: true,  sms: false, push: true,  group: 'Paiements' },
    { t: 'Réservation de salle confirmée',  email: true,  sms: true,  push: true,  group: 'Salle' },
    { t: 'Rappel de réservation (J-1)',     email: false, sms: true,  push: true,  group: 'Salle' },
    { t: 'Nouveau cours publié',            email: true,  sms: false, push: true,  group: 'Cours' },
    { t: 'Cours terminé · Certificat prêt', email: true,  sms: false, push: true,  group: 'Cours' },
    { t: 'Agent IA — lead qualifié',         email: true,  sms: false, push: false, group: 'IA' },
  ];
  return (
    <>
      <Section title="Canaux de notification" sub="Activez et configurez les services qui envoient les notifications." icon={I.bell}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {channels.map((c, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: 'auto 1fr auto auto',
              gap: 14, alignItems: 'center',
              padding: '14px 16px',
              background: '#FAFBFC', border: '1px solid var(--border-soft)',
              borderRadius: 12,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: '#fff', border: '1px solid var(--border)',
                display: 'grid', placeItems: 'center', color: 'var(--primary)',
              }}><c.ico size={18}/></div>
              <div>
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{c.title}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>{c.desc}</div>
              </div>
              <span className="pill gray mono" style={{ fontSize: 10 }}>{c.badge}</span>
              <label className="toggle">
                <input type="checkbox" defaultChecked={c.on}/>
                <span className="track"></span>
              </label>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Déclencheurs" sub="Choisissez quels événements génèrent une notification, et par quel canal.">
        <table className="table" style={{ margin: '-22px -22px -22px', width: 'calc(100% + 44px)' }}>
          <thead>
            <tr>
              <th>Événement</th>
              <th style={{ width: 110 }}>Catégorie</th>
              <th style={{ width: 80, textAlign: 'center' }}>Email</th>
              <th style={{ width: 80, textAlign: 'center' }}>SMS</th>
              <th style={{ width: 80, textAlign: 'center' }}>Push</th>
            </tr>
          </thead>
          <tbody>
            {triggers.map((t, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 500 }}>{t.t}</td>
                <td><span className="pill gray">{t.group}</span></td>
                {['email','sms','push'].map(k => (
                  <td key={k} style={{ textAlign: 'center' }}>
                    <label className="toggle" style={{ display: 'inline-flex' }}>
                      <input type="checkbox" defaultChecked={t[k]}/>
                      <span className="track"></span>
                    </label>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </>
  );
}

/* ---------- 7. Sécurité ---------- */
function PaneSecurity() {
  const sessions = [
    { dev: 'MacBook Pro · Safari',          loc: 'Pétion-Ville · Haïti',   ip: '190.115.182.41',  when: 'Maintenant',   current: true  },
    { dev: 'iPhone 15 · App IMSO',          loc: 'Port-au-Prince · Haïti', ip: '190.115.182.41',  when: 'il y a 8 min', current: false },
    { dev: 'Windows 11 · Chrome',           loc: 'Cap-Haïtien · Haïti',    ip: '190.115.220.18',  when: 'il y a 2 j',   current: false },
    { dev: 'Pixel 8 · App IMSO',            loc: 'Miami · USA',            ip: '73.181.40.122',   when: 'il y a 6 j',   current: false, suspicious: true },
  ];
  const audit = [
    { who: 'Pasteur Joseph',     what: 'Modifié le tarif de la salle (3 500 → 3 750 HTG)', when: '21 mai · 10:14', tag: 'Salle' },
    { who: 'Marie-Claude Joseph',what: 'Approuvé l\'inscription de 12 nouveaux apprenants', when: '21 mai · 09:02', tag: 'Membres' },
    { who: 'Wilkenson Auguste',  what: 'Exporté la table Transactions en CSV',              when: '20 mai · 18:40', tag: 'Paiements' },
    { who: 'Pasteur Joseph',     what: 'Régénéré le secret API MonCash',                    when: '19 mai · 14:22', tag: 'API' },
    { who: 'Roselène Bélizaire', what: 'Publié le cours "Théologie pratique I"',            when: '18 mai · 11:08', tag: 'Cours' },
  ];
  return (
    <>
      <Section title="Authentification à deux facteurs" sub="Une couche de sécurité supplémentaire pour tous les admins." icon={I.shieldCheck}>
        <div style={{
          padding: 20, background: 'linear-gradient(135deg, #F0F8F3, #FDF7EE)',
          borderRadius: 12, display: 'grid', gridTemplateColumns: '1fr auto',
          gap: 22, alignItems: 'center',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span className="pill green dot">Activé</span>
              <span style={{ fontSize: 13.5, fontWeight: 600 }}>4 admins sur 5 utilisent la 2FA</span>
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', lineHeight: 1.5 }}>
              Application d'authentification recommandée : <b>Google Authenticator</b>, <b>1Password</b> ou <b>Authy</b>. SMS disponible en secours.
            </div>
            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <button className="btn sm primary"><I.shield size={13}/> Imposer à toute l'équipe</button>
              <button className="btn sm"><I.qr size={13}/> Mon QR code</button>
            </div>
          </div>
          <div style={{
            width: 110, height: 110, background: '#fff',
            border: '1px solid var(--border)', borderRadius: 12,
            display: 'grid', placeItems: 'center', color: 'var(--text)',
          }}>
            <I.qr size={64}/>
          </div>
        </div>
      </Section>

      <Section title="Politique de mot de passe" sub="Règles appliquées à tous les comptes (admins et apprenants).">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <ToggleRow defaultOn title="Minimum 10 caractères" desc="Aujourd'hui : 10 caractères"/>
          <ToggleRow defaultOn title="Exiger un chiffre et un symbole"/>
          <ToggleRow defaultOn title="Expiration tous les 90 jours" desc="Les mots de passe doivent être changés régulièrement."/>
          <ToggleRow title="Bloquer les mots de passe compromis" badge="Have I Been Pwned"/>
          <ToggleRow defaultOn title="Verrouillage après 5 tentatives ratées" desc="Compte bloqué 30 min."/>
        </div>
      </Section>

      <Section title="Sessions actives" sub="Appareils actuellement connectés à votre compte." icon={I.key}
        actions={<button className="btn sm" style={{ color: 'var(--danger)' }}><I.ban size={13}/> Tout déconnecter</button>}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {sessions.map((s, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: '1fr auto auto auto',
              gap: 14, alignItems: 'center',
              padding: '12px 14px',
              background: s.suspicious ? '#FEF2F2' : '#FAFBFC',
              border: s.suspicious ? '1px solid #FECACA' : '1px solid var(--border-soft)',
              borderRadius: 10,
            }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                  {s.dev}
                  {s.current && <span className="pill green">Cette session</span>}
                  {s.suspicious && <span className="pill red dot">Suspecte</span>}
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>
                  <I.pin size={11} style={{ verticalAlign: '-2px', marginRight: 3 }}/>{s.loc}
                  <span className="mono" style={{ marginLeft: 10 }}>{s.ip}</span>
                </div>
              </div>
              <div className="mono" style={{ fontSize: 11.5, color: 'var(--muted)' }}>{s.when}</div>
              {!s.current && <button className="btn sm ghost" style={{ color: 'var(--danger)' }}>Déconnecter</button>}
            </div>
          ))}
        </div>
      </Section>

      <Section title="Journal d'audit" sub="Les 30 derniers jours d'activité administrative." icon={I.fileText}
        actions={<button className="btn sm"><I.download size={13}/> Exporter</button>}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {audit.map((a, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: 'auto 1fr auto auto',
              gap: 12, alignItems: 'center',
              padding: '12px 4px',
              borderBottom: i < audit.length - 1 ? '1px solid var(--border-soft)' : 'none',
            }}>
              <div className="avatar xs">{a.who.split(' ').map(n => n[0]).slice(0,2).join('')}</div>
              <div>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{a.who}</span>
                <span style={{ fontSize: 13, color: 'var(--muted)', marginLeft: 6 }}>{a.what}</span>
              </div>
              <span className="pill gray">{a.tag}</span>
              <span className="mono" style={{ fontSize: 11.5, color: 'var(--muted)' }}>{a.when}</span>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}

/* ---------- 8. Intégrations & API ---------- */
function PaneIntegrations() {
  const integrations = [
    { name: 'Claude (Anthropic)',  desc: 'Agents IA · Création de contenu & qualification de leads', status: 'connected', tag: 'IA',        badge: 'Haiku 4.5' },
    { name: 'Resend',              desc: 'Envoi des emails transactionnels',                          status: 'connected', tag: 'Email',     badge: '1 240/mois' },
    { name: 'Twilio',              desc: 'SMS et appels vocaux',                                       status: 'connected', tag: 'SMS',       badge: 'HT +509' },
    { name: 'OneSignal',           desc: 'Notifications push iOS & Android',                          status: 'connected', tag: 'Push',      badge: '1.2k devices' },
    { name: 'Cloudinary',          desc: 'Hébergement vidéo et image (cours)',                         status: 'connected', tag: 'Stockage',  badge: '128 Go' },
    { name: 'Google Calendar',     desc: 'Synchronisation des réservations de salle',                  status: 'connected', tag: 'Calendrier',badge: 'comptabilite@imso.ht' },
    { name: 'WhatsApp Business',   desc: 'Annonces et rappels via WhatsApp',                          status: 'disconnected', tag: 'Messagerie', badge: '—' },
    { name: 'Mailchimp',           desc: 'Campagnes newsletter',                                       status: 'disconnected', tag: 'Marketing',  badge: '—' },
  ];
  return (
    <>
      <Section title="Services connectés" sub="Les outils externes utilisés par IMSO." icon={I.link}
        actions={<button className="btn sm"><I.plus size={13}/> Parcourir le catalogue</button>}>
        <Grid cols={2} gap={12}>
          {integrations.map((it, i) => (
            <div key={i} style={{
              border: '1px solid var(--border-soft)', borderRadius: 12,
              padding: 16, background: '#FAFBFC',
              display: 'flex', gap: 12,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: '#fff', border: '1px solid var(--border)',
                display: 'grid', placeItems: 'center',
                color: it.status === 'connected' ? 'var(--primary)' : 'var(--muted)',
                flexShrink: 0,
              }}><I.link size={18}/></div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ fontSize: 13.5, fontWeight: 700 }}>{it.name}</span>
                  {it.status === 'connected'
                    ? <span className="pill green dot">Actif</span>
                    : <span className="pill gray">Non connecté</span>}
                </div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>{it.desc}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="pill gray mono" style={{ fontSize: 10 }}>{it.badge}</span>
                  <button className="btn sm">{it.status === 'connected' ? 'Configurer' : 'Connecter'}</button>
                </div>
              </div>
            </div>
          ))}
        </Grid>
      </Section>

      <Section title="Clés API IMSO" sub="Pour les développeurs qui veulent intégrer IMSO." icon={I.key}
        actions={<button className="btn primary sm"><I.plus size={13}/> Nouvelle clé</button>}>
        <table className="table" style={{ margin: '-22px -22px -22px', width: 'calc(100% + 44px)' }}>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Clé</th>
              <th>Portée</th>
              <th>Dernière utilisation</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {[
              { n: 'App mobile (iOS+Android)', k: 'imso_live_••••••••••3df9', s: 'Lecture + Écriture', l: 'il y a 2 min' },
              { n: 'Site public imso.ht',      k: 'imso_live_••••••••••8c14', s: 'Lecture seule',     l: 'il y a 8 min' },
              { n: 'Export comptable',          k: 'imso_live_••••••••••4d72', s: 'Export uniquement', l: 'il y a 2 j' },
              { n: 'Webhook Sogebank',          k: 'imso_live_••••••••••a1f5', s: 'Paiements',         l: 'il y a 5 h' },
            ].map((k, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600 }}>{k.n}</td>
                <td className="mono" style={{ fontSize: 12 }}>{k.k}</td>
                <td><span className="pill gray">{k.s}</span></td>
                <td style={{ color: 'var(--muted)', fontSize: 12.5 }}>{k.l}</td>
                <td style={{ textAlign: 'right' }}>
                  <div className="stack" style={{ justifyContent: 'flex-end' }}>
                    <button className="btn sm ghost"><I.copy size={13}/></button>
                    <button className="btn sm ghost"><I.refresh size={13}/></button>
                    <button className="btn sm ghost" style={{ color: 'var(--danger)' }}><I.trash size={13}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Webhooks sortants" sub="URLs qui reçoivent les événements IMSO en temps réel." icon={I.link}>
        <Grid cols={1} gap={10}>
          {[
            { url: 'https://hooks.imso.ht/comptabilite/payments', events: ['payment.success', 'payment.failed'], ok: true },
            { url: 'https://hooks.imso.ht/crm/members',           events: ['member.created', 'member.upgraded'], ok: true },
            { url: 'https://n8n.imso.ht/webhook/agent-ia',        events: ['ai.lead.qualified'],                   ok: false },
          ].map((w, i) => (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: '1fr auto auto',
              gap: 14, alignItems: 'center',
              padding: '12px 14px', background: '#FAFBFC',
              border: '1px solid var(--border-soft)', borderRadius: 10,
            }}>
              <div>
                <div className="mono" style={{ fontSize: 12.5, fontWeight: 600 }}>{w.url}</div>
                <div style={{ display: 'flex', gap: 5, marginTop: 5 }}>
                  {w.events.map(e => (
                    <span key={e} className="mono" style={{
                      fontSize: 10, padding: '2px 7px',
                      background: '#fff', border: '1px solid var(--border-soft)', borderRadius: 4,
                    }}>{e}</span>
                  ))}
                </div>
              </div>
              {w.ok ? <span className="pill green dot">200 OK</span> : <span className="pill red dot">503 Erreur</span>}
              <button className="btn sm ghost"><I.more size={14}/></button>
            </div>
          ))}
        </Grid>
      </Section>
    </>
  );
}

/* ---------- 9. Sauvegardes ---------- */
function PaneBackup() {
  const backups = [
    { date: '21 mai 2026 · 03:00', size: '247 Mo', dur: '1m 12s', status: 'ok', auto: true },
    { date: '20 mai 2026 · 03:00', size: '246 Mo', dur: '1m 08s', status: 'ok', auto: true },
    { date: '19 mai 2026 · 14:22', size: '244 Mo', dur: '1m 05s', status: 'ok', auto: false, note: 'Avant régénération API MonCash' },
    { date: '19 mai 2026 · 03:00', size: '244 Mo', dur: '1m 09s', status: 'ok', auto: true },
    { date: '18 mai 2026 · 03:00', size: '242 Mo', dur: '1m 11s', status: 'ok', auto: true },
    { date: '17 mai 2026 · 03:00', size: '241 Mo', dur: '—',      status: 'fail', auto: true, note: 'Disque saturé · résolu' },
  ];
  return (
    <>
      <Section title="Sauvegardes automatiques" sub="Vos données sont sauvegardées chaque nuit dans 2 régions." icon={I.database}
        actions={<button className="btn primary sm"><I.refresh size={13}/> Sauvegarder maintenant</button>}>
        <Grid cols={4}>
          <div style={{ padding: 16, background: 'var(--primary-light)', borderRadius: 12 }}>
            <div style={{ fontSize: 11.5, color: 'var(--primary)', fontWeight: 700, letterSpacing: '0.06em' }}>FRÉQUENCE</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 6 }}>Quotidienne</div>
            <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>Tous les jours à 03:00 (UTC−5)</div>
          </div>
          <div style={{ padding: 16, background: '#FAFBFC', border: '1px solid var(--border-soft)', borderRadius: 12 }}>
            <div style={{ fontSize: 11.5, color: 'var(--muted)', fontWeight: 700, letterSpacing: '0.06em' }}>RÉTENTION</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 6 }}>90 jours</div>
            <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>+ snapshots mensuels (1 an)</div>
          </div>
          <div style={{ padding: 16, background: '#FAFBFC', border: '1px solid var(--border-soft)', borderRadius: 12 }}>
            <div style={{ fontSize: 11.5, color: 'var(--muted)', fontWeight: 700, letterSpacing: '0.06em' }}>STOCKAGE UTILISÉ</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 6 }} className="num">14.8 Go</div>
            <div style={{ height: 5, background: '#F3F4F6', borderRadius: 999, marginTop: 8, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: '37%', background: 'var(--primary)' }}/>
            </div>
            <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 3 }}>37% de 40 Go</div>
          </div>
          <div style={{ padding: 16, background: '#FAFBFC', border: '1px solid var(--border-soft)', borderRadius: 12 }}>
            <div style={{ fontSize: 11.5, color: 'var(--muted)', fontWeight: 700, letterSpacing: '0.06em' }}>DERNIÈRE SAUV.</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 6 }}>Aujourd'hui · 03:00</div>
            <div style={{ fontSize: 11.5, color: '#047857', marginTop: 2, fontWeight: 600 }}>● Réussie</div>
          </div>
        </Grid>

        <div style={{ marginTop: 18, padding: 14, background: '#F0F8F3', borderRadius: 10, display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ color: 'var(--primary)' }}><I.shieldCheck size={18}/></div>
          <div style={{ fontSize: 12.5, flex: 1, lineHeight: 1.5 }}>
            <b>Chiffrées AES-256.</b> Stockées dans <b>OVH Paris</b> (primaire) et <b>Backblaze B2 US-East</b> (réplique). Aucun salarié IMSO ne peut lire le contenu sans la clé maître.
          </div>
          <button className="btn sm">Configurer</button>
        </div>
      </Section>

      <Section title="Historique des sauvegardes" sub="Restaurez à n'importe quel point dans les 90 derniers jours.">
        <table className="table" style={{ margin: '-22px -22px -22px', width: 'calc(100% + 44px)' }}>
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Taille</th>
              <th>Durée</th>
              <th>Statut</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody className="row-anim">
            {backups.map((b, i) => (
              <tr key={i} style={{ animationDelay: `${0.04 * i}s` }}>
                <td className="mono" style={{ fontSize: 12.5, fontWeight: 600 }}>{b.date}</td>
                <td>
                  {b.auto
                    ? <span className="pill gray">Automatique</span>
                    : <span className="pill blue dot">Manuelle</span>}
                  {b.note && <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 2 }}>{b.note}</div>}
                </td>
                <td className="mono" style={{ fontSize: 12.5 }}>{b.size}</td>
                <td className="mono" style={{ fontSize: 12.5, color: 'var(--muted)' }}>{b.dur}</td>
                <td>
                  {b.status === 'ok'
                    ? <span className="pill green dot">Réussie</span>
                    : <span className="pill red dot">Échouée</span>}
                </td>
                <td style={{ textAlign: 'right' }}>
                  <div className="stack" style={{ justifyContent: 'flex-end' }}>
                    <button className="btn sm"><I.download size={13}/> Télécharger</button>
                    {b.status === 'ok' && <button className="btn sm">Restaurer</button>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Export complet" sub="Téléchargez l'intégralité de vos données dans un format ouvert.">
        <Grid cols={3} gap={12}>
          {[
            { ico: I.fileText, t: 'CSV',   d: 'Tableaux Excel et Numbers',  size: '14 Mo' },
            { ico: I.fileText, t: 'JSON',  d: 'Pour migration ou backup',   size: '52 Mo' },
            { ico: I.fileText, t: 'SQL',   d: 'Dump PostgreSQL complet',    size: '247 Mo' },
          ].map((f, i) => (
            <button key={i} className="btn" style={{ padding: 16, justifyContent: 'flex-start', gap: 12, height: 'auto' }}>
              <div style={{
                width: 38, height: 38, borderRadius: 9,
                background: 'var(--primary-light)', color: 'var(--primary)',
                display: 'grid', placeItems: 'center', flexShrink: 0,
              }}><f.ico size={18}/></div>
              <div style={{ textAlign: 'left', flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: 13.5 }}>Export {f.t}</div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>{f.d} · ~{f.size}</div>
              </div>
              <I.download size={16} style={{ color: 'var(--muted)' }}/>
            </button>
          ))}
        </Grid>
      </Section>
    </>
  );
}

/* ---------- 10. Zone de danger ---------- */
function PaneDanger() {
  return (
    <Section title="Zone de danger" sub="Actions irréversibles. Lisez attentivement avant d'agir." icon={I.ban}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {[
          { t: 'Réinitialiser les statistiques de démo',
            d: 'Supprime les données de test mais conserve les comptes et cours réels.',
            btn: 'Réinitialiser', tone: 'amber' },
          { t: 'Transférer la propriété IMSO',
            d: 'Donne le statut de super-admin à un autre membre. Vous redeviendrez admin standard.',
            btn: 'Transférer', tone: 'amber' },
          { t: 'Archiver l\'année académique 2024–2025',
            d: 'Les données restent accessibles en lecture seule. Recommandé en fin d\'année.',
            btn: 'Archiver', tone: 'amber' },
          { t: 'Supprimer définitivement l\'institution',
            d: 'Efface tous les comptes, cours, paiements, sauvegardes et certificats. Cette action ne peut pas être annulée.',
            btn: 'Supprimer IMSO', tone: 'red' },
        ].map((d, i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '1fr auto',
            gap: 14, alignItems: 'center',
            padding: '16px 18px',
            border: d.tone === 'red' ? '1px solid #FECACA' : '1px solid var(--border-soft)',
            background: d.tone === 'red' ? '#FEF2F2' : '#FAFBFC',
            borderRadius: 12,
          }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: d.tone === 'red' ? '#B91C1C' : 'var(--text)' }}>{d.t}</div>
              <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 3, lineHeight: 1.5 }}>{d.d}</div>
            </div>
            <button className="btn sm" style={{
              borderColor: d.tone === 'red' ? '#FECACA' : 'var(--border)',
              color: d.tone === 'red' ? '#B91C1C' : 'var(--text)',
              background: '#fff',
              fontWeight: 600,
            }}>{d.btn}</button>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ---------- Settings shell ---------- */
function Settings() {
  const [tab, setTab] = useState('general');
  const groups = [...new Set(SETTINGS_TABS.map(t => t.group))];

  const panes = {
    general: <PaneGeneral/>,
    branding: <PaneBranding/>,
    team: <PaneTeam/>,
    payments: <PanePayments/>,
    room: <PaneRoom/>,
    notifications: <PaneNotifications/>,
    security: <PaneSecurity/>,
    integrations: <PaneIntegrations/>,
    backup: <PaneBackup/>,
    danger: <PaneDanger/>,
  };
  const current = SETTINGS_TABS.find(t => t.id === tab);

  return (
    <div className="content">
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 24, alignItems: 'flex-start' }}>
        {/* Side nav */}
        <aside style={{
          position: 'sticky', top: 'calc(var(--hd-h) + 20px)',
          background: '#fff', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)', padding: '12px 8px',
          boxShadow: 'var(--shadow-sm)',
        }} className="fade-in d1">
          {groups.map(g => (
            <div key={g}>
              <div style={{
                fontSize: 10.5, fontWeight: 600,
                color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.08em',
                padding: '10px 12px 6px',
              }}>{g}</div>
              {SETTINGS_TABS.filter(t => t.group === g).map(t => (
                <div key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`sb-item ${tab === t.id ? 'active' : ''} ${t.danger ? 'danger' : ''}`}
                  style={{ margin: '1px 0' }}>
                  <span className="ico"><t.icon size={17}/></span>
                  <span style={{ flex: 1 }}>{t.label}</span>
                  {tab === t.id && <I.chevronR size={14} style={{ color: 'var(--primary)' }}/>}
                </div>
              ))}
            </div>
          ))}
        </aside>

        {/* Panel */}
        <main key={tab} style={{ minWidth: 0 }}>
          <div className="between fade-in d1" style={{ marginBottom: 18 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Paramètres · {current.group}
              </div>
              <div className="h2" style={{ marginTop: 4 }}>{current.label}</div>
            </div>
            <div className="stack">
              <span className="pill green dot mono" style={{ fontSize: 10 }}>Auto-sauvegardé · à l'instant</span>
              <button className="btn sm ghost"><I.refresh size={14}/></button>
            </div>
          </div>
          {panes[tab]}
        </main>
      </div>
    </div>
  );
}

window.Settings = Settings;
