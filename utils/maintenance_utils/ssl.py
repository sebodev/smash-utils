"""Checks for SSL certificates that are about to expire"""

import socket
import ssl
import datetime
import subprocess
import os
import time
import traceback

import lib.webfaction
from runner import smash_vars
import lib.errors
from lib import errors
from lib import servers
from lib import ssh
from lib import webfaction
from lib import domains

#If CHECK_STRICTLY is false we try to ignore domains that where never set up with an SSL certificate or that cannot be reached
STRICT_CHECKING = False

class CertError(lib.errors.SmashException):
    def __init__(self, title, reason, domain, err):
        if smash_vars.verbose:
            print("\n!!", reason, "\n")
        super(CertError, self).__init__(domain+" "+title, str(err))
        self.title = title

class AlreadyExpired(CertError):
    def __init__(self, message):
        super(AlreadyExpired, self).__init__("expired", message, "!! This certificate has expired")

def install(server):
    print("If it's not already installed, follow the LetsEncrypt installation instructions at https://github.com/will-in-wi/letsencrypt-webfaction#system-ruby")
    input("press enter when done")
    # ssh.run(server, "rbenv install 2.3.1") # Installs Ruby 2.3.1
    # ssh.run(server, "rbenv local 2.3.1") # Sets Ruby 2.3.1 as the default version in the current folder.
    # ssh.run(server, "gem install letsencrypt_webfaction") # Installs this utility from RubyGems.
    # ssh.run(server, "rbenv rehash") # Makes RBenv aware of the letsencrypt_webfaction utility.
    # ssh.run(server, "rm .ruby-version") # Unsets Ruby 2.3.1 as the default version in the current folder.

def add(server, app):
    assert(server)
    install(server)
    s_info = servers.get(server)
    assert(s_info["is-webfaction-server"])

    email = smash_vars.credentials_conf["lastpass"]["username"]
    domains = ",".join(webfaction.get_domains(server, app))
    app_dir = webfaction.get_app_dir(server, app)
    user = s_info["webfaction-username"]
    passwd = s_info["webfaction-password"]

    #example command
    #letsencrypt_webfaction --letsencrypt_account_email hi@sitesmash.com --domains mojaworks.com,www.mojaworks.com --public /home/moja/webapps/moja/ --username moja --password y3ozq3E3IcVZ

    cmd = 'source $HOME/.bash_profile; letsencrypt_webfaction --letsencrypt_account_email' \
          ' {email} --domains {domains} --public {app_dir} --username {user} --password "{passwd}"'.format(**locals())
    ssh.run2(server, cmd)

    def website_info(server, domain):
        """returns a dictionary with the keys
        id, name, ip, https, subdomains, apps"""
        wf, wf_id = webfaction.connect(server)
        sites = wf.list_websites(wf_id)
        for site in sites:
            if domain in site["subdomains"]:
                return site

    domain = webfaction.get_domains(server, app)[0]
    cert_name = domain.replace(".", "_")
    info = website_info(server, domain)

    if info["name"]+"_https" in webfaction.get_website(server, domain):
        if smash_vars.verbose:
            print('updating website with site_name={name}, ip={ip}, https=True, domains={subdomains}, cert={cert_name}, apps={apps}'
                  .format(cert_name=cert_name, apps=info["website_apps"][0], **info))
        wf, wf_id = webfaction.connect(server, version=2)
        wf.update_website(wf_id, info["name"]+"_https", info["ip"], True, info["subdomains"], cert_name, info["website_apps"][0])
    else:
        if smash_vars.verbose:
            print("creating website where site_name={name}_https, ip={ip}, https=True, domains={subdomains}, cert={cert_name}, apps={apps}"
                  .format(cert_name=cert_name, apps=info["website_apps"][0], **info))
        wf, wf_id = webfaction.connect(server, version=2)
        wf.create_website(wf_id, info["name"]+"_https", info["ip"], True, info["subdomains"], cert_name, info["website_apps"][0])


def main(domain_or_server=None):
    """ checks when a domain expires.
    domain can also be a Webfaction server entry."""

    def prompt_install_failed_certs(failed):
        failed = list(filter(None, failed))
        if not failed:
            return
        print("\n" + "*"*80)
        failed_domains = [f[1] for f in failed if f]
        print("\nThe following websites need updated SSL certificates:", ", ".join(failed_domains))
        if not input("Would you like to update these SSL certificates [Yes/no]: ").lower().startswith("n"):
             for server, domain in failed:
                 if servers.get(server, "is-webfaction-server"):
                     add(server, domain)
                 else:
                     print("{} is not a webfaction server. Skipping".format(server))

    d_or_s = domain_or_server

    if d_or_s in smash_vars.servers:
        failed = check_server(d_or_s)
        prompt_install_failed_certs(failed)
    elif d_or_s:
        check_domain(d_or_s)
    else:
        d_or_s = input("Enter a domain or a Webfaction server entry to check. Leave blank to check them all: ")
        if not d_or_s:
            failed = []
            for server in smash_vars.servers:
                print("\nChecking " + server)
                try:
                    failed.append( check_server(server, print_results=smash_vars.verbose) )
                except lib.errors.LoginError:
                    print("unable to login to {}".format(server))
            if not failed:
                print("Everything is in tip top shape.")
            else:
                prompt_install_failed_certs(failed)

        else:
            main(d_or_s)

def check_domain(domain):
    try:
        cert = CertInfo(domain)
        days_left = cert.valid_time_remaining().days
        if not cert.expires_soon(suppressErrors=False):
            print("{} is in good shape. It's SSL certificate doesn't expire for {} days.".format(domain, days_left))
        return days_left

    except AlreadyExpired:
        res = input("Would you like me to install a new SSL certificate on the server [Y/n]")
        if not res.lower().startswith("n"):
            return add(**domains.get_server_app(domain))
    except CertError as err:
        if err.title == "connection_refused":
            res = input("Something is wrong with the SSl certificate (it could be trying to use webfaction's default SSL certificate),\n"
                        "Would you like me to install a new SSL certificate on the server [Y/n]")
            if not res.lower().startswith("n"):
                return add(**domains.get_server_app(domain))
        else:
            raise

def check_server(server, print_results=True):
    no_problems = True
    failed = []

    if servers.get(server, "is-webfaction-server"):
        #by getting the domains from Webfaction this way we can prevent us from checking every subdomain
        #when it's only the domain that has to be checked
        wf, wf_id = lib.webfaction.connect(server)
        domains = [data["domain"] for data in wf.list_domains(wf_id)]
    else:
        domains = servers.get(server, "domains")
        #remove entries that start with www. if the non-www. domain is in the list
        domains = filter(lambda d: d.startswith("www.") and d.replace("www.", "") not in domains, domains)

    for domain in domains:

        try:
            cert = CertInfo(domain)
            if cert.expires_soon():
                print("!", end="", flush=True)
                failed.append( (server, domain) )
            else:
                print(".", end="", flush=True)

        except AlreadyExpired:
            res = input("Would you like me to install a new SSL certificate on the website {} [Y/n]".format(data["domain"]))
            if not res.lower().startswith("n"):
                        return add(**domains.get_server_app(data["domain"]))
        except CertError as err:
            if not STRICT_CHECKING or err.title in ("connection_refused", "timed_out", "ssl_error_or_not_configured", "does_not_exist"):
                print("-", end="", flush=True)
            else:
                if print_results:
                    traceback.print_exc()
                    print()
                failed.append( (server, domain) )

    if not failed and print_results:
        print("\nYou're looking good. All of your SSL certificates are up to date.")

    return failed





class CertInfo:

    def __init__(self, domain):
        self.domain = domain
        self.datetime = self._expiry_datetime()

    def expires_soon(self, suppressErrors=True):
        """ Returns days_left and prints out a warning if a website's SSL certificate expires within 50 days. """
        domain = self.domain
        try:
            days_left = self.expires_in(50)
            if days_left is not None:
                print("Better watch out. {} expires in {} days".format(domain, days_left))
                return days_left
            return False
        except CertError as err:
            if not suppressErrors and (err.title == "ssl_error" or err.title == "ip_not_found"):
                if not smash_vars.verbose: #The error would have already been printed
                    print(err.message)

    def expires_in(self, buffer_days=14):
        """Check if SSL cert expires within `buffer_days`.

        Raises `AlreadyExpired` if the cert is past due
        """
        remaining = self.valid_time_remaining()

        # if the cert expires in less than two weeks, we should reissue it
        if remaining < datetime.timedelta(days=0):
            # cert has already expired - uhoh!
            raise AlreadyExpired("{} certificate expired {} days ago".format(self.domain, remaining.days))
        elif remaining < datetime.timedelta(days=buffer_days):
            # expires sooner than the buffer
            return remaining.days
        else:
            # everything is fine
            return

    def valid_time_remaining(self):
        """Get the number of days left in a cert's lifetime."""
        expires = self.datetime
        days_left = expires - datetime.datetime.utcnow()
        if smash_vars.verbose:
            print( "{} SSL certific expires in {} on {}".format( self.domain, days_left, expires.isoformat() ) )
        return days_left

    def _expiry_datetime(self):
        """ Gets the datetime, raising a CertError on failure """
        ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'
        ssl_info = self.get_cert()
        return datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)

    def get_cert(self):
        context = ssl.create_default_context()
        conn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=self.domain,
        )
        # 3 second timeout because Lambda has runtime limitations
        conn.settimeout(4.0)

        try:
            conn.connect((self.domain, 443))
        except socket.timeout as err:
            raise (
                    CertError(
                        "timed_out",
                        "Timed out trying to connect to {}".format(self.domain),
                        self.domain,
                        err
                    )
                  ) from None

        except ConnectionRefusedError as err:
            raise (
                    CertError(
                    "connection_refused",
                    "Invalid certificate or certificate doesn't exist for {}".format(self.domain),
                    self.domain,
                    err
                    )
                  ) from None

        except ssl.SSLError as err:
            raise (
                    CertError(
                    "ssl_error",
                    "Received the following: {}".format(err),
                    self.domain,
                    err
                    )
                  ) from None

        except ConnectionResetError as err:
            raise (
                    CertError(
                    "ssl_error",
                    "Received the following: {}".format(err),
                    self.domain,
                    err
                    )
                  ) from None

        except ssl.CertificateError as err:
            raise (
                    CertError(
                    "ssl_error_or_not_configured",
                    "SSL Error, probably because SSL was never configured for: {}".format(self.domain),
                    self.domain,
                    err
                    )
                  ) from None

        except socket.gaierror as err:
            raise (
                    CertError(
                    "does_not_exist",
                    "Couldn't find an IP address for {}. Does this website even exist?".format(self.domain),
                    self.domain,
                    err
                    )
                  ) from None

        return conn.getpeercert()
