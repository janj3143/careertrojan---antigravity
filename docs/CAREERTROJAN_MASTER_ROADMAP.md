# CareerTrojan — Master Roadmap
### The Paper Copy — Print This and Pin It to the Wall

**Created**: 8 February 2026
**Owner**: You
**Purpose**: One document. Every step. Small enough to follow. Big enough to not miss anything.

---

## HOW TO READ THIS DOCUMENT

- Each **TRACK** is a major workstream
- Each track has **numbered steps** — do them in order
- ✅ = done, ⬜ = to do, 🔒 = blocked until something else finishes
- **WHO DOES IT** tells you which AI or tool to use:
  - **CO** = Claude Opus 4.6 (VS Code) — code, APIs, infrastructure
  - **CS** = Claude Sonnet — copy, marketing, pitch decks, polish
  - **YOU** = requires your decision or a human acti
  - **STRIPE** = Stripe dashboard (web browser)
  - **DNS** = Domain registrar (web browser)

---

## THE BIG PICTURE (Print this page on its own)

```
 ┌─────────────────────────────────────────────────────────────┐
 │                    CAREERTROJAN ROADMAP                      │
 │                                                             │
 │  TRACK A: Finish the Runtime          ← YOU ARE HERE        │
 │     ↓                                                       │
 │  TRACK B: Ubuntu Machine + Deploy                           │
 │     ↓                                                       │
 │  TRACK C: Website (careertrojan.com)                        │
 │     ↓                                                       │
 │  TRACK D: Payments (Stripe)                                 │
 │     ↓                                                       │
 │  TRACK E: User Data + AI Learning Loop                      │
 │     ↓                                                       │
 │  TRACK F: Email Campaign (60K contacts)                     │
 │     ↓                                                       │
 │  TRACK G: Advertising (Google, LinkedIn, Social Media)      │
 │     ↓                                                       │
 │  TRACK H: Sales Pitch + Investor Deck                       │
 │     ↓                                                       │
 │  TRACK I: Mobile App (Shrink for Mobile)                    │
 │     ↓                                                       │
 │  TRACK J: User Base Management + Operations                 │
 └─────────────────────────────────────────────────────────────┘
```

---
---

# TRACK A: FINISH THE RUNTIME (Windows)
**Where**: Windows machine, VS Code, C:\careertrojan
**AI**: CO (Claude Opus 4.6)
**Timeline**: Current phase

### Why this is first
Nothing else works until the code runs cleanly and passes all tests.

### Steps

```
A1. ⬜ Run Antigravity test harness — all 4 tiers
        Command: .\scripts\agent_manager.ps1 -Tier all
        WHO: CO
        PASS CRITERIA: Preflight 100%, Unit 80%+, Integration 80%+, E2E informational

A2. ⬜ Fix every test failure from A1
        WHO: CO
        NOTE: Work tier by tier. Don't skip ahead.

A3. ⬜ Mount shared.router in FastAPI
        WHERE: services/backend_api/main.py
        WHAT: The shared router is imported but never include_router()'d
        WHO: CO

A4. ⬜ Standardise API prefixes to /api/v1/...
        WHERE: All 16 routers in services/backend_api/
        WHAT: Mixed prefixes — some bare, some /api/... — make them all /api/v1/
        WHO: CO

A5. ⬜ Fix rewards router prefix overlap
        WHERE: rewards router conflicts with user router at /api/user/v1
        WHO: CO

A6. ⬜ Run the Sales vs Python contamination trap
        WHAT: Feed a "Sales Person" profile to the AI
        PASS: It suggests "Account Executive", "Business Development"
        FAIL: It suggests "Python Developer" (means hardcoded data is leaking)
        WHO: CO + YOU (review the result)

A7. ⬜ Clean up legacy files
        REMOVE: recut_migration.ps1, .backup.* files, duplicate docker-compose files
        WHO: CO

A8. ⬜ Re-run Antigravity test harness — confirm green across all tiers
        WHO: CO
```

### Done when
All 4 test tiers pass. Zero contamination. Clean codebase.

---
---

# TRACK B: UBUNTU MACHINE + DEPLOY
**Where**: New Ubuntu machine (physical or VM)
**AI**: CO
**Timeline**: After Track A is green

### Why Ubuntu
- Docker runs natively (no WSL2 translation = 2–3x faster builds)
- Same OS as production servers
- Better security model for a live service
- Stable — no surprise Windows Update reboots

### Steps

```
B1. ⬜ Install Ubuntu 22.04 LTS on the system disk (SSD)
        WHO: YOU
        NOTE: System disk = ext4 (fast). Your C: and L: drives stay NTFS.

B2. ⬜ Plug in your existing C: and L: drives
        WHO: YOU
        NOTE: Ubuntu sees them as /dev/sdb, /dev/sdc etc.

B3. ⬜ Create mount points and add to /etc/fstab
        WHO: CO (tells you the exact commands)
        RESULT:
            /mnt/old-c-drive    ← your old C: drive (read-only reference)
            /mnt/ai-data        ← your L: drive (read/write for AI data)
        FSTAB LINE EXAMPLE:
            /dev/sdb1  /mnt/old-c-drive  ntfs3  defaults,uid=1000,gid=1000  0  0
            /dev/sdc1  /mnt/ai-data      ntfs3  defaults,uid=1000,gid=1000  0  0

B4. ⬜ Copy the project to the FAST ext4 system disk  ★ THIS IS THE "FAST PATH" ★
        WHO: CO
        COMMAND: cp -r /mnt/old-c-drive/careertrojan ~/careertrojan
        WHY: NTFS under Linux is ~30% slower for writes. The ext4 copy is full speed.
        RESULT: ~/careertrojan is your WORKING COPY (fast)
                /mnt/ai-data is your AI dataset (read-heavy, NTFS is fine)

B5. ⬜ Install VS Code, Docker, Python 3.11
        WHO: CO (gives you exact apt commands)
        PACKAGES: code, docker-ce, docker-compose-plugin, python3.11, python3.11-venv

B6. ⬜ Rebuild Python virtual environment (2 minutes)
        COMMANDS:
            cd ~/careertrojan
            python3.11 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
        WHO: CO
        WHY: Windows venv has .exe files — Linux needs fresh binaries

B7. ⬜ Update path references (Copilot does this in one pass)
        WHAT CHANGES:
            conftest.py:  C:\careertrojan        → ~/careertrojan
            conftest.py:  L:\antigravity_...      → /mnt/ai-data/ai_data_final
            agent_manager: convert .ps1 to .sh   (or keep PowerShell — it runs on Linux)
            .env:         Update all drive letters → Linux mount paths
        WHO: CO
        EFFORT: 30 minutes with Copilot doing the edits

B8. ⬜ Run: docker compose up -d
        WHO: CO
        WHAT HAPPENS: All your services start on native Linux Docker
        VERIFY: curl http://localhost:8500/docs shows your FastAPI docs

B9. ⬜ Run the Antigravity test harness on Ubuntu
        WHO: CO
        CONFIRMS: Everything works on the deployment OS
```

### Done when
`docker compose up` runs cleanly on Ubuntu. All tests pass. Services respond.

---
---

# TRACK C: WEBSITE (careertrojan.com)
**Where**: Ubuntu machine + DNS registrar
**AI**: CO for wiring, CS for content
**Timeline**: After Track B

### What you need
A public website at careertrojan.com that:
1. Tells visitors what CareerTrojan is (marketing landing page)
2. Lets them sign up / log in (connects to your app)
3. Looks professional and loads fast

### Steps

```
C1. ⬜ Choose a cloud server for production
        OPTIONS:
            Hetzner CX21   — €5/month  (good for starting, EU-based)
            DigitalOcean    — $12/month (easy, good docs)
            AWS Lightsail   — $10/month (scales to full AWS later)
        WHO: YOU (pick one)
        RECOMMENDATION: Hetzner or DigitalOcean to start. Move to AWS when you scale.

C2. ⬜ Set up the server
        WHO: CO
        WHAT: Ubuntu 22.04, Docker, firewall (ufw), SSH keys, fail2ban
        TIME: 30 minutes of commands

C3. ⬜ Point your domain to the server
        WHO: YOU + DNS
        WHAT: Log into your domain registrar, set an A record:
            careertrojan.com      → [server IP]
            www.careertrojan.com  → [server IP]
            careertrojan.co.uk    → [server IP]
        WAIT: DNS takes 5–30 minutes to propagate

C4. ⬜ Set up SSL (HTTPS)
        WHO: CO
        HOW: Caddy (easiest) or Certbot + Nginx
        RESULT: https://careertrojan.com shows a green padlock
        COST: Free (Let's Encrypt)

C5. ⬜ Build the landing page
        WHO: CS (writes the copy) + CO (builds it)
        SECTIONS:
            → Hero: "Your career, supercharged by AI"
            → What it does (3 bullet points with icons)
            → How it works (3-step visual)
            → Pricing (link to Track D)
            → Testimonials (use test account data initially)
            → Sign Up / Log In buttons
        TECH: Static HTML/CSS (Astro or Next.js) or a simple page in your existing app

C6. ⬜ Wire login to your FastAPI auth backend
        WHO: CO
        WHAT: Sign Up button → /api/v1/auth/register
              Log In button  → /api/v1/auth/login
              After login    → redirect to User Portal

C7. ⬜ Add your media elements (logo, brand assets)
        WHERE: From L: drive — the official CareerTrojan logo
        WHO: YOU + CO

C8. ⬜ Set up careertrojan.co.uk as a redirect to .com (or vice versa)
        WHO: CO (nginx redirect rule)
```

### Done when
https://careertrojan.com loads, looks professional, and you can sign up and log in.

---
---

# TRACK D: PAYMENTS (Stripe)
**Where**: Stripe dashboard + your FastAPI backend
**AI**: CO
**Timeline**: After Track C (or in parallel with C5–C8)

### Why Stripe
- Industry standard for SaaS subscriptions
- Handles PCI compliance (you NEVER touch card numbers)
- Python SDK plugs directly into FastAPI
- Handles invoicing, receipts, tax, and refunds

### Steps

```
D1. ⬜ Create a Stripe account
        WHO: YOU
        URL: https://stripe.com
        NOTE: Start in TEST MODE (fake money, fake cards)

D2. ⬜ Define your pricing
        WHO: YOU
        DECISION NEEDED:
            Free tier?    → Yes/No, what's included
            Monthly price → e.g., £9.99/month
            Annual price  → e.g., £89.99/year (save ~25%)
            Premium tier? → e.g., £29.99/month with AI coaching
        NOTE: You can change this later. Just pick something to start.

D3. ⬜ Create Products and Prices in Stripe dashboard
        WHO: YOU (in Stripe dashboard, click Products → Add Product)
        RESULT: You get Price IDs like "price_1ABC..." — you'll need these

D4. ⬜ Install Stripe Python SDK
        WHO: CO
        COMMAND: pip install stripe
        ADD TO: requirements.txt

D5. ⬜ Add payment endpoints to FastAPI
        WHO: CO
        NEW ENDPOINTS:
            POST /api/v1/payments/create-checkout    → starts a Stripe checkout
            POST /api/v1/payments/webhook             → Stripe tells you when someone pays
            GET  /api/v1/payments/portal               → customer manages their subscription
        FILES: New router at services/backend_api/routers/payments.py
        EFFORT: ~100 lines of code. CO can scaffold this.

D6. ⬜ Add "Subscribe" button to the website
        WHO: CO
        WHAT: Button on pricing page → calls /create-checkout → redirects to Stripe
        USER FLOW: Click Subscribe → Stripe payment page → success → back to your app

D7. ⬜ Test the full flow with Stripe test cards
        WHO: YOU
        TEST CARD: 4242 4242 4242 4242 (any expiry, any CVC)
        VERIFY: Payment appears in Stripe dashboard, user gets access

D8. ⬜ Go live (flip from test to live mode)
        WHO: YOU
        WHAT: In Stripe dashboard, toggle to Live mode
        NOTE: You'll need to verify your business details first
```

### Done when
A user can visit your site, click Subscribe, pay with a real card, and get access.

---
---

# TRACK E: USER DATA + AI LEARNING LOOP
**Where**: Ubuntu server + your AI data pipeline
**AI**: CO
**Timeline**: Runs continuously from the moment users sign up

### Why this is critical
This is the flywheel that makes CareerTrojan get smarter over time.
Every user interaction feeds back into the AI → better results → more users → more data.
**If you skip this, the AI stays static and competitors catch up.**

### The Loop (memorise this)

```
 USER SIGNS UP
       │
       ▼
 USER UPLOADS CV / SEARCHES JOBS / GETS COACHING
       │
       ▼
 DATA IS CAPTURED ──────────────────────────┐
       │                                     │
       ▼                                     ▼
 STORED IN USER DATA              MIRRORED TO BACKUP
 (primary database)               (disaster recovery)
       │
       ▼
 AI ORCHESTRATOR PICKS UP NEW INTERACTIONS
       │
       ▼
 ENRICHES ai_data_final KNOWLEDGE BASE
       │
       ▼
 NEXT USER GETS BETTER RESULTS
       │
       ▼
 (repeat forever)
```

### Steps

```
E1. ⬜ Set up the production database
        WHAT: PostgreSQL (you already have this in compose.yaml)
        WHERE: careertrojan-postgres container
        WHO: CO
        NOTE: User data in production lives in PostgreSQL, NOT flat files
              The L: drive / file-based approach is for AI training data only

E2. ⬜ Define what user data you capture
        WHO: YOU + CO
        MUST CAPTURE:
            → Profile data (name, skills, experience, location)
            → CV uploads (stored in object storage, e.g., S3 or local volume)
            → Search queries (what jobs they look for)
            → Match results (what AI suggested)
            → Coaching interactions (questions asked, advice given)
            → Session logs (login times, pages visited, time on page)
            → Feedback signals (did they apply? did they click? did they dismiss?)

E3. ⬜ Build the data capture pipeline
        WHO: CO
        HOW: FastAPI middleware that logs interactions to a queue (Redis)
             → Background worker reads queue
             → Writes structured data to PostgreSQL
             → Copies anonymised interaction data to AI training directory

E4. ⬜ Build the AI enrichment worker
        WHO: CO
        WHAT: Background service that:
            1. Reads new interaction data from the queue
            2. Anonymises it (strips names, emails, personal identifiers)
            3. Extracts patterns (skill clusters, job-title mappings, industry trends)
            4. Writes enriched entries to the AI knowledge base
        WHERE: services/workers/ai/ (you already have this container)

E5. ⬜ Set up backup / mirror strategy for production
        WHO: CO
        WHAT: PostgreSQL automated daily backups
              AI training data replicated to a second location
        OPTIONS:
            → Cloud: S3 bucket (pennies per GB)
            → Local: second drive or NAS
        NOTE: The L: ↔ E: tandem sync from Windows is replaced by proper
              database backups + object storage replication in production

E6. ⬜ GDPR compliance for user data
        WHO: YOU + CS
        MUST HAVE:
            → Privacy policy page on the website
            → Cookie consent banner
            → Right to deletion endpoint (user can delete their data)
            → Data export endpoint (user can download their data)
            → Clear consent at sign-up ("I agree to...")
            → Data processing records (what you collect, why, how long you keep it)
        NOTE: UK GDPR is law. Getting this wrong = fines. Get it right before launch.

E7. ⬜ Add admin monitoring dashboard for the AI loop
        WHO: CO
        WHAT: Admin Portal page showing:
            → Number of interactions processed today
            → Queue depth (how many pending)
            → AI knowledge base size
            → Last enrichment run timestamp
            → Error rate
```

### Done when
Users generate data. Data feeds back to AI. AI gets smarter. You can see it all in the admin dashboard.

---
---

# TRACK F: EMAIL CAMPAIGN (60K Contacts)
**Where**: Email service provider + your CRM
**AI**: CS (writes the emails), CO (sets up the infrastructure)
**Timeline**: After Tracks C and D are live (you need a website and payment page)

### ⚠️ CRITICAL WARNINGS

```
 ╔══════════════════════════════════════════════════════════════╗
 ║  1. DO NOT blast 60,000 emails on day one.                  ║
 ║     ISPs will blacklist your domain PERMANENTLY.            ║
 ║                                                             ║
 ║  2. GDPR: You MUST have consent or legitimate interest      ║
 ║     for every contact. No consent = do not email them.      ║
 ║                                                             ║
 ║  3. Every email MUST have an unsubscribe link.              ║
 ║     This is law, not optional.                              ║
 ╚══════════════════════════════════════════════════════════════╝
```

### Steps

```
F1. ⬜ Choose an email provider
        OPTIONS:
            SendGrid        — $15/month for 50K emails. API-friendly. Good deliverability.
            Mailchimp       — $75/month at this volume. Easier UI. Good templates.
            Amazon SES      — $5/month (cheapest). Raw API. Needs more setup.
        WHO: YOU
        RECOMMENDATION: SendGrid (good balance of cost + ease + deliverability)

F2. ⬜ Set up domain authentication (SPF, DKIM, DMARC)
        WHO: CO
        WHAT: DNS records that prove emails from careertrojan.com are legit
        WHY: Without these, your emails go straight to spam
        WHERE: Your domain registrar DNS settings
        RECORDS NEEDED:
            SPF:   TXT record  → v=spf1 include:sendgrid.net ~all
            DKIM:  CNAME records → provided by your email provider
            DMARC: TXT record  → v=DMARC1; p=quarantine; rua=mailto:dmarc@careertrojan.com

F3. ⬜ Audit your 60K contacts for GDPR compliance
        WHO: YOU
        QUESTIONS:
            → How did you get these contacts? (purchased list? opt-in? networking?)
            → Do you have consent records?
            → When was last contact with them?
        IF NO CONSENT: You can use "legitimate interest" if they're professional
            contacts in your industry, but you MUST offer opt-out in the first email.
        CONSIDER: Getting a quick legal review (£200-500 for a data protection consultation)

F4. ⬜ Segment your contacts
        WHO: YOU + CS
        SEGMENTS (based on your structured data):
            → Job seekers (active)
            → Career changers
            → Senior professionals
            → Recruiters / HR
            → Mentors / coaches
            → Cold / unknown
        WHY: Each segment gets a different email. "Hi recruiter" ≠ "Hi job seeker"

F5. ⬜ Write the email sequences
        WHO: CS
        SEQUENCE PER SEGMENT:
            Email 1 (Day 0):  Introduction — what CareerTrojan is, one clear CTA
            Email 2 (Day 3):  Value — one specific feature, how it helps them
            Email 3 (Day 7):  Social proof — results, testimonials
            Email 4 (Day 14): Offer — free trial, discount, or exclusive access
        KEEP THEM SHORT: 150 words max. One link. One action.

F6. ⬜ Warm up the domain (DO NOT SKIP THIS)
        WHO: CO sets it up, then it runs automatically
        SCHEDULE:
            Week 1:  Send to 200/day  (your most engaged contacts first)
            Week 2:  Send to 1,000/day
            Week 3:  Send to 5,000/day
            Week 4:  Send to 10,000/day
            Week 5+: Full volume
        WHY: ISPs watch new sending domains. Ramp slowly = good reputation.

F7. ⬜ Set up tracking
        WHO: CO
        TRACK:
            → Open rate (target: 20%+)
            → Click rate (target: 3%+)
            → Unsubscribe rate (alarm if > 1%)
            → Bounce rate (alarm if > 5% — clean your list)
            → Spam complaints (alarm if > 0.1%)

F8. ⬜ Test with a 500-person segment first
        WHO: YOU
        WHAT: Pick 500 of your best contacts. Send Email 1. Wait 48 hours.
        CHECK: Open rate, click rate, bounce rate, spam complaints
        IF OK: Proceed with warm-up schedule
        IF BAD: Fix the email copy, clean the list, try again
```

### Done when
All 60K contacts have received the sequence. Open rate is healthy. No blacklisting.

---
---

# TRACK G: ADVERTISING + SOCIAL MEDIA MARKETING
**Where**: Google Ads, LinkedIn, TikTok, Instagram, YouTube
**AI**: CS (writes ad copy + scripts), CO (sets up tracking + scheduling)
**Timeline**: After Track F (you want organic traction first)

### Steps

```
G1. ⬜ Set up Google Analytics on careertrojan.com
        WHO: CO
        WHAT: GA4 tracking code on every page
        WHY: You need data on who visits, from where, and what they do

G2. ⬜ Set up conversion tracking
        WHO: CO
        WHAT: Track these events:
            → Sign up completed
            → Subscription purchased
            → CV uploaded
        WHY: Ads are useless if you can't measure what they produce

G3. ⬜ Google Ads — Search campaigns
        WHO: YOU + CS
        KEYWORDS TO TARGET:
            → "career coaching tool"
            → "AI resume builder"
            → "job application tracker"
            → "career change advice"
            → "professional development platform"
        BUDGET: Start at £20/day. Measure for 2 weeks. Scale what works.
        AD FORMAT: Search ads (text only) — these have the highest intent

G4. ⬜ LinkedIn Ads (higher cost, better targeting)
        WHO: YOU + CS
        TARGET:
            → Job title: "looking for new opportunities"
            → Industry: your strongest segments
            → Seniority: Mid-level to Senior
        BUDGET: Start at £30/day. LinkedIn is expensive (~£3-8 per click).
        WHEN: Only after Google Ads prove the conversion funnel works.

G5. ⬜ A/B test landing pages
        WHO: CO + CS
        WHAT: Create 2 versions of your landing page
            Version A: Feature-focused ("AI-powered career tools")
            Version B: Outcome-focused ("Get your next job 3x faster")
        SPLIT: 50/50 traffic. Run for 2 weeks. Keep the winner.

G6. ⬜ Review and optimise weekly
        WHO: YOU
        EVERY MONDAY:
            → Check cost per acquisition (how much to get one paying user?)
            → Kill ads with CPA > your monthly subscription price
            → Double budget on ads with CPA < 50% of subscription price
```

### Done when
You're acquiring users profitably via paid ads (cost per acquisition < customer lifetime value).

---

## TRACK G — PART 2: SOCIAL MEDIA (TikTok, Instagram, YouTube Shorts)

### Why social media matters for CareerTrojan

```
 ╔══════════════════════════════════════════════════════════════╗
 ║  YOUR TARGET AUDIENCE LIVES ON THESE PLATFORMS:              ║
 ║                                                             ║
 ║  • 18-30 year olds starting careers     → TikTok + Insta   ║
 ║  • 25-40 career changers                → Instagram + YT   ║
 ║  • Professionals networking             → LinkedIn (done)   ║
 ║                                                             ║
 ║  CAREER CONTENT IS HUGE on social media.                    ║
 ║  #CareerTok has 4+ billion views on TikTok.                 ║
 ║  This costs £0 and reaches millions. You'd be mad to skip it║
 ╚══════════════════════════════════════════════════════════════╝
```

### The social media playbook (even if you've never used these apps)

**STEP 1: Understand what each platform actually is**

```
 ┌────────────────────────────────────────────────────────────────┐
 │  PLATFORM     │ WHAT IT IS              │ CONTENT FORMAT      │
 ├────────────────────────────────────────────────────────────────┤
 │  TikTok       │ Short video app         │ 15–60 sec videos    │
 │               │ (think YouTube but       │ Vertical (phone)    │
 │               │  everything is micro)    │ Casual, authentic   │
 │                                                               │
 │  Instagram    │ Photo + video sharing    │ Posts (photos)      │
 │  (Insta)      │ Owned by Meta/Facebook   │ Reels (TikTok-like) │
 │               │                          │ Stories (24hr)      │
 │                                                               │
 │  YouTube      │ Video platform           │ Shorts (≤60 sec)    │
 │  Shorts       │ You know YouTube —       │ Same vertical       │
 │               │ "Shorts" is their        │ format as TikTok    │
 │               │ TikTok competitor         │                     │
 └────────────────────────────────────────────────────────────────┘

 KEY INSIGHT: You make ONE video and post it to ALL THREE platforms.
             Same video. Three audiences. Triple the reach.
```

**STEP 2: What to actually post (content ideas)**

```
 You don't need to dance. You don't need to point at text.
 Career content that works on social:

 CONTENT TYPE 1: "Did you know?" facts
    Example: "Your CV gets 6 seconds of attention. Here's what
             recruiters actually look at first..." [show CareerTrojan scanning a CV]
    WHY IT WORKS: People love career tips. They share them.

 CONTENT TYPE 2: Before/After transformations
    Example: "This CV got zero interviews. After CareerTrojan: 5 interviews
             in 2 weeks." [show the before/after side by side]
    WHY IT WORKS: Transformation content goes viral.

 CONTENT TYPE 3: Screen recordings of CareerTrojan in action
    Example: Record yourself uploading a CV, then show the AI suggestions
    WHY IT WORKS: People trust what they can SEE working.

 CONTENT TYPE 4: "Career advice" talking head
    Example: You (or a voiceover) giving 1 tip in 30 seconds
    WHY IT WORKS: Positions you as an expert. Builds trust.

 CONTENT TYPE 5: User stories / testimonials
    Example: "Sarah was stuck as a junior dev for 3 years.
             She used CareerTrojan and got promoted in 6 months."
    WHY IT WORKS: Social proof is the #1 conversion driver.
```

**STEP 3: You don't have to show your face**

```
 FACELESS CONTENT THAT WORKS:

 → Screen recordings with voiceover (record your screen, talk over it)
 → Text-on-screen with trending music (Canva can make these)
 → AI-generated voiceover (ElevenLabs, free tier)
 → Animated explainers (Canva, free)

 TOOLS:
   Record:    OBS Studio (free) or just your phone
   Edit:      CapCut (free, made by TikTok, dead simple)
   Captions:  CapCut auto-captions (critical — 80% watch on mute)
   Graphics:  Canva (free tier is enough)
   Schedule:  Buffer or Later (free tier posts to all 3 platforms)
```

### Steps

```
G7. ⬜ Create accounts on TikTok, Instagram, YouTube (the brand, not personal)
        WHO: YOU
        HANDLE: @careertrojan on all three (grab them NOW even if you don't post yet)
        TIME: 20 minutes
        NOTE: Use a business/creator account, not personal.
              Business accounts get analytics (how many people saw your stuff).

G8. ⬜ Set up a simple content calendar
        WHO: CS (creates the calendar template) + YOU (approves topics)
        WHAT: Plan 3 posts per week across all platforms
            Monday:   Career tip / "Did you know?" fact
            Wednesday: Screen recording of CareerTrojan feature
            Friday:   User story / testimonial / before-after
        SCHEDULE: Use Buffer (free) to post to all 3 at once

G9. ⬜ Create your first 5 videos (batch-produce them)
        WHO: CS (writes the scripts) + CO (creates screen recordings if needed)
        BATCH PRODUCTION:
            → Write 5 scripts in one sitting (CS does this)
            → Record all 5 in one session (you or screen-record)
            → Edit all 5 in CapCut (add captions, trim, music)
            → Schedule them across 2 weeks
        TIME: 2-3 hours total for all 5

G10. ⬜ Add links in bio on all platforms
        WHO: YOU
        WHAT: Link to careertrojan.com (free trial / sign up page)
        USE: Linktree or Beacons (free) — gives you one link that leads to multiple pages
            → "Start free trial"
            → "See pricing"
            → "Read success stories"

G11. ⬜ Engage with career content creators (costs £0, builds audience)
        WHO: YOU (10 minutes per day)
        WHAT: Comment genuinely on career-related videos
              Follow career coaches, recruitment influencers
              Reply to people asking career questions (mention CareerTrojan naturally)
        WHY: The algorithm shows your profile to people in your niche

G12. ⬜ Track what works, drop what doesn't
        WHO: YOU
        CHECK WEEKLY:
            → Which videos got the most views? Make more of those.
            → Which got clicks to your website? (check analytics)
            → What time of day gets most engagement?
        RULE: Do more of what works. Don't overthink it.

G13. ⬜ Consider paid promotion (ONLY after organic content works)
        WHO: YOU
        WHAT: TikTok and Instagram both let you "boost" posts
              Take your best-performing organic video → pay £10-20 to show it to more people
        BUDGET: £5-10/day to start. Only boost videos that already performed well organically.
        WHEN: After you have 10+ organic posts and know what your audience likes.
```

### Social media reality check

```
 ┌────────────────────────────────────────────────────────────────┐
 │  EXPECTATION VS REALITY                                       │
 ├────────────────────────────────────────────────────────────────┤
 │                                                               │
 │  First 1-20 videos:  10-500 views each. This is normal.      │
 │  Videos 20-50:       You start finding what works.            │
 │  Videos 50-100:      One might "pop" (10K+ views).           │
 │  After 100 videos:   You have a system and a growing audience.│
 │                                                               │
 │  CONSISTENCY BEATS PERFECTION.                                │
 │  A mediocre video posted is better than a perfect video       │
 │  never made.                                                  │
 │                                                               │
 │  COST: £0 (just your time — 3-4 hours per week)              │
 │  ROI:  Potentially massive. One viral video = thousands of   │
 │        sign-ups for free.                                     │
 └────────────────────────────────────────────────────────────────┘
```

### Done when
You have a consistent posting cadence (3x/week) and growing follower counts on all platforms.

---
---

# TRACK H: SALES PITCH + INVESTOR DECK
**Where**: Google Slides / PowerPoint / Canva
**AI**: CS (writes everything), YOU (provides the numbers)
**Timeline**: Start after first 50 paying users (Track D + F)

### Three audiences, three pitches

```
AUDIENCE          FORMAT              LENGTH        PURPOSE
────────          ──────              ──────        ───────
Users             Landing page        30 seconds    Get them to sign up
Ad platforms      Ad copy + landing   5 seconds     Get the click
Investors         Pitch deck          10 minutes    Get the meeting / cheque
```

### Steps

```
H1. ⬜ Write the User Pitch (for the website)
        WHO: CS
        FORMULA: [Problem] → [Solution] → [Proof] → [Action]
            PROBLEM: "Job searching is broken. You spend hours on applications
                      that go nowhere."
            SOLUTION: "CareerTrojan uses AI to match you to the right roles,
                       optimise your CV, and coach you through the process."
            PROOF: "[X] users, [Y]% got interviews within 2 weeks"
            ACTION: "Start free → Subscribe for £9.99/month"

H2. ⬜ Write the Ad Pitch (for Google/LinkedIn)
        WHO: CS
        RULES:
            → Headlines: max 30 characters
            → Descriptions: max 90 characters
            → One clear benefit per ad
            → Include a number ("3x faster", "60% more interviews")
        EXAMPLES:
            "AI Career Coach — Get Hired Faster"
            "Your CV, Optimised by AI — Free Trial"

H3. ⬜ Build the Investor Pitch Deck (10-12 slides)
        WHO: CS + YOU
        SLIDE ORDER:
            1.  Title + one-liner
            2.  The problem (job search is broken — stats)
            3.  Your solution (CareerTrojan — what it does)
            4.  Demo screenshot (your actual product)
            5.  Market size (TAM: UK job market = £X billion)
            6.  Business model (subscription tiers + pricing)
            7.  Traction (users, revenue, growth rate)
            8.  The AI advantage (your data flywheel — Track E)
            9.  Competition (and why you're different)
            10. Team (you + your AI infrastructure)
            11. The Ask (how much, what for, what milestones)
            12. Contact details

H4. ⬜ Create a one-page investor summary
        WHO: CS
        WHAT: Single A4 page with the key numbers
        USE: Email to investors before the meeting

H5. ⬜ Identify investors
        WHO: YOU
        ANGEL NETWORKS (UK):
            → Angel Investment Network (angelinvestmentnetwork.co.uk)
            → SyndicateRoom
            → Crowdcube (equity crowdfunding)
        VC (when you have traction):
            → Seedcamp
            → Entrepreneur First
            → LocalGlobe
        ACCELERATORS:
            → Y Combinator (US, but takes UK companies)
            → Techstars London
            → Founders Factory
```

### Done when
You have three polished pitches and a target list of investors.

---
---

# TRACK I: MOBILE APP — SHRINKING CAREERTROJAN FOR PHONES
**Where**: Development environment
**AI**: CO
**Timeline**: After Tracks A–E are stable (this is a Phase 2 item)

### The honest truth about mobile

```
 ╔══════════════════════════════════════════════════════════════╗
 ║  DO NOT BUILD A MOBILE APP UNTIL YOU HAVE:                  ║
 ║    ✓ 100+ active web users                                  ║
 ║    ✓ Confirmed demand ("I wish I could use this on my phone")║
 ║    ✓ Stable API (Tracks A-E complete)                       ║
 ║                                                             ║
 ║  A mobile app before product-market fit = wasted money.     ║
 ╚══════════════════════════════════════════════════════════════╝
```

### HOW TO "SHRINK" A WEB APP FOR MOBILE — The Full Picture

Your desktop app has big dashboards, wide tables, multi-column layouts.
Phones have a 375px-wide screen. You can't just squeeze it down.
Here's the strategy — step by step — for making CareerTrojan work on phones.

```
 ┌──────────────────────────────────────────────────────────────┐
 │            THE MOBILE SHRINK STRATEGY                        │
 │                                                             │
 │  PHASE 1: Responsive CSS (make what you have not break)     │
 │     ↓                                                       │
 │  PHASE 2: PWA (make it installable on phones)               │
 │     ↓                                                       │
 │  PHASE 3: Mobile UX redesign (make it GOOD on phones)       │
 │     ↓                                                       │
 │  PHASE 4: Native app (only if demand proves it)             │
 └──────────────────────────────────────────────────────────────┘
```

**PHASE 1: Responsive CSS — Stop things breaking on small screens**

```
 WHAT THIS MEANS:
    Your CSS currently assumes a ~1200px wide browser.
    "Responsive" means: at smaller widths, the layout reorganises itself.

 WHAT CHANGES:
    ┌──────────────────────┐     ┌─────────┐
    │ DESKTOP (1200px)     │     │ MOBILE  │
    │                      │     │ (375px) │
    │ [Sidebar] [Content]  │ →   │ [Menu☰] │
    │          [Table····] │     │ [Card]  │
    │          [Dashboard] │     │ [Card]  │
    └──────────────────────┘     │ [Card]  │
                                 │ [Card]  │
                                 └─────────┘

 SPECIFIC CHANGES CO WILL MAKE:
    → Sidebar navigation → hamburger menu (☰ icon, tap to open)
    → Wide data tables → stacked cards (one item per card, scrollable)
    → Multi-column dashboards → single column, stacked vertically
    → Buttons → larger touch targets (min 44×44 px, Apple guideline)
    → Font sizes → 16px minimum (prevents iOS auto-zoom on form inputs)
    → Form inputs → full-width, larger padding for fat fingers
    → File upload → works with phone camera ("take photo" or "choose file")

 HOW:
    CSS media queries. Example:
    @media (max-width: 768px) {
      .sidebar { display: none; }     /* hide sidebar */
      .mobile-menu { display: block; } /* show hamburger */
      .data-table { display: none; }   /* hide wide table */
      .card-view { display: block; }   /* show card layout */
    }

 EFFORT: 2-3 days with CO. Zero backend changes needed.
 RESULT: The SAME web app works on phones without looking broken.
```

**PHASE 2: Progressive Web App (PWA) — Make it installable**

```
 WHAT A PWA IS:
    Your website, but it can be "installed" on a phone's home screen.
    It gets its own icon. It opens full-screen (no browser URL bar).
    It feels like a native app. Users don't know the difference.

 WHAT CO ADDS:
    1. manifest.json (tells the phone: "I'm an app, here's my icon and name")
    2. Service worker (caches pages so it loads fast, works partially offline)
    3. App icons (multiple sizes for different devices)
    4. Splash screen (loading screen when you tap the icon)

 WHAT USERS SEE:
    → Visit careertrojan.com on their phone
    → Phone says "Add to Home Screen?"
    → They tap yes
    → CareerTrojan icon appears next to their other apps
    → Tapping it opens full-screen, no URL bar, looks native

 WHAT YOU GET FOR FREE:
    ✓ No App Store approval process
    ✓ No Apple/Google taking 30% of revenue
    ✓ Updates instantly (it's still just your website)
    ✓ Works on ALL phones (iOS + Android + everything else)
    ✓ One codebase (your existing web app)

 WHAT YOU DON'T GET (yet):
    ✗ Push notifications on iOS (limited — improving with each iOS update)
    ✗ App Store presence (no discoverability from App Store search)
    ✗ Camera/sensor access beyond basics

 EFFORT: 1-2 days with CO.
 COST: £0.
```

**PHASE 3: Mobile UX Redesign — Make it GOOD, not just "not broken"**

```
 THIS IS WHERE YOU THINK ABOUT WHAT MOBILE USERS ACTUALLY DO:

 DESKTOP USER:                      MOBILE USER:
  → Sits at desk for 30 mins        → Has 3 minutes on the bus
  → Uploads CV, reads full report    → Wants to check application status
  → Compares 10 jobs side-by-side    → Swipes through 3-4 jobs
  → Edits cover letter at length     → Quick-replies to a message

 MOBILE-FIRST FEATURES TO ADD:
    → Quick dashboard: "You have 3 new job matches" (one tap to see them)
    → Swipe-to-save jobs (like dating apps — swipe right to save, left to skip)
    → One-tap apply: Pre-filled application from your profile
    → Push-style notifications: "CompanyX viewed your application"
    → Simplified CV upload: Take a photo of your CV with phone camera
    → Bite-sized AI tips: Daily career tip notification

 WHAT TO HIDE ON MOBILE (power features stay desktop-only):
    → Detailed analytics dashboards (too dense for small screens)
    → Admin panels (admins use desktops)
    → Bulk operations (uploading 50 CVs at once)
    → Complex comparison tables

 EFFORT: 1-2 weeks with CO.
 COST: £0 (it's design + CSS work).
```

**PHASE 4: Native App (only if demand proves it)**

```
OPTION A: React Native — START HERE IF YOU GO NATIVE
    WHAT: JavaScript/React code that compiles to real iOS + Android apps
    WHY: Your frontend is already React — most code reuses directly
    COST: 2-3 months with CO, or £10,000-25,000 outsourced
    RESULT: Real apps in App Store and Google Play
    SHARE CODE: ~70% of your web React code can be reused

OPTION B: Flutter
    WHAT: Google's framework, uses Dart language
    WHY: Beautiful animations, single codebase for iOS + Android
    COST: Similar to React Native
    DOWNSIDE: New language (Dart), can't reuse your existing React code

OPTION C: Outsource to an agency
    WHAT: A professional mobile dev shop builds it
    COST: £15,000-50,000
    TIME: 3-6 months
    WHEN: After you have revenue to fund it

╔══════════════════════════════════════════════════════════════╗
║  RECOMMENDATION:                                            ║
║  Phase 1 + 2 first (2-4 days, £0).                         ║
║  Phase 3 if mobile traffic > 30% (1-2 weeks, £0).          ║
║  Phase 4 ONLY if PWA isn't enough AND you have revenue.     ║
╚══════════════════════════════════════════════════════════════╝
```

### Steps

```
I1. 🔒 Make existing CSS responsive (media queries for ≤768px)
        WHO: CO
        WHAT: Hamburger menu, stacked cards, full-width forms
        EFFORT: 2-3 days
        BLOCKED BY: Track C complete (website must exist first)

I2. 🔒 Build PWA (manifest.json + service worker + icons)
        WHO: CO
        WHAT: Make the site installable on phone home screens
        EFFORT: 1-2 days
        BLOCKED BY: I1 complete

I3. 🔒 Test on real devices (your actual phone)
        WHO: YOU
        WHAT:
            → Open careertrojan.com on your phone
            → "Add to Home Screen"
            → Test: sign up, upload CV, view results, check jobs
            → Test on both iPhone AND Android if possible
        CHECKLIST:
            ⬜ Can you read all text without zooming?
            ⬜ Can you tap all buttons without misclicking?
            ⬜ Does file upload work from phone?
            ⬜ Do forms work (no text cut off, keyboard doesn't cover input)?
            ⬜ Does it load in under 3 seconds on 4G?

I4. 🔒 Fix issues from real-device testing
        WHO: CO
        WHAT: There WILL be issues. Every phone is different. Budget 1-2 days.

I5. 🔒 Add mobile-specific UX improvements (Phase 3)
        WHO: CO
        WHAT: Quick dashboard, swipe-to-save, simplified views
        WHEN: After mobile traffic > 30% of total traffic

I6. 🔒 Gather user feedback on mobile experience
        WHO: YOU
        WHAT: Ask 20 mobile users: "What's missing? What's annoying?"
        DECISION: Is PWA enough, or do users want a proper app store app?

I7. 🔒 Decide: PWA enough, or build native?
        WHO: YOU
        IF PWA IS ENOUGH: Stop here. Save thousands.
        IF NATIVE NEEDED: Proceed with React Native (Option A).
```

---
---

# TRACK J: USER BASE MANAGEMENT + OPERATIONS
**Where**: Admin Portal + monitoring dashboards
**AI**: CO
**Timeline**: Ongoing from first user sign-up

### Steps

```
J1. ⬜ Set up server monitoring
        WHO: CO
        TOOLS: Uptime Robot (free, checks if site is up every 5 min)
               Grafana + Prometheus (more detailed, inside Docker)
        ALERTS: Email you if the site goes down

J2. ⬜ Set up error tracking
        WHO: CO
        TOOL: Sentry (free tier covers you to start)
        WHAT: Catches Python exceptions in production, sends you alerts

J3. ⬜ Set up database backups
        WHO: CO
        WHAT: Daily PostgreSQL dump → stored off-server
        COMMAND: pg_dump in a cron job, upload to S3 or second server
        RULE: Test restoring a backup at least once a month

J4. ⬜ Create an operations runbook
        WHO: CO + CS
        DOCUMENT COVERING:
            → How to restart services (docker compose restart)
            → How to view logs (docker compose logs -f)
            → How to restore from backup
            → How to ban a user
            → How to issue a refund (Stripe dashboard)
            → How to check AI pipeline health
            → Emergency contacts

J5. ⬜ Set up a support channel
        WHO: YOU
        OPTIONS:
            → Simple: support@careertrojan.com (Gmail/Outlook)
            → Better: Crisp.chat or Intercom widget on the website (live chat)
            → Best: Help desk (Freshdesk free tier)

J6. ⬜ Plan for scaling
        WHO: CO
        WHEN TO WORRY:
            → 100 concurrent users: Your current single-server setup handles this fine
            → 1,000 concurrent users: Add a second server, load balancer
            → 10,000 concurrent users: Move to Kubernetes (your k8s configs exist!)
        DON'T OVER-ENGINEER: Start with one server. Scale when you need to.
```

---
---

# QUICK REFERENCE: WHICH AI FOR WHAT

Print this section separately and keep it by your monitor.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                     AI TOOL CHEAT SHEET                          │
 ├──────────────────────────────────────────────────────────────────┤
 │                                                                  │
 │  CLAUDE OPUS 4.6 (CO) — in VS Code terminal                     │
 │  ─────────────────────────────────────────                       │
 │  ✓ Writing code (Python, FastAPI, Docker, Nginx)                │
 │  ✓ Fixing bugs and test failures                                │
 │  ✓ Server setup commands (Ubuntu, Docker, SSL)                  │
 │  ✓ API integration (Stripe, SendGrid, analytics)               │
 │  ✓ Database queries and migrations                              │
 │  ✓ CI/CD pipelines and deployment scripts                       │
 │  ✓ PWA / React Native scaffolding                               │
 │                                                                  │
 │  CLAUDE SONNET (CS) — in chat / browser                         │
 │  ─────────────────────────────────                               │
 │  ✓ Marketing copy (landing page, emails, ads)                   │
 │  ✓ Sales pitches (user, advertiser, investor)                   │
 │  ✓ Pitch deck content and structure                             │
 │  ✓ Email sequences and subject lines                            │
 │  ✓ Social media scripts (TikTok, Insta, YouTube Shorts)        │
 │  ✓ Privacy policy and legal-ish text                            │
 │  ✓ Proofreading and tone polish                                 │
 │  ✓ Strategy brainstorming                                       │
 │                                                                  │
 │  YOU — decisions only you can make                               │
 │  ────────────────────────────────                                │
 │  ✓ Pricing decisions                                            │
 │  ✓ Which server/provider to use                                 │
 │  ✓ GDPR consent audit of your 60K contacts                     │
 │  ✓ Investor targeting and meetings                              │
 │  ✓ Final approval on all public-facing content                  │
 │  ✓ Budget allocation for ads                                    │
 │                                                                  │
 └──────────────────────────────────────────────────────────────────┘
```

---
---

# THE KILLER CHECKLIST — Things You MUST NOT Forget

These are the items that sink projects. Print this page. Check them off.

```
 ⬜  GDPR privacy policy BEFORE you collect any user data
 ⬜  Unsubscribe link in EVERY email
 ⬜  Domain warm-up BEFORE mass email (4 weeks)
 ⬜  SPF + DKIM + DMARC DNS records BEFORE sending any email
 ⬜  Stripe webhook endpoint BEFORE going live with payments
 ⬜  SSL certificate BEFORE any user logs in
 ⬜  Database backups BEFORE you have real user data
 ⬜  Error tracking (Sentry) BEFORE you have real users
 ⬜  Cookie consent banner on the website
 ⬜  Right to deletion endpoint (GDPR Article 17)
 ⬜  Terms of service page
 ⬜  Test the FULL payment flow with a real card BEFORE announcing
 ⬜  Anonymise user data BEFORE feeding it to AI training
 ⬜  Rate limiting on API endpoints (prevent abuse)
 ⬜  Admin 2FA enabled BEFORE production
```

---

## Timeline Reality Check

```
 Month 1:  Track A (finish runtime) + Track B (Ubuntu setup)
 Month 2:  Track C (website live) + Track D (payments working)
 Month 3:  Track E (AI loop running) + Track F starts (email warm-up begins)
 Month 4:  Track F completes (60K contacted) + Track G starts (ads + social media)
 Month 3+: Social media posting begins (costs £0 — start alongside Track C)
 Month 5:  Track G running + Track H (pitch deck ready, first investor meetings)
 Month 6:  Track I Phase 1-2 (responsive CSS + PWA — 4 days work)
 
 Track J runs continuously from Month 2 onwards.
```

---

**This document lives at**: `C:\careertrojan\docs\CAREERTROJAN_MASTER_ROADMAP.md`
**Print it. Pin it. Check things off with a pen. Update the file when things change.**
