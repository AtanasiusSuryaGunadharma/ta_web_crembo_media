
    const roleChip = document.getElementById("roleChip");
    const liveDateTime = document.getElementById("liveDateTime");
    const aboutForm = document.getElementById("aboutForm");
    const aboutDescription = document.getElementById("aboutDescription");
    const aboutButtonText = document.getElementById("aboutButtonText");
    const aboutButtonLink = document.getElementById("aboutButtonLink");
    const aboutAutoSeconds = document.getElementById("aboutAutoSeconds");
    const statusMessage = document.getElementById("statusMessage");
    const aboutImagesInput = document.getElementById("aboutImagesInput");
    const addVideoBtn = document.getElementById("addVideoBtn");
    const saveMediaBtn = document.getElementById("saveMediaBtn");
    const mediaStatus = document.getElementById("mediaStatus");
    const imageRows = document.getElementById("imageRows");
    const emptyState = document.getElementById("emptyState");

    let draggingImageId = "";
    let mediaItems = [];

    function getCurrentRole() {
      const params = new URLSearchParams(window.location.search);
      const roleFromQuery = params.get("role");
      let roleFromStorage = "";
      const storedSessionRaw = localStorage.getItem("crembo-login-session");
      if (storedSessionRaw) {
        try {
          const sessionObj = JSON.parse(storedSessionRaw);
          roleFromStorage = sessionObj && sessionObj.role ? String(sessionObj.role) : "";
        } catch (error) {
          roleFromStorage = "";
        }
      }
      return roleFromQuery || roleFromStorage || "admin";
    }

    function formatRole(role) {
      if (role === "super_admin") return "Super Admin";
      if (role === "admin") return "Admin";
      return "Anggota";
    }

    function escapeHtml(text) {
      return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function setStatus(text, kind) {
      statusMessage.textContent = text;
      statusMessage.className = "status show " + (kind || "ok");
    }

    function clearStatus() {
      statusMessage.className = "status";
      statusMessage.textContent = "";
    }
    
    function setMediaStatus(text, kind) {
      mediaStatus.style.display = "inline-block";
      mediaStatus.textContent = text;
      mediaStatus.className = "status show " + (kind || "ok");
      setTimeout(() => { mediaStatus.style.display = "none"; }, 3000);
    }

    async function loadConfig() {
        try {
            const res = await fetch("/api/tentang/config");
            const data = await res.json();
            if (data.description) aboutDescription.value = data.description;
            if (data.buttonText) aboutButtonText.value = data.buttonText;
            if (data.buttonLink) aboutButtonLink.value = data.buttonLink;
            if (data.autoSeconds) aboutAutoSeconds.value = data.autoSeconds;
        } catch (err) {
            console.error("Gagal memuat config:", err);
        }
    }

    async function loadMedia() {
        try {
            const res = await fetch("/api/tentang/media");
            mediaItems = await res.json();
            renderRows();
        } catch (err) {
            console.error("Gagal memuat media:", err);
        }
    }

    async function saveConfig(event) {
      event.preventDefault();
      const payload = {
        description: aboutDescription.value.trim(),
        buttonText: aboutButtonText.value.trim(),
        buttonLink: aboutButtonLink.value.trim(),
        autoSeconds: parseInt(aboutAutoSeconds.value) || 5
      };

      try {
          const res = await fetch("/api/tentang/config", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload)
          });
          if (res.ok) {
              setStatus("Pengaturan section Tentang Crembo berhasil disimpan.", "ok");
          } else {
              setStatus("Gagal menyimpan pengaturan.", "warn");
          }
      } catch (err) {
          setStatus("Kesalahan jaringan.", "danger");
      }
    }

    async function saveMediaSync() {
      try {
          saveMediaBtn.textContent = "Menyimpan...";
          const res = await fetch("/api/tentang/media/sync", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(mediaItems)
          });
          if (res.ok) {
              setMediaStatus("Urutan & status media berhasil disimpan.", "ok");
          } else {
              setMediaStatus("Gagal menyimpan media.", "warn");
          }
      } catch (err) {
          setMediaStatus("Kesalahan jaringan.", "danger");
      } finally {
          saveMediaBtn.textContent = "Simpan Perubahan Media";
      }
    }

    function sortImages(images) {
      return images.slice().sort((a, b) => a.order - b.order);
    }

    function renderRows() {
      mediaItems = sortImages(mediaItems);
      imageRows.innerHTML = "";

      if (!mediaItems.length) {
        emptyState.hidden = false;
        emptyState.textContent = "Belum ada media. Upload gambar atau tambah video untuk menampilkan slideshow di home.";
        return;
      }
      emptyState.hidden = true;

      mediaItems.forEach(function (item) {
        const tr = document.createElement("tr");
        tr.setAttribute("draggable", "true");
        tr.setAttribute("data-image-id", item.id);

        let previewUrl = item.url;
        let isVideo = item.type === "video";
        if (isVideo) {
            // Extract YT ID
            const match = item.url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^\/&\?]{11})/);
            if (match && match[1]) {
                previewUrl = 'https://img.youtube.com/vi/' + match[1] + '/hqdefault.jpg';
            }
        }

        const previewStyle = previewUrl
          ? ' style="background-image:url(\'' + escapeHtml(previewUrl) + '\')"'
          : "";
          
        const label = isVideo ? `<span style="background:red; color:white; padding: 2px 4px; font-size:10px; border-radius:4px; position:absolute; bottom:5px; right:5px; z-index:10;">VIDEO</span>` : "";

        tr.innerHTML =
          '<td data-label="Urut"><span class="drag-handle" title="Drag untuk ubah urutan">::</span></td>' +
          '<td data-label="Preview"><div class="preview-box"' + previewStyle + ' style="position:relative;">' + (previewUrl ? label : "Tanpa Thumbnail") + '</div></td>' +
          '<td data-label="Status"><span class="state-pill' + (item.active ? ' active' : '') + '">' + (item.active ? 'Aktif' : 'Nonaktif') + '</span></td>' +
          '<td data-label="Urutan">' + escapeHtml(String(item.order)) + '</td>' +
          '<td data-label="Aksi"><div class="action-stack">' +
            '<button class="btn ghost" type="button" data-toggle-id="' + escapeHtml(item.id) + '">' + (item.active ? 'Nonaktifkan' : 'Aktifkan') + '</button>' +
            '<button class="btn warn" type="button" data-delete-id="' + escapeHtml(item.id) + '">Hapus</button>' +
          '</div></td>';

        tr.addEventListener("dragstart", function () {
          draggingImageId = item.id;
          tr.classList.add("dragging");
        });
        tr.addEventListener("dragend", function () {
          draggingImageId = "";
          tr.classList.remove("dragging");
          imageRows.querySelectorAll("tr").forEach(row => row.classList.remove("drop-target"));
        });
        tr.addEventListener("dragover", function (event) {
          event.preventDefault();
          if (!draggingImageId || draggingImageId === item.id) return;
          tr.classList.add("drop-target");
        });
        tr.addEventListener("dragleave", function () {
          tr.classList.remove("drop-target");
        });
        tr.addEventListener("drop", function (event) {
          event.preventDefault();
          tr.classList.remove("drop-target");
          if (!draggingImageId || draggingImageId === item.id) return;
          reorderImages(draggingImageId, item.id);
        });

        imageRows.appendChild(tr);
      });
    }

    function reorderImages(sourceId, targetId) {
      const sourceIndex = mediaItems.findIndex(i => i.id === sourceId);
      const targetIndex = mediaItems.findIndex(i => i.id === targetId);

      if (sourceIndex < 0 || targetIndex < 0) return;

      const moved = mediaItems.splice(sourceIndex, 1)[0];
      mediaItems.splice(targetIndex, 0, moved);

      mediaItems.forEach((item, index) => {
        item.order = index + 1;
      });

      renderRows();
      setMediaStatus("Urutan diubah (belum disimpan).", "warn");
    }

    function toggleImage(id) {
      const target = mediaItems.find(i => i.id === id);
      if (!target) return;
      target.active = !target.active;
      renderRows();
      setMediaStatus("Status diubah (belum disimpan).", "warn");
    }

    function deleteImage(id) {
      const ok = window.confirm("Hapus media ini? (Perubahan akan langsung hilang dari tabel)");
      if (!ok) return;

      mediaItems = mediaItems.filter(i => i.id !== id);
      mediaItems.forEach((item, index) => { item.order = index + 1; });
      renderRows();
      setMediaStatus("Media dihapus (belum disimpan).", "warn");
    }

    async function handleUpload() {
      const files = Array.from(aboutImagesInput.files || []);
      if (!files.length) return;

      const invalid = files.find(f => !f.type.startsWith("image/"));
      if (invalid) {
        setMediaStatus("Semua file yang diupload harus berupa gambar.", "warn");
        aboutImagesInput.value = "";
        return;
      }

      let orderStart = mediaItems.length;
      
      for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const formData = new FormData();
          formData.append("file", file);
          try {
              const res = await fetch("/api/upload_image", { method: "POST", body: formData });
              const json = await res.json();
              if (json.success) {
                  orderStart += 1;
                  mediaItems.push({
                      id: "about-img-" + Date.now() + "-" + i,
                      type: "image",
                      url: json.url,
                      order: orderStart,
                      active: true
                  });
              }
          } catch(err) {
              console.error("Upload error:", err);
          }
      }
      
      renderRows();
      aboutImagesInput.value = "";
      setMediaStatus("Gambar diupload (belum disimpan).", "warn");
    }

    addVideoBtn.addEventListener("click", function() {
        const url = window.prompt("Masukkan Link Video YouTube (contoh: https://youtu.be/...):");
        if (!url || !url.trim()) return;
        
        let match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^\/&\?]{11})/);
        if(!match) {
            alert("URL YouTube tidak valid. Harap masukkan link yang benar.");
            return;
        }
        
        mediaItems.push({
            id: "vid-" + Date.now(),
            type: "video",
            url: url.trim(),
            order: mediaItems.length + 1,
            active: true
        });
        
        renderRows();
        setMediaStatus("Video ditambahkan (belum disimpan).", "warn");
    });

    imageRows.addEventListener("click", function (event) {
      const target = event.target;
      if (!(target instanceof HTMLButtonElement)) return;
      const toggleId = target.getAttribute("data-toggle-id");
      if (toggleId) return toggleImage(toggleId);
      const deleteId = target.getAttribute("data-delete-id");
      if (deleteId) deleteImage(deleteId);
    });

    aboutForm.addEventListener("submit", saveConfig);
    aboutImagesInput.addEventListener("change", function () {
      handleUpload();
    });
    saveMediaBtn.addEventListener("click", saveMediaSync);

    function updateLiveDateTime() {
      const now = new Date();
      const dayNames = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
      const monthNames = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
      const day = dayNames[now.getDay()];
      const date = String(now.getDate()).padStart(2, "0");
      const month = monthNames[now.getMonth()];
      const year = now.getFullYear();
      const hour = String(now.getHours()).padStart(2, "0");
      const minute = String(now.getMinutes()).padStart(2, "0");
      const second = String(now.getSeconds()).padStart(2, "0");
      liveDateTime.textContent = day + ", " + date + " " + month + " " + year + " " + hour + ":" + minute + ":" + second;
    }

    updateLiveDateTime();
    setInterval(updateLiveDateTime, 1000);
    roleChip.textContent = "Role: " + formatRole(getCurrentRole());
    
    // Initial fetch
    loadConfig();
    loadMedia();
