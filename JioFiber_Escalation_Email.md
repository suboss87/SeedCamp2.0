**To:** JioFiber Support / Network Operations Team
**From:** Subash Natarajan
**Date:** 6th March 2026
**Subject:** Network Performance Issue — Inconsistent Speeds & High Latency on Wired Connection (Requires Engineering Investigation)

---

Dear JioFiber Support Team,

I am writing to formally report a persistent network performance issue on my JioFiber connection. After conducting thorough diagnostics with our local support engineers, we have identified the problem to be within JioFiber's internal network infrastructure.

Below is a complete summary of our findings along with all supporting evidence.

---

### Connection Details

- **Public IPv4:** 157.51.88.72
- **Public IPv6:** 2409:40f4:3088:e7f8:b8a5:e347:f5d2:444b
- **Local IP:** 192.168.31.170 (DHCP)
- **Router/Gateway:** 192.168.31.1 (JioFiber Router)
- **MAC Address:** 00:1c:c2:84:60:5d
- **Connection Type:** Wired Gigabit Ethernet (USB 10/100/1000 LAN adapter)
- **Device:** MacBook Air, Apple M3, 16 GB RAM
- **Test Date/Time:** 6th March 2026, 18:45 – 19:00 IST

---

### The Problem

Despite using a **wired Gigabit Ethernet connection** (capable of 1000 Mbps), we are experiencing:

1. **Download speeds fluctuating between 22 Mbps and 98 Mbps** — a 4.5x variance within minutes
2. **Upload speeds swinging between 3.3 Mbps and 39 Mbps** — a 12x variance, which is severely abnormal
3. **Latency to internet averaging 50 ms** with spikes up to 78 ms
4. **A major latency jump occurring within JioFiber's own network** (from 2 ms to 25–44 ms at a single internal hop)

---

### What We Tested and Ruled Out (Customer Side)

Our engineers systematically tested and confirmed the following:

| Component | Result | Evidence |
|---|---|---|
| Router (LAN) | ✅ Healthy | Ping to gateway: 1.5 ms avg, 0% packet loss (20 packets) |
| Ethernet Cable/Adapter | ✅ Healthy | 0 interface errors, 0 collisions (netstat verified) |
| Device (MacBook Air M3) | ✅ Healthy | No hardware/software issues |
| Wi-Fi interference | ✅ Not applicable | Test conducted over wired Ethernet only |
| Local congestion | ✅ Ruled out | Tests done under controlled conditions, no other heavy usage |

**Conclusion: The issue is NOT on our side.**

---

### Speed Test Evidence (7 Consecutive Tests)

| Test # | Time (IST) | Ping | Download | Upload |
|---|---|---|---|---|
| 1 | 18:51 | 51.6 ms | 22.8 Mbps | 18.0 Mbps |
| 2 | 18:52 | 47.5 ms | 89.8 Mbps | 29.4 Mbps |
| 3 | 18:53 | 51.3 ms | 81.9 Mbps | 32.3 Mbps |
| 4 | 18:53 | 53.6 ms | 91.4 Mbps | 34.9 Mbps |
| 5 | 18:54 | 50.2 ms | 64.0 Mbps | 39.4 Mbps |
| 6 | 18:56 | 51.5 ms | 98.7 Mbps | 26.7 Mbps |
| 7 | 18:57 | 48.8 ms | 87.4 Mbps | 27.3 Mbps |

**Averages:** Download: 76.6 Mbps | Upload: 29.7 Mbps | Ping: 50.6 ms

Note: Three additional independent tests prior to monitoring showed download as low as **23 Mbps** and upload as low as **3.3 Mbps**.

---

### Traceroute Evidence — Bottleneck Location Identified

We ran traceroutes to two independent destinations (Google DNS 8.8.8.8 and Cloudflare DNS 1.1.1.1). **Both traceroutes show the same pattern**, confirming the issue is within JioFiber's infrastructure, not destination-specific.

**Key finding — Latency spike at JioFiber Hop 3:**

```
Hop 1  192.168.31.1 (Router)      →  1–3 ms     ✅ Normal
Hop 2  192.0.0.1 (JioFiber Hop 1) →  1–2 ms     ✅ Normal
Hop 3  192.0.0.1 (JioFiber Hop 2) →  25–44 ms   ⚠️ SPIKE — 25+ ms added at a SINGLE hop
Hop 4  192.0.0.1 (JioFiber Hop 3) →  24–40 ms   ⚠️ Packet drops observed (*)
Hop 5  192.0.0.1 (JioFiber Hop 4) →  25–40 ms   ⚠️ 15 ms jitter within same hop
Hop 6  192.168.227.98/99           →  23–39 ms   ⚠️ Load balancer alternating between nodes
Hop 7  192.168.250.8/10/12         →  24–53 ms   ⚠️ Highest jitter — 28 ms range
Hops 8–10  * * *                   →  No response ❌ 3 consecutive hops unresponsive
```

**All problematic hops (3–10) are JioFiber internal infrastructure** using private IP addresses (192.0.0.1, 192.168.227.x, 192.168.250.x).

---

### Summary of Issues for Your Network Team

1. **Congestion or misconfiguration at internal hops 3–7** — a single hop between your nodes is adding 25+ ms latency, which is abnormal for an internal network link.
2. **3 consecutive non-responsive hops (8–10)** — suggests overloaded or misconfigured routers in your backbone.
3. **Upload speed instability (3.3–39 Mbps)** — 12x variance on a wired connection indicates a provisioning or QoS issue.
4. **Download never reaches 100 Mbps** — even the best result (98.7 Mbps) was borderline, and drops to 22 Mbps were observed.

---

### What We Request

1. Please investigate the routing path from our connection (Public IP: 157.51.88.72) through your internal network, specifically the 192.0.0.1 chain and 192.168.227.x / 192.168.250.x nodes.
2. Confirm the provisioned speed for our connection (download and upload).
3. If there is congestion at your local node or exchange, please advise on the timeline for resolution.
4. Please escalate this to your network engineering team if Level 1 support cannot resolve it — the diagnostic data provided here is sufficient for a technical investigation.

We have attached the full diagnostic report (`ISP_Network_Diagnostic_Report.md`) and raw speed test logs (`speed_monitor.log`) for your reference.

We appreciate your prompt attention to this matter and look forward to a resolution.

Best regards,
**Subash Natarajan**
