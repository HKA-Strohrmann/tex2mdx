from arxiv.config import Settings as BaseSettings

class Settings (BaseSettings):
    CONVERT_PATH: str = ':8000/process-full-corpus'
    LOG_PATH: str = 'out.log'
    DATA_LOG_PATH: str = 'times.csv'

settings = Settings()