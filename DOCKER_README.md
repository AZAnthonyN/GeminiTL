# GeminiTL Docker Deployment for Raspberry Pi 5

This guide explains how to run GeminiTL in a Docker container on Raspberry Pi 5 (ARM64 architecture).

## 🎯 Why Docker on Raspberry Pi 5?

- **Isolated Environment**: Keep dependencies contained
- **Easy Deployment**: One-command setup
- **Reproducible**: Same environment every time
- **Resource Efficient**: Optimized for ARM64 architecture
- **Headless Operation**: Perfect for CLI-only usage on Raspberry Pi

## 📋 Prerequisites

### Hardware Requirements
- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- **Storage**: At least 16GB SD card (32GB+ recommended)
- **Internet Connection**: For downloading dependencies and API calls

### Software Requirements
1. **Raspberry Pi OS** (64-bit, Bookworm or later)
2. **Docker** and **Docker Compose** installed

## 🚀 Quick Start

### Step 1: Install Docker on Raspberry Pi 5

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version

# Reboot to apply group changes
sudo reboot
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/yourusername/GeminiTL.git
cd GeminiTL
```

### Step 3: Configure API Keys

Create a `.env` file in the project root:

```bash
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
EOF
```

For Google Gemini, place your service account JSON in `src/config/service_account.json`.

### Step 4: Build the Docker Image

```bash
# Build for ARM64 (Raspberry Pi 5)
docker build -t geminitl:latest .

# This may take 15-30 minutes on first build
```

### Step 5: Run the Container

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using Docker directly
docker run -it \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/compiled_epubs:/app/compiled_epubs \
  -v $(pwd)/src/config:/app/src/config \
  --env-file .env \
  geminitl:latest
```

## 📖 Usage Examples

### Basic Commands

```bash
# Show help
docker-compose run --rm geminitl python main.py --help

# Separate EPUB
docker-compose run --rm geminitl \
  python main.py epub-separate /app/input/novel.epub /app/input

# Run translation
docker-compose run --rm geminitl \
  python main.py translate --source-lang Japanese --provider openai

# Run proofing
docker-compose run --rm geminitl \
  python main.py proof

# Combine to EPUB
docker-compose run --rm geminitl \
  python main.py epub-combine /app/output /app/compiled_epubs/translated.epub
```

### Complete Workflow

```bash
# 1. Place your EPUB in the input directory
cp your-novel.epub input/

# 2. Extract chapters
docker-compose run --rm geminitl \
  python main.py epub-separate /app/input/your-novel.epub /app/input

# 3. Translate
docker-compose run --rm geminitl \
  python main.py translate --source-lang Japanese --provider gemini

# 4. Proof
docker-compose run --rm geminitl \
  python main.py proof

# 5. Create final EPUB
docker-compose run --rm geminitl \
  python main.py epub-combine /app/output /app/compiled_epubs/translated-novel.epub

# 6. Get the result
cp compiled_epubs/translated-novel.epub ~/
```

### Interactive Shell

```bash
# Enter container for manual operations
docker-compose run --rm geminitl /bin/bash

# Inside container:
python main.py translate --help
python main.py translate --source-lang Japanese
exit
```

## 🔧 Configuration

### Volume Mappings

The Docker setup uses these volume mappings:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./input` | `/app/input` | Input text/EPUB files |
| `./output` | `/app/output` | Translated output |
| `./compiled_epubs` | `/app/compiled_epubs` | Final EPUB files |
| `./src/config` | `/app/src/config` | Configuration files |
| `./translation/glossary` | `/app/translation/glossary` | Glossary files |

### Environment Variables

Set these in your `.env` file or docker-compose.yml:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=/app/src/config/service_account.json
```

### Resource Limits

The docker-compose.yml includes resource limits optimized for Raspberry Pi 5:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Use all 4 cores
      memory: 6G       # Leave 2GB for system
```

Adjust these based on your Raspberry Pi 5 model (4GB or 8GB RAM).

## 🎛️ Advanced Usage

### Custom Build Arguments

```bash
# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t geminitl:latest .
```

### Running in Background

```bash
# Start container in detached mode
docker-compose up -d

# View logs
docker-compose logs -f geminitl

# Stop container
docker-compose down
```

### Using Named Volumes

Edit `docker-compose.yml` to use named volumes instead of bind mounts:

```yaml
volumes:
  - input_data:/app/input
  - output_data:/app/output
```

This keeps data in Docker-managed volumes.

## 🐛 Troubleshooting

### Build Issues

**Problem**: Build fails with "no space left on device"
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

**Problem**: Build is very slow
```bash
# This is normal on Raspberry Pi 5. First build takes 15-30 minutes.
# Subsequent builds use cache and are much faster.
```

**Problem**: Package installation fails
```bash
# Try building with more memory
# Edit /etc/dphys-swapfile and increase CONF_SWAPSIZE to 2048
sudo nano /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Runtime Issues

**Problem**: Container exits immediately
```bash
# Check logs
docker-compose logs geminitl

# Run with interactive shell
docker-compose run --rm geminitl /bin/bash
```

**Problem**: Permission denied errors
```bash
# Fix permissions on host
sudo chown -R $USER:$USER input output compiled_epubs

# Or run container as root (not recommended)
docker-compose run --rm --user root geminitl /bin/bash
```

**Problem**: API authentication fails
```bash
# Verify environment variables
docker-compose run --rm geminitl env | grep API_KEY

# Check service account file exists
docker-compose run --rm geminitl ls -la /app/src/config/
```

### Performance Issues

**Problem**: Translation is slow
```bash
# Monitor resource usage
docker stats geminitl-translator

# Increase resource limits in docker-compose.yml
# Or close other applications to free up RAM
```

**Problem**: Out of memory errors
```bash
# Reduce memory usage by processing fewer chapters at once
# Or upgrade to Raspberry Pi 5 with 8GB RAM
```

## 📊 Performance Optimization

### For Raspberry Pi 5 (4GB RAM)

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '3.0'
      memory: 3G
```

### For Raspberry Pi 5 (8GB RAM)

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 6G
```

### Reduce Image Size

```bash
# Use multi-stage build (advanced)
# Edit Dockerfile to use multi-stage builds
# This can reduce image size by 30-50%
```

## 🔒 Security Best Practices

1. **Don't commit API keys**:
   ```bash
   # Add .env to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use secrets for production**:
   ```bash
   # Use Docker secrets instead of environment variables
   docker secret create openai_key openai_key.txt
   ```

3. **Run as non-root user**:
   ```bash
   # Already configured in Dockerfile
   USER geminitl
   ```

4. **Keep images updated**:
   ```bash
   # Rebuild regularly to get security updates
   docker-compose build --no-cache
   ```

## 📦 Backup and Restore

### Backup Data

```bash
# Backup volumes
docker run --rm \
  -v geminitl_input_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/input-backup.tar.gz /data

# Backup configuration
tar czf config-backup.tar.gz src/config/
```

### Restore Data

```bash
# Restore volumes
docker run --rm \
  -v geminitl_input_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/input-backup.tar.gz -C /

# Restore configuration
tar xzf config-backup.tar.gz
```

## 🚀 Automation

### Cron Job for Scheduled Translation

```bash
# Edit crontab
crontab -e

# Add line to run translation daily at 2 AM
0 2 * * * cd /home/pi/GeminiTL && docker-compose run --rm geminitl python main.py translate >> /var/log/geminitl.log 2>&1
```

### Batch Processing Script

```bash
#!/bin/bash
# batch-translate.sh

for epub in input/*.epub; do
  echo "Processing $epub..."
  docker-compose run --rm geminitl \
    python main.py epub-separate "/app/$epub" /app/input

  docker-compose run --rm geminitl \
    python main.py translate --source-lang Japanese

  docker-compose run --rm geminitl \
    python main.py proof

  output_name=$(basename "$epub" .epub)
  docker-compose run --rm geminitl \
    python main.py epub-combine /app/output "/app/compiled_epubs/translated-${output_name}.epub"
done
```

## 🔄 Updates and Maintenance

### Update the Application

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build --no-cache

# Restart container
docker-compose down
docker-compose up -d
```

### Clean Up Old Images

```bash
# Remove unused images
docker image prune -a

# Remove all stopped containers
docker container prune

# Full cleanup
docker system prune -a --volumes
```

## 📝 Tips for Raspberry Pi 5

1. **Use SSD instead of SD card** for better I/O performance
2. **Enable swap** if you have 4GB RAM model
3. **Monitor temperature**: `vcgencmd measure_temp`
4. **Use active cooling** for sustained workloads
5. **Overclock cautiously** if needed for better performance

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify configuration: `docker-compose config`
3. Test connectivity: `docker-compose run --rm geminitl ping -c 3 google.com`
4. Check resources: `docker stats`
5. Review main README.md and CLI_README.md

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [GeminiTL Main README](README.md)
- [GeminiTL CLI Guide](CLI_README.md)
- [Multi-Provider Setup](MULTI_PROVIDER_README.md)

## ⚠️ Limitations

- **No GUI support** in Docker (CLI only)
- **ARM64 only** - optimized for Raspberry Pi 5
- **Resource intensive** - translation requires significant RAM
- **Network dependent** - requires internet for API calls

---

**Note**: This Docker setup is optimized for Raspberry Pi 5 (ARM64). For other platforms, you may need to adjust the Dockerfile.

