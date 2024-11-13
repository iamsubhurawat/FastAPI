# Importing dependencies
import os
import asyncio

from dotenv              import load_dotenv
from pydantic            import BaseModel
from passlib.context     import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()


# Database Configuration 
USERNAME          = os.getenv('DATABASE_USERNAME')
USERNAME_PASSWORD = os.getenv('DATABASE_USERNAME_PASSWORD')

url            = f"mongodb+srv://{USERNAME}:{USERNAME_PASSWORD}@cluster1.hnszelp.mongodb.net/?retryWrites=true&w=majority&appName=cluster1"
client         = AsyncIOMotorClient(url)
mongodb_client = client['FastDB']
db             = mongodb_client['Users']


# Information for Password generation
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# User model
class User(BaseModel):
    username: str
    email: str | None = None
    name: str | None = None
    disabled: bool | None = None


# Method to convert the Plain text password into Hashed password
def get_password_hash(password: str):
    return pwd_context.hash(password)


# Method to create a user in the database
async def create_user(username: str, password: str, email: str = None, name: str = None, disabled: bool = False):
    # Check if the user already exists or not
    existing_user = await db.find_one({"username": username})
    if existing_user:
        print("User already exists.")
        return

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create the user
    user = {
        "username": username,
        "email": email,
        "name": name,
        "disabled": disabled,
        "hashed_password": hashed_password
    }

    # Insert the user in the database
    await db.insert_one(user)
    print(f"User {username} created successfully!")


# Main function 
async def main():
    # Provide details for the new user
    username = "test"
    password = "test123"
    email = "test@gmail.com"
    name = "tester"
    disabled = False

    # Create the user
    await create_user(username, password, email, name, disabled)


if __name__ == "__main__":
    asyncio.run(main())