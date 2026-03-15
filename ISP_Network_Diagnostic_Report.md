# Network Diagnostic Report — JioFiber
**Date:** 2026-03-06 (18:45 – 19:00 IST)
**Prepared by:** Subash Natarajan
**Purpose:** Document network performance issues for ISP escalation

---

## 1. Customer & Connection Details

| Field | Value |
|---|---|
| ISP | JioFiber |
| Connection Type | Wired (USB Ethernet Adapter → JioFiber Router) |
| Router Gateway | 192.168.31.1 (`jiofiber.local.html`) |
| Local IP | 192.168.31.170 (DHCP) |
| Public IPv4 | 157.51.88.72 |
| Public IPv6 | 2409:40f4:3088:e7f8:b8a5:e347:f5d2:444b |
| MAC Address | 00:1c:c2:84:60:5d |
| DNS Server | 2409:40f4:3088:e7f8:3e0a:f3ff:feaa:a5a2 (Router-provided, IPv6) |
| Device | MacBook Air, Apple M3, 16 GB RAM |
| Interface | en5 — USB 10/100/1000 LAN (Wired Gigabit) |

---

## 2. Issue Summary

Despite being connected via **wired Gigabit Ethernet** (1000 Mbps capable), the connection exhibits:
- **Highly inconsistent download speeds** (22–98 Mbps, ~4.5x variance)
- **Severely erratic upload speeds** (3.3–39 Mbps, ~12x variance)
- **Elevated and variable latency** to internet (32–78 ms ping)
- **Significant latency jump at ISP hops** (1 ms local → 25–44 ms at hop 3)

The local network (device ↔ router) is **healthy** — the issues originate **within the ISP infrastructure**.

---

## 3. Speed Test Results (7 Tests Over ~10 Minutes)

| # | Time (IST) | Ping | Download | Upload |
|---|---|---|---|---|
| 1 | 18:51:38 | 51.6 ms | 22.8 Mbps | 18.0 Mbps |
| 2 | 18:52:23 | 47.5 ms | 89.8 Mbps | 29.4 Mbps |
| 3 | 18:53:11 | 51.3 ms | 81.9 Mbps | 32.3 Mbps |
| 4 | 18:53:58 | 53.6 ms | 91.4 Mbps | 34.9 Mbps |
| 5 | 18:54:43 | 50.2 ms | 64.0 Mbps | 39.4 Mbps |
| 6 | 18:56:54 | 51.5 ms | 98.7 Mbps | 26.7 Mbps |
| 7 | 18:57:23 | 48.8 ms | 87.4 Mbps | 27.3 Mbps |

**Averages:** Ping: 50.6 ms | Download: 76.6 Mbps | Upload: 29.7 Mbps

**Key observations:**
- Download speed dropped to **22.8 Mbps** (test #1) — a 77% drop from the best result
- Upload swings wildly with no predictable pattern
- Even the best download (98.7 Mbps) is **below 100 Mbps** on a Gigabit wired link

Earlier independent tests (before monitoring) showed even worse: **Download 23 Mbps, Upload 3.3 Mbps**.

---

## 4. Local Network Health (Device ↔ Router)

**Result: HEALTHY — No issues on customer side.**

| Metric | Value |
|---|---|
| Ping to Gateway (192.168.31.1) | min 0.9 / avg 1.5 / max 3.2 ms |
| Packet Loss | 0.0% (20/20 packets) |
| Jitter (stddev) | 0.46 ms |
| Interface Errors (in/out) | 0 / 0 |
| Collisions | 0 |

This confirms the customer LAN and equipment are performing correctly. **All issues are beyond the router/gateway.**

---

## 5. Traceroute Analysis — Where the Bottleneck Is

### Route to Google DNS (8.8.8.8)
```
Hop  Address                  Latency (ms)         Notes
───────────────────────────────────────────────────────────────
 1   192.168.31.1 (Router)    3.1 / 1.3 / 1.0     ✅ Healthy
 2   192.0.0.1 (ISP Hop 1)   2.5 / 1.8 / 1.6     ✅ OK
 3   192.0.0.1 (ISP Hop 2)   25.9 / 42.6 / 44.0  ⚠️ LATENCY SPIKE (+40ms)
 4   192.0.0.1 (ISP Hop 3)   36.1 / 39.8 / *      ⚠️ HIGH + PACKET DROP
 5   192.0.0.1 (ISP Hop 4)   33.5 / 35.7 / 25.0  ⚠️ VARIABLE
 6   192.168.227.98/99        24.9 – 39.4          ⚠️ LOAD BALANCING, JITTER
 7   192.168.250.8/10         33.8 – 38.9          ⚠️ VARIABLE
8-10 * * *                    —                     ❌ NO RESPONSE (3 hops)
 11  209.85.175.48 (Google)   44.9                  Partial response
 13  8.8.8.8                  31.3 – 45.2          Final destination
```

### Route to Cloudflare DNS (1.1.1.1)
```
Hop  Address                  Latency (ms)         Notes
───────────────────────────────────────────────────────────────
 1   192.168.31.1 (Router)    2.1 / 1.3 / 1.1     ✅ Healthy
 2   192.0.0.1 (ISP Hop 1)   2.1 / 1.9 / 1.4     ✅ OK
 3   192.0.0.1 (ISP Hop 2)   25.9 / 30.5 / 28.2  ⚠️ LATENCY SPIKE (+28ms)
 4   192.0.0.1 (ISP Hop 3)   29.6 / 33.9 / 24.0  ⚠️ HIGH + VARIABLE
 5   192.0.0.1 (ISP Hop 4)   25.6 / 40.0 / 39.9  ⚠️ VARIABLE (15ms swing)
 6   192.168.227.98           23.2 – 39.1          ⚠️ JITTER
 7   192.168.250.12           24.5 – 52.8          ⚠️ HIGHEST JITTER (28ms range)
8-9  * * *                    —                     ❌ NO RESPONSE
 10  49.44.187.47             37.7 – 39.3          ISP peering
 11  1.1.1.1                  47.0 – 47.4          Final destination
```

---

## 6. Bottleneck Identification

### PRIMARY BOTTLENECK: ISP Hops 3–7 (192.0.0.1 → 192.168.250.x)

| Evidence | Detail |
|---|---|
| **Latency spike location** | Hop 2 → Hop 3: latency jumps from ~2 ms to ~25–44 ms |
| **Consistent across routes** | Same spike appears in BOTH traceroutes (to 8.8.8.8 and 1.1.1.1) |
| **ISP internal addresses** | All problem hops use private IPs (192.0.0.1, 192.168.x.x) — these are JioFiber infrastructure |
| **Packet drops** | Hop 4 shows `*` (timeout) on some probes |
| **3 non-responsive hops** | Hops 8–10 return no response at all |
| **High jitter** | Hop 7 shows 24–53 ms range (28 ms jitter) |
| **Load balancing instability** | Hop 6 alternates between .98 and .99 addresses |

**Conclusion:** The bottleneck is entirely within JioFiber's internal routing infrastructure, between the first ISP node and the peering/backbone handoff point.

---

## 7. DNS Configuration Concern

The DNS server is set to the router's IPv6 link-local address (`2409:40f4:3088:e7f8:...`). While DNS resolution works, there is **no custom or fallback DNS** configured. Recommend ISP verify DNS infrastructure performance.

---

## 8. What the Customer Has Ruled Out

| Potential Cause | Status | Evidence |
|---|---|---|
| Wi-Fi issues | ✅ Ruled out | Using wired Gigabit USB Ethernet |
| Device issues | ✅ Ruled out | MacBook Air M3, no interface errors |
| LAN/Router issues | ✅ Ruled out | 1.5 ms avg, 0% loss to gateway |
| Cable issues | ✅ Ruled out | 0 errors, 0 collisions on interface |
| Customer-side congestion | ✅ Ruled out | Testing during controlled conditions |

---

## 9. Action Requested from ISP

1. **Investigate congestion/routing issues at hops 3–7** — internal JioFiber infrastructure (192.0.0.1 chain and 192.168.227.x / 192.168.250.x nodes).
2. **Explain the 25–44 ms latency increase** between hop 2 and hop 3 — this is a single ISP hop adding 25+ ms which is abnormal.
3. **Address the 3 non-responsive hops** (8–10) — possible misconfigured or overloaded routers.
4. **Investigate upload speed instability** — 3.3 to 39 Mbps variance is unacceptable for a wired connection.
5. **Verify provisioned speed** — confirm what download/upload speeds are allocated to this connection, as actual throughput suggests possible throttling or underprovisioning.

---

## 10. Raw Data Files

- Speed test log: `speed_monitor.log` (attached)
- This report: `ISP_Network_Diagnostic_Report.md`
- All tests conducted on: 2026-03-06, 18:45–19:00 IST
- Tools used: `speedtest-cli`, `traceroute`, `ping`, `netstat`, `nslookup`
