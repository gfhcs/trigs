

class Player:
    # TODO: Have a class 'Player'. It should represent a VLC process. It is initialized with
    #       the path to a playlist file that VLC opens. We will use playerctl. It should make sure that loop status is 'None'
    #       and that 'shuffle' is "Off". Use --player=vlc
    # TODO: This should offer the actions available through playerctl.
    # TODO: We want to offer some information about the playback, like the name of the current title and the position in
    #       it.

    def __init__(self, paths):
        super().__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def terminate(self):
        pass