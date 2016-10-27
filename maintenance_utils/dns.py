""" Retreives and saves DNS records """
import os, socket, subprocess
import lib.whois
from runner import vars
from pathlib import Path

def main(domain, output_file=None):
    if output_file:
        output_file = Path(output_file)
    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.rstrip("/")

    if "." not in domain:
        user = os.getenv('username') if os.getenv('username') else "user"
        raise Exception("Hey %s. Could you quickly add a .com or a .whatever to the end of that domain. Thanks" % user)

    # decide where we will store the results
    if output_file:
        if not str(output_file).endswith(".txt"):
            output_file = output_file / (dns + ".txt")
    else:
        #create a folder for the dns records if it doesn't exist
        output_folder = vars.storage_dir / 'dnsRecords'
        try:
            os.makedirs(str(output_folder))
        except WindowsError:
            pass
        output_file = vars.storage_dir / 'dnsRecords' / (domain + ".txt")

    whois_dict = lib.whois.lookup(domain)

    #display whois
    if vars.verbose:
        for k, v in whois_dict.items():
            print(k, v)
        print()
        print("-"*80)
        print()

    #display nslookup and save to file
    cmd = 'nslookup -type=any %s'  % domain
    res = subprocess.check_output(cmd).decode("utf-8")
    output_file.write_text(res)
    if vars.verbose:
        print(res)
        print()
        print("-"*80)
        print()

    #get webhost
    webhost = None
    try:
        cmd = 'nslookup -type=ptr %s'  % socket.gethostbyname(domain)
        res = subprocess.check_output( cmd ).decode("utf-8")
        res = res[res.find("name") : ]
        _, res = res.split("=")
        webhost = res.strip()
    except:
        webhost = "IDK"

    #get email server
    email_server_msg = ""
    cmd = 'nslookup -type=mx %s'  % domain
    res = subprocess.check_output( cmd ).decode("utf-8")
    if res.find("mail exchanger") > 0:
        try:
            res = res[res.find("mail exchanger") : ]
            res_start = res.find("=") + 1
            res_end = res[res_start:].find("\n")
            res = res[res_start : res_start+res_end]
            email_server_msg = "\nEmail Server: " + res
        except ValueError:
            email_server_msg = "\nEmail mx record: " + res

    #output all of the info we where able to find
    try:
        print()
        print("IP Adress:", socket.gethostbyname(domain))
    except socket.gaierror as err:
        print("I couldn't find the IP address", err)

    print("Web Host:", webhost)


    try:
        print("Name Server:", whois_dict["Name Server"].lower())
    except:
        print("I just can't seem to find the name server")

    if email_server_msg:
        print(email_server_msg.strip())

    try:
        print("Registrar:", whois_dict["Registrar"])
    except KeyError:
        items = whois_dict.items()
        for key, val in whois_dict.items():
            if ("registrar" in key.lower() or "organization" in key.lower()):
                print(key+":", val)
