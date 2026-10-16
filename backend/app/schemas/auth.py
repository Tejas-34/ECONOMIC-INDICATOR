from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginCredentials(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: Optional[str] = Field(None, description="Username or email.")
    email: Optional[str] = Field(None, description="Email alias for username.")
    password: str = Field(..., description="Plaintext user password.")

    @model_validator(mode="before")
    @classmethod
    def harmonize_identity(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "email" in data and not data.get("username"):
                data["username"] = data["email"]
            elif "username" in data and not data.get("email"):
                data["email"] = data["username"]
        return data


class AuthUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique user identifier.")
    username: str = Field(..., description="Username.")
    email: Optional[str] = Field(None, description="Email address.")
    name: Optional[str] = Field("Lead Macro Analyst", description="Display name.")
    role: Literal["viewer", "admin"] = Field("viewer", description="User role ('viewer' or 'admin').")


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user: AuthUser = Field(..., description="Authenticated user profile.")
    accessToken: str = Field(..., description="JWT Bearer access token.")
    access_token: Optional[str] = Field(None, description="OAuth2 alias for accessToken.")
    token_type: str = Field("bearer", description="Token category.")
    expiresInSeconds: int = Field(3600, description="Token lifetime in seconds.")
    expires_in_seconds: Optional[int] = Field(3600, description="Alias for expiresInSeconds.")

    @model_validator(mode="before")
    @classmethod
    def synchronize_tokens(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "accessToken" in data and "access_token" not in data:
                data["access_token"] = data["accessToken"]
            elif "access_token" in data and "accessToken" not in data:
                data["accessToken"] = data["access_token"]
            if "expiresInSeconds" in data and "expires_in_seconds" not in data:
                data["expires_in_seconds"] = data["expiresInSeconds"]
            elif "expires_in_seconds" in data and "expiresInSeconds" not in data:
                data["expiresInSeconds"] = data["expires_in_seconds"]
        return data


class TokenData(BaseModel):
    sub: str = Field(..., description="User ID subject claim.")
    username: str = Field(..., description="User username.")
    role: str = Field("viewer", description="Role claim.")
    exp: int = Field(..., description="Expiration epoch timestamp.")
