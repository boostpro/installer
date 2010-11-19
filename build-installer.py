#!/usr/bin/python

import sys
import re
import os.path
import subprocess
import itertools
import glob
import shutil
import nsi

usage = '%s [OPTIONS] BOOST-DIRECTORY'

def make_directories(dirs):
    for d in dirs:
        try:
            os.makedirs(d)
        except:
            pass

def determine_boost_version(root):
    for i in open(os.path.join(root, 'boost/version.hpp')):
        if i.startswith('#define BOOST_LIB_VERSION'):
            return i.rsplit(' ', 1)[1].strip()[1:-1]
    raise Exception('Failed to determine boost version')

def execute_with_progress(working_directory, args, progress_re='', log=None):
    if log is not None:
        log.write("\n*** executing '%s'\n\n" % str(args))

    process = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=working_directory) # close_fds=True
    output = ''
    while 1:
        line = process.stdout.readline()
        if line == '':
            break
        if log is not None:
            log.write(line)
        output += line
        if re.match(progress_re, line):
            sys.stdout.write('.')
    status = process.wait()
    print 'done'

    return status, output

def build_bjam(root, log):
    print 'Building bjam executable..',

    src = os.path.join(root, 'tools/jam/src')
    build_script = src + '/build.bat'
    status, output = execute_with_progress(src, build_script, '', log)
    if status:
        raise RuntimeError, "FAILED: %(args)s\nwith status %(status)s" % locals()

    if status != 0:
        raise Exception('Failed to build bjam')

    m = re.search('\\[COMPILE\\] (.*)', output)
    bjam = m and m.group(1)
    if bjam is None:
        raise Exception('Failed to determine bjam executable path')

    return os.path.join(src, bjam).strip()

def build_libraries(root, bjam, toolsets, log):
    for toolset in toolsets:
        print 'Building with %s..' % toolset,

        cmd = bjam + [
            '--build-type=complete',
            'toolset=%s' % toolset,
            'stage'
        ]

        status, output = execute_with_progress(
            root, cmd, '^\\.\\.\\.on \\d+th target\\.\\.\\.', log)

def build_tools(root, bjam, log):
    cmd = bjam
    tools = os.path.join(root, 'tools')

    print 'Building tools..',

    status, output = execute_with_progress(
        tools, cmd, r'compile-c-c\+\+', log)

    shutil.rmtree(os.path.join(root,'bin'), ignore_errors=True)
    os.rename(os.path.join(root, 'dist/bin'), os.path.join(root, 'bin'))
    shutil.copyfile(bjam[0], os.path.join(root, 'bin/bjam.exe'))

variant_re = re.compile(r'(?:lib)?(boost_\w+)-(\w+)(-mt)?(-[a-z]+)?-(?:[0-9_]+)\.lib')

class Variant:
    def __init__(self, filename, name, compiler, threading, flags):
        self.filename = filename
        self.name = name
        self.compiler = compiler
        self.threading = threading
        self.flags = flags or ''

    def __repr__(self):
        result = '(compiler=%s' % self.compiler
        result += ', threading='
        if self.threading:
            result += 'multi'
        else:
            result += 'single'
        result += ', flags=%s' % self.flags
        result += ')'
        return result

def decompose_variant(lib):
    m = variant_re.match(lib)
    if not m:
        return None

    name = m.group(1)

    compiler = m.group(2)
    threading = m.group(3) is not None

    return Variant(lib, name, compiler, threading, m.group(4))

def variant_name(v):
    result = ''
    if v.threading:
        result = 'Multithreaded'
    else:
        result = 'Single threaded'

    if 'g' in v.flags:
        result += ' debug'
    if 's' in v.flags:
        result += ', static runtime'

    if not v.filename.startswith('lib'):
        result += ' DLL'

    return result

def generate_installer(installer_dir, libdir, lib_to_name, compiler_names, version, dvd):
    libs = [ decompose_variant(lib) for lib in os.listdir(libdir) ]
    libs = filter(lambda x: x is not None, libs)
    libs.sort(key=lambda x: (lib_to_name[x.name], x.compiler))

    sections = ''

    for lib, variants in itertools.groupby(libs, lambda x: x.name):
        sections += 'SectionGroup "%s"\n' % lib_to_name[lib]

        for compiler, v2 in itertools.groupby(variants, lambda x: x.compiler):
            sections += '  SectionGroup "%s"\n' % compiler_names[compiler]
            for v in v2:
                size = 0
                base = os.path.splitext(v.filename)[0]
                for f in glob.glob(os.path.join(libdir, base) + '.*'):
                    size += os.path.getsize(f)

                sections += '    Section /o "%s"\n' % variant_name(v)
                sections += '      AddSize %d\n' % (size / 1024,)
                sections += '      Push "%s"\n' % base
                sections += '      Call DownloadFile\n'
                sections += '    SectionEnd\n'
            sections += '  SectionGroupEnd\n'

        sections += 'SectionGroupEnd\n'

    human_version = version.replace('_', '.')

    installer = nsi.generate(
        dvd=dvd, version=version, human_version=human_version, sections=sections)

    open('boost_%s_setup.nsi' % version, 'w').write(installer)

def read_key_value_pairs(filename):
    result = {}
    for line in open(filename):
        if line[0] == '#':
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()

        if not key or not value:
            raise Exception('Bad key value pair')

        result[key] = value

    return result

zip_program=r'C:\Program Files\7-Zip\7z.exe'

def build_zip_files(boostdir, version, libdir, zipdir, log):
    files = filter(lambda x: x.endswith('.lib'), os.listdir(libdir))

    for f in files:
        base = os.path.splitext(f)[0]
        if not base.endswith(version):
            continue
        args = [ zip_program, 'u', '-tzip', '%s/%s.zip' % (zipdir, base), f ]
        if not f.startswith('libboost'):
            args.append(base + '.dll')
        print 'Zipping %s..' % base,
        execute_with_progress(libdir, args, log=log)

    args = [ zip_program, 'u', '-tzip', '%s/boost_%s_headers.zip' % (zipdir, version), 'boost' ]
    print 'Zipping headers..',
    execute_with_progress(boostdir, args, log=log)

    args = [ zip_program, 'u', '-tzip', '%s/boost_%s_tools.zip' % (zipdir, version), 'bin', 'tools' ]
    print 'Zipping tools..',
    execute_with_progress(boostdir, args, log=log)

    args = [
        zip_program, 'u', '-tzip', '%s/boost_%s_doc_src.zip' % (zipdir, version),
        'libs',
        'doc',
        'more',
        'people',
        'wiki',
        'boost.css',
        'boost.png',
        'boost-build.jam',
        'configure',
        'index.htm',
        'index.html',
        'INSTALL',
        'Jamroot',
        'LICENSE_1_0.txt',
        'rst.css'
    ]

    print 'Zipping doc and src..',
    execute_with_progress(boostdir, args, log=log)

def main(argv):
    if len(argv) < 2:
        print usage % argv[0]
        return 1

    build_libs = False
    build_zips = False
    build_installer = False
    do_build_tools = False

    dvd = False

    for arg in argv:
        if arg == '--build-libs':
            build_libs = True
        elif arg == '--zip':
            build_zips = True
        elif arg == '--build-installer':
            build_installer = True
        elif arg == '--build-tools':
            do_build_tools = True
        elif arg == '--dvd':
            dvd = True

    cwd = os.getcwd()
    root = argv[-1]
    version = determine_boost_version(root)
    installer_dir = os.path.abspath('%s-installer' % version)
    build_dir = os.path.join(installer_dir, 'build')
    stage_dir = os.path.join(installer_dir, 'stage')
    zip_dir = os.path.join(installer_dir, 'zips')

    make_directories([installer_dir, build_dir, stage_dir, zip_dir])

    log = open('build.log', 'w', 0)

    toolsets = open('toolsets.txt').read().split('\n')
    compiler_names = read_key_value_pairs('compiler-names.txt')

    bjam_options = [
        '--user-config=%s' % os.path.join(cwd, 'user-config.jam'),
        '--build-dir=%s' % build_dir,
        '--stagedir=%s' % stage_dir,
        '--debug-configuration',
        '--j2',
    ]

    if build_libs or do_build_tools:
        bjam = os.path.abspath(build_bjam(root, log))

    if build_libs:
        build_libraries(root, [bjam] + bjam_options, toolsets, log)

    if do_build_tools:
        build_tools(root, [bjam] + bjam_options, log)

    if build_zips:
        build_zip_files(root, version, os.path.join(stage_dir, 'lib'), zip_dir, log)

    if build_installer:
        lib_to_name = read_key_value_pairs('lib-names.txt')
        generate_installer(installer_dir,
                           os.path.join(stage_dir, 'lib'),
                           lib_to_name,
                           compiler_names,
                           version,
                           dvd)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

