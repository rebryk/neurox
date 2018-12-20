import asyncio
import shlex
import subprocess
import sys
from collections import namedtuple
from functools import wraps
from typing import List, Any, Callable

from neuromation.cli.rc import ConfigFactory
from neuromation.cli.ssh_utils import remote_debug
from neuromation.clientv2 import ClientV2
from neuromation.clientv2.jobs import JobDescription

from neurox.ssh_utils import connect_ssh

StatusUpdate = namedtuple('StatusUpdate', ['job_id', 'status'])
NewJobUpdate = namedtuple('NewJobUpdate', ['job_id', 'status'])


def sync_wait(future: Callable) -> Callable:
    @wraps(future)
    def wrapper(*args, **kwargs) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(future(*args, **kwargs))

    return wrapper


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
    @sync_wait
    async def job_kill(job_id: str):
        config = ConfigFactory.load()

        if not config.url:
            raise ValueError('Specify API URL! See for more info `neuro config`.')

        if not config.auth:
            raise ValueError('Specify API token! See for more info `neuro config`.')

        async with ClientV2(config.url, config.auth) as api:
            await api.jobs.kill(job_id)

    @staticmethod
    @sync_wait
    async def job_list() -> List[JobDescription]:
        config = ConfigFactory.load()

        if not config.url:
            raise ValueError('Specify API URL! See for more info `neuro config`.')

        if not config.auth:
            raise ValueError('Specify API token! See for more info `neuro config`.')

        async with ClientV2(config.url, config.auth) as api:
            return await api.jobs.list()

    @staticmethod
    @sync_wait
    async def connect_ssh(job_id: str, tmp_file: str):
        config = ConfigFactory.load()
        rsa_path = config.github_rsa_path
        username = config.get_platform_user_name()

        async with ClientV2(config.url, config.auth) as client:
            await connect_ssh(client, username, job_id, rsa_path, 'root', rsa_path, tmp_file)

    @staticmethod
    @sync_wait
    async def remote_debug(job_id: str, local_port: int):
        config = ConfigFactory.load()
        rsa_path = config.github_rsa_path
        username = config.get_platform_user_name()

        async with ClientV2(config.url, config.auth) as client:
            await remote_debug(client, username, job_id, rsa_path, local_port)

    @staticmethod
    def submit_raw(params: str):
        # TODO: use JobHandlerOperations instead of it
        args = shlex.split(f'neuro job submit {params}')

        process = subprocess.Popen(args, stdout=sys.stdout)
        process.communicate()

        if process.returncode != 0:
            raise ValueError('You may be using the wrong parameters!')
