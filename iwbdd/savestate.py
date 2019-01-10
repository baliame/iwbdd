import os


class Savestate:
    def __init__(self, savefile):
        self.savefile = savefile

    def write(self, ctrl):
        if ctrl.saved_state is None:
            return
        with open(self.savefile, 'wb') as f:
            ctrl.write_save_to_file(f)

    def read(self, ctrl):
        if os.path.isfile(self.savefile):
            with open(self.savefile, 'rb') as f:
                ctrl.restore_from_saved_file(f)
