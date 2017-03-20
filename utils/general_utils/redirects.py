"""
Creates redirect tables
Although some of these functions could be made to work with a different link checker, we recommend you install the linkchecker at http://wummel.github.io/linkchecker/
Any links that are still valid on the dev site are excluded from the redirect table
"""

import subprocess
import csv
from pathlib import Path
import os.path

import requests

from lib import domains
from runner import smash_vars

def main(old_site, new_site, csv):
    old_site = domains.normalize_domain(old_site)
    #new_site = domains.normalize_domain(new_site)

    #Once we move to Python 3.6 we could simply do
    #csv = Path(csv).resolve(strict=False)
    csv = Path(os.path.abspath(str(csv)))
    tmp_csv = smash_vars.tmp_dir/"redirects"/(old_site.replace("\\", "").replace(".", "_")+".csv")

    if not csv.parent.is_dir():
        csv.parent.mkdir()

    if not tmp_csv.parent.is_dir():
        tmp_csv.parent.mkdir()

    try:
        #when testing you can tack on a -r 1 to make it only recurse 1 layer deep during the link crawl
        cmd = "linkchecker http://{old_site} --file-output=csv/utf-8/{tmp_csv} --verbose -o none".format(**locals())
        if smash_vars.verbose:
            print("executing command:", cmd)
        subprocess.run(cmd)
    except FileNotFoundError:
        raise Exception("To use this command, install the link checker at http://wummel.github.io/linkchecker/ and at it to your path")

    #remove extra linkchecker info
    data = []
    with tmp_csv.open() as f:
        data = f.readlines()
    data = data[4:-1]
    data = "".join(data)
    tmp_csv.write_text(data)

    filter_redirects(tmp_csv, csv, old_site, new_site, delimiter=";")


def filter_redirects(in_file, out_file, old_domain, new_domain, delimiter="\t"):

    #Todo add options to remove js, css, images(png jpg jpeg ico) and misc(.xml) from results

    exclude_js_css = True
    exclude_images = True
    exclude_fonts = True
    exclude_misc = True

    exclude = []
    if exclude_js_css:
        exclude += [".js", ".css"]
    if exclude_images:
        exclude += [".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg"]
    if exclude_fonts:
        exclude += [".eot", ".woff", ".ttf", ".woff2"]
    if exclude_misc:
        exclude += [".xml"]
    if smash_vars.verbose:
        if exclude:
            print("skipping urls with the following extensions: " + ", ".join(exclude))
        else:
            print("All URLs will be processed and none will be skipped.")

    old_protocol = "http://"
    if new_domain.startswith("https://"):
        new_protocol = "https://"
    else:
        new_protocol = "http://"

    #If a lot of errors are being generated Change this to False
    #Otherwise we want to create redirects to clear up 404 errors and other errors on pages that outside sources could be linking to.
    skip_status_not_200 = False

    #these would only need to be different if the csv file was created with a program other than linkchecker
    url_column = 0
    file_has_header = False #ToDo make headers work better
    status_column = 2

    in_file = Path(in_file)
    out_file = Path(out_file)
    old_domain_original = old_domain
    old_domain = old_protocol + domains.normalize_domain(old_domain)
    new_domain = new_protocol + domains.normalize_domain(new_domain)

    if out_file.is_file():
        res = input("\n{} already exists. Continue anyways [yes/No]: ".format(out_file))
        if not res.lower().startswith("y"):
            exit()

    with in_file.open(newline='') as f:
        import csv
        data = csv.reader(f, delimiter=delimiter)
        data = list(data)
        csv_header = data[0]
        data = data[1:]

    dup_checker = set()
    for i, line in enumerate(data):
        skip = False
        url = line[url_column].strip()
        new_url = url
        if skip_status_not_200 and "200" not in line[status_column] and "OK" not in line[status_column]:
            skip = True
        elif url.startswith("#") or url.startswith("mailto:") or url.startswith("tel:") or url.startswith("javascript:") or url.startswith("sms:"):
            skip = True
        elif old_domain_original in url or url.startswith("/"):
            new_url = new_domain + "/" + url.replace("www.", "").replace(old_domain, "").lstrip("/")
        else:
            if "http://" in url or "https://" in url: #It's an external link
                skip = True
            else: #somehow we're recieving relative URLs with the beginning slash stripped off
                new_url = new_domain + "/" + url
        if new_url and new_url in dup_checker:
            skip = True
        else:
            for ext in exclude:
                if url.endswith(ext) or ext+"?" in url:
                    skip=True
                    break
        if skip:
            data[i] = None
        else:
            line[url_column] = new_url
            dup_checker.add(new_url)

    data = list(filter(None, data))

    print("Checking {} URLs...".format(len(data)))
    if smash_vars.verbose:
        print("The following URLs need redirects: ")

    data_out = [csv_header]
    for line in data:
        new_url = line[url_column]

        try:
            if not requests.get(new_url):
                line[url_column] = new_url #we're messing up with the data in the list named data, but we won't need to use that list again
                data_out.append(line)
                if smash_vars.verbose:
                    print(new_url)
                else:
                    print("x", end='', flush=True)
            else:
                print(".", end='', flush=True)
        except requests.exceptions.ConnectionError:
            #If we can't connect we don't want the URL appearing in the redirection table
            if smash_vars.verbose:
                print("unable to connect to {}".format(new_url))
            else:
                print("-", end='', flush=True)

    if not data_out:
        print("\nDid not find any URLs that need redirects")

    #ToDo fix how headers are handled. We logged an unneccessary request to http://domain/urlname that we know try to sem-fix on the next line
    data_out[0][url_column] = "urlname"

    try:
        with out_file.open("w", newline='') as f:
            csv = csv.writer(f, delimiter=delimiter)
            csv.writerows(data_out)
    except PermissionError:
        input("\n Something is preventing me from writing to {}. Could you close any programs that might have this file open, and then hit enter to try again.".format(out_file))
        with out_file.open("w", newline='') as f:
            csv = csv.writer(f, delimiter=delimiter)
            csv.writerows(data_out)

    if smash_vars.verbose:
        print("Done. You can review the results at {}".format(out_file))
