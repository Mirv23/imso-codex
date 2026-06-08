// All mock data + helpers.
const fmtNum = (n) => n.toLocaleString('fr-FR');
const fmtHTG = (n) => n.toLocaleString('fr-FR') + ' HTG';

const MEMBERS = [
  { id:'m1', name:'Marie-Claude Joseph', email:'mc.joseph@imso.ht', gei:'PAP', status:'Actif', date:'12 mars 2026', avatar:'warm', initials:'MJ', phone:'+509 3742 0918' },
  { id:'m2', name:'Jean-Robert Pierre', email:'jr.pierre@imso.ht', gei:'CAP', status:'Actif', date:'09 mars 2026', avatar:'blue', initials:'JP', phone:'+509 3811 4527' },
  { id:'m3', name:'Nadège Saint-Vil', email:'nadege.sv@gmail.com', gei:'JAC', status:'Attente', date:'07 mars 2026', avatar:'purple', initials:'NS', phone:'+509 4220 7733' },
  { id:'m4', name:'Wilkenson Auguste', email:'w.auguste@imso.ht', gei:'LGN', status:'Actif', date:'05 mars 2026', avatar:'teal', initials:'WA', phone:'+509 3699 1284' },
  { id:'m5', name:'Stéphanie Désir', email:'s.desir@yahoo.fr', gei:'PAP', status:'Suspendu', date:'02 mars 2026', avatar:'rose', initials:'SD', phone:'+509 3404 5566' },
  { id:'m6', name:'Frantz Cadet', email:'frantz.c@imso.ht', gei:'GON', status:'Actif', date:'01 mars 2026', avatar:'amber', initials:'FC', phone:'+509 3722 9911' },
  { id:'m7', name:'Roselène Bélizaire', email:'rose.b@gmail.com', gei:'CYS', status:'Actif', date:'28 fév 2026', avatar:'warm', initials:'RB', phone:'+509 4811 3322' },
  { id:'m8', name:'Edwidge Marcellin', email:'edwidge.m@imso.ht', gei:'CAP', status:'Attente', date:'27 fév 2026', avatar:'blue', initials:'EM', phone:'+509 3955 4012' },
  { id:'m9', name:'Patrick Théodore', email:'p.theodore@imso.ht', gei:'PAP', status:'Actif', date:'25 fév 2026', avatar:'purple', initials:'PT', phone:'+509 3677 8800' },
  { id:'m10', name:'Carline Estimé', email:'carline.e@gmail.com', gei:'JAC', status:'Actif', date:'24 fév 2026', avatar:'teal', initials:'CE', phone:'+509 4002 1717' },
  { id:'m11', name:'Yvon Gabriel', email:'yvon.g@imso.ht', gei:'LGN', status:'Actif', date:'22 fév 2026', avatar:'rose', initials:'YG', phone:'+509 3811 2244' },
  { id:'m12', name:'Marlène Charles', email:'marlene.c@imso.ht', gei:'GON', status:'Suspendu', date:'20 fév 2026', avatar:'amber', initials:'MC', phone:'+509 3300 9988' },
  { id:'m13', name:'Daniel Pétion', email:'d.petion@imso.ht', gei:'CYS', status:'Actif', date:'18 fév 2026', avatar:'warm', initials:'DP', phone:'+509 4567 1212' },
  { id:'m14', name:'Berthony Lamour', email:'berthony.l@gmail.com', gei:'PAP', status:'Attente', date:'15 fév 2026', avatar:'blue', initials:'BL', phone:'+509 3789 4561' },
  { id:'m15', name:'Sophonie Vincent', email:'s.vincent@imso.ht', gei:'CAP', status:'Actif', date:'12 fév 2026', avatar:'purple', initials:'SV', phone:'+509 4123 6677' },
];

const PAYMENTS = [
  { id:'p1', member:'Marie-Claude Joseph', course:'Théologie pratique I', amount:7500, method:'MonCash', status:'Réussi', date:'il y a 12 min' },
  { id:'p2', member:'Jean-Robert Pierre', course:'Leadership chrétien', amount:12000, method:'Stripe', status:'Réussi', date:'il y a 1 h' },
  { id:'p3', member:'Wilkenson Auguste', course:'Évangélisation moderne', amount:5500, method:'MonCash', status:'En attente', date:'il y a 2 h' },
  { id:'p4', member:'Roselène Bélizaire', course:'Étude de Romains', amount:9000, method:'Stripe', status:'Réussi', date:'il y a 3 h' },
  { id:'p5', member:'Frantz Cadet', course:'Théologie pratique I', amount:7500, method:'MonCash', status:'Échoué', date:'il y a 5 h' },
  { id:'p6', member:'Patrick Théodore', course:'Discipulat', amount:6500, method:'MonCash', status:'Réussi', date:'hier' },
];

const COURSES = [
  { id:'c1', title:'Théologie pratique — Module I', students:142, revenue:1065000, status:true, thumb:'green', cat:'Théologie', duration:'6h 24', price:7500 },
  { id:'c2', title:'Leadership chrétien et gestion d\'équipe', students:89, revenue:1068000, status:true, thumb:'warm', cat:'Leadership', duration:'8h 12', price:12000 },
  { id:'c3', title:'Évangélisation à l\'ère numérique', students:201, revenue:1105500, status:true, thumb:'blue', cat:'Évangélisation', duration:'4h 48', price:5500 },
  { id:'c4', title:'Étude approfondie de l\'épître aux Romains', students:67, revenue:603000, status:true, thumb:'purple', cat:'Bible', duration:'12h 30', price:9000 },
  { id:'c5', title:'Le ministère du discipulat', students:124, revenue:806000, status:true, thumb:'teal', cat:'Ministère', duration:'5h 15', price:6500 },
  { id:'c6', title:'Apologétique pour aujourd\'hui', students:0, revenue:0, status:false, thumb:'rose', cat:'Apologétique', duration:'7h 00', price:8500 },
];

const REVENUE = [
  { m:'Oct', v:412000 }, { m:'Nov', v:485000 },
  { m:'Déc', v:528000 }, { m:'Jan', v:601000 },
  { m:'Fév', v:723000 }, { m:'Mar', v:847500 },
];

const CATEGORIES = [
  { name:'Théologie', value:32, color:'#2D6A4F' },
  { name:'Bible', value:24, color:'#F4A261' },
  { name:'Leadership', value:18, color:'#4F86C6' },
  { name:'Ministère', value:14, color:'#8B5CF6' },
  { name:'Évangélisation', value:8, color:'#14B8A6' },
  { name:'Apologétique', value:4, color:'#EF4444' },
];

const NOTIFS = [
  { id:1, msg:'Nouveau membre inscrit : Marie-Claude Joseph (PAP)', time:'il y a 3 min', read:false },
  { id:2, msg:'Paiement reçu — 12 000 HTG via Stripe', time:'il y a 1 h', read:false },
  { id:3, msg:'L\'agent IA a publié 3 posts sur Facebook', time:'il y a 2 h', read:false },
  { id:4, msg:'Cours "Évangélisation moderne" : seuil de 200 inscrits atteint', time:'il y a 4 h', read:true },
  { id:5, msg:'Sauvegarde quotidienne effectuée avec succès', time:'hier, 02:00', read:true },
];

Object.assign(window, {
  MEMBERS, PAYMENTS, COURSES, REVENUE, CATEGORIES, NOTIFS,
  fmtNum, fmtHTG,
});
