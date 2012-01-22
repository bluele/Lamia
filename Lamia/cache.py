# -*- coding: utf-8 -*-
# Lamia
# Copyright 2011-2012 Jun Kimura
# LICENSE MIT
import os
from functools import wraps
from Lamia.util import current_time, create_expiration_date, is_expired, \
                 make_cache_dir, build_path, get_func_key,\
                 logger, _CacheData, ExpiredError
from Lamia.serialize import dump, load, \
                      DumpError, LoadError
from Lamia.async import AsyncPurgeFile, AsyncSaveFile, loop

join = os.path.join

__all__ = ("Cache",)

class Cache():

    _max_cache_file = 1000
    def __init__(self, cache_root, default_expires,
                  cache=dict(), namespace='default', mode=0777,
                  default_encoding='utf8'):
        '''
        @param cache_root: str or unicode: キャッシュファイルの格納ディレクトリのrootパス
        @param default_expires: float: デフォルトの有効期限
        @param cache: キャッシュオブジェクト
        @param namespace: str: キャッシュのnamespace
        @param mode: int: ディレクトリの作成パーミッション
        @param default_encoding: str: キャッシュファイル出力時のデフォルトのエンコード
        '''
        self.cache_root = cache_root
        self._init_cache(cache)
        self._init_mode(mode)
        self._init_cache_dir(self.cache_root, namespace)
        self._init_default_encoding(default_encoding)
        self._init_default_expires(default_expires)
        
    def change_namespace(self, namespace, default_expires=None,
                  mode=None, default_encoding=None):
        '''
        @summary: 
            指定した名前空間に切り替えます
        '''
        if default_expires is not None:
            self._init_default_expires(default_expires)
        if mode is not None:
            self._init_mode(mode)
        if default_encoding is not None:
            self.default_encoding = default_encoding
        self._init_cache_dir(self.cache_root, namespace)
    
    def get(self, key):
        '''
        @summary: 
            キーに対応する値を取り出します
            メモリ上にキーが存在しない場合、ディスク上のファイルを探索
            以上で見つからない場合、raise KeyError
        '''
        try:
            # search on memory
            val = self._get_cache_memory(key)
        except (KeyError, ExpiredError):
            # search on disk
            val = self._get_cache_file(key)
        return val
        
    def _get_cache_memory(self, key):
        '''
        @summary:
            指定したキーでメモリ上のキャッシュからデータを取得します
        '''
        data = self.cache[key]
        if is_expired(data.expiration_date):
            del self.cache[key]
            raise ExpiredError("ExpiredError")
        return data.val
    
    def _get_cache_file(self, key):
        '''
        @summary: 
            指定したキーでファイル上からデータを取得します
        '''
        try:
            path = build_path(self.cache_dir, key)
            data = load(path)
            if is_expired(data.expiration_date):
                raise ExpiredError("ExpiredError")
        except IOError:
            # if not exists file
            raise KeyError(key)
        except OSError:
            # Not Found key-cachefile
            raise KeyError(key)
        except ValueError,err:
            raise ValueError("Cache File '%s' style is wrong." % path)
        except LoadError:
            raise KeyError(key)
        except ExpiredError:
            self._delete_file(path)
            raise KeyError(key)
        else:
            return data.val
    
    def store(self, key, val, expires=None, is_store_file=True):
        '''
        @summary: 
            キャッシュにキーと値を格納します
            __setitem__と比べて引数が多いのでデフオルト引数が必要
        '''
        if expires is None:
            _expires = self.default_expires
        else:
            _expires = expires
        expiration_date = create_expiration_date(_expires)
        try:
            if is_store_file:
                self._store_cache_file(key, val, expiration_date)
            self._store_cache_memory(key, val, expiration_date)
        except:
            raise
        
    def _store_cache_memory(self, key, val, expiration_date):
        '''
        @summary: 
            メモリ上のキャッシュにキーと値を格納します
        '''
        self.cache[key] = _CacheData(val=val, expiration_date=expiration_date)
        #logger.debug("STORE MEMORY: Key:%s" % (key,))
        
    def _store_cache_file(self, key, val, expiration_date):
        '''
        @summary: 
            ファイル上のキャッシュにキーと値を格納します
        '''
        try:
            if isinstance(val, unicode):
                val = val.encode(self.default_encoding)
            dump(_CacheData(val=val, expiration_date=expiration_date),
                 build_path(self.cache_dir, key))
        except Exception:
            raise
        
    def sync(self):
        '''
        @summary: 
            現在保持しているメモリキャッシュをファイルキャッシュで更新します
        '''
        try:
            self.cache.update(load(self.cache_file))
        except Exception:
            # pickle error
            raise
        
    def save(self, is_async=False):
        '''
        @summary:
            現在のメモリキャッシュでキャッシュファイルを更新します
        '''
        if is_async:
            self._save_async()
        else:
            self._save()
        
    def _save_async(self):
        '''
        @summary: 
            非同期に現在のメモリキャッシュでキャッシュファイルを更新します
            SimpleCacheInstance.save(async=True)
        '''
        try:
            for key, cache in self.cache.iteritems():
                AsyncSaveFile(build_path(self.cache_dir, key), cache)
        except Exception:
            # pickle error
            raise
        
    def _save(self):
        '''
        @summary: 
            現在のメモリキャッシュでキャッシュファイルを更新します
        '''
        try:
            for key, cache in self.cache.iteritems():
                dump(cache, build_path(self.cache_dir, key))
        except Exception:
            # pickle error
            raise
        
    def purge(self, date=current_time(), is_async=False):
        '''
        @summary: 
            現在保持しているキャッシュの中で有効期限を過ぎたものを削除します
            purge_*は引数に指定した時刻、関数呼び出し時刻を基準に削除します
        '''
        try:
            self.purge_file(date, is_async)
            self.purge_memory(date)
        except:
            raise
        
    def purge_file(self, date=current_time(), is_async=False):
        '''
        @summary: 
            期限切れ、または不正なスタイルのキャッシュファイルを削除します
        '''
        if not os.path.isdir(self.cache_dir):
            raise IOError("%s is not directory." % self.cache_dir)
        try:
            root, _, files = os.walk(self.cache_dir).next()
            if not len(files): raise StopIteration
        except StopIteration:
            #logger.debug("There are no cache-file at %s" % self.cache_dir)
            return
        if is_async:
            self._purge_file_async(date, root, files)
        else:
            self._purge_file(date, root, files)
        
    def _purge_file(self, date, root, files):
        '''
        @summary: 
            期限切れのキャッシュファイルを削除します
        '''
        for fpath in files:
            path = join(root, fpath)
            with open(path, 'rb') as f:
                try:
                    if float(f.readline()) <= date:
                        os.remove(path)
                        #logger.debug("PURGE FILE: %s" % path)
                except ValueError:
                    os.remove(path)
                    #logger.debug("PURGE FILE: %s" % path)
                    
    def _purge_file_async(self, date, root, files):
        '''
        @summary: 
            期限切れのキャッシュファイルを非同期に削除します
        '''
        for fpath in files:
            AsyncPurgeFile(join(root, fpath), date)
    
    def purge_memory(self, date=current_time()):
        '''
        @summary: 
            memory上のキャッシュを削除します
        '''
        delete_key = set()
        try:
            for key, cache in self.cache.iteritems():
                if cache.expiration_date <= current_time():
                    delete_key.add(key)
            for key in delete_key:
                del self.cache[key]
                #logger.debug("PURGE MEMORY: %s" % key)
        except:
            raise
        
    def clear_cache(self):
        '''
        @summary: 
            メモリ上、現在の名前空間のキャッシュを削除します
        '''
        try:
            self._clear_cache_memory()
            self._clear_cache_file()
        except:
            raise
        
    def _clear_cache_file(self):
        '''
        @summary: 
            現在の名前空間のキャッシュファイルを削除します
        '''
        if not os.path.isdir(self.cache_dir):
            raise IOError("%s is not directory." % self.cache_dir)
        try:
            root, _, files = os.walk(self.cache_dir).next()
            if not len(files): raise StopIteration
        except StopIteration:
            #logger.debug("There are no cache-file at %s" % self.cache_dir)
            return
        for fpath in files:
            os.remove(join(root, fpath))
        
    def _clear_cache_memory(self):
        '''
        @summary: 
            メモリ上のキャッシュを削除します
        '''
        self.cache.clear()
        
    def cache_decorator(self, expires=None, is_store_file=False):
        '''
        @summary: 
            関数の名前と引数でキーを構成し、存在すれば、キーを取得します
            無ければ、キーと関数の結果をセットします
        '''
        def _cache_decorator(func):
            @wraps(func)
            def __cache_decorator(*args, **kw):
                key = get_func_key(func, *args, **kw)
                try:
                    return self[key]
                except KeyError:
                    pass
                self.store(key, func(*args, **kw), expires, is_store_file)
                return self[key]
            return __cache_decorator
        return _cache_decorator
    
    def async_loop(self, timeout=30.0, use_poll=False, map=None, count=None):
        '''
        @summary: 
            イベントループを起動します
        '''
        if count is None:
            count = self._max_cache_file
        loop(timeout, use_poll, map, count)
    
    def _delete_file(self, path):
        '''
        @summary: 
            指定したパスのファイルを削除します
        '''
        os.remove(path)
        #logger.debug("DELETE FILE: %s" % path)
        
    def _delete_expired_key(self, key):
        '''
        @summary: 
            指定されたパスのファイルが期限切れの場合、削除します
        '''
        path = build_path(self.cache_dir, key)
        data = load(path)
        if is_expired(data.expiration_date):
            # 古いキャッシュの際は削除する
            self._delete_file(path)
        
    def _init_cache(self, cache):
        '''
        @summary: 
            init self.cache
        '''
        self.cache = cache
        
    def _init_mode(self, mode):
        '''
        @summary: 
            init self.mode: ファイル、ディレクトリの作成権限
        '''
        self.mode = mode
        
    def _init_default_expires(self, expires):
        '''
        @summary: 
            init self.default_expires: 
        '''
        self.default_expires = float(expires)
        
    def _init_default_encoding(self, encoding):
        '''
        @summary: 
            init self.default_encoding:
            ファイル出力の際の基本エンコードです
        '''
        self.default_encoding = encoding
        
    def _init_cache_dir(self, cache_root, namespace):
        '''
        @summary: 
            init self.cache_dir: キャッシュの格納パス
        '''
        self.cache_dir = make_cache_dir(cache_root, namespace, self.mode)
        
    def _valid_expires(self, expires):
        '''
        @summary: 
            validation for expires
        '''
        if float(expires) < 0:
            raise ValueError("You must specify positive number for 'expires'.") 
        
    def __delitem__(self, key):
        '''
        @summary: 
            del self[key]
        '''
        del self.cache[key]
        
    __getitem__ = get
    __setitem__ = store
    
