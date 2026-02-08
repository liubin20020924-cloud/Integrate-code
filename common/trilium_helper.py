"""
Trilium 笔记服务辅助模块
提供 Trilium API 调用功能
"""
import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class TriliumHelper:
    """Trilium 笔记服务辅助类"""

    def __init__(self, server_url=None, token=None):
        """
        初始化 Trilium 辅助类

        Args:
            server_url: Trilium 服务器地址
            token: Trilium 认证令牌
        """
        self.server_url = server_url or ''
        self.token = token or ''
        self.session = requests.Session()

    def get_note_content(self, note_url):
        """
        获取笔记内容

        Args:
            note_url: 笔记的 URL

        Returns:
            tuple: (success: bool, content: str, message: str)
        """
        try:
            # 构建完整的 API URL
            if not note_url.startswith('http'):
                if self.server_url:
                    base_url = self.server_url.rstrip('/')
                    note_url = f"{base_url}/{note_url}"
                else:
                    return False, '', 'Trilium 服务未配置'

            # 添加认证头
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            # 调用 Trilium API
            response = self.session.get(note_url, headers=headers, timeout=10)

            if response.status_code == 200:
                content = response.text

                # 简单的内容清理
                content = self._clean_content(content)

                return True, content, '获取成功'
            elif response.status_code == 401:
                return False, '', 'Trilium 认证失败，请检查 Token 配置'
            elif response.status_code == 404:
                return False, '', '笔记不存在'
            else:
                return False, '', f'Trilium 服务返回错误: {response.status_code}'

        except requests.exceptions.Timeout:
            logger.error(f"获取 Trilium 内容超时: {note_url}")
            return False, '', '请求超时，请稍后重试'
        except requests.exceptions.ConnectionError:
            logger.error(f"连接 Trilium 服务失败: {note_url}")
            return False, '', '无法连接到 Trilium 服务'
        except Exception as e:
            logger.error(f"获取 Trilium 内容异常: {e}")
            return False, '', f'获取内容失败: {str(e)}'

    def _clean_content(self, content):
        """
        清理和规范化 HTML 内容

        Args:
            content: 原始 HTML 内容

        Returns:
            str: 清理后的 HTML 内容
        """
        # 这里可以添加内容清理逻辑
        # 例如：移除不需要的标签、规范化链接等
        return content

    def check_connection(self):
        """
        检查 Trilium 服务连接

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not self.server_url:
                return False, 'Trilium 服务未配置'

            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            response = self.session.get(
                self.server_url.rstrip('/') + '/api/notes/root',
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                return True, '连接成功'
            elif response.status_code == 401:
                return False, '认证失败'
            else:
                return False, f'服务返回错误: {response.status_code}'

        except Exception as e:
            return False, f'连接失败: {str(e)}'


def get_trilium_helper(server_url=None, token=None):
    """
    获取 Trilium 辅助类实例（工厂函数）

    Args:
        server_url: Trilium 服务器地址（可选，从配置读取）
        token: Trilium 认证令牌（可选，从配置读取）

    Returns:
        TriliumHelper: Trilium 辅助类实例
    """
    try:
        # 从配置导入
        import config

        if server_url is None:
            server_url = getattr(config, 'TRILIUM_SERVER_URL', '')
        if token is None:
            token = getattr(config, 'TRILIUM_TOKEN', '')

        return TriliumHelper(server_url, token)
    except ImportError:
        logger.warning("无法导入 config 模块")
        return TriliumHelper(server_url, token)
