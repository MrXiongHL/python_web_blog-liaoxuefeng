'''
Created on 2018-8-16

@author: 27136
'''

import logging
from logging import handlers

log_file_info = "./log/info.log"
log_file_error = "./log/error.log"
when = 'M'#时间间隔，资料https://www.cnblogs.com/nancyzhu/p/8551506.html
backCount = 100#文件个数
log_fmt = '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s : %(message)s'

#----------------日志
#--1.--写入文件，控制台打印
#lg = logging.basicConfig(filename=log_file,filemode="a",level=logging.INFO,format=log_fmt)
#lsh = logging.StreamHandler()#创建控制台输出流
#stream_log_fmt_str = logging.Formatter(log_fmt)#创建控制台日志输出格式
#lsh.setFormatter(stream_log_fmt_str)#设置控制台显示格式
#log = logging.getLogger(lg)#获取当前logging控制器
#log.addHandler(lsh)#添加控制台输出流到当前logging

#--2.--写入文件，控制台打印
#lg = logging.basicConfig(level=logging.INFO,format=log_fmt)
#log_file_handler = logging.FileHandler(filename=log_file,encoding='utf-8',delay=False)
#stream_log_fmt_str = logging.Formatter(log_fmt)#创建控制台日志输出格式
#log_file_handler.setFormatter(stream_log_fmt_str)#设置控制台显示格式
#log = logging.getLogger(lg)
#log.addHandler(log_file_handler)

#--3.--根据时间新建日志，写入文件，控制台打印
lg = logging.basicConfig(level=logging.INFO,format=log_fmt)
stream_log_fmt_str = logging.Formatter(log_fmt)#创建控制台日志输出格式
th_hander = handlers.TimedRotatingFileHandler(filename=log_file_info,when=when,backupCount=backCount,encoding='utf-8')
th_hander.setLevel(logging.INFO)
th_hander.setFormatter(stream_log_fmt_str)#设置显示样式
log = logging.getLogger(lg)
log.addHandler(th_hander)

th_hander_err = handlers.TimedRotatingFileHandler(filename=log_file_error,when=when,backupCount=backCount,encoding='utf-8')
#stream_log_fmt_str = logging.Formatter(log_fmt)#创建控制台日志输出格式
th_hander_err.setLevel(logging.ERROR)
th_hander_err.setFormatter(stream_log_fmt_str)#设置显示样式
log.addHandler(th_hander_err)


import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

import aiohttp_cors

from jinja2 import Environment,FileSystemLoader

import orm
from api_server_tool import add_static,add_routes

from config import configs

from handlers import COOKE_NAME,cookie_user

#模板配置
def init_jinja2(app,**kw):
    logging.info('init jinja2')
    options = dict(
        autoescape=kw.get('autoescape',True),
        block_start_string=kw.get('block_start_string','{%'),
        block_end_string=kw.get('block_end_string','%}'),
        variable_start_string=kw.get('variable_start_string','{{'),
        variable_end_string=kw.get('variable_end_string','}}'),
        auto_reload = kw.get('auto_reload',True)
    )
    path = kw.get('path',None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 templates path:%s'%path)
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env
    
#自定义错误处理页面
def error_url(app,request,status):
    kw = {
        'status':status,
    }
    logging.error('Can not access as:%s->%s'%(request.method,request.path))
    resp = web.Response(body=app['__templating__'].get_template('error.html').render(**kw).encode('utf-8'))
    resp.content_type = 'text/html;charset=utf-8'
    return resp

async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request:%s %s'%(request.method,request.path))
        
        try:
            r = await handler(request)
            if r.status!=200:
                return error_url(app, request, r)
            return r
        except web.HTTPException as ex:
            if ex.status != 200:
                return error_url(app, request, ex.status)
            raise
        
    return logger

async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json :%s'% str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.form()
                logging.info('request from :%s'% str(request.__data__))
            return (await hander(request))
    return parse_data

#解析cookie放在request里面
async def auth_factory(app,handler):
    async def auth(request):
        logging.info('check user %s=>%s'%(request.method,request.path))
        request.__user__ = None
        cookie_strs = request.cookies.get(COOKE_NAME)
        if cookie_strs:
            user = await cookie_user(cookie_strs)
            if user:
                logging.info('set current user:%s'%(user.email))
                request.__user__ = user
        return (await handler(request))
        
    return auth


async def response_factory(app,handler):

    async def response(request):

        logging.info('response hander')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__tempalte__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False,default=lambda o :o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r>=100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple):
            t,m = r
            if isinstance(t, int) and t>=100 and t <600:
                return web.Response(r,str(m))
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t):
    dela = int(time.time()-t)
    if dela<60:
        return u'1分钟前'
    if dela < 3600:
        return u'%s分钟前'%(dela//60)
    if dela < 86400:
        return u'%s小时前'%(dela//3600)
    if dela < 604800:
        return u'%s天前'%(dela//86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日 '%(dt.year,dt.moth,dt.day)

def stringx_filter(x):
    return u'%s,%s'%(x,'死了！')


async def init_web_py36(loop,cors=None):
    await orm.create_pool(loop=loop,**configs['db'])
    
    app = web.Application(loop=loop,middlewares=[
        logger_factory,auth_factory,response_factory
    ])
    init_jinja2(app,filters=dict(datetime=datetime_filter,stringx=stringx_filter))
    add_routes(app, 'handlers')
    add_static(app)
    
    #设置跨域
    if cors:
        set_cors(app)
        
    srv = await loop.create_server(app.make_handler(),'127.0.0.1','9100')
    return srv


async def init_web_py37(loop,cors=None):
    await orm.create_pool(loop=loop,**configs['db'])
    
    app = web.Application(middlewares=[
        logger_factory,auth_factory,response_factory
    ])
    init_jinja2(app,filters=dict(datetime=datetime_filter,stringx=stringx_filter))
    add_routes(app, 'handlers')
    add_static(app)
    
    #设置跨域
    if cors:
        set_cors(app)
    
    srv = await loop.create_server(app.make_handler(),'127.0.0.1','9100')
    return srv

def set_cors(app):
    #设置跨域
    cors = aiohttp_cors.setup(app,defaults={
        '*':aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    #resoure = cors.add(app.router.add_resource('/api'))
    for route in list(app.router.routes()):
        cors.add(route)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_web_py37(loop,cors=True))
    loop.run_forever()
    
    