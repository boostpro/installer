Library Installation
====================

Boost.IOStreams
---------------

zlib and libbz2 should be downloaded as source per 
http://www.boost.org/doc/libs/1_44_0/libs/iostreams/doc/installation.html#overview
and pointed at via the bjam variables BZIP2_SOURCE and ZLIB_SOURCE described in 
http://www.boost.org/doc/libs/1_44_0/libs/iostreams/doc/installation.html#bjam.

   bjam -s BZIP2_SOURCE=... -s ZLIB_SOURCE=...

Regex
-----

ICU support is tricky.  Among other things, regex only supports
runtime-link-dynamic when ICU is used.  Not sure how to handle that
best in the long run.

MPI
---

Boost.Build currently auto-detects the Microsoft Compute Cluster Pack,
but not Microsoft HPC Pack 2008 SDK, which is more modern.  It is
currently unknown whether we can force Boost.Build to use that
instead.  It also seems to be implied that the later SDK may not work
for Windows Server 2003 (and thus XP64, which is the same OS
underneath).

Tool Installation
=================

(from http://www.pion.org/files/pion-platform/common/doc/README.msvc)

To install Visual C++ 2005 Express Edition and the Microsoft Platform
SDK, follow the steps described at the following URL:

http://www.microsoft.com/express/2005/platformsdk/default.aspx

SDK at http://www.microsoft.com/downloads/details.aspx?displaylang=en&FamilyID=0baf2b35-c656-4969-ace8-e4c0c0716adb

In order for the Visual Studio Command Line Compiler to find the necessary
Microsoft Platform SDK files, one more file must be modified: open
"C:\Program Files\Microsoft Visual Studio 8\VC\vcvarsall.bat" in an editor
and add the following lines at the top, after "@echo off":

@set PATH=C:\Program Files\Microsoft Platform SDK for Windows Server 2003 R2\Bin;%PATH%
@set INCLUDE=C:\Program Files\Microsoft Platform SDK for Windows Server 2003 R2\Include;%INCLUDE%
@set LIB=C:\Program Files\Microsoft Platform SDK for Windows Server 2003 R2\Lib;%LIB%


64-Bit Tools
------------

Useful Links
............

* VS Express (General)
  * http://en.wikipedia.org/wiki/Microsoft_Visual_Studio_Express

* SDKs

  Each SDK comes with 64-bit tools built for compatibility with one
  version of Visual C++.
  
  * LATEST: http://msdn.microsoft.com/en-us/windows/bb980924.aspx
  * LEGACY: http://msdn.microsoft.com/en-us/windows/ff851942.aspx

* VS 2005 Express
  * Latest SDK: "Microsoft Windows SDK Update for Windows Vista and .NET Framework 3."
    http://www.microsoft.com/downloads/details.aspx?FamilyID=4377F86D-C913-4B5C-B87E-EF72E5B4E065

  * Official: http://msdn.microsoft.com/en-us/library/9yb4317s(v=VS.80).aspx
  * HOTFIX: http://support.microsoft.com/kb/949009/

* VS 2008 Express
  * Latest SDK: "Windows SDK for Windows 7 and .NET Framework 3.5 SP1" 
    http://www.microsoft.com/downloads/details.aspx?FamilyID=c17ba869-9671-4330-a63e-1fd44e0e2505
    
    This one gets installed under C:\Program Files\Microsoft SDKs\Windows\v7.0
    However, it doesn't come with mt.exe.  Therefore we fall back to “Windows® Software Development Kit Update for Windows Vista™”, which installs under C:\Program Files\Microsoft SDKs\Windows\v6.1
    
    That one, however, does not support IA64.

  * Official: http://msdn.microsoft.com/en-us/library/9yb4317s(v=VS.90).aspx
  * Detailed Instructions: http://jenshuebel.wordpress.com/2009/02/12/visual-c-2008-express-edition-and-64-bit-targets/
  * Quick Patch: http://www.cppblog.com/xcpp/archive/2009/09/09/vc2008express_64bit_win7sdk.html


* VS 2010 Express
  * Latest SDK: "Microsoft Windows SDK for Windows 7 and .NET Framework 4"
    http://www.microsoft.com/downloads/en/details.aspx?FamilyID=6b6c21d2-2006-4afa-9702-529fa782d63b

  * http://msdn.microsoft.com/en-us/library/9yb4317s.aspx
  * http://stackoverflow.com/questions/2629421/how-to-use-boost-in-visual-studio-2010

Note:

To build 64-bit binaries, you need to install the platform SDK, which
contains 64-bit tools.  The platform SDK also contains a script for setting up the tools, 
c:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\setenv.cmd

VS 2010 doesn't come with 

  c:/Program Files (x86)/Microsoft Visual Studio 10.0/VC/bin/x86_amd64/vcvarsx86_amd64.bat

so right now, I'm having some success by creating that file to contain

  call "c:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\setenv.cmd"

It's not clear yet whether that is getting the variant setup quite
right because that script also sets up Debug or Release mode.

Building The Installer
======================

Here is the script that I use to produce the installer.

It is invoked like this:

  > build-installer.py --build-libs --zip --build-installer \
    --build-tools <--dvd> [ABSOLUTE_PATH_TO_BOOST]

for instance, this produced the 1.39 installer:

  > build-installer.py --build-libs --zip --build-installer \
    --build-tools e:\boost\boost_1_39_0

New libraries need to be added to "lib-names.txt".  In a bash
shell at BOOST_ROOT,

  grep -hE '\<lib ' libs/*/build/Jamfile* | sed -e 's/^.*\<lib \([^ ]*\).*$/\1/' | sort

will get you a list.

You also need 7-zip installed. A standard install should just work.

After this is done you need to upload the binaries. I do this with
something like:

  @boostpro $ mkdir /home/daniel/1_39

  > cd 1_39-installer/zips
  > scp *.zip daniel@boostpro.com:1_39

and then move the binaries on the server:

 @boostpro $ mv /home/daniel/1_39 \
   /usr/local/www/data/boost-consulting/boost-binaries/

and set up the mirrors.txt file for the release:

 @boostpro $ echo "BoostPro Computing" >> \
   /usr/local/www/data/boost-consulting/boost-binaries/1_39/mirrors.txt

 @boostpro $ echo "http://www.boostpro.com/boost-binaries/1_39/" >> \
   /usr/local/www/data/boost-consulting/boost-binaries/1_39/mirrors.txt

You need the NSIS ZipDLL, NXS, and inetc plugins.  Drop the DLLs into
your NSIS Plugins folder.  Then Run NSIS on the generated .nsi file by 
right-clicking on it and selecting "compile NSIS file."

Now you should have a working installer. After this it's possible to
upload the binaries to sourceforge, and add mirrors to the mirrors.txt
file, but the procedure for that has changed. It's pretty simple though,
you can rsync (or something similar) the files from the server to SF.

  sudo mv 1_46_1 1.46.1
  rsync -avP 1.46.1 david_abrahams,boost@frs.sourceforge.net:/home/frs/project/b/bo/boost/boost-binaries/
  sudo mv 1.46.1 1_46_1 

There are a few manual steps as you can see, but they take me like 5
minutes to perform so I didn't bother scripting them.

Of course, you can just do the building if you want to and I can do the
manual steps when the build is done. For me, the build step takes more
than 24 hours, so it locks up my work station during that time. I also
sometimes have to do it incrementally because of lack disk space.

