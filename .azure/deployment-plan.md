# Deployment Plan - Money Tracker

## Status: Planning

## Phase 1: Planning
- [x] 0. Specialized Technology Check
- [x] 1. Analyze Workspace
- [x] 2. Gather Requirements
- [x] 3. Scan Codebase
- [x] 4. Select Recipe
- [x] 5. Plan Architecture
- [x] 6. Finalize Plan

## Phase 2: Execution
- [ ] 1. Research Components
- [ ] 2. Confirm Azure Context
- [ ] 3. Generate Artifacts
- [ ] 4. Harden Security
- [ ] 5. Functional Verification
- [ ] 6. Update Plan (Ready for Validation)
- [ ] 7. Hand Off to azure-validate

---

## 1. Project Analysis
- **Mode**: ADD (Enabling Azure hosting for existing FastAPI backend)
- **Class**: Public Web API + Mobile Client
- **Stack**: 
  - Backend: Python (FastAPI)
  - Database: PostgreSQL (Supabase - External)
  - AI: GitHub Models (using provided PAT) or Azure OpenAI
  - Mobile: Android (Kotlin)

## 2. Requirements
- **Scale**: Prototype MVP (10-20 users)
- **Budget**: Azure Credits available
- **Performance**: Near real-time AI categorization

## 3. Architecture
- **Azure Container Apps**: Hosting the containerized FastAPI backend (cost-effective for small scale/scaling to zero).
- **Azure Container Registry**: Private registry for backend images.
- **Azure Key Vault**: Secure storage for GitHub PAT, Supabase Connection Strings, and JWT Secrets.
- **Azure Log Analytics**: Monitoring and tracing.

## 4. Recipe Selection
- **Recipe**: `azd` (Azure Developer CLI)
- **Infrastructure**: Bicep

## 5. Security Strategy
- **Managed Identity**: Container App will use User-assigned identity to access Key Vault.
- **Secrets Management**: No secrets in environment variables; all pulled from Key Vault at runtime.
- **CORS**: Restricted to the App Service URL and local testing.

## 6. Next Steps
1. Confirm Azure Subscription and Location.
2. Generate Bicep templates for Container Apps + Key Vault.
3. Configure `azure.yaml`.
4. Push code to a new GitHub repository.
