#!/bin/bash

pattern="final_*.sif"
files=( $pattern )


if [ ${#files[@]} != 1 ]; then
   echo "WARNING multiple final_*.sif files found! First one will be executed: ${files[-1]} "
fi
echo "container file: ${files[-1]}"   

singularity exec ${files[-1]} visu_server.sh&
ret_code=$?
if [ $ret_code != 0 ]; then
    exit ret_code
fi
sleep 4

export DISPLAY=":1"
echo "Arguments for running singularity image: $SINGULARITY_RUN_ARGS"
SINGULARITYENV_DISPLAY=$DISPLAY singularity run $SINGULARITY_RUN_ARGS ./${files[-1]}
ret_code=$?
if [ $ret_code != 0 ]; then
    exit ret_code
fi

