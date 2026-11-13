# Landing Page Analytics Refresh Design

## Intent
Menyempurnakan landing page NEXANTARA menjadi halaman analitik yang profesional, mudah dipahami, dan tetap memakai alur analisis aktual yang sudah ada di `Hero.tsx`.

## Goals
- Memperjelas hierarki visual, spacing, responsivitas, dan state loading/error/empty.
- Menampilkan distribusi sentimen aktual sebagai grafik CSS/SVG ringan tanpa dependency baru.
- Menampilkan perbandingan model hanya dari `branchScores` atau data model aktual; jika tidak tersedia, tampilkan state transparan, bukan angka buatan.
- Menampilkan `followers` sebagai followers pada informasi akun bila data akun tersedia.

## Non-goals
- Tidak membuat dashboard route baru.
- Tidak mengubah API, database, autentikasi, pipeline model, atau struktur internal field.
- Tidak menambahkan data dummy atau mengklaim proxy model sebagai model terlatih.

## Approach
Pilihan yang digunakan adalah revisi komponen landing page yang ada, terutama `Hero.tsx`, `HeroNetworkPreview.tsx`, `Navbar.tsx`, `AboutUs.tsx`, `HowItWorks.tsx`, serta token global. Visualisasi dibuat dengan elemen HTML/SVG dan data dari respons analisis yang sudah dinormalisasi sehingga tidak menambah dependency chart. Alternatif membuat dashboard baru ditolak karena memperluas arsitektur dan tidak sesuai kebutuhan landing page; alternatif mengganti seluruh halaman ditolak karena berisiko merusak alur analisis yang sudah berjalan.

## Visual direction
Palet dasar biru tinta, slate, putih, dan aksen status hijau/amber/merah; kartu memakai border halus dan radius moderat tanpa glow atau gradient dekoratif. Hero menjadi ruang kerja analisis: input query dan preview hasil berada dalam satu komposisi yang tenang. Grafik sentimen memakai bar horizontal/segmented summary dengan tooltip native dan label angka/persentase. Area model memakai grouped comparison hanya ketika `branchScores` tersedia dan kompatibel; selain itu menyampaikan keterbatasan data.

## Data integrity
- Sentimen bersumber dari `AnalysisResult.sentiment` atau fallback tweet yang sudah ada di `Hero.tsx`.
- Perbandingan model bersumber dari respons model/`branchScores`; tidak ada nilai statis produksi.
- Followers bersumber dari `BuzzerAccount.followers`; tidak menggunakan `outDegree`, `inDegree`, atau `totalDegree`.
- Backend dan database tidak diubah.

## Acceptance
Landing page tetap dapat menerima query dan menampilkan hasil lama, visual hasil lebih terstruktur pada desktop/mobile, grafik aman untuk data kosong/null, dan lint/typecheck/build berhasil.
