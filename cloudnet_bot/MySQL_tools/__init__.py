import json
import pymysql
from typing import Optional, Dict, Any
from nonebot import logger
from ..config import config
from .basic_func import execute_query, execute_update

async def init_db_tables():
    """初始化数据库表"""
    # 检查并创建数据库
    try:
        connection = pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DB_NONEBOT}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            logger.info(f"✅ 数据库 {config.MYSQL_DB_NONEBOT} 检查/创建成功")
        connection.close()
    except Exception as e:
        logger.error(f"❌ 数据库 {config.MYSQL_DB_NONEBOT} 创建/检查失败: {e}")

    query = """
    CREATE TABLE IF NOT EXISTS qq_bind (
        qq_id VARCHAR(20) PRIMARY KEY,
        game_uuid VARCHAR(64) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    if execute_update(query, db_name=config.MYSQL_DB_NONEBOT):
        logger.info("✅ 数据库表 qq_bind 检查/创建成功")
    else:
        logger.error("❌ 数据库表 qq_bind 创建失败")

'''
查询玩家数据的函数并处理,玩家数据示例:
"Name" (即UUID)	"Document" (JSON字符串)
'''
async def get_player_data(player_name: str) -> Optional[Dict[str, Any]]:
    """
    查询玩家数据
    :param player_name: 玩家游戏名 (或 UUID)
    :return: 包含 uuid, name, lastLoginTime, firstLoginTime 的字典, 未找到返回 None
    """
    # 假设表名为 cloudnet_cloud_players
    # Name 列是 UUID, Document 是 JSON 字符串包含 "name": "..."
    
    # 1. 尝试模糊查询 JSON (匹配 "name": "player_name")
    search_json_part = f'%"name": "{player_name}"%'
    query = "SELECT Name, Document FROM cloudnet_cloud_players WHERE Document LIKE %s LIMIT 1"
    
    result = execute_query(query, (search_json_part,), db_name=config.MYSQL_DB_CLOUDNET)
    
    # 2. 如果没搜到，尝试是否本身输入的即为 UUID (匹配 Name 列)
    if not result:
        query_uuid = "SELECT Name, Document FROM cloudnet_cloud_players WHERE Name = %s LIMIT 1"
        result = execute_query(query_uuid, (player_name,), db_name=config.MYSQL_DB_CLOUDNET)
    
    if result and len(result) > 0:
        try:
            uuid = result[0]['Name']
            document_str = result[0]['Document']
            document = json.loads(document_str)
            
            return {
                "uuid": uuid,
                "name": document.get("name"),
                "lastLoginTimeMillis": document.get("lastLoginTimeMillis"),
                "firstLoginTimeMillis": document.get("firstLoginTimeMillis"),
                "clean_document": document
            }
        except json.JSONDecodeError as e:
            logger.error(f"❌ 解析玩家数据 JSON 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 处理玩家数据失败: {e}")
            return None
            
    return None

async def bind_qq_uuid(qq_id: str, name_or_uuid: str) -> bool:
    """
    绑定 QQ 号和游戏 UUID
    :param qq_id: QQ号
    :param name_or_uuid: 游戏名或者UUID (用于查询确认 UUID)
    :return: 绑定是否成功
    """
    # 先查询玩家数据的 UUID，确保玩家存在
    player_data = await get_player_data(name_or_uuid)
    if not player_data or not player_data.get('uuid'):
        logger.warning(f"⚠️ 绑定失败: 未找到玩家 {name_or_uuid}")
        return False
    
    game_uuid = player_data['uuid']
    real_name = player_data['name']

    # 使用 INSERT INTO ... ON DUPLICATE KEY UPDATE 语法
    query = """
    INSERT INTO qq_bind (qq_id, game_uuid) 
    VALUES (%s, %s) 
    ON DUPLICATE KEY UPDATE game_uuid = VALUES(game_uuid)
    """
    if execute_update(query, (qq_id, game_uuid), db_name=config.MYSQL_DB_NONEBOT):
        logger.info(f"✅ 绑定成功: QQ {qq_id} -> {real_name} ({game_uuid})")
        return True
    return False

async def get_bound_uuid(qq_id: str) -> Optional[str]:
    """获取 QQ 号绑定的游戏 UUID"""
    query = "SELECT game_uuid FROM qq_bind WHERE qq_id = %s"
    result = execute_query(query, (qq_id,), db_name=config.MYSQL_DB_NONEBOT)
    if result and len(result) > 0:
        return result[0]['game_uuid']
    return None

'''
{"name": "Ergo", "properties": {}, "lastLoginTimeMillis": 1772616215962, "firstLoginTimeMillis": 1772616215962, "lastNetworkPlayerProxyInfo": {"name": "Ergo", "xBoxId": null, "address": {"host": "0:0:0:0:0:0:0:1", "port": 34792}, "version": 774, "listener": {"host": "0.0.0.0", "port": 25565}, "uniqueId": "b8a0c272-f969-37b5-8742-f39a2f56e94f", "onlineMode": true, "networkService": {"groups": ["Global-Proxy", "Proxy"], "serviceId": {"taskName": "Proxy", "uniqueId": "4f07d99f-de3a-4f92-bc39-c3fe9513ecb8", "environment": {"name": "VELOCITY", "properties": {"isJavaProxy": true}, "defaultProcessArguments": [], "defaultServiceStartPort": 25565}, "allowedNodes": [], "nameSplitter": "-", "nodeUniqueId": "Node-1", "taskServiceId": 1, "environmentName": "VELOCITY"}}}}
json示例
'''

async def get_player_last_login(qq_id: str) -> Optional[int]:
    """
    获取 QQ 号绑定的玩家上次登录时间
    :param qq_id: QQ号
    :return: 上次登录时间戳 (毫秒) or None
    """
    # 1. 获取QQ绑定的UUID
    game_uuid = await get_bound_uuid(qq_id)
    if not game_uuid:
        logger.warning(f"⚠️ QQ {qq_id} 未绑定任何游戏UUID")
        return None
    
    # 2. 查询玩家数据
    # get_player_data 可以接受 UUID 作为参数
    player_data = await get_player_data(game_uuid)
    
    if player_data and player_data.get('lastLoginTimeMillis'):
        return player_data['lastLoginTimeMillis']
    
    logger.warning(f"⚠️ 无法获取玩家 {game_uuid} 的登录时间")
    return None