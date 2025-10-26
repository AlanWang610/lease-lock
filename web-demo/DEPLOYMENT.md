# Deployment Guide for Lease-Lock Web Demo

This guide explains how to deploy the Flask web demo to Vercel.

## Prerequisites

1. A Vercel account (free tier works)
2. GitHub repository with the code
3. Node.js installed (for Vercel CLI, optional)

## Method 1: Deploy via Vercel CLI

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy

From the `web-demo` directory:

```bash
cd web-demo
vercel
```

Follow the interactive prompts:
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No** (first deployment)
- What's your project's name? **lease-lock-demo** (or your choice)
- In which directory is your code located? **./** (or `.`)

### Step 4: Production Deployment

To deploy to production:

```bash
vercel --prod
```

Your demo will be live at: `https://your-project-name.vercel.app`

## Method 2: Deploy via GitHub

### Step 1: Push Code to GitHub

```bash
git add web-demo/
git commit -m "Add Flask web demo"
git push
```

### Step 2: Import to Vercel

1. Go to https://vercel.com/new
2. Sign in with GitHub
3. Import your repository
4. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: web-demo
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
5. Click **Deploy**

### Step 3: Configure Environment Variables (Optional)

If you want to override the config from `../client/config.env`:

1. Go to your project on Vercel
2. Navigate to **Settings** → **Environment Variables**
3. Add variables as needed (see `env.example` for structure)

### Step 4: View Your Deployment

Visit `https://your-project-name.vercel.app`

## Local Testing

Before deploying, test locally:

```bash
cd web-demo

# Install dependencies
pip install -r requirements.txt

# Run the app
python api/index.py
```

Open http://localhost:5000 in your browser.

## Troubleshooting

### Issue: Module not found errors

**Solution**: Ensure the `api` directory is properly structured with `__init__.py`.

### Issue: Static files not loading

**Solution**: Check the `vercel.json` routes configuration. Static files should be served from `/static/*`.

### Issue: Template not found

**Solution**: Verify Flask is configured with correct `template_folder` and `static_folder` paths.

### Issue: Config not loading

**Solution**: The demo reads from `../client/config.env`. Ensure that file exists with valid configuration.

## Project Structure

```
web-demo/
├── api/
│   ├── __init__.py          # Package marker
│   ├── index.py             # Flask app (Vercel serverless function)
│   └── demo_runner.py       # Mock script runner
├── static/
│   ├── script.js            # Frontend JavaScript
│   └── style.css            # Styling
├── templates/
│   └── index.html           # Demo UI template
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel configuration
├── README.md               # Project documentation
├── DEPLOYMENT.md           # This file
└── env.example             # Environment template
```

## Custom Domain

To use a custom domain:

1. Go to Vercel dashboard → Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. Wait for DNS propagation

## Updates

To update the deployment:

```bash
git add .
git commit -m "Update demo"
git push
```

Vercel will automatically deploy the new version.

## Rollback

To rollback to a previous deployment:

1. Go to Vercel dashboard → Project → Deployments
2. Find the deployment you want
3. Click the three dots → **Promote to Production**

## Performance

- Cold starts: ~1-2 seconds for first request
- Warm function: < 100ms response time
- File size: ~50KB (minimal dependencies)

## Costs

On Vercel's free tier:
- 100GB bandwidth/month
- Unlimited requests (within fair use)
- Edge network included

Perfect for demos and small projects!

