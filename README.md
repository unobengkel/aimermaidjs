# Mermaid AI Workspace 🚀

Aplikasi Mermaid.js AI Editor yang powerful dengan dukungan RAG (Retrieval-Augmented Generation) untuk membuat, menyimpan, dan mengelola diagram secara cerdas menggunakan model AI DeepSeek dan embedding lokal HuggingFace.

## ✨ Fitur Utama
- **AI-Powered Editor**: Generate diagram Mermaid.js hanya dengan mengetik perintah natural language via DeepSeek Chat.
- **RAG Support**: Unggah dokumen PDF/TXT Anda sendiri agar AI memiliki konteks khusus dari data Anda saat membuat diagram.
- **Diagram Management**: Simpan, edit kembali, cari, dan hapus diagram Anda dengan mudah.
- **Preview & Export**: Preview diagram secara interaktif dengan fitur pan/zoom yang tajam dan unduh hasil dalam format PNG kualitas tinggi.
- **Local Embedding**: Menggunakan model HuggingFace (`all-MiniLM-L6-v2`) untuk pemrosesan vektor dokumen secara lokal dan gratis.

## 🛠️ Persyaratan Sistem
- Python 3.13+
- Koneksi Internet (hanya untuk API DeepSeek dan unduhan model pertama kali)
- Web Browser Modern (Chrome/Edge direkomendasikan)

## 🚀 Cara Instalasi & Setup

1. **Clone/Download Project** ke komputer Anda.
2. **Buka Terminal/CMD** di direktori project.
3. **Install Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Jalankan Aplikasi**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. **Akses Aplikasi** di browser: `http://localhost:8000`

## 📖 Dokumentasi Lengkap
Dokumentasi interaktif tersedia langsung di dalam aplikasi pada menu **Dokumentasi**.

## ⚖️ Lisensi
Project ini dibuat untuk membantu mempercepat pembuatan workflow diagram menggunakan kekuatan AI.
