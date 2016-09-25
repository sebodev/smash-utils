import shutil, os, re
from runner import vars

# wpw_name contains the client name passed in from the command line
# wpw_level is a 1, 2, or 3 for the different wordpress warranty packages -- wpw 99, wpw+, and wpw & maintenance
wpw_name = None
wpw_level = None

client_dir = vars.google_drive_maintenance_dir / "clients" / wpw_name
client_website_guess = wpw_name.replace(" ", "").strip()
if re.search("(\....$)", client_website_guess) is None:
    client_website_guess += ".com"
client_website = input("what website is this for? Leave blank if it's {}: ".format(client_website_guess))
if not client_website:
    client_website = client_website_guess

def create_google_drive_folder():
    """create a folder for them in Google Drive
    The folder is a copy of _client folder template """
    try:
        client_template_dir = vars.google_drive_maintenance_dir / "clients" / "_client folder template"
        shutil.copytree(str(client_template_dir), str(client_dir))
        print("You can just hit ok on the Google Drive pop-up")
    except FileExistsError:
        response = input("%s already exists. Would you like to reconfigure this folder? This will delete some of the existing data [yes/No]:" % client_dir)
        if response.startswith("y"):
            pass
        else:
            print("okay, I'll leave your data alone")
            raise SystemExit

def create_contact_info_file():
    """create the contact info file, replacing it if it already exists"""

    contact_info_file = client_dir / "Contact Info.txt"

    try:
        os.remove(str(contact_info_file))
    except FileNotFoundError:
        pass

    contact_info_contents = ""
    def add_contact(contact, poc=True):
        if poc:
            print("\nHey, could I quickly get a little info about %s's point of contact" % wpw_name)
            poc_name = input("what is the name of the point of contact: ")
        else:
            poc_name = input("what is the contact's name: ")
        poc_email = input("What is {}'s email: ".format(poc_name))
        poc_phone = input("What is {}'s phone number: ".format(poc_name))
        poc_position = input("And What is {}'s position in the company (if known): ".format(poc_name))
        notes = input("Enter any other information you would like to add about %s: " % poc_name)

        if poc:
            contact_info_contents += "Point of contact"
        contact_info_contents += '''
        Name: {}
        Position: {}
        Email: {}
        Phone: {}'''.format(
                        poc_name,
                        poc_position,
                        poc_email,
                        poc_phone
                        )
        if notes:
            contact_info_contents += "notes: {}\n".format(notes)

    adding = "yes"
    while(adding.lower().startswith("y")):
        add_contact(wpw_name)
        adding = input("Would you like to add another contact [y/N]")

    contact_info_file.write_text(contact_info_contents)

def save_dns_info():
    import maintenance_utils.dns
    dns_file = client_dir / (client_website + " dns info.txt")
    print("client_website", client_website)
    maintenance_utils.dns.main(client_website, dns_file)

def check_ssl_expiration():
    import ssl_check
    res = ssl_check.ssl_expires_soon(client_website, suppressErrors=False)
    if res is None:
        print("couldn't check when the SSL certificate expires\n")

def initial_performance_test():
    import performance_test
    save_loc = client_dir / "initial-performance-test.csv"
    performance_test.run(client_website, save_loc)

def main(name, level):
    global wpw_name, wpw_level
    wpw_name = name
    wpw_level = level
    create_google_drive_folder()
    create_contact_info_file()
    save_dns_info()
    check_ssl_expiration()
    initial_performance_test()

# plugins_dir = vars.google_drive_maintenance_dir / "Maintenance Setup" / "Plugins"
# subprocess.call(r"pscp -scp -i %UserProfile%\.ssh\sitesmash.ppk -r sebodev@webfaction:{} {}".format(plugins_dir, vars.), shell=True)
# print( "copied (if everything went well) {} to {}".format(vars.current_project, vars.project_dir) )
# print("configuring")
