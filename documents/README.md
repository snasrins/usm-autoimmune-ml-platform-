# USM Autoimmune ML Platform

**Hybrid ML Platform for Autoimmune Disease Registry**  
Universiti Sains Malaysia × Aras Integrasi

---

## 🚀 Quick Links

- **[Quick Start Guide →](documents/QUICKSTART.md)** - Deploy in 5 minutes
- **[Deployment Guide →](documents/DEPLOYMENT.md)** - Complete step-by-step instructions
- **[Setup Documentation →](documents/SETUP.md)** - Detailed environment configuration
- **[Technical Overview →](documents/README.md)** - Full project documentation

---

## 📁 Project Structure

```
usm-autoimmune-ml-platform/
├── app/                    # FastAPI application code
│   ├── __init__.py
│   └── main.py            # Application entry point
├── config/                 # Configuration files (future)
├── documents/              # All project documentation
│   ├── README.md          # Technical overview
│   ├── QUICKSTART.md      # Quick start guide
│   ├── DEPLOYMENT.md      # Deployment instructions
│   └── SETUP.md           # Setup guide
├── init-db/                # PostgreSQL initialization
│   └── 01-schema.sql      # Database schema (7 tables)
├── scripts/                # Utility scripts
│   ├── generate-ssl-certs.sh
│   └── test_gpu.py        # GPU environment test
├── .env                    # Environment variables (DO NOT COMMIT)
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── docker-compose.yml      # Docker services configuration
├── Dockerfile              # Container image definition
└── requirements.txt        # Python dependencies

# Created on deployment:
├── data/                   # Data storage (gitignored)
│   ├── uploads/           # Uploaded files
│   ├── processed/         # Processed datasets
│   └── raw/               # Raw data backup
├── models/                 # ML model artifacts
└── logs/                   # Application logs
```

---

## 👥 Team

| Role | Name |
|------|------|
| **Project Director** | Mazdiana Makmor |
| **Project Manager** | Alia |
| **Solution Architect** | Veytri Yogan |
| **ML Engineer** | Iznie Humaiera |
| **Data Engineer** | Syarifah Fajriyah |

---

## 🎯 Project Timeline

- **Kick Off:** March 9, 2026
- **Development Complete:** April 21, 2026 (6 weeks)
- **Deployment & Handover:** October 1, 2026
- **Platform Access Until:** December 31, 2026

---

## 🔐 Security & Network

- **Network:** ZeroTier Private Network
- **Network ID:** `d5e5fb653720782f`
- **Platform IP:** `172.24.50.103`
- **Access:** Authorized devices only via ZeroTier

⚠️ **All patient data remains within encrypted private network**

---

## 🏃 Getting Started

### 1. New User?
Start with **[QUICKSTART.md](documents/QUICKSTART.md)** for immediate deployment.

### 2. Deploying to Production?
Follow **[DEPLOYMENT.md](documents/DEPLOYMENT.md)** for complete instructions.

### 3. Development Setup?
See **[SETUP.md](documents/SETUP.md)** for environment configuration.

---

## 📊 Current Status

**Sprint 1** (Infrastructure Setup)  
**Date:** March 12, 2026  
**Progress:** Configuration complete, ready for deployment

---

## 📞 Support

For technical issues or questions, contact the project team through official channels.

---

## 📄 License & Compliance

- **NMRR Compliant:** National Medical Research Registry guidelines
- **PDPA Compliant:** Personal Data Protection Act 2010 (Malaysia)
- **Ethics Clearance:** Required before processing real patient data

---

**Client:** Universiti Sains Malaysia (USM)  
**Vendor:** Aras Integrasi  
**Project Code:** USM-AUTOIMMUNE-ML-2026
