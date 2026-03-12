from typing import Optional

from nonebot import get_plugin_config
from pydantic import BaseModel, field_validator


# ===============================配置模型===============================
class Config(BaseModel):
    """Plugin Config Here"""
    CLOUDNET_API_URL: str
    CLOUDNET_USERNAME: str
    CLOUDNET_PASSWORD: str
    CLOUDNET_ACCESS_TOKEN: Optional[str] = None
    CLOUDNET_REFRESH_TOKEN: Optional[str] = None
    CLOUDNET_REFRESH_TIME: Optional[int] = None  # token刷新时间，单位秒
        # MySQL 配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 45678
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DB_CLOUDNET: str = "cloudnet"  # cloudnet 数据所在数据库
    MYSQL_DB_NONEBOT: str = "nonebot"    # bot 数据所在数据库 (qq绑定等)

# ===============================创建实例===============================
config = get_plugin_config(Config)
