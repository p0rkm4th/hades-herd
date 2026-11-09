# Nyx link diagnosis — 2026-11-09

Nyx `enp4s0` (`d8:bb:c1:d3:d5:f0`, Intel I225-V / `igc`, PCI
`0000:04:00.0`) is UP with carrier. `ethtool` reports support and advertisement
for 10/100/1000/2500BASE-T, autonegotiation enabled, full duplex, and a
negotiated 100 Mb/s. Sysfs agrees. No speed/duplex/autoneg override appeared
in `/etc/netplan` or `/etc/systemd/network`. Nyx routes to Hecate's documented
IPv6 address over this interface. Hecate's `enp4s0` reports 1000 Mb/s.

Counters at this sample: six cumulative RX CRC errors, zero RX missed errors,
zero TX errors/carrier errors, and six dropped packets in `ip -s link` (driver
reports six RX errors). These lifetime counters do not identify the component
or establish when the errors occurred. The NIC supports 2.5 Gb/s; local
software is not forcing 100 Mb/s. No switch-port mapping or switch capability
for this cable path is documented. Evidence therefore indicates a link
negotiation/path issue, with cause unresolved among switch port negotiation,
cable/termination, or link partner; it does not prove a cable defect.

No remote network changes were made because changing link parameters could
interrupt SSH. Physical/network operator action: trace Nyx MAC
`d8:bb:c1:d3:d5:f0` to its switch port, verify that port and its peer negotiate
at 1 Gb/s or faster, then inspect/reseat or substitute the patch cable if the
port is capable. Recheck `ethtool enp4s0` after the physical check.

| Configuration | Prompt tok/s | Generation tok/s | TTFT | GPU participation | Result |
|---|---:|---:|---:|---|---|
| Nyx only | Not measured | Not measured | Not measured | Not measured | Not run: Nyx link is 100 Mb/s |
| Nyx + Hecate | Not measured | Not measured | Not measured | Not measured | Not run: Nyx link is 100 Mb/s |

Distributed RPC was not attempted; no builds/models were installed or
services changed. Reconsider the bounded benchmark only after Nyx negotiates
at least 1 Gb/s.
