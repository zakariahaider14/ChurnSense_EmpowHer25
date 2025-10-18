#!/bin/bash

# Customer Churn Prediction Agent - Deployment Script
# This script automates the deployment process to Google Cloud

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-churn-agent-app}"
REGION="${GCP_REGION:-us-central1}"
APP_NAME="${APP_NAME:-churn-agent-app}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing=0
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install it first."
        missing=1
    else
        print_success "gcloud CLI found"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install it first."
        missing=1
    else
        print_success "Docker found"
    fi
    
    # Check Pulumi
    if ! command -v pulumi &> /dev/null; then
        print_error "Pulumi not found. Please install it first."
        missing=1
    else
        print_success "Pulumi found"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install it first."
        missing=1
    else
        print_success "Python 3 found"
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please install it first."
        missing=1
    else
        print_success "Node.js found"
    fi
    
    if [ $missing -eq 1 ]; then
        print_error "Missing required tools. Please install them and try again."
        exit 1
    fi
}

# Setup GCP
setup_gcp() {
    print_header "Setting Up Google Cloud Project"
    
    print_info "Setting default project to $PROJECT_ID"
    gcloud config set project $PROJECT_ID
    print_success "Project set to $PROJECT_ID"
    
    print_info "Enabling required APIs..."
    gcloud services enable \
        cloudrun.googleapis.com \
        sqladmin.googleapis.com \
        storage-api.googleapis.com \
        cloudbuild.googleapis.com \
        generativelanguage.googleapis.com \
        sheets.googleapis.com \
        iam.googleapis.com
    print_success "APIs enabled"
    
    print_info "Configuring Docker authentication..."
    gcloud auth configure-docker gcr.io
    print_success "Docker authentication configured"
}

# Train ML model
train_model() {
    print_header "Training XGBoost Model"
    
    if [ -f "xgboost_churn_model.pkl" ]; then
        print_warning "Model already trained. Skipping training."
        return
    fi
    
    print_info "Installing Python dependencies..."
    pip install -q pandas scikit-learn xgboost joblib
    print_success "Dependencies installed"
    
    print_info "Training model (this may take a few minutes)..."
    python3 train_model.py
    print_success "Model trained successfully"
}

# Build Docker images
build_docker_images() {
    print_header "Building Docker Images"
    
    print_info "Building model service image..."
    docker build -f Dockerfile.model -t gcr.io/$PROJECT_ID/$APP_NAME-model:latest .
    print_success "Model service image built"
    
    print_info "Building web service image..."
    docker build -f Dockerfile.web -t gcr.io/$PROJECT_ID/$APP_NAME-web:latest .
    print_success "Web service image built"
}

# Push Docker images
push_docker_images() {
    print_header "Pushing Docker Images to Container Registry"
    
    print_info "Pushing model service image..."
    docker push gcr.io/$PROJECT_ID/$APP_NAME-model:latest
    print_success "Model service image pushed"
    
    print_info "Pushing web service image..."
    docker push gcr.io/$PROJECT_ID/$APP_NAME-web:latest
    print_success "Web service image pushed"
}

# Setup Pulumi
setup_pulumi() {
    print_header "Setting Up Pulumi"
    
    print_info "Installing Pulumi dependencies..."
    pip install -q -r pulumi_requirements.txt
    print_success "Pulumi dependencies installed"
    
    print_info "Initializing Pulumi stack..."
    if ! pulumi stack select $ENVIRONMENT 2>/dev/null; then
        pulumi stack init $ENVIRONMENT
    fi
    print_success "Pulumi stack initialized"
    
    print_info "Configuring Pulumi stack..."
    pulumi config set gcp:project $PROJECT_ID
    pulumi config set gcp:region $REGION
    pulumi config set app_name $APP_NAME
    pulumi config set environment $ENVIRONMENT
    print_success "Pulumi stack configured"
    
    print_warning "Please set the following secrets:"
    print_info "pulumi config set --secret gemini_api_key 'your_api_key'"
    print_info "pulumi config set --secret db_password 'your_password'"
    print_info "pulumi config set google_sheets_id 'your_sheet_id'"
    
    read -p "Press Enter once you've set the secrets..."
}

# Deploy infrastructure
deploy_infrastructure() {
    print_header "Deploying Infrastructure with Pulumi"
    
    print_info "Previewing deployment..."
    pulumi preview
    
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    print_info "Deploying infrastructure (this may take 10-15 minutes)..."
    pulumi up --yes
    print_success "Infrastructure deployed successfully"
}

# Get deployment outputs
get_outputs() {
    print_header "Deployment Outputs"
    
    print_info "Web Service URL:"
    pulumi stack output web_service_url
    
    print_info "Model Service URL:"
    pulumi stack output model_service_url
    
    print_info "Database Instance:"
    pulumi stack output database_instance_name
    
    print_info "Service Account:"
    pulumi stack output service_account_email
}

# Test deployment
test_deployment() {
    print_header "Testing Deployment"
    
    WEB_URL=$(pulumi stack output web_service_url)
    MODEL_URL=$(pulumi stack output model_service_url)
    
    print_info "Testing web service..."
    if curl -s $WEB_URL > /dev/null; then
        print_success "Web service is accessible"
    else
        print_error "Web service is not accessible"
    fi
    
    print_info "Testing model service..."
    if curl -s $MODEL_URL/docs > /dev/null; then
        print_success "Model service is accessible"
    else
        print_error "Model service is not accessible"
    fi
}

# Main deployment flow
main() {
    print_header "Customer Churn Prediction Agent - Deployment"
    
    print_info "Configuration:"
    print_info "  Project ID: $PROJECT_ID"
    print_info "  Region: $REGION"
    print_info "  App Name: $APP_NAME"
    print_info "  Environment: $ENVIRONMENT"
    echo ""
    
    # Run deployment steps
    check_prerequisites
    setup_gcp
    train_model
    build_docker_images
    push_docker_images
    setup_pulumi
    deploy_infrastructure
    get_outputs
    test_deployment
    
    print_header "Deployment Complete!"
    print_success "Your application is now deployed to Google Cloud"
    print_info "Next steps:"
    print_info "1. Open the web service URL in your browser"
    print_info "2. Log in with your Manus credentials"
    print_info "3. Test the churn prediction functionality"
    print_info "4. Monitor logs: gcloud run services logs read $APP_NAME-web-service --region=$REGION"
}

# Run main function
main "$@"

