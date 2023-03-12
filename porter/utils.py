#!/usr/bin/env python
# -*- coding: utf-8 -*-


from itertools import zip_longest


def batch_read_file(n, f_obj):
    for n_lines in zip_longest(*[enumerate(f_obj)] * n, fillvalue=None):
        zips = filter(lambda x: x is not None, n_lines)
        _, items = zip(*zips)
        line_num = _[-1] + 1
        yield line_num, items
