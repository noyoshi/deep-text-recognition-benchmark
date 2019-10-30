#!/usr/bin/env python3

import sys
import os
from Matcher import Matcher

# PIPE the results file into this one

# ANS_DIR = "/home/nyoshida/transcriptions/" # TODO put the file here with the true_word_list words etc in here
ANS_DIR = "/home/nyoshida/annotations/" # TODO put the file here with the true_word_list words etc in here

def get_filename(file_path):
    num_id = file_path.strip("/").split("/")[-1]
    return num_id.replace("res_", "").replace(".jpg", "") # in case they are named that...


def get_annotations(file_n):
    annotations = []
    filename = f"{ANS_DIR}{file_n}.txt"

    if not os.path.exists(filename):
        return ["<SKIP>"]

    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines: # the first line of the annotations file is
            # foreground, second line is background - right now we are ignoring
            # that...
            line = line.strip().split(" ")
            annotations += line

    return annotations


def skip_annotation(annotations):
    for row in annotations:
        if row == "<SKIP>" or row == "<REPEAT>":
            # print("skipping...")
            return True

    return False


def test():
    for line in sys.stdin:
        # comma seperated: file_path,words...
        file_path, *words = line.strip().split(",")
        n = get_filename(file_path)
        annotations = get_annotations(n)

        if skip_annotation(annotations):
            continue # Skip the files we don't care about

        matcher = Matcher(annotations, words)
        word_n  = len(annotations)
        if annotations:
            perfect_matches = matcher.get_perfect_matches()
            ign_symbols = matcher.get_perfect_matches_ignoring_symbols()
            perf = len(perfect_matches)/word_n * 100
            ign = len(ign_symbols)/word_n * 100
            unmatched = matcher.get_number_unmatched()
            # print(n, perf, ign, unmatched)


def main():
    # maybe make it read from multiple places?
    # samples = ["CRAFT", "EAST", "USC", "GCP_lang_hints", "AWS", "GCP"]
    samples = ["GCP", "GCP_crops", "CRAFT_attn"]
    # samples = ["AWS"]
    filenames = ["{}_indo.txt".format(name) for name in samples]

    guessed_words = []
    annotations   = {}
    data = { i: {} for i in range(len(filenames)) }
    name_dict = { i: name for i, name in enumerate(samples) }

    for i, filename in enumerate(filenames):
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                file_path, *words = line.strip().split(",")
                words = [x for x in words if len(x) != 0]
                # Get the correct words
                n = get_filename(file_path)
                if n not in annotations:
                    img_annotations = get_annotations(n)
                    annotations[n] = img_annotations

                # i represents which of the sources it came from - CRAFT, EAST,
                # USC
                guessed_words.append((i, n, words))
    
    possible_true_words_dict = None
    for i, n, words in guessed_words:
        # i represents the source
        # get the real annotations
        annotation = annotations[n]
        # Skip the annotation
        if skip_annotation(annotation):
            continue

        matcher = Matcher(annotation, words, 
                possible_true_words_dict = possible_true_words_dict)

        possible_true_words_dict = matcher.possible_true_words_dict

        word_n  = len(annotation)
        if word_n == 0:
            # TODO remove this, if we end up testing with no text files
            continue

        if annotations:
            perfect_matches = matcher.get_perfect_matches()
            ign_symbols = matcher.get_perfect_matches_ignoring_symbols()
            perf = len(perfect_matches)/word_n * 100
            ign = len(ign_symbols)/word_n * 100
            # vocab_matched = matcher.get_vocab_matches()
            # vcb = len(vocab_matched) / word_n * 100
            # mismatched = matcher.get_imperfect_matches(1)
            # msm = len(mismatched)/word_n * 100
            # percent_matched = perf + ign  + vcb# maybe lets ignore the mismatched
            percent_matched = perf + ign
            # ones?
            # percent_matched = perf 
            data[i][n] = percent_matched
            unmatched = matcher.get_number_unmatched()

            if unmatched > 4: # ignore all but craft
            # if i == 3: # ignore all but craft
                print(name_dict[i], n)
                print("ANNOTATED", *matcher.get_unmatched_annotated())
                print("DETECTED", *matcher.get_unmatched_detected())
                print(">", matcher.char_level_accuracy)
                print("=================================")
            # print(n, perf, ign, unmatched)

    for k in data:
        avg = sum(data[k].values()) / (len(list(data[k].values())))
        print(name_dict[k], '\t', round(avg, 2))


if __name__ == "__main__":
    # test()
    main()

