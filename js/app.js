const $ = sel => document.querySelector(sel);
const views = { '/': renderHome, '/crear': renderCreate, '/dashboard': renderDashboard };

function route(){
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

function updateUserMenu(){
  const menu = $('#user-menu');
  if (!auth.currentUser){
    menu.innerHTML = `<a href="/login" class="nav-link">Ingresar</a><a href="/registro" class="nav-link nav-registro">Crear cuenta</a>`;
  } else {
    menu.innerHTML = `<a href="/dashboard" class="nav-link">${auth.currentUser.displayName || auth.currentUser.email}</a><button id="logout" class="btn-link">Salir</button>`;
  }
  const logout = $('#logout');
  if (logout) logout.onclick = () => auth.signOut().then(()=> location.href='/');
}

$('#dark-toggle')?.addEventListener('click', ()=>{
  const html=document.documentElement;
  const isDark = html.getAttribute('data-theme')==='dark';
  html.setAttribute('data-theme', isDark?'light':'dark');
  localStorage.setItem('theme', isDark?'light':'dark');
});
(function(){
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

function renderHome(container){
  container.innerHTML = `<section class="hero"><h1>Armá tu picadito</h1><p>Creá un evento, compartí el link y que la gente se anote sin tener que registrarse.</p><a href="/crear" class="btn btn-primary btn-lg">⚽ Crear picadito</a></section>`;
}

function renderCreate(container){
  container.innerHTML = `<div class="card"><h2>Crear evento</h2><form id="form-create"><label>Título <input name="title" required></label><label>Descripción <textarea name="description"></textarea></label><label>Fecha <input type="datetime-local" name="date" required></label><label>Lugar <input name="location"></label><label>Dirección <input name="address"></label><label>Total $ <input type="number" name="total" value="0"></label><label>Seña $ <input type="number" name="deposit" value="0"></label><label>Cupo máximo <input type="number" name="max_participants" value="0"></label><label>Tu nombre <input name="creator_name" required></label><button class="btn btn-primary">Crear</button></form></div>`;
  $('#form-create').onsubmit = async e=>{
    e.preventDefault();
    const fd=new FormData(e.target);
    const data=Object.fromEntries(fd.entries());
    data.total=parseInt(data.total||0);
    data.deposit=parseInt(data.deposit||0);
    data.max_participants=parseInt(data.max_participants||0);
    data.creator_token=crypto.randomUUID();
    data.creator_id=auth.currentUser?.uid||null;
    data.status='active';
    data.createdAt=Date.now();
    const ref=await db.ref('events').push(data);
    location.href='/e/'+ref.key;
  };
}

async function renderEvent(path){
  const id=path.split('/')[2];
  const snap=await db.ref('events/'+id).once('value');
  if (!snap.exists()) return renderNotFound();
  const event={id, ...snap.val()};
  const partSnap=await db.ref('events/'+id+'/participants').once('value');
  const participants=[];
  partSnap.forEach(child=>{ if(child.val().status!=='cancelled') participants.push({id:child.key,...child.val()}); });
  const perPerson=event.total>0? Math.ceil(event.total/(event.max_participants||participants.length||1)) :0;
  const app=$('#app');
  app.innerHTML=`<div class="event-header"><h1>${event.title}</h1><p>${new Date(event.date).toLocaleString()}</p><p>${event.location} ${event.address?'- '+event.address:''}</p></div><div class="cost-box"><div>Total $${event.total||0}</div><div>Seña $${event.deposit||0}</div><div class="cost-highlight">Por persona $${perPerson}</div></div><h3>Participantes ${participants.length}</h3><ul class="list">${participants.map(p=>`<li>${p.name} ${p.team?'(Equipo '+p.team+')':''}</li>`).join('')}</ul><form id="form-join"><input name="name" placeholder="Tu nombre" required><input name="phone" placeholder="WhatsApp"><input type="number" name="guests" value="1" min="1"><button class="btn btn-primary">Anotarse</button></form><a href="/admin/${id}/${event.creator_token}" class="btn btn-secondary">Admin</a>`;
  $('#form-join').onsubmit=async e=>{
    e.preventDefault();
    const fd=new FormData(e.target);
    const data=Object.fromEntries(fd.entries());
    data.guests=parseInt(data.guests);
    data.token=crypto.randomUUID();
    data.status='confirmed';
    data.createdAt=Date.now();
    await db.ref('events/'+id+'/participants').push(data);
    alert('Anotado!');
    route();
  };
}

function renderAdmin(path){
  const parts=path.split('/');
  const id=parts[2];
  const token=parts[3];
  $('#app').innerHTML=`<div class="card"><h2>Admin</h2><p>Evento ${id}</p><p>Token: ${token}</p><button id="random-teams" class="btn btn-primary">Randomizar equipos</button></div>`;
  $('#random-teams').onclick=async ()=>{
    const snap=await db.ref('events/'+id+'/participants').once('value');
    const updates={};
    let i=0;
    snap.forEach(child=>{
      const v=child.val();
      if(v.status==='confirmed'){
        updates['events/'+id+'/participants/'+child.key+'/team']= (i%2===0?'1':'2');
        i++;
      }
    });
    await db.ref().update(updates);
    alert('Equipos randomizados');
    location.reload();
  };
}

function renderParticipant(path){
  const token=path.split('/')[2];
  $('#app').innerHTML=`<div class="card"><h2>Tu participación</h2><p>Token: ${token}</p><button id="cancel" class="btn btn-secondary">Cancelar</button></div>`;
  $('#cancel').onclick=async ()=>{
    // Simple search: iterate events
    const snap=await db.ref('events').once('value');
    snap.forEach(ev=>{
      ev.forEach(part=>{
        const v=part.val();
        if(v.token===token){
          db.ref('events/'+ev.key+'/participants/'+part.key).update({status:'cancelled'});
        }
      });
    });
    alert('Cancelado');
  };
}

function renderDashboard(container){
  container.innerHTML=`<h2>Dashboard</h2><p>Cargando...</p>`;
  if(!auth.currentUser){ location.href='/login'; return; }
  db.ref('events').orderByChild('creator_id').equalTo(auth.currentUser.uid).once('value').then(snap=>{
    const items=[];
    snap.forEach(child=>items.push(`<li><a href="/e/${child.key}">${child.val().title}</a></li>`));
    container.innerHTML=`<h2>Dashboard</h2><ul>${items.join('')||'<li>Sin eventos</li>'}</ul>`;
  });
}

function renderLogin(){
  $('#app').innerHTML=`<div class="card"><h2>Ingresar</h2><form id="form-login"><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Contraseña" required><button class="btn btn-primary">Entrar</button></form></div>`;
  $('#form-login').onsubmit=async e=>{
    e.preventDefault();
    const fd=new FormData(e.target);
    await auth.signInWithEmailAndPassword(fd.get('email'), fd.get('password'));
    location.href='/dashboard';
  };
}

function renderRegister(){
  $('#app').innerHTML=`<div class="card"><h2>Crear cuenta</h2><form id="form-register"><input name="name" placeholder="Nombre" required><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Contraseña" required><button class="btn btn-primary">Crear</button></form></div>`;
  $('#form-register').onsubmit=async e=>{
    e.preventDefault();
    const fd=new FormData(e.target);
    const cred=await auth.createUserWithEmailAndPassword(fd.get('email'), fd.get('password'));
    await cred.user.updateProfile({displayName:fd.get('name')});
    location.href='/dashboard';
  };
}

function renderNotFound(){
  $('#app').innerHTML=`<h2>404</h2><p>No encontrado</p>`;
}

window.addEventListener('popstate', route);
document.addEventListener('click', e=>{
  const a=e.target.closest('a');
  if(a && a.origin===location.origin){
    e.preventDefault();
    history.pushState(null,'',a.href);
    route();
  }
});
route();
