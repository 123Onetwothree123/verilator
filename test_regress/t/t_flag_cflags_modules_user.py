#!/usr/bin/env python3
# DESCRIPTION: Verilator: Verilog Test driver/expect definition
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of either the GNU Lesser General Public License Version 3
# or the Perl Artistic License Version 2.0.
# SPDX-FileCopyrightText: 2026 Wilson Snyder
# SPDX-License-Identifier: LGPL-3.0-only OR Artistic-2.0
import os
import re
import shutil
import vltest_bootstrap

test.scenarios('simulator')
test.clean_objs()
cxx = os.environ.get('CXX', 'c++')
gcc_match = re.search(r'\(GCC\) (\d+)', test.cxx_version)
is_clang = re.search(r'clang', test.cxx_version)
flags = [
    '--exe',
    test.t_dir + '/t_flag_cflags_modules_user_main.cpp',
    '-CFLAGS',
    '-std=c++23',
]
if gcc_match:
    with open(test.obj_dir + '/empty.cpp', 'w', encoding='utf8'):
        pass
    test.run_capture('cd ' + test.obj_dir + ' && ' + cxx + ' -std=c++23 -fmodules -MM'
                     ' -fdeps-format=p1689r5 -fdeps-file=empty.deps.json'
                     ' -fdeps-target=empty.o -fsyntax-only empty.cpp',
                     check=False)
    if not os.path.exists(test.obj_dir + '/empty.deps.json'):
        test.skip('Requires a compiler with P1689 C++ module dependency scanning')
    flags += ['-CFLAGS', '-fmodules']
elif is_clang:
    scan_deps = shutil.which('clang-scan-deps')
    if scan_deps is None:
        match = re.search(r'clang version (\d+)', test.cxx_version)
        if match:
            scan_deps = shutil.which('clang-scan-deps-' + match.group(1))
    if scan_deps is None:
        test.skip('Requires clang-scan-deps for C++ module dependency scanning')
    probe_dir = test.obj_dir + '/probe'
    os.makedirs(probe_dir, exist_ok=True)
    with open(probe_dir + '/empty.cppm', 'w', encoding='utf8') as fh:
        fh.write('export module probe;\n')
    test.run_capture('cd ' + probe_dir + ' && ' + cxx + ' -std=c++23 --precompile'
                     ' empty.cppm -o empty.pcm', check=False)
    if not os.path.exists(probe_dir + '/empty.pcm'):
        test.skip('Requires Clang with --precompile')
else:
    test.skip('Requires GCC or Clang')
flags += [test.t_dir + '/t_flag_cflags_modules_user.cppm']
test.compile(make_main=False,
             verilator_flags2=flags,
             make_flags=['VM_PARALLEL_BUILDS=1'])
if gcc_match:
    test.glob_some(test.obj_dir + '/gcm.cache/*.gcm')
else:
    test.glob_some(test.obj_dir + '/*.pcm')
test.execute()
test.passes()
