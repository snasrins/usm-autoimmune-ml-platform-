"""
Comprehensive Database Seeding Script
Seeds all reference data: users, lab tests, and other initial data
Run this after creating fresh database or when data is missing

Usage: python scripts/seed_all_data.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.lab_test import LabTestDefinition
from sqlalchemy.exc import IntegrityError


def seed_users():
    """Create default users"""
    db = SessionLocal()
    
    users_data = [
        {
            "email": "admin@usm.edu.my",
            "username": "admin",
            "full_name": "System Administrator",
            "role": "admin",
            "password": "admin123",
            "is_superuser": True
        },
        {
            "email": "researcher@usm.edu.my",
            "username": "researcher",
            "full_name": "Research Staff",
            "role": "doctor",
            "password": "researcher123",
            "is_superuser": False
        },
        {
            "email": "viewer@usm.edu.my",
            "username": "viewer",
            "full_name": "Data Viewer",
            "role": "user",
            "password": "viewer123",
            "is_superuser": False
        }
    ]
    
    created_count = 0
    
    try:
        for user_data in users_data:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    hashed_password=get_password_hash(user_data["password"]),
                    is_active=True,
                    is_superuser=user_data["is_superuser"]
                )
                db.add(user)
                created_count += 1
                print(f"  ✓ Created user: {user_data['username']} (role: {user_data['role']})")
            else:
                print(f"  - User already exists: {user_data['username']}")
        
        db.commit()
        print(f"\n✅ Users seeded: {created_count} new, {len(users_data) - created_count} existing")
        
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()


def seed_lab_tests():
    """Seed lab test definitions from SLE dataset"""
    db = SessionLocal()
    
    # Comprehensive lab test definitions from SLE dataset
    lab_tests = [
        # CBC - Complete Blood Count
        {"code": "wbc", "name": "WBC", "category": "Hematology", "type": "numeric", "diseases": ["SLE"]},
        {"code": "neu_percent", "name": "NEU%", "category": "Hematology", "type": "numeric", "diseases": ["SLE"]},
        {"code": "lym_percent", "name": "LYM%", "category": "Hematology", "type": "numeric", "diseases": ["SLE"]},
        {"code": "hgb", "name": "HGB", "category": "Hematology", "type": "numeric", "diseases": ["SLE"]},
        {"code": "plt", "name": "PLT", "category": "Hematology", "type": "numeric", "diseases": ["SLE"]},
        
        # Inflammation Markers
        {"code": "crp", "name": "CRP", "category": "Inflammation", "type": "numeric", "diseases": ["SLE"]},
        {"code": "esr", "name": "ESR", "category": "Inflammation", "type": "numeric", "diseases": ["SLE"]},
        {"code": "alb", "name": "ALB", "category": "Inflammation", "type": "numeric", "diseases": ["SLE"]},
        {"code": "glo", "name": "GLO", "category": "Inflammation", "type": "numeric", "diseases": ["SLE"]},
        
        # Kidney Function
        {"code": "urinary_protein", "name": "Urinary protein", "category": "Kidney_Function", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "urine_protein_quant", "name": "Urine protein quantification", "category": "Kidney_Function", "type": "numeric", "diseases": ["SLE"]},
        {"code": "acr", "name": "ACR", "category": "Kidney_Function", "type": "numeric", "diseases": ["SLE"]},
        {"code": "urine_protein_24h", "name": "24-hour urine protein quantification", "category": "Kidney_Function", "type": "numeric", "diseases": ["SLE"]},
        
        # Immune Cells
        {"code": "cd3", "name": "CD3", "category": "Immune_Cells", "type": "numeric", "diseases": ["SLE"]},
        {"code": "cd4", "name": "CD4", "category": "Immune_Cells", "type": "numeric", "diseases": ["SLE"]},
        {"code": "cd8", "name": "CD8", "category": "Immune_Cells", "type": "numeric", "diseases": ["SLE"]},
        {"code": "nk", "name": "NK", "category": "Immune_Cells", "type": "numeric", "diseases": ["SLE"]},
        {"code": "cd19", "name": "CD19", "category": "Immune_Cells", "type": "numeric", "diseases": ["SLE"]},
        
        # Complement System
        {"code": "c3", "name": "C3", "category": "Complement", "type": "numeric", "diseases": ["SLE"]},
        {"code": "c4", "name": "C4", "category": "Complement", "type": "numeric", "diseases": ["SLE"]},
        
        # Immunoglobulins
        {"code": "igg", "name": "IgG", "category": "Immunoglobulin", "type": "numeric", "diseases": ["SLE"]},
        {"code": "igm", "name": "IgM", "category": "Immunoglobulin", "type": "numeric", "diseases": ["SLE"]},
        {"code": "ige", "name": "IgE", "category": "Immunoglobulin", "type": "numeric", "diseases": ["SLE"]},
        {"code": "iga", "name": "IgA", "category": "Immunoglobulin", "type": "numeric", "diseases": ["SLE"]},
        
        # Clinical Score
        {"code": "sledai", "name": "SLEDAI", "category": "Clinical_Score", "type": "numeric", "diseases": ["SLE"]},
        
        # Autoantibodies - Primary Panel
        {"code": "ana", "name": "ANA", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "nrnp_sm", "name": "nRNP/Sm", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "sm", "name": "SM", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "ssa", "name": "SSA", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "ro_52", "name": "RO-52", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "ssb", "name": "SSB", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "scl70", "name": "Scl70", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "jo1", "name": "Jo1", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "cenpb", "name": "CENPB", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "dsdna", "name": "dsDNA", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "nucleosome", "name": "Nucleosome", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "histone", "name": "Histone", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "ribosomal_p", "name": "Ribosomal P protein", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        
        # Autoantibodies - Extended Panel
        {"code": "rnp70", "name": "RNP70", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "jo_1", "name": "JO-1", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "scl_70", "name": "Scl-70", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "ama_2", "name": "AMA-2", "category": "Autoantibody", "type": "qualitative", "diseases": ["SLE"]},
        
        # Antiphospholipid Antibodies
        {"code": "anti_beta2_gp", "name": "Anti-β 2 glycoprotein Ig(GAM)", "category": "Antiphospholipid", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "acl_igg", "name": "Anticardiolipin antibody IgG", "category": "Antiphospholipid", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "acl_igm", "name": "Anticardiolipin anti-antibody IGM", "category": "Antiphospholipid", "type": "qualitative", "diseases": ["SLE"]},
        
        # ANCA Panel
        {"code": "pr3", "name": "PR3", "category": "ANCA", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "gbm", "name": "GBM", "category": "ANCA", "type": "qualitative", "diseases": ["SLE"]},
        {"code": "mpo", "name": "MPO", "category": "ANCA", "type": "qualitative", "diseases": ["SLE"]},
        
        # Vitamins
        {"code": "vit_d", "name": "25-OH VitD", "category": "Vitamin", "type": "numeric", "diseases": ["SLE"]},
    ]
    
    created_count = 0
    
    try:
        for test in lab_tests:
            existing = db.query(LabTestDefinition).filter(
                LabTestDefinition.test_code == test["code"]
            ).first()
            
            if not existing:
                lab_test = LabTestDefinition(
                    test_code=test["code"],
                    test_name=test["name"],
                    test_category=test["category"],
                    data_type=test["type"],
                    relevant_diseases=test["diseases"],
                    is_active=True
                )
                db.add(lab_test)
                created_count += 1
            else:
                print(f"  - Test already exists: {test['name']}")
        
        db.commit()
        print(f"\n✅ Lab tests seeded: {created_count} new, {len(lab_tests) - created_count} existing")
        print(f"   Total lab tests in database: {len(lab_tests)}")
        
    except Exception as e:
        print(f"❌ Error seeding lab tests: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    print("=" * 80)
    print("USM Autoimmune ML Platform - Database Seeding")
    print("=" * 80)
    
    print("\n📊 Seeding Users...")
    seed_users()
    
    print("\n🧪 Seeding Lab Test Definitions...")
    seed_lab_tests()
    
    print("\n" + "=" * 80)
    print("✅ Database seeding complete!")
    print("=" * 80)
    
    print("\n👤 User Credentials:")
    print("-" * 80)
    print("  Admin:      username=admin,      password=admin123")
    print("  Researcher: username=researcher, password=researcher123")
    print("  Viewer:     username=viewer,     password=viewer123")
    print("-" * 80)
    
    print("\n🌐 Access Points:")
    print(f"  API Docs:  http://172.24.175.24:8000/docs")
    print(f"  pgAdmin:   http://172.24.175.24:5050")
    print("\n⚠️  Remember to change default passwords in production!")


if __name__ == "__main__":
    main()
