""" Gets info from a nslookup and gets whois info """
import os, socket, subprocess
import lib.whois
from runner import vars
from lib import domains
from lib import errors

class InvalidDomain(errors.SmashException):
    pass

def get_info(domain):
    domain = domain.normalize_domain(domain)

    if "." not in domain:
        raise InvalidDomain("Invalid Domain Name '{}'".format(domain))

    whois_dict = lib.whois.lookup(domain)

    return {
        "domain": domain,
        "host": get_web_host(domain),
        "email_server": get_email_server(domain),
        "ip_address": get_ip_address(domain),
        "whois": whois_dict,
        "name_server": get_name_server(whois_dict),
        "domain_registrar": get_domain_registrar(whois_dict),
    }

def get_whois_dict(domain):
    return lib.whois.lookup(domain)

def get_web_host(domain):
    try:
        cmd = 'nslookup -type=ptr %s'  % socket.gethostbyname(domain)
        res = subprocess.check_output( cmd, shell=True ).decode("utf-8")
        res = res[res.find("name") : ]
        _, res = res.split("=")
        webhost = res.strip()
    except:
        webhost = None

    return webhost

def get_email_server(domain):
    #Does not take into account the fact that there could be multiple email servers in the MX records
    email_server = None
    cmd = 'nslookup -type=mx %s'  % domain
    res = subprocess.check_output( cmd ).decode("utf-8")
    if res.find("mail exchanger") > 0:
        try:
            res = res[res.find("mail exchanger") : ]
            res_start = res.find("=") + 1
            res_end = res[res_start:].find("\n")
            res = res[res_start : res_start+res_end]
            email_server = res
        except ValueError:
            email_server = None

def get_ip_address(domain):
    try:
        return socket.gethostbyname(domain)
    except:
         return None

def get_name_server(whois_dict):
    try:
        return whois_dict["Name Server"].lower()
    except KeyError:
        return None

def get_domain_registrar(whois_dict):
    try:
        domain_registrar = whois_dict["Registrar"]
    except KeyError:
        domain_registrar = None
