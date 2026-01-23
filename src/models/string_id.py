import random, string


def string_id(length: int):
    randlst = [
        random.choice(string.ascii_letters + string.digits) for i in range(length)
    ]
    return "".join(randlst)
