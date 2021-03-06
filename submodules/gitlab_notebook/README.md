# GitLab Notebook

This project contains the scripts necessary to automatically use Gitlab as a laboratory notebook. 

## Automatic Triggers with GitLab CI

To enable this features: 
1) Run the following commands:
```
mkdir -p submodules
git submodule add ../../../AIRL_tools/gitlab_notebook ./submodules/gitlab_notebook
```
The url is relative to the url of your project, so here we assumed that you project is for instance located in `/Students_projects/My_Self/My_Project`
You will now have a folder named `submodules/gitlab_notebook` containing all the necessary scripts.

2) If you want to use the CI pipeline to manage the publication in the note book, add in your project a file named `.gitlab-ci.yml` containing:
```
include:
  - project: 'AIRL/AIRL_tools/gitlab_notebook'
    ref: master
    file: 'gitlab-ci-template.yml'
```

3) Gitlab_notebook requires that your reprository also has the `remote_builder` submodule. You just have to follow the first step of the instructions [here](https://gitlab.doc.ic.ac.uk/AIRL/airl_tools/remote_builder#automatic-triggers-with-gitlab-ci)

4) Make sure you have a compatible Runner associated with your project. If your project is in the AIRL group, you can use the group runner. You might want to disable the shared runners that might not be compatible with singularity (TBC).
5) In the setting of your gitlab project, in section `repository`, set the master branch as protected.
6) Login on the HPC (via ssh) and create the following folder: `mkdir ~/gitlab_notebook_experiments/`. Gitlab\_notebook will store all the results and images on this folder.
7) Add the following "app" in the `singularity.def` file of your project:
```
%apprun gen_job_scripts
    python3 PATH_TO_YOUR_REPOSITORY/submodules/gitlab_notebook/gen_job_script.py "$@"

```
Where `PATH_TO_YOUR_REPOSITORY` is the path to your repository in the container (not on the host).

8) In the project settings, under CI/CD, variables add the following variables. It is suggested to protect and mask these variables.
   - `PERSONAL_TOKEN` : Gitlab personal token. This token allows gitlab_notebook processes to submit issues and comments on your name. To generate this token, you have to go in your profile's settings, and in Access Tokens. You have to create a tokem with the api scope.
   - `SREGISTRY_TOKEN` : Sregistery token. This token allows gitlab_notebook to push the singularity images in your private collections on the AIRL_Registry. To generate this token you have go on the AIRL_Registry [website](http://155.198.186.42)(try [here](http://airl.doc.ic.ac.uk/) if that website link does not work), in the "token" menu under your account settings.
   - `REGISTRY_PATH` : The AIRL_Registry allows you to create multiple collections (for instance, one per project). This variable tells gitlab_notebook (more precisely, the remote_builder) where to store the generated images.  Example of proper path: `antoine/my-collection` (it needs to start with your account name).
   - `USERNAME` : Your Imperial username, that you would use to connect on the HPC (via ssh).
   - `SSH_PRIVATE_KEY` : The private RSA key from a pair of keys that you have created to access the HPC. You have to put the public key in the known_host file on the HPC. The variable should contain the headers of the key: "-----BEGIN RSA PRIVATE KEY -----" and "-----END RSA PRIVATE KEY-----".
   - `JSON_FILE` : This variable should contain either the path to a JSON file for the jobs generation (more info below), this file should be accessible from inside the container when running on the HPC; or directly the content of the JSON file. Here is an example of valid content for the variable: 
   - `SERVER_IP` : (OPTIONAL) You can set the IP of the machine used to execute the jobs. Uses by default the Imperial HPC.
```
   '{
 "wall_time" : "01:29:00",
 "nb_cores" : "32",
 "nb_runs": "10",
 "mem" : "3gb",
}
' 
```

9) (optional) if you have an analysis job (see below) you will have to add the following commands to it to generate the "report" and to publish it on the gitlab thread:
```
    CURPATH=$(pwd)
    cd PATH_TO_YOUR_REPOSITORY
    python3 ./submodules/gitlab_notebook/gen_report.py $CURPATH
```
Full example of an actual "analysis app":
```
%apprun analysis
    python3 /git/sferes2/exp/template_experiment/python/analysis.py "$@"
    CURPATH=$(pwd)
    cd /git/sferes2/exp/template_experiment/
    python3 ./submodules/gitlab_notebook/gen_report.py $CURPATH
```

The `"$@"` (the argument passed to the job) will contain the location of the results generated by all the previous jobs (usually in `~/gitlab_experiments/NAME\_OF\_YOUR\_IMAGE/`), while `$CURPATH` contains the path where the analysis job is executed, which is where the report.md will be looking for the files to be uploaded. 
  
Now, every `push` will activate a `pipeline` in gitlab which offers you the possibility to 1) build your singularity images and publish them in the AIRL\_Registry and 2) launch your experiments on the HPC.
The Gitlab\_Notebook publishes the results of your experiments as an additional thread in the issue called `GITLAB\_NOTEBOOK`. 

------
## Using JSON file structure to generate the job files for the HPC

The content of JSON_FILE (which can also be included in an actual json file) should contain at minimum:
```
{
 "wall_time" : "01:29:00",
 "nb_cores" : "32",
 "nb_runs": "10",
 "mem" : "3gb",
}
```
The provided values should match the [requirements of the HPC queues](https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/computing/job-sizing-guidance/high-throughput/)
It is possible to manually generate the job files by calling the `gen_job_scripts` app defined above.

Details and options available in the json:
- `"wall_time"`: time after which your experiments are killed
- `"nb_cores"`: number of cores your experiments will use. Be careful, Sferes uses all the cores of the machine by default, it your program uses more cores than requested, your experiments will be killed
- `"mem"`: amount of memory your experiments will use. Like "nb_cores" if your program exceeds the requested values it will be killed.
- `"nb_runs"`: Number of times each experiment is replicated.  
- `"res_dir"`: (default value "./") Base directory for the results. Default is "./"
- `"apps"`: (default value "") List of app names to be execute. If your container contains several app (e.g., one per variant/algorithm you want to test), you can create a list `"apps":["algo_1","algo_2",""]`. `""` refers to the default run_script.
- `"args"`: (default value "") arguments to be passed to the experiments (currently, the same arguments are passed to all the apps)
- `"analysis"`: (default behaviour: analysis job disabled) Name of the app that will execute the data anaylisis. The data analysis is a job that is executed only when all the other jobs are finished. 
- `"wall_time_analysis"`: (default value "00:29:00") specific wall_time for the analysis job (allows this job to run a in faster queue).
- `"nb_cores_ analysis"`: (default value "1") specific nb_cores for the analysis job (allows this job to run a in faster queue).
- `"mem_analysis"`: (default value "1gb") specific mem for the analysis job (allows this job to run a in faster queue).
- `"nb_gpus"`: (default value "0") number of GPUs. WARNING: Using GPUs imposes using nb\_cpus = 4\*nb\_gpus and mem = 24\*nb\_gpus. More information [here](https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/computing/job-sizing-guidance/gpu/).
- `"run_options"`: (default value "") [singularity run option](https://sylabs.io/guides/3.4/user-guide/cli/singularity_run.html) like the `--nv` option if you need to use GPUs. 
- `"sync"`: (default value `{}`) dictionary of parameters for sending the information from the HPC nodes to our accessible result folder:
    - `"period_seconds"` (default value `None`) integer representing the number of seconds 
    between two consecutive synchronisation processes.
    - `"interrupt_main"` (default value "yes") if the value is "no" or "false", 
    then the synchronisation process does not interrupt the main `singularity run` process (it is launched in parallel to it).
- `"debug"`: (default value "no"). Used for launching the jobs in **debug mode**. 
In particular, if its value is `"yes"`, the temporary folder created for the visu_server is not deleted: it is sent with the results.
This option may be useful for testing new GitLab Notebook functionalities.

If you use vnc for the first time, it is important to log on the HPC (via ssh) and to run the following command: `module load vnc; vncserver` in order to create a password (that won't be used later).

Example of a more advanced `JSON_FILE`: 
```
'{
 "wall_time" : "01:29:00",
 "nb_cores" : "4",
 "mem" : "24gb",
 "nb_runs" : "10",
 "nb_gpus" : "1",
 "run_options" : "--nv",
 "apps" : ["high_mutation","low_mutation"],
 "analysis" : "analysis"
 "sync" : {"period_seconds": "3600", "interrupt_main": "yes"}
}'
```

------
## Names of Results Folders

The folders created on the nodes should all have a unique name.
Otherwise, some data may be lost when the final results are copied to `gitlab_notebook_experiments`.

Example of singularity runscript with random folder names:
```shell script
# Creating folder path name: 
# $(pwd)/results_{{ name executable }}
CURPATH=$(pwd)
cd /git/sferes2/
DIRNAME=results_$1
PATHNAME=$(date +%Y-%m-%d_%H_%M_%S)

# Creating random folder name of the form: 
# $(pwd)/results_{{ name executable }}/YYYY-MM-DD_hh_mm_ss.XXX
# where XXX will be replaced with random characters
mkdir -p $CURPATH/$DIRNAME/
tmp_dir=$(mktemp -d -p $CURPATH/$DIRNAME/ $PATHNAME.XXX)
mkdir -p $tmp_dir

# Launching experiment
echo Launching command \'build/exp/{{ project }}/$1 -d $tmp_dir\'
build/exp/{{ project }}/$1 -d $tmp_dir
```
where `{{ project }}` has to be replaced with the name of your project, 
as it appears in your `/git/sferes2/build/exp/` folder.

------
## Starting a VNC server

If you want to launch a VNC server before executing the script, 
you can add the following lines at the beginning of your singularity `runscript`:

```shell script
# Sleep random duration between 0 and 90 seconds, to prevent 2 vnc-servers from starting at the same time on the same host.
bash -c 'sleep $[ ( $RANDOM % 90 ) + 1 ]s' 

# Updating the HOME folder for the container, where the .Xauthority file will be created.
# That solution works iff the appropriate binding is performed (this is done automatically in gitlab-notebook jobs)
export HOME=/tmp/home
mkdir $HOME
D=$(/opt/TurboVNC/bin/vncserver 2>&1 | grep "Desktop" | awk '{print $3}' | sed 's/.*://g')
export DISPLAY=':'$D
```

------
## Manual Triggers

### Requirements

To use this feature you need to have `python>=3.6` and to install the required libraries:
```shell script
pip install python-gitlab==1.15.0
```

### Procedure

You can manually trigger an experiment with the following command from the root of your project repository:
```shell script
PERSONAL_TOKEN=<your-access-token> ./submodules/gitlab_notebook/launch_exp.sh [singularity run options...] 
```
where `[singularity run options...]` are all the arguments given to the container when the runscript is launched.

------
## Using commands through commit message. 

You can automatically start the build job and the launch exp job with by adding one or both of the following keywords in the message of you commit: 
`[start_exp]` and or `[start_build]`

If you want to create and use an issue with a different name (for instance to separate different experiments) you can use the follow commands: 

- `[GN_CREATE the name of your new issue]` this will create an issue with the name "GITLAB_NOTEBOOK the name of your new issue"
- `[GN the name of your new issue]` This will re-use the previously created issue "GITLAB_NOTEBOOK the name of your new issue"

If you attempt to use an issue name that has been be created first, the pipeline will show an error (this is made to avoid inadvertently creating issue because of typos).

Example of usage: 
`git commit -am "fix bugs in experiment 42 [start_build] [start_exp] [GN experiment 42]"`

------
## Quick Tips

Quick tips with git submodules

- To update the gitlab_notebook tools in your project, run `git submodule update --remote`
- To clone a project with the submodules already configures: `git clone --recurse-submodules https://your_url.git`
