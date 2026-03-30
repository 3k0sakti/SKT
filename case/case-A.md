# Rancangan Blockchain Publikasi Skripsi
> Tugas Kelas A — Sistem Komputasi Terdistribusi — 4 Kelompok Bekerja Sama, 1 Jaringan Bersama

---

## 📋 Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Kolaborasi Antar Kelompok](#2-kolaborasi-antar-kelompok)
3. [Topologi Jaringan](#3-topologi-jaringan)
4. [Spesifikasi VM & Node](#4-spesifikasi-vm--node)
5. [Arsitektur Sistem](#5-arsitektur-sistem)
6. [Struktur Data Blok](#6-struktur-data-blok)
7. [Smart Contract](#7-smart-contract)
8. [Mekanisme Konsensus](#8-mekanisme-konsensus)
9. [Alur Kerja Sistem](#9-alur-kerja-sistem)
10. [Deteksi Plagiasi](#10-deteksi-plagiasi)
11. [API Endpoint](#11-api-endpoint)
12. [Skenario Pengujian](#12-skenario-pengujian)
13. [Analisis Keamanan](#13-analisis-keamanan)
14. [Sistem Penilaian](#14-sistem-penilaian)

---

## 1. Gambaran Umum

### Latar Belakang

Ini adalah **tugas kelas kolaboratif** pada mata kuliah Sistem Komputasi Terdistribusi. Kelas dibagi menjadi **4 kelompok** yang **bekerja sama** membangun satu jaringan blockchain bersama. Masing-masing kelompok mendapat **1 VM** sebagai node, sehingga tidak ada satu kelompok pun yang menjadi pusat kendali — semua setara sebagai validator dan operator.

Berbeda dengan tugas individual, di sini **keberhasilan sistem bergantung pada koordinasi semua kelompok**: genesis block harus dibuat bersama, konfigurasi jaringan harus konsisten di semua VM, dan smart contract di-deploy secara kolektif.

### Data Kelompok Kelas A

| Kelompok | Wilayah | Universitas | Repository Sumber Data | PIC (Penerima Akses VM) |
|----------|---------|-------------|------------------------|-------------------------|
| **Kelompok 1** | Jawa Barat | Telkom University (Tel-U) | https://repository.telkomuniversity.ac.id/ | **muhammad arif rifki** |
| **Kelompok 2** | Jawa Timur | Universitas Brawijaya (UB) | https://repository.ub.ac.id/ | **Steven Anthony** |
| **Kelompok 3** | Jawa Tengah | Universitas Gadjah Mada (UGM) | https://etd.repository.ugm.ac.id/ | **Izzah Faiq Putri Madani** |
| **Kelompok 4** | Sumatera | Universitas Sumatera Utara (USU) | https://repository.usu.ac.id/ | **Yoga Raditya Nala** |

> 📧 **Akses VM** akan dikirimkan langsung ke masing-masing PIC kelompok.
> 📚 **Sumber data** skripsi yang disimpan ke blockchain diambil dari repository resmi universitas masing-masing kelompok.

### Tujuan

| Tujuan | Deskripsi |
|--------|-----------|
| **Desentralisasi** | Tidak ada satu kelompok/node pun yang menjadi otoritas tunggal |
| **Immutability** | Data skripsi yang sudah terdaftar tidak dapat dimanipulasi |
| **Transparansi** | Semua kelompok anggota dapat memverifikasi keabsahan skripsi |
| **Deteksi Plagiasi** | Perbandingan hash dan fingerprint konten lintas node kelompok |
| **Praktik SKT** | Mengimplementasikan konsep P2P, konsensus, dan replikasi data secara langsung |

### Jenis Blockchain

```
Tipe     : Consortium Blockchain (Permissioned)
Platform : Ethereum Private (Geth Clique PoA)
Konsensus: Clique PoA — setiap kelompok adalah validator
```

---

## 2. Kolaborasi Antar Kelompok

### Prinsip Kerja Sama

> Semua kelompok membangun **satu jaringan blockchain yang sama**. Tidak ada kelompok yang "lebih tinggi" dari yang lain — setiap node setara.

### Pembagian Tanggung Jawab

| Kelompok | VM | Universitas | Tanggung Jawab Khusus | Tanggung Jawab Bersama |
|----------|----|-------------|-----------------------|------------------------|
| **K1** – Nadiyatun | VM-1 | Tel-U | Buat & distribusikan `genesis.json`, koordinasi setup awal | Jalankan node, submit skripsi dari repo Tel-U, ikut konsensus |
| **K2** – Steven | VM-2 | UB | Konfigurasi dan deploy Smart Contract ke jaringan | Jalankan node, submit skripsi dari repo UB, ikut konsensus |
| **K3** – Izzah | VM-3 | UGM | Bangun REST API & plagiarism engine (dapat dipakai semua) | Jalankan node, submit skripsi dari repo UGM, ikut konsensus |
| **K4** – Yoga | VM-4 | USU | Setup monitoring (Grafana/dashboard) & dokumentasi teknis | Jalankan node, submit skripsi dari repo USU, ikut konsensus |

> **Catatan:** Pembagian di atas adalah pembagian tanggung jawab utama. Semua kelompok tetap harus memahami dan mampu menjalankan seluruh komponen di VM masing-masing.

### Tahap Kerja Sama

```
Tahap 1 — Persiapan Bersama (Semua Kelompok)
  ├── Sepakati chainId, IP address, dan port setiap VM
  ├── K1 membuat genesis.json → dibagikan ke K2, K3, K4
  ├── Setiap kelompok generate keypair validator (geth account new)
  ├── K1 mengumpulkan semua address → masukkan ke extradata genesis
  └── Semua jalankan: geth init genesis.json

Tahap 2 — Jalankan Jaringan Bersama
  ├── K1 jalankan node pertama (sebagai bootnode awal)
  ├── K2, K3, K4 jalankan node masing-masing & connect ke K1
  ├── Verifikasi: net.peerCount == 3 di semua node
  └── Verifikasi: clique.getSigners() muncul 4 address

Tahap 3 — Deploy Kontrak (K2 memimpin, semua menyetujui)
  ├── K2 deploy ThesisRegistry.sol
  ├── Bagikan contract address ke semua kelompok
  └── Semua kelompok tambahkan address ke konfigurasi API

Tahap 4 — Operasional & Pengujian
  ├── Setiap kelompok crawl/ambil minimal 5 data skripsi dari repository universitas masing-masing
  ├── Submit data ke blockchain melalui node VM kelompok sendiri
  ├── Uji cek plagiasi lintas kelompok (cek skripsi K1 vs repo K2, K3, K4)
  ├── Simulasi: matikan 1 node, pastikan jaringan tetap jalan
  └── K4 presentasikan dashboard monitoring jaringan
```

### Komunikasi & Koordinasi

| Kebutuhan | Cara |
|-----------|------|
| Tukar enode address | Bagikan via grup/chat kelas setelah node pertama jalan |
| Sinkronisasi genesis.json | K1 (Nadiyatun) upload ke repo bersama (Git/shared drive) |
| Contract address | K2 (Steven) umumkan setelah deploy berhasil |
| Troubleshooting | Cek log geth: `geth --verbosity 3`, bandingkan antar kelompok |
| Sumber data scraping | Ambil dari repository masing-masing: Tel-U / UB / UGM / USU |
| Koordinasi umum | PIC tiap kelompok saling berkomunikasi |

---

## 3. Topologi Jaringan

```
┌─────────────────────────────────────────────────────────────────────┐
│                     JARINGAN BLOCKCHAIN SKRIPSI                     │
│          Kelas A — SKT — Private Consortium Network                 │
│                                                                     │
│   ┌──────────────┐              ┌──────────────┐                    │
│   │  VM-1        │◄────────────►│  VM-2        │                    │
│   │  K1 – Tel-U  │              │  K2 – UB     │                    │
│   │  Jawa Barat  │              │  Jawa Timur  │                    │
│   │ 10.34.100.173│              │ 10.34.100.174│                    │
│   │  [Validator] │              │  [Validator] │                    │
│   └──────┬───────┘              └──────┬───────┘                    │
│          │                             │                            │
│          │         ┌──────────┐        │                            │
│          └────────►│ P2P Net  │◄───────┘                            │
│                    │ Gossip   │                                     │
│          ┌────────►│ Protocol │◄───────┐                            │
│          │         └──────────┘        │                            │
│          │                             │                            │
│   ┌──────┴───────┐              ┌──────┴───────┐                    │
│   │  VM-3        │◄────────────►│  VM-4        │                    │
│   │  K3 – UGM    │              │  K4 – USU    │                    │
│   │  Jawa Tengah │              │  Sumatera    │                    │
│   │ 10.34.100.177│              │ 10.34.100.176│                    │
│   │  [Validator] │              │  [Validator] │                    │
│   └──────────────┘              └──────────────┘                    │
│                                                                     │
│   Koneksi: Full Mesh (setiap node terhubung ke semua node lain)     │
└─────────────────────────────────────────────────────────────────────┘
```

### Identitas Node

| Node ID | Kelompok | Universitas | Wilayah | Kode | IP Address | Port P2P | Port RPC | Port HTTP-API |
|---------|----------|-------------|---------|------|------------|----------|----------|---------------|
| VM-1 | K1 – Nadiyatun | Telkom University | Jawa Barat | K1 | 10.34.100.173 | 30303 | 8545 | 8080 |
| VM-2 | K2 – Steven | Univ. Brawijaya | Jawa Timur | K2 | 10.34.100.174 | 30303 | 8545 | 8080 |
| VM-3 | K3 – Izzah | Univ. Gadjah Mada | Jawa Tengah | K3 | 10.34.100.177 | 30303 | 8545 | 8080 |
| VM-4 | K4 – Yoga | Univ. Sumatera Utara | Sumatera | K4 | 10.34.100.176 | 30303 | 8545 | 8080 |

### Sumber Data per Node

| VM | Universitas | URL Repository | Jenis Data yang Di-crawl |
|----|-------------|---------------|---------------------------|
| VM-1 | Telkom University | https://repository.telkomuniversity.ac.id/ | Judul, abstrak, metadata skripsi/TA |
| VM-2 | Universitas Brawijaya | https://repository.ub.ac.id/ | Judul, abstrak, metadata skripsi/TA |
| VM-3 | Universitas Gadjah Mada | https://etd.repository.ugm.ac.id/ | Judul, abstrak, metadata tesis/TA |
| VM-4 | Universitas Sumatera Utara | https://repository.usu.ac.id/ | Judul, abstrak, metadata skripsi/TA |

---

## 3. Spesifikasi VM & Node

### Spesifikasi Minimum per VM

```yaml
# Spesifikasi Setiap Node VM
vm_spec:
  cpu:     2 vCPU          # minimum 1 vCPU masih bisa berjalan (lihat catatan)
  ram:     8 GB            # nyaman untuk semua servis; minimum 2 GB jika hanya geth + API
  storage: 20 GB SSD       # chain data PoA kelas kecil, 20 GB sudah sangat cukup
  os:      Ubuntu Server 22.04 LTS
  network: jaringan internal lab / NAT

software_stack:
  blockchain_client: go-ethereum (geth) v1.13+   # ringan di Clique PoA, tanpa mining
  database_lokal:    LevelDB (state, bawaan geth) + PostgreSQL (metadata, opsional)
  plagiarism_engine: Python 3.11 + SimHash + MinHash LSH
  api_server:        Node.js 20 + Express.js
  container:         Docker 24 + Docker Compose
  monitoring:        Prometheus + Grafana (opsional, jika resources cukup)

# ── Catatan Kebutuhan CPU ──────────────────────────────────────────────
#
# 2 vCPU : Direkomendasikan untuk tugas kelas. Geth + Express API +
#           plagiarism check bisa berjalan paralel tanpa bottleneck.
#           RAM 4 GB nyaman untuk semua servis aktif sekaligus.
#
# Geth Clique PoA hanya ~50–150 MB RAM saat idle, lonjakan saat sync blok.
# PostgreSQL bisa diganti file JSON/SQLite jika RAM terbatas.
```

### Komponen per Node

```
VM-X/
├── blockchain/
│   ├── geth/               # Ethereum client (Clique PoA)
│   │   ├── keystore/       # Wallet & signing key node
│   │   ├── chaindata/      # Data blockchain lokal
│   │   └── genesis.json    # Genesis block konfigurasi
│   └── contracts/          # Compiled smart contracts (.abi, .bin)
│
├── backend/
│   ├── api/                # REST API server
│   ├── services/
│   │   ├── submission.js   # Logika submit skripsi
│   │   ├── plagiarism.py   # Engine cek plagiasi
│   │   └── sync.js         # Sinkronisasi antar node
│   └── utils/
│       ├── hashing.js      # SHA-256, SimHash utilities
│       └── ipfs.js         # Upload dokumen ke IPFS
│
├── database/
│   ├── postgres/           # Metadata & full-text index
│   └── leveldb/            # State cache blockchain
│
├── ipfs/                   # Node IPFS lokal (opsional)
└── monitoring/             # Prometheus, Grafana configs
```

---

## 4. Arsitektur Sistem

### Layer Arsitektur

```
┌─────────────────────────────────────────────────────────┐
│                    LAYER APLIKASI                        │
│  Portal Web Kelompok │ Demo App │ REST Client / Postman  │
└─────────────────────────────────────────────────────────┘
                           ▼  REST API / GraphQL
┌─────────────────────────────────────────────────────────┐
│                    LAYER LAYANAN                         │
│  Submission Svc │ Verification Svc │ Plagiarism Svc     │
│  Search Svc     │ Audit Svc        │ Notification Svc   │
└─────────────────────────────────────────────────────────┘
                           ▼  ABI / Contract Calls
┌─────────────────────────────────────────────────────────┐
│                   LAYER SMART CONTRACT                   │
│  ThesisRegistry.sol │ PlagiarismRegistry.sol            │
│  AccessControl.sol  │ GroupRegistry.sol                 │
└─────────────────────────────────────────────────────────┘
                           ▼  Ethereum / Fabric
┌─────────────────────────────────────────────────────────┐
│                   LAYER BLOCKCHAIN                       │
│  Consensus (Clique PoA)  │  P2P Network (devp2p)       │
│  State Machine (EVM)     │  Gossip Protocol             │
└─────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   LAYER PENYIMPANAN                      │
│  On-chain: Hash, Metadata, Fingerprint (kecil, ~500B)  │
│  Off-chain: Full PDF → IPFS (content-addressed)        │
│  Local DB: Full-text Index, Cache (PostgreSQL)         │
└─────────────────────────────────────────────────────────┘
```

### Strategi Penyimpanan: On-chain vs Off-chain

```
┌────────────────────────────────────────────────────────────────┐
│  BLOCKCHAIN (On-chain) — Data kecil, permanen, terverifikasi   │
│  ─────────────────────────────────────────────────────────────  │
│  ✔ SHA-256 hash dokumen PDF                                    │
│  ✔ SimHash fingerprint konten (64-bit)                         │
│  ✔ Metadata: judul, NIM, tahun, prodi, kode kelompok           │
│  ✔ IPFS CID (Content Identifier) dokumen                       │
│  ✔ Timestamp registrasi (Unix epoch)                           │
│  ✔ Tanda tangan digital institusi (ECDSA)                      │
└────────────────────────────────────────────────────────────────┘
                           ↕  CID Reference
┌────────────────────────────────────────────────────────────────┐
│  IPFS (Off-chain) — File besar, content-addressed              │
│  ─────────────────────────────────────────────────────────────  │
│  ✔ File PDF skripsi lengkap                                    │
│  ✔ File abstrak (TXT/HTML)                                     │
│  ✔ Metadata extended (JSON)                                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. Struktur Data Blok

### Genesis Block (`genesis.json`)

```json
{
  "config": {
    "chainId": 20260315,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "clique": {
      "period": 5,
      "epoch": 30000
    }
  },
  "difficulty": "1",
  "gasLimit": "8000000",
  "extradata": "0x0000000000000000000000000000000000000000000000000000000000000000[ADDR_K1][ADDR_K2][ADDR_K3][ADDR_K4]0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {
    "ADDRESS_VM1_K1": { "balance": "1000000000000000000000" },
    "ADDRESS_VM2_K2": { "balance": "1000000000000000000000" },
    "ADDRESS_VM3_K3": { "balance": "1000000000000000000000" },
    "ADDRESS_VM4_K4": { "balance": "1000000000000000000000" }
  }
}
```

### Struktur Data Skripsi (On-chain Record)

```solidity
struct Thesis {
    // Identitas Dokumen
    bytes32  documentHash;       // SHA-256 hash file PDF (32 bytes)
    uint64   simhash;            // SimHash fingerprint konten (8 bytes)
    string   ipfsCID;            // IPFS Content Identifier (CIDv1)

    // Metadata Akademik
    string   title;              // Judul skripsi
    string   authorNIM;          // NIM mahasiswa (terenkripsi partial)
    string   authorName;         // Nama mahasiswa
    string   program;            // Program studi
    uint16   year;               // Tahun kelulusan
    string   keywords;           // Kata kunci (comma-separated)
    string   abstractHash;       // SHA-256 hash abstrak

    // Metadata Kelompok/Node
    address  institutionAddr;    // Address wallet node kelompok
    string   institutionCode;    // Kode kelompok (K1/K2/K3/K4)
    address  supervisorAddr;     // Address pembimbing (opsional)
    bytes    institutionSig;     // Tanda tangan ECDSA kelompok

    // Metadata Sistem
    uint256  timestamp;          // Waktu registrasi (Unix epoch)
    uint256  blockNumber;        // Nomor blok saat pendaftaran
    bool     isActive;           // Status aktif/dicabut
    uint8    status;             // 0=pending, 1=active, 2=flagged, 3=revoked
}
```

### Contoh Data Record Skripsi

```json
{
  "documentHash": "0xa3f1c8d2e9b47f6c1a2d3e4f5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4",
  "simhash": "0x7F4A3B2C1D0E9F8A",
  "ipfsCID": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
  "title": "Implementasi Machine Learning untuk Prediksi Churn Pelanggan Telekomunikasi",
  "authorNIM": "K1-2021***456",
  "authorName": "Andi Wijaya",
  "program": "Teknik Informatika",
  "year": 2025,
  "keywords": "machine learning, churn prediction, telekomunikasi, random forest",
  "abstractHash": "0xb4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
  "institutionCode": "K1",
  "universitas": "Telkom University",
  "repositoryUrl": "https://repository.telkomuniversity.ac.id/",
  "institutionAddr": "0x1aB2cD3eF4aB5cD6eF7aB8cD9eF0aB1cD2eF3aB4",
  "timestamp": 1741996800,
  "blockNumber": 1024,
  "status": 1
}
```

---

## 6. Smart Contract

### `ThesisRegistry.sol` — Kontrak Utama

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ThesisRegistry
 * @notice Registri skripsi terdesentralisasi untuk deteksi plagiasi
 * @dev Tugas Kelas SKT — dijalankan pada jaringan 4 node (1 VM per kelompok)
 */
contract ThesisRegistry {

    // ── Tipe Data ──────────────────────────────────────────
    struct Thesis {
        bytes32 documentHash;
        uint64  simhash;
        string  ipfsCID;
        string  title;
        string  authorNIM;
        string  program;
        uint16  year;
        string  keywords;
        address institutionAddr;
        string  institutionCode; // Kode kelompok: K1/K2/K3/K4
        uint256 timestamp;
        uint8   status; // 0=pending, 1=active, 2=flagged, 3=revoked
    }

    struct PlagiarismReport {
        bytes32 sourceHash;
        bytes32 targetHash;
        uint8   similarityPercent; // 0–100
        string  reportType;        // "exact" | "partial" | "paraphrase"
        address reportedBy;
        uint256 reportedAt;
        bool    resolved;
    }

    // ── State Variables ────────────────────────────────────
    mapping(bytes32 => Thesis)           public theses;
    mapping(bytes32 => PlagiarismReport[]) public plagReports;
    mapping(address => bool)             public authorizedInstitutions;
    mapping(address => string)           public institutionNames;
    bytes32[]                            public thesisIndex;

    address public admin;
    uint256 public totalTheses;
    uint256 public totalReports;

    // ── Events ─────────────────────────────────────────────
    event ThesisRegistered(
        bytes32 indexed docHash,
        string  institutionCode,
        string  title,
        uint256 timestamp
    );
    event ThesisFlagged(
        bytes32 indexed docHash,
        bytes32 indexed similarTo,
        uint8   similarity
    );
    event ThesisRevoked(bytes32 indexed docHash, address revokedBy);
    event InstitutionAdded(address indexed inst, string name);

    // ── Modifiers ──────────────────────────────────────────
    modifier onlyAdmin() {
        require(msg.sender == admin, "ThesisRegistry: not admin");
        _;
    }

    modifier onlyInstitution() {
        require(
            authorizedInstitutions[msg.sender],
            "ThesisRegistry: not authorized institution"
        );
        _;
    }

    modifier thesisExists(bytes32 _hash) {
        require(theses[_hash].timestamp != 0, "ThesisRegistry: thesis not found");
        _;
    }

    // ── Constructor ────────────────────────────────────────
    constructor() {
        admin = msg.sender;
    }

    // ── Institution Management ─────────────────────────────
    function addInstitution(address _inst, string calldata _name)
        external onlyAdmin
    {
        authorizedInstitutions[_inst] = true;
        institutionNames[_inst] = _name;
        emit InstitutionAdded(_inst, _name);
    }

    // ── Core Functions ─────────────────────────────────────

    /**
     * @notice Mendaftarkan skripsi baru ke blockchain
     * @param _docHash   SHA-256 hash dokumen PDF
     * @param _simhash   SimHash 64-bit fingerprint konten
     * @param _ipfsCID   IPFS CID dokumen
     * @param _title     Judul skripsi
     * @param _nim       NIM mahasiswa
     * @param _program   Program studi
     * @param _year      Tahun lulus
     * @param _keywords  Kata kunci
     * @param _instCode  Kode kelompok (K1/K2/K3/K4)
     */
    function registerThesis(
        bytes32       _docHash,
        uint64        _simhash,
        string calldata _ipfsCID,
        string calldata _title,
        string calldata _nim,
        string calldata _program,
        uint16          _year,
        string calldata _keywords,
        string calldata _instCode
    ) external onlyInstitution {
        require(theses[_docHash].timestamp == 0, "ThesisRegistry: already registered");

        theses[_docHash] = Thesis({
            documentHash:    _docHash,
            simhash:         _simhash,
            ipfsCID:         _ipfsCID,
            title:           _title,
            authorNIM:       _nim,
            program:         _program,
            year:            _year,
            keywords:        _keywords,
            institutionAddr: msg.sender,
            institutionCode: _instCode,
            timestamp:       block.timestamp,
            status:          1
        });

        thesisIndex.push(_docHash);
        totalTheses++;

        emit ThesisRegistered(_docHash, _instCode, _title, block.timestamp);
    }

    /**
     * @notice Melaporkan potensi plagiasi antar dua dokumen
     */
    function reportPlagiarism(
        bytes32       _sourceHash,
        bytes32       _targetHash,
        uint8         _similarity,
        string calldata _reportType
    ) external onlyInstitution thesisExists(_sourceHash) thesisExists(_targetHash) {
        require(_similarity <= 100, "ThesisRegistry: invalid similarity");
        require(_similarity >= 30,  "ThesisRegistry: similarity too low to report");

        plagReports[_sourceHash].push(PlagiarismReport({
            sourceHash:       _sourceHash,
            targetHash:       _targetHash,
            similarityPercent: _similarity,
            reportType:       _reportType,
            reportedBy:       msg.sender,
            reportedAt:       block.timestamp,
            resolved:         false
        }));

        if (_similarity >= 70) {
            theses[_sourceHash].status = 2; // flagged
            emit ThesisFlagged(_sourceHash, _targetHash, _similarity);
        }

        totalReports++;
    }

    /**
     * @notice Mencabut registrasi skripsi (hanya institusi pemilik)
     */
    function revokeThesis(bytes32 _docHash)
        external onlyInstitution thesisExists(_docHash)
    {
        require(
            theses[_docHash].institutionAddr == msg.sender,
            "ThesisRegistry: not thesis owner"
        );
        theses[_docHash].status = 3;
        emit ThesisRevoked(_docHash, msg.sender);
    }

    // ── Query Functions ────────────────────────────────────
    function getThesis(bytes32 _docHash)
        external view returns (Thesis memory)
    {
        return theses[_docHash];
    }

    function getThesisCount() external view returns (uint256) {
        return thesisIndex.length;
    }

    function getPlagReports(bytes32 _docHash)
        external view returns (PlagiarismReport[] memory)
    {
        return plagReports[_docHash];
    }

    function getAllHashes(uint256 _offset, uint256 _limit)
        external view returns (bytes32[] memory)
    {
        uint256 end = _offset + _limit;
        if (end > thesisIndex.length) end = thesisIndex.length;
        bytes32[] memory result = new bytes32[](end - _offset);
        for (uint256 i = _offset; i < end; i++) {
            result[i - _offset] = thesisIndex[i];
        }
        return result;
    }
}
```

---

## 7. Mekanisme Konsensus

### Clique PoA (Proof of Authority) — Pilihan Utama

```
Alasan Memilih Clique PoA untuk Tugas Kelas (4 Kelompok):
  ✔ Identitas validator (kelompok) sudah diketahui dan terverifikasi oleh dosen
  ✔ Throughput tinggi: ~200 TPS vs Bitcoin 7 TPS
  ✔ Finality cepat: 5 detik per blok
  ✔ Hemat energi: tidak ada mining kompetitif
  ✔ Deterministik: cocok untuk simulasi dan pengujian di kelas
```

```
Aturan Konsensus Clique:
┌─────────────────────────────────────────────────────────────┐
│  Signer Set = { K1, K2, K3, K4 }  →  4 Validator           │
│                                                              │
│  Blok valid jika ditandatangani oleh signer yang bergiliran │
│  (round-robin) dan telah menunggu minimal EPOCH blok        │
│                                                              │
│  Voting untuk tambah/hapus signer:                          │
│    → Butuh ⌈N/2⌉ + 1 = 3 suara dari 4 node               │
│                                                              │
│  Signer tidak boleh menandatangani 2 blok berturut-turut    │
│  kecuali tidak ada signer lain yang aktif (DIFF_NOTURN=2)  │
└─────────────────────────────────────────────────────────────┘
```

### Skenario Fault Tolerance

```
Konfigurasi: 4 node, toleransi fault = ⌊(4-1)/3⌋ = 1 node

┌──────┬────────────┬──────────────────────────────────┐
│ Node │ Status     │ Kondisi Jaringan                 │
├──────┼────────────┼──────────────────────────────────┤
│  4   │ Semua UP   │ Normal, konsensus berjalan       │
│  3   │ 1 DOWN     │ Normal, jaringan tetap berjalan  │
│  2   │ 2 DOWN     │ ⚠️  Jaringan tertunda (no quorum) │
│  1   │ 3 DOWN     │ ❌ Jaringan berhenti              │
└──────┴────────────┴──────────────────────────────────┘

Untuk keandalan lebih tinggi → tambah ke 7 node (toleransi 2 fault)
```

---

## 8. Alur Kerja Sistem

### 8.1 Alur Submit Skripsi Baru

```
Anggota Kelompok / Penguji
        │
        │ (1) Upload PDF + Metadata ke portal node kelompok
        ▼
┌─────────────────┐
│  Backend VM-X   │
│  (misal VM-1/K1)│
│                 │
│ (2) Generate:   │
│   • SHA-256     │ ──── (3) Upload PDF ────► IPFS Node
│   • SimHash     │                         (dapatkan CID)
│   • Keywords    │
└───────┬─────────┘
        │
        │ (4) Pre-check: apakah hash sudah ada di blockchain?
        ▼
┌─────────────────────────────────────────┐
│          BLOCKCHAIN QUERY               │
│  getThesis(docHash) → null? lanjut     │
└───────┬─────────────────────────────────┘
        │
        │ (5) Cek plagiasi awal (SimHash comparison)
        ▼
┌───────────────────────────────────────────────────────┐
│               PLAGIARISM ENGINE (Python)              │
│                                                       │
│  a. Ambil semua simhash dari blockchain               │
│  b. Hitung Hamming distance setiap pasang             │
│  c. Jika distance < threshold (16 bit) → mirip       │
│  d. Jika mirip → ambil full text dari IPFS,          │
│     jalankan MinHash + Jaccard similarity             │
│  e. Return: { isClear: bool, matches: [...] }        │
└───────┬───────────────────────────────────────────────┘
        │
        ├──── Similarity ≥ 80%? ──► ❌ Tolak, laporan ke kelompok pemilik dokumen
        │
        ├──── 30% ≤ Similarity < 80%? ──► ⚠️  Submit + flag untuk review
        │
        └──── Similarity < 30%? ──► ✅ Lanjut ke registrasi blockchain
        │
        │ (6) Submit transaksi ke node lokal
        ▼
┌─────────────────┐     (7) Broadcast via     ┌─────────────────┐
│    VM-1 (K1)    │ ──── Gossip Protocol ────► │    VM-2 (K2)    │
│  [Pending TX]   │                            │  [Pending TX]   │
└─────────────────┘                            └─────────────────┘
        │                                               │
        ▼                       (8) Consensus (Clique)  ▼
┌───────────────────────────────────────────────────────────────┐
│  Signer giliran menandatangani blok baru                      │
│  Blok di-broadcast ke semua node                              │
│  Semua node memvalidasi dan menambahkan ke chain lokal        │
└───────────────────────────────────────────────────────────────┘
        │
        │ (9) Konfirmasi ke kelompok pengunggah
        ▼
   ✅ Skripsi terdaftar di blockchain dengan nomor blok & TX hash
```

### 8.2 Alur Cek Plagiasi (Query)

```
Pengguna/Staff
      │
      │ (1) Submit abstrak atau judul untuk dicek
      ▼
┌──────────────────┐
│  API Server VM-X │
└────────┬─────────┘
         │
         │ (2) Generate SimHash dari teks input
         ▼
┌─────────────────────────────────────────────────────┐
│              PLAGIARISM CHECK ENGINE                │
│                                                     │
│  Step 1: Fetch semua record dari blockchain         │
│          (via getAllHashes + getThesis batch)        │
│                                                     │
│  Step 2: Hamming Distance Screening                 │
│          Input SimHash vs setiap simhash on-chain   │
│          Sortir berdasarkan jarak terkecil          │
│          Kandidat = jarak ≤ 16 bit (dari 64 bit)   │
│                                                     │
│  Step 3: Full-text Analysis (kandidat saja)         │
│          Unduh PDF dari IPFS                        │
│          Ekstrak teks → tokenisasi → shingling      │
│          MinHash LSH → Jaccard similarity           │
│                                                     │
│  Step 4: Generate Laporan                           │
│          { hash, judul, kelompok, similarity% }     │
└─────────────────────────────────────────────────────┘
         │
         ▼
   Output: Daftar skripsi mirip + persentase kemiripan
```

---

## 9. Deteksi Plagiasi

### Algoritma yang Digunakan

#### A. SimHash (Locality Sensitive Hashing)

```python
import hashlib
from typing import List

def generate_simhash(text: str, bits: int = 64) -> int:
    """
    Menghasilkan SimHash 64-bit dari teks.
    Teks yang mirip menghasilkan hash dengan Hamming distance kecil.
    """
    # Tokenisasi: split menjadi kata/shingle
    tokens = tokenize(text)  # 3-gram karakter

    v = [0] * bits

    for token in tokens:
        # Hash setiap token dengan SHA-256, ambil `bits` pertama
        h = int(hashlib.sha256(token.encode()).hexdigest(), 16)
        for i in range(bits):
            bit = (h >> i) & 1
            v[i] += 1 if bit == 1 else -1

    # Finalisasi: bit ke-1 jika positif, 0 jika negatif
    simhash = 0
    for i in range(bits):
        if v[i] > 0:
            simhash |= (1 << i)

    return simhash


def hamming_distance(hash1: int, hash2: int) -> int:
    """Menghitung Hamming distance antara dua SimHash."""
    xor = hash1 ^ hash2
    return bin(xor).count('1')


def is_similar(h1: int, h2: int, threshold: int = 16) -> bool:
    """
    Threshold = 16 dari 64 bit → kemiripan ~75%
    Makin kecil threshold → makin ketat
    """
    return hamming_distance(h1, h2) <= threshold
```

#### B. MinHash + Jaccard Similarity (Full-text)

```python
from datasketch import MinHash, MinHashLSH

def compute_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Membuat MinHash dari shingles teks."""
    m = MinHash(num_perm=num_perm)
    shingles = set()

    words = text.lower().split()
    for i in range(len(words) - 2):
        shingle = ' '.join(words[i:i+3])  # 3-gram kata
        shingles.add(shingle.encode('utf-8'))

    for shingle in shingles:
        m.update(shingle)

    return m


def estimate_jaccard(m1: MinHash, m2: MinHash) -> float:
    """Estimasi Jaccard similarity menggunakan MinHash."""
    return m1.jaccard(m2)


def plagiarism_check(input_text: str, all_theses: list) -> list:
    """
    Pipeline deteksi plagiasi lengkap.
    Return: list of {hash, title, institution, similarity}
    """
    results = []

    # Step 1: SimHash screening (cepat, O(n))
    input_simhash = generate_simhash(input_text)
    candidates = [
        t for t in all_theses
        if is_similar(input_simhash, t['simhash'], threshold=16)
    ]

    # Step 2: MinHash full-text (hanya kandidat)
    input_minhash = compute_minhash(input_text)
    for candidate in candidates:
        full_text = fetch_from_ipfs(candidate['ipfsCID'])
        cand_minhash = compute_minhash(full_text)
        similarity = estimate_jaccard(input_minhash, cand_minhash)

        if similarity >= 0.30:  # ≥ 30% → dilaporkan
            results.append({
                'hash':        candidate['documentHash'],
                'title':       candidate['title'],
                'institution': candidate['institutionCode'],
                'year':        candidate['year'],
                'similarity':  round(similarity * 100, 2),
                'verdict':     verdict(similarity)
            })

    return sorted(results, key=lambda x: x['similarity'], reverse=True)


def verdict(sim: float) -> str:
    if sim >= 0.80: return 'PLAGIAT'
    if sim >= 0.50: return 'SANGAT MIRIP'
    if sim >= 0.30: return 'MIRIP - PERLU REVIEW'
    return 'AMAN'
```

### Tabel Interpretasi Hasil

| Similarity | Kategori | Tindakan |
|---|---|---|
| ≥ 80% | **PLAGIAT** | Otomatis ditolak, flag on-chain, notifikasi kedua kelompok pemilik |
| 50% – 79% | **Sangat Mirip** | Didaftarkan dengan status `flagged`, dilaporkan ke dosen/asisten |
| 30% – 49% | **Mirip** | Didaftarkan, laporan dikirim ke kelompok terkait |
| < 30% | **Aman** | Didaftarkan normal dengan status `active` |

---

## 10. API Endpoint

### REST API per Node (`http://10.0.0.X:8080/api/v1`)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        THESIS ENDPOINTS                              │
├────────┬──────────────────────────────┬────────────────────────────┤
│ Method │ Path                         │ Deskripsi                  │
├────────┼──────────────────────────────┼────────────────────────────┤
│ POST   │ /thesis/register             │ Daftarkan skripsi baru     │
│ GET    │ /thesis/:hash                │ Ambil detail skripsi       │
│ GET    │ /thesis/search?q=...         │ Cari skripsi by keyword    │
│ GET    │ /thesis/group/:code          │ List skripsi per kelompok  │
│ DELETE │ /thesis/:hash/revoke         │ Cabut registrasi           │
│ GET    │ /thesis/stats                │ Statistik keseluruhan      │
├────────┼──────────────────────────────┼────────────────────────────┤
│                      PLAGIARISM ENDPOINTS                            │
├────────┼──────────────────────────────┼────────────────────────────┤
│ POST   │ /plagiarism/check            │ Cek plagiasi teks/file     │
│ GET    │ /plagiarism/reports/:hash    │ Laporan plagiasi per dokumen│
│ POST   │ /plagiarism/report           │ Laporkan plagiasi manual   │
│ PATCH  │ /plagiarism/report/:id/resolve│ Resolve laporan plagiasi  │
├────────┼──────────────────────────────┼────────────────────────────┤
│                        NETWORK ENDPOINTS                             │
├────────┼──────────────────────────────┼────────────────────────────┤
│ GET    │ /network/peers               │ List node aktif            │
│ GET    │ /network/status              │ Status sinkronisasi node   │
│ GET    │ /network/blocks/latest       │ Info blok terbaru          │
└────────┴──────────────────────────────┴────────────────────────────┘
```

### Contoh Request & Response

```json
// POST /api/v1/thesis/register
// Request Body:
{
  "title": "Implementasi Deep Learning untuk Klasifikasi Tanaman Padi",
  "authorNIM": "PG2022001",
  "program": "Teknik Informatika",
  "year": 2025,
  "keywords": "deep learning, CNN, klasifikasi, padi",
  "ipfsFile": "<base64 PDF atau CID jika sudah di-upload>",
  "groupCode": "K3"
}

// Response 201 Created:
{
  "success": true,
  "data": {
    "txHash": "0xabc123def456...",
    "blockNumber": 2048,
    "documentHash": "0x7f2d91...",
    "simhash": "0x4A3B2C1D",
    "ipfsCID": "bafybeihdwdcefgh...",
    "plagiarismCheck": {
      "status": "clear",
      "similarity": 12.4,
      "matches": []
    },
    "registeredAt": "2026-03-15T08:00:00Z"
  }
}
```

```json
// POST /api/v1/plagiarism/check
// Request Body:
{
  "text": "abstrak atau isi skripsi yang ingin dicek...",
  "checkDepth": "full"   // "quick" = SimHash only, "full" = + MinHash
}

// Response 200 OK:
{
  "success": true,
  "data": {
    "inputSimhash": "0x7F4A3B2C",
    "checkedAgainst": 1247,
    "processingMs": 342,
    "results": [
      {
        "documentHash": "0xa3f1c8...",
        "title": "Implementasi Machine Learning untuk Prediksi...",
        "group": "K1",
        "year": 2025,
        "similarity": 83.4,
        "verdict": "PLAGIAT",
        "ipfsCID": "bafybei..."
      }
    ]
  }
}
```

---

## 11. Skenario Pengujian

### Skenario 1: Submit Skripsi Orisinal

```
Aktor   : K3 – Izzah (VM-3 / UGM)
Input   : Skripsi dari repository.ugm.ac.id, belum ada di blockchain
Expected: Terdaftar di blockchain, TX hash diterima
          Status = active, similarity < 30%

Steps:
  1. POST /api/v1/thesis/register dari VM-3
  2. Backend generate SHA-256 + SimHash dari teks abstrak
  3. Plagiarism check vs semua data on-chain → no matches
  4. Submit ke geth node VM-3
  5. Blok dipropagasi ke VM-1, VM-2, VM-4
  6. Semua node konfirmasi blok yang sama
  7. Response: txHash returned ✅
```

### Skenario 2: Deteksi Plagiat Exact Copy

```
Aktor   : K1 – Nadiyatun (VM-1 / Tel-U)
Input   : File PDF identik dengan skripsi yang sudah didaftarkan oleh VM-2 (UB)
Expected: Tolak otomatis dengan laporan plagiasi

Steps:
  1. POST /api/v1/thesis/register dari VM-1
  2. SHA-256 identik → cek blockchain
  3. getThesis(hash) → sudah ada (milik K2/UB)
  4. Return 409 Conflict + info dokumen asli
  5. Tidak ada transaksi yang dikirim ke blockchain
```

### Skenario 3: Deteksi Plagiasi Partial (Parafrase)

```
Aktor   : K4 – Yoga (VM-4 / USU)
Input   : Skripsi dari repository USU yang ~65% kontennya mirip dengan
          skripsi dari repository UGM (VM-3)
Expected: Terdaftar dengan status "flagged", laporan dibuat

Steps:
  1. POST /api/v1/thesis/register dari VM-4
  2. SHA-256 berbeda (lolos pre-check)
  3. SimHash distance = 10 bit → kandidat!
  4. Unduh full text dari IPFS VM-3 (data UGM)
  5. MinHash Jaccard = 0.65 → 65%
  6. registerThesis() dipanggil + reportPlagiarism()
  7. Event ThesisFlagged di-emit
  8. Notifikasi ke VM-3 (K3/UGM) dan VM-4 (K4/USU)
  9. Status dokumen baru = 2 (flagged) ⚠️
```

### Skenario 4: Node VM-2 Offline

```
Kondisi : VM-2 (K2 – Steven / UB) mati / tidak dapat diakses
Expected: Jaringan tetap berjalan (3 dari 4 node aktif)

Steps:
  1. VM-2 offline (simulasi: docker stop vm2)
  2. VM-1 submit skripsi baru
  3. Transaksi broadcast ke VM-3 dan VM-4
  4. Signer aktif (3 node) cukup untuk konsensus
  5. Blok baru terbentuk dan divalidasi
  6. Saat VM-2 kembali online:
     a. Request sync dari peer
     b. Unduh blok yang terlewat
     c. Kembali aktif sebagai validator ✅
```

---

## 12. Sistem Penilaian

> Penilaian tugas ini terdiri dari **dua komponen utama**: uji fungsionalitas sistem dan refleksi antar anggota kelompok.

---

### 12.1 Penilaian Sistem (Uji Fungsionalitas)

Sistem dinilai berdasarkan seberapa lengkap dan benar setiap fungsi dapat didemonstrasikan. Pengujian dilakukan pada saat presentasi atau demo langsung.

#### Bobot Penilaian Sistem

| No | Komponen Uji | Indikator Keberhasilan | Bobot |
|----|-------------|------------------------|-------|
| 1 | **Jaringan P2P Aktif** | `net.peerCount == 3` di semua node, 4 validator terdeteksi | 10% |
| 2 | **Konsensus Berjalan** | Blok baru terbentuk setiap ±5 detik, semua node sinkron di block number yang sama | 10% |
| 3 | **Submit Skripsi** | Data dari repository universitas berhasil didaftarkan, TX hash dan block number tercatat | 15% |
| 4 | **Replikasi Data** | Skripsi yang didaftarkan dari VM-1 dapat dibaca dari VM-2, VM-3, VM-4 | 15% |
| 5 | **Deteksi Plagiasi** | Cek plagiasi lintas node berjalan, similarity score muncul, dokumen mirip terdeteksi | 20% |
| 6 | **Fault Tolerance** | Saat 1 node dimatikan, 3 node lain tetap dapat memproses transaksi | 10% |
| 7 | **Recovery Node** | Node yang sempat offline berhasil sync kembali saat dinyalakan | 5% |
| 8 | **Smart Contract** | Fungsi `registerThesis`, `getThesis`, `reportPlagiarism` dapat dipanggil dan hasilnya benar | 15% |

**Total Bobot Sistem: 100%**

#### Rubrik Penilaian per Komponen

| Skor | Kriteria |
|------|----------|
| **4** (Sangat Baik) | Fungsi berjalan sempurna, dapat didemonstrasikan, output sesuai ekspektasi |
| **3** (Baik) | Fungsi berjalan dengan minor issue, output sebagian besar benar |
| **2** (Cukup) | Fungsi berjalan sebagian, ada error yang dapat dijelaskan penyebabnya |
| **1** (Kurang) | Fungsi tidak berjalan, tetapi kelompok dapat menjelaskan konsepnya |
| **0** (Tidak Ada) | Fungsi tidak diimplementasikan dan tidak dapat dijelaskan |

---

### 12.2 Penilaian Refleksi Antar Anggota (Peer Assessment)

Setiap anggota kelompok **menilai kontribusi sesama anggota** dalam kelompoknya sendiri.

#### Formulir Peer Assessment

> Isi untuk setiap anggota kelompok selain diri sendiri, (akan disediakan dalam bentuk google form)

```
─────────────────────────────────────────────────────
 FORMULIR PEER ASSESSMENT — Tugas SKT Blockchain
 Kelas A | Kelompok : ___________
 Penilai  : (anonim)
─────────────────────────────────────────────────────

Nama Anggota yang Dinilai : ______________________

1. KONTRIBUSI TEKNIS
   Seberapa aktif berkontribusi dalam implementasi/coding?
   [ ] 4 – Sangat aktif, menjadi penggerak teknis kelompok
   [ ] 3 – Aktif, menyelesaikan bagian yang ditugaskan
   [ ] 2 – Cukup, kontribusi ada tapi kurang konsisten
   [ ] 1 – Minim, lebih banyak bergantung pada anggota lain

2. PEMAHAMAN MATERI
   Seberapa baik memahami konsep blockchain & SKT yang dikerjakan?
   [ ] 4 – Memahami dan mampu menjelaskan ke anggota lain
   [ ] 3 – Memahami materi yang dikerjakan sendiri
   [ ] 2 – Memahami sebagian, perlu banyak bimbingan
   [ ] 1 – Kurang memahami meski sudah dibimbing

3. KOLABORASI & KOMUNIKASI
   Seberapa baik berkomunikasi dan bekerja sama dengan tim?
   [ ] 4 – Sangat komunikatif, proaktif koordinasi antar kelompok
   [ ] 3 – Komunikatif, hadir dan responsif saat dibutuhkan
   [ ] 2 – Komunikasi kadang terlambat atau kurang responsif
   [ ] 1 – Sulit dihubungi, jarang hadir dalam diskusi

4. TANGGUNG JAWAB
   Apakah menyelesaikan tugas/bagian yang disepakati tepat waktu?
   [ ] 4 – Selalu tepat waktu, bahkan membantu bagian lain
   [ ] 3 – Tepat waktu untuk tugasnya sendiri
   [ ] 2 – Sering terlambat, perlu diingatkan
   [ ] 1 – Tidak menyelesaikan bagian yang ditugaskan

5. KOMENTAR KUALITATIF (wajib diisi)
   Apa kontribusi terbesar anggota ini dalam proyek?
   ___________________________________________________
   ___________________________________________________

   Apa yang perlu ditingkatkan?
   ___________________________________________________
   ___________________________________________________
─────────────────────────────────────────────────────
```

#### Rekapitulasi Skor Peer Assessment

Skor peer assessment **dirata-rata** dari semua penilai dalam kelompok:

$$\text{Skor Peer}_i = \frac{\sum_{j \neq i} \text{Nilai}_{ji}}{n - 1} \times 25$$

Dimana:
- $\text{Nilai}_{ji}$ = total skor dari penilai $j$ untuk anggota $i$ (maks 16 poin dari 4 kriteria × skor 4)
- $n$ = jumlah anggota kelompok
- Skor akhir peer dinormalisasi ke skala 0–25

---

### 12.3 Komposisi Nilai Akhir

| Komponen | Keterangan | Bobot |
|----------|------------|-------|
| **Nilai Sistem** | Rata-rata nilai uji fungsionalitas kelompok | **60%** |
| **Nilai Laporan** | Kualitas dokumen rancangan & dokumentasi teknis | **15%** |
| **Nilai Presentasi** | Kemampuan menjelaskan dan menjawab pertanyaan | **10%** |
| **Peer Assessment** | Penilaian kontribusi oleh sesama anggota kelompok | **15%** |

> **Catatan:** Nilai sistem adalah nilai kelompok (sama untuk semua anggota). Nilai akhir individu dapat berbeda akibat bobot peer assessment.

#### Contoh Perhitungan

```
Kelompok K3 — VM-3 (UGM)

Nilai Sistem    : 85  × 60% = 51.0
Nilai Laporan   : 80  × 15% = 12.0
Nilai Presentasi: 78  × 10% =  7.8

Anggota: Izzah Faiq Putri Madani
Skor Peer       : 22  × 15% =  3.3  (dari maks 25)

Nilai Akhir Izzah = 51.0 + 12.0 + 7.8 + 3.3 = 74.1
```

---

### 12.4 Jadwal & Mekanisme Pengumpulan

| Aktivitas | Waktu | Keterangan |
|-----------|-------|------------|
| Demo sistem (live) | Saat presentasi kelas | Semua fungsi diuji langsung di depan dosen |
| Pengumpulan formulir peer | Paling lambat H+1 presentasi | Dikumpulkan ke dosen/asisten secara individual dan anonim |
| Pengumpulan laporan MD/PDF | Bersamaan dengan demo | Dokumen rancangan ini |
| Rekap nilai | 1 minggu setelah presentasi | Diumumkan oleh dosen |

---

## Lampiran: Perintah Inisialisasi Jaringan

### Langkah Setup (Ringkas)

```bash
# 1. Inisialisasi genesis block di setiap VM
geth init --datadir ./chaindata genesis.json

# 2. Buat akun validator untuk setiap VM
geth account new --datadir ./chaindata
# Tambahkan address ke extradata genesis.json

# 3. Jalankan node VM-1 (K1) sebagai bootnode pertama
geth \
  --datadir ./chaindata \
  --networkid 20260315 \
  --port 30303 \
  --http --http.addr "0.0.0.0" --http.port 8545 \
  --http.api "eth,net,web3,personal,miner" \
  --mine --miner.etherbase <ADDRESS_K1> \
  --unlock <ADDRESS_K1> --password ./password.txt \
  --allow-insecure-unlock \
  --nodiscover \
  --verbosity 3

# 4. Kelompok 2, 3, 4 — jalankan node dengan bootnodes ke VM-1
geth \
  --datadir ./chaindata \
  --networkid 20260315 \
  --bootnodes "enode://<ENODE_VM1>@10.0.0.1:30303" \
  --port 30303 \
  --http --http.addr "0.0.0.0" --http.port 8545 \
  --mine --miner.etherbase <ADDRESS_NODE> \
  --unlock <ADDRESS_NODE> --password ./password.txt \
  --allow-insecure-unlock

# 5. Deploy smart contract — dilakukan bersama (salah satu kelompok)
npx hardhat run scripts/deploy.js --network skripsichain

# 6. Verifikasi jaringan (dilakukan setiap kelompok)
geth attach --datadir ./chaindata
> eth.blockNumber        // harus > 0
> net.peerCount          // harus = 3 (terhubung ke 3 kelompok lain)
> clique.getSigners()    // harus muncul 4 address (K1, K2, K3, K4)
```

---

*Dokumen ini merupakan rancangan teknis tugas kelas sistem blockchain publikasi skripsi untuk mata kuliah Sistem Komputasi Terdistribusi.*
*Setiap kelompok mengelola 1 VM sebagai node validator dalam jaringan bersama.*
*Revisi dapat dilakukan sesuai kebutuhan implementasi aktual di lab.*
