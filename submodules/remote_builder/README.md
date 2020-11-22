# remote_builder

git submodule to enable the remote build of singularity images, and their storage on the Lab's SRegistry.

## Automatic Triggers with GitLab CI

To enable this features: 
1) Run the following commands:
```
mkdir -p submodules
git submodule add ../../../AIRL_tools/remote_builder ./submodules/remote_builder
```
The url is relative to the url of your project, so here we assumed that you project is for instance located in `/Students_projects/My_Self/My_Project`
You will now have a folder named `submodules/remote_builder` containing all the necessary scripts.

2) If you want to use the CI pipeline to manage the publication in the note book, add in your project a file named `.gitlab-ci.yml` containing:
```
include:
  - project: 'AIRL/AIRL_tools/remote_builder'
    ref: master
    file: 'gitlab-ci-template.yml'
```
3) Make sure you have a compatible Runner associated with your project. If your project is in the AIRL group, you can use the group runner. You might want to disable the shared runners that might not be compatible with singularity (TBC).
3) In the setting of your gitlab project, in section `repository`, set the master branch as protected.
4) In the project setting (CI/CD, variable) add the two following variables: 
- `SREGISTRY_TOKEN`: This token should be obtained from the AIRL_Registry (http://10.0.5.254 or http://10.0.5.254). It is suggested to protect and mask this variable.
- `REGISTRY_PATH`: This is the path of the container collection you should create on the AIRL_Registry and want to use. Example of proper path: `antoine/my-collection`  

Now, every `push` will activate a `pipeline` in gitlab which offers you the possibility to launch your build of the image.



------
NOTE: 
your singularity.def file should use the following procedure to clone the repository: 
```
 if [ -z "${CI_JOB_TOKEN}" ]; then  # this enables the automated build in the CI environment
      git clone  --recurse-submodules  https://gitlab.doc.ic.ac.uk/AIRL/research_projects/antoine_cully/template_experiment.git ./template_experiment
   else
      git clone --recurse-submodules  http://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.doc.ic.ac.uk/AIRL/research_projects/antoine_cully/template_experiment.git ./template_experiment
   fi
```
in which you should replace `research_projects/antoine_cully/template_experiment` by the relevant information for your project. 