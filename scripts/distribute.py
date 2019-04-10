import binpacking
import os
import argparse


def collect_files(basedir_path):
    """
    Takes in a base directory. 

    Returns list of fully qualified, relative file names within the 
    directory (recursively).

    Note that if empty directories exist within the directory, 
    for instance, a/b/c/d/ where d is a directory –– then this
    path will not appear in the returned list. Only files are returned.
    """
    files = []
    for (dirpath, dirnames, filenames) in os.walk(basedir_path):
        full_filenames = [os.path.join(dirpath, x) for x in filenames]
        files.extend(full_filenames)
    return files

def get_sizes(filenames_list):
    """
    Takes in a list of fully-qualified, relative file names.

    Returns a dictionary mapping items from the list to their
    file sizes in bytes.

    Note that every item in the list MUST be an existing file.
    """
    return {k: os.path.getsize(k) for k in filenames_list}

def find_empty_dirs(base_dir):
    """
    Takes in a base directory and returns (recursively) all 
    empty directories within (as a dictionary mapped from
    key: dirpath to value: 0 bytes in size.)
    """

    empty_dirs = {}
    for dirpath, dirs, files in os.walk(base_dir):
        if not dirs and not files:
            empty_dirs[dirpath] = 0
    return empty_dirs


def do_binpack_constbin(bp_dict, num_bins=10):
    """
    Takes in a dictionary mapping filenames to filesizes (in bytes).
    Takes in number of bins wanted (while minimizing size).

    Determines a packing of filenames to num_bins bins, and
    returns list of num_bins dictionaries. The pairwise 
    intersection of the list returned is empty, and the union
    is the entirety of bp_dict.
    """
    bins = binpacking.to_constant_bin_number(bp_dict, num_bins)
    return bins

def do_binpack_constvol(bp_dict, max_vol=100*1024):
    """
    Takes in a dictionary mapping filenames to filesizes (in bytes).
    Takes in maximum filesize of each bin. Default: 100 MB.

    Determines a packing of filenames into X bins, where X is 
    minimized, and each of the X bins is constrained to be 
    less than max_vol in size.

    Returns a list of dictionaries of size X. The pairwise
    intersection of the list returned is empty, and the union
    is the entirety of bp_dict.

    Note: requires max_vol >= the size of the largest file
    in the list (because otherwise there is no way to partition.)
    """
    assert max_vol >= max(bp_dict.values()), """Maximum volume for 
            binpacking must be larger than the largest 
            file {}""".format(max(bp_dict.values()))

    bins = binpacking.to_constant_volume(bp_dict, max_vol)
    return bins

def do_binpack_distribution(bp_dict, distribution):
    """
    Takes in a dictionary mapping filenames to filesizes (in bytes).
    Takes in a target distribution list of integers (for simplicity). 
    For instance: [1, 2, 5, 6, 10, 4, 5] means that a total of 7 bins
    are wanted with a rough distribution with the first bin having 
    1/(1+2+5+6+10+4+5) fraction of the bytes, the second bin having
    2/(2+5+6+10+4+5) fraction of the bytes, and so on.

    Returns a list of dictionaries of size len(distribution). See
    comments in do_binpack_[..] functions for format of this dictionary.

    This function achieves this distribution by instead asking for
    sum(distribution) number of bins of roughly even sizes from
    do_binpack_constbin. 

    Then, it combines bins as returned from do_binpack_constbin to 
    match the requested distribution.
    """
    assert all([type(x) is int for x in distribution])

    bins = do_binpack_constbin(bp_dict, sum(distribution))
    combined_bins = []

    counter = 0
    for i in distribution:
        """Example run from docstring:

        First combine bins[0:1] into 1 dict.
        Then combine bins[1:3] into 1 dict.
        Then combine bins[3:8] into 1 dict.
        and so on.
        """
        combined_bins.append(merge_dicts(bins[counter : counter + i]))
        counter = counter + i
        
    return combined_bins

def merge_dicts(list_of_dicts):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.

    Source: https://stackoverflow.com/questions/38987/how-to-merge-two-dictionaries-in-a-single-expression
    """
    result = {}
    for dictionary in list_of_dicts:
        result.update(dictionary)
    return result

def bin_sizes(bins):
    """Utility function for viewing/debugging.

    Takes in list of dictionaries as outputted by
    do_binpack_X functions. 

    Outputs a list of size len(bins), with the size
    of each bin in bytes.
    """
    return [sum(x.values()) for x in bins]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dirpath", help="path to directory")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--constbin", action='store', type=int, help="Supply this argument to require that the directory be distributed to a constant number of bins. Must be an integer.")
    group.add_argument("--constvol", action='store', type=int, help="Supply this argument to require that the directory be distributed to the smallest number of bins possible, while requiring the constraint that the volume of each bin be upper bounded by the argument. Must be an integer.")
    group.add_argument("--distribution", nargs='+', type=int, help="Supply a list of integers of target distribution. For example: [1, 2, 3] will output 3 bins, with ~1/6 of the data in the first bin, 2/6 in the second and 3/6 in the third. Must be a list of integers.")

    args = parser.parse_args()
    print(args)
    dirpath = args.dirpath

    filenames = collect_files(dirpath)
    filesizes_map = get_sizes(filenames)

    empty_dirs = find_empty_dirs(dirpath)

    bins = None

    if args.constbin:
        bins = do_binpack_constbin(filesizes_map, args.constbin)
    elif args.constvol:
        bins = do_binpack_constvol(filesizes_map, args.constvol)
    else: # args.distribution
        bins = do_binpack_distribution(filesizes_map, args.distribution)

    # Add the empty directories, which are missing from filesizes_map because
    # they have no files to the first bin (arbitrary choice...)
    bins[0] = merge_dicts([bins[0], empty_dirs])

    print(["{:,}".format(x) for x in bin_sizes(bins)])

    

# Binpacking example code.
'''
b = {'a': 10, 'b': 10, 'c': 11, 'd': 1, 'e': 2, 'f': 7}
bins = binpacking.to_constant_bin_number(b, 4)
print(b, "\n", bins)

b = list(b.values())
bins = binpacking.to_constant_volume(b, 11)
print(b, "\n", bins)
'''
    
