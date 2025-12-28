# 🏠 Funda Property Tracker

A full-stack application for searching, tracking, and rating properties on Funda.nl. Built with Python (search backend) and React + TypeScript + Tailwind v4 (frontend).

## 📁 Project Structure

```
funda-scraper/
├── src/                      # React frontend source
│   ├── components/           # React components
│   ├── types/               # TypeScript definitions
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Tailwind v4 styles
├── public/                  # Static assets
│   └── data/                # Data files (served publicly)
│       ├── properties.json  # Property data from Funda
│       └── ratings.json     # Your ratings
├── scripts/                 # Python backend
│   ├── config.json          # Search configuration
│   ├── search.py            # Property search script
│   └── requirements.txt     # Python dependencies
├── .github/workflows/       # GitHub Actions
│   └── deploy.yml           # Auto-deploy to Pages
├── dist/                    # Build output (auto-generated)
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Clone the repo
git clone <your-repo-url>
cd funda-scraper

# Install Python dependencies
pip install git+https://github.com/0xMH/pyfunda.git

# Install Node dependencies
npm install
```

### 2. Configure Your Search

Edit `scripts/config.json`:

```json
{
  "search": {
    "city": "breda",
    "neighborhoods": ["ginneken", "princenhage"],
    "price_min": 500000,
    "price_max": 750000,
    "area_min": 130,
    "max_results": 50
  }
}
```

### 3. Run Search

```bash
python scripts/search.py
```

This will:
- Search Funda based on your criteria
- Save/update properties in `public/data/properties.json`
- Track new, updated, and removed properties
- Show price change history

### 4. Start Development Server

```bash
npm run dev
```

Open http://localhost:5173 to view the app.

### 5. Review Properties

- Browse unreviewed properties in the Review Queue
- Click "View on Funda" to open listings
- Rate properties (1-5 scale) on:
  - Location
  - House Quality
  - Garden
  - Value for Money
- Quick reject with optional reason
- Update status (viewed, bidding, etc.)

### 6. Save Your Ratings

1. Click "💾 Save Ratings" button
2. Download the `ratings.json` file
3. Replace `public/data/ratings.json` with the downloaded file
4. Commit and push to GitHub

## 📊 Features

### Dashboard
- Overview statistics
- Status breakdown
- Average ratings
- Top rated properties

### Review Queue
- Filter by status (unreviewed, reviewed, rejected, etc.)
- Property cards with thumbnails
- Quick actions (review, reject, view on Funda)
- Rating display for reviewed properties

### Rating System
- **Criteria scores** (1-5): Location, Quality, Garden, Value
- **Status tracking**:
  - Unreviewed → Reviewed → Viewing Interest → Viewed → Bidding
  - Quick reject option
  - Archive when no longer relevant
- **Notes**: Free-form text for each property
- **Price history**: Automatic tracking of price changes

## 🔧 Development

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## 🌐 Deployment

### GitHub Pages Setup

1. Go to your repo Settings → Pages
2. Set Source to "GitHub Actions"
3. Push to `main` branch
4. GitHub Actions will automatically build and deploy

Your app will be available at: `https://<username>.github.io/<repo-name>/`

### Future: Automated Search

The repo includes a placeholder for daily automated searches at 7am:

```yaml
# .github/workflows/search.yml (to be created)
on:
  schedule:
    - cron: '0 7 * * *'  # 7am UTC daily
```

This will require:
- GitHub Actions secrets for any API keys
- Auto-commit workflow for properties.json updates

## 💾 Data Management

### Properties Data
- Automatically tracked in `public/data/properties.json`
- Includes full property details, features, thumbnail URLs
- Tracks `added_date`, `last_seen`, `status`
- Price history for properties that change price

### Ratings Data
- Stored in `public/data/ratings.json`
- Kept in localStorage during review sessions
- Downloaded and manually committed
- Can be upgraded to API backend later

## 🔮 Future Enhancements

- [ ] FastAPI backend for automatic rating sync
- [ ] Multi-device rating sync
- [ ] Automated daily searches via GitHub Actions
- [ ] Property comparison feature
- [ ] Export ratings to CSV/Excel
- [ ] Email alerts for new properties
- [ ] Save full property photos locally
- [ ] Advanced filtering (map view, specific features)

## 🛠️ Tech Stack

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS v4
- Vite

**Backend:**
- Python 3
- pyfunda library
- JSON file storage

**Deployment:**
- GitHub Pages
- GitHub Actions

## 📝 Workflow

1. **Search** → Run `python scripts/search.py` locally
2. **Commit** → Push updated `properties.json`
3. **Review** → Use web app to rate properties
4. **Save** → Download and commit `ratings.json`
5. **Repeat** → Run searches as often as you like

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt for your own use!

## 📄 License

MIT