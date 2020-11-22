import glob
import os
import re
import sys
from datetime import datetime

import gitlab


def get_project_and_issue_ids(dryrun = False):
    project = get_project_id()
    issue = get_issue_id(project, dryrun)
    return project, issue

def get_project_id():
    # private token or personal token authentication
    if "PERSONAL_TOKEN" in os.environ:
        gl = gitlab.Gitlab('https://gitlab.doc.ic.ac.uk/', private_token= os.environ['PERSONAL_TOKEN'] )
    else:
        print("ERROR: you need to defined an environment variable PERSONAL_TOKEN with you access token for gitlab")
        exit(1)

    # Search projects
    command = os.popen("git config --local remote.origin.url")
    url = command.read()[:-1]
    pattern = '(AIRL/)([A-z0-9-_+\/]+\/)*([A-z0-9-_+.]+)'
    reponame = ''.join(re.findall(pattern, url)[0])
    reponame = reponame[:-4] #removing the .git
    print(reponame)
    projects = gl.projects.list(search=reponame, membership=True, search_namespaces=True)
    
    if(len(projects)!=1):
        print("project '"+reponame+"' not found. Exit")
        exit(2)
    else:
        print("Project '"+reponame+"' found")
        
    project = projects[0]
    return project

def get_issue_id(project, dryrun=False):
    
    issue_name = "GITLAB_NOTEBOOK"
    command = ""

    if "CI_COMMIT_TITLE" in os.environ:
        pattern ='(\[GN[ -_]CREATE[ -_]|\[GN[ -_])(.*?)(\])'
        results = re.findall(pattern, os.environ["CI_COMMIT_TITLE"])
        if(len(results) and len(results[0])==3):
            issue_name="GITLAB_NOTEBOOK "+results[0][1]
            command = results[0][0][4:-1]

    print("issue name should be: "+ issue_name +" Command is: "+command) 
     

    issues = project.issues.list()
    print("looking for issues to publish the report: project contains "+str(len(issues)) + " issue(s)")
    
    for iss in issues:
        if(iss.title==issue_name):
            print("corresponding issue found")
            issue = iss
            if(command == "CREATE"):
                print("ERROR the command was CREATE but an issue with the same name already exists")
                exit(3)
            break
    if('issue' not in locals()): # no corresponding issue
        if(command=="CREATE" or issue_name == "GITLAB_NOTEBOOK"):
            print("no corresponding issue found. Creating a new one to host results")
            if(not dryrun):
                issue = create_issue(project, issue_name)
                return issue
            else:
                return None
        else:
            print("ERROR: No corresponding issue found and command is not CREATE")
            exit(4)

    return issue



def create_content(project, data_path, reportmd_folder_path):
    reportfile= open(os.path.join(reportmd_folder_path, "report.md"), "r")
    content = reportfile.read()

    pattern = '(/UPLOAD/)([A-z0-9-_+\/]+\/)*([A-z0-9-_+.*]+)'
    results = re.findall(pattern, content)
    #print(results)

    for local_file in results:
        if "*" in local_file[2]:
            wild_card_expanded = sorted(glob.glob(data_path+"/"+local_file[1]+local_file[2]))
            if(len(wild_card_expanded)==0):
                print("WARNING: Expanded wildcard `" + data_path +"/"+ local_file[1]+local_file[2] +"' led to zero files. Nothing will be uploaded")
            else:
                urls=[]
                res = list(filter(lambda x: local_file[0]+local_file[1]+local_file[2] in x, content.split("\n")))
                if(len(res)>1):
                    print("WARNING: More than one line matching the filename reference in wildcard. This situation has not been anticipated and might cause issues.")
                template_line=res[0]
                for wild_card_file in wild_card_expanded:
                    if(os.path.exists( wild_card_file)):
                        print("uploading " + wild_card_file)
                        uploaded_file = project.upload( wild_card_file,filepath= wild_card_file)
                        tmpline=template_line
                        urls.append(tmpline.replace( local_file[0]+local_file[1]+local_file[2],uploaded_file["url"]))
                    else:
                        print("file (from wildcard) " + wild_card_file +" not found.")
            
                content = content.replace( template_line ,"\n".join(urls))
            
        else:    
            if(os.path.exists(data_path +"/"+ local_file[1]+local_file[2])):
                print("uploading " + local_file[1] + local_file[2])
                uploaded_file = project.upload(local_file[2], filepath=data_path +"/"+ local_file[1]+local_file[2]) 
                print("updating report with: " + uploaded_file["url"])
                content = content.replace( local_file[0]+local_file[1]+local_file[2],uploaded_file["url"])
            else:
                print("file "+data_path +"/"+ local_file[1]+local_file[2]+" not found.")


    pattern = '(/IMPORT/)([A-z0-9-_+\/]+\/)*([A-z0-9-_+.]+)'
    results = re.findall(pattern, content)
    #print(results)

    for local_file in results:
        if(os.path.exists(data_path +"/"+ local_file[1]+local_file[2])):
            print("IMPORT " + local_file[1] + local_file[2])
            contentfile= open( data_path +"/"+ local_file[1] + local_file[2] ,"r")
            print("updating report with content of the file")
            content = content.replace( local_file[0]+local_file[1]+local_file[2],contentfile.read())
        else:
            print("file "+data_path +"/"+ local_file[1]+local_file[2] + " not found.")

    content = "<details><summary>Click to expand!</summary>\n\n " + content + "\n\n</details>"
    #print(content)
    return content


def create_issue(project, issue_name):
    labels = project.labels.list()

    found = False
    for label in labels:
        if label.name=="gitlab_notebook":
            found = True

    if not found:
        print("Creating label for gitlab_notebook")
        label = project.labels.create({'name': 'gitlab_notebook', 'color': '#5843AD'})
    else:
        print("Label already existing")
    
    print("Creating new issue named " + issue_name)
    return (project.issues.create({'title': issue_name,
                                   'description': 'The results will be automatically saved here. Enjoy!',
                                   'labels': ['gitlab_notebook']}))
    
def populate_issue(data_path, reportmd_folder_path):
    
    project, issue = get_project_and_issue_ids()
    
    body =  "ID:"+  str(len(issue.discussions.list())) + " Date: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if "CI_COMMIT_SHORT_SHA" in os.environ:
        body += " Commit:" + os.environ['CI_COMMIT_SHORT_SHA'] + " - " + os.environ["CI_COMMIT_TITLE"]
    else:
        body += " Manual push"

    body += "\nData saved here: "+ os.path.abspath(data_path)
    
    discussion = issue.discussions.create({'body': body +"\n\n"+ create_content(project, data_path, reportmd_folder_path) })

def main(argv):
    if len(argv)>=1 and argv[0] == '--find_project':
        print("Checking that we can find the project id and that we have the rights to publish issues")
        get_project_and_issue_ids(dryrun=True)
        return
    elif len(argv) >= 2:
        data_path = argv[0]
        reportmd_folder_path = argv[1]
    elif len(argv) == 1:
        data_path = argv[0]
        reportmd_folder_path = os.getcwd()
    else:
        data_path = os.getcwd()
        reportmd_folder_path = os.getcwd()

    print("Generating report")
    populate_issue(data_path, reportmd_folder_path)
        

if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
