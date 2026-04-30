(function(){
  const plans = window.NWFP_PLANS || [];
  if(!plans.length) return;

  const fmt = n => Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 1 });
  const pct = (v, total) => total ? Math.round((v / total) * 100) : 0;
  const present = v => v !== null && v !== undefined && String(v).trim() !== "";
  const by = key => plans.reduce((m, p) => {
    const value = p[key] || "Unknown";
    m[value] ||= [];
    m[value].push(p);
    return m;
  }, {});
  const sum = (rows, key) => rows.reduce((n, p) => n + Number(p[key] || 0), 0);
  const countWhere = fn => plans.filter(fn).length;

  function setHTML(id, html){
    const el = document.getElementById(id);
    if(el) el.innerHTML = html;
  }

  function chip(label, value, note){
    return `<div class="metric">
      <div class="metric-label">${label}</div>
      <div class="metric-value">${value}</div>
      <div class="metric-note">${note}</div>
    </div>`;
  }

  function bar(label, value, total, note){
    const width = Math.max(4, pct(value, total));
    return `<div class="bar-row">
      <div class="bar-row-head"><strong>${label}</strong><span>${fmt(value)} / ${fmt(total)}</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <div class="bar-sub">${note}</div>
    </div>`;
  }

  const palette = ["#f0c848", "#c9a227", "#8a6d18", "#c46c35", "#f3e8ce", "#7c6a32", "#d9b74a"];

  function groupedCounts(key){
    return Object.entries(plans.reduce((m, p) => {
      const value = p[key] || "Unknown";
      m[value] = (m[value] || 0) + 1;
      return m;
    }, {})).map(([name, value]) => ({ name, value })).sort((a,b) => b.value - a.value);
  }

  function donut(id, title, subtitle, rows){
    const totalValue = rows.reduce((n, r) => n + Number(r.value || 0), 0) || 1;
    let cursor = 0;
    const stops = rows.map((r, i) => {
      const start = cursor;
      cursor += (Number(r.value || 0) / totalValue) * 100;
      const color = r.color || palette[i % palette.length];
      return `${color} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`;
    }).join(", ");
    setHTML(id, `
      <div class="flex h-full flex-col">
        <p class="kicker mb-1">${subtitle}</p>
        <h3 class="section-title mb-4" style="font-size:1.35rem">${title}</h3>
        <div class="pie-plot" style="background:conic-gradient(${stops})">
          <div class="pie-hole">
            <strong style="font-family:'Cormorant Garamond',serif;font-size:1.8rem;color:#f0ece0;line-height:1">${fmt(totalValue)}</strong>
            <span style="font-size:0.62rem;color:rgba(240,236,224,0.58);font-weight:700;text-transform:uppercase;letter-spacing:.12em">Total</span>
          </div>
        </div>
        <div class="chart-legend">
          ${rows.map((r, i) => `
            <div class="legend-item">
              <span class="legend-name"><span class="legend-dot" style="background:${r.color || palette[i % palette.length]}"></span><span>${r.name}</span></span>
              <strong>${fmt(r.value)} (${pct(r.value, totalValue)}%)</strong>
            </div>
          `).join("")}
        </div>
      </div>
    `);
  }

  function extractYear(p){
    const planYear = String(p.plan || "").match(/\b(20\d{2}|19\d{2})\b/);
    if(planYear) return Number(planYear[1]);
    if(p.est) return Number(p.est);
    return null;
  }

  const total = plans.length;
  const docs = countWhere(p => present(p.pdf));
  const areaRows = plans.filter(p => Number(p.area || 0) > 0);
  const hhRows = plans.filter(p => Number(p.hh || 0) > 0);
  const planRows = plans.filter(p => present(p.plan));
  const speciesRows = plans.filter(p => present(p.species) && !/^mixed nwfps?$/i.test(String(p.species).trim()));
  const missingDocs = plans.filter(p => !present(p.pdf));
  const missingArea = plans.filter(p => !Number(p.area || 0));
  const unknownType = plans.filter(p => (p.ptype || "unknown") === "unknown");
  const inactive = plans.filter(p => p.status !== "active");
  const totalArea = sum(plans, "area");
  const totalHH = sum(plans, "hh");
  const statusCounts = groupedCounts("status");
  const typeCounts = groupedCounts("ptype");

  setHTML("advancedMetrics", [
    chip("Documentation rate", `${pct(docs, total)}%`, `${docs} of ${total} records have linked documents`),
    chip("Area coverage", `${pct(areaRows.length, total)}%`, `${areaRows.length} records include management area`),
    chip("HH coverage", `${pct(hhRows.length, total)}%`, `${hhRows.length} records include household count`),
    chip("Avg area / known plan", `${fmt(totalArea / Math.max(areaRows.length, 1))} ha`, `${fmt(totalArea)} ha across known records`)
  ].join(""));

  setHTML("qualityBars", [
    bar("Linked document", docs, total, "PDF or file path present"),
    bar("Plan period", planRows.length, total, "Plan year range recorded"),
    bar("Management area", areaRows.length, total, "Area value above zero"),
    bar("Households", hhRows.length, total, "Member household count recorded"),
    bar("Specific species", speciesRows.length, total, "Species listed beyond generic mixed NWFPs")
  ].join(""));

  const dzongGroups = Object.entries(by("dzong")).map(([name, rows]) => ({
    name, count: rows.length, area: sum(rows, "area"), hh: sum(rows, "hh"), docs: rows.filter(p => present(p.pdf)).length
  })).sort((a,b) => b.count - a.count);
  const divGroups = Object.entries(by("div")).map(([name, rows]) => ({
    name, count: rows.length, area: sum(rows, "area"), hh: sum(rows, "hh"), docs: rows.filter(p => present(p.pdf)).length
  })).sort((a,b) => b.count - a.count);
  const top4 = dzongGroups.slice(0, 4).reduce((n, d) => n + d.count, 0);
  const largestArea = dzongGroups.slice().sort((a,b) => b.area - a.area)[0];
  const busiestOffice = divGroups[0];
  const docGapOffice = divGroups.slice().sort((a,b) => (b.count - b.docs) - (a.count - a.docs))[0];

  const areaPieRows = dzongGroups.slice().sort((a,b) => b.area - a.area).slice(0, 5).map(d => ({ name: d.name, value: d.area }));
  const areaOther = Math.max(0, totalArea - areaPieRows.reduce((n, d) => n + d.value, 0));
  if(areaOther) areaPieRows.push({ name: "Other", value: areaOther, color: "rgba(240,236,224,0.35)" });

  donut("statusPie", "Status share", "Pie chart", statusCounts.map((d, i) => ({
    name: d.name,
    value: d.value,
    color: i === 0 ? "#f0c848" : "#c46c35"
  })));
  donut("ptypePie", "Plan type share", "Pie chart", typeCounts.map((d, i) => ({
    name: d.name,
    value: d.value,
    color: palette[i % palette.length]
  })));
  donut("documentPie", "Document coverage", "Donut chart", [
    { name: "Linked document", value: docs, color: "#f0c848" },
    { name: "Missing document", value: missingDocs.length, color: "#c46c35" }
  ]);
  donut("areaPie", "Area share by Dzongkhag", "Pie chart", areaPieRows);

  const years = plans.reduce((m, p) => {
    const year = extractYear(p);
    if(year) m[year] = (m[year] || 0) + 1;
    return m;
  }, {});
  const yearRows = Object.entries(years).map(([year, value]) => ({ year, value })).sort((a,b) => Number(a.year) - Number(b.year));
  const maxYear = Math.max(...yearRows.map(y => y.value), 1);
  setHTML("yearColumnChart", yearRows.map(y => `
    <div class="vertical-bar">
      <strong>${y.value}</strong>
      <div class="vertical-bar-fill" style="height:${Math.max(0.8, (y.value / maxYear) * 11)}rem"></div>
      <span>${y.year}</span>
    </div>
  `).join(""));

  const stackRows = dzongGroups.slice(0, 10);
  const maxStack = Math.max(...stackRows.map(d => d.count), 1);
  setHTML("documentStackBars", stackRows.map(d => {
    const gap = d.count - d.docs;
    return `<div class="stack-row">
      <div class="bar-row-head">
        <strong>${d.name}</strong>
        <span>${d.docs} docs / ${gap} gaps</span>
      </div>
      <div class="stack-track" title="${d.name}: ${d.docs} documented, ${gap} gaps">
        <div class="stack-doc" style="width:${pct(d.docs, maxStack)}%"></div>
        <div class="stack-gap" style="width:${pct(gap, maxStack)}%"></div>
      </div>
    </div>`;
  }).join(""));

  setHTML("concentrationPanel", [
    `<div class="metric"><div class="metric-label">Top 4 Dzongkhags</div><div class="metric-value">${pct(top4, total)}%</div><div class="metric-note">${top4} of ${total} records</div></div>`,
    `<div class="metric"><div class="metric-label">Largest area Dzongkhag</div><div class="metric-value">${largestArea.name}</div><div class="metric-note">${fmt(largestArea.area)} ha reported</div></div>`,
    `<div class="metric"><div class="metric-label">Busiest office / park</div><div class="metric-value">${busiestOffice.name}</div><div class="metric-note">${busiestOffice.count} records, ${fmt(busiestOffice.area)} ha</div></div>`,
    `<div class="metric"><div class="metric-label">Largest document gap</div><div class="metric-value">${docGapOffice.name}</div><div class="metric-note">${docGapOffice.count - docGapOffice.docs} records without linked documents</div></div>`
  ].join(""));

  const stop = new Set(["mixed","nwfps","nwfp","spp","spp.","other","plants","plant","medicinal","herbs","herbal","and","the"]);
  const termCounts = {};
  plans.forEach(p => String(p.species || "").split(/[,\(\)\/]+/).forEach(raw => {
    let term = raw.trim().replace(/\s+/g, " ");
    if(!term || /^mixed nwfps?$/i.test(term)) return;
    const key = term.toLowerCase();
    if(stop.has(key)) return;
    termCounts[term] = (termCounts[term] || 0) + 1;
  }));
  const species = Object.entries(termCounts).sort((a,b) => b[1] - a[1]).slice(0, 24);
  const maxSpecies = Math.max(...species.map(([,count]) => count), 1);
  setHTML("speciesCloud", species.map(([name, count]) => {
    const weight = 0.75 + (count / maxSpecies) * 0.55;
    return `<span class="rounded-full px-3 py-2 text-xs font-bold" style="font-size:${weight}rem;background:rgba(201,162,39,0.12);border:1px solid rgba(201,162,39,0.24);color:var(--cream)">${name} · ${count}</span>`;
  }).join(""));

  const flags = [
    ["Missing documents", missingDocs.length, "Records without linked plan documents or file paths"],
    ["Missing area", missingArea.length, "Records excluded from area concentration analytics"],
    ["Unknown plan type", unknownType.length, "Records needing new/revised/other classification"],
    ["Inactive records", inactive.length, "Groups marked outside active status"]
  ];
  setHTML("priorityFlags", flags.map(([label, value, note]) => `
    <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(201,162,39,0.18);border-radius:0.875rem;padding:1rem">
      <div class="metric-label">${label}</div>
      <div class="metric-value" style="font-size:2.2rem;color:#f0c848">${value}</div>
      <div class="metric-note">${note}</div>
    </div>
  `).join(""));

  const priority = plans.map(p => {
    const issues = [];
    if(!present(p.pdf)) issues.push("missing document");
    if(!Number(p.area || 0)) issues.push("missing area");
    if(!Number(p.hh || 0)) issues.push("missing HH");
    if((p.ptype || "unknown") === "unknown") issues.push("unknown type");
    if(p.status !== "active") issues.push("inactive");
    return { p, issues, score: issues.length + (Number(p.area || 0) > 10000 ? 1 : 0) };
  }).filter(x => x.issues.length).sort((a,b) => b.score - a.score || Number(b.p.area || 0) - Number(a.p.area || 0)).slice(0, 14);

  setHTML("priorityRows", priority.map(({p, issues}) => `
    <tr>
      <td><strong>${p.group}</strong></td>
      <td>${p.dzong || "-"}</td>
      <td>${p.div || "-"}</td>
      <td>${issues.join(", ")}</td>
      <td>${p.area ? fmt(p.area) + " ha" : "-"}</td>
      <td>${p.hh ? fmt(p.hh) : "-"}</td>
    </tr>
  `).join(""));
  setHTML("priorityCount", `${priority.length} high-priority records shown`);

  const insightText = [
    `Document coverage is ${pct(docs, total)}%, but ${missingDocs.length} records still need linked evidence.`,
    `${pct(areaRows.length, total)}% of records have usable area values, so area analytics should be treated as partial.`,
    `The top four Dzongkhags hold ${pct(top4, total)}% of the plan registry, indicating a concentrated operational portfolio.`,
    `${species.length} recurring product/species terms were detected from the species field.`
  ];
  const notes = document.querySelector(".card-dark ul");
  if(notes){
    notes.innerHTML = insightText.map(t => `<li>${t}</li>`).join("");
  }
})();
