'''
Created on 2018-8-21

@author: 27136
'''
import logging,aiomysql,asyncio

def log(sql,args=()):
    logging.info('SQL:%s \r\nARGS:%s'%(sql,args))
    
async def create_pool(loop,**kw):
    logging.info('create database connection pool')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['database'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

async def select(sql,args,size=None):
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        rs = None
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        logging.info('rows returned:%s'%(len(rs)))
        return rs
        
async def execute(sql,args):
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args or ())
            affected = cur.rowcount
        except BaseException as e:
            raise e
        return affected



def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)

class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)

class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)
        
        
class ModelMetaClass(type):
    
    def __new__(cls,name,bases,attrs):
           
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)
        #表名
        table_name = attrs.get('__table__',None) or name
        logging.info('found model:name=%s table_name=%s'%(name,table_name))
        
        #主键,参数（含主键），参数（不含主键）
        table_primary_key = None
        mappings = dict()
        fields = []
        
        for k,v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                #找到主键
                if v.primary_key:
                    if table_primary_key:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    table_primary_key = k
                else:
                    fields.append(k)
        
        if not table_primary_key:
            raise RuntimeError('Primary key not found.')
        
        for k in mappings.keys():
            attrs.pop(k)
        
        select_fields = list(map(lambda x: '`%s`' %(x) ,fields))
        update_fields = ', '.join(map(lambda f: '`%s` = ?'%(mappings.get(f) or f),fields))
        attrs['__table__'] = table_name
        attrs['__mappings__'] = mappings
        attrs['__fields__'] = fields
        attrs['__primary_key__'] = table_primary_key
        
        #构造默认，select,insert,update,delete语句
        attrs['__select__'] = 'select `%s` ,%s from `%s`'%(table_primary_key,', '.join(select_fields),table_name)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values(%s)'%(table_name,', '.join(select_fields),table_primary_key,create_args_string(len(select_fields)+1))
        attrs['__update__'] = 'update `%s` set %s where `%s` = ?'%(table_name,update_fields,table_primary_key)
        attrs['__delete__'] = 'delete from `%s` where `%s` = ?'%(table_name,table_primary_key)
        
        return type.__new__(cls,name,bases,attrs)
        

class Model(dict,metaclass=ModelMetaClass):
    
    def __init__(self,filterColumn=None,**kw):
        logging.info("筛选结果：%s"%str(filterColumn))
        if isinstance(filterColumn, list) and len(filterColumn)>0:
            copy = dict()
            for k in filterColumn:
                copy[k] = kw[k]
            kw = copy
        super(Model,self).__init__(**kw)
    
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"Model" has not attrobite as %s'%(key))
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def getValue(self,key):
        return getattr(self, key,None)

    def getDefaultValue(self,key):
        value = getattr(self, key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                setattr(self, key, value)
        return value
    
    @classmethod
    async def findAll(cls,where=None,args=None,**kw):
        'find objects by where clause'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit',None)
        if limit:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit,tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value:%s'%(str(limit)))
        rs = await select(' '.join(sql), args)
        filterColumn = kw.get('filterColumn',None)
        return [cls(filterColumn=filterColumn,**r) for r in rs]

    @classmethod
    async def findNumber(cls,selectField,where=None,args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`'%(selectField,cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']
        
    @classmethod
    async def find(cls,pk):
        'find object by primary key.'
        sql = '%s where `%s`=?'%(cls.__select__,cls.__primary_key__)
        rs = await select(sql, [pk],1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    
    async def save(self):
        args = list(map(self.getDefaultValue,self.__fields__))
        args.append(self.getDefaultValue(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows !=1:
            logging.warn('failed to insert record: affected rows: %s' % rows)
        return rows

    async def upadate(self):
        args = list(map(self.getvalue,self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update record: affected rows: %s' % rows)

    async def remove(self):
        args = list(self.getValue(self.__primary_key__))
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to delete record: affected rows: %s' % rows)

        
if __name__ == '__main__':
    print('orm')
    
    fields = ['35','测试',1.2,'啊哈']
    escaped_fields = list(map(lambda f: '`%s`' % f, fields))
    escaped_fields2 = ', '.join(map(lambda f: '`%s`' % f, fields))
    print(escaped_fields)
    print(escaped_fields2)
    
    def gets():
        return 'd'
    gets = 'ah'
    value = gets() if callable(gets) else gets
    print(value)
    