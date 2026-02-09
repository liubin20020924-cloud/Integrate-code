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

    def search_note(self, query, limit=30):
        """
        搜索Trilium笔记

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            tuple: (success: bool, results: list, message: str)
        """
        try:
            if not query:
                return False, [], '请输入搜索关键词'

            # 尝试使用 trilium-py 模块
            try:
                from trilium_py.client import ETAPI

                server_url = self.server_url.rstrip('/')
                token = self.token

                # 如果没有token，尝试使用密码登录
                if not token:
                    logger.info("使用密码模式连接Trilium")
                    ea = ETAPI(server_url)
                    # 注意：这里需要从外部获取密码
                    token = None
                else:
                    ea = ETAPI(server_url, token)

                # 执行搜索
                # 注意：根据 trilium-py 文档，limit 只有在使用 orderBy 时才有效
                # 对于简单搜索，我们获取所有结果后再截取
                results = ea.search_note(search=query)

                # 格式化结果并限制数量
                formatted_results = []
                if 'results' in results:
                    for i, result in enumerate(results['results']):
                        if i >= limit:
                            break
                        formatted_results.append({
                            'noteId': result.get('noteId', ''),
                            'title': result.get('title', ''),
                            'type': result.get('type', 'text'),
                            'dateModified': result.get('utcDateModified', '')
                        })

                return True, formatted_results, '搜索成功'

            except ImportError:
                logger.warning("trilium-py 模块未安装，回退到基础API模式")
                # 回退方案：直接调用Trilium API
                return self._search_via_api(query, limit)

        except Exception as e:
            logger.error(f"搜索Trilium笔记异常: {e}")
            return False, [], f'搜索失败: {str(e)}'

    def _search_via_api(self, query, limit=30):
        """
        通过基础API搜索（备用方案）

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            tuple: (success: bool, results: list, message: str)
        """
        try:
            # 构建搜索URL
            search_url = f"{self.server_url.rstrip('/')}/api/notes/search"
            
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            params = {
                'search': query,
                'limit': limit
            }

            response = self.session.get(search_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                return True, results, '搜索成功'
            else:
                return False, [], f'搜索失败: {response.status_code}'

        except Exception as e:
            logger.error(f"基础API搜索失败: {e}")
            return False, [], f'搜索失败: {str(e)}'

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

            # 尝试使用 trilium-py 模块
            try:
                from trilium_py.client import ETAPI

                server_url = self.server_url.rstrip('/')
                token = self.token

                # 如果没有token，尝试使用密码登录
                if not token:
                    logger.info("使用密码模式连接Trilium")
                    ea = ETAPI(server_url)
                    # 注意：这里需要从外部获取密码
                    token = None
                else:
                    ea = ETAPI(server_url, token)

                # 从URL中提取noteId
                # URL格式可能是: http://server/#root/noteId 或 /#root/noteId
                # 注意：noteId可能是克隆笔记，格式为 parent_child
                note_id = note_url.split('#root/')[-1].split('?')[0] if '#root/' in note_url else None

                logger.info(f"尝试获取Trilium笔记内容: note_id={note_id}, url={note_url}")

                # 检查是否是克隆笔记（包含路径分隔符）
                is_branch_note = '/' in note_id if note_id else False
                if is_branch_note:
                    logger.info(f"检测到克隆笔记，原始noteId: {note_id}")
                    # 对于克隆笔记，使用子noteId
                    child_note_id = note_id.split('/')[-1]
                    logger.info(f"使用子noteId: {child_note_id}")
                    note_id = child_note_id

                if note_id:
                    try:
                        # 使用ETAPI获取笔记内容
                        logger.info(f"通过ETAPI获取笔记内容: note_id={note_id}")

                        # 获取笔记内容
                        content = ea.get_note_content(note_id)

                        if content:
                            logger.info(f"成功获取Trilium笔记内容，内容长度: {len(content)}")
                            print(f"[DEBUG] 原始内容前200字符: {content[:200]}")

                            # 清理内容
                            content = self._clean_content(content)
                            print(f"[DEBUG] 清理后内容前200字符: {content[:200]}")
                            print(f"[DEBUG] 清理后内容长度: {len(content)}")
                            return True, content, '获取成功'
                        elif response.status_code == 401:
                            logger.warning("HTTP访问失败，尝试使用get_note方法")
                            # 回退到 get_note 方法
                            note_info = ea.get_note(note_id)
                            logger.info(f"Trilium笔记信息: {note_info}")

                            # 检查返回的数据结构
                            if isinstance(note_info, dict):
                                note_type = note_info.get('type', 'text')
                                logger.info(f"笔记类型: {note_type}")

                                # 对于笔记本（book）类型，获取第一个子笔记的内容
                                if note_type == 'book':
                                    child_note_ids = note_info.get('childNoteIds', [])
                                    if child_note_ids:
                                        # 获取第一个子笔记的内容
                                        first_child_id = child_note_ids[0]
                                        logger.info(f"检测到笔记本类型，获取第一个子笔记: {first_child_id}")

                                        # 递归获取子笔记内容
                                        child_note_info = ea.get_note(first_child_id)
                                        logger.info(f"子笔记信息: {child_note_info}")

                                        if isinstance(child_note_info, dict):
                                            # 尝试从子笔记获取内容
                                            content = None
                                            for field in ['content', 'noteContent', 'text', 'contentText']:
                                                if field in child_note_info and child_note_info[field]:
                                                    content = child_note_info[field]
                                                    logger.info(f"从子笔记字段 '{field}' 获取到内容")
                                                    break

                                            if content:
                                                logger.info(f"成功获取Trilium笔记本内容，内容长度: {len(content) if content else 0}")
                                                return True, content, '获取成功'
                                            else:
                                                logger.warning(f"子笔记中未找到内容字段，子笔记信息: {child_note_info}")
                                                return False, f'笔记本格式不支持: {str(child_note_info)[:100]}', '无法解析笔记内容'
                                    else:
                                        logger.warning("笔记本类型笔记但没有子笔记")
                                        return False, '笔记本为空', '笔记本为空，没有可显示的内容'
                                else:
                                    # 对于普通笔记，尝试从不同的字段获取内容
                                    content = None

                                    # 尝试多个可能的字段名
                                    for field in ['content', 'noteContent', 'text', 'contentText']:
                                        if field in note_info and note_info[field]:
                                            content = note_info[field]
                                            logger.info(f"从字段 '{field}' 获取到内容")
                                            break

                                    if content:
                                        logger.info(f"成功获取Trilium笔记内容，内容长度: {len(content) if content else 0}")
                                        return True, content, '获取成功'
                                    else:
                                        # 如果没有内容字段，返回整个笔记信息
                                        logger.warning(f"笔记信息中未找到内容字段，笔记信息: {note_info}")
                                        return False, f'笔记格式不支持: {str(note_info)[:100]}', '无法解析笔记内容'
                            else:
                                logger.error(f"get_note 返回了非字典类型: {type(note_info)}")
                                return False, '', f'笔记数据格式错误: {str(note_info)[:100]}'
                        elif response.status_code == 404:
                            logger.error(f"笔记不存在: {note_id}")
                            return False, '', '笔记不存在'
                        else:
                            logger.error(f"HTTP返回错误: {response.status_code}")
                            return False, '', f'访问失败: HTTP {response.status_code}'

                    except Exception as api_error:
                        logger.error(f"获取笔记内容失败: {api_error}", exc_info=True)
                        return False, '', f'获取笔记失败: {str(api_error)}'
                else:
                    logger.error(f"无法从URL中解析noteId: {note_url}")
                    return False, '', '无法解析笔记ID'

            except ImportError:
                logger.warning("trilium-py 模块未安装，回退到基础API模式")
                # 回退方案：直接获取
                return self._get_content_via_api(note_url)

        except Exception as e:
            logger.error(f"获取Trilium内容异常: {e}", exc_info=True)
            return False, '', f'获取内容失败: {str(e)}'

    def _get_content_via_api(self, note_url):
        """
        通过直接HTTP请求获取笔记渲染内容（备用方案）

        Args:
            note_url: 笔记的 URL

        Returns:
            tuple: (success: bool, content: str, message: str)
        """
        try:
            # 从URL中提取noteId
            note_id = note_url.split('#root/')[-1].split('?')[0] if '#root/' in note_url else None

            if not note_id:
                return False, '', '无法解析笔记ID'

            # 构建Trilium笔记的HTTP访问URL（直接获取渲染后的HTML）
            # 这种方法可以直接获取笔记的渲染内容，无需通过API
            trilium_note_url = f"{self.server_url.rstrip('/')}/#/root/{note_id}"

            # 添加认证头
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            logger.info(f"通过HTTP直接访问Trilium笔记: {trilium_note_url}")

            # 调用 Trilium 的HTTP接口获取渲染后的HTML
            response = self.session.get(trilium_note_url, headers=headers, timeout=10)

            if response.status_code == 200:
                content = response.text
                logger.info(f"成功获取Trilium笔记渲染内容，内容长度: {len(content)}")

                # 清理内容
                content = self._clean_content(content)
                return True, content, '获取成功'
            elif response.status_code == 401:
                return False, '', 'Trilium 认证失败，请检查 Token 配置'
            elif response.status_code == 404:
                return False, '', '笔记不存在'
            else:
                logger.error(f"Trilium HTTP返回错误: {response.status_code}")
                return False, '', f'Trilium 服务返回错误: {response.status_code}'

        except requests.exceptions.Timeout:
            logger.error(f"获取 Trilium 内容超时: {note_url}")
            return False, '', '请求超时，请稍后重试'
        except requests.exceptions.ConnectionError:
            logger.error(f"连接 Trilium 服务失败: {note_url}")
            return False, '', '无法连接到 Trilium 服务'
        except Exception as e:
            logger.error(f"获取 Trilium 内容异常: {e}", exc_info=True)
            return False, '', f'获取内容失败: {str(e)}'

    def _clean_content(self, content):
        """
        清理和规范化 HTML 内容

        Args:
            content: 原始 HTML 内容

        Returns:
            str: 清理后的 HTML 内容
        """
        import re

        if not content:
            return content

        # 调试：检查是否有外部引用
        has_kb_ref = '/kb/' in content
        has_svg_ref = '.svg' in content or '<svg' in content
        has_img_ref = '<img' in content
        print(f"[DEBUG] 清理前检查: has_kb_ref={has_kb_ref}, has_svg_ref={has_svg_ref}, has_img_ref={has_img_ref}")
        logger.info(f"清理前检查: has_kb_ref={has_kb_ref}, has_svg_ref={has_svg_ref}, has_img_ref={has_img_ref}")

        # 移除外部CSS链接引用（这些会导致404错误）
        # 移除 <link> 标签引用的CSS文件
        content = re.sub(r'<link[^>]*>', '', content)

        # 移除外部CSS样式表
        # 移除 <style> 标签中引用的外部CSS
        content = re.sub(r"@import\s+url\(['\"]?[^'\"]+['\"]?\)", '', content, flags=re.IGNORECASE)
        content = re.sub(r"@import\s+url\([^)]+\)", '', content, flags=re.IGNORECASE)

        # 移除内联样式表中的外部URL引用（相对路径和绝对路径）
        # 处理 style 标签中的 background-image、src 等属性
        content = re.sub(r"url\(['\"]?https?://[^'\"]+['\"]?\)", '', content, flags=re.IGNORECASE)
        content = re.sub(r"url\(['\"]?/kb/[^'\"]*['\"]?\)", '', content, flags=re.IGNORECASE)
        content = re.sub(r"url\(['\"]?\.\./[^'\"]*['\"]?\)", '', content, flags=re.IGNORECASE)

        # 移除或替换图片标签中的外部资源引用
        # 移除所有包含外部路径的 img 标签
        content = re.sub(r'<img[^>]*src=["\']/?kb/[^"\']*["\'][^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<img[^>]*src=["\']?\.\./[^"\']*["\'][^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<img[^>]*src=["\'][^"\"]*\.(png|jpg|jpeg|gif|svg|ico|webp)["\'][^>]*>', '', content, flags=re.IGNORECASE)

        # 移除 SVG 标签
        content = re.sub(r'<svg[^>]*>.*?</svg>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除 script 标签（避免外部脚本加载问题）
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除 iframe 标签（避免外部资源加载）
        content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除所有 meta 标签（除了 charset 和 viewport）
        content = re.sub(r'<meta(?![^>]*(charset|viewport))[^>]*>', '', content, flags=re.IGNORECASE)

        # 再次检查清理后的内容
        has_kb_ref_after = '/kb/' in content
        has_svg_ref_after = '.svg' in content or '<svg' in content
        has_img_ref_after = '<img' in content
        print(f"[DEBUG] 清理后检查: has_kb_ref={has_kb_ref_after}, has_svg_ref={has_svg_ref_after}, has_img_ref={has_img_ref_after}")
        logger.info(f"清理后检查: has_kb_ref={has_kb_ref_after}, has_svg_ref={has_svg_ref_after}, has_img_ref={has_img_ref_after}")

        # 确保HTML标签正确闭合
        # 添加基本的内联样式，确保基本可读性
        cleaned_html = content

        # 提取body内容（如果有）
        body_match = re.search(r'<body[^>]*>(.*?)</body>', cleaned_html, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_content = body_match.group(1)
            # 添加基础样式容器
            styled_body = f"""
                <div style="
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 100%;
                    overflow-x: auto;
                    padding: 20px;
                ">
                    {body_content}
                </div>
            """
            cleaned_html = cleaned_html.replace(body_match.group(0), styled_body)

        # 添加meta标签确保正确的字符集
        meta_tag = '<meta charset="UTF-8">'
        if '<meta' not in cleaned_html:
            cleaned_html = meta_tag + cleaned_html

        return cleaned_html

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
