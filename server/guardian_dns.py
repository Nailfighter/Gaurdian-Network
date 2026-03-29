import socket
from dnslib import DNSRecord, QTYPE, RR, A

# CONFIG
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 53
UPSTREAM_DNS = "1.1.1.1"
BLOCKED_CLIENT_IP = "100.81.172.29"
BLOCKED_SITES = ["reddit.com", "psu.edu", "facebook.com"]

def get_real_ip(domain):
    """Directly queries upstream to avoid Tailscale loops."""
    try:
        q = DNSRecord.question(domain)
        packet = q.send(UPSTREAM_DNS, 53, timeout=1.5)
        answer = DNSRecord.parse(packet)
        for rr in answer.rr:
            if rr.rtype == QTYPE.A:
                return str(rr.rdata)
    except:
        return None

def start_guardian():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    print("--- GUARDIAN CORE IS LIVE (Global Mode) ---")

    while True:
        data, addr = sock.recvfrom(512)
        request = DNSRecord.parse(data)
        domain = str(request.q.qname).strip(".")

        # Apply domain blocklist only to the configured client IP.
        site_blocked = any(site in domain for site in BLOCKED_SITES)
        is_blocked = (addr[0] == BLOCKED_CLIENT_IP) and site_blocked

        reply = request.reply()
        if is_blocked:
            print(f"[BLOCK] {addr[0]} -> {domain}")
            reply.add_answer(RR(domain, QTYPE.A, rdata=A("0.0.0.0")))
        else:
            print(f"[ALLOW] {addr[0]} -> {domain}")
            ip = get_real_ip(domain)
            if ip:
                reply.add_answer(RR(domain, QTYPE.A, rdata=A(ip)))
        
        sock.sendto(reply.pack(), addr)

if __name__ == "__main__":
    start_guardian()