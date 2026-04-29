const NWFP_PAGE_LINKS = [
  ["index.html","Home"],["NWFP_Management_Plans.html","Plans"],["data_analytics.html","Analytics"],["spatial_resources.html","Spatial"],
  ["nwfp_gallery.html","Gallery"],["marketplace_sample.html","Market"],["about.html","About"],["dzongkhag_directory.html","Dzongkhags"],
  ["product_catalog.html","Products"],["nwfp_groups.html","Groups"],["species_profile.html","Species"],["people_nwfp.html","People & NWFP"],["certification_traceability.html","Traceability"],
  ["training_resources.html","Training"],["buyer_enquiry.html","Buyer Enquiry"]
];

function setupChrome(title){
  const header = document.getElementById("siteHeader");
  if(header){
    header.innerHTML = `
      <header class="sticky top-0 z-30 border-b border-white/10 bg-emerald-950/95 text-white shadow-xl backdrop-blur">
        <div class="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <a href="index.html" class="flex min-w-0 items-center gap-3">
            <img src="DoFPS_Bhutan_Logo.png" alt="Department of Forests and Park Services logo" class="h-14 w-14 shrink-0 object-contain logo-shadow">
            <div class="min-w-0">
              <strong class="block leading-tight">${title}</strong>
              <small class="block truncate text-xs text-lime-100">Forest Resources Planning and Management Division, Department of Forests and Park Services</small>
            </div>
          </a>
          <nav class="hidden max-w-4xl flex-wrap items-center justify-end gap-2 text-xs font-bold lg:flex">
            ${NWFP_PAGE_LINKS.map(([href,label])=>`<a class="nav-link rounded-xl px-3 py-2" href="${href}">${label}</a>`).join("")}
          </nav>
        </div>
      </header>`;
  }
  const footer = document.getElementById("siteFooter");
  if(footer){
    footer.innerHTML = `<footer class="mx-auto max-w-7xl px-4 pb-8 pt-2"><div class="rounded-2xl border border-emerald-900/10 bg-white/80 px-5 py-4 text-center text-sm font-bold text-emerald-950 shadow-sm">Made by Wangdi - <a class="text-emerald-700 hover:text-emerald-950" href="mailto:wangidues@gmail.com">wangidues@gmail.com</a></div></footer>`;
  }
}

const plans = window.NWFP_PLANS || [];
const safe = v => (v === null || v === undefined || v === "") ? "Not recorded" : v;
const fmt = n => Number(n || 0).toLocaleString();
const speciesList = p => (p.species || "Mixed NWFPs").split(",").map(s=>s.trim()).filter(Boolean);
const matches = (p, q) => !q || [p.group,p.div,p.dzong,p.gewog,p.status,p.ptype,p.species].join(" ").toLowerCase().includes(q.toLowerCase());

function dzongSummary(){
  const map = {};
  plans.forEach(p=>{
    const k = p.dzong || "Unknown";
    map[k] ||= {name:k,count:0,hh:0,area:0,divs:new Set(),products:new Set()};
    map[k].count++;
    map[k].hh += Number(p.hh || 0);
    map[k].area += Number(p.area || 0);
    if(p.div) map[k].divs.add(p.div);
    speciesList(p).slice(0,6).forEach(s=>map[k].products.add(s));
  });
  return Object.values(map).sort((a,b)=>b.count-a.count || a.name.localeCompare(b.name));
}

function renderStats(){
  const el = document.getElementById("stats");
  if(!el) return;
  const dz = dzongSummary();
  const active = plans.filter(p=>p.status==="active").length;
  el.innerHTML = [
    ["Groups / records", plans.length],
    ["Dzongkhags", dz.length],
    ["Active plans", active],
    ["Households", fmt(plans.reduce((s,p)=>s+Number(p.hh||0),0))]
  ].map(([label,value])=>`<div class="card rounded-3xl p-5"><div class="text-4xl font-black text-emerald-950">${value}</div><div class="mt-1 text-xs font-black uppercase tracking-wide text-slate-500">${label}</div></div>`).join("");
}

function renderDzongDirectory(){
  const el = document.getElementById("dzongDirectory");
  if(!el) return;
  el.innerHTML = dzongSummary().map(d=>`
    <article class="card rounded-3xl p-5">
      <div class="flex items-start justify-between gap-3">
        <div><p class="kicker">${d.divs.size} offices/parks</p><h2 class="mt-1 text-2xl font-black text-emerald-950">${d.name}</h2></div>
        <span class="rounded-full bg-yellow-300 px-3 py-1 text-xs font-black text-emerald-950">${d.count} groups</span>
      </div>
      <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div class="rounded-2xl bg-lime-50 p-3"><strong>${fmt(d.hh)}</strong><span class="block text-xs text-slate-500">households</span></div>
        <div class="rounded-2xl bg-lime-50 p-3"><strong>${fmt(Math.round(d.area))} ha</strong><span class="block text-xs text-slate-500">reported area</span></div>
      </div>
      <p class="mt-4 text-sm leading-6 text-slate-700">${[...d.products].slice(0,8).join(", ") || "Mixed NWFPs"}</p>
      <div class="mt-4 flex flex-wrap gap-2">
        <a class="chip rounded-full px-3 py-2 text-xs font-black text-emerald-950" href="NWFP_Management_Plans.html">Plans</a>
        <a class="chip rounded-full px-3 py-2 text-xs font-black text-emerald-950" href="spatial_resources.html">Spatial links</a>
        <a class="chip rounded-full px-3 py-2 text-xs font-black text-emerald-950" href="nwfp_groups.html">Groups</a>
      </div>
    </article>`).join("");
}

function renderGroups(){
  const tbody = document.getElementById("groupsBody");
  const search = document.getElementById("groupSearch");
  if(!tbody) return;
  const draw = ()=>{
    const q = search ? search.value : "";
    tbody.innerHTML = plans.filter(p=>matches(p,q)).map(p=>`
      <tr>
        <td><strong class="text-emerald-950">${p.group}</strong><span class="mt-1 block text-xs text-slate-500">${safe(p.species)}</span></td>
        <td>${safe(p.gewog)}<span class="block text-xs text-slate-500">${safe(p.dzong)}</span></td>
        <td>${safe(p.div)}</td>
        <td>${safe(p.status)}<span class="block text-xs text-slate-500">${safe(p.ptype)}</span></td>
        <td>${p.hh ? fmt(p.hh) : "-"}</td>
        <td>${p.area ? fmt(Math.round(p.area))+" ha" : "-"}</td>
      </tr>`).join("");
  };
  if(search) search.addEventListener("input", draw);
  draw();
}

const products = [
  {name:"Cordyceps sinensis",cat:"Medicinal high-value",img:"assets/nwfp_images/cordyceps-sinensis.jpg",keys:["Cordyceps"],use:"Premium medicinal NWFP with strict seasonal allocation and traceability needs."},
  {name:"Matsutake mushroom",cat:"Mushrooms",img:"assets/nwfp_images/matsutake.jpg",keys:["Matsutake","Mushroom"],use:"Fresh and graded mushroom products for seasonal buyers and processors."},
  {name:"Paris polyphylla",cat:"Medicinal plants",img:"assets/nwfp_images/paris-polyphylla.jpg",keys:["Paris polyphylla"],use:"Medicinal herb requiring inventory, quota control, and careful harvest timing."},
  {name:"Rubia cordifolia",cat:"Dyes and medicinal",img:"assets/nwfp_images/rubia-cordifolia.jpg",keys:["Rubia cordifolia"],use:"Natural dye and medicinal raw material suited for value addition."},
  {name:"Juniperus spp",cat:"Aromatics",img:"assets/nwfp_images/juniperus-recurva.jpg",keys:["Juniperus"],use:"Aromatic resource for incense, ritual use, and processed products."},
  {name:"Bamboo and cane",cat:"Bamboo/cane",img:"assets/nwfp_images/rubia-cordifolia.jpg",keys:["Bamboo","Cane","Plectocomia"],use:"Raw and processed materials for craft, furniture, baskets, and household items."},
  {name:"Daphne spp",cat:"Fiber plants",img:"assets/nwfp_images/paris-polyphylla.jpg",keys:["Daphne"],use:"Fiber resource with paper, handicraft, and niche product potential."},
  {name:"Broom grass",cat:"Household products",img:"assets/nwfp_images/matsutake.jpg",keys:["Thysanolaena","Broom"],use:"Common group product for local markets and simple processing enterprises."}
];

function productCount(item){
  return plans.filter(p=>item.keys.some(k=>(p.species||"").toLowerCase().includes(k.toLowerCase()) || (p.group||"").toLowerCase().includes(k.toLowerCase()))).length;
}

function renderProducts(){
  const el = document.getElementById("productGrid");
  if(!el) return;
  el.innerHTML = products.map(p=>`
    <article class="card overflow-hidden rounded-3xl">
      <img src="${p.img}" alt="${p.name}" class="product-img">
      <div class="p-5">
        <p class="kicker">${p.cat}</p>
        <h2 class="mt-1 text-2xl font-black text-emerald-950">${p.name}</h2>
        <p class="mt-3 text-sm leading-6 text-slate-700">${p.use}</p>
        <div class="mt-4 flex items-center justify-between gap-3">
          <span class="rounded-full bg-lime-100 px-3 py-2 text-xs font-black text-emerald-950">${productCount(p)} linked records</span>
          <a href="buyer_enquiry.html" class="rounded-xl bg-emerald-950 px-4 py-2 text-sm font-black text-white">Enquire</a>
        </div>
      </div>
    </article>`).join("");
}

function renderSpecies(){
  const el = document.getElementById("speciesGrid");
  if(!el) return;
  const qEl = document.getElementById("speciesSearch");
  const draw = ()=>{
    const q = (qEl?.value || "").toLowerCase();
    el.innerHTML = products.filter(p=>!q || p.name.toLowerCase().includes(q) || p.cat.toLowerCase().includes(q)).map(p=>`
      <article class="card grid overflow-hidden rounded-3xl md:grid-cols-[16rem_1fr]">
        <img src="${p.img}" alt="${p.name}" class="h-full min-h-56 w-full object-cover">
        <div class="p-5">
          <p class="kicker">${p.cat}</p>
          <h2 class="mt-1 text-2xl font-black text-emerald-950">${p.name}</h2>
          <p class="mt-3 text-sm leading-7 text-slate-700">${p.use}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="chip rounded-full px-3 py-2 text-xs font-black text-emerald-950">${productCount(p)} dataset matches</span>
            <a href="product_catalog.html" class="chip rounded-full px-3 py-2 text-xs font-black text-emerald-950">Product catalogue</a>
          </div>
        </div>
      </article>`).join("");
  };
  qEl?.addEventListener("input", draw);
  draw();
}

function boot(){
  setupChrome(document.body.dataset.title || "Bhutan NWFP Platform");
  renderStats();
  renderDzongDirectory();
  renderGroups();
  renderProducts();
  renderSpecies();
}
document.addEventListener("DOMContentLoaded", boot);
