"""This should aim to get the predicted words, and try to match them with
Bahasa? Such that we make sure that the words we got are more or less legit"""

class Matcher(object):
    def __init__(self,
            parsed_word_list,
            vocab_file="bahasa.txt",
        ):
        # Need to make these copies, as we are mutating them
        self.parsed_word_list = list(parsed_word_list)
        self.vocab = set()


        with open(vocab_file, "r") as f:
            for line in f.readlines():
                word = line.strip().lower()
                self.vocab.add(word)

    def match(self, matcher):
        """The matcher should be the function we call to declare two strings
        match"""
        matches = []
        for i, parsed_word in enumerate(self.parsed_word_list):
            if parsed_word is None: continue
            parsed_word = self.normalize(parsed_word)

            for j, true_word in enumerate(self.true_word_list):
                # We convert words we already recognized into None so they are
                # no longer considered for future iterations
                if true_word is None: continue

                # Normalize the word
                true_word = self.normalize(true_word)

                if matcher(parsed_word, true_word):
                    matches.append(parsed_word)
                    self.true_word_list[j]   = None
                    self.parsed_word_list[i] = None
                    # print("---------------------------")
                    # print("Parsed word:\t", parsed_word,"\nReal Word:\t",  true_word)
                    break

        return matches

    def get_perfect_matches(self):
        def perfect_matcher(parsed_word, true_word):
            return parsed_word == true_word

        return self.match(perfect_matcher)

    def get_perfect_matches_ignoring_symbols(self):
        """Our OCR tools do not recongnize special characters - these should be
        ignored

        The problem is that symbols can either be replaced with predicted
        letters, or they might not be parsed at all?

        I think we should just straight up ignore the ones that don't match in
        legth :P

        say that "hello!" == "hello"

        Period ans some other stuff get split up a lot :(
        """
        def all_deleted_matcher(parsed_word, true_word):
            new_true_word = ""
            indicies_to_ignore = set()
            parsed_word_index = 0
            num_allowed_mismatches = 0

            # This is assuming ALL of the special chars were ignored!
            # This really just helps for trailing punctuation, or stuff like
            # phone numbers or dates which had their punctuation ignored. Also
            # helps for urls.

            num_unmatched = len([x for x in true_word if is_symbol(x)])
            if len(parsed_word) + num_unmatched != len(true_word):
                return False

            for i, char in enumerate(true_word):
                # Ignore the non alphanumeric characters
                if not char.isalpha() and not char.isdigit():
                    continue

                # if the characters do not match / the string lengths don't
                # match
                if parsed_word_index >= len(parsed_word) or char != parsed_word[parsed_word_index]:
                    return False

                parsed_word_index += 1

            return True

        def all_replaced_matcher(parsed_word, true_word):
            """assume we parse a symbol as a random character"""
            if len(parsed_word) != len(true_word):
                return False

            for i, char in enumerate(true_word):
                if is_symbol(char):
                    continue

                if char != parsed_word[i]:
                    return False

            """we should also try to figure out if the parsed word is in the vocab -
            otherwise, we should reject it (how would we know what its supposed
            to be. We should try to match the parsed_word with something in the
            grammar, assuming we can ignore some symbols?"""

            return True


        all_deleted_matched = self.match(all_deleted_matcher)
        all_replaced_matched = self.match(all_replaced_matcher)
        return all_deleted_matched + all_replaced_matched


    def get_substring_matches(self):
        """What if we split it wrong? we need to try to match on substrings
        instead.
        Aim for finding the true_word inside the parsed_word
        """
        pass

    def get_unmatched_annotated(self):
        """return the non matched annotated words"""
        return list(filter(lambda x: x is not None, self.true_word_list))

    def get_unmatched_detected(self):
        return list(filter(lambda x: x is not None, self.parsed_word_list))

    def get_imperfect_matches(self, n=1):
        """n is the number of characters that can differ between the two
        strings"""

        # TODO below
        # I would try to also find the most likely match, ie, if this has n=2
        # mismatches, but there is something else that has n=1 mismatches, we
        # should do that. Would require rewriting this to not use self.match

        def matcher(parsed_word, true_word):
            mismatched = 0
            if len(parsed_word) != len(true_word): return False

            for i, char in enumerate(true_word):
                # ignore symbols again
                if not char.isalpha() and not char.isdigit():
                    continue

                if char != parsed_word[i] or i >= len(parsed_word):
                    mismatched += 1

                if mismatched > n:
                    return False, None

            return True, mismatched


        mismatched = {} # save the mismatched info

        # pretty sure this is dumb
        for i, parsed_word in enumerate(self.parsed_word_list):
            if parsed_word is None: continue

            for j, true_word in enumerate(self.true_word_list):
                if true_word is None: continue

                true_word = self.normalize(true_word)

                matched, mismatched = matcher(parsed_word, true_word)
                if matched:
                    if true_word in mismatched and mismatched[true_word][0] > mismatched:
                        # we should replace the mismatched one!
                        data = (mismatched, parsed_word, i)
                        _, old_parsed_word, old_i = mismatched[true_word]
                        # Put this back in the list
                        self.parsed_word_list[old_i] = old_parsed_word
                        mismatched[true_word] = data

                        self.true_word_list[j]   = None
                        self.parsed_word_list[i] = None
                        print("---------------------------")
                        print("Parsed word:\t", parsed_word,"\nReal Word:\t",  true_word)
                        break

                    if parsed_word not in mismatched:
                        data = (mismatched, parsed_word, i)
                        mismatched[true_word] = data


        return self.match(matcher)

    def get_vocab_matches(self, n=1):
        """search for the word in the vocab, if its different by n chars, thats
        ok! but find the least different one

        we want to do this for both the parsed and the annotated word, then run
        a perfect match on them?
        """
        num_different = float('inf')

        def matcher(parsed_word, true_word):
            """Need to get the correct parsed and true_word"""
            possible_parsed_words = self.find_matches(parsed_word)

            # Memoized dict for the possible words from a given true word
            if true_word not in self.possible_true_words_dict:
                possible_true_words = self.find_matches(true_word)
                self.possible_true_words_dict[true_word] = possible_true_words
            else:
                possible_true_words   = self.possible_true_words_dict[true_word]

            possible_matches = (possible_parsed_words & possible_true_words)

            # There are some possible spell corrections that involve us having
            # the same word
            if len(possible_matches) != 0:
                # print(possible_matches, parsed_word, true_word)
                return True

            return False

        return self.match(matcher)

    def find_matches(self, word, n=1):
        """search in the vocab for words with n=1 differences to the input
        word

        Right now, just doing for n=1
        """

        import string
        possible_new_chars = string.ascii_lowercase
        possible_new_chars += '0123456789'

        possible_words = set()

        # add the first word
        possible_words.add(word)

        # n = 1
        for i, char in enumerate(word):
            for new_char in possible_new_chars:
                s = word[:i] + new_char + word[i + 1:]

                # Make sure the new word is a valid bahasa word
                if s in self.vocab:
                    possible_words.add(s)

            # pretent it doens't exist
            s = word[:i] + "" +  word[i + 1:]

            # Make sure the new word is valid bahasa
            if s in self.vocab:
                possible_words.add(s)

        return possible_words

    def get_number_unmatched(self):
        unmatched = [x for x in self.true_word_list if x is not None]
        return len(unmatched)
