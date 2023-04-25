from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(mobile,seconds):
    s=Serializer('*2023_1!meghana',seconds)
    return s.dumps({'user':mobile}).decode('utf-8')