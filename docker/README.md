# Docker judge on a small EC2 instance

This is the judge backend for the project's `t3.medium` deployment.
Each submission runs in a fresh container and the container is removed after it
returns a result.

## Security boundary

The worker starts judge containers with:

- no network namespace connectivity;
- a read-only root filesystem;
- no Linux capabilities;
- Docker's default seccomp profile;
- `no-new-privileges`;
- a fixed unprivileged UID/GID (`65532:65532`);
- fixed memory, CPU, PID, file-descriptor, output, and wall-clock limits;
- a bounded memory-backed `/tmp`;
- no host bind mounts and no Docker socket inside the container.

Docker containers share the EC2 host kernel. This is practical for a small,
controlled project, but it is not a virtual-machine isolation boundary. Keep
Docker and the Ubuntu kernel patched.

## Local or EC2 setup

Install and start Docker, then build the judge image:

```bash
chmod +x docker/build-judge.sh
./docker/build-judge.sh
```

Run a real container smoke test:

```bash
python -m backend.docker_smoke_test
```

Copy the example environment file and fill in the admin credentials:

```bash
cp .env.docker.example .env
```

Generate a session secret and replace the placeholder:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Start Redis and run one worker process:

```bash
python -m backend.worker
```

One worker processes one submission at a time. Do not launch multiple workers on
a `t3.medium` unless you deliberately lower per-container resources.

## Configuration

```dotenv
JUDGE_EXECUTOR=docker
JUDGE_DOCKER_IMAGE=leetcode-judge:latest
JUDGE_DOCKER_MEMORY=512m
JUDGE_DOCKER_CPUS=1.0
JUDGE_DOCKER_PIDS_LIMIT=128
JUDGE_DOCKER_TMPFS_SIZE=384m
JUDGE_DOCKER_TIMEOUT_SECONDS=45
```

The image contains Python, C++, Java, and JavaScript. It is built once during
deployment, not once per submission.

## Operational checks

List running judge containers:

```bash
docker ps --filter name=leetcode-judge
```

The list should normally be empty between submissions. Remove a stale container:

```bash
docker rm --force CONTAINER_NAME
```

Inspect image size:

```bash
docker image ls leetcode-judge
```

Never expose the Docker daemon TCP port or mount `/var/run/docker.sock` into the
API, frontend, or judge container.
