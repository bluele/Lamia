# -*- coding: utf-8 -*-

from Lamia.cache import Cache
import os
import unittest

class TestCacheMethod(unittest.TestCase):
    
    cache_root="/tmp/lamia"
    default_expires=10
    namespace="test"

    def setUp(self):
        ''' do initialization '''
        self.cache = Cache(cache_root=self.cache_root,
              default_expires=self.default_expires,
              namespace=self.namespace)
        
    def tearDown(self):
        ''' do finalization '''
        self.cache.clear_cache()
        
    def test_cache_dir(self):
        ''' test for create cache directory '''
        self.assertEqual(self.cache.cache_dir, 
                         os.path.join(
                            self.cache_root,
                            self.namespace            
                            ),
                         'error test_cache_dir'
                         )

    def test_store(self):
        '''test for store cache'''
        key = "key"
        val = "val"
        self.cache.store(key, val, is_store_file=False)
        self.assertEqual(self.cache[key], val,  'error test_store')
        
    def test_store_none(self):
        ''' test for fetch not existing value '''
        self.assertIsNone(self.cache.get("key"), 'error test_store_none')
        
    def test_store_file(self):
        '''test for store_file'''
        key = "key"
        val = "val"
        self.cache.store(key, val, is_store_file=True)
        del self.cache[key]
        self.assertEqual(self.cache[key], val, 'error test_store_file')
        
    def test_function_decorator(self):
        ''' test for cache_decorator'''
        import time
        cached = self.cache.cache_decorator
        @cached(expires=10, is_store_file=False)
        def get_current_time():
            return time.time()
        first = get_current_time()
        second = get_current_time()
        self.assertEqual(first, second, 'error test_function_decorator')
        
    def test_change_namespace(self):
        ''' test for change_namespace '''
        key = "key"
        val = "val"
        self.cache.store(key, val, is_store_file=True)
        self.cache.change_namespace("test_change")
        del self.cache[key]
        self.assertNotIn(key, self.cache, 'error test_change_namespace')

# do unittest
suite = unittest.TestLoader().loadTestsFromTestCase(TestCacheMethod)
unittest.TextTestRunner(verbosity=2).run(suite)