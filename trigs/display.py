

class Display:
    # TODO: Have a class 'Display'.
    #  Under the hood it creates a separate process that  displays a Tkinter window with a certain color.
    #  The color can be changed and there can be text displayed. The window should be full-screenable.
    #  The separate process receives commands via a queue. It listens to that queue and reacts to commands.
    #
    pass


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        pass
