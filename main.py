import datetime

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.params import Arg, CommandArg
from nonebot.rule import Rule, is_type, to_me
from nonebot.typing import T_State

from .config import Config
from .utils import api, parse_service_data
from .utils.resolve import tasks_data
from .utils.tools import update_config_param
from nonebot import require
from .MySQL_tools import bind_qq_uuid, init_db_tables

# 服务器启动时初始化数据库
from nonebot import get_driver

driver = get_driver()
@driver.on_startup
async def _():
    await init_db_tables()

require("nonebot_plugin_htmlkit")

from nonebot_plugin_htmlkit import html_to_pic, md_to_pic, template_to_pic, text_to_pic

# ========================帮助指令========================
help_cmd = on_command(
    cmd="cloudnet帮助",
    aliases={"云服务器帮助", "服务器帮助", "cn帮助", "help", "帮助", "菜单"},
    priority=11,
    block=True,
)

@help_cmd.handle()
async def handle_help(event: MessageEvent):
    """CloudNet 服务器管理插件帮助"""
    help_msg = """
🎮 CloudNet 管理助手
━━━━━━━━━━━━━━━━━━
📚 帮助入口：cloudnet帮助 / 帮助 / help / 菜单

📌 信息查询
1) 获取服务器信息
    指令：查询 / 查看服务器状态
    说明：查看服务名称、状态、CPU、内存、在线人数等

2) 获取在线人数
    指令：在线人数 / 查看在线人数

3) 获取注册人数
    指令：注册人数 / 查看注册人数

📌 服务器管理
4) 创建服务器
    指令：创建服务器 / 新建服务器 / 启动新服务器
    说明：按提示输入任务编号完成创建

5) 删除服务器
    指令：删除服务器 [服务器ID] / 移除服务器 [服务器ID] / 销毁服务器 [服务器ID]

6) 生命周期操作
    启动：启动 [服务器ID]
    重启：重启 [服务器ID]
    停止：关闭 [服务器ID]

🧪 示例
• 获取服务器信息
• 创建服务器
• 启动服务器 Lobby-2
• 重启服务器 Lobby-2
• 停止服务器 Lobby-2
• 删除服务器 Lobby-2

💡 使用提示
• 服务器ID可先通过「获取服务器信息」查询
• 指令支持别名，中文空格不敏感
• 若调用失败，请检查 CloudNet 服务与网络连接
━━━━━━━━━━━━━━━━━━
    """.strip()
    await help_cmd.finish(MessageSegment.text(help_msg))
# ========================默认回复========================
# 定义兜底指令（优先级最低，确保最后触发）
default_reply = on_command(
    cmd="",  # 空命令，匹配所有未被其他指令捕获的消息
    priority=999,  # 优先级设为999（最低），确保其他命令先匹配
    block=True     # 触发后阻断后续逻辑，避免重复回复
)

@default_reply.handle()
async def handle_default_reply(
    event: MessageEvent,
):
    """无匹配指令时的兜底回复逻辑"""
    # 1. 过滤空消息/纯表情/纯空格（避免无效回复）
    msg_text = event.get_message().extract_plain_text()
    if not msg_text.strip():
        return  # 不回复空消息或纯表情等无意义内容
    
    # 2. 友好提示 + 引导使用帮助指令
    default_msg = f"""
🤔 暂未识别到该指令：「{msg_text.strip()}」

💡 你可以尝试以下操作：
✅ 发送「cloudnet帮助」「帮助」或「help」查看所有可用指令
✅ 检查指令是否输入正确（支持别名：如「更新token」=「刷新token」）
✅ 常用指令示例：
   • 更新token —— 更新CloudNet认证Token
   • 获取服务器信息 —— 查看所有服务器状态
   • 启动服务器 Lobby-2 —— 启动指定服务器

    """.strip()
    
    # 3. 发送兜底回复（适配QQ消息格式）
    await default_reply.finish(MessageSegment.text(default_msg))
# ========================功能指令========================

# 获取服务器信息命令
get_services_cmd = on_command(
    cmd="获取服务器信息",
    aliases={"查询", "查看服务器状态"},
    priority=60,
    block=True
)

@get_services_cmd.handle()
async def handle_get_services(event: MessageEvent):
    await get_services_cmd.send(MessageSegment.text("🔍 正在获取服务器信息..."))

    try:
        # 1. 调用API获取服务器数据
        services_result = await api.list_cloudnet_services()

        # 2. 基础校验：返回空/非列表直接失败
        if not isinstance(services_result, list):
            fail_msg = (
                "❌ 获取服务器信息失败！\n"
                "请检查：\n"
                "1. API地址/用户名密码是否正确\n"
                "2. CloudNet 服务是否运行\n"
                "3. 网络是否通畅"
            )
            await get_services_cmd.finish(MessageSegment.text(fail_msg))

        # 3. 解析并格式化服务器信息
        services_info = parse_service_data(services_result)

        # 4. 消息格式化（简洁且QQ显示正常）
        service_cards = []
        for idx, info in enumerate(services_info, 1):
            card = f"""
服务器 {idx}
📛 服务名称：{info['服务名称']}
📌 服务类型：{info['服务类型']}
🔧 服务模版：{info['服务模版']}
📍 绑定地址：{info['绑定地址']}
🕒 创建时间：
{info['创建时间']}
🟢 运行状态：{info['运行状态']}
📊 CPU使用率：{info['CPU 使用率']}
📈 内存使用：
{info['内存使用']}
👥 在线人数：{info['在线人数']}
🎯 服务版本：{info['服务版本']}
───────────────"""
            service_cards.append(card)
        
        # 最终消息拼接
        final_msg = f"""🎉 服务器信息获取成功！
    📋 共检测到 {len(services_info)} 个服务器节点：
    {''.join(service_cards)}

    ✅ 数据来源：CloudNet API
    🕙 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        # 5. 结束会话
        await get_services_cmd.finish(MessageSegment.text(final_msg))

    except FinishedException:
        pass  # 正常结束，不处理
    except Exception as e:
        logger.error(f"获取服务器信息异常：{str(e)}", exc_info=True)
        await get_services_cmd.finish(
            MessageSegment.text(f"❌ 获取出错：{str(e)}\n请查看后台日志")
        )

# 创建服务器命令
create_service_cmd = on_command(
    cmd="创建服务器",
    aliases={"新建服务器", "启动新服务器"},
    priority=15,
    block=True
)

@create_service_cmd.handle()
async def handle_create_service(event: MessageEvent,state: T_State):
    try: 
        # 1.尝试获取服务器task列表
        tasks = await api.list_tasks()
        if not isinstance(tasks, list) or not tasks:
            await create_service_cmd.finish(
                MessageSegment.text("❌ 获取服务器任务失败，无法创建服务器！")
            )
        # 2. 提取任务名称列表
        state["task_names"] = tasks_data(tasks)  # 存储任务列表到状态，供后续步骤使用
        # 3. 给任务编号并发送任务列表给用户，提示输入任务编号
        task_msg = "请选择服务器任务（输入编号）：\n" + "\n".join(
            [f"{idx + 1}. {name}" for idx, name in enumerate(state["task_names"])]
        )
        await create_service_cmd.send(MessageSegment.text(task_msg))
        # 4. 等待用户输入任务编号
    except FinishedException:
        pass  # 正常结束，不处理
    except Exception as e:
        logger.error(f"创建服务器异常：{str(e)}", exc_info=True)
        await create_service_cmd.finish(
            MessageSegment.text(f"❌ 创建服务器出错：{str(e)}\n请查看后台日志")
        )
@create_service_cmd.got("task_index", prompt="请输入任务编号：") 
async def handle_task_index(state: T_State, task_index: Message = Arg()):
    try:
        index = int(task_index.extract_plain_text().strip()) - 1
        if index < 0 or index >= len(state["task_names"]):
            await create_service_cmd.finish(
                MessageSegment.text("❌ 编号无效，请重新执行命令并输入正确编号！")
            )
        selected_task = state["task_names"][index]
        # 5. 调用API创建服务器
        create_result = await api.create_service(selected_task)
        if create_result:
            await create_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器创建成功！使用任务：{selected_task}")
            )
        else:
            await create_service_cmd.finish(
                MessageSegment.text("❌ 服务创建失败，请查看后台日志！")
            )
    except ValueError:
        await create_service_cmd.finish(
            MessageSegment.text("❌ 输入无效，请输入数字编号！")
        )

# 删除服务的命令
delete_service_cmd = on_command(
    cmd="删除服务器",
    aliases={"移除服务器", "销毁服务器"},
    priority=15,
    block=True
)

@delete_service_cmd.handle()
async def handle_delete_service(CommandArg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = CommandArg.extract_plain_text().strip()
        if not service_id:
            await delete_service_cmd.finish(
                MessageSegment.text("❌ 请提供要删除的服务器唯一ID！")
            )
        # 2. 调用API执行删除操作
        result = await api.delete_service(service_id)
        if result:
            await delete_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 删除成功！")
            )
        else:
            await delete_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 删除失败，请检查服务器是否存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

#服务器的生命周期操作
start_service_cmd = on_command(
    cmd="启动服务器",
    aliases={"开启服务器", "运行服务器","启动"},
    priority=15,
    block=True
)
@start_service_cmd.handle()
async def handle_start_service(CommandArg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = CommandArg.extract_plain_text().strip()
        if not service_id:
            await start_service_cmd.finish(
                MessageSegment.text("❌ 请提供要启动的服务器！")
            )
        # 2. 调用API执行启动操作
        result = await api.life_cycle_action(service_id, "start")
        if result:
            await start_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 启动成功！")
            )
        else:
            await start_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 启动失败，请检查服务器是否已存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

restart_service_cmd = on_command(
    cmd="重启服务器",
    aliases={"重启", "重新启动服务器"},
    priority=15,
    block=True
)
@restart_service_cmd.handle()
async def handle_restart_service(arg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = arg.extract_plain_text().strip()
        if not service_id:
            await restart_service_cmd.finish(
                MessageSegment.text("❌ 请提供要重启的服务器！")
            )
        # 2. 调用API执行重启操作
        result = await api.life_cycle_action(service_id, "restart")
        if result:
            await restart_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 重启成功！")
            )
        else:
            await restart_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 重启失败，请检查服务器是否已存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

stop_service_cmd = on_command(
    cmd="停止服务器",
    aliases={"关闭服务器", "停止运行服务器", "关闭"},
    priority=15,
    block=True
)
@stop_service_cmd.handle()
async def handle_stop_service(CommandArg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = CommandArg.extract_plain_text().strip()
        if not service_id:
            await stop_service_cmd.finish(
                MessageSegment.text("❌ 请提供要停止的服务器！")
            )
        # 2. 调用API执行停止操作
        result = await api.life_cycle_action(service_id, "stop")
        if result:
            await stop_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 停止成功！")
            )
        else:
            await stop_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 停止失败，请检查服务器是否已存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

get_online_players_cmd = on_command(
    cmd="获取在线人数",
    aliases={"在线人数", "查看在线人数"},
    priority=15,
    block=True
)
@get_online_players_cmd.handle()
async def handle_get_online_players(CommandArg: Message = CommandArg()):
    try:
        result = await api.get_online_players()
        if result is not None:
            await get_online_players_cmd.finish(
                MessageSegment.text(f"🎉 当前在线人数：{result}人")
            )
        else:
            await get_online_players_cmd.finish(
                MessageSegment.text("❌ 获取在线人数失败，请检查API连接！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

get_registered_players_cmd = on_command(
    cmd="获取注册人数",
    aliases={"查询注册人数", "注册人数"},
    priority=15,
    block=True
)
@get_registered_players_cmd.handle()
async def handle_get_registered_players(CommandArg: Message = CommandArg()):
    try:
        result = await api.get_num_of_players()
        if result is not None:
            await get_registered_players_cmd.finish(
                MessageSegment.text(f"🎉 当前注册人数：{result}人")
            )
        else:
            await get_registered_players_cmd.finish(
                MessageSegment.text("❌ 获取注册人数失败，请检查API连接！")
            )
    except FinishedException:
        pass  # 正常结束，不处理




# 绑定发言用户qq号与游戏name的命令
bind_player_cmd = on_command(
    cmd="绑定账号",
    aliases={"绑定游戏名", "bind"},
    priority=15,
    block=True
)

@bind_player_cmd.handle()
async def handle_bind_player(event: MessageEvent, args: Message = CommandArg()):
    # 1. 获取用户QQ号
    qq_id = event.get_user_id()
    
    # 2. 获取用户输入的游戏名
    game_name = args.extract_plain_text().strip()
    
    if not game_name:
        await bind_player_cmd.finish(
            MessageSegment.text("❌ 请输入游戏名！\n格式：绑定账号 <游戏名>")
        )
    
    await bind_player_cmd.send(MessageSegment.text(f"🔍 正在查找玩家 {game_name}..."))
    
    # 3. 调用绑定函数
    try:
        success = await bind_qq_uuid(qq_id, game_name)
        if success:
            await bind_player_cmd.finish(
                MessageSegment.text(f"🎉 绑定成功！\nQQ：{qq_id}\n游戏名：{game_name}")
            )
        else:
            await bind_player_cmd.finish(
                MessageSegment.text("❌ 绑定失败！\n可能原因：\n1. 玩家不存在 (请确认大小写)\n2. 数据库连接异常")
            )
    except Exception as e:
        logger.error(f"绑定账号异常：{str(e)}", exc_info=True)
        await bind_player_cmd.finish(
            MessageSegment.text(f"❌ 系统错误：{str(e)}")
        )