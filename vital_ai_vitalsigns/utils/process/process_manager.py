import subprocess
import psutil
import os
import threading
import time

# TODO switch to logging
# start/stop processes
# use for jvm and fuseki memory service
# fuseki-server is a shell script
# ./fuseki-server --mem /graph


class ProcessManager:
    def __init__(self):
        self.processes = {}

    def start_process(self, name, script_path, java_home, working_directory):
        env = os.environ.copy()
        env['JAVA_HOME'] = java_home

        process = subprocess.Popen(['bash', script_path], env=env, cwd=working_directory,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.processes[name] = process

        threading.Thread(target=self._monitor_output, args=(name, process.stdout, 'stdout')).start()
        threading.Thread(target=self._monitor_output, args=(name, process.stderr, 'stderr')).start()

        print(f"Started process {name} with PID {process.pid}")
        return process

    def _monitor_output(self, name, stream, stream_type):
        for line in iter(stream.readline, ''):
            print(f"[{name}][{stream_type}] {line.strip()}")
        stream.close()

    def stop_process(self, name):
        process = self.processes.get(name)
        if process:
            process.terminate()
            print(f"Terminated process {name}")
        else:
            print(f"No such process: {name}")

    def kill_process(self, name):
        process = self.processes.get(name)
        if process:
            process.kill()
            print(f"Killed process {name}")
        else:
            print(f"No such process: {name}")

    def restart_process(self, name, script_path, java_home_path, working_directory):
        self.stop_process(name)
        time.sleep(2)  # wait a bit for the process to terminate properly
        self.start_process(name, script_path, java_home_path, working_directory)
        print(f"Restarted process {name}")

    def get_process_info(self, name):
        process = self.processes.get(name)
        if process and psutil.pid_exists(process.pid):
            p = psutil.Process(process.pid)
            return {
                "pid": p.pid,
                "name": p.name(),
                "status": p.status(),
                "cpu_percent": p.cpu_percent(interval=1.0),
                "memory_info": p.memory_info()._asdict()
            }
        else:
            return f"No such process: {name}"

    def get_all_processes(self):
        return {name: self.get_process_info(name) for name in self.processes}
