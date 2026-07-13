# Deploying Mandarin Coach to GCP (Docker + Compute Engine)

An always-on `e2-small` VM in **Melbourne (`australia-southeast2`)** running the app
behind Caddy (automatic HTTPS). The ChromaDB corpus persists on a Docker volume.

Why a VM and not Cloud Run: ChromaDB is SQLite-backed and needs a real local
filesystem, and an always-on VM has no cold starts (the usual cause of "GCP feels
slow"). Right-sized to `e2-small` with real vCPUs — not a throttled `e2-micro`.

---

## 0. Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- A GCP project with billing enabled
- Your API keys: `OPENROUTER_API_KEY` (required), `OPENAI_API_KEY` (recommended —
  keeps the image light by using OpenAI embeddings instead of a local model),
  optionally `TAVILY_API_KEY`, `LANGSMITH_API_KEY`

```bash
export PROJECT=your-gcp-project-id
gcloud config set project $PROJECT
gcloud config set compute/zone australia-southeast2-a

# One-time: enable the Compute Engine API on the project (the gcloud compute
# commands below call this API). Skip if it's already enabled.
gcloud services enable compute.googleapis.com
```

## 1. Firewall — allow HTTP/HTTPS

```bash
gcloud compute firewall-rules create allow-web \
  --direction=INGRESS --action=ALLOW \
  --rules=tcp:80,tcp:443 \
  --target-tags=http-server,https-server
```

## 2. Create the VM

```bash
gcloud compute instances create mandarin-coach \
  --machine-type=e2-small \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server
```

Get its external IP (used to form a free hostname via nip.io):

```bash
gcloud compute instances describe mandarin-coach \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
# e.g. 34.129.1.2  ->  hostname 34-129-1-2.nip.io
```

## 2b. Create and attach a persistent disk (durable storage)

A dedicated disk keeps the ChromaDB corpus + user accounts independent of the VM,
so they survive VM deletion and can be snapshotted.

```bash
gcloud compute disks create mandarin-data --size=10GB --type=pd-balanced
gcloud compute instances attach-disk mandarin-coach \
  --disk=mandarin-data --device-name=mandarin-data
```

On the VM, format (first time only) and mount it at `/mnt/mandarin-data`:

```bash
DEV=/dev/disk/by-id/google-mandarin-data
sudo blkid $DEV || sudo mkfs.ext4 -m 0 -F $DEV     # format only if empty
sudo mkdir -p /mnt/mandarin-data
sudo mount -o discard,defaults $DEV /mnt/mandarin-data
echo "UUID=$(sudo blkid -s UUID -o value $DEV) /mnt/mandarin-data ext4 discard,defaults,nofail 0 2" | sudo tee -a /etc/fstab
```

`docker-compose.yml` bind-mounts `/mnt/mandarin-data` into the container at
`/var/data` (override with `DATA_DIR` for other environments). Snapshot it with
`gcloud compute disks snapshot mandarin-data`.

## 3. SSH in and install Docker

```bash
gcloud compute ssh mandarin-coach
```

On the VM:

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker   # run docker without sudo
```

## 4. Get the code and configure secrets

```bash
git clone https://github.com/<you>/mandarin-coach.git
cd mandarin-coach

cat > .env <<'EOF'
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=
LANGSMITH_API_KEY=
SITE_ADDRESS=34-129-1-2.nip.io
EOF
```

Set `SITE_ADDRESS` to `<dashed-ip>.nip.io` (or your own domain pointed at the IP).

## 5. Launch

```bash
docker compose up -d --build
```

Caddy fetches a Let's Encrypt certificate automatically. Visit:

```
https://34-129-1-2.nip.io
```

Send a wrong sentence, then ask "what am I getting wrong?" — the corpus you build
persists on the `chroma-data` volume across restarts.

---

## Operating notes

- **Update after a push:** `git pull && docker compose up -d --build`
- **Upgrading the reference corpus (e.g. the Task 6 grammar 24→98 expansion):** `load_reference_data()`
  only seeds a collection when it is *empty*, so a running deployment on the persistent disk will
  **not** auto-pick-up new rules in `data/grammar_rules.json`. Force a rebuild after pulling:
  `docker compose exec app python -c "import sys; sys.path.insert(0,'app'); import memory; print(memory.load_reference_data(force=True))"`
  (⚠️ the live VM is currently on the original 24-rule corpus until this is run; user-authored
  `*_personal_errors` collections are untouched by the `force` rebuild — only the shared reference
  collections are re-seeded).
- **Logs:** `docker compose logs -f app`
- **Persistence:** the ChromaDB corpus + user accounts live on the `/mnt/mandarin-data`
  persistent disk, which survives VM deletion and `compose down`. Snapshot it with
  `gcloud compute disks snapshot mandarin-data` for backups.
- **Cost:** an always-on `e2-small` is roughly USD $13/mo. `gcloud compute
  instances stop mandarin-coach` when idle to pause billing (data is kept).
- **If nip.io TLS fails** (Let's Encrypt rate limits it occasionally): use
  `sslip.io` instead (`34-129-1-2.sslip.io`) or point a real domain at the IP.
- **RAM:** `e2-small` (2 GB) is fine with OpenAI embeddings. If you drop
  `OPENAI_API_KEY` and use the local embedding model, use `e2-medium` (4 GB).
