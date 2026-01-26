"""Bash process."""
import subprocess as sp
import io
import time
import traceback

def eprint(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)

class Bash(object):
    """A Bash session."""
    def __init__(self, sudo=False, stdout=sp.DEVNULL, stderr=sp.DEVNULL, **kwargs):
        """Initialize bash process."""
        self.proc = None
        self.stdin = None
        self.stderr = None
        self.stdout = None
        self.open(sudo, stdout, stderr, **kwargs)

    def open(self, sudo=False, stdout=sp.DEVNULL, stderr=sp.DEVNULL, **kwargs):
        if self.proc is not None:
            return
        if sudo:
            command = ['sudo', 'bash']
        else:
            command = ['bash']
        self.proc = sp.Popen(
            command, stdin=sp.PIPE, stdout=stdout, stderr=stderr, **kwargs)
        if kwargs.get('text', False):
            self.stdin = self.proc.stdin
        else:
            self.stdin = io.TextIOWrapper(self.proc.stdin)
        self.stdout = self.proc.stdout
        self.stderr = self.proc.stderr
        self('trap "" SIGINT')

    def close(self):
        if self.proc is None:
            return
        # proc.wait uses os.waitpid, but it seems like if
        # __del__ is called due to interpreter exit, then
        # os.waitpid might have been set to None causing
        # an error.
        try:
            self('exit')
            self.stdin.flush()
            self.stdin.close()
        except IOError:
            traceback.print_exc()
        time.sleep(0.1)
        try:
            for i in range(3):
                if self.proc.poll() is not None:
                    break
                time.sleep(1)
            else:
                eprint('Bash not exiting, terminating and waiting...')
                self.proc.terminate()
                self.proc.wait()
                eprint('Bash done.')
        finally:
            self.proc = None

    def __call__(self, *args, **kwargs):
        """Write to bash process.

        Same as print(), except flush defaults to True
        and file defaults to the bash stdin.
        """
        kwargs.setdefault('flush', True)
        kwargs.setdefault('file', self.stdin)
        try:
            print(*args, **kwargs)
        except Exception:
            traceback.print_exc()
        return self

    def __enter__(self):
        self.open()
        return self
    def __exit__(self, tp, exc, tb):
        self.close()
    def __del__(self):
        self.close()
    def __bool__(self):
        """Session still open."""
        return self.proc is not None and self.proc.poll() is None

if __name__ == '__main__':
    with Bash(stdout=None, stderr=None) as b:
        while b(input('>>> ')):
            pass
