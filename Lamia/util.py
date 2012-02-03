# -*- coding: utf-8 -*-
# Lamia
# Copyright 2011-2012 Jun Kimura
# LICENSE MIT
try:
    import cPickle as pickle
except ImportError:
    import pickle
from hashlib import sha1
import inspect
import time
import os
import logging
import os.path as _op

logger = None
def set_logger():
    global logger
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s (%(threadName)-2s) %(message)s',
                    #filename='/tmp/lamia.log',
                    #filemode='w'
                    )
    logger = logging.getLogger("server")
    
def setup():
    if logger is None:
        set_logger()
setup()

def current_time():
    '''
    @summary:  現在時刻を返します
    @return: float: 現在時刻
    '''
    return time.time()

def create_expiration_date(expires=0):
    '''
    @summary: 
        指定された期限が正しい形式かどうか確認し、
        現在時刻から加算した値を返します
    @param expires: float: 数値型
    @return: float: 有効期限日
    '''
    try:
        _expires = float(expires)
        expiration_date = current_time() + _expires
    except:
        # ValueError => specify int or float type for "expires" 
        raise
    return expiration_date

def is_expired(expiration_date):
    '''
    @summary:
        指定された日付が無効であれば真を返します。
    @return bool
    '''
    
    return current_time() >= expiration_date

def build_path(cache_dir, key):
    '''
    @summary:
        キャッシュの格納先ファイルパスを返します
    '''
    path = _op.join(cache_dir, key)
    return path

def make_cache_dir(cache_root, namespace, mode):
    '''
    @summary: 
        ディレクトリが存在しない場合はキャッシュディレクトリを作成し、
        ディレクトリパスを返します
    '''
    path = _op.join(cache_root, namespace)
    if not _op.isdir(path):
        if _op.exists(path):
            raise OSError("%s is not directory." % path)
        os.makedirs(path, mode)
    return path
    
def get_abs_dir_path(dir):
    ''' 
    指定されたディレクトリパスが存在したら
    その絶対パスを返します。
    @return: str: path 
    '''
    path = _op.abspath(dir)
    if not _op.isdir(path):
        raise OSError("%s is not directory." % path)
    return path

_key_func_tpl = "%(module_name)s::%(func_name)s(%(arguments)s)"

def get_func_key(func, *args, **kw):
    '''
    @summary: 
        指定した関数と引数からキーを生成します
    '''
    try:
        arguments = sha1("%s%s" % (str(args), str(kw))).hexdigest()
        module_name = _op.basename(inspect.getfile(func))
    except Exception:
        # pickle error
        raise
    else:
        return _key_func_tpl % dict(
                    module_name=module_name,     
                    func_name=func.func_name,
                    arguments=arguments
                )

class _CacheData():
    '''
    @summary:
        メモリ上のキャッシュクラス
    '''
    __slots__ = ['val', 'expiration_date']
    
    def __init__(self, val, expiration_date):
        self.val = val
        self.expiration_date = expiration_date

class ExpiredError(Exception):
    '''
    @summary: 
        データが有効期限切れの場合に発生する例外クラスです
    '''
    pass
