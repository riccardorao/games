# $100K Hackathon Playbook

Window: **Mon Nov 16, 2026, 2:00 PM local → Wed Dec 16, 2026, 2:00 PM local.**
Score: cash received − refunds − chargebacks − payment fees − marketing spend.

Follow the steps in order. Every decision is already made; the only judgement calls are the three gates in section 6.

---

## 1. The product in one paragraph

**Working title: Snowpost** (final name is picked Monday, see step M2).
A business pastes its website URL and a client list. In five minutes it gets a branded animated holiday greeting, personalised for every client, each on its own page with a share link. One-off payment. No recording, no avatar, no editing.

**The engine that replaces an audience:** an AI pipeline builds every prospect's finished greeting *before* contacting them, then sends them the link: "Your holiday video for {Company} is ready. Unlock it and send it to your clients." The product is the pitch. Each paying customer then shows the product to 50–5,000 recipients with a "Send yours" button.

## 2. What the research validated, and what it did not

| Question | Finding | Status |
|---|---|---|
| Does the category exist? | HeyGen, Sendspark ($49/mo), Videoup and Invideo all market batch-personalised holiday video. All require recording yourself, an avatar or manual editing. | Demand exists; the zero-effort one-off version is open |
| What do buyers pay today? | Printed business cards run about $1.59–$3.89 each, so 200 clients costs $300–$800 plus addressing time. | $99–$249 is clearly cheaper |
| Is the AI cost viable? | Higgsfield API is pay-as-you-go, roughly $0.07–$0.12 per second on its own pricing page, so about $0.50 per 5-second hero clip. | Viable; verify live rates Monday |
| Can outbound start on day 1 with a new domain? | Pre-warmed inboxes are sold ready to send (about $10/month each, 20–30 emails/day each, per third-party guides). | Viable; verify Monday |
| Has anyone made $100k in 30 days without an audience? | Almost every case found relied on an audience or a marketplace. One team did $100k in 31 days on an AI rewriter. | Rare. This is the real risk |
| Will strangers pay for *this*? | Cannot be known before launch. | Settled by Gate 1 on day 5 |

Honest forecast: $15k–$50k is the realistic range, $100k+ needs the recipient loop or the Agency tier to take off. Chance of first place is low single digits. Only real payments validate the model, which is why the plan is built around gates, not hope.

## 3. Pricing (all one-off, paid upfront)

| Tier | Recipients | Price |
|---|---|---|
| Solo | 100 | $99 |
| Pro | 500 | $249 |
| Team | 2,500 | $799 |
| Agency (white-label, unlimited client campaigns this season) | n/a | $1,999 |

Checkout order bump: **Year Pass +$199** (same list, automatic greetings for New Year, birthdays and client anniversaries through 2027). Prepaid, so it counts in full.

## 4. Who to target, in priority order

Pick segments whose *clients are also business owners*, because those recipients become buyers.

1. Accountants, bookkeepers, CPA firms
2. Marketing, web and creative agencies (also the Agency tier buyers)
3. IT service providers, commercial insurance brokers, law firms
4. Real estate agents and mortgage brokers (high willingness to pay, weaker loop)
5. Italy: commercialisti, consulenti del lavoro, agenzie (in Italian, from day 8)

## 5. The AI stack

| Job | Tool | Est. cost |
|---|---|---|
| Build and deploy everything | Claude Code with the Vercel and Supabase connectors | existing plan |
| Hero video clips | Higgsfield API | ~$50–$300 |
| Per-recipient personalisation | Browser overlay on the hero clip (name, company, logo, message). No per-recipient rendering | $0 |
| Lead lists (business name, site, email) | Google Maps scraper (Outscraper or Apify) | ~$150 |
| Logo and brand colours | Scraped from each prospect's site by the pipeline | $0 |
| Outbound sending | Instantly + 40 pre-warmed inboxes | ~$500 |
| Payments | Stripe Checkout (not the App Store) | ~3% |
| Verification | TrustMRR connected to Stripe | free |
| Analytics and attribution | PostHog or DataFast, UTM on every link | free tier |
| Daily content | Higgsfield clips posted to LinkedIn, TikTok, Instagram | included |

Log every dollar spent on Instantly and lead data in a sheet. Declare it as marketing spend if asked. It is under $1,000 and not worth a disqualification risk.

Two product rules that protect the entry: no faces or real people in any video (logos, names and animated scenes only), and never mention the hackathon in sales copy.

---

## 6. Day-by-day instructions

### Before Monday 2:00 PM (the only things the rules explicitly allow)

- [ ] Pre-register for the hackathon when it opens.
- [ ] Open a Stripe account with zero customers and zero payments.
- [ ] Do nothing else. No domain, no repo, no code, no listing, no teasers.

### Monday Nov 16 (Day 1): build

- [ ] **M1, 2:00 PM.** Open a new Claude Code session and paste **Prompt A** (section 7).
- [ ] **M2.** Name: take the first of these with a free `.com`: Snowpost, Greetloop, Merrylist, Yulecast, Cardloop. Buy it through Vercel.
- [ ] **M3.** Create a new empty GitHub repo for the product. Do not reuse any existing repo.
- [ ] **M4.** Create a Higgsfield API key and top up $50. Give Claude the key as an environment variable.
- [ ] **M5.** Email crew@email.ship-or-die.com: "Do cold-email tooling and lead data count as paid marketing? I am logging them either way."
- [ ] **M6.** By midnight: landing page live, Stripe Checkout live in production, TrustMRR connected.

### Tuesday Nov 17 (Day 2): finish product, start the engine

- [ ] Paste **Prompt B** (hero clip library and the personalised recipient page).
- [ ] Buy your own product flow in Stripe **test mode only**. Never buy it live.
- [ ] Sign up for Instantly, buy 40 pre-warmed inboxes on 8 new sending domains (variants of the product name).
- [ ] Buy 10,000 leads: accountants and agencies, US, UK, Canada, Australia.

### Wednesday Nov 18 (Day 3): first sends

- [ ] Paste **Prompt C** (prospect pipeline: lead → logo → demo page → email row).
- [ ] Send the first 500 demos. Use **Email 1** (section 8).
- [ ] Post the first demo clip on LinkedIn, TikTok and Instagram. One post a day from now on.

### Thursday Nov 19 – Friday Nov 20 (Days 4–5): ramp to 1,000/day

- [ ] Send 800–1,000 demos a day.
- [ ] Every morning paste **Prompt D** (daily ops report and reply drafts). Send the drafted replies.

**GATE 1, Friday evening (after about 2,500 sends):**

| Result | Action |
|---|---|
| ≥ 5 paid orders | Scale: double inboxes to 80, buy 30,000 more leads |
| Click rate ≥ 3% but < 5 orders | Offer problem. Drop Solo to $49 for 48 hours and put the video above the fold |
| Click rate < 1% | Delivery problem. Have Claude rewrite subject lines and check inbox placement; switch segment to agencies only |

### Nov 21 – Nov 27 (Days 6–12): scale and add high-ticket

- [ ] 1,500–2,000 demos a day.
- [ ] Day 8: paste **Prompt E** (Italian version and Italian lead list).
- [ ] Day 9: start Agency outreach. 30 LinkedIn messages a day to agency owners with their own white-label demo. Target: 10 Agency deals.
- [ ] Black Friday (Nov 27): no discount. Message is "Printed cards will not arrive in time. This takes five minutes."

**GATE 2, Friday Nov 27:**

| Cumulative profit | Action |
|---|---|
| ≥ $5,000 | Continue, add realtors and mortgage brokers as a volume segment |
| $1,000–$5,000 | Put 70% of effort into the Agency tier and Italian market |
| < $1,000 | Keep the engine, change the payload: reposition as year-end client thank-you videos for sales teams, Team tier only |

### Nov 28 – Dec 12 (Days 13–27): peak season

- [ ] Maximum send volume. Rotate subject lines weekly.
- [ ] Ask every buyer by automated email for a one-line testimonial; put the best three on the landing page.
- [ ] Add "New Year" and "Thank you for 2026" templates so buyers after Dec 10 still have a reason.

**GATE 3, Monday Dec 7:** check recipients-to-buyers rate. If fewer than 1 in 300 recipient page views turns into an order, make the "Send yours" button larger and add it to the end of the video. If more, shift outbound entirely to segments whose clients are businesses, since the loop is doing the selling.

### Dec 13 – Dec 16, 2:00 PM (Days 28–30): close

- [ ] "Last day to send before the holidays" email to everyone who clicked but did not buy.
- [ ] Answer every support email within two hours. A refund comes straight off the score.
- [ ] Export analytics and the marketing-spend sheet. Keep TrustMRR connected.

---

## 7. Copy-paste prompts for Claude Code

**Prompt A (Monday, 2:00 PM)**

> Build and deploy a new product from an empty repo. Stack: Next.js on Vercel, Supabase, Stripe Checkout. Product: a business enters its website URL and uploads a CSV of client names and companies; we fetch its logo and brand colour, and create one greeting page per client at /c/{id} that plays a holiday hero video with an animated overlay showing the client's name, the sender's logo and a short message. Pages are locked until payment. Tiers: Solo 100 recipients $99, Pro 500 $249, Team 2,500 $799, Agency $1,999, plus a $199 Year Pass order bump. After payment, unlock the pages and give a CSV export of share links. Every recipient page has a "Send yours" button linking to the landing page with a UTM tag. Add analytics with UTM capture on every route. Today's goal: landing page, checkout and paid unlock working in production. Use a placeholder hero video.

**Prompt B (Tuesday)**

> Using the Higgsfield API key in the environment, generate a library of 5-second looping holiday hero clips: 8 visual styles (snow globe, cosy fireplace, city lights, minimal gold, winter forest, shop window, northern lights, festive desk) with no people or faces. Store them in Supabase storage. Let the customer pick a style. After payment, generate one custom hero clip with the customer's logo integrated into the scene. Add a per-recipient social preview image. Polish the recipient page for mobile.

**Prompt C (Wednesday)**

> Build the prospect pipeline. Input: a CSV of leads (business name, website, email, segment). For each lead: scrape the logo and brand colour from the site, create a locked demo at /for/{slug} showing their greeting with three sample client names, and output a CSV row with the demo link, a thumbnail image link, and merge fields for Instantly. Skip leads with no usable logo. Process 1,000 leads per run and report how many succeeded.

**Prompt D (every morning)**

> Daily ops. Pull yesterday's numbers from Stripe, the analytics tool and the Instantly export I am attaching: sends, opens, clicks, demo views, orders, revenue, refunds, recipient page views, and orders that came from "Send yours". Compare with the gates in the playbook and tell me the one thing to change today. Then draft replies to the attached inbound emails.

**Prompt E (Day 8)**

> Add full Italian localisation: landing page, checkout, recipient pages, templates ("Buone Feste", "Auguri di Buon Natale"), and an Italian version of the outbound emails for commercialisti and agenzie.

## 8. Outbound copy

**Email 1**
Subject: {Company}'s holiday video is ready
> Hi {FirstName}, I made {Company} a holiday greeting video, with your logo, personalised for each of your clients. Here it is: {DemoLink}
> If you like it, upload your client list and it is ready to send in five minutes. No printing, no postage, no deadline.
> {YourName}

**Email 2 (day 3, non-openers and non-clickers)**
Subject: still time before the holidays
> {FirstName}, printed cards ordered now may not arrive in time. Yours is already made: {DemoLink}

**Email 3 (day 7, clicked but did not buy)**
Subject: your video expires Friday
> The demo I made for {Company} comes down on Friday. Unlock it here if you want to send it: {DemoLink}

## 9. The scoreboard to watch daily

| Metric | Target |
|---|---|
| Demos sent per day | 1,000 → 2,000 |
| Click rate | ≥ 3% |
| Click-to-order | ≥ 5% |
| Average order | ≥ $180 |
| Orders from "Send yours" ÷ total orders | ≥ 20% by Dec 7 |
| Refund rate | < 2% |

At targets: 40,000 demos → 1,200 clicks → 60 direct orders, plus loop and Agency deals. Direct outbound alone lands near $10k–$15k; the difference between that and $100k is the loop and the Agency tier, which is where your own time should go from day 9.
