def create_hierarchic_dict(files, separator="/"):
    tree = {}
    for file in files:
        if file is None:
            continue
        # end if
        tree_pointer = tree
        parts = file.split(separator)
        for part in parts:
            if part not in tree_pointer:
                tree_pointer[part] = {}
            # end if
            tree_pointer = tree_pointer[part]
        # end for
    # end for
    return tree


# end def


def hierarchic_dict_simplify_paths(tree_pointer, separator="/"):
    for cur_key in list(tree_pointer.keys()):
        hierarchic_dict_simplify_paths(tree_pointer[cur_key], separator=separator)
        if len(tree_pointer[cur_key]) == 1:  # only one node, can be flattened.
            sub_key = list(tree_pointer[cur_key].keys())[0]
            new_key = cur_key + separator + sub_key
            tree_pointer[new_key] = tree_pointer.pop(cur_key)[sub_key]
        # end if
    # end for
# end def
