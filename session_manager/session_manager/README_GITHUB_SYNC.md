# 🔥 HARRY ON GitHub Sync System v1.0.0

## Apa Ini?

Sistem **GitHub Sync** memungkinkan semua project HARRY ON tersimpan **permanen** di GitHub. Kalau chat session berakhir dan file di `/mnt/agents/output/` dihapus, kamu bisa **restore semuanya** dari GitHub dalam hitungan detik.

---

## 🚀 Cara Pakai (3 Langkah Saja)

### LANGKAH 1: Setup (Sekali Saja)

**Opsi A: Wizard Interaktif**
```bash
python session_manager/github_setup.py
```

**Opsi B: Quick Setup (Kalau Sudah Punya Token)**
```python
from session_manager.github_setup import quick_setup
quick_setup("ghp_xxxxxxxxxxxxxxxxxxxx")
```

**Cara Dapat Token GitHub:**
1. Buka: https://github.com/settings/tokens
2. Klik: **"Generate new token (classic)"**
3. Note: `HARRY ON Sync`
4. Expiration: **"No expiration"**
5. Centang: **✅ repo** (Full control)
6. Klik: **"Generate token"**
7. **COPY token segera** (tidak bisa dilihat lagi!)

---

### LANGKAH 2: Save ke GitHub (Sebelum Chat Berakhir)

**Cara 1: One-Click**
```bash
python session_manager/one_click_sync.py save
```

**Cara 2: Python Script**
```python
from session_manager.auto_sync import sync_now
sync_now()
```

**Cara 3: HARRY ON Command**
```
HARRY ON sync
```

---

### LANGKAH 3: Restore dari GitHub (Chat Baru)

**Cara 1: One-Click**
```bash
python session_manager/one_click_sync.py restore
```

**Cara 2: Python Script**
```python
from session_manager.download_all import restore_now
restore_now()
```

**Cara 3: HARRY ON Command**
```
HARRY ON restore
```

---

## 📁 Struktur File

```
harry_on_v1_mva/
├── session_manager/
│   ├── github_setup.py       ← Setup wizard
│   ├── auto_sync.py          ← Upload ke GitHub
│   ├── download_all.py       ← Download dari GitHub
│   ├── one_click_sync.py     ← Wrapper simpel
│   ├── .github_config.json   ← Config (auto-generated)
│   └── .sync_index.json      ← Sync tracking
│
└── [semua project lain]      ← Auto-sync ke GitHub
```

---

## 🔄 Workflow Harian

### Session 1 (Hari Ini):
```
1. Kerja project...
2. python one_click_sync.py save
3. Chat berakhir ✅
```

### Session 2 (Besok, Chat Baru):
```
1. python one_click_sync.py restore
2. Semua file kembali! 🎉
3. Lanjutkan kerja...
4. python one_click_sync.py save
```

---

## 🛡️ Keamanan

| Aspek | Penjelasan |
|-------|-----------|
| **Token** | Disimpan di `.github_config.json` (local only) |
| **Repo** | Bisa private atau public |
| **Akses** | Hanya repo yang kamu tentukan |
| **Backup** | Semua versi tersimpan di Git history |

---

## ⚡ Perintah Cepat

| Perintah | Fungsi |
|----------|--------|
| `python one_click_sync.py setup` | Konfigurasi awal |
| `python one_click_sync.py save` | Upload semua ke GitHub |
| `python one_click_sync.py restore` | Download semua dari GitHub |
| `python one_click_sync.py status` | Cek status |

---

## 🎯 Contoh Lengkap

### Setup Pertama Kali:
```bash
# 1. Dapatkan token dari GitHub
# 2. Setup
python session_manager/github_setup.py
#    → Paste token
#    → Enter (gunakan default repo)
#    → Enter (gunakan default branch)
#    → Done!

# 3. Test
python one_click_sync.py status
```

### Save Project:
```bash
# Setelah selesai coding...
python one_click_sync.py save
# Output:
# 🔥 HARRY ON Auto-Sync: Syncing ALL projects
# ✅ Uploaded: session_manager/session_manager.py
# ✅ Uploaded: modules/storycraft/hook_engine.py
# ...
# ✅ SYNC COMPLETE
#    Total synced: 45 files
```

### Restore Project:
```bash
# Di chat baru...
python one_click_sync.py restore
# Output:
# 🔥 HARRY ON Project Restore v1.0.0
# 📥 Restoring from: github.com/harryansyah212-coder/harry-on-v1-mva
# ✅ Downloaded: session_manager/session_manager.py
# ✅ Downloaded: modules/storycraft/hook_engine.py
# ...
# ✅ RESTORE COMPLETE
#    Total files downloaded: 45
```

---

## 🔧 Troubleshooting

### ❌ "No token configured"
```bash
# Solusi: Run setup dulu
python session_manager/github_setup.py
```

### ❌ "Repository not found"
```bash
# Solusi: Buat repo dulu atau cek nama repo
# Repo default: harryansyah212-coder/harry-on-v1-mva
```

### ❌ "API rate limit exceeded"
```bash
# Solusi: Tunggu 1 jam atau upgrade GitHub account
# Free: 60 requests/jam (unauthenticated)
# Authenticated: 5000 requests/jam
```

### ❌ File tidak muncul setelah restore
```bash
# Solusi: Cek path
ls /mnt/agents/output/harry_on_v1_mva/
# Kalau masih kosong, coba clone manual:
git clone https://github.com/harryansyah212-coder/harry-on-v1-mva.git
```

---

## 📊 Limitasi GitHub API

| Plan | Rate Limit |
|------|-----------|
| GitHub Free (authenticated) | 5,000 requests/jam |
| GitHub Pro | 5,000 requests/jam |
| GitHub Enterprise | 15,000 requests/jam |

> **Tips**: Satu file = 1 request. 100 file = ~100 requests. Masih sangat cukup!

---

## 🎉 Keuntungan Menggunakan GitHub Sync

1. ✅ **Permanen** — File survive selamanya
2. ✅ **Version History** — Bisa lihat perubahan per commit
3. ✅ **Multi-Device** — Akses dari mana saja
4. ✅ **Collaboration** — Bisa share dengan tim
5. ✅ **Backup** — GitHub backup otomatis
6. ✅ **Free** — Gratis untuk public repo

---

## 📞 Support

Kalau ada masalah:
1. Cek status: `python one_click_sync.py status`
2. Cek token: Buka https://github.com/settings/tokens
3. Cek repo: Buka https://github.com/harryansyah212-coder/harry-on-v1-mva

---

**HARRY ON V1 MVA UNLIMITED v2.0.0**  
*GitHub Sync System v1.0.0*  
*Built for baginda* 🚀
