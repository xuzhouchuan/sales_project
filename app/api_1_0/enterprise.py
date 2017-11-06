#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Equipment, Enterprise, Permission
from . import api
from decorators import permission_required
from errors import bad_request
import json
import datetime

@api.route('/enterprise/headers', methods=['GET', 'POST'])
def get_enterprise_headers():
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : Enterprise.get_ordered_headers()
            })

@api.route('/enterprise', methods=['GET'])
@permission_required(Permission.MODULE_PERMISSION_DICT['enterprise']['read'])
def get_enterprises():
    state = int(request.args.get('state')) if request.args.get('state') is not None else None
    enterprises = []
    if state is None:
        enterprises = Enterprise.query.all()
    else:
        enterprises = Enterprise.query.filter_by(state=state).all()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : {
            'headers' : Enterprise.get_ordered_headers(),
            'enterprises' : [enterprise.to_json() for enterprise in enterprises]
            }})


@api.route('/enterprise/<int:id>', methods=['GET'])
@permission_required(Permission.MODULE_PERMISSION_DICT['enterprise']['read'])
def get_enterprise(id):
    enterprise = Enterprise.query.get_or_404(id)
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : enterprise.to_json()
            })

@api.route('/enterprise', methods=['POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['enterprise']['write'])
def new_enterprise():
    request_json = request.get_json()
    if request_json is None:
        return jsonify({
                'error' : 1,
                'msg' : u'不是application/json类',
                'data' : {}
                }), 403
    try:
        enterprise = Enterprise.json2obj(request_json)
        enterprise.create_user_id = g.current_user.id
        enterprise.create_date = datetime.datetime.now()
        enterprise.last_modify_user_id = g.current_user.id
        enterprise.last_modify_date = datetime.datetime.now()
        db.session.add(enterprise)
        db.session.commit()
    except Exception, e:
        print e
        return jsonify({
                'error' : 2,
                'msg' : 'fields error or add database error',
                'data' : {}
                }), 404
    
    return jsonify({
            'error' : 0,
            'msg' : u'添加首营企业成功',
            'data' : enterprise.to_json()
            })

@api.route('/enterprise/<int:id>', methods=['PUT'])
@permission_required(Permission.MODULE_PERMISSION_DICT['enterprise']['approve'])
def edit_enterprise(id):
    enterprise = Enterprise.query.get_or_404(id)
    enterprise_json = request.get_json()
    if enterprise_json is None:
        return jsonify({
                'error' : 1,
                'msg' : u'不是application/json类',
                'data' : {}
                }), 403
    enterprise.json_modify_obj(enterprise_json)
    enterprise.last_modify_user_id = g.current_user.id
    enterprise.last_modify_date = datetime.datetime.now()
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : enterprise.to_json()
        })

@api.route('/enterprise/<int:id>', methods=['DELETE'])
@permission_required(Permission.MODULE_PERMISSION_DICT['enterprise']['approve'])
def delete_enterprise(id):
    #TODO 权限判断，结合state判断
    #审批通过的普通用户不能删除
    #待审批或审批失败的原用户可以删除
    #put 也是如此(能修改的只能是已经审批通过的或者审批打回重写的，审批失败的不能修改，但是可以删除)
    #equipment也是如此
    enterprise = Enterprise.query.get(id)
    if enterprise is None:
        return bad_request('no such a enterprise')
    db.session.delete(enterprise)
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : 'delete enterprise successful',
            'data' : {}
            })

@api.route('/enterprise/approve/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['enterprise']['approve'])
def approve_new_enterprise(id):
    c = Enterprise.query.get(id)
    if c is None:
        return bad_request(u'首营企业不存在')
    c.approve_user_id = g.current_user.id
    c.approve_date = datetime.datetime.now()
    #TODO approve_state设计
    c.approve_state = 0
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : c.to_json()
            })
