# =============================================================================
# GCP Cloud Run Module
# Cloud Run サービス + Artifact Registry + Cloud SQL + Secret Manager
# =============================================================================

# =============================================================================
# Artifact Registry（コンテナレジストリ）
# =============================================================================
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "${var.name}-docker"
  format        = "DOCKER"

  labels = var.labels
}

# =============================================================================
# Cloud SQL (PostgreSQL)
# =============================================================================
resource "google_sql_database_instance" "main" {
  name             = "${var.name}-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = 20
    disk_type         = "PD_SSD"

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = false
      private_network = var.vpc_network_id != "" ? var.vpc_network_id : null
    }
  }

  deletion_protection = var.environment != "dev"

  labels = var.labels
}

resource "google_sql_database" "main" {
  name     = "policy_review"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  name     = "app"
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# =============================================================================
# Secret Manager
# =============================================================================
resource "google_secret_manager_secret" "app_secret_key" {
  secret_id = "${var.name}-secret-key"

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "app_secret_key" {
  secret      = google_secret_manager_secret.app_secret_key.id
  secret_data = var.app_secret_key
}

# =============================================================================
# Service Account
# =============================================================================
resource "google_service_account" "cloud_run" {
  account_id   = "${var.name}-run-sa"
  display_name = "Cloud Run Service Account for ${var.name}"
}

# Secret Manager アクセス
resource "google_secret_manager_secret_iam_member" "cloud_run_secret" {
  secret_id = google_secret_manager_secret.app_secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud SQL クライアント
resource "google_project_iam_member" "cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# =============================================================================
# Cloud Run - Backend
# =============================================================================
resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.name}-backend"
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/backend:${var.image_tag}"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
      }

      env {
        name  = "LLM_PROVIDER"
        value = "gcp_vertex"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_LOCATION"
        value = var.region
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql://app:${var.db_password}@/${google_sql_database.main.name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
      }

      env {
        name  = "OCR_PROVIDER"
        value = "tesseract"
      }

      env {
        name  = "DEBUG"
        value = tostring(var.environment == "dev")
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_secret_key.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health/live"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health/live"
          port = 8080
        }
        period_seconds = 30
      }
    }

    # Cloud SQL接続
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  labels = var.labels
}

# Cloud Run パブリックアクセス（開発環境のみ）
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  count    = var.environment == "dev" ? 1 : 0
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# =============================================================================
# Cloud Run - Frontend
# =============================================================================
resource "google_cloud_run_v2_service" "frontend" {
  count    = var.deploy_frontend ? 1 : 0
  name     = "${var.name}-frontend"
  location = var.region

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/frontend:${var.image_tag}"

      ports {
        container_port = 3030
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  labels = var.labels
}
