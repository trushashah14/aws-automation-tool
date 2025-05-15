# Name of your Docker image
IMAGE_NAME=aws-cli-tool

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run CLI tool (e.g. help command)
run:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME)


# Run an actual command, e.g. list EC2
create-instances:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) create

list-instances:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) list
start-instance:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials  $(IMAGE_NAME) start --instance-id $(id)

stop-instance:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) stop --instance-id $(id)

terminate-instance:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) terminate --instance-id $(id)

# S3 Operations
list-buckets:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials  $(IMAGE_NAME) s3-bucket-list

list-objects:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) s3-file-list

create-bucket:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) s3-create

upload-object:
	docker run --rm -it -v ${PWD}:/app -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) s3-file-upload --file-path $(file)

delete-object:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) s3-file-delete --file-names $(key)

delete-bucket:
	docker run --rm -it -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) s3-delete

download-object:
	docker run --rm -it -v ${PWD}:/app -v ${PWD}/config.yaml:/app/config.yaml -v C:/Users/behip/.aws/credentials:/root/.aws/credentials $(IMAGE_NAME) s3-file-download --file-names $(file)

# Clean up Docker image
clean:
	docker rmi -f $(IMAGE_NAME)

# Help
help:
	@echo "Available commands:"
	@echo "  make build                 Build the Docker image"
	@echo "  make run                   Run CLI interactively"
	@echo "  make create-instances      Create an ec2 instance "
	@echo "  make list-instances        List running EC2 instances"
	@echo "  make start-instance id=iid Start EC2 instance (pass id=...)"
	@echo "  make stop-instance id=iid  Stop EC2 instance (pass id=...)"
	@echo "  make terminate-instance id=iid Terminate EC2 instance"
	@echo "  make create-bucket          create S3 buckets"
	@echo "  make list-buckets          List S3 buckets"
	@echo "  make list-objects          Lists objects in S3 bucket configured in config.yaml"
	@echo "  make upload-object  file=path     Upload files to S3 buckets"
	@echo "  make delete-object  key=\"key1 key2\"    Delete sepcified objects from s3 bucket"
	@echo "  make download-object key=\"key1 key2\"    Download specified objects from s3 bucket"
	@echo "  make delete-bucket    Deletes the bucket configured in config.yaml"
	@echo "  make clean                 Remove Docker image"