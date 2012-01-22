# -*- coding: utf-8 -*-
# Lamia
# Copyright 2011-2012 Jun Kimura
# LICENSE MIT
from Lamia.util import _CacheData, logger
'''
@summary: 
    serialize系のメソッドをサポートするモジュール    
'''

def dump(data, path):
    '''
    @summary: 
        指定したデータをシリアライズして指定したファイル上に書き込みます
    '''
    with open(path, 'wb') as f:
        f.write("%s\n" % str(data.expiration_date))
        f.write(str(data.val))
    #logger.debug("STORE FILE: %s" % path)

def load(path):
    '''
    @summary: 
        指定したデータをpythonデータ型に変換したものを返します
        format for serialize_data:
            <expiration_date>(enter)
            <val>
    '''
    with open(path, 'rb') as f:
        expiration_date = float(f.readline().strip())
        val = f.read()
    return _CacheData(val=val, expiration_date=expiration_date)

class DumpError(Exception):
    '''
    @summary: 
        指定したデータのシリアライズに失敗した場合に発生する例外クラス
    '''
    pass
    
class LoadError(Exception):
    '''
    @summary: 
        指定したデータのpython型への変換に失敗した場合に発生する例外クラス
    '''
    pass
    
    