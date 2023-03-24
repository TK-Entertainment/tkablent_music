_player = None

def assign_player(cogs):
    global _player
    _player = cogs

def get_player():
    return _player