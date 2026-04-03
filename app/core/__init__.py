from app.core.config import Config


def get_config() -> Config:
    return Config()

# 모듈 단위로 미리 주입
config: Config = get_config()
