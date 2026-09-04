# Securox — Enterprise Security Architecture & Threat Model

## 1. Threat Modeling & Defense-in-Depth

The platform is engineered according to Zero-Trust Architecture principles (NIST SP 800-207) and protects against the OWASP Top 10 API Security Risks:

1. **Broken Object Level Authorization (BOLA / IDOR)**:
   - Evaluated server-side in `AccessControlEngine`.
   - Doctors attempting to query patient records by ID (`/api/healthcare/patients/P-1004`) have their department and assignment validated before data serialization.
2. **Broken Authentication**:
   - Cryptographic password hashing via PBKDF2-HMAC-SHA256 (260,000 iterations + 18-byte cryptographically secure salt).
   - JWT tokens signed with HS256 and verified strictly on every privileged request.
3. **Broken Object Property Level Authorization**:
   - Ambulance drivers and Tellers receive filtered dataclass payloads omitting sensitive medical history or internal ledger keys.
4. **Unrestricted Resource Consumption (Rate Limiting & DoS)**:
   - Batch request size thresholds ($>50$ items triggers elevated risk, $>500$ triggers critical containment).
5. **Security Misconfiguration & Super Admin Auditability**:
   - Super Administrators are never invisible. Every action executed by `superadmin` generates an immutable cryptographic audit trail in `store.audit`.

---

## 2. Immutable Audit Logging Specification

Every operational request logs the following schema to SQLite (WAL mode):
- `id`: Unique UUID v4
- `timestamp`: ISO-8601 UTC timestamp
- `actor`: Authenticated username or API principal
- `action`: Specific evaluated verb (e.g. `VIEW_PATIENT_RECORD`, `OVERRIDE_TRAFFIC_SIGNAL`)
- `target`: Target entity ID and sector
- `payload`: Complete JSON snapshot of:
  - Client IP & Geolocation
  - Enrolled Device Fingerprint & Trust Score
  - Evaluated Risk Score ($0 - 100$)
  - Policy Decision (`ALLOWED`, `MONITORED`, `CHALLENGED`, `BLOCKED`)
  - Full XAI factor breakdown

---

## 3. Incident Lifecycle & Containment States

When an adaptive access block occurs, an incident is dispatched with the following statuses:
1. `OPEN`: Newly triggered anomaly dispatched to SOC.
2. `INVESTIGATING`: Security Analyst assigned; containment playbook initiated.
3. `CONTAINED`: Compromised credential/session revoked; device isolated in MDM.
4. `RESOLVED`: Forensic review complete; post-incident report generated.
5. `FALSE_POSITIVE`: Verified legitimate operator action; baseline profile updated.
