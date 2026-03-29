import socket
from dnslib import DNSRecord

# CONFIG
LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 53
UPSTREAM_DNS = "1.1.1.1"

# In a real hack, this would be your SQLite DB or an AI API call
BLOCK_LIST = [
    "reddit.com",
    "redd.it",
    "redditmedia.com",
    "redditstatic.com",
    "youtube.com",
    "facebook.com",
    "psu.edu",
]
BLOCK_KEYWORDS = ["reddit", "youtube"]
CLIENT_IP = "100.73.141.11"


def is_blocked_domain(domain):
    """Block exact/suffix domains and keyword matches."""
    normalized = domain.lower().rstrip(".")

    for keyword in BLOCK_KEYWORDS:
        if keyword.lower() in normalized:
            return True

    for blocked in BLOCK_LIST:
        blocked = blocked.lower().rstrip(".")
        if normalized == blocked or normalized.endswith("." + blocked):
            return True
    return False

def query_upstream_raw(data):
    """For allowed domains, return the full upstream DNS response."""
    try:
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        upstream_sock.settimeout(1.5)
        upstream_sock.sendto(data, (UPSTREAM_DNS, 53))
        response, _ = upstream_sock.recvfrom(4096)
        upstream_sock.close()
        return response
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

        # 1. THE AGENTIC CHECK
        is_blocked = False
        reason = "Allowed"

        if addr[0] == CLIENT_IP and is_blocked_domain(domain):
            is_blocked = True
            reason = "Static Blocklist"
        
        # TODO: Add your K2 Think / Claude API call here
        # if ai_check(domain) == "UNSAFE": is_blocked = True

        if is_blocked:
            reply = request.reply()
            if addr[0] == CLIENT_IP:
                print(f"[BLOCK] {addr[0]} tried to visit {domain} -> Filtered ({reason})")

            # Force block for all DNS record types.
            reply.header.rcode = 3  # NXDOMAIN

            sock.sendto(reply.pack(), addr)
        else:
            if addr[0] == CLIENT_IP:
                print(f"[ALLOW] {addr[0]} is visiting {domain}")

            upstream_response = query_upstream_raw(data)
            if upstream_response:
                sock.sendto(upstream_response, addr)
            else:
                # Fallback to an empty reply instead of crashing on timeout.
                reply = request.reply()
                sock.sendto(reply.pack(), addr)

if __name__ == "__main__":
    start_guardian()