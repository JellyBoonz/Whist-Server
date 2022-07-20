"""'/user/create api"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from whist_server.database.user import UserInDb
from whist_server.services.password import PasswordService
from whist_server.services.user_db_service import UserDatabaseService

router = APIRouter(prefix='/user')


class CreateUserArgs(BaseModel):
    """
    JSON body for creating user
    """
    username: str
    password: str


@router.post('/create')
def create_user(request: CreateUserArgs, pwd_service=Depends(PasswordService),
                user_db_service=Depends(UserDatabaseService)):
    """
    Creates a new user.
    :param request: Must contain a 'username' and a 'password' field. If one is missing it raises
    HTTP 400 error.
    :param pwd_service: service to handle password requests.
    :param user_db_service: service to handle request to the database storing users.
    :return: the ID of the user or an error message.
    """
    user = UserInDb(username=request.username, hashed_password=pwd_service.hash(request.password))
    user_id = user_db_service.add(user)
    return {'user_id': user_id}
