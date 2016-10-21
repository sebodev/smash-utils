"""Checks for SSL certificates that are about to expire"""

import socket
import ssl
import datetime
import lib.webfaction
from runner import vars

def main(domain_or_server=None):
    """ checks when a domain expires.
    domain can also be a Webfaction server entry."""

    d_or_s = domain_or_server

    if d_or_s in vars.servers:
        check_server(d_or_s)
    elif d_or_s:
        check_domain(d_or_s)
    else:
        d_or_s = input("Enter a domain or a Webfaction server entry to check: ")
        main(d_or_s)

def check_domain(domain):
    if not ssl_expires_soon(domain,  suppressErrors=False):
        print("{} is in good shape. It's SSL certificate doesn't expire for {} days.".format(domain, ssl_valid_time_remaining(domain).days))

def check_server(server):
    no_problems = True
    wf, wf_id = lib.webfaction.xmlrpc_connect(server)

    for data in wf.list_domains(wf_id):
        if ssl_expires_soon(data["domain"]):
            print("x", end="")
            no_problems = False
        else:
            print(".", end="", flush=True)
    if no_problems:
        print("\nYou're looking good. All of your SSL certificates are up to date.")

def ssl_expires_soon(domain, suppressErrors=True):
    """ Returns True and prints out a warning if a website's SSL certificate expires within 50 days. """
    try:
        days_left = ssl_expires_in(domain, 50)
        if days_left is not None:
            print("Better watch out. {} expires in {} days".format(domain, days_left))
            return True
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
    conn.settimeout(3.0)

    conn.connect((hostname, 443))
    ssl_info = conn.getpeercert()
    # parse the string from the certificate into a Python datetime object
    return datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)
