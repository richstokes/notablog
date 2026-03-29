---
title: "DIY Autoscaling on Railway with ~150 Lines of Python"
description: "Building a lightweight autoscaler that scales worker replicas based on job backlog using Railway's GraphQL API"
date: 2026-03-28
tags: [railway, python, autoscaling, infrastructure]
---

## DIY Autoscaling on Railway with ~150 Lines of Python

Railway doesn't have built-in horizontal autoscaling. You can manually set replica counts from the dashboard, but if your workload is bursty (quiet most of the time with occasional spikes) you're either paying for idle replicas or making users wait.

I wanted something simple: scale up when there's a backlog of jobs, scale back to one when the queue is empty. No Kubernetes, no external autoscaler service. Just the worker itself managing its own replicas.

### The Setup

The app is [ToneChef](https://tonechef.app), which generates camera recipes from reference photos using AI. The architecture is straightforward:

- **API server** — accepts jobs, manages auth/credits
- **Worker** — polls a Postgres jobs table, processes one job at a time
- **Supabase** — Postgres database + storage

Workers already use optimistic concurrency to claim jobs (atomic `UPDATE ... WHERE status = 'pending'`), so multiple workers can run safely without duplicate processing. The question was just: how many should be running?

### The Scaling Logic

The rules are simple:

```python
SCALE_UP_THRESHOLD = 3
MIN_REPLICAS = 1
MAX_REPLICAS = 6

if pending > SCALE_UP_THRESHOLD:
    desired = min(pending, MAX_REPLICAS)
elif pending == 0 and processing == 0:
    desired = MIN_REPLICAS
else:
    desired = current  # hold steady
```

- **More than 3 pending jobs?** Scale up. One replica per pending job, capped at 6.
- **Queue empty and nothing processing?** Scale down to 1. (The "nothing processing" check prevents killing replicas that are mid-job.)
- **1-3 pending?** Hold steady. This avoids thrashing when jobs are trickling in at a normal rate.

### Talking to Railway's API

Railway's API is GraphQL-based. A few things to be aware of:

**Authentication:** Railway has two token types. Account tokens use `Authorization: Bearer`, but project-scoped tokens use a `Project-Access-Token` header instead. This is [documented](https://docs.railway.com/integrations/api) but easy to miss if you assume all tokens use Bearer auth.

```python
resp = httpx.post(
    "https://backboard.railway.com/graphql/v2",
    json=payload,
    headers={
        "Content-Type": "application/json",
        "Project-Access-Token": token,
    },
    timeout=30,
)
```

**Setting replicas:** `serviceInstanceUpdate` only writes config. It doesn't trigger actual scaling. For that, you need the two-step [staged changes](https://docs.railway.com/guides/staged-changes) flow that the dashboard uses internally:

```python
# Step 1: Stage the change
_railway_request(
    """mutation($eid: String!, $input: EnvironmentConfig!, $merge: Boolean) {
        environmentStageChanges(environmentId: $eid, input: $input, merge: $merge) {
            id
        }
    }""",
    {
        "eid": ENVIRONMENT_ID,
        "input": {
            "services": {
                SERVICE_ID: {
                    "deploy": {
                        "multiRegionConfig": {
                            REGION: {"numReplicas": count}
                        }
                    }
                }
            }
        },
        "merge": True,
    },
)

# Step 2: Commit (skipDeploys=true — scaling doesn't need a redeploy)
_railway_request(
    """mutation($eid: String!, $skipDeploys: Boolean) {
        environmentPatchCommitStaged(environmentId: $eid, skipDeploys: $skipDeploys)
    }""",
    {"eid": ENVIRONMENT_ID, "skipDeploys": True},
)
```

You need three IDs (service, environment, and region), all available from the Railway console under your project and service settings.

**Reading the current replica count** turned out to be unreliable. The `numReplicas` field on `serviceInstance` is stale, and the environment patches API doesn't always reflect dashboard changes. The solution: don't read at all. Just track what you last set in memory and only write when the desired count changes.

### Integration

The autoscaler runs inside the worker's existing poll loop. No separate process, no cron job:

```python
while True:
    reap_stale_jobs(db)

    try:
        check_and_scale(db)
    except Exception as e:
        logger.warning(f"Autoscaler error (non-critical): {e}")

    job = claim_next_job(db)
    if job:
        process_job(db, job)
    else:
        time.sleep(poll_interval)
```

Every poll cycle (3 seconds), it counts pending and processing jobs (two cheap Supabase `count` queries), computes the desired replica count, and only calls Railway if the number needs to change.

### Race Conditions with Multiple Replicas

When you have 6 replicas running, all 6 are executing `check_and_scale` independently. They'll all compute the same desired count and try to set it simultaneously. This is fine because:

1. The stage+commit flow is idempotent. Setting the same value twice is harmless.
2. When two replicas race, the second one gets "No patch to apply" on commit. We just suppress that error:

```python
msgs = [e.get("message", "") for e in result["errors"]]
if not all("No patch to apply" in m for m in msgs):
    logger.warning(f"Railway API errors: {result['errors']}")
```

### Results

Threw 10 test jobs at it and watched:

```
Autoscaler: 10 pending, 0 processing — setting 6 replica(s)
Railway replicas set to 6
Processing job 45c5ab68... Vibe-only job: 'punchy rooftop view...'
Processing job 8024fe6f... Vibe-only job: 'dreamy night market...'
Processing job 801e7087... Vibe-only job: 'warm rainy city...'
...
Autoscaler: 4 pending, 5 processing — setting 4 replica(s)
...
Autoscaler: 0 pending, 0 processing — setting 1 replica(s)
Railway replicas set to 1
```

It scaled to 6 within seconds, processed all 10 jobs across multiple workers in parallel, then scaled back to 1. The whole burst took under a minute.

### What It Doesn't Handle

- **Manual dashboard scaling.** If you manually set 6 replicas while the autoscaler is running, it won't notice (it tracks its own state, not Railway's). It self-corrects on the next deploy, or as soon as the job queue state changes.
- **Gradual scale-down.** It goes straight from N to 1 when the queue empties. You could step down gradually with a cooldown, but Railway handles replica termination gracefully enough that this hasn't been an issue.

### Takeaways

The whole thing is about 150 lines of Python with no dependencies beyond `httpx` (which the worker already used). It piggybacks on the existing poll loop, uses the database as the source of truth for load, and only hits the Railway API when something actually needs to change.

If your workload is bursty and you're on Railway, this approach gives you autoscaling without any external infrastructure. The workers themselves are the best place to make scaling decisions. They already know the queue depth and can manage their own replica count.

This was built for a background worker with a queryable job queue, which makes the scaling signal obvious. But the same pattern works for API servers and frontends. You'd just swap the scaling signal: request latency, CPU usage, or request rate instead of queue depth. Railway exposes service metrics via the API, or you could track your own (e.g. a rolling average of response times). The staged changes mechanism is the same either way.
