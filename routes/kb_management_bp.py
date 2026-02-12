"""
知识库系统路由蓝图 - 管理功能（需要管理员权限）
"""
from flask import Blueprint, request, render_template, session, jsonify
from common.unified_auth import login_required, get_current_user
from common.response import success_response, error_response, validation_error_response, server_error_response
from common.validators import validate_required
from common.logger import logger, log_exception
from common.kb_utils import fetch_record_by_id, fetch_records_with_pagination, get_total_count, fetch_all_records
from datetime import datetime

kb_management_bp = Blueprint('kb_management', __name__, url_prefix='/kb/MGMT')





@kb_management_bp.route('/')
@login_required(roles=['admin'])
def management():
    """管理页面"""
    user = get_current_user()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        records, total_count = fetch_records_with_pagination(page, per_page)
        
        total_pages = (total_count + per_page - 1) // per_page
        showing_start = (page - 1) * per_page + 1
        showing_end = min(page * per_page, total_count)
        
        return render_template('kb/management.html', records=records,
                             total_count=total_count,
                             showing_count=showing_end - showing_start + 1 if records else 0,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             showing_start=showing_start,
                             showing_end=showing_end,
                             current_user=user,
                             debug_mode=False)
    except Exception as e:
        logger.error(f"加载知识库管理页面失败: {e}")
        return render_template('kb/management.html', records=[],
                             error=str(e),
                             total_count=0,
                             page=1,
                             per_page=20,
                             total_pages=1)


@kb_management_bp.route('/api/add', methods=['POST'])
@login_required(roles=['admin'])
def add_record():
    """添加记录
    
    添加新的知识库记录
    ---
    tags:
      - 知识库-管理
    security:
      - CookieAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - KB_Number
            - KB_Name
          properties:
            KB_Number:
              type: integer
              description: 知识库编号
            KB_Name:
              type: string
              description: 知识库名称
            KB_link:
              type: string
              description: 知识库链接
    responses:
      200:
        description: 添加成功
        schema:
          $ref: '#/definitions/SuccessResponse'
      400:
        description: 参数错误或记录已存在
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        data = request.get_json()

        # 验证必填字段
        is_valid, errors = validate_required(data, ['KB_Number', 'KB_Name'])
        if not is_valid:
            return validation_error_response(errors)

        existing = fetch_record_by_id(data['KB_Number'])
        if existing:
            return error_response(f"编号 {data['KB_Number']} 已存在", 400)

        from common.database_context import db_connection
        with db_connection('kb') as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO `KB-info` (KB_Number, KB_Name, KB_link) VALUES (%s, %s, %s)"
            cursor.execute(sql, (data['KB_Number'], data['KB_Name'], data.get('KB_link', '')))
            conn.commit()
            affected_rows = cursor.rowcount

        if affected_rows > 0:
            logger.info(f"添加知识库记录 {data['KB_Number']} 成功")
            return success_response(message='记录添加成功', data={'id': data['KB_Number']})
        else:
            return error_response('添加记录失败', 500)
    except Exception as e:
        log_exception(logger, "添加知识库记录失败")
        return server_error_response(f"添加记录时发生错误: {str(e)}")


@kb_management_bp.route('/api/trilium/search', methods=['GET'])
@login_required(roles=['admin'])
def search_trilium_notes():
    """搜索Trilium笔记
    
    搜索Trilium笔记，用于快速添加到知识库
    ---
    tags:
      - 知识库-管理
    parameters:
      - in: query
        name: query
        type: string
        required: true
        description: 搜索关键词
      - in: query
        name: limit
        type: integer
        default: 20
        description: 返回结果数量限制
    responses:
      200:
        description: 搜索成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            results:
              type: array
              items:
                type: object
                properties:
                  noteId:
                    type: string
                    description: 笔记ID
                  title:
                    type: string
                    description: 笔记标题
                  type:
                    type: string
                    description: 笔记类型
                  dateModified:
                    type: string
                    description: 修改时间
    """
    try:
        query = request.args.get('query', '').strip()
        limit = request.args.get('limit', 20, type=int)

        if not query:
            return error_response('搜索关键词不能为空', 400)

        # 使用TriliumHelper搜索笔记
        from common.trilium_helper import get_trilium_helper
        trilium = get_trilium_helper()

        success, results, message = trilium.search_note(query, limit)

        if success:
            return success_response(
                message='搜索成功',
                data={'results': results}
            )
        else:
            return error_response(message, 500)

    except Exception as e:
        log_exception(logger, "搜索Trilium笔记失败")
        return server_error_response(f"搜索失败: {str(e)}")


@kb_management_bp.route('/api/trilium/note/<note_id>', methods=['GET'])
@login_required(roles=['admin'])
def get_trilium_note():
    """获取Trilium笔记信息
    
    获取指定Trilium笔记的详细信息
    ---
    tags:
      - 知识库-管理
    parameters:
      - in: path
        name: note_id
        type: string
        required: true
        description: 笔记ID
    responses:
      200:
        description: 获取成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            note:
              type: object
              properties:
                noteId:
                  type: string
                title:
                  type: string
                content:
                  type: string
    """
    try:
        note_id = request.args.get('note_id', '').strip()

        if not note_id:
            return error_response('笔记ID不能为空', 400)

        # 使用TriliumHelper获取笔记内容
        from common.trilium_helper import get_trilium_helper
        trilium = get_trilium_helper()

        # 构建笔记URL
        note_url = f"#root/{note_id}"
        success, content, message = trilium.get_note_content(note_url)

        if success:
            # 获取笔记基本信息
            try:
                from trilium_py.client import ETAPI
                import config

                server_url = config.TRILIUM_SERVER_URL.rstrip('/')
                token = config.TRILIUM_TOKEN

                if token:
                    ea = ETAPI(server_url, token)
                    note_info = ea.get_note(note_id)

                    note_data = {
                        'noteId': note_id,
                        'title': note_info.get('title', ''),
                        'content': content,
                        'type': note_info.get('type', 'text'),
                        'dateModified': note_info.get('utcDateModified', '')
                    }
                else:
                    note_data = {
                        'noteId': note_id,
                        'title': note_id,
                        'content': content
                    }
            except ImportError:
                note_data = {
                    'noteId': note_id,
                    'title': note_id,
                    'content': content
                }
            except Exception as e:
                logger.warning(f"获取笔记元数据失败: {e}")
                note_data = {
                    'noteId': note_id,
                    'title': note_id,
                    'content': content
                }

            return success_response(
                message='获取成功',
                data={'note': note_data}
            )
        else:
            return error_response(message, 404)

    except Exception as e:
        log_exception(logger, "获取Trilium笔记失败")
        return server_error_response(f"获取笔记失败: {str(e)}")


@kb_management_bp.route('/api/update/<int:record_id>', methods=['PUT'])
@login_required(roles=['admin'])
def update_record(record_id):
    """更新记录"""
    try:
        data = request.get_json()
        existing = fetch_record_by_id(record_id)
        if not existing:
            return error_response(f"记录 {record_id} 不存在", 404)
        
        from common.database_context import db_connection
        with db_connection('kb') as conn:
            cursor = conn.cursor()
            sql = "UPDATE `KB-info` SET KB_Name = %s, KB_link = %s WHERE KB_Number = %s"
            cursor.execute(sql, (data.get('KB_Name', existing['KB_Name']), data.get('KB_link', existing['KB_link']), record_id))
            conn.commit()
            affected_rows = cursor.rowcount
        
        if affected_rows > 0:
            logger.info(f"更新知识库记录 {record_id} 成功")
            return success_response(message='记录更新成功')
        else:
            return error_response('更新记录失败', 500)
    except Exception as e:
        log_exception(logger, "更新知识库记录失败")
        return server_error_response(f"更新记录时发生错误: {str(e)}")


@kb_management_bp.route('/api/delete/<int:record_id>', methods=['DELETE'])
@login_required(roles=['admin'])
def delete_record(record_id):
    """删除记录"""
    try:
        existing = fetch_record_by_id(record_id)
        if not existing:
            return error_response(f"记录 {record_id} 不存在", 404)
        
        from common.database_context import db_connection
        with db_connection('kb') as conn:
            cursor = conn.cursor()
            sql = "DELETE FROM `KB-info` WHERE KB_Number = %s"
            cursor.execute(sql, (record_id,))
            conn.commit()
            affected_rows = cursor.rowcount
        
        if affected_rows > 0:
            logger.info(f"删除知识库记录 {record_id} 成功")
            return success_response(message='记录删除成功')
        else:
            return error_response('删除记录失败', 500)
    except Exception as e:
        log_exception(logger, "删除知识库记录失败")
        return server_error_response(f"删除记录时发生错误: {str(e)}")


@kb_management_bp.route('/api/batch-delete', methods=['POST'])
@login_required(roles=['admin'])
def batch_delete_records():
    """批量删除记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])

        if not ids:
            return error_response('没有要删除的记录', 400)

        from common.kb_utils import get_kb_db_connection
        connection = get_kb_db_connection()
        if connection is None:
            return server_error_response('数据库连接失败')

        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(ids))
            sql = f"DELETE FROM `KB-info` WHERE KB_Number IN ({placeholders})"
            cursor.execute(sql, ids)
            affected_rows = cursor.rowcount
            connection.commit()

        connection.close()

        logger.info(f"批量删除知识库记录完成: {affected_rows} 条")
        return success_response(
            message=f'成功删除 {affected_rows} 条记录'
        )
    except Exception as e:
        log_exception(logger, "批量删除知识库记录失败")
        return server_error_response(f"批量删除记录时发生错误: {str(e)}")


@kb_management_bp.route('/api/export', methods=['GET'])
@login_required(roles=['admin'])
def export_data():
    """导出所有数据"""
    try:
        records = fetch_all_records()
        logger.info(f"导出知识库数据: {len(records)} 条记录")
        return success_response(
            message='数据导出成功',
            data={
                'data': records,
                'count': len(records)
            }
        )
    except Exception as e:
        log_exception(logger, "导出知识库数据失败")
        return server_error_response(f"导出数据时发生错误: {str(e)}")


@kb_management_bp.route('/api/records', methods=['GET'])
@login_required(roles=['admin'])
def get_paginated_records():
    """获取分页记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_name = request.args.get('search', '').strip()
        
        if not page or page < 1:
            page = 1
        if not per_page or per_page < 1 or per_page > 100:
            per_page = 20
        
        from common.kb_utils import fetch_records_by_name_with_pagination
        if search_name:
            records, total_count = fetch_records_by_name_with_pagination(search_name, page, per_page)
        else:
            records, total_count = fetch_records_with_pagination(page, per_page)
        
        total_pages = (total_count + per_page - 1) // per_page
        showing_start = (page - 1) * per_page + 1
        showing_end = min(page * per_page, total_count)
        
        response_data = {
            'records': records,
            'total_count': total_count,
            'showing_count': showing_end - showing_start + 1 if records else 0,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'showing_start': showing_start,
            'showing_end': showing_end
        }
        return jsonify({
            'success': True,
            'message': '查询成功',
            **response_data
        })
    except Exception as e:
        log_exception(logger, "获取知识库分页记录失败")
        return server_error_response(
            message=f"获取记录失败: {str(e)}"
        )


@kb_management_bp.route('/api/system-status', methods=['GET'])
@login_required(roles=['admin'])
def system_status():
    """获取系统状态"""
    try:
        total_records = get_total_count()
        
        from common.database_context import db_connection
        user_count = 0
        latest_record_time = None
        database_connected = True
        
        with db_connection('kb') as conn:
            try:
                import pymysql
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT COUNT(*) as count FROM `users`")
                user_count = cursor.fetchone()['count']
                
                if total_records > 0:
                    cursor.execute("SELECT MAX(KB_UpdateTime) as max_time FROM `KB-info`")
                    result = cursor.fetchone()
                    if result and result.get('max_time'):
                        latest_record_time = result['max_time'].strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"获取知识库系统状态失败: {e}")
                database_connected = False
        
        system_health = 'database_error' if not database_connected else ('connected_no_data' if total_records == 0 else 'healthy')
        
        return success_response(
            data={
                'system_health': system_health,
                'database_connected': database_connected,
                'total_records': total_records,
                'user_count': user_count,
                'latest_record_time': latest_record_time,
                'current_user': get_current_user(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            message='查询成功'
        )
    except Exception as e:
        log_exception(logger, "获取知识库系统状态失败")
        return server_error_response(message=f"获取系统状态失败: {str(e)}")
