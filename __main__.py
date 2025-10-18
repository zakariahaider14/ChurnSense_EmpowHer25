import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
import json

# Get configuration
config = pulumi.Config()
gcp_project = config.require("gcp:project")
gcp_region = config.require("gcp:region")
app_name = config.get("app_name") or "churn-agent-app"
environment = config.get("environment") or "dev"

# Create a GCP provider
provider = gcp.Provider("gcp", project=gcp_project, region=gcp_region)

# Create a GCS bucket for model storage
model_bucket = gcp.storage.Bucket(
    f"{app_name}-models",
    location=gcp_region,
    force_destroy=True,
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a GCS bucket for data storage
data_bucket = gcp.storage.Bucket(
    f"{app_name}-data",
    location=gcp_region,
    force_destroy=True,
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a service account for the application
service_account = gcp.serviceaccount.Account(
    f"{app_name}-sa",
    account_id=f"{app_name}-sa",
    display_name=f"Service account for {app_name}",
    opts=pulumi.ResourceOptions(provider=provider),
)

# Grant the service account necessary permissions
# Storage permissions
storage_role = gcp.projects.IAMBinding(
    f"{app_name}-storage-role",
    project=gcp_project,
    role="roles/storage.objectAdmin",
    members=[pulumi.Output.concat("serviceAccount:", service_account.email)],
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a Cloud Run service for the FastAPI model server
model_service = gcp.cloudrun.Service(
    f"{app_name}-model-service",
    location=gcp_region,
    template={
        "spec": {
            "containers": [
                {
                    "image": f"gcr.io/{gcp_project}/{app_name}-model:latest",
                    "ports": [{"container_port": 8000}],
                    "env": [
                        {
                            "name": "MODEL_BUCKET",
                            "value": model_bucket.name,
                        },
                    ],
                }
            ],
            "service_account_name": service_account.email,
        }
    },
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a Cloud Run service for the web application
web_service = gcp.cloudrun.Service(
    f"{app_name}-web-service",
    location=gcp_region,
    template={
        "spec": {
            "containers": [
                {
                    "image": f"gcr.io/{gcp_project}/{app_name}-web:latest",
                    "ports": [{"container_port": 3000}],
                    "env": [
                        {
                            "name": "MODEL_SERVICE_URL",
                            "value": model_service.statuses[0].url,
                        },
                        {
                            "name": "ENVIRONMENT",
                            "value": environment,
                        },
                    ],
                }
            ],
            "service_account_name": service_account.email,
        }
    },
    opts=pulumi.ResourceOptions(provider=provider, depends_on=[model_service]),
)

# Make the services publicly accessible
model_iam = gcp.cloudrun.IamMember(
    f"{app_name}-model-public",
    service=model_service.name,
    location=gcp_region,
    role="roles/run.invoker",
    member="allUsers",
    opts=pulumi.ResourceOptions(provider=provider),
)

web_iam = gcp.cloudrun.IamMember(
    f"{app_name}-web-public",
    service=web_service.name,
    location=gcp_region,
    role="roles/run.invoker",
    member="allUsers",
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a Cloud SQL instance for the database
db_instance = gcp.sql.DatabaseInstance(
    f"{app_name}-db",
    database_version="MYSQL_8_0",
    region=gcp_region,
    settings={
        "tier": "db-f1-micro",
        "availability_type": "REGIONAL",
        "backup_configuration": {
            "enabled": True,
            "start_time": "03:00",
        },
    },
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a database
database = gcp.sql.Database(
    f"{app_name}-db-instance",
    instance=db_instance.name,
    opts=pulumi.ResourceOptions(provider=provider),
)

# Create a database user
db_user = gcp.sql.User(
    f"{app_name}-db-user",
    instance=db_instance.name,
    name="churn_user",
    password=config.require_secret("db_password"),
    opts=pulumi.ResourceOptions(provider=provider),
)

# Export the URLs
pulumi.export("model_service_url", model_service.statuses[0].url)
pulumi.export("web_service_url", web_service.statuses[0].url)
pulumi.export("model_bucket_name", model_bucket.name)
pulumi.export("data_bucket_name", data_bucket.name)
pulumi.export("database_instance_name", db_instance.name)
pulumi.export("service_account_email", service_account.email)

