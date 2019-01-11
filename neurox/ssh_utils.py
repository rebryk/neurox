import asyncio
import subprocess

import aiofiles as aiof
import aiohttp
from neuromation.cli.ssh_utils import _validate_args_for_ssh_session
from neuromation.cli.ssh_utils import _validate_job_status_for_ssh_session
from neuromation.clientv2 import ClientV2
from neuromation.clientv2.jobs import JobDescription

from neurox.utils import make_executable


async def _connect_ssh(
        username: str,
        job_status: JobDescription,
        jump_host_key: str,
        container_user: str,
        container_key: str,
        tmp_file: str):
    _validate_job_status_for_ssh_session(job_status)
    # We shall make an attempt to connect only in case it has SSH
    ssh_hostname = job_status.jump_host()
    if not ssh_hostname:
        raise RuntimeError('Job has no SSH server enabled')

    proxy_command = f'\"ProxyCommand=ssh -i {jump_host_key} {username}@{ssh_hostname} nc {job_status.id} 22\"'
    command = f'ssh -o {proxy_command} -i {container_key} {container_user}@{job_status.id}'

    try:
        async with aiof.open(tmp_file, 'w') as file:
            await file.write(command)

        make_executable(tmp_file)
        proc = await asyncio.create_subprocess_exec('open', tmp_file)
        await proc.wait()
    except subprocess.CalledProcessError as e:
        pass


async def connect_ssh(
        client: ClientV2,
        username: str,
        job_id: str,
        jump_host_key: str,
        container_user: str,
        container_key: str,
        tmp_file: str):
    _validate_args_for_ssh_session(container_user, container_key, jump_host_key)
    # Check if job is running
    try:
        job_status = await client.jobs.status(job_id)
    except aiohttp.ClientError as e:
        raise ValueError(f'Job not found. Job Id = {job_id}') from e
    await _connect_ssh(username, job_status, jump_host_key, container_user, container_key, tmp_file)
