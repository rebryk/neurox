import subprocess
from collections import namedtuple, OrderedDict
from functools import partial

import neuromation.cli.command_handlers as command_handlers
from neuromation.cli.rc import ConfigFactory
from neuromation.client.jobs import Job, JobDescription

from neurox.utils import make_executable

StatusUpdate = namedtuple('StatusUpdate', ['job_id', 'status'])
NewJobUpdate = namedtuple('NewJobUpdate', ['job_id', 'status'])


class JobHandlerOperations(command_handlers.JobHandlerOperations):
    def __init__(self, principal: str, tmp_file: str = None):
        super().__init__(principal)
        self.tmp_file = tmp_file

    def start_ssh(self,
                  job_id: str,
                  jump_host: str,
                  jump_user: str,
                  jump_key: str,
                  container_user: str,
                  container_key: str):
        proxy_command = f'\"ProxyCommand=ssh -i {jump_key} {jump_user}@{jump_host} nc {job_id} 22\"'
        command = f'ssh -o {proxy_command} -i {container_key} {container_user}@{job_id}'

        try:
            with open(self.tmp_file, 'w') as file:
                file.write(command)

            make_executable(self.tmp_file)
            subprocess.call(args=['open', self.tmp_file])
        except subprocess.CalledProcessError as e:
            pass

        return None


class NeuroxClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.job = Job(url, self.token)
        self.jobs = self._job_list()

    def update(self) -> [StatusUpdate or NewJobUpdate]:
        updates = []
        jobs = self._job_list()

        # update old job statuses
        for job in self.jobs.values():
            if job.id not in jobs:
                raise RuntimeError(f'Job `{job.id}` is not presented in job history!')

            if job.status != jobs[job.id].status:
                self.jobs[job.id] = jobs[job.id]
                updates.append(StatusUpdate(job.id, jobs[job.id].status))

        # update new job statuses
        for job in jobs.values():
            if job.id in self.jobs:
                continue

            self.jobs[job.id] = job
            updates.append(NewJobUpdate(job.id, job.status))

        return updates

    def kill(self, job_id: str):
        self.job.kill(job_id)

    def get_active_jobs(self) -> [JobDescription]:
        return list(filter(lambda it: it.status in ['pending', 'running'], self.jobs.values()))

    def connect_ssh(self, job_id: str, tmp_file: str):
        config = ConfigFactory.load()
        git_key = config.github_rsa_path
        user_name = config.get_platform_user_name()
        jobs = partial(Job, self.url, self.token)
        JobHandlerOperations(user_name, tmp_file).connect_ssh(job_id, git_key, 'root', git_key, jobs)

    def remote_debug(self, job_id: str, local_port: int = 1489):
        config = ConfigFactory.load()
        git_key = config.github_rsa_path
        user_name = config.get_platform_user_name()
        jobs = partial(Job, self.url, self.token)
        JobHandlerOperations(user_name).python_remote_debug(job_id, git_key, local_port, jobs)

    @staticmethod
    def submit_raw(params: str):
        # TODO: use JobHandlerOperations instead of it
        args = f'neuro job submit {params}'.split()
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = process.communicate()
        return process.returncode, out, err

    def _job_list(self) -> OrderedDict:
        return OrderedDict({job.id: job for job in self.job.list()})
