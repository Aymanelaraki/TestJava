
import sendmail
import Template
import datetime
import timedelta
import subprocess
import glob
import shutil
import time
import urllib.request
import os
import os.path 

#Is Java existent in this computer ?
path = 'C:\Program Files (x86)\Java'
path1 = 'C:\Program Files (x86)\Oracle'
isFolder = os.path.exists(path)  
isFolder1 = os.path.exists(path1)  
print(isFolder) 
print(isFolder1) 

#If not, it will download and install it
if isFolder or isFolder1 is 'True':
                    os.system("java -version")
                    
def download(cookie, license, url, filename):
    print (url)
    print (filename)
    opener = urllib.request.build_opener()
    opener.addheaders.append((cookie, license))
    f = opener.open(url)
    with open(filename, 'wb+') as save:
        save.write(f.read())

cookie = 'Cookie'
license = 'oraclelicense=accept-securebackup-cookie'
url = 'http://download.oracle.com/otn-pub/java/jdk/8u131-b11/d54c1d3a095b4ff2b6607d096fa80163/jdk-8u131-windows-x64.exe'
filename = 'jdk-8u131-windows-x64.exe'

download(cookie, license, url, filename)

os.startfile(("C:\Users\User\.spyder-py3\jdk-8u131-windows-x64.exe")

#Latest Update to Java, I took a whole "Java updating" script from the community
def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds())

def make_cookies(cookies):
    cookieTemplate = Template('.${domain}\t${allmachines}\t${path}\t${secure}\t${expiration}\t${name}\t${value}\n')
    tomorrow = unix_time(datetime.now() + timedelta(days=1))
    d = dict(
        domain = 'oracle.com',
        allmachines = 'TRUE',
        path = '/',
        secure = 'FALSE',
        expiration = tomorrow,
        name = 'oraclelicense',
        value = 'accept-securebackup-cookie'
    )
    cookieString = cookieTemplate.safe_substitute(d)
    with open(cookies,'w') as f:
        f.write(cookieString)

def find_latest_update(version):
    versionUrl = Template("http://java.com/en/download/installed${version}.jsp")
    url = versionUrl.safe_substitute(version=version)
    output = subprocess.check_output(["wget", "-qO-", url])
    tagLine = Template("latest${version}Version").safe_substitute(version=version)
    for line in output.split('\n'):
        if tagLine in line:
            #print line
            (_, versionString, _) = line.split("'")
            # print versionString # 1.8.0_101
            (_, update) = versionString.split("_")
            # print update # 101
            return int(update)

def download_java(kinds, version, update, cookies):
    site = "http://download.oracle.com/otn-pub/java/jdk"
    b = 13 # not sure how often this changes
    archList = ["windows-x64", "windows-i586"]
    urlTemplate = Template("${site}/${version}u${update}-b${b}/${package}-${version}u${update}-${arch}.exe")
    for arch in archList:
        for package in kinds:
            d = dict(
                site = site,
                package = package,
                version = version,
                update = update,
                b = b,
                arch = arch
            )
            url = urlTemplate.safe_substitute(d)
            print ("Downloading %s") % (url)
            cookieFlag = "--load-cookies=%s" % (cookies)
            subprocess.call(["wget", "-q", cookieFlag, url],
                            cwd = os.getcwd())

def copy_java_contents(kinds, version, update, msiDestination):
    # For each executable with correct version and update
    patternTemplate=Template("${kind}-${version}u${update}-windows-*.exe")
    for kind in kinds:
        d = dict(
            kind = kind,
            version = version,
            update = update
        )
        pattern = patternTemplate.safe_substitute(d)
        olddir = os.getcwd()
        for file in glob.glob(pattern):
            print (file)
            # - Make a directory in wpkg/software
            (_, _, _, archexe) = file.split("-")
            if archexe=="i586.exe":
                arch = "x86"
            elif archexe=="x64.exe":
                arch = "x64"
            path = msiDestination + (r'\%s\%d\%d-%s '[:-1] % (kind,
                                                              version,
                                                              update,
                                                              arch))
            print ("Will makedirs(%s) if needed") % (path)
            if not os.path.isdir(path):
                os.makedirs(path, mode = 0o777)
            # - Run the executable to extract contents to temp
            print ("Starting %s") % (file)
            proc = subprocess.Popen([file], shell=False)
            print ("Started %s as %s") % (file, proc)
            # - Copy contents to wpkg directory
            extract_parent = os.path.join(os.environ['USERPROFILE'], 'Appdata',
                                          'LocalLow', 'Oracle', 'Java')
            print ("Checking for extract parent directory %s...") % (extract_parent),
            while not os.path.isdir(extract_parent):
                time.sleep(1)
            os.chdir(extract_parent)
            print ("done.")
            if arch=="x64":
                tempFolder = "%s1.%d.0_%d_%s" % (kind, version, update, arch)
            else:
                tempFolder = "%s1.%d.0_%d" % (kind, version, update)
            print ("Checking for extract directory...",)
            while not os.path.isdir(tempFolder):
                time.sleep(1)
            os.chdir(tempFolder)
            print ("done.")
            print ("Sleeping for 10 seconds...",)
            time.sleep(10)
            print ("done.")
            # - Kill the executable
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)])
            print ("Copying files...",)
            for f in glob.glob("*.msi"):
                shutil.copy(f,path)
            for f in glob.glob("*.cab"):
                shutil.copy(f,path)
            print ("done.")
            os.chdir('..')
            # - Remove contents from temp
            shutil.rmtree(tempFolder)
            os.chdir(olddir)

def update_java_packages(kinds, version, update, wpkgRoot, branches):
    for kind in kinds:
        for branch in branches:
            sourceXML = "%s-%d.xml" % (kind, version)
            with open(sourceXML) as templateXML:
                lines=templateXML.readlines()
            template = Template( ''.join(lines) )
            d=dict(update=update)
            targetXML = os.path.join(wpkgRoot,branch,'packages',sourceXML)
            with open(targetXML,'w') as packageXML:
                packageXML.writelines(template.safe_substitute(d))

def check_local_update(msiDestination, version):
    localfile = os.path.join(msiDestination, 'jdk', str(version),
                             'localVersion.txt')

    try:
        with open(localfile, 'r') as f:
            lines = f.readlines()
            update = int(lines[0])
    except IOError:
        update = 0
    return int(update)

def write_local_update(msiDestination, version, update):
    localVersionFile = os.path.join(msiDestination, 'jdk', str(version),
                                    'localVersion.txt')
    with open(localVersionFile, 'w') as f:
        f.write(str(update))

if __name__ == "__main__":
    version = 8
    cookies = 'cookies.txt'
    kinds = ["jdk", "jre"]
    #wpkgRoot = r'\\some.server.fqdn\wpkg '[:-1]
    wpkgRoot = r'c:\users\someuser\desktop\wpkg-tmp '[:-1]
    msiDestination = wpkgRoot+r'\software '[:-1]
    branches = [ 'dev', 'stable' ]

    print ("Checking for latest update to Java %d") % (version)
    update = find_latest_update(version = version)
    print ("It's update %s") % (update)
    localUpdate = check_local_update(msiDestination = msiDestination,
                                     version = version)
    if localUpdate < update:
        print ("Local copy (%d) is out of date.") % (localUpdate)
        print ("Making cookies")
        make_cookies(cookies)
        download_java(kinds = kinds,
                      version = version,
                      update = update,
                      cookies = cookies)
        copy_java_contents(kinds = kinds,
                           version = version,
                           update = update,
                           msiDestination = msiDestination)
        update_java_packages(kinds = kinds,
                             version = version,
                             update = update,
                             wpkgRoot = wpkgRoot,
                             branches = branches)
        write_local_update(msiDestination = msiDestination,
                           version = version, update = update)
    else:
        print ("Local copy (%d) is current.") % (localUpdate)
        

#Java version verification
os.system("java -version")


#Sending a Status Email
import smtplib

#Ports 465 and 587 are intended for email client to email server communication - sending email
server = smtplib.SMTP('smtp.gmail.com', 587)

#starttls() is a way to take an existing insecure connection and upgrade it to a secure connection using SSL/TLS.
server.starttls()

#Next, log in to the server
server.login("#SENDER_EMAIL", "#SENDER_PASSWORD")

msg = "Java is correctly installed in your computer"

#Send the mail
server.sendmail("#SENDER_EMAIL", "#RECEIVER_REMAIL", msg)