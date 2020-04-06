#wrapper for api-related things that discriminates between an api url
#and an html url for the same content
# f should return {'api': lambda:function(), 'html':lambda:function()}

def api(f):

    def wrapper(*args, **kwargs):

        x=f(*args, **kwargs)

        if requests.path.startswith('/api/v1'):
            return jsonify(x['api']())
        else:
            return x['html']()

    wrapper.__name__=f.__name__
    return wrapper
