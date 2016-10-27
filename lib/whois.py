import subprocess, os.path, os

def lookup(domain):
    "does a whois lookup and returns a dictionary of the results"
    whois = {}
    if os.name == "nt":
        this_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = os.path.join(this_dir, "whois.exe") + " " + domain
    else:
        cmd = "whois " + domain
    whois_text = subprocess.check_output(cmd).decode("utf-8")
    for line in whois_text.split("\n"):
        line_split = line.split(":")
        if len(line_split) == 2:
            k, v = line.split(":")
            whois[k] = v
    return whois
