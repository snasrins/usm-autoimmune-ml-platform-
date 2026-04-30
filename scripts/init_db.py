"""
Database Initialization Script
Creates tables and seeds initial admin user
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.patient import Patient


def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def create_demo_users():
    """Create demo users for testing"""
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
            admin = User(
                email="admin@arasintegrasi.ai",
                username="admin",
                full_name="System Administrator",
                role="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            print("✓ Admin user created (username: admin, password: admin123)")
        
        # Create researcher user
        researcher_exists = db.query(User).filter(User.username == "researcher").first()
        if not researcher_exists:
            researcher = User(
                email="researcher@arasintegrasi.ai",
                username="researcher",
                full_name="Research Staff",
                role="doctor",
                hashed_password=get_password_hash("researcher123"),
                is_active=True,
                is_superuser=False
            )
            db.add(researcher)
            print("✓ Researcher user created (username: researcher, password: researcher123)")
        
        # Create viewer user
        viewer_exists = db.query(User).filter(User.username == "viewer").first()
        if not viewer_exists:
            viewer = User(
                email="viewer@arasintegrasi.ai",
                username="viewer",
                full_name="Data Viewer",
                role="user",
                hashed_password=get_password_hash("viewer123"),
                is_active=True,
                is_superuser=False
            )
            db.add(viewer)
            print("✓ Viewer user created (username: viewer, password: viewer123)")
        
        db.commit()
        
    except Exception as e:
        print(f"✗ Error creating demo users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("USM Autoimmune ML Platform - Database Initialization")
    print("=" * 60)
    
    init_db()
    create_demo_users()
    
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    print("\n Demo User Credentials:")
    print("-" * 60)
    print("  Admin:      username=admin,      password=admin123")
    print("  Researcher: username=researcher, password=researcher123")
    print("  Viewer:     username=viewer,     password=viewer123")
    print("-" * 60)
    print("\n Access Points:")
    print(f"  API Docs:  http://172.24.175.24:8000/docs")
    print(f"  pgAdmin:   http://172.24.175.24:5050")
    print(f"    Email:    admin@usm.edu.my")
    print(f"    Password: PgAdmin_P@ssw0rd_2026_CHANGE_THIS!")
    print("\n  Remember to change default passwords in production!")

