'''
Created on 2018-8-27

@author: 27136
'''

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''
    
    def __init__(self,error,data='',message=''):
        super(APIError,self).__init__(message)
        self.error = error
        self.data = data
        self.message = message
        

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    
    def __init__(self,data='',message=''):
        super(APIValueError,self).__init__('value:invalid',data,message)

class APIResoureNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''
    
    def __init__(self,data='',message=''):
        super(APIResoureNotFoundError,self).__init__('value:notfound',data,message)
        

class APIPermission(APIError):
    '''
    Indicate the api has no permission.
    '''
    
    def __init__(self,message=''):
        super(APIPermission,self).__init__('permission:forbdden','permission',message)