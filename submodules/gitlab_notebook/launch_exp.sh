#!/bin/bash

python ./submodules/gitlab_notebook/gen_report.py --find_project  # Check that we can find the project and push issues
if [ $? != 0 ]; then
    exit $?
fi


# Build the final image
cd ./singularity
SINGULARITYENV_PERSONAL_TOKEN=$PERSONAL_TOKEN \
  SINGULARITYENV_CI_JOB_TOKEN=$CI_JOB_TOKEN \
  ./build_final_image.sh

# Run the experiment (will start a visu_server)
SINGULARITY_RUN_ARGS="$@" \
  /bin/bash ../submodules/gitlab_notebook/exp.sh

cd ../
pattern="./singularity/results/20*" && files=( $pattern ) && echo "using result folder ${files[-1]} " # finds the last folder (in alphabetic order)
python ./submodules/gitlab_notebook/gen_report.py ${files[-1]} # generate report and push in issue

