from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import event_message_type, EventMessageType
from astrbot.api.message_components import *
from astrbot.api import logger
from astrbot.api.event.filter import permission_type, PermissionType
import os, json, datetime, time

from data.plugins.astrbot_plugin_gewe_chatsummary.message_store import MessageStore


def with_project_path(file: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file)


@register("gewe_chatssummary", "NiceAir", "微信版总结消息", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.message_store = MessageStore(filename=with_project_path("message_store.json"))

    @filter.command("总结消息")
    async def summary(self, event: AstrMessageEvent, count: int = None):
        """触发消息总结，命令加空格，后面跟获取聊天记录的数量即可（例如“ /消息总结 20 ”）"""
        if not event.is_admin():
            event.stop_event()
            return

        # 检查是否传入了要总结的聊天记录数量，未传入则返回错误，并终止事件传播
        if count is None:
            yield event.plain_result(
                "未传入要总结的聊天记录数量\n请按照「 /消息总结 [要总结的聊天记录数量]\n例如「 /消息总结 114」~")
            event.stop_event()
            return

        massage_lines = self.message_store.get_messages(event.unified_msg_origin, count)

        msg = "\n".join(massage_lines)

        # 调用LLM生成总结内容
        llm_response = await self.context.get_using_provider().text_chat(
            prompt=self.load_prompt(),
            contexts=[
                {"role": "user", "content": str(msg)}
            ],
        )

        # 输出LLM最终总结内容，发送总结消息
        yield event.plain_result(llm_response.completion_text)

    @event_message_type(EventMessageType.ALL, priority=3)
    async def on_all_message(self, event: AstrMessageEvent):
        content = event.message_str,
        sender = event.get_sender_name() if event.get_sender_name() != "" else event.get_sender_id()
        msg_type = event.get_message_type()
        target = event.unified_msg_origin
        is_private = event.get_group_id() == ""

        messages = event.get_messages()
        message = None
        if len(messages) != 0:
            message = messages[0]
        if msg_type == 1 and content.startswith("总结消息"):
            return
        if msg_type == 49 and message is not None:  # 很多，其中就有引用
            if isinstance(message, Reply):
                content = message.message_str

        self.message_store.add_message(target, is_private, sender, content)

    def load_prompt(self):
        with open(os.path.join('data', 'config', 'astrbot_plugin_gewe_chatsummary_config.json'), 'r',
                  encoding='utf-8-sig') as a:
            config = json.load(a)
            prompt_str = config.get('prompt', {})
            return str(prompt_str.replace('\\n', '\n'))
