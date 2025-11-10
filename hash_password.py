from werkzeug.security import generate_password_hash

password = input("Enter password to hash: ")
hashed = generate_password_hash(password)
print(f"\nHashed password:")
print(hashed)
print(f"\nAdd this to your .env file:")
print(f"COACH_PASSWORD_HASH={hashed}")