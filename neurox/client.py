import subprocess
from collections import namedtuple
from functools import partial
from typing import List

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
    def __init__(self):
        self._jobs = None

    def update(self) -> List[StatusUpdate or NewJobUpdate]:
        updates = []
        jobs = {it.id: it for it in self.job_list()}

        if self._jobs is None:
            self._jobs = jobs
            return updates

        # update old job statuses
        for job in self._jobs.values():
            if job.id not in jobs:
                raise RuntimeError(f'Job `{job.id}` is not presented in job history!')

            if job.status != jobs[job.id].status:
                self._jobs[job.id] = jobs[job.id]
                updates.append(StatusUpdate(job.id, jobs[job.id].status))

        # update new job statuses
        for job in jobs.values():
            if job.id in self._jobs:
                continue

            self._jobs[job.id] = job
            updates.append(NewJobUpdate(job.id, job.status))

        return updates

    def get_active_jobs(self) -> List[JobDescription]:
        jobs = self._jobs.values() if self._jobs else []
        return list(filter(lambda it: it.status in ['pending', 'running'], jobs))

    @staticmethod
    def job_kill(job_id: str):
        config = ConfigFactory.load()

        if not config.url:
            raise ValueError('Specify API URL! See for more info `neuro config`.')

        if not config.auth:
            raise ValueError('Specify API token! See for more info `neuro config`.')

        with Job(config.url, config.auth) as job:
            job.kill(job_id)

    @staticmethod
    def job_list() -> List[JobDescription]:
        config = ConfigFactory.load()

        if not config.url:
            raise ValueError('Specify API URL! See for more info `neuro config`.')

        if not config.auth:
            raise ValueError('Specify API token! See for more info `neuro config`.')

        with Job(config.url, config.auth) as job:
            return job.list()

    @staticmethod
    def connect_ssh(job_id: str, tmp_file: str):
        config = ConfigFactory.load()
        rsa_path = config.github_rsa_path
        user_name = config.get_platform_user_name()
        jobs = partial(Job, config.url, config.auth)
        JobHandlerOperations(user_name, tmp_file).connect_ssh(job_id, rsa_path, 'root', rsa_path, jobs)

    @staticmethod
    def remote_debug(job_id: str, local_port: int):
        config = ConfigFactory.load()
        rsa_path = config.github_rsa_path
        user_name = config.get_platform_user_name()
        jobs = partial(Job, config.url, config.auth)
        JobHandlerOperations(user_name).python_remote_debug(job_id, rsa_path, local_port, jobs)

    @staticmethod
    def submit_raw(params: str):
        # TODO: use JobHandlerOperations instead of it
        args = f'neuro job submit {params}'.split()
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        process.communicate()

        if process.returncode != 0:
            raise ValueError('You may be using the wrong parameters!')
