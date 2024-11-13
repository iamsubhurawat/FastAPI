1. Create a virtual enviroment:
   A virtual enviroment should be created using command "virtualenv .venv"
   
2. Activate the virtual enviroment:
   Activate the virtual enviroment .venv with the command ".venv/Scripts/activate"

3. Install the dependencies: 
   All the dependencies are given in a file requirements.txt so with the help of that install all the dependencies.
   run the command "pip install -r requirements.txt"

4. Create user for API testing: 
   Create a user to login and performing CRUD operations using FastAPI endpoints.
   run the python script with the command "python create_user.py"

5. Run the server: 
   Run the server by using the command "uvicorn main:app --reload"
