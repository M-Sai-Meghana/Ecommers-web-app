from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def atoken(email,seconds):
    s=Serializer('*2023_1!meghana',seconds)
    return s.dumps({'user':email}).decode('utf-8')