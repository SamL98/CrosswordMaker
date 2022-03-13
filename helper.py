from collections import defaultdict
from glob import glob

end = '_end_'

def construct_trie(words):
    root = dict()

    for word in words:
        node = root

        for c in word:
            node = node.setdefault(c, {})

        node[end] = end

    return root


#all_words = []
words = defaultdict(list)

for fname in glob('answers/*.txt'):
    with open(fname) as f:
        #all_words.extend(f.read().split(','))
        for word in f.read().split(','):
            words[len(word)].append(word)

#trie = construct_trie(all_words)


def get_matches(constraints, n, maxlen=20):
    '''
    node = trie
    i = 0

    while constraints[i][0] == i:
        node = node[constraints[i][1]]
        i += 1

    matches = []
    '''

    #matches = [word for word in all_words if len(word) == n]
    matches = words[n]

    for i, ch in constraints:
        matches = [word for word in matches if word[i] == ch]

    return matches[:min(len(matches), maxlen)]
