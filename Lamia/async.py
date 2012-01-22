# -*- coding: utf-8 -*-
# Lamia
# Copyright 2011-2012 Jun Kimura
# LICENSE MIT
import os
import asyncore
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from Lamia.util import logger

loop = asyncore.loop

__all__ = ("AsyncPurgeFile", "AsyncSaveFile", "loop")

class AsyncWriteFile(asyncore.file_dispatcher):
    '''
    @summary: 
        非同期ファイル書き出しクラス
    '''
    _mode = "wb"
    def __init__(self, path, buffer, *args, **kw):
        '''
        @param buffer: str: 書き出し文字列
        '''
        asyncore.file_dispatcher.__init__(self, open(path, self._mode), *args, **kw)
        self.write_buffer = buffer
    
    def handle_write(self):
        '''
        @summary: 
            書き込み用のハンドル
        '''
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]
        if len(self.write_buffer) <= 0:
            self.handle_close()
        
    def writable(self):
        return (len(self.write_buffer) > 0)
    
    def readable(self):
        return False
        
    def handle_expt(self):
        # 帯域外のデータにみえるイベントを無視する
        pass
    
    def handle_close(self):
        '''
        @summary: 
            ファイル操作の終了処理を行います
        '''
        self.close()
        
class AsyncReadFile(asyncore.file_dispatcher):
    '''
    @summary: 
        非同期ファイル読み込みクラス
        初期化に
    '''
    _mode = "rb"
    def __init__(self, path, ret, *args, **kw):
        '''
        @param ret: class: 戻り値を格納するクラスのインスタンス（参照はメインスレッドで保持しておく）
                  ret.val, ret.expiration_date
        '''
        asyncore.file_dispatcher.__init__(self, open(path, self._mode), *args, **kw)
        self.read_buffer = StringIO()
        self.ret = ret
        
    def writable(self):
        return False
    
    def handle_read(self):
        '''
        @summary: 
            読み込み処理を行います
        '''
        while True:
            m = self.recv(8192)
            if m == "":
                break
            self.read_buffer.write(m)
        
    def handle_expt(self):
        # 帯域外のデータにみえるイベントを無視する
        pass
    
    def handle_close(self):
        '''
        @summary: 
            ファイル操作の終了処理を行います
        '''
        self.close()
        self._parse_data()
        
    def _parse_data(self):
        '''
        @summary: 
            取得したデータをパースしてreturnclassに格納します
        '''
        self.read_buffer.seek(0)
        self.ret.expiration_date = float(self.read_buffer.readline())
        self.ret.val = self.read_buffer.read()
        
class AsyncPurgeFile(asyncore.file_dispatcher):
    '''
    @summary: 
        非同期ファイル読み込みクラス
        初期化に
    '''
    _mode = "rb"
    def __init__(self, path, expiration_date, *args, **kw):
        '''
        @param ret: class: 戻り値を格納するクラスのインスタンス（参照はメインスレッドで保持しておく）
                  ret.val, ret.expiration_date
        '''
        self.path = path
        self.expiration_date = expiration_date
        asyncore.file_dispatcher.__init__(self, open(path, self._mode), *args, **kw)
        self.read_buffer = StringIO()
        
    def writable(self):
        return False
    
    def handle_read(self):
        while True:
            m = self.recv(64)
            self.read_buffer.write(m)
            if m == "" or "\n" in m:
                break
        
    def handle_expt(self):
        # 帯域外のデータにみえるイベントを無視する
        pass
    
    def handle_close(self):
        '''
        @summary: 
            ファイル操作の終了処理を行います
        '''
        self.close()
        try:
            self._parse_data()
        except:
            raise
        
    def _parse_data(self):
        '''
        @summary: 
            取得したデータをパースして処理を行います
        '''
        self.read_buffer.seek(0)
        try:
            if float(self.read_buffer.readline()) <= self.expiration_date:
                os.remove(self.path)
                #logger.debug("PURGE FILE: %s" % self.path)
        except ValueError:
            os.remove(self.path)
            
class AsyncSaveFile(asyncore.file_dispatcher):
    '''
    @summary: 
        非同期キャッシュファイル書き出しクラス
    '''
    _mode = "wb"
    def __init__(self, path, cache, *args, **kw):
        '''
        @param path: str: 格納先のパス 
        @param cache: str: 書き出し文字列
        '''
        asyncore.file_dispatcher.__init__(self, open(path, self._mode), *args, **kw)
        #self.write_buffer = cache
        self.write_buffer = "%s\n%s" % (cache.expiration_date, cache.val)
    
    def handle_write(self):
        '''
        @summary: 
            書き込み用のハンドル
        '''
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]
        if len(self.write_buffer) <= 0:
            self.handle_close()
        
    def writable(self):
        return (len(self.write_buffer) > 0)
    
    def readable(self):
        return False
        
    def handle_expt(self):
        # 帯域外のデータにみえるイベントを無視する
        pass
    
    def handle_close(self):
        '''
        @summary: 
            ファイル操作の終了処理を行います
        '''
        self.close()
