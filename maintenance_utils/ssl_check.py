"""Checks for SSL certificates that are about to expire"""

import socket
import ssl
import datetime
import lib.webfaction
from runner import vars
from lib.errors import SmashException

class AlreadyExpired(SmashException):
    pass

def add(domain_or_server):
    #letsencrypt_webfaction --letsencrypt_account_email hi@sitesmash.com --domains mojaworks.com,www.mojaworks.com --public /home/moja/webapps/moja/ --username moja --password y3ozq3E3IcVZ
    pass
    
def main(domain_or_server=None):
    """ checks when a domain expires.
    domain can also be a Webfaction server entry."""

    d_or_s = domain_or_server

    if d_or_s in vars.servers:
        check_server(d_or_s)
    elif d_or_s:
        check_domain(d_or_s)
    else:
        d_or_s = input("Enter a domain or a Webfaction server entry to check. Leave blank to check them all: ")
        if not d_or_s:
            res = []
            for server in vars.servers:
                print("\nChecking " + server)
                res.append( check_server(server, print_results=False) )
            if all(res):
                print("Everything is in tip top shape.")

        else:
            main(d_or_s)

def check_domain(domain):
    days_left = ssl_valid_time_remaining(domain).days
    if not ssl_expires_soon(domain,  suppressErrors=False):
        print("{} is in good shape. It's SSL certificate doesn't expire for {} days.".format(domain, days_left))
    return days_left

def check_server(server, print_results=True):
    no_problems = True
    wf, wf_id = lib.webfaction.connect(server)

    for data in wf.list_domains(wf_id):
        if ssl_expires_soon(data["domain"]):
            print("!", end="")
            no_problems = False
        else:
            print(".", end="", flush=True)
    if no_problems and print_results:
        print("\nYou're looking good. All of your SSL certificates are up to date.")
    return no_problems

def ssl_expires_soon(domain, suppressErrors=True):
    """ Returns days_left and prints out a warning if a website's SSL certificate expires within 50 days. """
    try:
        days_left = ssl_expires_in(domain, 50)
        if days_left is not None:
            print("Better watch out. {} expires in {} days".format(domain, days_left))
            return days_left
        return False
    except ssl.CertificateError:
        if not suppressErrors or vars.verbose:
            print("There was an SSL error connecting to {}. HTTPS was probably never enabled for this website.".format(domain))
    except socket.gaierror:
        if not suppressErrors or vars.verbose:
            print("Couldn't find an IP address for {}. Does this website even exist?".format(domain))

def ssl_expires_in(hostname, buffer_days=14):
    """Check if `hostname` SSL cert expires is within `buffer_days`.

    Raises `AlreadyExpired` if the cert is past due
    """
    remaining = ssl_valid_time_remaining(hostname)

    # if the cert expires in less than two weeks, we should reissue it
    if remaining < datetime.timedelta(days=0):
        # cert has already expired - uhoh!
        raise AlreadyExpired("{} certificate expired {} days ago".format(hostname, remaining.days))
    elif remaining < datetime.timedelta(days=buffer_days):
        # expires sooner than the buffer
        return remaining.days
    else:
        # everything is fine
        return

def ssl_valid_time_remaining(hostname):
    """Get the number of days left in a cert's lifetime."""
    expires = ssl_expiry_datetime(hostname)
    days_left = expires - datetime.datetime.utcnow()
    if vars.verbose:
        print( "{} SSL certific expires in {} on {}".format( hostname, days_left, expires.isoformat() ) )
    return days_left

def ssl_expiry_datetime(hostname):
    ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'

    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(4.0)
    try:
        conn.connect((hostname, 443))
    except socket.timeout:
        print("\n!! Timed out trying to connect to {}\n".format(hostname))
        raise
    ssl_info = conn.getpeercert()
    # parse the string from the certificate into a Python datetime object
    return datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)
