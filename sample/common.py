# -*- coding: utf-8 -*-

from Lamia.cache import Cache
import time

cache = Cache(cache_root="/tmp/lamia", 
              default_expires=10,
              namespace="test")
cached = cache.cache_decorator

# メモリにのみキャッシュします
@cached(expires=10, is_store_file=False)
def get_time():
    return unicode(time.time())

# ファイルにキャッシュを行います
@cached(expires=100, is_store_file=True)
def get_last_time():
    return unicode(time.time())

def main():
    for _ in xrange(3):
        print get_time()
    for _ in xrange(3):
        print get_last_time()
    cache.store("key", "val", expires=100, is_store_file=True)
    print cache["key"]
    # 名前空間内の有効期限切れのキャッシュファイルを削除します
    cache.purge_file()
    # 保持しているメモリ上の有効期限切れのキャッシュを削除します
    cache.purge_memory()

if __name__ == '__main__':
    main()