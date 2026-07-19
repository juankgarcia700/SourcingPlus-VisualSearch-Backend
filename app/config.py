import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    pinecone_api_key: str = "mock-key"
    pinecone_index_name: str = "sourcingplus-visual-search"
    use_mock_embeddings: bool = True
    openai_api_key: str = "mock-key"
    database_url: str = "sqlite:///./sourcingplus.db"

    # Allow loading from a .env file if it exists
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
