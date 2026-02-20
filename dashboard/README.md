# AdCamp Dashboard - Modern UI/UX

This dashboard provides a modern, intuitive interface for the AdCamp AI video generation pipeline.

## 🎨 Design Philosophy

The redesigned dashboard follows modern UX principles:

1. **Visual Hierarchy**: Clear information architecture with progressive disclosure
2. **Modern Aesthetics**: Gradient backgrounds, smooth animations, rounded corners
3. **Responsive Layout**: Optimized for wide screens with proper content spacing
4. **Status Communication**: Visual feedback for every user action
5. **Accessibility**: High contrast, clear typography, keyboard navigation support

## ✨ Key UI Improvements

### 1. Hero Header
- **Before**: Plain text header
- **After**: Gradient hero section with gradient text effect
- **Impact**: Immediate brand recognition, premium feel

### 2. Configuration Sidebar
- **Before**: Basic form controls
- **After**: 
  - Visual tier indicators with color-coded cards
  - Collapsible sections for settings
  - Integrated cost calculator
  - Pipeline architecture visualization
- **Impact**: Self-documenting interface, reduces cognitive load

### 3. Tab-Based Navigation
- **Before**: Single-page layout
- **After**: 
  - 🎬 Generate Video (primary workflow)
  - 📊 Analytics (metrics dashboard)
  - 📚 Library (placeholder for future features)
- **Impact**: Separates concerns, cleaner workflow

### 4. Generation Progress
- **Before**: Sequential text status updates
- **After**: 
  - Visual step indicators with numbered badges
  - Color-coded completion states (blue → green)
  - Real-time status descriptions
- **Impact**: Users understand where they are in the process

### 5. Result Presentation
- **Before**: Linear layout with all info mixed
- **After**: 
  - Sectioned output (Script, Routing, Cost, Video)
  - Gradient cards for hero vs catalog tiers
  - Custom metric cards with visual styling
  - Progress bars for analytics
- **Impact**: Scan-able information, easier to digest

### 6. Cost Metrics
- **Before**: Simple st.metric displays
- **After**: 
  - Custom gradient metric cards
  - Color-coded borders and values
  - Savings percentage with visual emphasis
- **Impact**: Cost transparency, easier comparison

### 7. Analytics Dashboard
- **Before**: Basic cost summary at bottom
- **After**: 
  - Dedicated analytics tab
  - 4 key metrics in cards
  - Cost breakdown with progress bars
  - Performance vs target comparison
- **Impact**: Data-driven insights at a glance

## 🎨 Color System

```css
Primary:   #0066FF (Blue)     - Primary actions, main branding
Success:   #10B981 (Green)    - Completed states, positive metrics
Warning:   #F59E0B (Orange)   - Info boxes, alerts
Error:     #EF4444 (Red)      - Error states, failures
Hero:      #8B5CF6 (Purple)   - Hero tier branding
Catalog:   #3B82F6 (Blue)     - Catalog tier branding
```

## 📊 Layout Structure

```
┌─────────────────────────────────────────────────┐
│  Hero Header (Gradient Banner)                   │
├─────────────────────────────────────────────────┤
│  Quick Stats Bar (4 columns)                    │
├──────────────┬──────────────────────────────────┤
│   Sidebar    │  Main Content (Tabs)             │
│              │                                   │
│   Settings   │  Tab 1: Generate Video           │
│   Tier Info  │  ├─ Campaign Details (2/3)       │
│   Calculator │  ├─ Product Image (1/3)          │
│   Pipeline   │  ├─ Generate Button (centered)   │
│              │  ├─ Progress Steps               │
│              │  ├─ Script Output (2 cols)       │
│              │  ├─ Routing Info (card)          │
│              │  ├─ Cost Metrics (4 cols)        │
│              │  └─ Video Output                 │
│              │                                   │
│              │  Tab 2: Analytics                │
│              │  ├─ Metrics (4 cols)             │
│              │  ├─ Cost Summary (left)          │
│              │  └─ Performance (right)          │
│              │                                   │
│              │  Tab 3: Library (placeholder)    │
├──────────────┴──────────────────────────────────┤
│  Footer (3 columns - branding/links/powered by) │
└─────────────────────────────────────────────────┘
```

## 🎯 UX Patterns

### Progressive Disclosure
- Configuration options hidden in expandable sections
- Advanced settings available but not overwhelming
- Full video prompt in expander (not cluttering main view)

### Visual Feedback
- Hover effects on buttons (lift + shadow)
- Loading states with progress bars
- Success/error states with icons + color
- Smooth transitions (0.2s ease-in-out)

### Smart Defaults
- Catalog tier selected by default (most common use case)
- 720p resolution (balanced quality/cost)
- 8 second duration (optimal for social)
- TikTok platform pre-selected (highest volume)

### Error Recovery
- Inline validation (disabled button when brief empty)
- Troubleshooting expander with common issues
- Specific error messages with actionable fixes
- Graceful degradation (API offline warning)

## 🚀 Performance Optimizations

1. **Lazy Loading**: Heavy components only render when needed
2. **Conditional Rendering**: Results only shown after generation
3. **Caching**: Static content cached by browser
4. **Optimistic UI**: Immediate feedback before API response

## 📱 Responsive Considerations

While optimized for desktop (wide layout), the design gracefully degrades:
- Sidebar collapses on narrow screens
- Multi-column layouts stack vertically
- Touch-friendly button sizes (48px+ targets)
- Mobile-optimized spacing

## 🔄 Workflow Optimization

### Generation Flow (Tab 1)
1. User inputs campaign brief (large, prominent)
2. Configure settings in sidebar (always accessible)
3. Optional product image with preview
4. Single, centered CTA button
5. Progress visualization (builds confidence)
6. Sectioned results (easy to scan)

### Analytics Flow (Tab 2)
1. Single refresh button
2. Metrics cards above the fold
3. Cost breakdown + performance comparison
4. Quick stats sidebar for context

## 🎨 Custom Components

### Metric Cards
```html
<div class="metric-card">
    <div class="metric-value">$0.08</div>
    <div class="metric-label">Total Cost</div>
</div>
```
- Gradient backgrounds
- Color-coded borders
- Large value typography
- Uppercase labels with letter-spacing

### Progress Steps
```html
<div class="progress-step">
    <div class="step-icon">1</div>
    <div><strong>Title</strong><br/>Description</div>
</div>
```
- Circular numbered badges
- Gray background for pending
- Green background for complete
- Flex layout with gap

### Tier Cards
- Hero: Purple gradient (#f3e8ff → #e9d5ff)
- Catalog: Blue gradient (#dbeafe → #bfdbfe)
- Left border accent (4px solid)
- Rounded corners (12px)
- Padding: 1.5rem

## 🏗️ Future Enhancements

### Library Tab (Planned)
- Video grid view with thumbnails
- Search/filter functionality
- Campaign organization
- Regeneration workflow
- Bulk operations

### Analytics Tab (Enhancements)
- Time-series charts (cost over time)
- Platform breakdown (TikTok vs Instagram vs YouTube)
- Quality scores / approval rates
- A/B test comparison

### Generation Tab (Enhancements)
- Batch upload for multiple SKUs
- Template library (pre-configured briefs)
- Brand guidelines integration
- Preview before generate

## 🎓 Design Decisions

### Why Tabs Over Single Page?
- **Separation of Concerns**: Generation vs analytics are distinct workflows
- **Reduced Clutter**: Each tab focuses on one task
- **Scalability**: Easy to add new features (Library, Settings)
- **User Mental Model**: Familiar pattern from modern web apps

### Why Sidebar Configuration?
- **Always Accessible**: Settings don't scroll away
- **Contextual Help**: Info boxes explain tier differences
- **Visual Hierarchy**: Main content reserved for workflow
- **Sticky Navigation**: Pipeline architecture always visible

### Why Custom CSS Over Streamlit Defaults?
- **Brand Alignment**: Match modern design trends
- **Visual Consistency**: Unified color system
- **Professional Polish**: Streamlit defaults feel prototypey
- **Competitive Differentiation**: Stand out from other tools

## 📦 File Structure

```
dashboard/
├── app.py              # Main dashboard (redesigned)
├── app_old.py          # Original version (backup)
├── README.md           # This file
└── requirements.txt    # Dependencies
```

## 🚀 Running the Dashboard

### Local Development

```bash
# From project root
make dev

# Or directly
streamlit run dashboard/app.py --server.port 8501
```

Access at: http://localhost:8501

### GCP Cloud Run Deployment

The dashboard is configured to use the production API by default:

```bash
# Set your GCP project
export GCP_PROJECT_ID=your-gcp-project-id

# Deploy both API and Dashboard
make deploy-gcp

# Or use the script directly
./deploy/gcp/deploy-all.sh
```

The dashboard will automatically connect to:
- **Production API**: https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app
- **Dashboard URL**: https://adcamp-dashboard-YOUR_PROJECT_HASH.asia-southeast1.run.app

**Environment Variables**:
- `API_URL`: Set to override the default production API (optional)
  - Default: `https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app`
  - Local dev: `http://localhost:8000`

## 🔗 Integration Points

- **API Backend**: http://localhost:8000
- **Monitoring**: http://localhost:3000 (Grafana)
- **API Docs**: http://localhost:8000/docs

## 💡 Pro Tips

1. **Test with API offline**: The dashboard gracefully handles connection errors
2. **Use sidebar calculator**: Estimate costs before generating
3. **Check analytics regularly**: Track cost efficiency over time
4. **Try both tiers**: Compare hero vs catalog quality
5. **Save successful briefs**: Reuse patterns that work well

---

**Built with**: Streamlit · Python · Modern CSS
**Design inspiration**: Linear, Notion, Vercel
**Color system**: Tailwind CSS palette
