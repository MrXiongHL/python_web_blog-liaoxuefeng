'''
Created on 2018-8-23

@author: 27136
'''
import time,uuid
from orm import Model,TextField,StringField,FloatField,BooleanField


def next_id():
    return '%slhx%s271'%(int(time.time()), uuid.uuid4().hex) 

class User(Model):
    
    __table__ = 'users'
    
    
    id = StringField(primary_key = True, default = next_id, ddl = 'varchar(50)')
    email = StringField(ddl = 'varchar(50)')
    passwd = StringField(ddl = 'varchar(50)')
    admin = BooleanField()
    name = StringField(ddl = 'varchar(50)')
    image = StringField(ddl = 'varchar(500)')
    create_dt = FloatField(default = time.time)

class Blog(Model):
    
    __table__ = 'blogs'
    
    id = StringField(primary_key=True,default=next_id,ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    name = StringField(ddl = 'varchar(50)')
    summary = StringField(ddl = 'varchar(200)')
    context = TextField()
    create_dt = FloatField(default = time.time)

class Comment(Model):
    
    __table__ = 'comments'
    
    id = StringField(primary_key=True,default=next_id,ddl = 'varchar(50)')
    blog_id = StringField(ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    content = TextField()
    create_dt = FloatField(default=time.time)

    
if __name__ == '__main__':
    print(next_id())
  
    
    