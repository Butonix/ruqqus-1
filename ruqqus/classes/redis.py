import flask_caching
import redis
from os import environ
import hashlib

class CustomCache(flask_caching.backends.rediscache.RedisCache):


	def __init__(self, app, redis_urls=[]):

		self.caches = [
			flask_caching.Cache(
				app,
				config={
					"REDIS_URL":url
				}
				) for url in redis_urls
			]

	def key_to_cache(self, key):

		hash_object=hashlib.md5(bytes(key, 'utf-8'))

		hexstring=hash_object.hexdigest()

		x=int(hexstring[-5:], 16) % len(self.caches)

		return self.caches[x]

	



