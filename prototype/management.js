const CSV_URL = "downloads/national-nwfp-groups.csv";
const MAP_URL = "assets/nwfp-management-groups-bhutan.jpeg";

let groups = [];
let loggedInEmail = "";
let submissions = [
  {
    id: "sub-001",
    email: "tang.group@gmail.com",
    group: "Tangpa Shingmein Menrig Detshen",
    dzongkhag: "Bumthang",
    period: "2024-2034",
    file: "Tang_NWFP_plan.pdf",
    notes: "Updated medicinal plant list and harvest area.",
    status: "Pending review"
  },
  {
    id: "sub-002",
    email: "zangbi.group@gmail.com",
    group: "Zangbi NWFP Group",
    dzongkhag: "Trongsa",
    period: "2026-2031",
    file: "Zangbi_management_plan.pdf",
    notes: "Cane resource plan submitted for renewal.",
    status: "Pending review"
  }
];

const baseDocuments = [
  { title: "National NWFP Groups CSV", owner: "National registry", type: "CSV", status: "Current", href: CSV_URL },
  { title: "NWFP Management Groups Map", owner: "National spatial reference", type: "JPEG", status: "Current", href: MAP_URL },
  { title: "Tang Management Plan", owner: "Tang NWFP Group", type: "PDF", status: "Current", href: "../management_plans_nwfp/WCNP_Tang-NWFP.pdf" },
  { title: "Zangbi Management Plan", owner: "Zangbi NWFP Group", type: "PDF", status: "Current", href: "../management_plans_nwfp/RMNP_Zangbi_NWFP.pdf" },
  { title: "Daphne Management Plan", owner: "Sakteng Lhayul Sangzey Deytshen", type: "PDF", status: "Review", href: "../management_plans_nwfp/SWS_Daphne Management Plan_Yumzang_Semthuen_NWFP.pdf" },
  { title: "Resource Sites GeoJSON", owner: "GIS sample", type: "GEOJSON", status: "Sample", href: "downloads/sample-resource-sites.geojson" },
  { title: "Resource Sites Shapefile", owner: "GIS sample", type: "SHP", status: "Sample", href: "downloads/sample-resource-sites-shapefile.zip" }
];

const searchInput = document.querySelector("#opsSearch");
const statusFilter = document.querySelector("#statusFilter");
const registryTable = document.querySelector("#registryTable");
const toast = document.querySelector("#opsToast");

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];

    if (char === '"' && quoted && next === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") {
        index += 1;
      }
      row.push(cell);
      if (row.some((value) => value.trim())) {
        rows.push(row);
      }
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }

  const headers = rows.shift().map((header) => header.trim());
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, (values[index] || "").trim()])));
}

function deriveStatus(item) {
  const review = item["Review Status"].toLowerCase();
  const planPeriod = item["Plan Period"];
  if (review.includes("review") || review.includes("pending")) return "review";
  if (!planPeriod && !item["Estd year"]) return "draft";
  return "active";
}

function normalizeGroup(item) {
  return {
    sn: item.SN,
    group: item["Group Name"] || "Unnamed group",
    dzongkhag: item.Dzongkhag || "Not recorded",
    division: item["Division/Park"] || "Not recorded",
    gewog: item.Gewog || "Not recorded",
    village: item.Village || "Not recorded",
    members: Number.parseInt(item["Members (Nos)"], 10) || 0,
    female: Number.parseInt(item["Female (Nos)"], 10) || 0,
    area: Number.parseFloat(item["Area (ha)"]) || 0,
    established: item["Estd year"] || "Not recorded",
    planPeriod: item["Plan Period"] || "Not recorded",
    planType: item["Plan Type"] || "Not recorded",
    contact: item["Contact Details"] || "Not recorded",
    species: item.Species || item["Legacy Species"] || "Not recorded",
    source: item["Source Sheet"] || "Unknown source",
    status: deriveStatus(item)
  };
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2200);
}

function statusClass(status) {
  if (status === "active" || status === "Current") return "ok";
  if (status === "Approved") return "ok";
  if (status === "review" || status === "Review" || status === "Pending review") return "warn";
  if (status === "Returned") return "returned";
  return "draft";
}

function filteredGroups() {
  const query = searchInput.value.trim().toLowerCase();
  const status = statusFilter.value;
  return groups.filter((item) => {
    const matchesStatus = status === "all" || item.status === status;
    const matchesQuery = !query || [
      item.group,
      item.dzongkhag,
      item.division,
      item.gewog,
      item.village,
      item.species,
      item.planPeriod,
      item.status
    ].join(" ").toLowerCase().includes(query);
    return matchesStatus && matchesQuery;
  });
}

function updateStats() {
  const dzongkhags = new Set(groups.map((item) => item.dzongkhag).filter(Boolean));
  const totalMembers = groups.reduce((total, item) => total + item.members, 0);
  const planRecords = groups.filter((item) => item.planPeriod !== "Not recorded").length;
  document.querySelector("#activeGroupCount").textContent = formatNumber(groups.length);
  document.querySelector("#dzongkhagCount").textContent = formatNumber(dzongkhags.size);
  document.querySelector("#memberCount").textContent = formatNumber(totalMembers);
  document.querySelector("#planCount").textContent = formatNumber(planRecords);
}

function renderDashboardDetails() {
  const approved = submissions.filter((item) => item.status === "Approved").length;
  const pending = submissions.filter((item) => item.status === "Pending review").length;
  const returned = submissions.filter((item) => item.status === "Returned").length;
  const activeGroups = groups.filter((item) => item.status === "active").length;
  const reviewGroups = groups.filter((item) => item.status === "review").length;
  const draftGroups = groups.filter((item) => item.status === "draft").length;
  const totalArea = groups.reduce((total, item) => total + item.area, 0);
  const topDzongkhag = [...groups.reduce((map, item) => {
    map.set(item.dzongkhag, (map.get(item.dzongkhag) || 0) + 1);
    return map;
  }, new Map())].sort((a, b) => b[1] - a[1])[0];

  document.querySelector("#dashboardDetails").innerHTML = [
    { label: "Pending plan reviews", value: pending, detail: "Plans waiting for officer decision", tone: pending ? "warn" : "ok" },
    { label: "Approved submissions", value: approved, detail: "Plans approved in this session", tone: "ok" },
    { label: "Returned submissions", value: returned, detail: "Plans sent back for correction", tone: returned ? "returned" : "draft" },
    { label: "Registry status", value: `${activeGroups}/${reviewGroups}/${draftGroups}`, detail: "Active / review / draft group records", tone: "draft" },
    { label: "Mapped area", value: `${formatNumber(totalArea)} ha`, detail: "Total hectares recorded in the registry", tone: "ok" },
    { label: "Largest Dzongkhag set", value: topDzongkhag ? topDzongkhag[0] : "None", detail: `${topDzongkhag ? topDzongkhag[1] : 0} group records`, tone: "draft" }
  ].map((item) => `
    <article class="dashboard-card">
      <span>${item.label}</span>
      <strong>${item.value}</strong>
      <p>${item.detail}</p>
      <em class="tag ${item.tone}">${item.tone}</em>
    </article>
  `).join("");
}

function renderRegistry() {
  const rows = filteredGroups();
  registryTable.innerHTML = `
    <div class="data-row header">
      <span>Group</span><span>Dzongkhag</span><span>Gewog</span><span>Members</span><span>Species</span><span>Status</span>
    </div>
    ${rows.map((item) => `
      <div class="data-row">
        <strong>${item.group}</strong>
        <span>${item.dzongkhag}</span>
        <span>${item.gewog}</span>
        <span class="mono">${formatNumber(item.members)}</span>
        <span>${item.species}</span>
        <span class="tag ${statusClass(item.status)}">${item.status}</span>
      </div>
    `).join("") || `<div class="data-row"><strong>No records found</strong><span></span><span></span><span></span><span></span><span></span></div>`}
  `;
}

function renderQueue() {
  const noPlan = groups.filter((item) => item.planPeriod === "Not recorded").length;
  const noArea = groups.filter((item) => !item.area).length;
  const missingSpecies = groups.filter((item) => item.species === "Not recorded").length;
  const topDzongkhag = [...groups.reduce((map, item) => {
    map.set(item.dzongkhag, (map.get(item.dzongkhag) || 0) + 1);
    return map;
  }, new Map())].sort((a, b) => b[1] - a[1])[0];

  const queue = [
    { title: "Plan period missing", detail: `${formatNumber(noPlan)} group records need plan-period confirmation.`, level: noPlan ? "warn" : "ok" },
    { title: "Area field missing", detail: `${formatNumber(noArea)} records have no area value in hectares.`, level: noArea ? "warn" : "ok" },
    { title: "Species field check", detail: `${formatNumber(missingSpecies)} records have no species value.`, level: missingSpecies ? "warn" : "ok" },
    { title: "Largest Dzongkhag set", detail: `${topDzongkhag ? topDzongkhag[0] : "None"} has ${topDzongkhag ? topDzongkhag[1] : 0} records.`, level: "ok" }
  ];

  document.querySelector("#queueList").innerHTML = queue.map((item) => `
    <div class="queue-item">
      <div>
        <strong>${item.title}</strong>
        <span>${item.detail}</span>
      </div>
      <span class="tag ${item.level}">${item.level}</span>
    </div>
  `).join("");
}

function renderDocuments() {
  const submissionDocs = submissions.map((item) => ({
    title: item.file,
    owner: item.group,
    type: "PDF",
    status: item.status,
    href: "../management_plans_nwfp/WCNP_Tang-NWFP.pdf"
  }));
  document.querySelector("#documentGrid").innerHTML = [...submissionDocs, ...baseDocuments].map((item) => `
    <article class="document-card">
      <span class="file-icon">${item.type}</span>
      <div>
        <strong>${item.title}</strong>
        <span>${item.owner}</span>
      </div>
      <span class="tag ${statusClass(item.status)}">${item.status}</span>
      <footer>
        <a class="solid-button" href="${item.href}" download>Download</a>
        <a class="ghost-button" href="${item.href}" target="_blank" rel="noreferrer">Open</a>
      </footer>
    </article>
  `).join("");
}

function renderSubmissions() {
  const pending = submissions.filter((item) => item.status === "Pending review").length;
  document.querySelector("#reviewCount").textContent = `${pending} pending`;
  document.querySelector("#submissionList").innerHTML = submissions.map((item) => `
    <article class="submission-card">
      <header>
        <div>
          <strong>${item.group}</strong>
          <span>${item.email} · ${item.dzongkhag} · ${item.period}</span>
        </div>
        <span class="tag ${statusClass(item.status)}">${item.status}</span>
      </header>
      <p>${item.file} — ${item.notes || "No reviewer note submitted."}</p>
      <div class="submission-actions">
        <button class="solid-button" data-plan-approve="${item.id}">Approve</button>
        <button class="ghost-button" data-plan-return="${item.id}">Return for correction</button>
      </div>
    </article>
  `).join("");
}

function renderApprovalBoard() {
  const columns = [
    { title: "Pending review", status: "Pending review" },
    { title: "Approved", status: "Approved" },
    { title: "Returned", status: "Returned" }
  ];

  document.querySelector("#approvalBoard").innerHTML = columns.map((column) => {
    const cards = submissions.filter((item) => item.status === column.status);
    return `
      <section class="approval-column">
        <h3>${column.title}</h3>
        ${cards.map((item) => `
          <article class="approval-card">
            <strong>${item.group}</strong>
            <span>${item.dzongkhag} · ${item.period}</span>
            <span>${item.file}</span>
            <em class="tag ${statusClass(item.status)}">${item.status}</em>
          </article>
        `).join("") || `<p class="empty-note">No plans in this stage.</p>`}
      </section>
    `;
  }).join("");
}

function renderLayers() {
  const dzongkhags = new Set(groups.map((item) => item.dzongkhag)).size;
  const layers = [
    { name: "National_NWFP_Groups", type: "CSV registry", records: groups.length, file: "national-nwfp-groups.csv" },
    { name: "NWFP Management Groups in Bhutan", type: "Reference map", records: dzongkhags, file: "nwfp-management-groups-bhutan.jpeg" },
    { name: "sample_resource_sites", type: "GeoJSON points", records: 4, file: "sample-resource-sites.geojson" },
    { name: "sample_resource_sites_shp", type: "Shapefile package", records: 4, file: "sample-resource-sites-shapefile.zip" }
  ];

  document.querySelector("#layerList").innerHTML = layers.map((item) => `
    <div class="layer-item">
      <strong>${item.name}</strong>
      <span>${item.type} · ${formatNumber(item.records)} records · ${item.file}</span>
    </div>
  `).join("");
}

function renderAudit() {
  const audit = [
    { actor: "System", action: `Loaded ${formatNumber(groups.length)} records from National_NWFP_Groups.csv`, time: "Current session" },
    { actor: "Group portal", action: `${formatNumber(submissions.length)} management plan submissions in review workflow`, time: "Current session" },
    { actor: "GIS Officer", action: "Attached NWFP Management Groups in Bhutan.jpeg", time: "Current session" },
    { actor: "Data Officer", action: "Validated registry columns and searchable fields", time: "Current session" },
    { actor: "Admin", action: "Separated management console from marketplace", time: "Current session" }
  ];

  document.querySelector("#auditList").innerHTML = audit.map((item) => `
    <div class="audit-item">
      <strong>${item.action}</strong>
      <span>${item.actor} · ${item.time}</span>
    </div>
  `).join("");
}

function renderAll() {
  updateStats();
  renderDashboardDetails();
  renderRegistry();
  renderQueue();
  renderSubmissions();
  renderApprovalBoard();
  renderDocuments();
  renderLayers();
  renderAudit();
}

async function loadGroups() {
  try {
    const response = await fetch(CSV_URL);
    if (!response.ok) throw new Error(`CSV returned ${response.status}`);
    const text = await response.text();
    groups = parseCsv(text).map(normalizeGroup);
    renderAll();
  } catch (error) {
    groups = [];
    renderAll();
    showToast(`Could not load CSV: ${error.message}`);
  }
}

document.addEventListener("click", (event) => {
  const sectionButton = event.target.closest("[data-section]");
  const fakeAction = event.target.closest("[data-fake-action]");
  const approve = event.target.closest("[data-plan-approve]");
  const returnPlan = event.target.closest("[data-plan-return]");

  if (sectionButton) {
    document.querySelectorAll("[data-section]").forEach((button) => {
      button.classList.toggle("active", button === sectionButton);
    });
    document.querySelectorAll(".ops-section").forEach((section) => {
      section.classList.toggle("active", section.id === sectionButton.dataset.section);
    });
  }

  if (fakeAction) {
    showToast(`${fakeAction.dataset.fakeAction} queued`);
  }

  if (approve) {
    const submission = submissions.find((item) => item.id === approve.dataset.planApprove);
    if (submission) {
      submission.status = "Approved";
      renderAll();
      showToast(`${submission.group} plan approved`);
    }
  }

  if (returnPlan) {
    const submission = submissions.find((item) => item.id === returnPlan.dataset.planReturn);
    if (submission) {
      submission.status = "Returned";
      renderAll();
      showToast(`${submission.group} plan returned for correction`);
    }
  }
});

document.querySelector("#gmailLoginButton").addEventListener("click", () => {
  loggedInEmail = document.querySelector("#groupEmail").value || "nwfp.group@gmail.com";
  document.querySelector("#groupEmail").value = loggedInEmail;
  const loginState = document.querySelector("#loginState");
  loginState.textContent = `Signed in: ${loggedInEmail}`;
  loginState.className = "tag ok";
  showToast("Gmail login simulated for prototype");
});

document.querySelector("#planForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const email = document.querySelector("#groupEmail").value.trim();
  const group = document.querySelector("#planGroup").value.trim();
  const dzongkhag = document.querySelector("#planDzongkhag").value.trim();
  const period = document.querySelector("#planPeriod").value.trim();
  const fileInput = document.querySelector("#planFile");
  const notes = document.querySelector("#planNotes").value.trim();

  if (!email.endsWith("@gmail.com")) {
    showToast("Use a Gmail address for group login in this prototype");
    return;
  }

  if (!loggedInEmail) {
    loggedInEmail = email;
    const loginState = document.querySelector("#loginState");
    loginState.textContent = `Signed in: ${loggedInEmail}`;
    loginState.className = "tag ok";
  }

  submissions.unshift({
    id: `sub-${Date.now()}`,
    email,
    group,
    dzongkhag,
    period,
    file: fileInput.files[0]?.name || "submitted-management-plan.pdf",
    notes,
    status: "Pending review"
  });

  event.target.reset();
  document.querySelector("#groupEmail").value = loggedInEmail;
  renderAll();
  showToast("Plan submitted for officer review");
});

document.querySelector("#syncButton").addEventListener("click", () => {
  loadGroups();
  showToast("National registry reloaded");
});

searchInput.addEventListener("input", renderRegistry);
statusFilter.addEventListener("change", renderRegistry);

loadGroups();
