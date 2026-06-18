# Manual backend deployment

The application uses one `t3.medium` EC2 host:

```text
EC2 host
├── /home/ubuntu/leetcode       Git checkout and Python virtual environment
├── leetcode-api.service        FastAPI on 127.0.0.1:8000
├── leetcode-worker.service     Redis consumer and Docker launcher
├── redis-server.service        Submission queue and status updates
├── docker.service              Host container runtime
└── leetcode-judge:latest       Immutable judge image
    └── short-lived container   One per submission
```

The backend itself runs as host `systemd` services. It is deliberately not put
inside Docker because the worker needs to launch judge containers; mounting the
host Docker socket into a backend container would grant that container
host-equivalent control.

## First deployment

After cloning the repository and creating `.env`, run:

```bash
chmod +x deploy/*.sh docker/build-judge.sh
./deploy/bootstrap-backend.sh
```

This installs dependencies, runs tests, builds and smoke-tests the judge image,
seeds demo data, and installs Nginx plus the API and worker services.

## Later deployments

```bash
./deploy/update-backend.sh
```

The SQLite database lives in `/home/ubuntu/leetcode/data` and is not replaced by
Git updates. Seeding is idempotent.

## Useful commands on EC2

```bash
sudo systemctl status leetcode-api leetcode-worker
sudo journalctl -u leetcode-api -f
sudo journalctl -u leetcode-worker -f
curl http://127.0.0.1:8000/docs
curl http://127.0.0.1/docs
docker ps --filter name=leetcode-judge
```
