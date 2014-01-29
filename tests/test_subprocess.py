from asyncio import subprocess
import asyncio
import os
import sys
import unittest

class SubprocessTestCase(unittest.TestCase):
    def setUp(self):
        policy = asyncio.get_event_loop_policy()
        if os.name == 'nt':
            self.loop = asyncio.ProactorEventLoop()
        else:
            self.loop = policy.new_event_loop()
        # ensure that the event loop is passed explicitly in the code
        policy.set_event_loop(None)

    def tearDown(self):
        policy = asyncio.get_event_loop_policy()
        self.loop.close()
        policy.set_child_watcher(None)

    def test_stdin_stdout(self):
        code = '; '.join((
            'import sys',
            'data = sys.stdin.buffer.read()',
            'sys.stdout.buffer.write(data)',
        ))
        args = [sys.executable, '-c', code]

        @asyncio.coroutine
        def run(data):
            proc = yield from asyncio.create_subprocess_exec(
                                          *args,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          loop=self.loop)

            # feed data
            proc.stdin.write(data)
            yield from proc.stdin.drain()
            proc.stdin.close()

            # get output and exitcode
            data = yield from proc.stdout.read()
            exitcode = yield from proc.wait()
            return (exitcode, data)

        task = run(b'some data')
        task = asyncio.wait_for(task, 10.0, loop=self.loop)
        exitcode, stdout = self.loop.run_until_complete(task)
        self.assertEqual(exitcode, 0)
        self.assertEqual(stdout, b'some data')

    def test_communicate(self):
        code = '; '.join((
            'import sys',
            'data = sys.stdin.buffer.read()',
            'sys.stdout.buffer.write(data)',
        ))
        args = [sys.executable, '-c', code]

        @asyncio.coroutine
        def run(data):
            proc = yield from asyncio.create_subprocess_exec(
                                          *args,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          loop=self.loop)
            stdout, stderr = yield from proc.communicate(data)
            return proc.returncode, stdout

        task = run(b'some data')
        task = asyncio.wait_for(task, 10.0, loop=self.loop)
        exitcode, stdout = self.loop.run_until_complete(task)
        self.assertEqual(exitcode, 0)
        self.assertEqual(stdout, b'some data')

    def test_get_subprocess(self):
        args = [sys.executable, '-c', 'pass']

        @asyncio.coroutine
        def run():
            proc = yield from asyncio.create_subprocess_exec(*args,
                                                             loop=self.loop)
            yield from proc.wait()

            popen = proc.get_subprocess()
            popen.wait()
            return (proc, popen)

        proc, popen = self.loop.run_until_complete(run())
        self.assertEqual(popen.returncode, proc.returncode)
        self.assertEqual(popen.pid, proc.pid)


if __name__ == '__main__':
    unittest.main()
