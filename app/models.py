#!/usr/bin/env python
#-*- coding:utf-8 -*-

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from . import db
import json
import datetime
import os

#datetime.datetime object to string
def datetime2str(date):
    if type(date) != datetime.datetime:
        raise TypeError('use datetime2str but input is not datetime.datime object')
    return datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

#string to datetime.datetime object
def str2datetime(date_str):
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return date

#string to boolean
def str2boolean(bool_str):
    if type(bool_str) == int:
        return bool(bool_str)
    elif type(bool_str) == str or type(bool_str) == unicode:
        if bool_str.upper() == 'FALSE':
            return False
        elif bool_str.upper() == 'TRUE':
            return True
    else:
        return bool(bool_str)

#one db object to a dict(can be jsonify)
def model2json(inst, cls):
    convert = {
        datetime.datetime : datetime2str
    }
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if v is not None and type(v) in convert.keys():
            try:
                d[c.name] = convert[type(v)](v)
            except:
                d[c.name] = "Error: Failed to convert using %s" % str(convert[type(v)])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return d

#json object to a db class (cls)
#cls class
#*args, **kw, used to build a cls(*args, **kw)
def json2model(json_obj, cls, *args, **kw):
    obj = cls(*args, **kw)
    convert = {
        'INTEGER' : str2datetime,
        'BOOLEAN' : str2boolean
    }
    for c in cls.__table__.columns:
        if c.name in json_obj:
            if str(c.type) in convert.keys():
                try:
                    setattr(obj, c.name, convert[str(c.type)](json_obj[c.name])) 
                except:
                    raise TypeError("invalid type used for json2model name[{}],value[{}],type[{}]".format(c.name, json_obj[c.name], str(c.type)))
            else:
                setattr(obj, c.name, json_obj[c.name])
    return obj

def json_modify_model(json_obj, db_obj):
    headers = db_obj.__class__.get_ordered_headers()
    convert = {
        'INTEGER' : str2datetime,
        'BOOLEAN' : str2boolean
    }
    header_dict = {}
    #set for attribute
    for header in headers:
        header_dict[header[0]] = {'immutable': False}
        if len(header) > 2 and header[2] == 'immutable':
            header_dict[header[0]]['immutable'] = True
    for k, v in json_obj.iteritems():
        #can modify
        for c in db_obj.__class__.__table__.columns:
            if c.name in json_obj and header_dict[c.name]['immutable'] == False:
                if str(c.type) in convert.keys():
                    try:
                        setattr(db_obj, c.name, convert[str(c.type)](json_obj[c.name]))
                    except:
                        raise TypeError("invalid type used for json2model name[{}],value[{}],type[{}]".format(c.name, json_obj[c.name], str(c.type)))
                else:
                    setattr(db_obj, c.name, json_obj[c.name])

#Equipment/Enterprise/Customer的审批状态转移类
class ApproveState(object):
    STATES = (u'待审批', u'审批成功') 
    STATE_DICT = {}
    _index = 0
    for state in STATES:
        STATE_DICT[state] = _index
        _index += 1

    def __init__(self):
        pass

    @staticmethod
    def first_state():
        return EquipmentState.STATES[0]
    
    @staticmethod
    def next_state(state):
        if type(state) == str:
            state = unicode(state, 'utf-8')
        if state in EquipmentState.STATE_DICT.keys():
            idx = EquipmentState.STATE_DICT[state]
            if (idx + 1) == len(EquipmentState.STATES):
                return None #mean the last state 
            else:
                return EquipmentState.STATES[idx + 1]
        else:
            raise ValueError('invalid state[{}], no in state list'.format(state))

    @staticmethod
    def previous_state(state):
        if type(state) == str:
            state = unicode(state, 'utf-8')
        if state in EquipmentState.STATE_DICT.keys():
            idx = EquipmentState.STATE_DICT[state]
            if idx == 0:
                return None #mean the last state 
            else:
                return EquipmentState.STATES[idx - 1]
        else:
            raise ValueError('invalid state[{}], no in state list'.format(state))


class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True, doc=u'编号', info={'name': u'编号', 'immutable': True, 'options': None})#产品ID
    stdid = db.Column(db.String(256), doc=u'产品编号', info={'name': u'产品编号', 'immutable': False, 'options': None})#产品编号
    name = db.Column(db.String(1024), doc=u'名称', info={'name': u'名称', 'immutable': False, 'options': None})#名称
    abbr = db.Column(db.String(256), doc=u'产品简称', info={'name': u'产品简称', 'immutable': False, 'options': None})#产品简称
    english_name = db.Column(db.String(256), doc=u'英文名', info={'name': u'英文名', 'immutable': False, 'options': None})#英文名
    standard_code = db.Column(db.String(256), doc=u'医疗器械标准码', info={'name': u'医疗器械标准码', 'immutable': False, 'options':None})#医疗器械标准码
    standard_catagory = db.Column(db.String(256), doc=u'医疗器械分类', info={'name': u'医疗器械分类', 'immutable': False, 'options':None})#医疗器械分类
    spec = db.Column(db.String(256), doc=u'产品规格', info={'name':u'产品规格','immutable':False,'options':None})#产品规格
    model = db.Column(db.String(256), doc=u'产品型号', info={'name':u'产品型号','immutable':False,'options':None})#产品型号
    type = db.Column(db.String(256), doc=u'产品类型', info={'name':u'产品类型','immutable':False,'options':[u'设备',u'试剂',u'耗材']})#产品类型，可选的类型
    unit = db.Column(db.String(256), doc=u'单位', info={'name':u'单位','immutable':False,'options':None})#单位
    producer = db.Column(db.String(256), doc=u'产品厂家', info={'name':u'产品厂家','immutable':False,'options':None})#产品厂家
    certificate_expiration_date = db.Column(db.DateTime, doc=u'产品注册证到期日期', info={'name':u'产品注册证到期日期','immutable':False,'options':None})#产品注册证到期日期
    audit_material_accessories = db.Column(db.Text, doc=u'审核材料附件', info={'name':u'审核材料附件','immutable':False,'options':None})#审核材料附件
    is_cold_chain = db.Column(db.Boolean, doc=u'是否冷链', info={'name':u'是否冷链', 'immutable':False,'options':None})#是否冷链
    create_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_user = db.relationship('User', backref=db.backref('create_equipments', lazy=True), foreign_keys=[create_user_id])
    create_date = db.Column(db.DateTime, doc=u'创建日期', info={'name':u'创建日期','immutable':True,'options':None})
    last_modify_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_modify_user = db.relationship('User', backref=db.backref('modify_equipments', lazy=True), foreign_keys=[last_modify_user_id])
    last_modify_date = db.Column(db.DateTime)
    approve_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approve_user = db.relationship('User', backref=db.backref('approve_equipments', lazy=True), foreign_keys=[approve_user_id])
    approve_date = db.Column(db.DateTime)
    approve_state = db.Column(db.Integer) #当前的状态 0:正常状态， 1:需要审批状态

    def __init__(self, stdid=None, name=None, abbr=None, english_name=None, standard_code=None, standard_category=None, type=None, spec=None, model=None, unit=None, producer=None, certificate_expiration_date=None, audit_material_accessories=None, is_cold_chain=None, create_user_id=None, approve_user_id=None, modify_user_id=None, create_date=None, approve_date=None, last_modify_date=None):
        self.stdid = stdid
        self.abbr = abbr
        self.name = name
        self.english_name = english_name
        self.standard_code = standard_code
        self.standard_category = standard_category
        self.type = type
        self.spec = spec
        self.model = model
        self.unit = unit
        self.producer = producer
        self.certificate_expiration_date = certificate_expiration_date
        self.audit_material_accessories = audit_material_accessories
        self.is_cold_chain = is_cold_chain
        self.create_user_id = create_user_id
        self.approve_user_id = approve_user_id
        self.last_modify_user_id = modify_user_id
        self.ceate_date = create_date
        self.approve_date = approve_date
        self.last_modify_date = last_modify_date
        self.approve_state = 1
    
    def to_json(self):
        equipment_json = model2json(self, self.__class__)
        print self.create_user.to_json()
        equipment_json['create_user'] = self.create_user.to_json()
        if self.approve_user is not None:
            equipment_json['approve_user'] = self.approve_user.to_json()
        equipment_json['last_modify_user'] = self.last_modify_user.to_json()
        return equipment_json

    @staticmethod
    def json2obj(json_obj):
        obj = json2model(json_obj, Equipment)
        return obj
    
    def json_modify_obj(self, json_obj):
        json_modify_model(json_obj, self)
    
    @staticmethod
    def get_ordered_headers():
        return [
        ('id', u'编号', 'immutable'), #自动生成的，不能修改
        ('stdid', u'产品编号'),
        ('name', '名称'),
        ('abbr', '简称'),
        ('english_name', '英文名'),
        ('standard_code', '医疗器械标准码'),
        ('standard_category', '医疗器械分类'),
        ('spec', '规格'),
        ('model', '型号'),
        ('unit', '单位'),
        ('type', '产品类别', 'option', ['设备', '试剂', '耗材']),
        ('producer', '厂商'),
        ('certificate_expiration_date', '产品注册证到期日期'),
        ('audit_material_accessories', '审核材料附件'),
        ('is_cold_chain', '是否冷链'),
        ('create_user', '创建人', 'immutable'),
        ('create_date', '创建时间', 'immutable'),
        ('last_modify_user', '最后修改人', 'immutable'),
        ('last_modify_date', '最后修改时间', 'immutable'),
        ('approve_user', '审批人', 'immutable'),
        ('approve_date', '审批时间', 'immutable')
        ]

class Enterprise(db.Model):
    __tablename__ = 'enterprise'
    id = db.Column(db.Integer, primary_key=True)#首营企业编号
    abbr = db.Column(db.String(256))#简称
    name = db.Column(db.String(256))#名称
    attribution_location = db.Column(db.String(256))#归属地
    state = db.Column(db.String(256))#状态
    medical_instrument_business_scope = db.Column(db.String(1024))#医疗器械经营范围
    category = db.Column(db.String(256))#分类
    business_scope = db.Column(db.String(1024))#经营范围
    contact_person = db.Column(db.String(256))#联系人
    contact_phone_number = db.Column(db.String(256))#电话
    contact_mobilephone_number = db.Column(db.String(256))#手机
    location = db.Column(db.String(1024))#地址
    fax_number = db.Column(db.String(256))#传真
    email = db.Column(db.String(256))#邮箱
    website = db.Column(db.String(1024))#网址
    currency_type = db.Column(db.String(256))#币种
    carriage_way = db.Column(db.String(256))#承运方式
    settle_account_way = db.Column(db.String(256))#结算方式
    settle_unit = db.Column(db.String(256))#结算单位
    create_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_user = db.relationship('User', backref=db.backref('create_enterprises', lazy=True), foreign_keys=[create_user_id])
    create_date = db.Column(db.DateTime)
    last_modify_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_modify_user = db.relationship('User', backref=db.backref('modify_enterprises', lazy=True), foreign_keys=[last_modify_user_id])
    last_modify_date = db.Column(db.DateTime)
    approve_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approve_user = db.relationship('User', backref=db.backref('approve_enterprises', lazy=True), foreign_keys=[approve_user_id])
    approve_date = db.Column(db.DateTime)
    approve_state = db.Column(db.Integer)#审批状态
    maintain_people = db.Column(db.String(1024))#维护人员
    qualification_docs = db.Column(db.String(10240))#资质文件
    remark = db.Column(db.Text)#备注
    

    def __init__(self, abbr=None, name=None, attribution_location=None, state=None, medical_instrument_business_scope=None, category=None, business_scope=None, contact_person=None, contact_phone_number=None, contact_mobilephone_number=None, location=None, fax_number=None, email=None, website=None, currency_type=None, carriage_way=None, settle_account_way=None, create_user_id=None, create_date=None, approve_user_id=None, approve_date=None, approve_state=None, last_modify_user_id=None, last_modify_date=None, qualification_docs=None, remark=None, maintain_people=None, settle_unit=None):
        self.abbr = abbr
        self.name = name
        self.attribution_location = attribution_location
        self.state = state
        self.medical_instrument_business_scope = medical_instrument_business_scope
        self.category = category
        self.business_scope = business_scope
        self.contact_person = contact_person
        self.contact_phone_number = contact_phone_number
        self.contact_mobilephone_number  = contact_mobilephone_number
        self.location = location
        self.fax_number = fax_number
        self.email = email
        self.website = website
        self.currency_type = currency_type
        self.carriage_way = carriage_way
        self.settle_account_way = settle_account_way
        self.create_user_id = create_user_id
        self.create_date = create_date
        self.approve_user_id = approve_user_id
        self.approve_date = approve_date
        self.approve_state = approve_state
        self.qualification_docs = qualification_docs
        self.remark = remark
        self.last_modify_user_id = last_modify_user_id
        self.last_modify_date = last_modify_date
        self.maintain_people = maintain_people
        self.settle_unit = settle_unit
        self.approve_state = 0
        
    def to_json(self):
        enterprise_json = model2json(self, self.__class__)
        enterprise_json['create_user'] = self.create_user.to_json()
        if self.approve_user is not None:
            enterprise_json['approve_user'] = self.approve_user.to_json()
        enterprise_json['last_modify_user'] = self.last_modify_user.to_json()
        return enterprise_json
    
    @staticmethod
    def json2obj(json_obj):
        obj = json2model(json_obj, Enterprise)
        return obj

    def json_modify_obj(self, json_obj):
        json_modify_model(json_obj, self)
        
    @staticmethod
    def get_ordered_headers():
        return [
            ('id', u'首营企业编号', 'immutable'),
            ('abbr', u'简称'),
            ('name', u'名称'),
            ('attribution_location', u'归属地'),
            ('state', u'状态'),
            ('medical_instrument_business_scope', u'医疗器械经营范围'),
            ('business_scope', u'经营范围'),
            ('category', u'分类'),
            ('contact_person', u'联系人'),
            ('contact_phone_number', u'电话'),
            ('contact_mobilephone_number', u'手机'),
            ('location', u'地址'),
            ('fax_number', u'传真'),
            ('email', u'邮箱'),
            ('website', u'网址'),
            ('currency_type', u'币种'),
            ('carriage_way', u'承运方式'),
            ('settle_account_way', u'结算方式'),
            ('settle_unit', '结算单位'),
            ('maintain_people', '维护人员'),
            ('create_user', u'创建人'),
            ('create_date', u'创建日期'),
            ('approve_user', u'审核人'),
            ('approve_date', u'审核日期'),
            ('last_modify_user', u'最后修改人'),
            ('last_modify_date', u'最后修改日期'),
            ('remark', u'备注'),
            ('qualification_docs', u'资质文件')
        ]


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)#客户系统编号
    name = db.Column(db.String(256))#客户名称
    capital = db.Column(db.String(256))#注册资金
    abbr = db.Column(db.String(256))#简称
    type = db.Column(db.String(256))#供应商类型(设备/试剂/耗材等)
#name = db.Column(db.String(256))#名
    legal = db.Column(db.String(256))#法人代表
#date = db.Column(db.String(256))#成立
#location = db.Column(db.String(256))#住所
    establish_date = db.Column(db.String(256))#成立日期
    c1 = db.Column(db.String(256))
    c2 = db.Column(db.String(256))
    c3 = db.Column(db.String(256))
    c4 = db.Column(db.String(256))
    c5 = db.Column(db.String(256))
    c6 = db.Column(db.String(256))
    c7 = db.Column(db.String(256))

    a1 = db.Column(db.String(256))
    a2 = db.Column(db.String(256))
    a3 = db.Column(db.String(256))
    a4 = db.Column(db.String(256))
    a5 = db.Column(db.String(256))
    a6 = db.Column(db.String(256))
    a7 = db.Column(db.String(256))
    a8 = db.Column(db.String(256))
    
    d1 = db.Column(db.String(256))
    d2 = db.Column(db.String(256))
    d3 = db.Column(db.String(256))
    d4 = db.Column(db.String(256))
    d5 = db.Column(db.String(256))
    d6 = db.Column(db.String(256))
    d7 = db.Column(db.String(256))
#accessory = db.Column(db.String(1024)) #json
    create_user = db.Column(db.Integer)
    approve_user = db.Column(db.Integer)
#files = db.Column(db.String(256))#资质文件名
    state = db.Column(db.Integer)

    def __init__(self, abbr, name, type, establish_date, capital, legal, c1, c2, c3, c4, c5, c6, c7, a1, a2, a3, a4, a5, a6, a7, a8, d1, d2, d3, d4, d5, d6, d7, create_user):
        self.name = name
        self.abbr = abbr
        self.type = type
#self.ever_name = ever_name
        self.legal = legal
#self.location = location
        self.establish_date = establish_date
        self.capital = capital
#self.accessory = accessory
#self.create_user = create_user
#self.approve_user = approve_user
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.c5 = c5
        self.c6 = c6
        self.c7 = c7

        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
        self.d4 = d4
        self.d5 = d5
        self.d6 = d6
        self.d7 = d7

        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.a4 = a4
        self.a5 = a5
        self.a6 = a6
        self.a7 = a7
        self.a8 = a8

        self.state = 0 
    
    def to_json(self):
        create_user_name = self.create_user
        if self.create_user is not None:
            cu = User.query.get(self.create_user)
            if cu is not None:
                create_user_name = cu.nickname or cu.username
        approve_user_name = self.approve_user
        if self.approve_user is not None:
            au = User.query.get(self.approve_user)
            if au is not None:
                approve_user_name = au.nickname or au.username

        enterprise_json = { 'id' : self.id,
            'name' : self.name,
            'capital' : self.capital,
            'abbr' : self.abbr,
            'type' : self.type,
#'ever_name' : self.ever_name,
            'legal' : self.legal,
#'location' : self.location,
            'establish_date' : self.establish_date,
            'capital' : self.capital,
            'create_user' : create_user_name,
            'approve_user' : approve_user_name,
        }
        if self.c1 is not None:
            enterprise_json['c1'] = self.c1
        if self.c2 is not None:
            enterprise_json['c2'] = self.c2
        if self.c3 is not None:
            enterprise_json['c3'] = self.c3
        if self.c4 is not None:
            enterprise_json['c4'] = self.c4
        if self.c5 is not None:
            enterprise_json['c5'] = self.c5
        if self.c6 is not None:
            enterprise_json['c6'] = self.c6
        if self.c7 is not None:
            enterprise_json['c7'] = self.c7

        if self.d1 is not None:
            enterprise_json['d1'] = self.d1
        if self.d2 is not None:
            enterprise_json['d2'] = self.d2
        if self.d3 is not None:
            enterprise_json['d3'] = self.d3
        if self.d4 is not None:
            enterprise_json['d4'] = self.d4
        if self.d5 is not None:
            enterprise_json['d5'] = self.d5
        if self.d6 is not None:
            enterprise_json['d6'] = self.d6
        if self.d7 is not None:
            enterprise_json['d7'] = self.d7

        if self.a1 is not None:
            enterprise_json['a1'] = self.a1
        if self.a2 is not None:
            enterprise_json['a2'] = self.a2
        if self.a3 is not None:
            enterprise_json['a3'] = self.a3
        if self.a4 is not None:
            enterprise_json['a4'] = self.a4
        if self.a5 is not None:
            enterprise_json['a5'] = self.a5
        if self.a6 is not None:
            enterprise_json['a6'] = self.a6
        if self.a7 is not None:
            enterprise_json['a7'] = self.a7
        if self.a8 is not None:
            enterprise_json['a8'] = self.a8
#if self.accessory:
#           obj = json.loads(self.accessory)
#           for item in obj:
#               enterprise_json[item] = obj[item]
        return enterprise_json
    
    @staticmethod
    def get_headers():
        headers = {
            'id' : u'首营企业编号(系统自动分配)',
            'name' : u'供应商名称',
            'register_capital' : u'注册资金',
            'abbr' : u'简称',
            'type' : u'供应商类型(设备/试剂/耗材等)',
            'ever_name' : u'曾用名',
            'legal_representor' : u'法人代表',
            'location' : u'住所',
            'establish_date' : u'成立日期'
        }
        return headers
    
    @staticmethod
    def get_ordered_headers():
        return [
            ('id', '客户系统编号', 'immutable'),
            ('abbr', '简称'),
            ('name', '名称'),
            ('type', '类型'),
            ('establish_date', '成立日期'),
            ('capital', '注册资金'),
            ('legal', '法人'),
            ('c1', '联系人'),
            ('c2', '手机'),
            ('c3', '电话'),
            ('c4', '传真'),
            ('c5', '地址'),
            ('c6', '邮箱'),
            ('c7', '网址'),
            ('a1', '营业执照注册号'),
            ('a2', '营业期限'),
            ('a3', '组织机构代码证号码'),
            ('a4', '有效期'),
            ('a5', '开户许可证'),
            ('a6', '医疗器械经营企业备案证书'),
            ('a7', '医疗器械经营许可证'),
            ('a8', '税务登记证'),
            ('d1', '税号'),
            ('d2', '是否一般纳税人'),
            ('d3', '开户行'),
            ('d4', '账户'),
            ('d5', '开票地址'),
            ('d6', '开票账户'),
            ('d7', '备注'),
            ('create_user', '创建人'),
            ('approve_user', '审核人'),
        ]

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_order'
    id = db.Column(db.Integer, primary_key=True)#合同编号
    sign_date = db.Column(db.Date)#签订日期
    provider_info = db.Column(db.String(256))#供应商名称、地址、电话
    billing_company = db.Column(db.String(256))#结算公司
    arrive_date = db.Column(db.DateTime)#到货日期
    get_location = db.Column(db.String(1024))#收货地点
    pay_mode = db.Column(db.String(256))#付款方式
    invoice_type = db.Column(db.String(256))#发票类型
    postage_account = db.Column(db.String(256))#运费承担方
    state = db.Column(db.Integer, default=1)#状态，1:创建，待审核, 0:已审批, -1:买货中(占位) -2:待入库 -3:入库中(partial) -4：已入库
    total_stored = db.Column(db.Integer, default=0)#是否完全入库, 0:未入库；1：部分入库；2:完全入库
    contract = db.Column(db.String(256))#合同文件名
    create_user = db.Column(db.Integer)
    approve_user = db.Column(db.Integer)

    @staticmethod
    def get_ordered_headers():
        return [('id', u'合同编号', 'immutable'),
        ('sign_date', u'签订日期'),
        ('provider_info', u'供应商名称、地址、电话'),
        ('billing_company', u'结算公司', 'option', ['天津市汇天利商贸有限公司']),
        ('arrive_date', u'到货时间'),
        ('get_location', u'收货地点'),
        ('pay_mode', u'付款方式'),
        ('invoice_type', u'发票类型'),
        ('postage_account', u'运费承担方'),
        ('state', u'当前状态', 'immutable'),
        ('total_stored', u'入库情况（未/部分/完全)', 'immutable'),
        ('contract', u'合同文件'),
        ('create_user', '创建人'),
        ('approve_user', '审核人'),
        (),
        ('id', u'入库设备编号', 'immutable', 'invisable'),
        ('equipment_id', '产品编号', 'immutable'),
        ('warranty_period', u'保修期限'),
        ('install_require', u'安装调试要求'),
        ('product_name', u'产品名称', 'immutable'),
        ('spec', u'规格', 'immutable'),
        ('model', u'型号', 'immutable'),
        ('measurement_unit', u'单位', 'immutable'),
        ('unit_price', u'单价'),
        ('quantity', u'数量'),
        ('total_price', u'总价'),
        ('producer', u'生产厂商', 'immutable'),
        ('product_configure', u'产品配置单'),
        ('received', u'是否接收', 'immutable'),
        ('received_user', u'接收人', 'immutable'),
        ('receive_temperature', u'接收温度', 'immutable'),
        ('receive_message', u'接收备注', 'immutable'),
        ('receive_time', u'接收时间', 'immutable'),
        ('inspected', u'是否检验', 'immutable'),
        ('inspected_user', u'检验人', 'immutable'),
        ('inspect_ok_number', u'检验合格数', 'immutable'),
        ('inspect_message', u'检验备注', 'immutable'),
        ('inspect_time', u'检验时间', 'immutable'),
        ('stored', u'是否入库', 'immutable'),
        ('stored_user', u'入库人', 'immutable'),
        ('store_temperature', u'入库温度', 'immutable'),
        ('store_message', u'入库备注', 'immutable'),
        ('store_time', u'入库时间', 'immutable'),
        ]

    def to_json(self):
        total_price = 0
        equipments = []
# print "IV.I", self.purchase_equipments
        for e in self.purchase_equipments:
            total_price += e.total_price
            ru = e.received_user
            if ru is not None:
                ru = User.query.get(ru)
                if ru is not None:
                    ru = ru.nickname or ru.username
            iu = e.inspected_user
            if iu is not None:
                iu = User.query.get(iu)
                if iu is not None:
                    iu = iu.nickname or iu.username
            su = e.stored_user
            if su is not None:
                su = User.query.get(su)
                if su is not None:
                    su = su.nickname or su.username
#print "get equipment_id ", e.equipment_id 
            id_out = ""
            producer_out = ""
            name_out = ""
            spec_out = ""
            model_out = ""
            if e.equipment_id is not None:
                equip_model = Equipment.query.get(e.equipment_id)
                id_out = equip_model.id
                producer_out = equip_model.get_producer_name()
                name_out = equip_model.get_name()
                spec_out = equip_model.get_spec()
                model_out = equip_model.get_model()
            equipments.append({
                    'id' : e.id,
                    'equipment_id' : id_out,
                    'warranty_period' : e.warranty_period,
                    'install_require' : e.install_require,
                    'measurement_unit' : e.measurement_unit,
                    'unit_price' : e.unit_price,
                    'quantity' : e.quantity,
                    'total_price' : e.total_price,
                    'producer' : producer_out,
                    'product_configure' : e.product_configure,
                    'product_name' : name_out,# or json.loads(e.equipment.accessory)['名称'],
                    'spec' : spec_out,
                    'model' : model_out,
                    'received' : e.received,
                    'received_user' : ru,
                    'inspected' : e.inspected,
                    'inspected_user' : iu,
                    'stored' : e.stored,
                    'stored_user' : su,
                    'receive_message' : e.receive_message,
                    'inspect_message' : e.inspect_message,
                    'store_message' : e.store_message,
                    'receive_time' : e.receive_time,
                    'inspect_time' : e.inspect_time,
                    'store_time' : e.store_time,
                    'receive_temperature' : e.receive_temperature,
                    'inspect_ok_number' : e.inspect_ok_number,
                    'store_temperature' : e.store_temperature,
                    })
#print "IV.II"
#print self, equipments, total_price
#print "Angel ", self.sign_date , type(self.sign_date), type(self.arrive_date)
#print "Angel ", len(self.sign_date), len(self.arrive_date)
#print self.sign_date , len(self.sign_date), len(self.sign_date.strip(' '))
#self.sign_date = self.sign_date.strip(' ')
#print "Angel ", len(self.sign_date), len(self.arrive_date)
#sds =  datetime.datetime.strptime(self.sign_date, "%Y-%m-%d")
#sds = self.sign_date.strftime('%Y-%m-%d')
#sds =  self.sign_date
#print self.arrive_date
#ads =  datetime.datetime.strptime(self.arrive_date.strip(' '), '%Y-%m-%d %H:%M:%S')
#ads = self.arrive_date.strftime('%Y-%m-%d %H:%M:%S')
#ads =  self.arrive_date
#print self.id, self.provider_info, self.billing_company, self.get_location, self.pay_mode, self.invoice_type, self.postage_account 

#print "IV.IIUUU"

        create_user_name = self.create_user
        if self.create_user is not None:
            cu = User.query.get(self.create_user)
            if cu is not None:
                create_user_name = cu.nickname or cu.username
        approve_user_name = self.approve_user
        if self.approve_user is not None:
            au = User.query.get(self.approve_user)
            if au is not None:
                approve_user_name = au.nickname or au.username

        equip_json = {'id' : self.id,
            'sign_date' : self.sign_date.strftime('%Y-%m-%d'),
            'provider_info' : self.provider_info,
            'billing_company' : self.billing_company,
            'arrive_date' : self.arrive_date.strftime('%Y-%m-%d %H:%M:%S'),
            'get_location' : self.get_location,
            'pay_mode' : self.pay_mode,
            'invoice_type' : self.invoice_type,
            'postage_account' : self.postage_account,
            'total_price' : total_price,
            'state' : (u'审核通过' if self.state == 0 else (u'待审核' if self.state == 1 else (u'待入库' if self.state == -2 else (u'入库中' if self.state == -3 else (u'已入库' if self.state == -4 else u'状态异常'))))),
            'equipments' : equipments,
            'total_stored' : u'未入库' if self.total_stored == 0 else (u'部分入库' if self.total_stored == 1 else u'完全入库'),
            'contract' : self.contract,
            'create_user' : create_user_name,
            'approve_user' : approve_user_name
        }
#print "IV.III"
        return equip_json

#associate PurchaseOrder and Equipment
class PurchaseEquipment(db.Model):
    __tablename__ = 'purchase_equipment'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    #extra info
    warranty_period = db.Column(db.String(256))#保修期限
    install_require = db.Column(db.String(256))#安装调试要求
    measurement_unit = db.Column(db.String(256))#单位
    unit_price = db.Column(db.Float)#单价
    quantity = db.Column(db.Integer)#数量
    total_price = db.Column(db.Float)#总价
    product_configure = db.Column(db.Text)#产品配置单
    stored = db.Column(db.Integer, default=0)#0:未入库，1:已入库
    stored_user = db.Column(db.Integer)
    store_message = db.Column(db.String(256))
    store_time = db.Column(db.String(256))
    store_temperature = db.Column(db.String(256))
    received = db.Column(db.Integer, default=0)
    received_user = db.Column(db.Integer)
    receive_message = db.Column(db.String(256))
    receive_time = db.Column(db.String(256))
    receive_temperature = db.Column(db.String(256))
    inspected = db.Column(db.Integer, default=0)
    inspected_user = db.Column(db.Integer)
    inspect_message = db.Column(db.String(256))
    inspect_time = db.Column(db.String(256))
    inspect_ok_number = db.Column(db.Integer)

    
    purchase_order = db.relationship(PurchaseOrder, uselist=False, backref="purchase_equipments")
    equipment = db.relationship(Equipment, uselist=False, backref="purchase_order")


class SaleOrder(db.Model):
    __tablename__ = 'sale_order'
    id = db.Column(db.Integer, primary_key=True)#合同编号
    sign_date = db.Column(db.Date)#签证日期
    provider_info = db.Column(db.String(256))#供应商名称、地址、电话
    billing_company = db.Column(db.String(256))#结算公司
    arrive_date = db.Column(db.DateTime)#到货日期
    get_location = db.Column(db.String(1024))#收货地点
    pay_mode = db.Column(db.String(256))#付款方式
    invoice_type = db.Column(db.String(256))#发票类型
    #state = db.Column(db.Integer, default=1)#状态， 0:正常，1:创建，待审核
    state = db.Column(db.Integer, default=1)#状态，1:创建，待审核, 0:已审批, -1:(合同生成) -2:(待出库 ==> 已审批) -3:出库中(partial) -4：已出库
    total_outstore = db.Column(db.Integer, default=0)#出库状态，0:未出库; 1:部分出库; 2:完全出库
    contract = db.Column(db.String(256))#合同文件
    create_user = db.Column(db.Integer)
    approve_user = db.Column(db.Integer)

    @staticmethod
    def get_ordered_headers():
        return [('id', u'销售订单编号', 'immutable'),
        ('sign_date', u'签订日期'),
        ('provider_info', u'客户名称、地址、电话'),
        ('billing_company', u'结算公司', 'option', ['天津市汇天利商贸有限公司']),
        ('arrive_date', u'到货时间'),
        ('get_location', u'收货地点'),
        ('pay_mode', u'付款方式'),
        ('invoice_type', u'发票类型'),
        ('state', u'订单状态', 'immutable'),
        ('total_outstore', u'出库情况(未/部分/完全', 'immutable'),
        ('total_price', u'总价', 'immutable'),
        ('contract', u'合同文件'),
        ('create_user', '创建人'),
        ('approve_user', '审核人'),
        (),
        ('service_commitment', u'售后服务承诺'),
        ('warranty_period', u'保修期限'),
        ('product_name', u'产品名称', 'immutable'),
        ('spec', u'规格', 'immutable'),
        ('model', u'型号', 'immutable'),
        ('measurement_unit', u'单位', 'immutable'),
        ('unit_price', u'单价'),
        ('total_price', u'总价'),
        ('producer', u'生产厂商', 'immutable'),
        ('product_configure', u'产品配置单'),
        ('equipment_id', u'产品编号', 'immutable'),
        ('outstore_quantity', u'已出库数量', 'immutable'),
        ('quantity', u'数量'),
        ('outstore_state', u'出库状态', 'immutable'),
        ]

    def to_json(self):
        total_price = 0
        equipments = []
        for e in self.sale_equipments:
            total_price += e.total_price
            equipments.append({
                    'id' : e.id,
                    'service_commitment' : e.service_commitment,
                    'warranty_period' : e.warranty_period,
                    'measurement_unit' : e.measurement_unit,
                    'unit_price' : e.unit_price,
                    'quantity' : e.quantity,
                    'total_price' : e.total_price,
                    'producer' : e.equipment.producer if e.equipment else None,
                    'product_configure' : e.product_configure,
                    'product_name' : e.equipment.get_name() if e.equipment else None, #.info,
                    'spec' : e.equipment.spec if e.equipment else None,
                    'model' : e.equipment.model if e.equipment else None,
                    'equipment_id' : e.equipment_id,
                    'outstore_state' : u' 未出库' if e.outstore_state == 0 else (u'部分出库' if e.outstore_state == 1 else (u'全出库' if e.outstore_state == 2 else u'状态异常')),
                    'outstore_quantity' : e.outstore_quantity,
                    })

        create_user_name = self.create_user
        if self.create_user is not None:
            cu = User.query.get(self.create_user)
            if cu is not None:
                create_user_name = cu.nickname or cu.username
        approve_user_name = self.approve_user
        if self.approve_user is not None:
            au = User.query.get(self.approve_user)
            if au is not None:
                approve_user_name = au.nickname or au.username

        equip_json = {'id' : self.id,
            'sign_date' : self.sign_date.strftime('%Y-%m-%d'),
            'provider_info' : self.provider_info,
            'billing_company' : self.billing_company,
            'arrive_date' : self.arrive_date.strftime('%Y-%m-%d %H:%M:%S'),
            'get_location' : self.get_location,
            'pay_mode' : self.pay_mode,
            'invoice_type' : self.invoice_type,
            'total_price' : total_price,
            'state' : (u'审核通过' if self.state == 0 else (u'待审核' if self.state == 1 else (u'合同生成' if self.state == -1 else (u'待出库' if self.state == -2 else (u'出库中' if self.state == -3 else (u'已出库' if self.state == -4 else u'状态异常')))))),
            'total_outstore' : u'未出库' if self.total_outstore == 0  else (u'部分出库' if self.total_outstore == 1 else u'完全出库'),
            'equipments' : equipments,
            'contract' : self.contract,
            'create_user' : create_user_name,
            'approve_user' : approve_user_name
        }
        return equip_json

#associate sale_order and equipment
class SaleEquipment(db.Model):
    __tablename__ = 'sale_equipment'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale_order.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    #extra info
    service_commitment = db.Column(db.String(1024))
    warranty_period = db.Column(db.String(256))#保修期限
    measurement_unit = db.Column(db.String(256))#单位
    unit_price = db.Column(db.Float)#单价
    quantity = db.Column(db.Integer)#数量
    total_price = db.Column(db.Float)#总价
    product_configure = db.Column(db.Text)#产品配置单
    outstore_quantity = db.Column(db.Integer, default=0)
    outstore_state = db.Column(db.Integer, default=0)#出库状态：0:完全未出库，1:部分出库；2：完全出库

    sale_order = db.relationship(SaleOrder, uselist=False, backref='sale_equipments')
    equipment = db.relationship(Equipment, uselist=False, backref='sale_order')

class Logistic(db.Model):
    __tablename__ = 'logistic'
    id = db.Column(db.Integer, primary_key=True)#物流单号(系统自分配)
    equipment_name = db.Column(db.String(256))#待送设备名称
    delivery_address = db.Column(db.String(1024))#送货地址
    equipment_type = db.Column(db.String(64))#设备类型(设备/试剂/耗材等)
    delivery_status = db.Column(db.String(64))#完成状态
    state = db.Column(db.Integer, default=1) #当前状态 0:审批通过，1:待审批
    order_num = db.Column(db.Integer)

    def __init__(self):
        self.state = 1

    @staticmethod
    def get_ordered_headers():
        return [('id', u'物流单号(系统自分配)', 'immutable'),
        ('equipment_name', u'待送设备名称', 'immutable'),
        ('delivery_address', u'送货地址'),
        ('equipment_type', u'设备类型(设备/试剂/耗材等)', 'immutable'),
        ('delivery_status', u'完成状态', 'immutable'),
        ('order_num', u'相关销售订单编号')
        ]

    def to_json(self):
        return {
            'id' : self.id,
            'equipment_name' : self.equipment_name,
            'delivery_address' : self.delivery_address,
            'equipment_type' : self.equipment_type,
            'delivery_status' : self.delivery_status,
            'order_num' : self.order_num,
        }

class Repair(db.Model):
    __tablename__ = 'repair'
    
    id = db.Column(db.Integer, primary_key=True)#维修单号(系统自分配)
    equipment_name = db.Column(db.String(256))#待维修设备名称
    repair_address = db.Column(db.String(1024))#维修地址
    equipment_type = db.Column(db.String(64))#设备类型(设备/试剂/耗材等)
    repair_status = db.Column(db.String(64))#完成状态
    state = db.Column(db.Integer, default=1)#当前状态, 0:审核完成, 1:待审核
    order_num = db.Column(db.Integer)

    def __init__(self):
        self.state = 1

    @staticmethod
    def get_ordered_headers():
        return [('id', u'维修单号(系统自分配)', 'immutable'),
        ('equipment_name', u'待维修设备名称', 'immutable'),
        ('repair_address', u'维修地址'),
        ('equipment_type', u'设备类型(设备/试剂/耗材等)', 'immutable'),
        ('repair_status', u'完成状态', 'immutable'),
        ('order_num', u'相关销售订单编号')
        ]

    def to_json(self):
        return {
            'id' : self.id,
            'equipment_name' : self.equipment_name,
            'repair_address' : self.repair_address,
            'equipment_type' : self.equipment_type,
            'repair_status' : self.repair_status,
            'order_num' : self.order_num,
        }

class Store(db.Model):
    __tablename__ = 'store'
    id = db.Column(db.Integer, primary_key=True)#仓库信息编号(系统自分配)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'))
    store_number = db.Column(db.Integer)#在库数字
    #state = db.Column(db.Integer, default=1)#当前状态, 0:审核完成, 1:待审核
    bad_date = db.Column(db.Date)

    purchase_order = db.relationship(PurchaseOrder, uselist=False, backref="stores")
    equipment = db.relationship(Equipment, uselist=False, backref="stores")

    def __init(self):
        #self.state = 1
        pass

    @staticmethod
    def get_ordered_headers():
        return [('id', u'仓库信息编号(系统自分配)', 'immutable'),
        ('equipment_name', u'设备名称', 'immutable'),
#('abbr', u'简称'),
#('equipment_type', u'设备类型(设备/试剂/耗材等)'),
        ('store_number', u'在库数字'),
        ('bad_date', u'过期日期')
        ]

    def to_json(self):
        return {
            'id' : self.id,
            'equipment_name' : self.equipment.get_name() if self.equipment else None, #info,
#'abbr' : self.equipment.abbr,
#'equipment_type' : self.equipment.type,
            'store_number' : self.store_number,
            'bad_date' : 'NULL' if self.bad_date is None else self.bad_date.strftime('%Y-%m-%d'),
        }


class Permission:
    MODULE_PERMISSION_LIST = [
        ('equipment', {
         'read' : 0x01,
         'write' : 0x02,
         'approve' : 0x04
         }),
        ('enterprise', {
         'read' : 0x08,
         'write' : 0x10,
         'approve' : 0x20
         }),
        ('purchase', {
         'read' : 0x40,
         'write' : 0x80,
         'approve' : 0x100
         }),
        ('sale', {
         'read' : 0x200,
         'write' : 0x400,
         'approve' : 0x800
         }),
        ('store', {
         'read' : 0x1000,
         'write' : 0x2000,
         'approve' : 0x4000
         }),
        ('repair', {
         'read' : 0x8000,
         'write' : 0x10000,
         'approve' : 0x20000
         }),
        ('logistic', {
         'read' : 0x40000,
         'write' : 0x80000,
         'approve' : 0x100000
         }),
        ('finance', {
         'read' : 0x200000,
         'write' : 0x400000,
         'approve' : 0x800000
         }),
        ('customer', {
         'read' : 0x1000000,
         'write' : 0x2000000,
         'approve' : 0x4000000
         }),
        ('administer', 0xffffffff)
    ]

    MODULE_PERMISSION_DICT = dict(MODULE_PERMISSION_LIST)

    @staticmethod
    def get_modules(permissions):
        modules = []
        for module_perm in Permission.MODULE_PERMISSION_LIST:
            if module_perm[0] == 'administer':
                if (module_perm[1] & permissions == module_perm[1]):
                    modules.append(module_perm[0])
            elif ((module_perm[1]['read'] & permissions) == module_perm[1]['read']):
                modules.append(module_perm[0])
        return modules

    @staticmethod
    def get_permission(permissions):
        permission_json = {}
        for module_perm in Permission.MODULE_PERMISSION_LIST:
            if module_perm[0] == 'administer':
                continue
            permission_json[module_perm[0]] = {}
            for name, value in module_perm[1].iteritems():
                if (value & permissions) == value:
                    permission_json[module_perm[0]][name] = True
                else:
                    permission_json[module_perm[0]][name] = False
        return permission_json

    @staticmethod
    def to_json():
        return Permission.MODULE_PERMISSION_LIST
    
    
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    permission = db.Column(db.BigInteger, default=0)
    nickname = db.Column(db.String(64))

    def __init__(self, email, username, password, nickname):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.nickname = nickname
        if username == current_app.config['FLASKY_ADMIN']:
            self.permission = Permission.MODULE_PERMISSION_DICT['administer']
        

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def to_json(self):
        user_json = model2json(self, self.__class__)
        user_json.pop('password_hash', None)
        return user_json

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True
    
    def can(self, permissions):
        return (self.permission & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

class UploadFile(db.Model):
    __tablename__ = 'upload_files'
    UPLOAD_DIR ="../uploadfiles"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    filename = db.Column(db.String(256))
    displayName = db.Column(db.String(256))#此变量风格用错
    upload_time = db.Column(db.DateTime)
    type = db.Column(db.String(256))

    def __init__(self, userid, filename, displayName, todaytime, type):
        self.userid = userid
        self.filename = filename
        self.displayName = displayName
        self.upload_time = todaytime
        self.type = type

    def to_json(self):
        upload_user_name = self.userid
        if self.userid is not None:
            cu = User.query.get(self.userid)
            if cu is not None:
                upload_user_name = cu.nickname or cu.username
        if upload_user_name == 0:
            upload_user_name = 'AnonymousUser'
        filejson = {'id' : self.id,
            'upload_user' : upload_user_name,
            'filename' : self.target_filename(), 
            'displayName' : self.displayName,
            'upload_time' : self.upload_time.strftime('%Y-%m-%d %H:%M:%S') if self.upload_time is not None else None,
            'type' : self.type,
        }
        return filejson

    def target_filename(self):
        return os.path.join(self.UPLOAD_DIR, self.filename)

    @staticmethod
    def get_ordered_headers():
        return [('id', u'文件编号', 'immutable'),
        ('upload_user', u'上传用户', 'immutable'),
        ('filename', u'文件名', 'immutable'),
        ('displayName', u'原始文件名', 'immutable'),
        ('upload_time', u'上传时间', 'immutable'),
        ('type', u'类型', 'immutable'),
        ]

class AnonymousUser:
    id = 0
    def can(self, permissions):
        #TODO just for test
        return True
    def is_administrator(self):
        return False


def init_db():
    db.create_all()
    db.session.commit()
    table_names = []
    for clazz in db.Model._decl_class_registry.values():
        try:

            table_names.append(clazz.__tablename__)
        except:
            pass
    #set utf8 or not work well
    for table in table_names:
        db.engine.execute("alter table %s convert to character set utf8" % table)
    print table_names

    admin = User(current_app.config['FLASKY_ADMIN'], current_app.config['FLASKY_ADMIN'], current_app.config['FLASKY_ADMIN_PASSWORD'], current_app.config['FLASKY_ADMIN'])
    db.session.add(admin)
    db.session.commit()
