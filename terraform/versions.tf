terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  # Remote state for team use. Create the bucket first, then uncomment and run
  # `terraform init -migrate-state`. Kept commented so a fresh clone works locally.
  # backend "s3" {
  #   bucket       = "deskflow-terraform-state-10099"
  #   key          = "eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   encrypt      = true
  #   use_lockfile = true
  # }
}
