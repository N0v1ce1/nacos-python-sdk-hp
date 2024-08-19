import hashlib


def md5(content):
    if content:
        md = hashlib.md5()
        md.update(content.encode('utf-8'))
        return md.hexdigest()

