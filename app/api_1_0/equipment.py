#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Equipment, Permission, Store
from . import api
from decorators import permission_required
from errors import bad_request
import json
import datetime


@api.route('/equipment/headers', methods=['GET', 'POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['read'])
def get_equipment_headers():
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : Equipment.get_ordered_headers()
            })

@api.route('/equipment', methods=['GET'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['read'])
def get_equipments():
    state = int(request.args.get('approve_state')) if request.args.get('approve_state') is not None else None
    equips = []
    if state is None:
        equips = Equipment.query.all()
    else:
        equips = Equipment.query.filter_by(approve_state=state).all()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : {
            'headers': Equipment.get_ordered_headers(),
            'equipments': [equip.to_json() for equip in equips]
            }
            })
        

@api.route('/equipment/<int:id>', methods=['GET'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['read'])
def get_equipment(id):
    equip = Equipment.query.get_or_404(id)
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : equip.to_json()
            })


@api.route('/equipment', methods=['POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['write'])
def new_equipment():
    equip_json = request.get_json()
    if equip_json is None:
        return jsonify({
                'error' : 1,
                'msg' : u'不是application/json类',
                'data' : {}
                }), 403
    print equip_json
    equip = None
    try:
        equip = Equipment.json2obj(equip_json)
        equip.create_user_id = g.current_user.id 
        equip.create_date = datetime.datetime.now()
        equip.last_modify_user_id = g.current_user.id
        equip.last_modify_date = datetime.datetime.now()
        db.session.add(equip)
        db.session.commit()
    except Exception, e:
        print e
        return jsonify({
                'error' : 2,
                'msg' : 'fields not complete or error:stdid|info|abbr|spec|model|producer|accessory',
                'data' : {}
                }), 403
    
    return jsonify({
            'error' : 0,
            'msg' : u'添加首营设备成功',
            'data' : equip.to_json()
            })

@api.route('/equipment/<int:id>', methods=['PUT'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['approve'])
def edit_equipment(id):
    equip = Equipment.query.get_or_404(id)
    request_json = request.get_json()
    if request_json is None:
        return jsonify({
                'error' : 1,
                'msg' : u'不是application/json类',
                'data' : {}
                }), 403
    print request_json

    equip.json_modify_obj(request_json)
    equip.last_modify_user_id = g.current_user.id
    equip.last_modify_date = datetime.datetime.now()
    db.session.commit()

    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : equip.to_json()
            })
 
#这里可以反复调用，不是很合理，tofix
@api.route('/equipment/approve/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['approve'])
def approve_new_equipment(id):
    #TODO approve_state判断
    equip = Equipment.query.get(id)
    if equip is None:
        return bad_request('no such a equipment')
    equip.approve_user_id = g.current_user.id
    equip.approve_date = datetime.datetime.now()
    #TODO approve_state设计
    equip.approve_state = 0
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : equip.to_json()
            })

@api.route('/equipment/<int:id>', methods=['DELETE'])
@permission_required(Permission.MODULE_PERMISSION_DICT['equipment']['approve'])
def delete_equipment(id):
    equip = Equipment.query.get(id)
    if equip is None:
        return bad_request('no such a equipment')
    db.session.delete(equip)
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : 'delete equipment successful',
            'data' : {}
            })

#TODO get_store api
@api.route('/equipment/get_store/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['store']['write'])
def get_store_equipoment(id):
    equip = Equipment.query.get(id)
    if equip is None:
        return bad_request('no such a equipment')
    print "get store equipment id", id, len(equip.stores)
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : [store.to_json() for store in equip.stores]
            })
