import aiohttp
import base64
import json
from typing import Optional, Dict, Any, List
from nonebot.log import logger
from ..config import config

BASE_URL = config.CLOUDNET_API_URL  # 例如 http://localhost:8080/api/v3


def _build_auth_headers() -> Optional[Dict[str, str]]:
    access_token = config.CLOUDNET_ACCESS_TOKEN
    if not access_token:
        logger.error("❌ CLOUDNET_ACCESS_TOKEN 为空")
        return None
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


"""
服务处理部分
"""
# 获取服务列表的函数
async def list_cloudnet_services() -> Optional[List[Dict[str, Any]]]:
    """
    用获取到的 Bearer Token 查询服务
    """
    headers = _build_auth_headers()
    if not headers:
        return None
    url = f"{BASE_URL}/service"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    services = await response.json()
                    if isinstance(services["services"], list):
                        logger.info(f"✅ 获取到 {len(services['services'])} 个服务")
                        return services["services"]
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询服务失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询服务异常：{e}")
    return None

async def create_service(service_name: str):
    """
    创建新服务的函数
    """
    headers = _build_auth_headers()
    if not headers:
        return None
    url = f"{BASE_URL}/service/create/taskName"
    payload = {
        "taskName": service_name,
    }

    # 发送post请求
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                if response.status == 200 or response.status == 201:
                    logger.info(f"✅ 服务 '{service_name}' 创建成功")
                    return await response.json()
                else:
                    logger.error(f"❌ 创建服务失败：HTTP {response.status} - {await response.text()}")
    except Exception as e:
        logger.error(f"❌ 创建服务异常：{e}")

async def delete_service(service_id: str) -> bool:
    """
    删除服务的函数
    """
    headers = _build_auth_headers()
    if not headers:
        return False
    url = f"{BASE_URL}/service/{service_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers, timeout=10) as response:
                if response.status == 204:
                    logger.info(f"✅ 服务 '{service_id}' 删除成功")
                    return True
                else:
                    logger.error(f"❌ 删除服务失败：HTTP {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ 删除服务异常：{e}")
        return False

async def get_template_list() -> Optional[List[str]]:
    """
    获取可用模板列表
    """
    headers = _build_auth_headers()
    if not headers:
        return None
    url = f"{BASE_URL}/templateStorage/local/templates"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    templates = await response.json()
                    if isinstance(templates["templates"], list):
                        logger.info(f"✅ 获取到 {len(templates['templates'])} 个模板")
                        return [t["name"] for t in templates["templates"]]
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询模板失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询模板异常：{e}")

async def list_tasks() -> Optional[List[Dict[str, Any]]]:
    """
    获取任务列表
    """
    headers = _build_auth_headers()
    if not headers:
        return None
    url = f"{BASE_URL}/task"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    tasks = await response.json()
                    if isinstance(tasks["tasks"], list):
                        logger.info(f"✅ 获取到 {len(tasks['tasks'])} 个任务")
                        return tasks["tasks"]
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询任务失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询任务异常：{e}")
    return None

async def life_cycle_action(
    service_id: str,
    action: str,
) -> bool:
    """
    对服务执行生命周期操作（start/stop/restart）
    """
    if action not in {"start", "stop", "restart"}:
        logger.error(f"❌ 无效的生命周期操作：{action}")
        return False
    headers = _build_auth_headers()
    if not headers:
        return False
    url = f"{BASE_URL}/service/{service_id}/lifecycle"
    target = {"target": action}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, params=target, timeout=10) as response:
                if response.status == 204:
                    logger.info(f"✅ 服务 {service_id} 执行 {action} 成功")
                    return True
                elif response.status == 404:
                    logger.error(f"❌ 服务 {service_id} 不存在，无法执行 {action}")
                else:
                    logger.error(f"❌ 服务 {service_id} 执行 {action} 失败：HTTP {response.status} - {await response.text()}")
    except Exception as e:
        logger.error(f"❌ 服务 {service_id} 执行 {action} 异常：{e}")
    return False

async def get_num_of_players() -> Optional[Dict[str, int]]:
    """
    获取注册人数
    """
    headers = _build_auth_headers()
    if not headers:
        return None
    url = f"{BASE_URL}/player/registeredCount"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    props = await response.json()
                    registered_count = props.get("registeredCount", 0)
                    logger.info(f"✅ 获取到注册人数：{registered_count}")
                    return registered_count
                else:
                    logger.error(f"❌ 获取注册人数失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 获取注册人数异常：{e}")
    return None

async def get_online_players() -> Optional[Dict[str, int]]:
    """
    获取在线人数
    """
    headers = _build_auth_headers()
    if not headers:
        return None
    url = f"{BASE_URL}/player/onlineCount"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    props = await response.json()
                    online_count = props.get("onlineCount", 0)
                    logger.info(f"✅ 获取到在线人数：{online_count}")
                    return online_count
                else:
                    logger.error(f"❌ 获取在线人数失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 获取在线人数异常：{e}")
    return None