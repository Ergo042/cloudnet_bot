"""
工具函数模块
负责配置文件更新、数据脱敏、路径处理等通用功能
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from nonebot.log import logger

# 配置文件路径（根据你的项目结构调整）
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.py")


def update_config_param(key: str, new_value: str, config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    更新配置文件中的指定参数值（适配 Python 格式的 config.py）
    :param key: 要更新的参数名（如 rest_access_key、rest_refresh_key）
    :param new_value: 新的参数值（如 Token 字符串）
    :param config_path: 配置文件路径，默认取插件根目录的 config.py
    :return: 更新成功返回 True，失败返回 False
    """
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在：{config_path}")
        return False

    try:
        # 读取配置文件内容
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 遍历并替换目标参数（保留原缩进）
        updated = False
        for i, line in enumerate(lines):
            # 去除首尾空白后判断是否匹配参数名
            stripped_line = line.strip()
            if stripped_line.startswith(f"{key} ="):
                # 提取原行的缩进（空格/制表符）
                indent = line[:len(line) - len(line.lstrip())]
                # 保留原缩进，替换参数值
                lines[i] = f"{indent}{key} = \"{new_value}\"\n"
                updated = True
                logger.info(f"已更新配置参数 {key}")
                break

        # 参数不存在则追加（适配文件整体缩进风格）
        if not updated:
            # 自动检测文件的缩进风格（优先用空格，默认4个空格）
            indent_char = " "
            indent_size = 4
            # 遍历文件找非空行，提取缩进参考
            for line in lines:
                if line.strip() and not line.strip().startswith("#"):
                    # 提取第一个有效行的缩进
                    line_indent = line[:len(line) - len(line.lstrip())]
                    if line_indent:
                        # 判断是空格还是制表符
                        if "\t" in line_indent:
                            indent_char = "\t"
                            indent_size = len(line_indent)
                        else:
                            indent_size = len(line_indent)
                    break
            # 拼接缩进后的新参数行
            new_line = f"{indent_char * indent_size}{key} = \"{new_value}\"\n"
            # 避免末尾无换行的情况，先加换行再追加
            if lines and not lines[-1].endswith("\n"):
                lines[-1] = lines[-1] + "\n"
            lines.append(new_line)
            logger.info(f"配置参数 {key} 不存在，已追加到文件末尾（缩进：{indent_size}{indent_char}）")

        # 写入修改后的内容
        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info(f"配置文件更新完成：{config_path}")
        return True

    except PermissionError:
        logger.error(f"更新配置失败：没有文件写入权限 {config_path}")
    except Exception as e:
        logger.error(f"更新配置异常：{str(e)}")

    return False


def desensitize_token(token: str, keep_head: int = 8, keep_tail: int = 4) -> str:
    """
    脱敏 Token/密钥，只保留开头和结尾部分
    :param token: 原始 Token 字符串
    :param keep_head: 保留开头字符数，默认8
    :param keep_tail: 保留结尾字符数，默认4
    :return: 脱敏后的字符串
    """
    if not isinstance(token, str) or len(token) <= keep_head + keep_tail:
        return token

    return f"{token[:keep_head]}...{token[-keep_tail:]}"


def load_env_file(env_path: str = ".env") -> Optional[Dict[str, str]]:
    """
    加载 .env 配置文件
    :param env_path: .env 文件路径
    :return: 配置字典，失败返回 None
    """
    if not os.path.exists(env_path):
        logger.warning(f".env 文件不存在：{env_path}")
        return None

    env_config = {}
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_config[key.strip()] = value.strip()

        logger.info(f"成功加载 .env 文件：{env_path}")
        return env_config

    except Exception as e:
        logger.error(f"加载 .env 文件异常：{str(e)}")
        return None


def check_file_permission(file_path: str, mode: str = "w") -> bool:
    """
    检查文件是否有指定权限（读/写）
    :param file_path: 文件路径
    :param mode: 权限类型，r=读，w=写
    :return: 有权限返回 True，无返回 False
    """
    if mode == "r":
        return os.access(file_path, os.R_OK)
    elif mode == "w":
        if os.path.exists(file_path):
            return os.access(file_path, os.W_OK)
        else:
            dir_path = os.path.dirname(file_path)
            return os.access(dir_path, os.W_OK)
    return False