from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from . import token_updater
from .config import Config, config
from . import main

__plugin_meta__ = PluginMetadata(
    name="cloudnet_bot",
    description="",
    usage="",
)
