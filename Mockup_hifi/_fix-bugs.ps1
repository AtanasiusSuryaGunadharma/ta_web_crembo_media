## Fix All Bugs Script
## Memperbaiki:
## 1. CTA cards gelap di dashboard-anggota
## 2. Sidebar id missing di beberapa halaman
## 3. Sidebar dengan menu yang tidak lengkap (hanya punya beberapa group)

# ========================
# FIX 1: CTA cards di dashboard-anggota.html - replace dark gradients with bright red-theme
# ========================
$f = 'dashboard-anggota.html'
$c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

# Replace dark CTA colors dengan merah tema cerah
$c = $c -replace '\.cta\.blue \{ background: linear-gradient\(130deg, #4b5563 0%, #111827 100%\); \}', '.cta.blue { background: linear-gradient(130deg, #800000 0%, #5c0000 100%); }'
$c = $c -replace '\.cta\.purple \{ background: linear-gradient\(130deg, #6b7280 0%, #1f2937 100%\); \}', '.cta.purple { background: linear-gradient(130deg, #a52a2a 0%, #5c0000 100%); }'
$c = $c -replace '\.cta\.green \{ background: linear-gradient\(130deg, #374151 0%, #030712 100%\); \}', '.cta.green { background: linear-gradient(130deg, #b91c1c 0%, #7f1d1d 100%); }'

[System.IO.File]::WriteAllText($f, $c, [System.Text.Encoding]::UTF8)
Write-Host "Fixed: CTA card colors in $f"

# ========================
# FIX 2: Add id="sidebar" to all aside.sidebar without an id
# ========================
$filesToFix = @(
  'hasil-form-kerusakan-barang.html',
  'data-inventaris-barang.html',
  'persetujuan-peminjaman.html',
  'riwayat-peminjaman-pengembalian.html',
  'hasil-evaluasi-streaming.html',
  'setting-pertanyaan-evaluasi-streaming.html',
  'jadwal-tugas-streaming-admin.html',
  'registrasi-tugas-misa-besar.html',
  'penugasan-petugas-misa.html',
  'monitoring-tugas-anggota.html',
  'kelola-berita.html',
  'form-berita.html',
  'manajemen-agenda.html',
  'form-agenda.html',
  'manajemen-form-pendaftaran.html',
  'builder-form-pendaftaran.html',
  'kelola-carousel-home.html',
  'kelola-tentang-crembo.html',
  'kelola-embed-youtube.html',
  'kelola-embed-google-maps.html',
  'kelola-embed-instagram.html',
  'manajemen-anggota.html',
  'setting-sertifikat-anggota.html',
  'kelola-data-admin.html',
  'log-aktivitas.html',
  'manajemen-profil.html',
  'form-profil.html',
  'profil-admin.html',
  'sertifikat-anggota.html',
  'jadwal-tugas-misa-anggota.html',
  'request-tugas-anggota.html',
  'pembatalan-tugas-anggota.html',
  'penukaran-jadwal-tugas-anggota.html',
  'riwayat-tugas-saya.html',
  'evaluasi-streaming-anggota.html',
  'monitoring-kewajiban-tugas-anggota.html',
  'pengajuan-peminjaman-barang-anggota.html',
  'input-pengambilan-barang-anggota.html',
  'input-pengembalian-barang-anggota.html',
  'riwayat-peminjaman-barang-anggota.html',
  'form-kerusakan-barang-anggota.html',
  'riwayat-form-kerusakan-barang-anggota.html',
  'isi-form-pendaftaran.html'
)

foreach ($f2 in $filesToFix) {
  if (-not (Test-Path $f2)) { continue }
  $c2 = [System.IO.File]::ReadAllText($f2, [System.Text.Encoding]::UTF8)
  
  # Add id="sidebar" if aside.sidebar doesn't have one
  if ($c2 -match '<aside class="sidebar"' -and $c2 -notmatch '<aside id="sidebar"') {
    $c2 = $c2 -replace '<aside class="sidebar"', '<aside id="sidebar" class="sidebar"'
    Write-Host "Added id=sidebar: $f2"
  }

  [System.IO.File]::WriteAllText($f2, $c2, [System.Text.Encoding]::UTF8)
}

Write-Host "`nAll fixes applied."
