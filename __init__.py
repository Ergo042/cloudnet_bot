from nonebot.plugin import PluginMetadata

from .config import config

__plugin_meta__ = PluginMetadata(
    name="cloudnet_bot",
    description="",
    usage="",
    config=config, # type: ignore  # noqa: PGH003
)


