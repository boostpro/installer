def generate(version_string, architecture):
    subdir = version_string + '-x64' if architecture == '64' else version_string

    return '''Nearest SourceForge Mirror (recommended)
http://downloads.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
BoostPro Computing
http://www.boostpro.com/boost-binaries/%(subdir)s/
SourceForge voxel
http://voxel.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
SourceForge internap
http://internap.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
SourceForge superb-east
http://superb-east.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
SourceForge superb-west
http://superb-west.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
SourceForge easynews
http://easynews.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
SourceForge dfn
http://dfn.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
SourceForge switch
http://switch.dl.sourceforge.net/project/boost/boost-binaries/%(subdir)s/
''' % locals()
