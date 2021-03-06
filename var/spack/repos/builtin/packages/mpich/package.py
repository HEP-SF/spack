# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *
import os
import sys


class Mpich(AutotoolsPackage):
    """MPICH is a high performance and widely portable implementation of
    the Message Passing Interface (MPI) standard."""

    homepage = "http://www.mpich.org"
    url      = "http://www.mpich.org/static/downloads/3.0.4/mpich-3.0.4.tar.gz"
    git      = "https://github.com/pmodels/mpich.git"
    list_url = "http://www.mpich.org/static/downloads/"
    list_depth = 1

    version('develop', submodules=True)
    version('3.3.2', sha256='4bfaf8837a54771d3e4922c84071ef80ffebddbb6971a006038d91ee7ef959b9')
    version('3.3.1', sha256='fe551ef29c8eea8978f679484441ed8bb1d943f6ad25b63c235d4b9243d551e5')
    version('3.3',   sha256='329ee02fe6c3d101b6b30a7b6fb97ddf6e82b28844306771fa9dd8845108fa0b')
    version('3.2.1', sha256='5db53bf2edfaa2238eb6a0a5bc3d2c2ccbfbb1badd79b664a1a919d2ce2330f1')
    version('3.2',   sha256='0778679a6b693d7b7caff37ff9d2856dc2bfc51318bf8373859bfa74253da3dc')
    version('3.1.4', sha256='f68b5330e94306c00ca5a1c0e8e275c7f53517d01d6c524d51ce9359d240466b')
    version('3.1.3', sha256='afb690aa828467721e9d9ab233fe00c68cae2b7b930d744cb5f7f3eb08c8602c')
    version('3.1.2', sha256='37c3ba2d3cd3f4ea239497d9d34bd57a663a34e2ea25099c2cbef118c9156587')
    version('3.1.1', sha256='455ccfaf4ec724d2cf5d8bff1f3d26a958ad196121e7ea26504fd3018757652d')
    version('3.1',   sha256='fcf96dbddb504a64d33833dc455be3dda1e71c7b3df411dfcf9df066d7c32c39')
    version('3.0.4', sha256='cf638c85660300af48b6f776e5ecd35b5378d5905ec5d34c3da7a27da0acf0b3')

    variant('hydra', default=True,  description='Build the hydra process manager')
    variant('romio', default=True,  description='Enable ROMIO MPI I/O implementation')
    variant('verbs', default=False, description='Build support for OpenFabrics verbs.')
    variant('slurm', default=False, description='Enable SLURM support')
    variant('wrapperrpath', default=True, description='Enable wrapper rpath')
    variant(
        'pmi',
        default='pmi',
        description='''PMI interface.''',
        values=('off', 'pmi', 'pmi2', 'pmix'),
        multi=False
    )
    variant(
        'device',
        default='ch3',
        description='''Abstract Device Interface (ADI)
implementation. The ch4 device is currently in experimental state''',
        values=('ch3', 'ch4'),
        multi=False
    )
    variant(
        'netmod',
        default='tcp',
        description='''Network module. Only single netmod builds are
supported. For ch3 device configurations, this presumes the
ch3:nemesis communication channel. ch3:sock is not supported by this
spack package at this time.''',
        values=('tcp', 'mxm', 'ofi', 'ucx'),
        multi=False
    )
    variant('pci', default=(sys.platform != 'darwin'),
            description="Support analyzing devices on PCI bus")

    provides('mpi')
    provides('mpi@:3.0', when='@3:')
    provides('mpi@:1.3', when='@1:')

    filter_compiler_wrappers(
        'mpicc', 'mpicxx', 'mpif77', 'mpif90', 'mpifort', relative_root='bin'
    )

    # fix MPI_Barrier segmentation fault
    # see https://lists.mpich.org/pipermail/discuss/2016-May/004764.html
    # and https://lists.mpich.org/pipermail/discuss/2016-June/004768.html
    patch('mpich32_clang.patch', when='@3.2:3.2.0%clang')

    # Fix SLURM node list parsing
    # See https://github.com/pmodels/mpich/issues/3572
    # and https://github.com/pmodels/mpich/pull/3578
    # Even though there is no version 3.3.0, we need to specify 3.3:3.3.0 in
    # the when clause, otherwise the patch will be applied to 3.3.1, too.
    patch('https://github.com/pmodels/mpich/commit/b324d2de860a7a2848dc38aefb8c7627a72d2003.patch',
          sha256='c7d4ecf865dccff5b764d9c66b6a470d11b0b1a5b4f7ad1ffa61079ad6b5dede',
          when='@3.3:3.3.0')

    depends_on('findutils', type='build')
    depends_on('pkgconfig', type='build')

    depends_on('libfabric', when='netmod=ofi')
    # The ch3 ofi netmod results in crashes with libfabric 1.7
    # See https://github.com/pmodels/mpich/issues/3665
    depends_on('libfabric@:1.6', when='device=ch3 netmod=ofi')

    depends_on('ucx', when='netmod=ucx')

    depends_on('libpciaccess', when="+pci")
    depends_on('libxml2')

    # Starting with version 3.3, Hydra can use libslurm for nodelist parsing
    depends_on('slurm', when='+slurm')

    depends_on('pmix', when='pmi=pmix')

    conflicts('device=ch4', when='@:3.2')
    conflicts('netmod=ofi', when='@:3.1.4')
    conflicts('netmod=ucx', when='device=ch3')
    conflicts('netmod=mxm', when='device=ch4')
    conflicts('netmod=mxm', when='@:3.1.3')
    conflicts('netmod=tcp', when='device=ch4')
    conflicts('pmi=pmi2', when='device=ch3 netmod=ofi')
    conflicts('pmi=pmix', when='device=ch3')

    def setup_build_environment(self, env):
        env.unset('F90')
        env.unset('F90FLAGS')

    def setup_dependent_build_environment(self, env, dependent_spec):
        # On Cray, the regular compiler wrappers *are* the MPI wrappers.
        if 'platform=cray' in self.spec:
            env.set('MPICC', spack_cc)
            env.set('MPICXX', spack_cxx)
            env.set('MPIF77', spack_fc)
            env.set('MPIF90', spack_fc)
        else:
            env.set('MPICC', join_path(self.prefix.bin, 'mpicc'))
            env.set('MPICXX', join_path(self.prefix.bin, 'mpic++'))
            env.set('MPIF77', join_path(self.prefix.bin, 'mpif77'))
            env.set('MPIF90', join_path(self.prefix.bin, 'mpif90'))

        env.set('MPICH_CC', spack_cc)
        env.set('MPICH_CXX', spack_cxx)
        env.set('MPICH_F77', spack_f77)
        env.set('MPICH_F90', spack_fc)
        env.set('MPICH_FC', spack_fc)

    def setup_dependent_package(self, module, dependent_spec):
        if 'platform=cray' in self.spec:
            self.spec.mpicc = spack_cc
            self.spec.mpicxx = spack_cxx
            self.spec.mpifc = spack_fc
            self.spec.mpif77 = spack_f77
        else:
            self.spec.mpicc = join_path(self.prefix.bin, 'mpicc')
            self.spec.mpicxx = join_path(self.prefix.bin, 'mpic++')
            self.spec.mpifc = join_path(self.prefix.bin, 'mpif90')
            self.spec.mpif77 = join_path(self.prefix.bin, 'mpif77')

        self.spec.mpicxx_shared_libs = [
            join_path(self.prefix.lib, 'libmpicxx.{0}'.format(dso_suffix)),
            join_path(self.prefix.lib, 'libmpi.{0}'.format(dso_suffix))
        ]

    def autoreconf(self, spec, prefix):
        """Not needed usually, configure should be already there"""
        # If configure exists nothing needs to be done
        if os.path.exists(self.configure_abs_path):
            return
        # Else bootstrap with autotools
        bash = which('bash')
        bash('./autogen.sh')

    @run_before('autoreconf')
    def die_without_fortran(self):
        # Until we can pass variants such as +fortran through virtual
        # dependencies depends_on('mpi'), require Fortran compiler to
        # avoid delayed build errors in dependents.
        if (self.compiler.f77 is None) or (self.compiler.fc is None):
            raise InstallError(
                'Mpich requires both C and Fortran compilers!'
            )

    def configure_args(self):
        spec = self.spec
        config_args = [
            '--enable-shared',
            '--with-pm={0}'.format('hydra' if '+hydra' in spec else 'no'),
            '--{0}-romio'.format('enable' if '+romio' in spec else 'disable'),
            '--{0}-ibverbs'.format('with' if '+verbs' in spec else 'without'),
            '--enable-wrapper-rpath={0}'.format('no' if '~wrapperrpath' in
                                                spec else 'yes')
        ]

        if '+slurm' in spec:
            config_args.append('--with-slurm=yes')
            config_args.append('--with-slurm-include={0}'.format(
                spec['slurm'].prefix.include))
            config_args.append('--with-slurm-lib={0}'.format(
                spec['slurm'].prefix.lib))
        else:
            config_args.append('--with-slurm=no')

        if 'pmi=off' in spec:
            config_args.append('--with-pmi=no')
        elif 'pmi=pmi' in spec:
            config_args.append('--with-pmi=simple')
        elif 'pmi=pmi2' in spec:
            config_args.append('--with-pmi=pmi2/simple')
        elif 'pmi=pmix' in spec:
            config_args.append('--with-pmix={0}'.format(spec['pmix'].prefix))

        # setup device configuration
        device_config = ''
        if 'device=ch4' in spec:
            device_config = '--with-device=ch4:'
        elif 'device=ch3' in spec:
            device_config = '--with-device=ch3:nemesis:'

        if 'netmod=ucx' in spec:
            device_config += 'ucx'
        elif 'netmod=ofi' in spec:
            device_config += 'ofi'
        elif 'netmod=mxm' in spec:
            device_config += 'mxm'
        elif 'netmod=tcp' in spec:
            device_config += 'tcp'

        config_args.append(device_config)

        # Specify libfabric or ucx path explicitly, otherwise
        # configure might fall back to an embedded version.
        if 'netmod=ofi' in spec:
            config_args.append('--with-libfabric={0}'.format(
                spec['libfabric'].prefix))
        if 'netmod=ucx' in spec:
            config_args.append('--with-ucx={0}'.format(
                spec['ucx'].prefix))

        return config_args
