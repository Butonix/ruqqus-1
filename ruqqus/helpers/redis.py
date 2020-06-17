import flask_caching
from flask_caching import backends
import redis
from os import environ
import hashlib

class CustomCache(backends.rediscache.RedisCache):


	def __init__(self, app, config, **kwargs):

		self.caches = [
			flask_caching.Cache(
				app,
				config={
					"REDIS_URL":url
				}
				) for url in config['redis_urls']
			]

	def key_to_cache(self, key):

		return self.caches[self.key_to_cache_number]

	def key_to_cache_number(self, key):

		return int(hashlib.md5(bytes(key, 'utf-8')).hexdigest()[-5:], 16) % len(self.caches)

	def get(self, key):

		cache=self.key_to_cache(key)

		return cache.get(key)

	def get_many(self, *keys):

		sharded_keys={i: [] for i in range(len(self.caches))}
		for key in keys:
			cache=self.key_to_cache_number(key)
			sharded_keys[cache].append(key)

		objects={i: self.caches[i].get_many[sharded_keys[i]] for i in range(len(self.caches))}

		output=[]
		for i in objects:
			output+=objects[i]

		output.sort(key=lambda x:keys.index(x))

		return output


	def set(self, key, value, timeout=None):
		cache=self.key_to_cache(key)
		return cache.set(key, value, timeout=timeout)

	def add(self, key, value, timeout=None):
		cache=self.key_to_cache(key)
		return cache.add(key, value, timeout=timeout)

	def set_many(self, mapping, timeout=None):

		caches={i:{} for i in range(len(self.caches))}
		for key, value in mapping:
			caches[self.key_to_cache_number(key)][key]=value

		for i in cache:
			self.caches[i].set_many(caches[i], timeout=timeout)

	def delete(self, key):

		cache=self.key_to_cache(key)
		return cache.delete(key)

	def delete_many(self, *keys):

		if not keys:
			return

		sharded_keys={i: [] for i in range(len(self.caches))}
		for key in keys:
			cache=self.key_to_cache_number(key)
			sharded_keys[cache].append(key)

		for i in sharded_keys:
			self.caches[i].delete_many(sharded_keys[i])

		return True

	def has(self, key):
		cache=self.key_to_cache(key)
		return cache.has(key)

	def clear(self):

		return any([i.clear() for i in self.caches])

	def inc(self, key, delta=1):
		cache=self.key_to_cache(key)
		cache.inc(key, delta=delta)

	def dec(self, key, delta=1):
		cache=self.key_to_cache(key)
		cache.dec(key, delta=delta)

	def unlink(self, *keys):

		if not keys:
			return

		sharded_keys={i: [] for i in range(len(self.caches))}
		for key in keys:
			cache=self.key_to_cache_number(key)
			sharded_keys[cache].append(key)

		for i in sharded_keys:
			self.caches[i].unlink(sharded_keys[i])

		return True

	