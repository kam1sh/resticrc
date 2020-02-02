from subprocess import check_call

from attr import attrib, attrs

@attrs
class ConsoleExecutor:
    """ Command executor with debugging support. """
    dry_run: bool = attrib(default=False)

    def run(self, command, cwd=None):
        if self.dry_run:
            print("Executing: ", command)
        else:
            check_call(command, cwd=cwd)

executor = ConsoleExecutor()
