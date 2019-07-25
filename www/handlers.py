'''
Created on 2018-8-28

@author: 27136

API

'''
# coding=utf-8

import logging,hashlib,base64,time,json,os,sys

from models import User,Blog,Comment,next_id

from api_server import get,post

from config import configs

from aiohttp import web
import asyncio


#设置cookie
COOKE_NAME = 'aswesome_cookie'
_COOKE_KEY = configs.session.secret



def user_cookie(user,max_age):
    '''
     Generate cookie str by user.
    '''
    #设置cookie格式
    expires = str(int(time.time()+max_age))
    s = '%s-%s-%s-%s'%(user.id,user.passwd,expires,_COOKE_KEY)
    L = '%s-%s-%s'%(user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest())
    return L

async def cookie_user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return  None
    try:
        L = cookie_str.split('-')
        if len(L)!=3:
            return None
        id,expires,sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(id)
        if not user:
            return None
        s = '%s-%s-%s-%s'%(user.id,user.passwd,expires,_COOKE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invild sha1')
            return None
        user.passwd = '***'
        return user
        
    except Exception as e:
        logging.exception(e)
        return None


class JsonData(dict):
    def __init__(self,**kw):
        super(JsonData,self).__init__(**kw)
    
    def __getattr__(self,key):
        try:
            return self[key]
        except:
            raise AttributeError('JsonDict has not attribute as:%s'%key)
    
    def __setattr__(self,key,value):
        self[key] = value



def get_page_index(*,page='1'):
    p = 1
    try:
        p = int(page)
    except ValueError as v:
        raise
    if p<1:
        p=1 
    return p

#api
@get('/')
async def get_index(*,request):
    return {
        '__template__':'index.html',
        'title':'首页'
    }


#api-test-----------------------------
@get('/doc/{t}')
@get('/doc1/{t}')
async def getText(t,request):
    return {
        '__template__':'test_api.html',
		'title':'测试 user 接口'
    }

@get('/api/user')
async def getUser(*,user,name,request):
    ck = request.cookies.get(COOKE_NAME)
    #return "%s-%s-%s"%(ck[0],ck[1],ck[2])
    logging.info('get cookie->%s'%(str(ck)))
    lg = await cookie_user(ck)
    
    data = JsonData()
    if ck is None or lg is None:
        data.status = -1
        data.data = []
        data.message = '用户未登录'
    else:
        data = JsonData(**lg)
    return  data


@get('/html/test')
async def get_html_test(*,request):
    return  {
        '__template__':"index.html",
        'title':'标题',
        'datetime':time.time()
    }
		
@get('/api/usersall')
async def getAll(request,*arg,**kw):
    user = kw.get('user',None)
    name = kw.get('name',None)
    #filterColumn=['name','email','image']
    filterColumn=[]
    rs = await User.findAll(filterColumn=filterColumn)
    data = dict(
        status=1,
        data=rs,
        message='获取用户信息成功',
        user=user,
        name=name
    )
    r = web.Response(body=json.dumps(data,ensure_ascii=False,default=lambda o :o.__dict__).encode('utf-8'))
    r.content_type = 'application/json;charset=utf-8'
    r.set_cookie('COOKE_NAME','user_cookie(User(**rs[0]), 86400)',max_age=86400,httponly=True)
    r.set_cookie(COOKE_NAME,user_cookie(User(**rs[0]), 86400),max_age=86400,httponly=True)
    return r
