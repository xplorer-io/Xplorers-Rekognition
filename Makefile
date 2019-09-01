
SHELL = /bin/bash
SHELLFLAGS = -ex

branch := $(shell git rev-parse --abbrev-ref HEAD)
githash := $(shell git rev-parse HEAD)
git_repo := $(shell env | grep GITHUB_REPO | cut -d "=" -f2)
git_token := $(shell aws ssm get-parameter --name /github/sshkey --with-decryption --output text --query Parameter.Value)

ci:
	scripts/deploy-ci.sh
.PHONY: ci

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
			GithubBranch=$(branch) \
			
.PHONY: deploy-pipeline
