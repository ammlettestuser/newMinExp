import sys, os
import json
import stat
from operator import itemgetter

def copy_env():
    
    singularity_env = []
    for k in os.environ.keys():
        if k.startswith('CI_COMMIT'):
            singularity_env.append('export '+ k + '="' + os.environ[k]+'"')
    if len(singularity_env)==0:
        return ""
    return '\n'.join(singularity_env)


def get_job_file_name(exp_name, arg: str, list_previous_file_names):
    def get_first_2_letters(s):
        if not s:
            return ''
        elif len(s) == 1:
            return f'{s[0].upper()}'
        else:
            return f'{s[0].upper()}{s[1].lower()}'

    #  Creating standard name for job
    arg = arg\
        .replace(" ", "_")\
        .replace('=', '-')

    fname = f"{exp_name}_{arg}"

    #  If name too long, we reduce it (we keep only the 2 first letters of each component)
    #  Example: "alpha_beta" becomes "AlBe"
    if len(fname) <= 75:
        job_file_name = f'{fname}.job'
    else:
        arg = ''.join([''.join([get_first_2_letters(x)
                                for x in s.split('_')])
                       for s in arg.split('-')])

        new_fname = f"{exp_name}_{arg}"
        if len(new_fname) <= 75:
            job_file_name = f'{new_fname}.job'
        else:
            job_file_name = f'{new_fname[:75]}.job'

    #  If that name is already used, we remove the last letters and use additional digits
    index = 0
    while job_file_name in list_previous_file_names:
        job_file_name = job_file_name[:-7] + f"-{index:02}.job"
        index += 1
        if index >= 100:
            raise FileExistsError("Too many files with the same name have already been created")

    return job_file_name


def _sub_script(tpl, conf_file):
    if "SINGULARITY_CONTAINER" in os.environ:
        image = os.path.split(os.environ["SINGULARITY_CONTAINER"])
        image_location = image[0]
        image_name = image[1]
        print("image is " + image_location + "/" + image_name)
    else:
        print("This script should be executed from withing a container, typically via: 'singularity exec CONTAINER_NAME.sif python3 /PATH/TO/YOUR/REPO/submodules/gitlab_notebook/gen_job_script.py'")
        exit(1)

    print("json file: " + conf_file)
    
    if os.path.exists(conf_file) :
        conf = json.load(open(conf_file))  # type: dict
    else:
        conf = json.loads(conf_file)  # type: dict

    
    mem = conf['mem']
    nb_runs = conf['nb_runs']
    wall_time = conf['wall_time']


    try:
        run_options = conf['run_options']
    except:
        run_options = ""
        
    try:
        mem_analysis = conf['mem_analysis']
    except:
        mem_analysis = "1gb"
        
    try:
        wall_time_analysis = conf['wall_time_analysis']
    except:
        wall_time_analysis = "00:29:00"
        
    try:
        res_dir = conf['res_dir']
    except:
        res_dir = './'
        
    try:
        apps = conf['apps']
    except:
        apps = ['']
        
    try:
        nb_cores = conf['nb_cores']
    except:
        nb_cores = 1

    try:
        nb_gpus = conf['nb_gpus']
    except:
        nb_gpus = 0
        
    if nb_gpus == 0 :
        gpu = ""
        cuda_visible_devices_init = ""
    else:
        gpu = ":ngpus=" + str(nb_gpus) + ":gpu_type=RTX6000"
        cuda_visible_devices_init = "export SINGULARITYENV_CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
        print("WARNING, The HPC scheduler accepts only GPU jobs where nb_cpus = 4*nb_gpus and mem = 24 * nb_gpus")


        
        
    try:
        nb_cores_analysis = conf['nb_cores_analysis']
    except:
        nb_cores_analysis = 1


        
    try:
        args = conf['args']
    except:
        args = ['']
        
    if(nb_runs=='1'):
        array=''
    else:
        array="#PBS -J 1-"+nb_runs

    try:
        analysis = conf['analysis']
        apps.append(analysis)
    except:
        analysis = None

    dict_sync = conf.get("sync", {})

    period_sync = dict_sync.get("period_seconds", None)  # synchronisation period in seconds
    do_interrupt_main_process = dict_sync.get("interrupt_main", "yes")

    if period_sync:
        period_sync_str = str(period_sync)
        synchronisation_parallel = "synchronisation &\nSYNC=$!"
        synchronisation_kill = "kill $SYNC"
    else:
        period_sync_str = ""
        synchronisation_parallel = ""
        synchronisation_kill = ""

    if do_interrupt_main_process.lower().strip() in ['no', 'false']:
        kill_stop_child = ""
        kill_cont_child = ""
    else:
        kill_stop_child = "kill -STOP $CHILD"
        kill_cont_child = "kill -CONT $CHILD"

    debug = str(conf.get('debug', 'no'))
    if debug.strip().lower() in ['yes', 'true']:
        rsync_option_exclude_TMP_SING_DIR = ""
    else:
        rsync_option_exclude_TMP_SING_DIR = "--exclude=$TMP_SING_DIR"

    fnames = []
    analysis_name = [] 
    for app in apps:
        directory = res_dir + "/"+image_name[:-4]+"/" + app
        try:
            os.makedirs(directory)
        except:
            print("WARNING, dir:" + directory + " not be created")

        if(app !=''):
            run_app = "--app "+app
            exp_name = (app + "_" + image_name)
        else:
            run_app = app
            exp_name = (image_name)
            
        personal_token =""
        

        if 'analysis' in locals() and app==analysis: #analysis app (to be executed after all the others)
            if "PERSONAL_TOKEN" not in os.environ:
                print("WARNING: PERSONAL_TOKEN is not set. Submitting the report to gitlab will be impossible." )

            else:
                personal_token = "export SINGULARITYENV_PERSONAL_TOKEN="+os.environ['PERSONAL_TOKEN']

            fname = exp_name + ".job"
            f = open(directory + "/" + fname, "w")
            f.write(tpl
                    .replace("@array", "")
                    .replace("@mem", mem_analysis)
                    .replace("@singularity_env", copy_env())
                    .replace("@run_options", "") # no option for analysis?? GPU is probably not needed.
                    .replace("@gpu", "") # no option for analysis?? GPU is probably not needed.
                    .replace("@cuda_visible_devices_init", "")
                    .replace("@res_dir", os.path.abspath(directory))
                    .replace("@image_location", image_location)
                    .replace("@image_name", image_name)
                    .replace("@exp_name", exp_name)
                    .replace("@wall_time", wall_time_analysis)
                    .replace("@nb_cores", str(nb_cores_analysis))
                    .replace("@personal_token", personal_token)
                    .replace("@args", os.path.abspath(res_dir + "/"+image_name[:-4]+"/")+" ")  #Here we provide the root directory of the results, where all the other app have their folders. For now analysis does not take any additional args, can be changed later.
                    .replace("@app", "--bind "+ os.path.abspath(res_dir + "/"+image_name[:-4]+"/")+" " + str(run_app))
                    .replace("@kill_stop_child", "")
                    .replace("@kill_cont_child", "")
                    .replace("@synchronisation_parallel", "")
                    .replace("@synchronisation_kill", "")
                    .replace("@period_sync", "")
                    .replace("@rsync_option_exclude_TMP_SING_DIR", rsync_option_exclude_TMP_SING_DIR)
                    )
            f.close()
            os.chmod(directory + "/" + fname, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
            analysis_name += [(fname, directory)]
        else: # normal app
            for arg in args:

                fname = get_job_file_name(exp_name, arg, list(map(itemgetter(0), fnames)))
                f = open(directory + "/" + fname, "w")
                f.write(tpl
                        .replace("@array", array)
                        .replace("@mem", mem)
                        .replace("@singularity_env", copy_env())
                        .replace("@run_options", run_options)
                        .replace("@gpu", gpu) # no option for analysis?? GPU is probably not needed.
                        .replace("@cuda_visible_devices_init", cuda_visible_devices_init)
                        .replace("@res_dir", os.path.abspath(directory))
                        .replace("@image_location", image_location)
                        .replace("@image_name", image_name)
                        .replace("@exp_name", exp_name)
                        .replace("@wall_time", wall_time)
                        .replace("@nb_cores", str(nb_cores))
                        .replace("@personal_token", personal_token)
                        .replace("@args", str(arg))
                        .replace("@app", str(run_app))
                        .replace("@kill_stop_child", kill_stop_child)
                        .replace("@kill_cont_child", kill_cont_child)
                        .replace("@synchronisation_parallel", synchronisation_parallel)
                        .replace("@synchronisation_kill", synchronisation_kill)
                        .replace("@period_sync", period_sync_str)
                        .replace("@rsync_option_exclude_TMP_SING_DIR", rsync_option_exclude_TMP_SING_DIR)
                        )
                fnames += [(fname, directory)]
                f.close()
                os.chmod(directory + "/" + fname, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
        
    return (fnames, analysis_name)


def gen_job_scripts(conf_file):
    tplfile= open(os.path.dirname(os.path.abspath(__file__))+"/template.job","r")
    tpl = tplfile.read()
    fnames, analysis_name = _sub_script(tpl, conf_file)
    exec_content=[]
    exec_content.append('JOB_LIST="depend=afterany"')
    for (fname, directory) in fnames:
        s = 'cd '+ directory + '; if OUTPUT="$(/opt/pbs/bin/qsub  ' + fname + ')"; then echo $OUTPUT; JOB_LIST=$JOB_LIST:$OUTPUT; else echo "job submission failed"; exit 1; fi; cd - > /dev/null'
        exec_content.append(s)
        #print("to be executed:" + s)
    if len(analysis_name):
        s = 'cd '+ analysis_name[0][1] + '; /opt/pbs/bin/qsub  -W $JOB_LIST ' + analysis_name[0][0] + '; rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi; cd - > /dev/null'
        exec_content.append(s)
        #print("to be executed:" + s)
    exec_filename="./exec.sh"
    exec_file= open(exec_filename,"w")
    exec_file.write("\n".join(exec_content))
    exec_file.close()
    os.chmod(exec_filename, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)

def main(argv):
    if len(argv)==0:
        print("Please provide a json file")
        exit(3)
    else:
        print("Generating job scripts and result structure")
        gen_job_scripts(''.join(argv))



if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
