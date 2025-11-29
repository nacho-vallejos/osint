from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    shodan_api_key: Optional[str] = None
    virustotal_api_key: Optional[str] = None
    securitytrails_api_key: Optional[str] = None
    hibp_api_key: Optional[str] = None
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
