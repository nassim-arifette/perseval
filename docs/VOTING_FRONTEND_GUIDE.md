# Frontend Voting Implementation Guide

## Quick Start

The voting system is now fully integrated into the marketplace! Here's how users can vote:

### 1. View Marketplace

Navigate to: `http://localhost:3000/marketplace`

### 2. Vote on Influencer Cards

Each influencer card in the marketplace grid now displays voting buttons:

- **👍 Trust** button - Vote that you trust this influencer
- **👎 Distrust** button - Vote that you don't trust this influencer
- **Community Score** - Shows the crowdsourced trust percentage
- **Vote Count** - Shows total number of votes

### 3. Voting Behavior

**First Vote:**
- Click either thumbs up or thumbs down
- Vote is recorded immediately
- See success message: "Vote recorded! Thank you for your feedback."
- Vote counts update in real-time

**Change Your Vote:**
- Click the opposite button to change your vote
- Your previous vote is automatically updated

**Remove Your Vote:**
- Click the same button again (toggle off)
- Or use the "(remove vote)" link below the buttons

**Rate Limiting:**
- Maximum 20 votes per hour per user
- Enforced by IP address for privacy

## Component: VotingButtons

### Location
`frontend/src/app/components/VotingButtons.tsx`

### Usage

```tsx
import { VotingButtons } from '../components/VotingButtons';

<VotingButtons
  handle="influencer_username"
  platform="instagram"
  className="optional-custom-classes"
/>
```

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `handle` | string | Yes | Influencer's username (without @) |
| `platform` | string | Yes | Platform name (e.g., 'instagram') |
| `className` | string | No | Additional CSS classes |

### Features

✅ **Real-time Updates**
- Fetches current vote status on mount
- Updates vote counts immediately after voting
- Shows user's current vote status

✅ **Visual Feedback**
- Active button highlights when you've voted
- Loading state while submitting
- Success message after voting
- Error messages for failures

✅ **Smart Behavior**
- Toggle vote by clicking the same button twice
- Auto-updates to reflect changes
- Prevents double-clicking with disabled state

✅ **Accessibility**
- Clear button states (active/inactive)
- Descriptive labels
- Keyboard navigation support

## Integration Points

### 1. Marketplace Cards

**File:** `frontend/src/app/marketplace/page.tsx`

Voting buttons added before the trust label:

```tsx
{/* Voting Buttons */}
<div className="mb-3" onClick={(e) => e.stopPropagation()}>
  <VotingButtons
    handle={influencer.handle}
    platform={influencer.platform}
  />
</div>
```

**Note:** `onClick={(e) => e.stopPropagation()}` prevents the card click event from opening the modal when voting.

### 2. Detail Modal

**File:** `frontend/src/app/marketplace/page.tsx`

Added as a dedicated section:

```tsx
{/* Community Voting Section */}
<div className="mb-6">
  <h3 className="text-lg font-bold mb-4">Community Voting</h3>
  <VotingButtons
    handle={selectedInfluencer.handle}
    platform={selectedInfluencer.platform}
  />
</div>
```

### 3. Trust Score Breakdown

The detail modal now shows:
- **Community Score** bar in the trust breakdown
- Vote count next to the community score
- Visual progress bar showing the score

## API Endpoints Used

The VotingButtons component interacts with these endpoints:

### 1. Get Vote Status (on load)
```
GET /api/votes/influencers/{handle}?platform=instagram
```

Returns:
```json
{
  "handle": "username",
  "platform": "instagram",
  "user_vote": "trust" | "distrust" | null,
  "vote_stats": {
    "trust_votes": 15,
    "distrust_votes": 3,
    "total_votes": 18,
    "user_trust_score": 0.77
  }
}
```

### 2. Submit Vote
```
POST /api/votes/influencers
```

Body:
```json
{
  "handle": "username",
  "platform": "instagram",
  "vote_type": "trust" | "distrust"
}
```

Response:
```json
{
  "handle": "username",
  "platform": "instagram",
  "vote_type": "trust",
  "message": "Thank you for your vote!",
  "vote_stats": { ... }
}
```

### 3. Remove Vote
```
DELETE /api/votes/influencers/{handle}?platform=instagram
```

Response:
```json
{
  "message": "Vote removed successfully.",
  "handle": "username",
  "platform": "instagram"
}
```

## Styling

The component uses the theme context for consistent styling:

```tsx
import { useTheme } from '../context/ThemeContext';
import { getThemeColors } from '../lib/theme';

const { theme } = useTheme();
const colors = getThemeColors(theme);
```

**Colors:**
- **Trust button (active):** `colors.accent.success` (green)
- **Distrust button (active):** `colors.accent.danger` (red)
- **Inactive buttons:** `colors.background.secondary`
- **Community score:**
  - High (≥75%): `colors.accent.success`
  - Medium (≥50%): `colors.accent.warning`
  - Low (<50%): `colors.accent.danger`

## User Experience Flow

### Scenario 1: First-time Voter

1. User sees influencer card with voting buttons
2. Buttons show current vote counts: "👍 Trust (15)" and "👎 Distrust (3)"
3. Community score shows: "Community Score: 77% (18 votes)"
4. User clicks "👍 Trust"
5. Button highlights in green
6. Success message appears: "Vote recorded! Thank you for your feedback."
7. Vote count updates: "👍 Trust (16)"
8. Community score recalculates: "78% (19 votes)"
9. Text appears: "You voted: 👍 Trust (remove vote)"

### Scenario 2: Changing Vote

1. User previously voted "👍 Trust" (button is green)
2. User clicks "👎 Distrust"
3. Trust button returns to neutral
4. Distrust button highlights in red
5. Vote counts update accordingly
6. Success message appears
7. Text updates: "You voted: 👎 Distrust (remove vote)"

### Scenario 3: Removing Vote

1. User previously voted "👍 Trust" (button is green)
2. User clicks "👍 Trust" again
3. Button returns to neutral
4. Vote counts decrease
5. Vote removed indicator disappears

### Scenario 4: Rate Limit Hit

1. User submits their 21st vote within an hour
2. Error message appears: "You have exceeded the voting rate limit (20 votes per hour). Please try again later."
3. Vote is not recorded
4. Button returns to previous state

## Testing the Integration

### Manual Testing

1. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Navigate to marketplace:**
   ```
   http://localhost:3000/marketplace
   ```

3. **Test voting:**
   - Click thumbs up on an influencer
   - Verify button highlights
   - Check vote count increases
   - Open detail modal
   - Verify vote persists
   - Change to thumbs down
   - Verify counts update
   - Click same button to remove
   - Verify vote is removed

4. **Test rate limiting:**
   - Submit 20 votes quickly
   - Try 21st vote
   - Verify error message

### Automated Testing

```tsx
// Example test (Jest + React Testing Library)
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VotingButtons } from './VotingButtons';

test('allows user to vote trust', async () => {
  render(<VotingButtons handle="testuser" platform="instagram" />);

  // Wait for initial load
  await waitFor(() => {
    expect(screen.getByText(/Trust/)).toBeInTheDocument();
  });

  // Click trust button
  fireEvent.click(screen.getByText(/Trust/));

  // Wait for success message
  await waitFor(() => {
    expect(screen.getByText(/Vote recorded!/)).toBeInTheDocument();
  });

  // Verify button is active
  expect(screen.getByText(/You voted: 👍 Trust/)).toBeInTheDocument();
});
```

## Customization

### Change Button Style

Edit `VotingButtons.tsx`:

```tsx
<button
  onClick={() => handleVote('trust')}
  disabled={submitting}
  className="your-custom-classes"
  style={{
    // Your custom styles
    backgroundColor: userVote === 'trust' ? 'green' : 'gray',
    // ...
  }}
>
  {/* Button content */}
</button>
```

### Add Comment Field

To allow users to add comments with votes:

```tsx
const [comment, setComment] = useState('');

<textarea
  value={comment}
  onChange={(e) => setComment(e.target.value)}
  placeholder="Why do you trust/distrust this influencer? (optional)"
  maxLength={500}
/>

// In handleVote function:
body: JSON.stringify({
  handle,
  platform,
  vote_type: voteType,
  comment: comment || undefined,
})
```

### Disable Voting for Certain Users

```tsx
const [canVote, setCanVote] = useState(true);

<VotingButtons
  handle={influencer.handle}
  platform={influencer.platform}
  disabled={!canVote}
/>
```

## Troubleshooting

### Votes Not Appearing

**Issue:** Clicked vote but count didn't update

**Solutions:**
1. Check browser console for errors
2. Verify backend is running: `http://localhost:8000`
3. Check network tab for failed requests
4. Verify Supabase is configured
5. Check database has `influencer_votes` table

### Vote Removed After Page Refresh

**Issue:** Voted but vote disappeared after refresh

**Solutions:**
1. Votes are tracked by IP address
2. If IP changed (VPN, new network), vote won't show
3. Check browser network requests to verify vote was saved
4. Verify database has vote record

### Can't Vote (Always Disabled)

**Issue:** Vote buttons are greyed out

**Solutions:**
1. Check if rate limit exceeded (20 votes/hour)
2. Wait an hour and try again
3. Check browser console for errors
4. Verify network connectivity

### Wrong Vote Count

**Issue:** Vote count doesn't match expected

**Solutions:**
1. Counts are cached - wait a moment and refresh
2. Multiple users voting simultaneously
3. Check database directly for accurate count:
   ```sql
   SELECT * FROM influencer_vote_stats
   WHERE influencer_handle = 'username';
   ```

## Performance Considerations

### Caching

The component fetches vote status once on mount. To refresh:

```tsx
// Add refresh capability
const refreshVotes = () => {
  fetchVoteStatus();
};

<button onClick={refreshVotes}>Refresh Votes</button>
```

### Debouncing

Votes are submitted immediately (no debounce) because:
- Users vote intentionally (not accidental clicks)
- Rate limiting prevents spam
- Immediate feedback improves UX

### Loading States

The component shows loading state while:
1. Initial fetch of vote status
2. Submitting a vote
3. Removing a vote

This prevents duplicate submissions and provides feedback.

## Accessibility

The voting component follows accessibility best practices:

✅ **Keyboard Navigation**
- All buttons are keyboard accessible
- Tab order is logical

✅ **Screen Readers**
- Descriptive button labels
- Vote counts announced
- Success/error messages announced

✅ **Visual Feedback**
- Clear active/inactive states
- High contrast colors
- Loading indicators

✅ **Touch Targets**
- Buttons are large enough for mobile (44px minimum)
- Adequate spacing between buttons

## Mobile Responsiveness

The component works well on mobile:

- **Stacked buttons** on narrow screens
- **Touch-friendly** button sizes
- **Readable** text and vote counts
- **No hover states** that break on mobile

## Summary

The voting system is fully integrated and ready to use:

✅ **VotingButtons** component in marketplace cards
✅ **Community score** in trust breakdown
✅ **Detail modal** voting section
✅ **Real-time updates** with immediate feedback
✅ **Rate limiting** to prevent abuse
✅ **Responsive design** for all devices
✅ **Accessible** for all users

Users can now easily vote on influencers and contribute to the community-driven trust scores!

## Next Steps

To see voting in action:

1. Start backend: `python -m uvicorn backend.main:app --reload`
2. Start frontend: `npm run dev`
3. Navigate to: `http://localhost:3000/marketplace`
4. Click thumbs up or down on any influencer
5. Watch the community score update in real-time!
