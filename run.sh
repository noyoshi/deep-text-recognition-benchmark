#!/bin/sh

# Run this with the image folder as a command line variable to get the data
# Change the saved_model to whatever you need - more models can be found in the
# github repo

# The image folder should contain all the images you want to run throught this.
# The files should be all cropped and processed at this stage.

# NOTE - you can add a CLI arg to this to change the characters you can use?
# might be able to add @ or # etc if we need to? Probably depends on the model

# NOTE - NEED TO GIVE THE FULL FILEPATH
# E.G
# $ bash run.sh /home/nyoshida/textDetectionWithScriptID/cropped_images

for dir in $1/*/
do
  # this prints comma seperated words from the image
  # the first item it prints is the image filepath BTW
  python3 demo.py \
  --Transformation TPS --FeatureExtraction ResNet --SequenceModeling BiLSTM --Prediction Attn \
  --image_folder $dir \
  --sensitive \
  --saved_model TPS-ResNet-BiLSTM-Attn-case-sensitive.pth 
done
