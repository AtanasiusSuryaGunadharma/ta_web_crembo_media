(function () {
  var runtimeDefs = [];
  var LOCAL_SUBMISSION_KEY = "uf-last-submission";
  var LOCAL_DRAFT_KEY_PREFIX = "uf-draft";
  var SUPABASE_URL = "https://ahietuoflhphnrhausvp.supabase.co";
  var SUPABASE_PUBLISHABLE_KEY = "sb_publishable_O6MsXlM4QrsNjZGsK9uLaw_JGl8aTAT";

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function getElementValue(id) {
    var element = byId(id);
    return String((element && element.value) || "").trim();
  }

  function normalizeText(value) {
    return String(value || "").trim().toLowerCase();
  }

  function containsAny(haystack, terms) {
    return terms.some(function (term) {
      return haystack.indexOf(term) !== -1;
    });
  }

  function getFlowRoleLabel(flowSlug) {
    if (flowSlug === "super-admin") {
      return "Super Admin";
    }
    if (flowSlug === "admin") {
      return "Admin";
    }
    if (flowSlug === "anggota") {
      return "Anggota";
    }
    return "Role";
  }

  function getRoleScenarioPack(flowSlug) {
    if (flowSlug === "super-admin") {
      return {
        login_name: "Nico Gandawijaya",
        login_user: "crembomedia",
        login_password: "SAdmin#2026",
        login_email: "nico.gandawijaya@crembo.id",
        otp_code: "482915",
        profile_name: "Nico Gandawijaya",
        member_name: "Christoforus Tadeus",
        admin_name: "Riean Aditya",
        streaming_title: "Misa Paskah 2026",
        streaming_petugas: "Rico Gunawan",
        publication_title: "Info Jadwal Pelayanan Minggu Palma",
        publication_category: "Pengumuman Internal",
        agenda_title: "Briefing Petugas Pekan Suci",
        agenda_date: "2026-04-30",
        agenda_place: "Ruang Kontrol Streaming",
        registration_title: "Pendaftaran Kegiatan Umum",
        registration_target: "Anggota",
        registration_visibility: "Publik",
        damaged_item: "Kamera Sony A6400",
        damaged_code: "CAM-001",
        loan_item: "Tripod Heavy Duty",
        loan_note: "Keperluan pelayanan"
      };
    }

    if (flowSlug === "admin") {
      return {
        login_name: "Riean Aditya",
        login_user: "mmtc123",
        login_password: "Admin#2026",
        login_email: "riean.aditya@crembo.id",
        otp_code: "315870",
        profile_name: "Riean Aditya",
        member_name: "Aurel",
        admin_name: "Riean Aditya",
        streaming_title: "Misa Minggu Palma",
        streaming_petugas: "Yusuf Hidayat",
        publication_title: "Pengumuman Jadwal Latihan Koor",
        publication_category: "Pengumuman Internal",
        agenda_title: "Latihan Petugas Streaming",
        agenda_date: "2026-05-02",
        agenda_place: "Ruang Multimedia",
        registration_title: "Form Kegiatan OMK",
        registration_target: "Anggota",
        registration_visibility: "Publik",
        damaged_item: "Mikrofon Wireless",
        damaged_code: "MIC-014",
        loan_item: "Kabel HDMI",
        loan_note: "Pakai untuk layar proyektor"
      };
    }

    if (flowSlug === "anggota") {
      return {
        login_name: "Katherine Ivana Hadi",
        login_user: "crembicrembi",
        login_password: "Anggota#2026",
        login_email: "katherine.ivana@crembo.id",
        otp_code: "904216",
        profile_name: "Katherine Ivana Hadi",
        member_name: "Katherine Ivana Hadi",
        admin_name: "Riean Aditya",
        streaming_title: "Misa Jumat Agung",
        streaming_petugas: "Katherine Ivana Hadi",
        technical_issue: "Kamera 1 mati",
        publication_title: "Info Kegiatan Mudika",
        publication_category: "Pengumuman Internal",
        agenda_title: "Briefing Tim Penerima Tamu",
        agenda_date: "2026-04-28",
        agenda_place: "Aula Paroki",
        registration_title: "Pendaftaran Retret OMK",
        registration_target: "Anggota",
        registration_visibility: "Publik",
        damaged_item: "Kursi Plastik Putih",
        damaged_code: "KRS-008",
        loan_item: "Speaker Portable",
        loan_note: "Untuk latihan koor"
      };
    }

    return {
      login_name: "Penguji",
      login_user: "user.dummy",
      login_password: "Dummy#2026",
      login_email: "penguji@crembo.id",
      otp_code: "000000",
      profile_name: "Penguji",
      member_name: "Penguji",
      admin_name: "Penguji",
      streaming_title: "Jadwal Dummy",
      streaming_petugas: "Petugas Dummy",
      publication_title: "Konten Dummy",
      publication_category: "Pengumuman Internal",
      agenda_title: "Agenda Dummy",
      agenda_date: "2026-01-01",
      agenda_place: "Lokasi Dummy",
      registration_title: "Form Dummy",
      registration_target: "Anggota",
      registration_visibility: "Publik",
      damaged_item: "Barang Dummy",
      damaged_code: "DUM-001",
      loan_item: "Barang Dummy",
      loan_note: "Kebutuhan dummy"
    };
  }

  function buildContextQuestion(flowSlug, item) {
    var haystack = normalizeText([item.step_title, item.flow_title, item.action_instruction].join(" "));
    var roleLabel = getFlowRoleLabel(flowSlug);
    var pack = getRoleScenarioPack(flowSlug);

    if (haystack.indexOf("evaluasi") !== -1) {
      if (flowSlug === "anggota") {
        return "Apakah pilihan kendala teknis seperti kamera 1 mati, audio pecah, dan catatan tambahan pada evaluasi anggota sudah mudah dipilih?";
      }

      return "Apakah daftar kendala teknis dan hasil evaluasi pada role " + roleLabel + " sudah jelas untuk dibaca dan divalidasi?";
    }

    if (haystack.indexOf("pengumuman") !== -1 || haystack.indexOf("berita") !== -1) {
      return "Apakah judul, kategori, update, hapus, dan download laporan pada task scenario ini sudah berjalan sesuai urutan?";
    }

    if (haystack.indexOf("agenda") !== -1) {
      return "Apakah input judul, tanggal, lokasi, lalu aksi update/hapus pada task scenario agenda sudah jelas?";
    }

    if (haystack.indexOf("form pendaftaran") !== -1 || haystack.indexOf("pendaftaran") !== -1) {
      return "Apakah input field form, status publish, dan proses simpan pada task scenario ini sudah mudah diikuti?";
    }

    if (haystack.indexOf("dashboard") !== -1 || haystack.indexOf("header") !== -1 || haystack.indexOf("headline") !== -1) {
      return "Apakah warna, kontras teks, dan posisi elemen header pada langkah ini sudah nyaman dilihat?";
    }

    if (haystack.indexOf("form") !== -1) {
      return "Apakah susunan field, label, dan tombol pada form ini sudah jelas?";
    }

    if (haystack.indexOf("kerusakan") !== -1) {
      return "Apakah input nama barang, pencarian dummy, dan opsi manual pada task scenario kerusakan sudah mudah dipahami?";
    }

    if (haystack.indexOf("peminjaman") !== -1 || haystack.indexOf("pengembalian") !== -1 || haystack.indexOf("pengambilan") !== -1) {
      return "Apakah urutan aksi dan status persetujuan pada alur ini sudah sesuai?";
    }

    if (haystack.indexOf("berita") !== -1 || haystack.indexOf("pengumuman") !== -1 || haystack.indexOf("agenda") !== -1) {
      return "Apakah tampilan daftar dan tombol aksi pada halaman ini sudah rapi?";
    }

    if (haystack.indexOf("login") !== -1 || haystack.indexOf("otp") !== -1 || haystack.indexOf("reset") !== -1) {
      return "Apakah alur autentikasi untuk akun " + pack.login_name + " dan pesan bantuannya sudah jelas?";
    }

    if (haystack.indexOf("profil") !== -1) {
      return "Apakah komposisi judul, isi, dan tombol pada halaman ini sudah seimbang?";
    }

    return "Apakah tampilan langkah ini sudah sesuai dengan high fidelity mock up yang diharapkan?";
  }

  function buildTaskScenarioBrief(flowSlug, item) {
    var haystack = normalizeText([item.step_title, item.flow_title, item.action_instruction].join(" "));
    var roleLabel = getFlowRoleLabel(flowSlug);
    var pack = getRoleScenarioPack(flowSlug);

    if (containsAny(haystack, ["dashboard anggota", "dashboard admin", "dashboard super admin"])) {
      return "Task scenario " + roleLabel + ": cek layout dashboard, sidebar, header, dan notifikasi. Pastikan nama akun " + pack.profile_name + " tampil sesuai role.";
    }

    if (containsAny(haystack, ["home", "entry", "beranda publik"])) {
      return "Task scenario " + roleLabel + ": mulai dari home, klik login, lalu masuk menggunakan akun dummy yang sudah disiapkan untuk role ini.";
    }

    if (containsAny(haystack, ["log aktivitas", "log "])) {
      return "Task scenario " + roleLabel + ": gunakan search, filter, export atau preview PDF jika tersedia, lalu pastikan hasil hanya sesuai cakupan role ini.";
    }

    if (containsAny(haystack, ["pengumuman", "berita"])) {
      return "Task scenario " + roleLabel + ": isi judul dummy '" + pack.publication_title + "', kategori '" + pack.publication_category + "', lalu uji update, hapus, dan download laporan jika tersedia.";
    }

    if (haystack.indexOf("agenda") !== -1) {
      return "Task scenario " + roleLabel + ": isi judul '" + pack.agenda_title + "', tanggal '" + pack.agenda_date + "', lokasi '" + pack.agenda_place + "', lalu simpan dan cek opsi update/hapus.";
    }

    if (containsAny(haystack, ["form pendaftaran", "builder form", "manajemen form", "pendaftar", "isi form kegiatan", "pendaftaran retret", "pendaftaran"] )) {
      return "Task scenario " + roleLabel + ": gunakan dummy judul form '" + pack.registration_title + "', target '" + pack.registration_target + "', visibility '" + pack.registration_visibility + "', lalu uji simpan, edit, hapus, dan preview hasil.";
    }

    if (haystack.indexOf("kerusakan") !== -1) {
      return "Task scenario " + roleLabel + ": pilih nama barang dummy '" + pack.damaged_item + "' atau ketik manual jika tidak ada, isi kode '" + pack.damaged_code + "', lalu kirim dan cek riwayat.";
    }

    if (haystack.indexOf("evaluasi") !== -1) {
      if (flowSlug === "anggota") {
        return "Task scenario " + roleLabel + ": isi evaluasi dengan kendala teknis '" + pack.technical_issue + "', lalu tambahkan catatan audio dan pencahayaan sebelum simpan.";
      }

      return "Task scenario " + roleLabel + ": validasi hasil evaluasi dengan contoh kendala 'Kamera 1 mati', 'Audio pecah', dan 'Internet tersendat'.";
    }

    if (haystack.indexOf("peminjaman") !== -1 || haystack.indexOf("pengembalian") !== -1 || haystack.indexOf("pengambilan") !== -1) {
      return "Task scenario " + roleLabel + ": gunakan barang dummy '" + pack.loan_item + "' dengan keterangan '" + pack.loan_note + "', lalu uji alur approve, ambil, kembalikan, dan buka riwayat.";
    }

    if (containsAny(haystack, ["login", "otp", "reset", "masuk sistem"])) {
      return "Task scenario " + roleLabel + ": gunakan akun dummy nama '" + pack.login_name + "' dengan username '" + pack.login_user + "', password '" + pack.login_password + "', lalu cek recovery jika diminta.";
    }

    if (containsAny(haystack, ["manajemen anggota", "kelola data admin", "sertifikat", "profil admin", "profil anggota", "profil publik", "profil organisasi", "kelola tentang", "manajemen profil"])) {
      return "Task scenario " + roleLabel + ": gunakan data dummy nama '" + pack.member_name + "' dan akun pengelola '" + pack.profile_name + "' untuk uji tambah/edit/validasi data sesuai modul.";
    }

    if (containsAny(haystack, ["jadwal streaming", "jadwal tugas", "request tugas", "pembatalan", "tukar jadwal", "monitoring", "penugasan petugas", "registrasi misa", "riwayat tugas"])) {
      return "Task scenario " + roleLabel + ": gunakan jadwal '" + pack.streaming_title + "' dan petugas '" + pack.streaming_petugas + "' untuk uji alur streaming end-to-end.";
    }

    if (containsAny(haystack, ["inventaris", "persetujuan peminjaman", "riwayat pinjam", "riwayat peminjaman", "pengajuan peminjaman"])) {
      return "Task scenario " + roleLabel + ": gunakan barang '" + pack.loan_item + "' dan catatan '" + pack.loan_note + "' untuk uji alur inventaris dan approval.";
    }

    if (containsAny(haystack, ["carousel", "embed", "youtube", "instagram", "google maps", "search", "pencarian", "notifikasi"])) {
      return "Task scenario " + roleLabel + ": gunakan konten dummy milik akun '" + pack.profile_name + "' lalu verifikasi tampilan publik dan hasil pencarian/notifikasi.";
    }

    if (containsAny(haystack, ["logout", "kembali ke home", "kembali ke dashboard"])) {
      return "Task scenario " + roleLabel + ": akhiri sesi akun '" + pack.login_user + "' lalu pastikan halaman tujuan terbuka tanpa error.";
    }

    return "Task scenario " + roleLabel + ": gunakan akun '" + pack.login_user + "' (" + pack.login_name + "), jalankan aksi pada node, lalu validasi hasil tampil sesuai modul.";
  }

  function buildTaskScenarioDetails(flowSlug, item) {
    var haystack = normalizeText([item.step_title, item.flow_title, item.action_instruction].join(" "));
    var roleLabel = getFlowRoleLabel(flowSlug);
    var pack = getRoleScenarioPack(flowSlug);
    var brief = buildTaskScenarioBrief(flowSlug, item);
    var dummyData = "Akun: " + pack.login_name + " | Username: " + pack.login_user + " | Password: " + pack.login_password + ".";
    var action = "Jalankan aksi sesuai node, simpan perubahan, lalu lanjut ke langkah berikutnya.";
    var expected = "Hasil tampil spesifik sesuai modul dan role " + roleLabel + ".";

    if (containsAny(haystack, ["dashboard anggota", "dashboard admin", "dashboard super admin"])) {
      dummyData = "Akun aktif: " + pack.profile_name + ". Fokus pada halaman dashboard, sidebar, header, dan notifikasi yang muncul.";
      action = "Buka dashboard, cek semua menu, lalu pastikan setiap ikon/tombol bisa diklik.";
      expected = "Dashboard memuat lengkap, nama akun tampil benar, dan setiap elemen navigasi stabil.";
    } else if (containsAny(haystack, ["home", "entry", "beranda publik"])) {
      dummyData = "Gunakan home sebagai titik awal lalu lanjut login dengan akun " + pack.login_name + ".";
      action = "Klik tombol Login di home lalu masuk ke halaman login sesuai role.";
      expected = "Alur masuk menuju halaman login berjalan normal.";
    } else if (containsAny(haystack, ["login", "otp", "reset", "masuk sistem"])) {
      dummyData = "Nama: " + pack.login_name + " | Username: " + pack.login_user + " | Password: " + pack.login_password + " | Email recovery: " + pack.login_email + " | OTP dummy: " + pack.otp_code + ".";
      action = "Masukkan kredensial dummy, cek recovery bila ada, lalu masuk ke dashboard role terkait.";
      expected = "Autentikasi berhasil dan redirect sesuai role yang diuji.";
    } else if (containsAny(haystack, ["pengumuman", "berita"])) {
      dummyData = "Judul: '" + pack.publication_title + "' | Kategori: '" + pack.publication_category + "' | Penulis: '" + pack.profile_name + "' | Status: Draft/Published sesuai skenario.";
      action = "Tambahkan data dummy, lalu uji update, hapus, dan download laporan jika ada tombolnya.";
      expected = "Daftar konten berubah sesuai aksi dan detail laporan bisa dibuka.";
    } else if (haystack.indexOf("agenda") !== -1) {
      dummyData = "Judul: '" + pack.agenda_title + "' | Tanggal: '" + pack.agenda_date + "' | Lokasi: '" + pack.agenda_place + "' | PIC: '" + pack.profile_name + "'.";
      action = "Isi data dummy agenda, lalu uji simpan, update, hapus, dan buka detailnya.";
      expected = "Agenda tersimpan dan detail tampil konsisten.";
    } else if (haystack.indexOf("form pendaftaran") !== -1 || haystack.indexOf("pendaftaran") !== -1) {
      dummyData = "Judul form: '" + pack.registration_title + "' | Target: '" + pack.registration_target + "' | Visibility: '" + pack.registration_visibility + "'.";
      action = "Buat atau ubah form dengan data dummy, lalu preview hasil dan pastikan data masuk.";
      expected = "Form bisa dipublish, diedit, dihapus, dan data pendaftar terbaca.";
    } else if (haystack.indexOf("kerusakan") !== -1) {
      dummyData = "Nama barang: '" + pack.damaged_item + "' atau ketik manual bila tidak ada | Kode: '" + pack.damaged_code + "' | Tingkat: 'Sedang' | Lokasi: 'Ruang Kontrol Streaming'.";
      action = "Isi form kerusakan dengan data dummy, kirim, lalu cek riwayat atau hasil laporan.";
      expected = "Laporan kerusakan tersimpan dan muncul di daftar/riwayat terkait.";
    } else if (haystack.indexOf("peminjaman") !== -1 || haystack.indexOf("pengembalian") !== -1 || haystack.indexOf("pengambilan") !== -1) {
      dummyData = "Barang dummy: '" + pack.loan_item + "' atau barang yang muncul pada daftar approved | Keterangan: '" + pack.loan_note + "'.";
      action = "Ajukan, ambil, atau kembalikan barang sesuai node, lalu cek status/riwayatnya.";
      expected = "Status peminjaman berubah sesuai aksi dan riwayat tetap sinkron.";
    } else if (haystack.indexOf("evaluasi") !== -1) {
      dummyData = flowSlug === "anggota"
        ? "Kendala teknis: '" + pack.technical_issue + "' | Catatan tambahan: audio jelas, lighting kurang terang."
        : "Isi evaluasi dengan kendala teknis spesifik, misalnya kamera 1 mati, audio pecah, atau internet tersendat.";
      action = "Pilih kendala yang tersedia, isi catatan teknis, lalu simpan evaluasi.";
      expected = "Evaluasi tersimpan dengan kendala teknis yang sesuai scenario.";
    } else if (haystack.indexOf("log aktivitas") !== -1 || haystack.indexOf("log") !== -1) {
      dummyData = "Gunakan filter tanggal, role, search kata kunci, serta export/preview bila tersedia.";
      action = "Uji pencarian, filter, export, dan preview laporan pada log aktivitas.";
      expected = "Hasil log hanya sesuai cakupan role dan fitur output berfungsi.";
    } else if (containsAny(haystack, ["profil", "manajemen profil", "kelola tentang", "profil publik"])) {
      dummyData = "Nama profil: '" + pack.profile_name + "' | Tentang: 'Koordinator tim multimedia Crembo' | Kontak: '" + pack.login_email + "'.";
      action = "Buka halaman profil/tentang, ubah satu data, simpan, lalu cek sinkronisasi di halaman terkait.";
      expected = "Data profil dan narasi tentang tampil konsisten setelah disimpan.";
    } else if (containsAny(haystack, ["manajemen anggota", "kelola data admin", "sertifikat anggota", "setting sertifikat"])) {
      dummyData = "Nama anggota: '" + pack.member_name + "' | Nama admin: '" + pack.admin_name + "' | Status anggota: Aktif | Nomor sertifikat: SRT-2026-014.";
      action = "Uji tambah/edit/validasi data anggota atau admin, lalu uji generate/pengaturan sertifikat.";
      expected = "Perubahan data user tersimpan dan pengaturan sertifikat bisa dipakai.";
    } else if (containsAny(haystack, ["jadwal streaming", "jadwal tugas", "request tugas", "pembatalan", "tukar jadwal", "penugasan petugas", "registrasi misa", "riwayat tugas", "monitoring tugas", "monitoring kewajiban"])) {
      dummyData = "Judul jadwal: '" + pack.streaming_title + "' | Petugas: '" + pack.streaming_petugas + "' | Tanggal: 2026-05-05 | Shift: 17:00-19:00.";
      action = "Uji alur pilih jadwal, request/assign, ubah status, lalu validasi monitoring dan riwayat.";
      expected = "Status tugas berpindah sesuai alur dan histori tersimpan benar.";
    } else if (containsAny(haystack, ["inventaris", "persetujuan peminjaman", "riwayat pinjam", "riwayat peminjaman"])) {
      dummyData = "Barang inventaris: '" + pack.loan_item + "' | Kode: INV-2026-031 | Kondisi awal: Baik | Keterangan: '" + pack.loan_note + "'.";
      action = "Cek inventaris, proses approval, lalu validasi riwayat pinjam-kembali.";
      expected = "Stok, status approval, dan riwayat transaksi konsisten.";
    } else if (containsAny(haystack, ["carousel", "embed", "youtube", "instagram", "google maps"])) {
      dummyData = "Judul carousel: 'Pelayanan Misa Paskah 2026' | Link YouTube: https://youtube.com/watch?v=crembo2026 | Link Instagram: https://instagram.com/crembo.media | Maps: Gereja St. Paulus.";
      action = "Uji tambah/edit konten home lalu buka home untuk cek semua embed tampil.";
      expected = "Konten home berubah sesuai input dan komponen embed tampil normal.";
    } else if (containsAny(haystack, ["search", "pencarian"])) {
      dummyData = "Kata kunci: 'misa', 'pengumuman', dan 'retret omk'.";
      action = "Lakukan pencarian minimal 3 kata kunci lalu cek relevansi hasil.";
      expected = "Hasil pencarian menampilkan konten terkait dan bisa dibuka detailnya.";
    } else if (containsAny(haystack, ["notifikasi", "header"])) {
      dummyData = "User: '" + pack.login_name + "' | Notifikasi uji: 'Jadwal tugas diperbarui' dan 'Form pendaftaran diterima'.";
      action = "Buka header notifikasi, uji filter/search notifikasi, lalu cek status terbaca.";
      expected = "Notifikasi tampil, bisa difilter, dan status terbaca berubah.";
    } else if (containsAny(haystack, ["logout", "kembali ke home", "kembali ke dashboard"])) {
      dummyData = "Sesi aktif akun: '" + pack.login_user + "'.";
      action = "Klik kembali ke halaman tujuan dan lakukan logout dari sesi aktif.";
      expected = "Sesi berakhir tanpa error dan halaman login/home terbuka.";
    }

    return {
      brief: brief,
      dummy_data: dummyData,
      action: action,
      expected: expected
    };
  }

  function collectNodeDefinitions(flowSlug) {
    var questionnaire = byId("ufQuestionnaire");
    if (!questionnaire) {
      return [];
    }

    var lanes = Array.prototype.slice.call(document.querySelectorAll(".lane"));
    var defs = [];
    var stepNo = 1;

    lanes.forEach(function (lane) {
      if (lane === questionnaire || lane.classList.contains("checklist-lane")) {
        return;
      }

      var laneTitleEl = lane.querySelector(".lane-head h2");
      var laneTitle = laneTitleEl ? String(laneTitleEl.textContent || "").trim() : "";
      var nodes = lane.querySelectorAll(".flow .node");
      var prevNodeTitle = "";

      nodes.forEach(function (node) {
        var nodeTitleEl = node.querySelector("strong");
        var nodeDescEl = node.querySelector("p");
        var nodeTitle = nodeTitleEl ? String(nodeTitleEl.textContent || "").trim() : "Langkah " + stepNo;
        var nodeDesc = nodeDescEl ? String(nodeDescEl.textContent || "").trim() : "Silakan uji langkah ini sesuai skenario flow.";
        var links = Array.prototype.slice.call(node.querySelectorAll("a")).map(function (a) {
          return String(a.textContent || "").trim();
        }).filter(Boolean);

        var openText = links.length
          ? "Klik dan buka halaman berikut secara berurutan: " + links.join(" lalu ") + "."
          : "Buka halaman pada node ini dari tautan yang tersedia.";

        var prevText = prevNodeTitle
          ? "Setelah menyelesaikan langkah \"" + prevNodeTitle + "\", lanjutkan ke langkah ini."
          : "Mulai dari langkah ini sebagai awal alur pengujian.";

        var actionInstruction = [
          prevText,
          openText,
          "Fokuskan pengujian pada: " + nodeDesc,
          "Setelah selesai, simpan perubahan jika ada dan lanjutkan ke langkah berikutnya."
        ].join(" ");

        prevNodeTitle = nodeTitle;

        defs.push({
          step_no: stepNo,
          scenario_no: stepNo,
          scenario_title: "Task Scenario " + stepNo,
          step_title: nodeTitle,
          flow_title: laneTitle,
          action_instruction: actionInstruction,
          scenario_details: buildTaskScenarioDetails(flowSlug, {
            step_title: nodeTitle,
            flow_title: laneTitle,
            action_instruction: actionInstruction
          }),
          question_text: "Apakah " + nodeTitle + " pada " + laneTitle + " sudah sesuai dan mudah digunakan?",
          context_question_text: buildContextQuestion(flowSlug, {
            step_title: nodeTitle,
            flow_title: laneTitle,
            action_instruction: actionInstruction
          })
        });

        stepNo += 1;
      });
    });

    return defs;
  }


  function buildQuestionnaire(defs) {
    defs.forEach(function (item) {
      var candidates = document.querySelectorAll(".lane .flow .node");
      var node = candidates[item.step_no - 1];
      if (!node || node.querySelector(".uf-node-question")) {
        return;
      }

      var card = document.createElement("div");
      card.className = "uf-node-question";
      card.setAttribute("data-step-no", String(item.step_no));
      card.innerHTML = [
        '<div class="uf-node-question-head">',
          '<span class="uf-node-question-step">' + escapeHtml(item.scenario_title || ("Task Scenario " + item.step_no)) + '</span>',
          '<span class="uf-node-question-flow">' + escapeHtml(item.flow_title) + '</span>',
        '</div>',
        '<p class="uf-node-question-scenario">' + escapeHtml((item.scenario_details && item.scenario_details.brief) || "Task scenario belum ditentukan.") + '</p>',
        '<div class="uf-scenario-grid">',
          '<div class="uf-scenario-box">',
            '<p class="uf-scenario-label">Data Dummy</p>',
            '<p class="uf-scenario-value">' + escapeHtml((item.scenario_details && item.scenario_details.dummy_data) || "Gunakan data dummy sesuai skenario.") + '</p>',
          '</div>',
          '<div class="uf-scenario-box">',
            '<p class="uf-scenario-label">Aksi yang Diuji</p>',
            '<p class="uf-scenario-value">' + escapeHtml((item.scenario_details && item.scenario_details.action) || "Ikuti aksi pada node.") + '</p>',
          '</div>',
          '<div class="uf-scenario-box">',
            '<p class="uf-scenario-label">Hasil Diharapkan</p>',
            '<p class="uf-scenario-value">' + escapeHtml((item.scenario_details && item.scenario_details.expected) || "Hasil mengikuti alur yang dirancang.") + '</p>',
          '</div>',
        '</div>',
        '<p class="uf-node-question-action">' + escapeHtml(item.action_instruction) + '</p>',
        '<div class="uf-question-block">',
          '<p class="uf-question-label">Pertanyaan 1</p>',
          '<p class="uf-node-question-text">' + escapeHtml("Apakah " + (item.scenario_title || ("Task Scenario " + item.step_no)) + " sudah mengikuti input dummy dan aksi yang ditentukan?") + '</p>',
          '<div class="uf-answer-row">',
            '<label><input type="radio" name="answer-main-' + item.step_no + '" value="YA"> YA</label>',
            '<label><input type="radio" name="answer-main-' + item.step_no + '" value="TIDAK"> TIDAK</label>',
          '</div>',
        '</div>',
        '<div class="uf-question-block">',
          '<p class="uf-question-label">Pertanyaan 2</p>',
          '<p class="uf-node-question-context">' + escapeHtml(item.context_question_text) + '</p>',
          '<div class="uf-answer-row secondary">',
            '<label><input type="radio" name="answer-context-' + item.step_no + '" value="YA"> YA</label>',
            '<label><input type="radio" name="answer-context-' + item.step_no + '" value="TIDAK"> TIDAK</label>',
          '</div>',
        '</div>',
        '<label class="uf-label">Saran</label>',
        '<textarea id="note-' + item.step_no + '" rows="2" placeholder="Saran untuk kotak ini..."></textarea>'
      ].join("");

      node.appendChild(card);
    });
  }

  function selectedValue(groupName, stepNo) {
    var checked = document.querySelector('input[name="' + groupName + '-' + stepNo + '"]:checked');
    return checked ? checked.value : "";
  }

  function buildDraftStorageKey(flowSlug) {
    var slug = String(flowSlug || "").trim() || "unknown";
    return LOCAL_DRAFT_KEY_PREFIX + "-" + slug;
  }

  function getCurrentFlowSlug() {
    var root = byId("ufQuestionnaire");
    return root ? String(root.getAttribute("data-flow-slug") || "").trim() : "";
  }

  function collectDraftPayload(flowSlug, defs) {
    var steps = {};

    (defs || []).forEach(function (def) {
      var key = String(def.step_no || "");
      if (!key) {
        return;
      }

      steps[key] = {
        main_answer: selectedValue("answer-main", def.step_no),
        context_answer: selectedValue("answer-context", def.step_no),
        note_text: String((byId("note-" + def.step_no) || {}).value || "")
      };
    });

    return {
      flow_slug: flowSlug,
      saved_at: new Date().toISOString(),
      tester: {
        full_name: getElementValue("testerFullName"),
        org: getElementValue("testerOrg"),
        email: getElementValue("testerEmail"),
        phone: getElementValue("testerPhone"),
        device: getElementValue("testerDevice"),
        browser: getElementValue("testerBrowser")
      },
      steps: steps
    };
  }

  function saveDraft(flowSlug, defs) {
    try {
      var key = buildDraftStorageKey(flowSlug);
      var payload = collectDraftPayload(flowSlug, defs);
      localStorage.setItem(key, JSON.stringify(payload));
    } catch (error) {
      // Ignore draft save failures (e.g. storage quota/private mode)
    }
  }

  function restoreDraft(flowSlug, defs) {
    try {
      var key = buildDraftStorageKey(flowSlug);
      var raw = localStorage.getItem(key);
      if (!raw) {
        return;
      }

      var draft = JSON.parse(raw);
      if (!draft || !draft.steps) {
        return;
      }

      if (draft.tester) {
        var tester = draft.tester;
        if (byId("testerFullName")) { byId("testerFullName").value = tester.full_name || ""; }
        if (byId("testerOrg")) { byId("testerOrg").value = tester.org || ""; }
        if (byId("testerEmail")) { byId("testerEmail").value = tester.email || ""; }
        if (byId("testerPhone")) { byId("testerPhone").value = tester.phone || ""; }
        if (byId("testerDevice") && tester.device) { byId("testerDevice").value = tester.device; }
        if (byId("testerBrowser") && tester.browser) { byId("testerBrowser").value = tester.browser; }
      }

      (defs || []).forEach(function (def) {
        var stepKey = String(def.step_no || "");
        var row = draft.steps[stepKey] || null;
        if (!row) {
          return;
        }

        if (row.main_answer) {
          var mainRadio = document.querySelector('input[name="answer-main-' + def.step_no + '"][value="' + row.main_answer + '"]');
          if (mainRadio) {
            mainRadio.checked = true;
          }
        }

        if (row.context_answer) {
          var contextRadio = document.querySelector('input[name="answer-context-' + def.step_no + '"][value="' + row.context_answer + '"]');
          if (contextRadio) {
            contextRadio.checked = true;
          }
        }

        var noteEl = byId("note-" + def.step_no);
        if (noteEl) {
          noteEl.value = row.note_text || "";
        }
      });
    } catch (error) {
      // Ignore invalid draft data.
    }
  }

  function clearDraft(flowSlug) {
    try {
      localStorage.removeItem(buildDraftStorageKey(flowSlug));
    } catch (error) {
      // Ignore draft clear failures.
    }
  }

  function bindDraftAutoSave(flowSlug, defs) {
    var form = byId("ufForm");
    if (!form) {
      return;
    }

    var throttled = null;
    var scheduleSave = function () {
      if (throttled) {
        clearTimeout(throttled);
      }
      throttled = setTimeout(function () {
        saveDraft(flowSlug, defs);
      }, 120);
    };

    form.addEventListener("input", scheduleSave);
    form.addEventListener("change", scheduleSave);
  }

  function renderMessage(type, text) {
    var el = byId("ufSubmitInfo");
    if (!el) {
      return;
    }

    el.className = "uf-submit-info " + type;
    el.textContent = text;
  }

  function detectDevice() {
    var ua = String(navigator.userAgent || "").toLowerCase();
    if (/android|iphone|ipad|ipod|mobile/.test(ua)) {
      return "Handphone";
    }
    return "PC/Laptop";
  }

  function detectBrowser() {
    var ua = String(navigator.userAgent || "");
    if (/Edg\//.test(ua)) {
      return "Microsoft Edge";
    }
    if (/OPR\//.test(ua)) {
      return "Opera";
    }
    if (/Brave\//.test(ua)) {
      return "Brave";
    }
    if (/Chrome\//.test(ua) && !/Edg\//.test(ua) && !/OPR\//.test(ua)) {
      return "Google Chrome";
    }
    if (/Firefox\//.test(ua)) {
      return "Mozilla Firefox";
    }
    if (/Safari\//.test(ua) && !/Chrome\//.test(ua) && !/Edg\//.test(ua)) {
      return "Safari";
    }
    return "Lainnya";
  }

  function applyIdentityDefaults() {
    var deviceEl = byId("testerDevice");
    var browserEl = byId("testerBrowser");

    if (deviceEl && !deviceEl.value) {
      deviceEl.value = detectDevice();
    }

    if (browserEl && !browserEl.value) {
      browserEl.value = detectBrowser();
    }
  }

  function buildSupabaseHeaders() {
    return {
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Authorization: "Bearer " + SUPABASE_PUBLISHABLE_KEY,
      "Content-Type": "application/json"
    };
  }

  async function supabaseRequest(method, path, body, extraHeaders) {
    var options = {
      method: method,
      headers: Object.assign(buildSupabaseHeaders(), extraHeaders || {})
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    var response = await fetch(SUPABASE_URL + path, options);
    var raw = await response.text();
    var data = raw ? JSON.parse(raw) : null;

    if (!response.ok) {
      throw new Error((data && (data.message || data.error_description || data.error)) || "Request Supabase gagal");
    }

    return data;
  }

  function sortByStepNo(a, b) {
    return Number(a.step_no || 0) - Number(b.step_no || 0);
  }

  function pickQuestionOrderIndex(questionText, fallbackIndex) {
    var text = normalizeText(questionText);

    if (text.indexOf("pertanyaan 1") !== -1 || text.indexOf("sudah mengikuti") !== -1) {
      return 0;
    }

    if (text.indexOf("pertanyaan 2") !== -1 || text.indexOf("konteks") !== -1) {
      return 1;
    }

    return fallbackIndex;
  }

  async function fetchFlowIdBySlug(flowSlug) {
    var rows = await supabaseRequest(
      "GET",
      "/rest/v1/uf_flows?select=id,slug&slug=eq." + encodeURIComponent(flowSlug) + "&limit=1"
    );

    if (!rows || !rows.length || !rows[0].id) {
      throw new Error("Flow tidak ditemukan di Supabase: " + flowSlug);
    }

    return rows[0].id;
  }

  async function fetchFlowSteps(flowId) {
    var rows = await supabaseRequest(
      "GET",
      "/rest/v1/uf_steps?select=id,flow_id,step_no,step_title&flow_id=eq." + encodeURIComponent(flowId) + "&order=step_no.asc"
    );

    return (rows || []).sort(sortByStepNo);
  }

  async function fetchQuestionsForStepIds(stepIds) {
    if (!stepIds.length) {
      return [];
    }

    var inValues = stepIds.map(function (id) {
      return '"' + String(id).replace(/"/g, "") + '"';
    }).join(",");

    return await supabaseRequest(
      "GET",
      "/rest/v1/uf_questions?select=id,step_id,question_text&step_id=in.(" + inValues + ")"
    );
  }

  function buildQuestionLookup(rows) {
    var map = {};

    (rows || []).forEach(function (row) {
      var key = String(row.step_id || "");
      if (!key) {
        return;
      }

      if (!map[key]) {
        map[key] = [];
      }

      map[key].push(row);
    });

    Object.keys(map).forEach(function (stepId) {
      map[stepId].sort(function (a, b) {
        var ta = normalizeText(a.question_text);
        var tb = normalizeText(b.question_text);
        return ta.localeCompare(tb);
      });
    });

    return map;
  }

  function findDefByStepNo(defs, stepNo) {
    var found = null;
    (defs || []).some(function (def) {
      if (Number(def.step_no || 0) === Number(stepNo || 0)) {
        found = def;
        return true;
      }
      return false;
    });
    return found;
  }

  function buildDefaultQuestionTexts(def) {
    return [
      "Apakah " + (def.scenario_title || ("Task Scenario " + def.step_no)) + " sudah mengikuti input dummy dan aksi yang ditentukan?",
      def.context_question_text || "Apakah tampilan langkah ini sudah sesuai dengan high fidelity mock up yang diharapkan?"
    ];
  }

  async function bootstrapStepsAndQuestions(flowId, defs) {
    if (!defs || !defs.length) {
      return;
    }

    var stepPayload = defs.map(function (def) {
      return {
        flow_id: flowId,
        step_no: Number(def.step_no || 0),
        step_title: def.step_title || ("Langkah " + def.step_no),
        action_instruction: def.action_instruction || ""
      };
    }).filter(function (item) {
      return item.step_no > 0;
    });

    if (!stepPayload.length) {
      return;
    }

    await supabaseRequest(
      "POST",
      "/rest/v1/uf_steps",
      stepPayload,
      { Prefer: "return=representation" }
    );

    var remoteSteps = await fetchFlowSteps(flowId);
    var questionPayload = [];

    remoteSteps.forEach(function (step) {
      var def = findDefByStepNo(defs, step.step_no);
      if (!def) {
        return;
      }

      var questionTexts = buildDefaultQuestionTexts(def);
      questionTexts.forEach(function (text) {
        questionPayload.push({
          step_id: step.id,
          question_text: text
        });
      });
    });

    if (questionPayload.length) {
      await supabaseRequest(
        "POST",
        "/rest/v1/uf_questions",
        questionPayload,
        { Prefer: "return=minimal" }
      );
    }
  }

  async function ensureQuestionsForExistingSteps(remoteSteps, defs, questionLookup) {
    var missingPayload = [];

    remoteSteps.forEach(function (step) {
      var def = findDefByStepNo(defs, step.step_no);
      if (!def) {
        return;
      }

      var existing = questionLookup[String(step.id)] || [];
      var existingTextMap = {};
      existing.forEach(function (q) {
        existingTextMap[normalizeText(q.question_text)] = true;
      });

      buildDefaultQuestionTexts(def).forEach(function (qText) {
        if (!existingTextMap[normalizeText(qText)]) {
          missingPayload.push({
            step_id: step.id,
            question_text: qText
          });
        }
      });
    });

    if (missingPayload.length) {
      await supabaseRequest(
        "POST",
        "/rest/v1/uf_questions",
        missingPayload,
        { Prefer: "return=minimal" }
      );
    }
  }

  async function submitToSupabase(flowSlug, tester, defs, answerRows) {
    var flowId = await fetchFlowIdBySlug(flowSlug);
    var remoteSteps = await fetchFlowSteps(flowId);

    if (!remoteSteps.length) {
      await bootstrapStepsAndQuestions(flowId, defs);
      remoteSteps = await fetchFlowSteps(flowId);
    }

    if (!remoteSteps.length) {
      throw new Error("Step flow belum tersedia di Supabase untuk role ini.");
    }

    var stepMapByNo = {};
    remoteSteps.forEach(function (step) {
      stepMapByNo[String(step.step_no)] = step;
    });

    var stepIds = remoteSteps.map(function (step) { return step.id; });
    var questionLookup = buildQuestionLookup(await fetchQuestionsForStepIds(stepIds));

    await ensureQuestionsForExistingSteps(remoteSteps, defs, questionLookup);
    questionLookup = buildQuestionLookup(await fetchQuestionsForStepIds(stepIds));

    var rpcAnswers = [];
    var rpcStepNotes = [];

    defs.forEach(function (def, index) {
      var answer = answerRows[index];
      var remoteStep = stepMapByNo[String(def.step_no)] || remoteSteps[index] || null;

      if (!remoteStep || !answer) {
        return;
      }

      var questionRows = questionLookup[String(remoteStep.id)] || [];

      if (questionRows.length) {
        var firstIdx = pickQuestionOrderIndex("Pertanyaan 1", 0);
        var secondIdx = pickQuestionOrderIndex("Pertanyaan 2", 1);
        var q1 = questionRows[firstIdx] || questionRows[0] || null;
        var q2 = questionRows[secondIdx] || questionRows[1] || questionRows[0] || null;

        if (q1 && answer.main_answer) {
          rpcAnswers.push({
            step_id: remoteStep.id,
            question_id: q1.id,
            answer_value: answer.main_answer,
            note_text: ""
          });
        }

        if (q2 && answer.context_answer) {
          rpcAnswers.push({
            step_id: remoteStep.id,
            question_id: q2.id,
            answer_value: answer.context_answer,
            note_text: ""
          });
        }
      }

      rpcStepNotes.push({
        step_id: remoteStep.id,
        opinion_text: answer.note_text || ""
      });
    });

    var payload = {
      flow_slug: flowSlug,
      tester: {
        full_name: tester.full_name,
        org: tester.org,
        email: tester.email,
        phone: tester.phone,
        device: tester.device,
        browser: tester.browser
      },
      answers: rpcAnswers,
      step_notes: rpcStepNotes
    };

    return await supabaseRequest("POST", "/rest/v1/rpc/uf_submit_full", {
      payload: payload
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();

    var root = byId("ufQuestionnaire");
    var flowSlug = root ? root.getAttribute("data-flow-slug") : "";
    var defs = runtimeDefs.length ? runtimeDefs : collectNodeDefinitions(flowSlug);

    var fullName = getElementValue("testerFullName");
    var testerDevice = getElementValue("testerDevice");
    var testerBrowser = getElementValue("testerBrowser");

    if (!fullName) {
      renderMessage("error", "Nama lengkap penguji wajib diisi.");
      return;
    }

    if (!testerDevice) {
      renderMessage("error", "Pilih device yang digunakan penguji.");
      return;
    }

    if (!testerBrowser) {
      renderMessage("error", "Pilih browser yang digunakan penguji.");
      return;
    }

    var submitButton = byId("ufSubmitBtn");
    submitButton.disabled = true;
    renderMessage("loading", "Sedang menyimpan hasil pengujian ke Supabase...");

    try {
      var answers = [];
      var missingAnswers = [];

      defs.forEach(function (def) {
        var mainAnswer = selectedValue("answer-main", def.step_no);
        var contextAnswer = selectedValue("answer-context", def.step_no);
        var noteText = String((byId("note-" + def.step_no) || {}).value || "").trim();

        if (!mainAnswer || !contextAnswer) {
          missingAnswers.push((def.scenario_title || ("Task Scenario " + def.step_no)) + " - " + def.step_title);
        }

        answers.push({
          step_no: def.step_no,
          step_title: def.step_title,
          flow_title: def.flow_title,
          main_answer: mainAnswer,
          context_answer: contextAnswer,
          note_text: noteText
        });
      });

      if (missingAnswers.length) {
        renderMessage("error", "Masih ada jawaban kosong: " + missingAnswers.join("; "));
        submitButton.disabled = false;
        return;
      }

      var testerPayload = {
        full_name: fullName,
        org: getElementValue("testerOrg"),
        instansi_unit: getElementValue("testerOrg"),
        email: getElementValue("testerEmail"),
        phone: getElementValue("testerPhone"),
        no_hp: getElementValue("testerPhone"),
        device: testerDevice,
        browser: testerBrowser,
        user_agent: String(navigator.userAgent || "")
      };

      var submission = {
        id: "local-" + Date.now(),
        submitted_at: new Date().toISOString(),
        flow_slug: flowSlug,
        tester: testerPayload,
        answers: answers
      };

      var remoteSubmissionId = await submitToSupabase(flowSlug, testerPayload, defs, answers);
      if (remoteSubmissionId) {
        submission.id = String(remoteSubmissionId);
      }

      localStorage.setItem(LOCAL_SUBMISSION_KEY, JSON.stringify(submission));
      localStorage.setItem(LOCAL_SUBMISSION_KEY + "-" + flowSlug, JSON.stringify(submission));
      clearDraft(flowSlug);
      window.__UF_LAST_SUBMISSION__ = submission;
      renderMessage("success", "Hasil task scenario berhasil tersimpan ke Supabase dan lokal backup.");
      byId("ufForm").reset();
      applyIdentityDefaults();
    } catch (error) {
      renderMessage("error", "Submit gagal: " + error.message);
    } finally {
      submitButton.disabled = false;
    }
  }

  function injectStyles() {
    if (document.getElementById("ufRuntimeStyles")) {
      return;
    }

    var style = document.createElement("style");
    style.id = "ufRuntimeStyles";
    style.textContent = [
      ".uf-form { display:grid; gap:10px; padding:12px; }",
      ".uf-grid { display:grid; grid-template-columns:repeat(2,minmax(220px,1fr)); gap:8px; }",
      ".uf-grid input,.uf-grid select { width:100%; border:1px solid #b9c2d1; border-radius:8px; padding:8px; font:inherit; font-size:0.82rem; background:#fff; color:#0f172a; }",
      ".uf-question-block { border:1px solid #dbe3ef; border-radius:10px; background:#fff; padding:8px; display:grid; gap:6px; }",
      ".uf-question-label { margin:0; font-size:0.72rem; font-weight:800; color:#475569; text-transform:uppercase; letter-spacing:0.04em; }",
      ".uf-node-question { margin-top:10px; border:1px solid #cbd5e1; border-radius:12px; background:linear-gradient(180deg,#f8fbff 0%,#ffffff 100%); padding:10px; display:grid; gap:8px; }",
      ".uf-node-question-head { display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap; align-items:center; }",
      ".uf-node-question-step { display:inline-flex; align-items:center; border-radius:999px; padding:4px 8px; background:#dbeafe; color:#1e3a8a; font-size:0.72rem; font-weight:800; }",
      ".uf-node-question-flow { font-size:0.7rem; font-weight:800; color:#64748b; text-transform:uppercase; letter-spacing:0.04em; }",
      ".uf-node-question-scenario { margin:0; font-size:0.74rem; color:#7c2d12; line-height:1.45; padding:7px 8px; border-radius:8px; background:#fff7ed; border:1px solid #fed7aa; font-weight:700; }",
      ".uf-scenario-grid { display:grid; grid-template-columns:1fr; gap:8px; }",
      ".uf-scenario-box { min-width:0; border:1px solid #e2e8f0; border-radius:10px; background:#fff; padding:8px; display:grid; gap:4px; }",
      ".uf-scenario-label { margin:0; font-size:0.68rem; font-weight:800; color:#1e3a8a; text-transform:uppercase; letter-spacing:0.04em; white-space:normal; overflow-wrap:anywhere; word-break:break-word; }",
      ".uf-scenario-value { margin:0; font-size:0.75rem; color:#334155; line-height:1.45; white-space:normal; overflow-wrap:anywhere; word-break:break-word; }",
      ".uf-node-question-action,.uf-node-question-text,.uf-node-question-context { margin:0; font-size:0.78rem; color:#334155; line-height:1.45; }",
      ".uf-node-question-text { font-weight:700; color:#0f172a; }",
      ".uf-answer-row { display:flex; gap:14px; flex-wrap:wrap; font-size:0.78rem; color:#1f2937; }",
      ".uf-answer-row.secondary { border-top:1px dashed #dbe3ef; padding-top:6px; }",
      ".uf-label { font-size:0.75rem; font-weight:700; color:#374151; }",
      ".uf-node-question textarea { width:100%; border:1px solid #b9c2d1; border-radius:8px; padding:8px; font:inherit; font-size:0.8rem; resize:vertical; }",
      ".uf-submit-row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }",
      ".uf-btn { border:0; border-radius:8px; background:#1d4ed8; color:#fff; font-weight:700; padding:8px 12px; cursor:pointer; }",
      ".uf-btn.link { text-decoration:none; border:1px solid #94a3b8; background:#fff; color:#1f2937; }",
      ".uf-submit-info { font-size:0.78rem; padding:7px 9px; border-radius:8px; }",
      ".uf-submit-info.loading { background:#eff6ff; color:#1e3a8a; border:1px solid #bfdbfe; }",
      ".uf-submit-info.success { background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }",
      ".uf-submit-info.error { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }",
      "@media (min-width:680px){ .uf-scenario-grid{ grid-template-columns:repeat(2,minmax(0,1fr)); } }",
      "@media (min-width:980px){ .uf-scenario-grid{ grid-template-columns:repeat(3,minmax(0,1fr)); } }",
      "@media (max-width:900px){ .uf-grid{ grid-template-columns:1fr; } }"
    ].join("");
    document.head.appendChild(style);
  }

  function init() {
    var section = byId("ufQuestionnaire");
    if (!section) {
      return;
    }

    injectStyles();

    var flowSlug = section.getAttribute("data-flow-slug");
    applyIdentityDefaults();
    runtimeDefs = collectNodeDefinitions(flowSlug);
    buildQuestionnaire(runtimeDefs);
    restoreDraft(flowSlug, runtimeDefs);
    bindDraftAutoSave(flowSlug, runtimeDefs);
    byId("ufForm").addEventListener("submit", handleSubmit);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
