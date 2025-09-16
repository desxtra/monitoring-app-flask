# Panduan Setup Sistem Monitoring IoT Kelas

## Untuk Guru/Pengelola Server

1. Pastikan Python 3.7+ terinstall di komputer server
2. Copy folder `server` ke komputer yang akan menjadi server
3. Buka terminal, masuk ke folder server, dan jalankan:

```bash
    pip install -r requirements.txt
    python app.py
```

4. Server akan berjalan di http://0.0.0.0:5000
5. Catat alamat IP komputer server (gunakan `ipconfig` di Windows atau `ifconfig` di Linux/Mac)

## Untuk Setiap Kelompok

1. Dapatkan alamat IP server dari guru
2. Copy folder kelompok contoh (misal `group1_smartlight`) dan rename sesuai kelompok Anda
3. Edit file `config.py` di folder kelompok Anda:
- Ganti `GROUP_ID` dengan ID kelompok Anda (group1, group2, dst)
- Ganti `SERVER_IP` dengan alamat IP server
- Sesuaikan pin dan konfigurasi sensor sesuai hardware Anda
4. Upload kode `main.py` dan `config.py` ke ESP32 menggunakan Thonny IDE
5. Pastikan ESP32 terhubung ke WiFi yang sama dengan server

## Akses Dashboard

Buka browser dan kunjungi: http://[IP_SERVER]:5000
Contoh: http://192.168.1.100:5000