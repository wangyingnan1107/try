from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo" # 或者 gpt-4o

    class Config:
        env_file = ".env"

settings = Settings()
