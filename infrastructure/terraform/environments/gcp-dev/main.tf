# =============================================================================
# GCP Development Environment
# GCP開発環境用Terraform設定（Cloud Run + Vertex AI）
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # バックエンド設定（リモート状態管理）
  # backend "gcs" {
  #   bucket = "policy-reviewer-tfstate"
  #   prefix = "gcp-dev"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ローカル変数
locals {
  environment = "dev"
  project     = "policy-reviewer"

  common_labels = {
    environment = local.environment
    project     = local.project
    managed-by  = "terraform"
    owner       = var.owner
  }
}

# =============================================================================
# APIの有効化
# =============================================================================
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# =============================================================================
# Cloud Run + Artifact Registry + Cloud SQL
# =============================================================================
module "cloud_run" {
  source = "../../modules/gcp/cloud-run"

  name        = "${local.project}-${local.environment}"
  project_id  = var.project_id
  region      = var.region
  environment = local.environment

  # 開発環境では低コスト設定
  backend_cpu           = "1"
  backend_memory        = "1Gi"
  backend_min_instances = 0  # ゼロスケール（開発コスト削減）
  backend_max_instances = 3
  image_tag             = var.image_tag

  # Cloud SQL（開発環境は最小スペック）
  db_tier     = "db-f1-micro"
  db_password = var.db_password

  # アプリケーション
  app_secret_key  = var.app_secret_key
  deploy_frontend = var.deploy_frontend

  labels = local.common_labels

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Vertex AI Access（Cloud RunサービスアカウントにVertex AI権限を付与）
# =============================================================================
module "vertex_ai" {
  source = "../../modules/gcp/vertex-ai"

  project_id            = var.project_id
  service_account_email = module.cloud_run.service_account_email

  depends_on = [module.cloud_run]
}
