# API Automation Connector

Pulls data from one API (Open-Meteo weather, as a stand-in for any
public or client-provided API) and delivers it somewhere the client
actually checks -- Slack, plus a running CSV log. This is the shape
of most "connect API X to API Y" or "notify me when Z happens" gigs.

## What this demonstrates for a client-facing gig

- Config lives in `.env`, not hardcoded -- a client (or a future you)
  can point this at a different city or Slack channel with no code
  changes
- A reusable `retry()` decorator applied to every network call
- Logging that makes a failed scheduled run diagnosable without
  re-running it
- Zero interactive input -- built to run unattended from cron, a
  scheduled AWS Lambda, or Windows Task Scheduler

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env
# (optional) add a real Slack webhook URL to .env
python automation.py
```

## Adapting for a real client job

- Swap `fetch_weather()` for the client's actual data source (a REST
  API, a scrape result, a database query)
- Swap `send_slack_message()` for email (`smtplib`), a different
  webhook, or writing to Google Sheets via `gspread`
- For scheduling: wrap this in a cron entry, or deploy as a scheduled
  AWS Lambda function for a serverless, always-on version
