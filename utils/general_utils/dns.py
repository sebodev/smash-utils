""" Retreives and saves DNS records """
import os, socket, subprocess
import lib.whois
from runner import smash_vars
from pathlib import Path

#If you're looking to get DNS info for a different command, check out the lib.dns module

def main(domain, output_file=None):

    while not domain:
        domain = input('Enter a domain (example google.com): ')

    if output_file:
        output_file = Path(output_file)
    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.rstrip("/")

    if "." not in domain:
        user = os.getenv('username') if os.getenv('username') else "user"
        raise Exception("Hey %s. Could you quickly add a .com or a .whatever to the end of that domain. Thanks" % user)

    cmd = 'nslookup -type=any %s'  % domain
    output_file_res = subprocess.check_output(cmd, shell=True).decode("utf-8")

    # decide where we will store the results
    if output_file:
        if not str(output_file).endswith(".txt"):
            output_file = output_file / (dns + ".txt")
    else:
        #create a folder for the dns records if it doesn't exist
        output_folder = smash_vars.storage_dir / 'dnsRecords'
        try:
            os.makedirs(str(output_folder))
        except WindowsError:
            pass

        #use a new output_file if the nslookup data has changed since the last time the command was otherwise
        output_file = smash_vars.storage_dir / 'dnsRecords' / (domain + ".txt")
        if output_file.is_file():
            i = 0
            next_output_file = output_file
            while (next_output_file.is_file()):
                output_file = next_output_file
                i += 1
                next_output_file = smash_vars.storage_dir / 'dnsRecords' / (domain + str(i) + ".txt")

            #ToDo the nslookup is not consisten in which records it displays first, so this check will return false postives
            #remove all newlines so we don't run into any problems with newlines being retrieved differently then they are saved on the file system
            file_1_newlines_removed = output_file.read_text().replace("\n", "").replace("\r", "")
            file_2_newlines_removed = output_file_res.replace("\n", "").replace("\r", "")
            if ( file_1_newlines_removed == file_2_newlines_removed):
                if smash_vars.verbose:
                    print("Did not detect any changes to the dns info stored at {}".format(output_file))
            else:
                output_file = next_output_file
                if smash_vars.verbose:
                    print("Found changes to the DNS info. Storing results at {}".format(output_file))




    whois_dict = lib.whois.lookup(domain)

    #display whois
    if smash_vars.verbose:
        for k, v in whois_dict.items():
            print(k, v)
        print()
        print("-"*80)
        print()

    #display nslookup and save to file
    output_file.write_text(output_file_res)
    if smash_vars.verbose:
        print(output_file_res)
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
