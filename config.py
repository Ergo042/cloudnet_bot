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
    CLOUDENT_REFRESH_TIME: Optional[int] = None  # token刷新时间，单位秒

    @field_validator("CLOUDNET_USERNAME")
    def validate_username(cls, value: str) -> str:  # noqa: N805
        if not value:
            raise ValueError("CLOUDNET_USERNAME不能为空")
        return value

    @field_validator("CLOUDNET_PASSWORD")
    def validate_password(cls, value: str) -> str:  # noqa: N805
        if not value:
            raise ValueError("CLOUDNET_PASSWORD不能为空")
        return value

# ===============================创建实例===============================
config = get_plugin_config(Config)
