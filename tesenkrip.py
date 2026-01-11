from passlib.context import CryptContext
ctx = CryptContext(schemes=["bcrypt"])
print(ctx.hash("2"))
