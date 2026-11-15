(() => {
  const $ = (id) => document.getElementById(id);
  const st = { skills: [], role: null, meta: null };
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
  const post = (url, body) => fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(r => r.json());
  const note = (text, kind) => { const m = $("msg"); m.innerHTML = ""; if (text) m.appendChild(el("div", "alert-x " + kind, text)); };

  // Opens LinkedIn's own job search for a role (no scraping, no LinkedIn account needed to build the link).
  const jobsUrl = (role) => {
    const q = new URLSearchParams({ keywords: role });
    if ($("loc").value.trim()) q.set("location", $("loc").value.trim());
    if ($("lvl").value) q.set("f_E", $("lvl").value);
    return "https://www.linkedin.com/jobs/search/?" + q.toString();
  };
  const jobsLink = (role, label) => { const a = el("a", "btn btn-jobs", label || "Find jobs"); a.href = jobsUrl(role); a.target = "_blank"; a.rel = "noopener noreferrer"; a.setAttribute("aria-label", "Find " + role + " jobs on LinkedIn (opens in a new tab)"); return a; };

  async function init() {
    st.meta = await (await fetch("/api/meta")).json();
    const m = st.meta, best = m.models.find(x => x.Model === m.best);
    $("st-roles").textContent = Object.keys(m.roles).length;
    $("st-skills").textContent = m.skills.length;
    $("st-acc").textContent = Math.round(best["F1-score (macro)"] * 100) + "%";
    $("skillList").append(...m.skills.map(s => { const o = el("option"); o.value = s; return o; }));
    $("model").append(...m.models.map(x => { const o = el("option", null, x.Model + (x.Model === m.best ? " (best)" : "")); o.value = x.Model; if (x.Model === m.best) o.selected = true; return o; }));
    $("modelNote").textContent = `Trained on ${m.n_train} samples and tested on ${m.n_test} held-out samples. The best model by F1-score is used by default.`;
    $("mbody").append(...m.models.map(x => { const tr = el("tr"); tr.append(el("td", null, x.Model), el("td", null, (x.Accuracy * 100).toFixed(1) + "%"), el("td", null, (x["F1-score (macro)"] * 100).toFixed(1) + "%")); const t = el("td"); if (x.Model === m.best) t.append(el("span", "best", "Best")); tr.append(t); return tr; }));
    const grid = $("roleGrid");
    Object.entries(m.roles).forEach(([role, skills]) => {
      const col = el("div", "col-md-6 col-lg-4 mb-4"), card = el("div", "role"); card.append(el("h4", null, role));
      skills.forEach(s => card.append(el("span", "chip", s)));
      const b = el("button", "btn btn-brand btn-sm mt-3 no-print", "Check my gap"); b.onclick = () => { if (!st.skills.length) { location.hash = "#analyzer"; note("Add your skills first, then pick a role.", "info"); return; } st.role = role; location.hash = "#analyzer"; recommend(true); };
      card.append(el("div")); card.lastChild.append(b); col.append(card); grid.append(col);
    });
  }

  function renderChips() {
    const box = $("chips"); box.innerHTML = "";
    if (!st.skills.length) { box.append(el("span", "text-muted", "No skills yet.")); return; }
    st.skills.forEach(s => { const c = el("span", "chip", s), x = el("button", null, "\u00d7"); x.type = "button"; x.setAttribute("aria-label", "Remove " + s); x.onclick = () => { st.skills = st.skills.filter(k => k !== s); renderChips(); recommend(); }; c.append(x); box.append(c); });
  }

  async function recommend(keepRole) {
    const box = $("recs");
    if (!st.skills.length) { box.innerHTML = '<p class="text-muted mb-0">Add skills to see recommendations.</p>'; $("gap").innerHTML = '<p class="text-muted mb-0">Select a role above.</p>'; $("gapRole").textContent = ""; return; }
    const { recommendations } = await post("/api/recommend", { skills: st.skills, model: $("model").value });
    box.innerHTML = "";
    recommendations.forEach(r => {
      const row = el("div", "rec" + (r.role === st.role ? " sel" : "")), bar = el("div", "bar"), fill = el("i");
      fill.style.width = r.score + "%"; bar.append(fill);
      const b = el("button", "btn", "Analyze gap"); b.type = "button"; b.onclick = () => { st.role = r.role; recommend(true); };
      const act = el("div", "acts"); act.append(b, jobsLink(r.role, "Find jobs")); row.append(el("strong", null, r.role + " (" + r.score + "%)"), bar, act); box.append(row);
    });
    if (st.role) gap();
  }

  async function gap() {
    const g = await post("/api/gap", { skills: st.skills, role: st.role }), box = $("gap");
    $("gapRole").textContent = "for " + st.role; box.innerHTML = "";
    const top = el("div", "d-flex align-items-center flex-wrap"), ring = el("div", "ring"); ring.style.setProperty("--p", g.match_percent);
    ring.append(el("span", null, Math.round(g.match_percent) + "%")); ring.setAttribute("role", "img"); ring.setAttribute("aria-label", g.match_percent + " percent match");
    const side = el("div", "ml-3"); side.append(el("strong", null, "Skill match"), el("p", "text-muted mb-0", g.matched.length + " of " + (g.matched.length + g.missing.length) + " required skills")); top.append(ring, side); box.append(top);
    const sec = (title, arr, cls) => { box.append(el("h4", "mt-4", title)); const w = el("div"); (arr.length ? arr : ["None"]).forEach(s => w.append(el("span", "chip " + (arr.length ? cls : ""), s))); box.append(w); };
    sec("Matched skills", g.matched, "ok"); sec("Missing skills", g.missing, "bad");
    if (g.priority.length) { box.append(el("h4", "mt-4", "Learning priority")); const ol = el("ol", "road pl-3"); g.priority.forEach(p => { const li = el("li", null, p.skill + " "); li.append(el("small", null, "(needed by " + p.roles + " role" + (p.roles > 1 ? "s" : "") + ")")); ol.append(li); }); box.append(ol); }
    const bar2 = el("div", "mt-3 no-print"), pr = el("button", "btn btn-brand mr-2", "Download report (PDF)"); pr.onclick = () => window.print(); const jl = jobsLink(st.role, "View " + st.role + " jobs on LinkedIn"); jl.classList.add("mt-2"); bar2.append(pr, jl); box.append(bar2);
  }

  async function upload(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) return note("Please choose a PDF file.", "err");
    if (file.size > 4 * 1024 * 1024) return note("File is too large (max 4 MB).", "err");
    note("Reading your resume...", "info");
    const fd = new FormData(); fd.append("resume", file);
    try {
      const res = await fetch("/api/extract", { method: "POST", body: fd }), data = await res.json();
      if (!res.ok) return note(data.error || "Upload failed.", "err");
      st.skills = data.skills; st.role = null; renderChips();
      note(data.skills.length ? data.skills.length + " skills found. Review them below." : "No listed skills were found (scanned PDFs have no text). Add skills manually.", data.skills.length ? "info" : "err");
      recommend();
    } catch (e) { note("Could not reach the server.", "err"); }
  }

  const drop = $("drop"), file = $("file");
  file.onchange = () => upload(file.files[0]);
  drop.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); file.click(); } };
  ["dragenter", "dragover"].forEach(t => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach(t => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => upload(e.dataTransfer.files[0]));
  $("addForm").onsubmit = (e) => { e.preventDefault(); const v = $("addSkill").value.trim(), hit = st.meta.skills.find(s => s.toLowerCase() === v.toLowerCase());
    if (!hit) return note(v ? '"' + v + '" is not in the listed skills.' : "", "err");
    note("", ""); if (!st.skills.includes(hit)) { st.skills.push(hit); st.skills.sort(); } $("addSkill").value = ""; renderChips(); recommend(); };
  $("model").onchange = () => recommend();
  $("loc").oninput = $("lvl").onchange = () => recommend();
  init();
})();
