$files = @(
  'profil-admin.html',
  'hasil-form-kerusakan-barang.html',
  'jadwal-tugas-streaming-admin.html',
  'registrasi-tugas-misa-besar.html',
  'penugasan-petugas-misa.html',
  'monitoring-tugas-anggota.html',
  'hasil-evaluasi-streaming.html',
  'setting-pertanyaan-evaluasi-streaming.html',
  'data-inventaris-barang.html',
  'persetujuan-peminjaman.html',
  'riwayat-peminjaman-pengembalian.html',
  'manajemen-profil.html',
  'form-profil.html',
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
  'dashboard-anggota.html',
  'profil-anggota.html',
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

$linkTag = '<link rel="stylesheet" href="_admin-theme.css">'
$fontLink = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">'
$sidebarScript = '<script src="_sidebar-fix.js"></script>'

$processed = 0
$skipped = 0

foreach ($file in $files) {
  if (-not (Test-Path $file)) {
    Write-Host "SKIP: $file" -ForegroundColor Yellow
    $skipped++
    continue
  }
  
  $content = Get-Content $file -Raw -Encoding UTF8
  $changed = $false
  
  if ($content -notmatch 'fonts\.googleapis\.com') {
    $content = $content -replace '</head>', "$fontLink`n</head>"
    $changed = $true
  }
  
  if ($content -notmatch '_admin-theme\.css') {
    $content = $content -replace '</head>', "$linkTag`n</head>"
    $changed = $true
  }
  
  if ($content -notmatch '_sidebar-fix\.js') {
    $content = $content -replace '</body>', "$sidebarScript`n</body>"
    $changed = $true
  }
  
  if ($changed) {
    [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8)
    Write-Host "OK: $file" -ForegroundColor Green
    $processed++
  } else {
    Write-Host "SKIP(done): $file" -ForegroundColor Cyan
  }
}

Write-Host "`nDone. Processed: $processed, Skipped: $skipped"
