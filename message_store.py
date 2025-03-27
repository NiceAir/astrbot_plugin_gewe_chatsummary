import json
import os
from collections import defaultdict
from datetime import datetime
from astrbot.api import logger


class MessageStore:
    def __init__(self, filename="message_store.json", max_per_target=1000):
        self.filename = filename
        self.max_per_target = max_per_target
        self.data = defaultdict(list)

        # 如果文件存在，加载数据
        if os.path.exists(self.filename):
            self._load_from_file()

    def add_message(self, target, is_private, sender, content, timestamp=None):
        """添加新消息到存储"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        message = f"private_chat:{is_private}, timestamp:{timestamp}, sender:{sender}, content:{content}"

        # 添加到对应target的列表
        self.data[target].append(message)

        # 如果超过最大数量，移除最旧的消息
        if len(self.data[target]) > self.max_per_target:
            self.data[target] = self.data[target][-self.max_per_target:]

        # 保存到文件
        self._save_to_file()

    def get_messages(self, target, count=None):
        """获取指定target的消息，可指定数量"""
        if target not in self.data:
            return []

        messages = self.data[target]
        if count is not None and count < len(messages):
            return messages[-count:]
        return messages

    def _save_to_file(self):
        """保存数据到文件"""
        # 将defaultdict转换为普通dict
        save_data = dict(self.data)
        with open(self.filename, 'w') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

    def _load_from_file(self):
        """从文件加载数据"""
        try:
            with open(self.filename, 'r') as f:
                loaded_data = json.load(f)

            # 转换为defaultdict
            self.data = defaultdict(list, loaded_data)

            # 确保每个target不超过最大数量
            for target in self.data:
                self.data[target] = self.data[target][-self.max_per_target:]
                
        except Exception as e:
            logger.error(f"_load_from_file, err:{e}")
            return
