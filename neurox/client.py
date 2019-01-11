import asyncio
import shlex
import subprocess
from collections import namedtuple
from functools import wraps
from typing import List, Any, Callable

import aiofiles as aiof
import aiohttp
from neuromation.cli.commands import dispatch
from neuromation.cli.defaults import DEFAULTS
from neuromation.cli.main import neuro
from neuromation.cli.ssh_utils import remote_debug
from neuromation.clientv2 import ClientV2
from neuromation.clientv2.jobs import JobDescription, JobStatus

from neurox.ssh_utils import connect_ssh

StatusUpdate = namedtuple('StatusUpdate', ['job_id', 'status', 'reason'])
NewJobUpdate = namedtuple('NewJobUpdate', ['job_id', 'status', 'reason'])


def sync_wait(future: Callable) -> Callable:
    @wraps(future)
    def wrapper(*args, **kwargs) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(future(*args, **kwargs))

    return wrapper


class NeuroxClient:
    def __init__(self):
        self._jobs = None
        self._username = None
        self._auth = None
        self._url = None
        self._rsa_path = None

    def update_username(self, username: str):
        self._username = username

    def update_auth(self, auth: str):
        self._auth = auth

    def update_url(self, url: str):
        self._url = url

    def update_rsa_path(self, rsa_path: str):
        self._rsa_path = rsa_path

    def update(self) -> List[StatusUpdate or NewJobUpdate]:
        updates = []
        jobs = {it.id: it for it in self.job_list()}

        if self._jobs is None:
            self._jobs = jobs
            return updates

        # update old job statuses
        for job_id, job in self._jobs.items():
            if job_id not in jobs:
                raise RuntimeError(f'Job `{job_id}` is not presented in job history!')

            new_job = jobs[job_id]

            if job.status != new_job.status:
                self._jobs[job_id] = new_job
                name = new_job.description if new_job.description else job_id
                reason = new_job.history.reason if new_job.status == JobStatus.FAILED else None
                updates.append(StatusUpdate(name, new_job.status, reason))

        # update new job statuses
        for job_id, new_job in jobs.items():
            if job_id in self._jobs:
                continue

            self._jobs[job_id] = new_job
            name = new_job.description if new_job.description else job_id
            reason = new_job.history.reason if new_job.status == JobStatus.FAILED else None
            updates.append(NewJobUpdate(name, new_job.status, reason))

        return updates

    def get_active_jobs(self) -> List[JobDescription]:
        jobs = self._jobs.values() if self._jobs else []
        return list(filter(lambda it: it.status in [JobStatus.PENDING, JobStatus.RUNNING], jobs))

    @sync_wait
    async def job_kill(self, job_id: str):
        if not self._url:
            raise ValueError('Specify neuromation API URL!')

        if not self._auth:
            raise ValueError('Specify neuromation API token!')

        async with ClientV2(self._url, self._auth) as api:
            await api.jobs.kill(job_id)

    @sync_wait
    async def job_list(self) -> List[JobDescription]:
        if not self._url:
            raise ValueError('Specify neuromation API URL!')

        if not self._auth:
            raise ValueError('Specify neuromation API token!')

        async with ClientV2(self._url, self._auth) as api:
            return await api.jobs.list()

    @sync_wait
    async def monitor(self, job_id: str, tmp_file: str) -> Any:
        if not self._url:
            raise ValueError('Specify neuromation API URL!')

        if not self._auth:
            raise ValueError('Specify neuromation API token!')

        timeout = aiohttp.ClientTimeout(None, None, 1, 5)

        async with ClientV2(self._url, self._auth, timeout=timeout) as api:
            try:
                async with aiof.open(tmp_file, 'w') as file:
                    try:
                        async for data in api.jobs.monitor(job_id):
                            await file.write(data.decode('utf-8'))
                    except:
                        # Nothing to read.
                        pass

                proc = await asyncio.create_subprocess_exec('open', tmp_file)
                await proc.wait()
            except subprocess.CalledProcessError as e:
                pass

    @sync_wait
    async def connect_ssh(self, job_id: str, tmp_file: str):
        if not self._username:
            raise ValueError('Specify neuromation username!')

        async with ClientV2(self._url, self._auth) as client:
            await connect_ssh(client, self._username, job_id, self._rsa_path, 'root', self._rsa_path, tmp_file)

    @sync_wait
    async def remote_debug(self, job_id: str, local_port: int):
        if not self._username:
            raise ValueError('Specify neuromation username!')

        async with ClientV2(self._url, self._auth) as client:
            await remote_debug(client, self._username, job_id, self._rsa_path, local_port)

    def submit_raw(self, params: str):
        args = shlex.split(f'job submit {params}')
        format_spec = DEFAULTS.copy()

        if self._username:
            format_spec['username'] = self._username

        if self._url:
            format_spec['api_url'] = self._url

        # Save initial event loop, because `dispatch` changes it.
        loop = asyncio.get_event_loop()

        try:
            dispatch(target=neuro, tail=args, format_spec=format_spec, token=self._auth)
        finally:
            # Restore initial event loop, because `dispatch` changes it.
            asyncio.set_event_loop(loop)
