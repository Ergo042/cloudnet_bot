import base64
from typing import Any, Optional

import aiohttp
from nonebot import get_driver, require
from nonebot.log import logger

from .config import Config, config

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

"""
api接口，获取token
"""
async def get_auth_token() -> bool:
    """用 Basic Auth 获取 CloudNet Token"""
    # 1. 生成 Basic Auth 头
    auth_str = f"{config.CLOUDNET_USERNAME}:{config.CLOUDNET_PASSWORD}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode().strip()
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}

    # 2. 发送 POST 请求
    try:
        async with aiohttp.ClientSession() as session, session.post(
            f"{config.CLOUDNET_API_URL}/auth",
            headers=headers,
            json={},
            timeout=10
        ) as resp:
            # 3. 处理响应
            if resp.status != 200:  # noqa: PLR2004
                logger.error(f"获取Token失败：{resp.status} {await resp.text()}")
                return False

            token_data = await resp.json()
            access_token = token_data.get("accessToken", {}).get("token")
            refresh_token = token_data.get("refreshToken", {}).get("token")
            Config.CLOUDNET_ACCESS_TOKEN = access_token
            Config.CLOUDNET_REFRESH_TOKEN = refresh_token
            return True
    except aiohttp.ClientError as e:
        logger.error(f"获取Token时发生网络异常：{e},请检查CloudNet是否正常运行")
        return False
    except ValueError as e:
        logger.error(f"解析Token响应时发生异常：{e}")
        return False

"""
api接口，确认token是否有效
"""
async def check_token_validity() -> bool:
    """检查当前 Access Token 是否有效"""
    if not config.CLOUDNET_ACCESS_TOKEN:
        logger.warning("没有 Access Token，无法验证")
        return False

    headers = {"Authorization": f"Bearer {config.CLOUDNET_ACCESS_TOKEN}"}
    async with aiohttp.ClientSession() as session, session.get(
        f"{config.CLOUDNET_API_URL}/auth/verify",
        headers=headers,
        timeout=10
    ) as resp:
        if resp.status == 200:  # noqa: PLR2004
            return True
        logger.warning(f"Access Token 无效：{resp.status} {await resp.text()}")
        return False

"""
api接口，刷新token
"""
async def refresh_auth_token() -> bool:
    """用 Refresh Token 刷新 CloudNet Token"""
    if not config.CLOUDNET_REFRESH_TOKEN:
        logger.warning("没有 Refresh Token，无法刷新")
        return False

    headers = {"Authorization": f"Bearer {config.CLOUDNET_REFRESH_TOKEN}", "Content-Type": "application/json"}  # noqa: E501
    async with aiohttp.ClientSession() as session, session.post(
        f"{config.CLOUDNET_API_URL}/auth/refresh",
        headers=headers,
        json={},
        timeout=10
    ) as resp:
        if resp.status != 200:  # noqa: PLR2004
            logger.error(f"刷新Token失败：{resp.status} {await resp.text()}")
            return False

        token_data = await resp.json()
        access_token = token_data.get("accessToken", {}).get("token")
        refresh_token = token_data.get("refreshToken", {}).get("token")
        Config.CLOUDNET_ACCESS_TOKEN = access_token
        Config.CLOUDNET_REFRESH_TOKEN = refresh_token
        return True

"""
定时任务，每隔一定时间检查并刷新Token
"""
@scheduler.scheduled_job("interval", seconds=config.CLOUDENT_REFRESH_TIME or 300)
async def scheduled_token_refresh() -> None:
    """定时检查并刷新 CloudNet Token,失败则重新获取"""
    if not await check_token_validity():
        logger.info("Access Token 无效，尝试刷新...")
        if not await refresh_auth_token():
            logger.warning("刷新失败，尝试重新获取...")
            await get_auth_token()

"""
插件启动时获取一次Token
"""
driver = get_driver() # 初始化钩子函数
@driver.on_startup
async def on_startup() -> None:
    """插件启动时获取一次 CloudNet Token"""
    if not await get_auth_token():
        logger.error("插件启动时获取Token失败，请检查配置")
    else:
        logger.info("成功获取Token")

logger.info("CloudNet Bot Token Updater 已加载")
