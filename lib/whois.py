import subprocess, os.path

def lookup(domain):
    "does a whois lookup and returns a dictionary of the results"
    whois = {}
    this_dir = os.path.dirname(os.path.realpath(__file__))
    whois_text = subprocess.check_output(os.path.join(this_dir, "whois.exe") + " " + domain).decode("utf-8")
    for line in whois_text.split("\n"):
        line_split = line.split(":")
        if len(line_split) == 2:
            k, v = line.split(":")
            whois[k] = v
    return whois
