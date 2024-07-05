from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordBearer
from typing import TypeVar, Optional, List, Annotated
from ...Application.LaiaBaseModel import ReadLaiaBaseModel, DeleteLaiaBaseModel, SearchLaiaBaseModel, UpdateLaiaBaseModel
from ...Application.LaiaUser import CreateRole
from ...Application.LaiaUser import JWTToken
from ...Domain.LaiaUser.Role import Role
from ...Domain.LaiaBaseModel.LaiaBaseModel import LaiaBaseModel
from ...Domain.LaiaBaseModel.ModelRepository import ModelRepository
from ...Domain.Shared.Utils.logger import _logger

T = TypeVar('T', bound='LaiaBaseModel')

async def CRUDRoleController(repository: ModelRepository=None, jwtSecretKey: str='secret_key', auth_required: bool = False):
    model = Role
    router = APIRouter(tags=[model.__name__])
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def get_auth_dependency():
        if auth_required:
            return Annotated[Optional[str], Depends(oauth2_scheme)]
        else:
            return Optional[str]
        
    async def get_user_roles(repository: ModelRepository=None, token: Optional[str] = None, jwtSecretKey: str = 'secret_key') -> List[str]:
        if not token:
            if auth_required:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization header")
            else:
                return ["admin"]

        try:
            payload = JWTToken.verify_jwt_token(token, jwtSecretKey)
            _logger.info(payload)
            
            user_roles_ids = payload.get("user_roles", [])
            _logger.info(user_roles_ids)
            user_roles = []
            for role in user_roles_ids:
                user_role = await ReadLaiaBaseModel.read_laia_base_model(role, Role, ['admin'], repository)
                user_roles.append(user_role['name'])

        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
        
        return user_roles

    admin_role, _ = await repository.get_items("role", skip=0, limit=10, filters={ "name": "admin"})
    if not admin_role:
        await CreateRole.create_role({"name": "admin"}, ["admin"], repository)

    @router.post("/role/", response_model=dict)
    async def create_element(element: Role, token: get_auth_dependency() = None):
        user_roles = await get_user_roles(repository, token, jwtSecretKey)
        try:
            return await CreateRole.create_role(dict(element), user_roles, repository)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.put("/role/{element_id}", response_model=dict)
    async def update_element(element_id: str, values: dict, token: get_auth_dependency() = None):
        user_roles = await get_user_roles(repository, token, jwtSecretKey)
        try:
            return await UpdateLaiaBaseModel.update_laia_base_model(element_id, values, model, user_roles, repository)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    @router.get("/role/{element_id}", response_model=dict)
    async def read_element(element_id: str, token: get_auth_dependency() = None):
        user_roles = await get_user_roles(repository, token, jwtSecretKey)
        try:
            return await ReadLaiaBaseModel.read_laia_base_model(element_id, model, user_roles, repository)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.delete("/role/{element_id}", response_model=str)
    async def delete_element(element_id: str, token: get_auth_dependency() = None):
        user_roles = await get_user_roles(repository, token, jwtSecretKey)
        try:
            await DeleteLaiaBaseModel.delete_laia_base_model(element_id, model, user_roles, repository)
            return f"Role deleted successfully"
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @router.post("/roles/", response_model=dict)
    async def search_element(token: get_auth_dependency() = None, skip: int = 0, limit: int = 10, filters: dict = {}, orders: dict = {}):
        user_roles = await get_user_roles(repository, token, jwtSecretKey)
        try:
            return await SearchLaiaBaseModel.search_laia_base_model(skip, limit, filters, orders, model, user_roles, repository)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return router