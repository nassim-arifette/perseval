# User Influencer Submissions Feature

## Overview

This feature allows users to submit influencer handles for marketplace consideration. Submissions go through automated analysis (Perplexity + Mistral) and admin review before being added to the public marketplace.

## Architecture

### Database Schema

**Table: `influencer_submissions`**

Located in: `backend/sql/supabase_schema.sql`

Key fields:
- `handle`, `platform` - Influencer identification
- `reason` - User's explanation (optional, max 500 chars)
- `status` - Workflow state (pending/analyzing/approved/rejected)
- `submitter_ip_hash` - Privacy-preserving submitter tracking
- `analysis_data` - Full AI analysis results (JSONB)
- `trust_score` - Automated trust score (0.00-1.00)
- `reviewed_by`, `admin_notes`, `rejection_reason` - Admin review data

**Rate Limiting Functions:**
- `check_submission_rate_limit(p_ip_hash)` - Max 3 submissions per IP per 24 hours
- `check_duplicate_submission(p_handle, p_platform)` - Prevents duplicate submissions within 7 days

**Indexes:**
- Status + created_at for admin workflow
- Handle + platform for duplicate detection
- Submitter IP hash for user history

**View: `pending_submissions`**
- Shows submissions awaiting review with hours_waiting metric

### Backend API

**Repository: `backend/app/repositories/submissions.py`**

Functions:
- `hash_ip_address(ip)` - SHA-256 hashing for privacy
- `check_submission_rate_limit(ip_hash)` - Rate limit validation
- `check_duplicate_submission(handle, platform)` - Duplicate detection
- `create_influencer_submission(...)` - Create new submission
- `get_submission_by_id(id)` - Fetch single submission
- `list_submissions(status, limit, offset)` - List with filtering
- `update_submission_status(...)` - Update status and analysis
- `review_submission(...)` - Admin approval/rejection
- `get_user_submissions(ip_hash, limit)` - User's submission history

**API Endpoints: `backend/api/routes.py`**

Public endpoints:
- `POST /submissions/influencers` - Submit an influencer
  - Rate limited: 3 per day per IP
  - Duplicate check: 7-day window
  - Returns submission ID and status

- `GET /submissions/influencers/my` - Get user's submissions
  - Limited to 10 most recent
  - Identified by IP hash

Admin endpoints (require `Authorization: Bearer <ADMIN_API_KEY>`):
- `GET /admin/submissions/influencers` - List all submissions
  - Filter by status
  - Pagination support

- `GET /admin/submissions/influencers/{id}` - Get submission details

- `POST /admin/submissions/influencers/{id}/analyze` - Trigger AI analysis
  - Calls Perplexity + Mistral
  - Stores results in `analysis_data`
  - Updates trust_score

- `POST /admin/submissions/influencers/{id}/review` - Approve/reject
  - Required fields: status, rejection_reason (if rejected)
  - Optional: admin_notes
  - Auto-adds to marketplace if approved

**Request/Response Models: `backend/app/models/schemas.py`**

- `InfluencerSubmissionRequest` - User submission payload
- `InfluencerSubmissionResponse` - Submission confirmation
- `InfluencerSubmission` - Full submission with analysis
- `SubmissionListResponse` - Paginated list
- `ReviewSubmissionRequest` - Admin review payload
- `ReviewSubmissionResponse` - Review result

### Frontend

**Submission Modal: `frontend/src/app/components/SubmitInfluencerModal.tsx`**

Features:
- Clean modal UI with backdrop
- Handle input with validation (max 100 chars)
- Platform selector (Instagram/TikTok/YouTube)
- Reason textarea (optional, max 500 chars)
- Real-time validation feedback
- Rate limit error handling
- Duplicate detection messaging
- Success confirmation with submission ID

**Marketplace Integration: `frontend/src/app/marketplace/page.tsx`**

- "Submit Influencer" button in header
- Opens submission modal on click
- Refreshes marketplace after successful submission

**Admin Interface: `frontend/src/app/admin/submissions/page.tsx`**

Features:
- API key authentication (stored in localStorage)
- Status filter tabs (all/pending/analyzing/approved/rejected)
- Submission cards with status badges
- "Analyze" button triggers AI analysis
- "Review" button opens review modal
- Review modal shows:
  - Analysis results (JSON)
  - Admin notes field
  - Rejection reason field
  - Approve/Reject buttons
- Real-time error handling

## Workflow

### User Submission Flow

1. User clicks "Submit Influencer" on marketplace page
2. Modal opens with form
3. User enters handle, selects platform, optionally adds reason
4. Frontend validates input
5. POST to `/submissions/influencers`
6. Backend checks:
   - Rate limit (3 per day per IP)
   - Duplicate (7-day window)
   - Input validation
7. Creates submission with status "pending"
8. Returns submission ID to user
9. User sees success message

### Admin Review Flow

1. Admin logs in with API key
2. Views pending submissions list
3. Clicks "Analyze" on a submission
4. Backend:
   - Updates status to "analyzing"
   - Calls Perplexity + Mistral APIs
   - Stores analysis results
   - Updates status back to "pending"
5. Admin clicks "Review"
6. Reviews analysis data
7. Adds notes/rejection reason
8. Clicks "Approve & Add" or "Reject"
9. Backend:
   - Updates submission status
   - If approved: adds to marketplace_influencers table
   - Records admin review metadata
10. Admin sees updated list

## Security Features

### Privacy Protection
- IP addresses hashed with SHA-256 before storage
- Never store raw IP addresses
- Session hashing for additional deduplication

### Rate Limiting
- 3 submissions per IP per 24 hours (prevents spam)
- Duplicate prevention (7-day window)
- Admin endpoints rate limited separately

### Input Validation
- Handle: max 100 chars, normalized (@ prefix removed)
- Reason: max 500 chars, XSS prevention
- Platform: enum validation
- Admin notes: max 1000 chars
- Rejection reason: max 500 chars, required when rejecting

### Authentication
- Admin endpoints require Bearer token
- API key validated via `verify_admin_auth()`
- Set in environment: `ADMIN_API_KEY`

### Graceful Degradation
- If Supabase unavailable, returns 503 with clear message
- Rate limiting fails open with warnings
- Marketplace addition failure doesn't break review process

## Configuration

### Environment Variables

**Backend (.env):**
```bash
ADMIN_API_KEY=your_secure_admin_api_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database Setup

Run in Supabase SQL Editor:
```sql
-- Execute the full schema in backend/sql/supabase_schema.sql
-- This creates:
-- - influencer_submissions table
-- - check_submission_rate_limit() function
-- - check_duplicate_submission() function
-- - update_submission_timestamp() trigger
-- - pending_submissions view
```

## Usage Examples

### Submit an Influencer (User)

```typescript
const response = await fetch('/api/submissions/influencers', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    handle: 'johndoe',
    platform: 'instagram',
    reason: 'High engagement and transparent about sponsorships'
  })
});

const data = await response.json();
// { id: "uuid", handle: "johndoe", platform: "instagram",
//   status: "pending", message: "Thank you...", created_at: "..." }
```

### Analyze Submission (Admin)

```bash
curl -X POST "http://localhost:8000/admin/submissions/influencers/{id}/analyze" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Review Submission (Admin)

```bash
curl -X POST "http://localhost:8000/admin/submissions/influencers/{id}/review" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "admin_notes": "High trust score, good reputation",
    "add_to_marketplace": true
  }'
```

## Testing

### Test User Submission

1. Navigate to marketplace page: http://localhost:3000/marketplace
2. Click "Submit Influencer"
3. Enter test data:
   - Handle: test_influencer
   - Platform: instagram
   - Reason: Testing submission system
4. Submit and verify success message

### Test Rate Limiting

1. Submit 3 influencers in quick succession
2. Attempt 4th submission
3. Verify 429 error: "You have reached the maximum number of submissions"

### Test Admin Review

1. Navigate to admin page: http://localhost:3000/admin/submissions
2. Enter ADMIN_API_KEY
3. View pending submissions
4. Click "Analyze" on a submission
5. Wait for analysis to complete
6. Click "Review"
7. Enter notes and approve/reject
8. Verify marketplace update if approved

## Future Enhancements

### Planned Features
- [ ] Email notifications for submission status updates
- [ ] Bulk approve/reject for admins
- [ ] Advanced filtering (date range, trust score range)
- [ ] Submission analytics dashboard
- [ ] User reputation system (trusted submitters)
- [ ] Automated approval for high-trust-score submissions
- [ ] Appeal system for rejected submissions

### Performance Optimizations
- [ ] Background job queue for analysis (Celery/Redis)
- [ ] Caching for frequently accessed submissions
- [ ] Pagination for large submission lists
- [ ] Real-time updates via WebSockets

### UX Improvements
- [ ] Progress indicator during analysis
- [ ] Rich text editor for admin notes
- [ ] Submission history timeline
- [ ] In-app notification system
- [ ] Mobile-optimized admin interface

## Troubleshooting

### Common Issues

**"Submissions are not available"**
- Check SUPABASE_URL and SUPABASE_KEY in backend .env
- Verify Supabase connection with `python -c "from backend.app.integrations.supabase import get_supabase_client; print(get_supabase_client())"`
- Ensure SQL schema has been executed

**"Invalid API key"**
- Verify ADMIN_API_KEY is set in backend .env
- Check Authorization header format: `Bearer <key>`
- Try generating new key: `openssl rand -base64 32`

**"Rate limit exceeded"**
- Wait 24 hours for IP rate limit to reset
- For testing, use different IPs or clear submission history from database
- Check `influencer_submissions` table for IP hash records

**Analysis fails**
- Check PERPLEXITY_API_KEY and MISTRAL_API_KEY in .env
- Verify influencer handle exists on platform
- Check backend logs for detailed error messages

## File Reference

### Backend
- `backend/sql/supabase_schema.sql` - Database schema
- `backend/app/repositories/submissions.py` - Data access layer
- `backend/app/models/schemas.py` - Request/response models
- `backend/api/routes.py` - API endpoints
- `backend/app/core/rate_limiter.py` - Rate limiting logic

### Frontend
- `frontend/src/app/components/SubmitInfluencerModal.tsx` - Submission form
- `frontend/src/app/marketplace/page.tsx` - Marketplace with submit button
- `frontend/src/app/admin/submissions/page.tsx` - Admin review interface

### Documentation
- `docs/USER_SUBMISSIONS_FEATURE.md` - This file
- `docs/MARKETPLACE_GUIDE.md` - Overall marketplace documentation
- `docs/ADMIN_API_USAGE.md` - Admin API reference

## Support

For issues or questions:
1. Check backend logs: `tail -f backend.log`
2. Check Supabase logs in dashboard
3. Review API response errors
4. Consult documentation files in `docs/`
