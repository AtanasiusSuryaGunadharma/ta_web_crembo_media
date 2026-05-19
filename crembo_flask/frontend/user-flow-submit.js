(function () {
  var SUPABASE_URL = "https://lzdcuvyxksyoozvhcfyj.supabase.co";
  var SUPABASE_PUBLISHABLE_KEY = "sb_publishable_xWcnjZtOOVDrEP1-Q2npng_eUqPpceM";
  var TABLE_NAME = "user_flow_submissions";
  var LOCAL_SUBMISSION_PREFIX = "crembo-user-flow-submission";

  function byId(id) { return document.getElementById(id); }

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function textOf(el) {
    return String((el && el.textContent) || "").replace(/\s+/g, " ").trim();
  }

  function valueOf(id) {
    var el = byId(id);
    return String((el && el.value) || "").trim();
  }

  function roleLabel(flowSlug) {
    if (flowSlug === "super-admin") return "Super Admin";
    if (flowSlug === "admin") return "Admin";
    if (flowSlug === "anggota") return "Anggota";
    return valueOf("testerRole") || "Role";
  }

  function setInvalid(el, state) {
    if (!el) return;
    el.classList.toggle("is-invalid", Boolean(state));
    if (state) el.setAttribute("aria-invalid", "true");
    else el.removeAttribute("aria-invalid");
  }

  function calculateSus() {
    var answers = [];
    var rows = Array.prototype.slice.call(document.querySelectorAll(".sus-table tbody tr"));
    for (var i = 1; i <= 10; i += 1) {
      var checked = document.querySelector('input[name="sus' + i + '"]:checked');
      var value = checked ? Number(checked.value) : null;
      var row = rows[i - 1];
      answers.push({
        no: i,
        question: row && row.children && row.children[1] ? textOf(row.children[1]) : "SUS " + i,
        value: value,
        contribution: value ? (i % 2 === 1 ? value - 1 : 5 - value) : null
      });
    }

    if (answers.some(function (item) { return !item.value; })) {
      return { score: null, category: "Belum lengkap", grade: "-", answers: answers };
    }

    var raw = answers.reduce(function (sum, item) { return sum + Number(item.contribution || 0); }, 0);
    var score = raw * 2.5;
    var category = "Not Acceptable";
    var grade = "F";
    if (score >= 85) { category = "Excellent"; grade = "A"; }
    else if (score >= 73) { category = "Good"; grade = "B"; }
    else if (score >= 68) { category = "Acceptable"; grade = "C"; }
    else if (score >= 51) { category = "Marginal"; grade = "D"; }
    return { score: score, category: category, grade: grade, answers: answers };
  }

  function collectIdentity(flowSlug) {
    return {
      tester_name: valueOf("testerName"),
      tester_role: valueOf("testerRole") || roleLabel(flowSlug),
      tester_org: valueOf("testerOrg"),
      test_date: valueOf("testDate"),
      tester_device: valueOf("testerDevice"),
      tester_browser: valueOf("testerBrowser"),
      user_agent: String(navigator.userAgent || "")
    };
  }

  function collectBlackbox() {
    var resultInputs = Array.prototype.slice.call(document.querySelectorAll("input[data-result]"));
    var groups = {};
    resultInputs.forEach(function (input) {
      var name = input.name;
      if (!groups[name]) {
        var checkRow = input.closest(".check-row");
        var card = input.closest(".scenario-card");
        var section = input.closest(".test-section");
        var detailItems = [];
        if (card) {
          Array.prototype.slice.call(card.querySelectorAll(".mini-grid div")).forEach(function (box) {
            var label = textOf(box.querySelector("b"));
            var value = textOf(box.querySelector("span"));
            if (label || value) detailItems.push({ label: label, value: value });
          });
        }
        groups[name] = {
          name: name,
          case_id: input.getAttribute("data-case") || textOf(card && card.querySelector(".code")),
          flow_section: textOf(section && section.querySelector(".test-head h3")),
          step_no: textOf(card && card.querySelector(".card-number")),
          step_title: textOf(card && card.querySelector("h4")),
          question: textOf(checkRow && checkRow.querySelector("span")),
          instruction: textOf(card && card.querySelector("details ol")),
          scenario_details: detailItems,
          answer: "",
          answer_value: "",
          is_valid: null
        };
      }
      if (input.checked) {
        groups[name].answer_value = input.value;
        groups[name].answer = input.value === "valid" ? "Valid" : "Tidak Valid";
        groups[name].is_valid = input.value === "valid";
      }
    });
    return Object.keys(groups).map(function (name) { return groups[name]; });
  }

  function collectAdditional() {
    var ids = ["open1", "open2", "open3", "open4"];
    return ids.map(function (id, idx) {
      var el = byId(id);
      var label = el && el.closest(".field") ? textOf(el.closest(".field").querySelector("label")) : "Pertanyaan Tambahan " + (idx + 1);
      label = label.replace(/\(Opsional\)/gi, "").replace(/\s+/g, " ").trim();
      return { no: idx + 1, id: id, question: label, answer: valueOf(id) };
    });
  }

  function buildPayload(flowSlug) {
    var identity = collectIdentity(flowSlug);
    var blackbox = collectBlackbox();
    var sus = calculateSus();
    var additional = collectAdditional();
    var validCount = blackbox.filter(function (item) { return item.answer_value === "valid"; }).length;
    var invalidCount = blackbox.filter(function (item) { return item.answer_value === "invalid"; }).length;
    var pendingCount = blackbox.filter(function (item) { return !item.answer_value; }).length;

    return {
      version: "2026-05-user-flow-static-v2",
      source_page: String(location.pathname || "").split("/").pop() || "user-flow.html",
      flow_slug: flowSlug,
      role_name: roleLabel(flowSlug),
      submitted_at: new Date().toISOString(),
      identity: identity,
      summary: {
        blackbox_total: blackbox.length,
        blackbox_valid: validCount,
        blackbox_invalid: invalidCount,
        blackbox_pending: pendingCount,
        sus_score: sus.score,
        sus_category: sus.category,
        sus_grade: sus.grade
      },
      blackbox: blackbox,
      sus: sus,
      additional: additional
    };
  }

  function renderResult(message, type, extraHtml) {
    var resultBox = byId("resultBox");
    if (!resultBox) return;
    var color = type === "error" ? "#991b1b" : (type === "success" ? "#166534" : "#1e3a8a");
    resultBox.innerHTML = "<b style='color:" + color + "'>" + esc(message) + "</b>" + (extraHtml || "");
  }

  function validateRequired() {
    var missing = [];
    var requiredFields = [
      ["testerName", "Nama Penguji"],
      ["testerRole", "Role yang Diuji"],
      ["testerOrg", "Instansi / Unit / Kelas"],
      ["testDate", "Tanggal Pengujian"],
      ["testerDevice", "Perangkat"],
      ["testerBrowser", "Browser"]
    ];

    requiredFields.forEach(function (pair) {
      var el = byId(pair[0]);
      var empty = !el || !String(el.value || "").trim();
      setInvalid(el, empty);
      if (empty) missing.push(pair[1]);
    });

    var resultInputs = Array.prototype.slice.call(document.querySelectorAll("input[data-result]"));
    var groupNames = Array.from(new Set(resultInputs.map(function (input) { return input.name; })));
    var missingBlackbox = groupNames.filter(function (name) {
      return !resultInputs.some(function (input) { return input.name === name && input.checked; });
    });
    if (missingBlackbox.length) missing.push(missingBlackbox.length + " checklist Black Box belum dipilih");

    var missingSus = [];
    for (var i = 1; i <= 10; i += 1) {
      if (!document.querySelector('input[name="sus' + i + '"]:checked')) missingSus.push(i);
    }
    if (missingSus.length) missing.push("SUS nomor " + missingSus.join(", "));

    if (missing.length) {
      renderResult("Data wajib belum lengkap.", "error", "<span>" + esc(missing.slice(0, 6).join("; ")) + (missing.length > 6 ? "; dan beberapa data wajib lainnya." : "") + "</span>");
      alert("Lengkapi data wajib terlebih dahulu:\n- " + missing.join("\n- "));
      return false;
    }
    return true;
  }

  function supabaseHeaders(extra) {
    var headers = {
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Authorization: "Bearer " + SUPABASE_PUBLISHABLE_KEY,
      "Content-Type": "application/json"
    };
    if (extra) {
      Object.keys(extra).forEach(function (key) { headers[key] = extra[key]; });
    }
    return headers;
  }

  async function supabaseRequest(method, path, body, extraHeaders) {
    var options = {
      method: method,
      headers: supabaseHeaders(extraHeaders)
    };
    if (body !== undefined) options.body = JSON.stringify(body);
    var response = await fetch(SUPABASE_URL + path, options);
    var text = await response.text();
    var data = text ? JSON.parse(text) : null;
    if (!response.ok) {
      var message = data && (data.message || data.error_description || data.error) ? (data.message || data.error_description || data.error) : "Request Supabase gagal";
      throw new Error(message);
    }
    return data;
  }

  async function submitPayload(payload) {
    var record = {
      flow_slug: payload.flow_slug,
      role_name: payload.role_name,
      tester_full_name: payload.identity.tester_name,
      tester_role: payload.identity.tester_role,
      tester_org: payload.identity.tester_org,
      test_date: payload.identity.test_date,
      tester_device: payload.identity.tester_device,
      tester_browser: payload.identity.tester_browser,
      blackbox_total: payload.summary.blackbox_total,
      blackbox_valid: payload.summary.blackbox_valid,
      blackbox_invalid: payload.summary.blackbox_invalid,
      blackbox_pending: payload.summary.blackbox_pending,
      sus_score: payload.summary.sus_score,
      sus_category: payload.summary.sus_category,
      sus_grade: payload.summary.sus_grade,
      payload: payload
    };
    return await supabaseRequest("POST", "/rest/v1/" + TABLE_NAME, record, { Prefer: "return=representation" });
  }

  function updateFooterNote() {
    var notes = Array.prototype.slice.call(document.querySelectorAll(".footer-note"));
    notes.forEach(function (note) {
      if (/Integrasi Supabase|draft lokal sementara|siap dikirim ke Supabase/i.test(note.textContent || "")) {
        note.textContent = "Tombol Simpan menyimpan hasil pengujian ke Supabase project Crembo Media. Tombol Reset Data digunakan untuk mengosongkan seluruh isian.";
      }
    });
  }

  function addHasilLink() {
    var nav = document.querySelector(".nav-pills");
    if (!nav || nav.querySelector('a[href="user-flow-hasil.html"]')) return;
    var link = document.createElement("a");
    link.href = "user-flow-hasil.html";
    link.textContent = "Hasil Pengujian";
    nav.appendChild(link);
  }

  function cleanupOversizedUserFlowStorage(flowSlug) {
    var keys = [
      LOCAL_SUBMISSION_PREFIX + "-" + flowSlug,
      "uf-last-submission-" + flowSlug,
      "uf-last-submission",
      "uf-last-submission-meta-" + flowSlug
    ];
    keys.forEach(function (key) {
      try { localStorage.removeItem(key); } catch (error) {}
    });
  }

  function safeSaveSubmissionSnapshot(payload, savedRecord) {
    var flowSlug = payload.flow_slug || (document.body && document.body.getAttribute("data-flow")) || "role";
    var snapshot = {
      submission_id: payload.submission_id || (savedRecord && savedRecord.id) || "",
      flow_slug: payload.flow_slug,
      role_name: payload.role_name,
      tester_full_name: payload.identity && payload.identity.tester_name,
      tester_org: payload.identity && payload.identity.tester_org,
      submitted_at: payload.submitted_at,
      sus_score: payload.summary && payload.summary.sus_score,
      sus_category: payload.summary && payload.summary.sus_category,
      sus_grade: payload.summary && payload.summary.sus_grade
    };

    try {
      cleanupOversizedUserFlowStorage(flowSlug);
      localStorage.setItem("uf-last-submission-meta-" + flowSlug, JSON.stringify(snapshot));
    } catch (error) {
      // Penyimpanan utama sudah berhasil di Supabase. LocalStorage hanya cache kecil,
      // jadi error quota browser tidak boleh dianggap gagal submit.
      console.warn("Cache localStorage dilewati:", error && error.message ? error.message : error);
    }
  }

  function installSaveHandler() {
    var oldButton = byId("saveBtn");
    if (!oldButton || oldButton.getAttribute("data-supabase-bound") === "1") return;

    var newButton = oldButton.cloneNode(true);
    newButton.setAttribute("data-supabase-bound", "1");
    newButton.classList.add("primary");
    oldButton.parentNode.replaceChild(newButton, oldButton);

    newButton.addEventListener("click", async function () {
      if (!validateRequired()) return;
      var flowSlug = document.body.getAttribute("data-flow") || "role";
      var payload = buildPayload(flowSlug);
      newButton.disabled = true;
      newButton.textContent = "Menyimpan...";
      renderResult("Menyimpan ke Supabase...", "info");
      try {
        var response = await submitPayload(payload);
        var saved = Array.isArray(response) && response[0] ? response[0] : null;
        if (saved && saved.id) payload.submission_id = saved.id;
        safeSaveSubmissionSnapshot(payload, saved);
        var scoreText = payload.summary.sus_score == null ? "-" : Number(payload.summary.sus_score).toFixed(2);
        renderResult("Data berhasil disimpan ke Supabase.", "success", "<span>Skor SUS: " + esc(scoreText) + " - " + esc(payload.summary.sus_category || "-") + "</span>");
        alert("Data berhasil disimpan ke Supabase.");
      } catch (error) {
        renderResult("Gagal menyimpan ke Supabase.", "error", "<span>" + esc(error.message) + "</span>");
        alert("Gagal menyimpan ke Supabase: " + error.message + "\n\nPastikan file supabase_user_flow_setup.sql sudah dijalankan di SQL Editor Supabase.");
      } finally {
        newButton.disabled = false;
        newButton.textContent = "Simpan";
      }
    });
  }

  function installResetCleanup() {
    var resetBtn = byId("resetBtn");
    if (!resetBtn || resetBtn.getAttribute("data-supabase-reset-bound") === "1") return;
    resetBtn.setAttribute("data-supabase-reset-bound", "1");
    resetBtn.addEventListener("click", function () {
      var flowSlug = document.body.getAttribute("data-flow") || "role";
      setTimeout(function () {
        cleanupOversizedUserFlowStorage(flowSlug);
      }, 250);
    });
  }

  function init() {
    if (!document.body || !document.body.getAttribute("data-flow")) return;
    if (!byId("saveBtn")) return;
    cleanupOversizedUserFlowStorage(document.body.getAttribute("data-flow") || "role");
    addHasilLink();
    updateFooterNote();
    installSaveHandler();
    installResetCleanup();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
