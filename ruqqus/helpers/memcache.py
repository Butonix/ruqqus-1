app.config["CACHE_MEMCACHED_SERVERS"]=[environ.get("MEMCACHIER_SERVERS")]
app.config["CACHE_MEMCACHED_USERNAME"]=environ.get("MEMCACHIER_USERNAME")
app.config["CACHE_MEMCACHED_PASSWORD"]=environ.get("MEMCACHIER_PASSWORD")

custom_memcache = pylibmc.Client(servers, binary=True,
                    username=app.config["CACHE_MEMCACHED_USERNAME"],
                    password=app.config["CACHE_MEMCACHED_PASSWORD"],
                    behaviors={
                      # Faster IO
                      'tcp_nodelay': True,

                      # Keep connection alive
                      'tcp_keepalive': True,

                      # Timeout for set/get requests
                      'connect_timeout': 2000, # ms
                      'send_timeout': 750 * 1000, # us
                      'receive_timeout': 750 * 1000, # us
                      '_poll_timeout': 2000, # ms

                      # Better failover
                      'ketama': True,
                      'remove_failed': 1,
                      'retry_timeout': 2,
                      'dead_timeout': 30,
                    })
