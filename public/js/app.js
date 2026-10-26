const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

const views = {
  '/': renderHome,
  '/crear': renderCreate,
  '/dashboard': renderDashboard,
};

function route() {
  const path = location.pathname;
  const app = $('#app');
  if (path.startsWith('/e/')) return renderEvent(path);
  if (path.startsWith('/admin/')) return renderAdmin(path);
  if (path.startsWith('/p/')) return renderParticipant(path);
  if (path === '/login') return renderLogin();
  if (path === '/registro') return renderRegister();
  const handler = views[path] || renderNotFound;
  app.innerHTML = '';
  handler(app);
  updateUserMenu();
}

function updateUserMenu() {
  const menu = $('#user-menu');
  if (!auth.currentUser) {
    menu.innerHTML = `<a href="/login" class="nav-link">Ingresar</a><a href="/registro" class="nav-link nav-registro">Crear cuenta</a>`;
  } else {
    menu.innerHTML = `<a href="/dashboard" class="nav-link">${auth.currentUser.displayName || auth.currentUser.email}</a><button id="logout" class="btn-link">Salir</button>`;
  }
  const logout = $('#logout');
  if (logout) logout.onclick = () => auth.signOut().then(()=> location.href='/');
}

// Dark toggle
$('#dark-toggle')?.addEventListener('click', () => {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
});

// Init theme
(function(){
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

function renderHome(container){
  container.innerHTML = `
  <section class="hero">
    <h1>Armá tu picadito</h1>
    <p>Creá un evento, compartí el link y que la gente se anote sin tener que registrarse.</p>
    <a href="/crear" class="btn btn-primary btn-lg">⚽ Crear picadito</a>
  </section>
  <section class="how">
    <h2>Cómo funciona</h2>
    <div class="steps">
      <div class="step"><div class="step-num">1</div><h3>Creás el evento</h3><p>Ponés fecha, lugar y cupo máximo.</p></div>
      <div class="step"><div class="step-num">2</div><h3>Compartís el link</h3><p>Lo mandás por WhatsApp, Telegram, o como quieras.</p></div>
      <div class="step"><div class="step-num">3</div><h3>La gente se anota</h3><p>Sin crear cuenta. Solo nombre y listo.</p></div>
    </div>
  </section>`;
}

function renderCreate(container){
  container.innerHTML = `
  <div class="card">
    <h2>Crear evento</h2>
    <form id="form-create">
      <label>Título <input name="title" required></label>
      <label>Descripción <textarea name="description"></textarea></label>
      <label>Fecha <input type="datetime-local" name="date" required></label>
      <label>Lugar <input name="location"></label>
      <label>Dirección <input name="address"></label>
      <label>Total $ <input type="number" name="total" value="0"></label>
      <label>Seña $ <input type="number" name="deposit" value="0"></label>
      <label>Cupo máximo <input type="number" name="max_participants" value="0"></label>
      <label>Tu nombre <input name="creator_name" required></label>
      <button class="btn btn-primary">Crear</button>
    </form>
  </div>`;
  $('#form-create').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd.entries());
    data.total = parseInt(data.total||0);
    data.deposit = parseInt(data.deposit||0);
    data.max_participants = parseInt(data.max_participants||0);
    data.creator_token = crypto.randomUUID();
    data.creator_id = auth.currentUser?.uid || null;
    data.status = 'active';
    data.createdAt = firebase.firestore.FieldValue.serverTimestamp();
    const ref = await db.collection('events').add(data);
    location.href = '/e/' + ref.id;
  };
}

async function renderEvent(path){
  const id = path.split('/')[2];
  const doc = await db.collection('events').doc(id).get();
  if (!doc.exists) return renderNotFound();
  const event = {id: doc.id, ...doc.data()};
  const participantsSnap = await db.collection('events').doc(id).collection('participants').get();
  const participants = participantsSnap.docs.map(d=>({id:d.id,...d.data()})).filter(p=>p.status!=='cancelled');
  const perPerson = event.total>0 ? Math.ceil(event.total / (event.max_participants||participants.length||1)) : 0;
  const app = $('#app');
  app.innerHTML = `
  <div class="event-header">
    <h1>${event.title}</h1>
    <p>${new Date(event.date?.seconds? event.date.seconds*1000 : event.date).toLocaleString()}</p>
    <p>${event.location} ${event.address?'- '+event.address:''}</p>
  </div>
  <div class="cost-box">
    <div>Total $${event.total||0}</div>
    <div>Seña $${event.deposit||0}</div>
    <div class="cost-highlight">Por persona $${perPerson}</div>
  </div>
  <h3>Participantes ${participants.length}</h3>
  <ul class="list">${participants.map(p=>`<li>${p.name} ${p.team?'(Equipo '+p.team+')':''}</li>`).join('')}</ul>
  <form id="form-join">
    <input name="name" placeholder="Tu nombre" required>
    <input name="phone" placeholder="WhatsApp">
    <input type="number" name="guests" value="1" min="1">
    <button class="btn btn-primary">Anotarse</button>
  </form>
  <a href="/admin/${id}/${event.creator_token}" class="btn btn-secondary">Admin</a>
  `;
  $('#form-join').onsubmit = async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd.entries());
    data.guests = parseInt(data.guests);
    data.token = crypto.randomUUID();
    data.status = 'confirmed';
    data.createdAt = firebase.firestore.FieldValue.serverTimestamp();
    await db.collection('events').doc(id).collection('participants').doc().set(data);
    alert('Anotado!');
    route();
  };
}

function renderAdmin(path){
  const parts = path.split('/');
  const id = parts[2];
  const token = parts[3];
  $('#app').innerHTML = `<div class="card"><h2>Admin</h2><p>Evento ${id}</p><p>Token: ${token}</p><button id="random-teams">Randomizar equipos</button></div>`;
  $('#random-teams').onclick = async () => {
    const snap = await db.collection('events').doc(id).collection('participants').where('status','==','confirmed').get();
    const participants = snap.docs.map(d=>d.id);
    participants.forEach((pid,i)=>{
      const team = i%2===0?'1':'2';
      db.collection('events').doc(id).collection('participants').doc(pid).update({team});
    });
    alert('Equipos randomizados');
    location.reload();
  };
}

function renderParticipant(path){
  $('#app').innerHTML = `<div class="card"><h2>Tu participación</h2><p>Token: ${path.split('/')[2]}</p><button id="cancel">Cancelar</button></div>`;
  $('#cancel').onclick = async ()=>{
    // find participant by token
    const snap = await db.collectionGroup('participants').where('token','==',path.split('/')[2]).get();
    snap.forEach(doc=> doc.ref.update({status:'cancelled'}));
    alert('Cancelado');
  };
}

function renderDashboard(container){
  container.innerHTML = `<h2>Dashboard</h2><p>Cargando eventos...</p>`;
  if (!auth.currentUser){ location.href='/login'; return; }
  db.collection('events').where('creator_id','==',auth.currentUser.uid).get().then(snap=>{
    const items = snap.docs.map(d=>`<li><a href="/e/${d.id}">${d.data().title}</a></li>`).join('');
    container.innerHTML = `<h2>Dashboard</h2><ul>${items}</ul>`;
  });
}

function renderLogin(){
  $('#app').innerHTML = `
  <div class="card">
    <h2>Ingresar</h2>
    <form id="form-login">
      <input name="email" type="email" placeholder="Email" required>
      <input name="password" type="password" placeholder="Contraseña" required>
      <button class="btn btn-primary">Entrar</button>
    </form>
  </div>`;
  $('#form-login').onsubmit = async e=>{
    e.preventDefault();
    const fd = new FormData(e.target);
    await auth.signInWithEmailAndPassword(fd.get('email'), fd.get('password'));
    location.href='/dashboard';
  };
}

function renderRegister(){
  $('#app').innerHTML = `
  <div class="card">
    <h2>Crear cuenta</h2>
    <form id="form-register">
      <input name="name" placeholder="Nombre" required>
      <input name="email" type="email" placeholder="Email" required>
      <input name="password" type="password" placeholder="Contraseña" required>
      <button class="btn btn-primary">Crear</button>
    </form>
  </div>`;
  $('#form-register').onsubmit = async e=>{
    e.preventDefault();
    const fd = new FormData(e.target);
    const cred = await auth.createUserWithEmailAndPassword(fd.get('email'), fd.get('password'));
    await cred.user.updateProfile({displayName: fd.get('name')});
    location.href='/dashboard';
  };
}

function renderNotFound(){
  $('#app').innerHTML = `<h2>404</h2><p>No encontrado</p>`;
}

// Router init
window.addEventListener('popstate', route);
document.addEventListener('click', e=>{
  const a = e.target.closest('a');
  if (a && a.origin===location.origin){
    e.preventDefault();
    history.pushState(null,'',a.href);
    route();
  }
});
route();
author: OpenCode
