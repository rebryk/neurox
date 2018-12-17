import subprocess
from collections import namedtuple, OrderedDict

from neuromation.cli.rc import ConfigFactory
from neuromation.client.jobs import Job, JobDescription

StatusUpdate = namedtuple('StatusUpdate', ['job_id', 'status'])
NewJobUpdate = namedtuple('NewJobUpdate', ['job_id', 'status'])


class NeuroxClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.job = Job(url, self.token)

        config = ConfigFactory.load()
        self.git_key = config.github_rsa_path
        self.auth = config.auth
        self.user_name = config.get_platform_user_name()

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

    def connect_ssh(self, job: JobDescription) -> str:
        proxy_command = f'\"ProxyCommand=ssh -i {self.git_key} {self.user_name}@{job.jump_host()} nc {job.id} 22\"'
        command = f'ssh -o {proxy_command} -i {self.git_key} root@{job.id}'
        return command

    @staticmethod
    def submit_raw(params: str):
        args = f'neuro job submit {params}'.split()
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        out, err = process.communicate()
        return process.returncode, out, err

    def _job_list(self) -> OrderedDict:
        return OrderedDict({job.id: job for job in self.job.list()})
