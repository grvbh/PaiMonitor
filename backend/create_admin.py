"""
One-off script to create the first admin user.
Run inside the backend container/venv:  python create_admin.py
"""
from app.database import SessionLocal, Base, engine
from app import models
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

email = input("Admin email: ").strip()
name = input("Admin name: ").strip()
password = input("Admin password: ").strip()

if db.query(models.User).filter(models.User.email == email).first():
    print("A user with that email already exists.")
else:
    admin = models.User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=models.UserRole.admin,
    )
    db.add(admin)
    db.commit()
    print(f"Admin user '{email}' created.")

db.close()
