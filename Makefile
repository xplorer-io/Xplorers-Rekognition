
SHELL = /bin/bash
SHELLFLAGS = -ex

branch := $(shell git rev-parse --abbrev-ref HEAD)
git_repo := $(shell env | grep GITHUB_REPO | cut -d "=" -f2)
git_token := $(shell aws ssm get-parameter --name /github/sshkey --with-decryption --output text --query Parameter.Value)

deploy-vpc:
	$(info [+] Deploying 3 tier VPC...)
	@aws cloudformation deploy \
		--template-file cfn/3tier-vpc.yml \
		--stack-name three-tier-vpc \
		--capabilities CAPABILITY_NAMED_IAM

deploy-pipeline:
	$(info [+] Deploying CFN stack for Codepipeline...)
	@aws cloudformation deploy \
		--template-file cfn/pipeline.yml \
		--stack-name xplorers-rekognition-$(branch) \
		--capabilities CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			GithubRepo=$(git_repo) \
			GitHubOAuthToken=$(git_token) \
			GitHubBranch=$(branch) \
			S3ConfigBucket=$(CONFIG_BUCKET) \
			NetworkStack=$(NETWORK_STACK) \
			KnownBucket=$(KNOWN_BUCKET_NAME) \
			UnknownBucket=$(UNKNOWN_BUCKET_NAME) \
			RekogCollectionId=$(REKOGNITION_COLLECTION_ID) \
			SlackApiToken=$(SLACK_API_TOKEN) \
			SlackChannelId=$(SLACK_CHANNEL_ID) \
			SlackTrainingChannel=$(SLACK_TRAINING_CHANNEL_ID) \
			AccountNumber=$(AWS_ACCOUNT_NUMBER) \
			SnsArn=$(SNS_TOPIC_ARN)
.PHONY: deploy-pipeline

deploy-sns:
	$(info [+] Deploying SNS stack for Xplorers...)
	@aws cloudformation deploy \
		--template-file cfn/sns-topic.yml \
		--stack-name xplorers-snstopic-$(branch) \
		--capabilities CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			GitHubBranch=$(branch) \
			AdminPhoneNumber=$(ADMIN_CONTACT_NUMBER) \
			AdminEmail=$(ADMIN_EMAIL)
