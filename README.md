# 🚀 AWS Automation Tool

A CLI-based AWS EC2 and S3 automation tool using Python, Boto3, and Docker. This project allows you to manage EC2 instances and S3 buckets/files directly from your terminal using Makefile commands or by running the tool inside a Docker container.

---

## ⚙️ Prerequisites

Make sure the following are set up **before cloning** the repository:

### ✅ Install Docker

- **Windows:** [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **macOS:** [Download Docker for Mac](https://www.docker.com/products/docker-desktop/)

### ✅ Configure AWS Credentials

Create the AWS credentials file to allow the CLI tool to authenticate with your AWS account.

#### 🔐 On Windows:

Create the file at:

```
C:\Users\<YourUsername>\.aws\credentials
```

#### 🔐 On macOS/Linux:

Create the file at:

```
~/.aws/credentials
```

Add the following format to the file:

```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

---

## 📥 Clone the Repository

```bash
git clone https://github.com/trushashah14/aws-automation-tool.git
cd aws-automation-tool
```

---

## 🛠️ Configure Your `config.yaml`

Edit `config.yaml` in the root directory with your desired AWS setup:

```yaml
aws:
  region_name: us-east-2
  instance_type: t2.micro
  ami_id: ami-04f167a56786e4b09
  key_name: my-key-pair
  security_group_name: my-security-group
  security_group_description: Security group for EC2 automation
  instance_name: my-ec2-instance

s3:
  bucket_name: ts-automation-bucket
  region_name: us-east-2
```

---

## 🧱 Build the Docker Image

```bash
make build
```

This uses the Dockerfile to install all Python dependencies from `requirements.txt`.

---

## 🚀 Run the Tool

### Option 1: Enter Docker container and use Python CLI

```bash
make run
```

Inside the container, run:

```bash
python main.py create
python main.py list
python main.py start --instance-id i-0123456789abcdef0
python main.py s3-file-upload --file-path README.md
```

### Option 2: Use Makefile Commands Directly

```bash
make create-instances    # 🚀 Launch a new EC2 instance
make list-instances            # 📄 List all running EC2 instances
make stop-instance id=...      # ⏹️ Stop an EC2 instance
make start-instance id=...     # ▶️ Start a stopped EC2 instance
make terminate-instance id=... # ❌ Terminate an EC2 instance

make create-bucket             # 🪣 Create the configured S3 bucket
make list-buckets              # 📋 List all S3 buckets
make list-objects              # 📦 List all objects in the S3 bucket
make upload-object file=...    # ⬆️ Upload a file to the S3 bucket
make download-object key=...   # ⬇️ Download a file from the S3 bucket
make delete-object key=...     # 🗑️ Delete file(s) from the S3 bucket
make delete-bucket             # 🪣 Delete the configured S3 bucket

make clean                     # 🧹 Stop and remove all containers/images
```
💡 Replace `...` with actual values (e.g., instance ID, file name).

### 🔁 Multi-File Support
You can update,  download or delete multiple files at once by wrapping them in quotes:

```bash
make delete-object obj="obj1 obj2"
make download-object obj="obj1 obj2"
make upload-object obj="obj1 obj2"
```
Same applies to python main.py commands inside the container.

---

## 📃 License

MIT License. Use freely with attribution. Contributions welcome!
