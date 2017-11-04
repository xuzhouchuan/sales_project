#!/usr/bin/env python
#-*- coding:utf-8 -*-

from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Equipment, Customer, Permission
from . import api
from decorators import permission_required
from errors import bad_request
import json

@api.route('/customer/headers', methods=['GET', 'POST'])
def get_customer_headers():
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : Customer.get_ordered_headers()
            })

@api.route('/customer', methods=['GET'])
@permission_required(Permission.MODULE_PERMISSION_DICT['customer']['read'])
def get_customer():
    state = int(request.args.get('state')) if request.args.get('state') is not None else None
    customers = []
    if state is None:
        customers = Customer.query.all()
    else:
        customers = Customer.query.filter_by(state=state).all()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : {
            'headers' : Customer.get_ordered_headers(),
            'customers' : [customer.to_json() for customer in customers]
            }})


@api.route('/customer/<int:id>', methods=['GET'])
@permission_required(Permission.MODULE_PERMISSION_DICT['customer']['read'])
def get_customer_id(id):
    customer = Customer.query.get_or_404(id)
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : customer.to_json()
            })

@api.route('/customer', methods=['POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['customer']['write'])
def new_customer():
    enterprise_json = request.get_json()
    if enterprise_json is None:
        return jsonify({
                'error' : 1,
                'msg' : u'不是application/json类',
                'data' : {}
                }), 403
    print enterprise_json
    try:
        name = enterprise_json.get('name') or None #enterprise_json['name']
        capital = enterprise_json.get('register') or None
        abbr = enterprise_json.get('abbr') or None
        type = enterprise_json.get('type') or None
#ever_name = enterprise_json.get('ever_name') or None
        legal = enterprise_json.get('legal') or None
#location = enterprise_json.get('location') or None
        establish_date = enterprise_json.get('establish_date') or None
        create_user = enterprise_json.get('create_user') or None
        if create_user is None:
            create_user = g.current_user.id

        c1 = enterprise_json.get('c1') or None
        c2 = enterprise_json.get('c2') or None
        c3 = enterprise_json.get('c3') or None
        c4 = enterprise_json.get('c4') or None
        c5 = enterprise_json.get('c5') or None
        c6 = enterprise_json.get('c6') or None
        c7 = enterprise_json.get('c7') or None
        a1 = enterprise_json.get('a1') or None
        a2 = enterprise_json.get('a2') or None
        a3 = enterprise_json.get('a3') or None
        a4 = enterprise_json.get('a4') or None
        a5 = enterprise_json.get('a5') or None
        a6 = enterprise_json.get('a6') or None
        a7 = enterprise_json.get('a7') or None
        a8 = enterprise_json.get('a8') or None
        d1 = enterprise_json.get('d1') or None
        d2 = enterprise_json.get('d2') or None
        d3 = enterprise_json.get('d3') or None
        d4 = enterprise_json.get('d4') or None
        d5 = enterprise_json.get('d5') or None
        d6 = enterprise_json.get('d6') or None
        d7 = enterprise_json.get('d7') or None
#approve_user = enterprise_json.get('approve_user') or None

#a = {}
#       for item in enterprise_json:
#           print item
#           if item != 'id':
#               a[item] = enterprise_json[item]
#       accessory = json.dumps(a)
        customer = Customer(abbr, name, type, establish_date, capital, legal,
                c1, c2, c3, c4, c5, c6, c7,
                a1, a2, a3, a4, a5, a6, a7, a8,
                d1, d2, d3, d4, d5, d6, d7,
                create_user)
        try:
            db.session.add(customer)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            return jsonify({
                    'error' : 3,
                    'msg' : 'database not support ',
                    'data' : {}
                    }), 404
    except Exception, e:
        print e
        return jsonify({
                'error' : 2,
                'msg' : 'fields not complete ',
                'data' : {}
                }), 404
    
    return jsonify({
            'error' : 0,
            'msg' : u'添加首营企业成功',
            'data' : customer.to_json()
            })

@api.route('/customer/<int:id>', methods=['PUT'])
@permission_required(Permission.MODULE_PERMISSION_DICT['customer']['approve'])
def edit_costomer(id):
    customer = Customer.query.get_or_404(id)
    enterprise_json = request.get_json()
    if enterprise_json is None:
        return jsonify({
                'error' : 1,
                'msg' : u'不是application/json类',
                'data' : {}
                }), 403
    print enterprise_json
#if enterprise_json.get('name'):
#        customer.name = enterprise_json['name']
#    if enterprise_json.get('register_capital'):
#        customer.register_capital = enterprise_json['register_capital']
#    if enterprise_json.get('abbr'):
#        customer.abbr = enterprise_json['abbr']
#    if enterprise_json.get('type'):
#        customer.type = enterprise_json['type']
#    if enterprise_json.get('ever_name'):
#        customer.ever_name = enterprise_json['ever_name']
#    if enterprise_json.get('legal_representor'):
#        customer.legal_representor = enterprise_json['legal_representor']
#    if enterprise_json.get('location'):
#        customer.location = enterprise_json['location']
#    if enterprise_json.get('establish_date'):
#        customer.establish_date = enterprise_json['establish_date']
#a = {}
#    for item in enterprise_json:
#       if item != 'id' and item != 'create_user' and item != 'approve_user':
#           a[item] = enterprise_json[item]
#   customer.accessory = json.dumps(a)
    try:
        name = enterprise_json.get('name') or None #enterprise_json['name']
        capital = enterprise_json.get('register') or None
        abbr = enterprise_json.get('abbr') or None
        type = enterprise_json.get('type') or None
        legal = enterprise_json.get('legal') or None
        establish_date = enterprise_json.get('establish_date') or None
        c1 = enterprise_json.get('c1') or None
        c2 = enterprise_json.get('c2') or None
        c3 = enterprise_json.get('c3') or None
        c4 = enterprise_json.get('c4') or None
        c5 = enterprise_json.get('c5') or None
        c6 = enterprise_json.get('c6') or None
        c7 = enterprise_json.get('c7') or None
        a1 = enterprise_json.get('a1') or None
        a2 = enterprise_json.get('a2') or None
        a3 = enterprise_json.get('a3') or None
        a4 = enterprise_json.get('a4') or None
        a5 = enterprise_json.get('a5') or None
        a6 = enterprise_json.get('a6') or None
        a7 = enterprise_json.get('a7') or None
        a8 = enterprise_json.get('a8') or None
        d1 = enterprise_json.get('d1') or None
        d2 = enterprise_json.get('d2') or None
        d3 = enterprise_json.get('d3') or None
        d4 = enterprise_json.get('d4') or None
        d5 = enterprise_json.get('d5') or None
        d6 = enterprise_json.get('d6') or None
        d7 = enterprise_json.get('d7') or None
        try:
            db.session.commit()
        except Exception as e:
            print e
            return jsonify({
                    'error' : 2,
                    'msg' : 'database commit error',
                    'data' : {},
                }), 404
    except Exception as e:
        print e
        return jsonify({
                'error' : 1,
                'msg' : 'parse error',
                'data' : {},
            }), 404
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : customer.to_json()
        })

@api.route('/customer/<int:id>', methods=['DELETE'])
@permission_required(Permission.MODULE_PERMISSION_DICT['customer']['approve'])
def delete_customer(id):
    customer = Customer.query.get(id)
    if customer is None:
        return bad_request('no such a customer')
    db.session.delete(customer)
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : 'delete customer successful',
            'data' : {}
            })

@api.route('/customer/approve/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MODULE_PERMISSION_DICT['customer']['approve'])
def approve_new_customer(id):
    c = Customer.query.get(id)
    if c is None:
        return bad_request('no such a customer')

    try:
        if request:
            equip_json = request.get_json()
            if equip_json is not None and equip_json.get('approve_user') is not None:
                c.approve_user = equip_json['approve_user']
        if c.approve_user is None:
            c.approve_user = g.current_user.id
    except Exception, e:
        print e
        return jsonify({
                'error' : 1,
                'msg' : 'approve_user cannot get',
                'data' : ''
                })

    c.state = 1
    db.session.commit()
    return jsonify({
            'error' : 0,
            'msg' : '',
            'data' : c.to_json()
            })
