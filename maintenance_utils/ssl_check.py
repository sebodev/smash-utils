"""Checks for SSL certificates that are about to expire"""

import socket
import ssl
import datetime
import subprocess
import os
import time

import lib.webfaction
from runner import vars
from lib.errors import SmashException
import lib.errors
from lib import servers
from lib import ssh
from lib import webfaction
from lib import domains

class AlreadyExpired(SmashException):
    pass

def install(server):
    print("If it's not already installed, follow the LetsEncrypt installation instructions at https://github.com/will-in-wi/letsencrypt-webfaction#system-ruby")
    input("press enter when done")
    # ssh.run(server, "rbenv install 2.3.1") # Installs Ruby 2.3.1
    # ssh.run(server, "rbenv local 2.3.1") # Sets Ruby 2.3.1 as the default version in the current folder.
    # ssh.run(server, "gem install letsencrypt_webfaction") # Installs this utility from RubyGems.
    # ssh.run(server, "rbenv rehash") # Makes RBenv aware of the letsencrypt_webfaction utility.
    # ssh.run(server, "rm .ruby-version") # Unsets Ruby 2.3.1 as the default version in the current folder.


def add(domain_or_server):
    return add_using_domain(domain_or_server)
    #letsencrypt_webfaction --letsencrypt_account_email hi@sitesmash.com --domains mojaworks.com,www.mojaworks.com --public /home/moja/webapps/moja/ --username moja --password y3ozq3E3IcVZ

def add_using_server(server_name, app):
    install(server_name)
    s_info = servers.get(server_name)
    assert(s_info["is-webfaction-server"])
    email = vars.credentials_conf["lastpass"]["username"]
    cmd = 'source $HOME/.bash_profile; letsencrypt_webfaction --letsencrypt_account_email {} --domains {} --public {} --username {} --password "{}"'.format(
            email,
            ",".join(webfaction.get_domains(server_name, app)),
            webfaction.get_app_dir(server_name, app),
            s_info["webfaction-username"],
            s_info["webfaction-password"]
        )
    ssh.run(server_name, cmd)


    domain = webfaction.get_domains(server_name, app)[0]
    cert_name = domain.replace(".", "_")
    info = website_info(server_name, domain)

    if info["name"]+"_https" in webfaction.get_website(server_name, domain):
        if vars.verbose:
            print('updating website with site_name={name}, ip={ip}, https=True, domains={subdomains}, cert={cert_name}, apps={apps}'
                  .format(cert_name=cert_name, apps=info["website_apps"][0], **info))
        wf, wf_id = webfaction.connect(server_name, version=2)
        wf.update_website(wf_id, "esa_https", info["ip"], True, info["subdomains"], cert_name, info["website_apps"][0])
    else:
        if vars.verbose:
            print("creating website where site_name={name}_https, ip={ip}, https=True, domains={subdomains}, cert={cert_name}, apps={apps}"
                  .format(cert_name=cert_name, apps=info["website_apps"][0], **info))
        wf, wf_id = webfaction.connect(server_name, version=2)
        wf.create_website(wf_id, info["name"]+"_https", info["ip"], True, info["subdomains"], cert_name, info["website_apps"][0])

def add_using_domain(domain):
    _, server, app = domains.info(domain)
    assert(server)
    return add_using_server(server, app)

def website_info(server, domain):
    """returns a dictionary with the keys
    id, name, ip, https, subdomains, apps"""
    wf, wf_id = webfaction.connect(server)
    sites = wf.list_websites(wf_id)
    for site in sites:
        if domain in site["subdomains"]:
            return site

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
                try:
                    if servers.get(server, "is-webfaction-server"):
                        res.append( check_server(server, print_results=False) )
                    else:
                        print("{} is not a webfaction server. skipping".format(server))
                except lib.errors.LoginError:
                    print("unable to login to {}".format(server))
            if all(res):
                print("Everything is in tip top shape.")

        else:
            main(d_or_s)

def check_domain(domain):
    try:
        days_left = ssl_valid_time_remaining(domain).days
        if not ssl_expires_soon(domain,  suppressErrors=False):
            print("{} is in good shape. It's SSL certificate doesn't expire for {} days.".format(domain, days_left))
        return days_left

    except AlreadyExpired:
        res = input("Would you like me to install a new SSL certificate on the server [Y/n]")
        if not res.lower().startswith("n"):
            add_using_domain(domain)

def check_server(server, print_results=True):
        no_problems = True
        wf, wf_id = lib.webfaction.connect(server)

        for data in wf.list_domains(wf_id):
            try:
                if ssl_expires_soon(data["domain"]):
                    print("!", end="")
                    no_problems = False
                else:
                    print(".", end="", flush=True)

            except AlreadyExpired:
                res = input("Would you like me to install a new SSL certificate on the website {} [Y/n]".format(data["domain"]))
                if not res.lower().startswith("n"):
                    add_using_server(data["domain"])

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
