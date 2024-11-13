# Importing dependencies
import os

from mangum              import Mangum
from dotenv              import load_dotenv
from jose                import JWTError, jwt
from fastapi             import Depends, FastAPI, HTTPException, status
from pydantic            import BaseModel
from datetime            import datetime, timedelta
from passlib.context     import CryptContext
from fastapi.security    import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()


# Declaring information for Token and Password generation
ALGORITHM                   = "HS256"
SECRET_KEY                  = os.getenv('PASSWORD_ENCODING_KEY')
pwd_context                 = CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth_2_scheme              = OAuth2PasswordBearer(tokenUrl="login")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Database Configuration 
USERNAME          = os.getenv('DATABASE_USERNAME')
USERNAME_PASSWORD = os.getenv('DATABASE_USERNAME_PASSWORD')

url            = f"mongodb+srv://{USERNAME}:{USERNAME_PASSWORD}@cluster1.hnszelp.mongodb.net/?retryWrites=true&w=majority&appName=cluster1"
client         = AsyncIOMotorClient(url)
mongodb_client = client['FastDB']
db             = mongodb_client['Users']


# Declaring the models for Token and User
class Token(BaseModel):
    access_token: str
    token_type:   str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email:    str | None = None
    name:     str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str


# Initializing FastAPI 
app = FastAPI()
handler = Mangum(app)

# Method to verify the password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password,hashed_password)


# Method to convert the Plain text password into Hashed password
def get_password_hash(password):
    return pwd_context.hash(password)


# Method to retreive the user on the basis of username
async def get_user(username: str):
    user = await db.find_one({"username": username})
    if user:
        return UserInDB(**user)
    

# Method to authenticate the user based on given credentials
async def authenticate_user(username: str, password:str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password,user.hashed_password):
        return False
    return user


# Method to retreive the access token on the basis of given credentials
def create_access_token(data:dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp":expire, "sub": data.get("sub")})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt


# Method to retreive the current user
async def get_current_user(token: str = Depends(oauth_2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credential_exception
    return user


# Method to check whether the current user is active or not
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive User!")
    return current_user


# Greeting endpoint
@app.get("/")
async def greet():
    return {"Greet": "Hello! This is a message from Sourav Rawat."}


# Login Endpoint: To retreive the access token by providing the user credentials
@app.post("/login/",response_model=Token)
async def retreive_access_token(form_data: OAuth2PasswordRequestForm=Depends()):
    user = await authenticate_user(form_data.username,form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password",headers={"WWW-Authenticate":"Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub":user.username}, 
                                       expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "Bearer"}


# Read Endpoint: To retreive the details of current active user without hashed password
@app.get("/users/me/",response_model=User)
async def read_myself(current_user: User = Depends(get_current_active_user)):
    return current_user


# Read Endpoint: To retreive the details of current active user along with the hashed password
@app.get("/users/me/details/")
async def read_own_complete_details(current_user: User = Depends(get_current_active_user)):
    return [{"id": 1, "owner": current_user}]


# Update Endpoint: To update the details of a particular user with the help of username
@app.put("/users/update/", response_model=User)
async def update_user(updated_user: User, current_user: User = Depends(get_current_active_user)):
    username = current_user.username
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updated_data = updated_user.dict(exclude_unset=True)
    await db.update_one({"username": username}, {"$set": updated_data})
    user = await get_user(username)
    return user


# Delete Endpoint: To delete any particular user with the help of username
@app.delete("/users/delete/")
async def delete_user(current_user: User = Depends(get_current_active_user)):
    username = current_user.username
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete_one({"username": username})
    return {"detail": f"User {username} deleted successfully"}