Name: cyrus-imapd
Version: 3.0.5
Release: 1%{?dist}

%define ssl_pem_file %{_sysconfdir}/pki/%{name}/%{name}.pem

# uid/gid reserved, see setup:/usr/share/doc/setup*/uidgid
%define uid 76
%define gid 76

%define _cyrususer cyrus
%define _cyrusgroup mail
%define _cyrexecdir %{_exec_prefix}/lib/%{name}

Summary: A high-performance mail server with IMAP, POP3, NNTP and SIEVE support
License: BSD
Group: System Environment/Daemons
URL: http://www.cyrusimap.org/
Source0: ftp://ftp.cyrusimap.org/cyrus-imapd/%{name}-%{version}.tar.gz
Source1: cyrus-imapd.logrotate
Source3: cyrus-imapd.pam-config
Source7: cyrus-imapd.sysconfig
Source8: cyrus-imapd.cvt_cyrusdb_all
Source9: cyrus-imapd.magic
Source10: cyrus-imapd.cron-daily

#systemd support
Source12: cyrus-imapd.service
Source13: cyr_systemd_helper

Source100: cyrus.conf
Source101: imapd.conf

BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires: autoconf
BuildRequires: cyrus-sasl-devel, perl-devel, tcp_wrappers
BuildRequires: libdb-devel, openssl-devel, pkgconfig
BuildRequires: flex, bison, groff, automake
BuildRequires: openldap-devel
BuildRequires: krb5-devel
BuildRequires: net-snmp-devel
BuildRequires: transfig
BuildRequires: jansson-devel >= 2.5
BuildRequires: libical-devel
BuildRequires: xapian-core-devel
BuildRequires: sqlite-devel >= 3
BuildRequires: libxml2-devel
BuildRequires: libicu-devel

Requires(post):   e2fsprogs, perl, grep, coreutils, findutils, systemd-units
Requires(preun):  systemd-units, coreutils
Requires(postun): systemd-units

Requires: %{name}-utils = %{version}-%{release}
Requires: file, libdb-utils
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%{?perl_default_filter}

%description
The %{name} package contains the core of the Cyrus IMAP server.
It is a scaleable enterprise mail system designed for use from
small to large enterprise environments using standards-based
internet mail technologies.

A full Cyrus IMAP implementation allows a seamless mail and bulletin
board environment to be set up across multiple servers. It differs from
other IMAP server implementations in that it is run on "sealed"
servers, where users are not normally permitted to log in and have no
system account on the server. The mailbox database is stored in parts
of the file system that are private to the Cyrus IMAP server. All user
access to mail is through software using the IMAP, POP3 or KPOP
protocols. It also includes support for virtual domains, NNTP,
mailbox annotations, and much more. The private mailbox database design
gives the server large advantages in efficiency, scalability and
administratability. Multiple concurrent read/write connections to the
same mailbox are permitted. The server supports access control lists on
mailboxes and storage quotas on mailbox hierarchies.

The Cyrus IMAP server supports the IMAP4rev1 protocol described
in RFC 3501. IMAP4rev1 has been approved as a proposed standard.
It supports any authentication mechanism available from the SASL
library, imaps/pop3s/nntps (IMAP/POP3/NNTP encrypted using SSL and
TLSv1) can be used for security. The server supports single instance
store where possible when an email message is addressed to multiple
recipients, SIEVE provides server side email filtering.

%package devel
Group: Development/Libraries
Summary: Cyrus IMAP server development files
Provides: %{name}-static = %{version}-%{release}

%description devel
The %{name}-devel package contains header files and libraries
necessary for developing applications which use the imclient library.

%package utils
Group: Applications/System
Summary: Cyrus IMAP server administration utilities
Requires(pre): shadow-utils
Requires(post): grep, coreutils, make, openssl
Requires(postun): shadow-utils
Obsoletes: %{name}-perl < 2.3.16-5

%description utils
The %{name}-utils package contains administrative tools for the
Cyrus IMAP server. It can be installed on systems other than the
one running the server.

%prep
%setup -q
# only to update config.* files
#automake -a -f -c || :
#aclocal -I cmulocal
#autoheader
#autoconf -f

# Modify docs master --> cyrus-master
%{__perl} -pi -e "s@master\(8\)@cyrus-master(8)@" man/*5 man/*8 lib/imapoptions
# sed -i -e 's|\([^-]\)master|\1cyrus-master|g;s|^master|cyrus-master|g;s|Master|Cyrus-master|g;s|MASTER|CYRUS-MASTER|g' \
#        man/master.8 doc/man.html

# Modify path in perl scripts
find . -type f -name "*.pl" | xargs %{__perl} -pi -e "s@/usr/local/bin/perl@%{__perl}@"

# modify lmtp socket path in .conf files
%{__perl} -pi -e "s@/var/imap/@%{_var}/lib/imap/@" master/conf/*.conf doc/cyrusv2.mc

# enable idled in .conf files to prevent error messages
%{__perl} -pi -e "s/#  idled/  idled/" master/conf/*.conf

# Fix permissions on perl programs
find . -type f -name "*.pl" -exec chmod 755 {} \;

%build
%global _hardened_build 1

CPPFLAGS="${__global_cflags} -I%{_includedir}/et -I%{_includedir}/kerberosIV -fno-strict-aliasing"; export CPPFLAGS
CFLAGS="%{__global_cflags} -fno-strict-aliasing"; export CFLAGS
CCDLFLAGS="-rdynamic"; export CCDLFLAGS
LDFLAGS="-Wl,-z,now -Wl,-z,relro"
%ifnarch ppc ppc64
LDFLAGS="$LDFLAGS -pie"; export LDFLAGS
%endif

%{configure} \
  --libexecdir=%{_cyrexecdir} \
  --enable-idled \
  --enable-autocreate \
  --enable-http --enable-calalarmd \
  --enable-xapian \
  --enable-jmap \
  --with-ldap=/usr \
  --with-snmp \
  --enable-murder \
  --enable-replication \
  --enable-nntp \
  --with-perl=%{__perl} \
  --with-syslogfacility=MAIL \
  --with-krbimpl=mit

# make -C man -f Makefile.dist
# make -C doc -f Makefile.dist
make LDFLAGS="$LDFLAGS -pie %{__global_ldflags}"
# make -C notifyd notifytest

%install
rm -rf %{buildroot}

# This is needed to install the perl files correctly
pushd perl/imap
  %{__perl} Makefile.PL PREFIX=%{buildroot}%{_prefix} INSTALLDIRS=vendor
popd
pushd perl/sieve/managesieve
  %{__perl} Makefile.PL PREFIX=%{buildroot}%{_prefix} INSTALLDIRS=vendor
popd

# Do what the regular make install does
make install DESTDIR=%{buildroot} PREFIX=%{_prefix} mandir=%{_mandir}
# make -C man install DESTDIR=%{buildroot} PREFIX=%{_prefix} mandir=%{_mandir}

install -m 755 imtest/imtest       %{buildroot}%{_bindir}/
#install -m 755 notifyd/notifytest  %{buildroot}%{_bindir}/
install -m 755 perl/imap/cyradm    %{buildroot}%{_bindir}/

# Install tools
mkdir -p %{buildroot}%{_cyrexecdir}
for tool in tools/* ; do
  test -f ${tool} && install -m 755 ${tool} %{buildroot}%{_cyrexecdir}/
done

# Create directories
install -d \
  %{buildroot}%{_sysconfdir}/{rc.d/init.d,logrotate.d,pam.d,sysconfig,cron.daily} \
  %{buildroot}%{_libdir}/sasl \
  %{buildroot}%{_var}/spool/imap \
  %{buildroot}%{_var}/lib/imap/{user,quota,proc,log,msg,socket,db,sieve,sync,md5,rpm,backup,meta} \
  %{buildroot}%{_var}/lib/imap/ptclient \
  %{buildroot}%{_datadir}/%{name}/rpm \
  %{buildroot}%{_sysconfdir}/pki/%{name} \
  doc/contrib

# Install additional files
install -m 755 %{SOURCE8}   %{buildroot}%{_cyrexecdir}/cvt_cyrusdb_all
install -m 644 %{SOURCE9}   %{buildroot}%{_datadir}/%{name}/rpm/magic
install -p -m 644 doc/examples/cyrus_conf/prefork.conf %{buildroot}%{_sysconfdir}/cyrus.conf
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/pop
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/imap
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/sieve
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/mupdate
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/lmtp
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/nntp
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/csync
install -p -m 644 %{SOURCE3}    %{buildroot}%{_sysconfdir}/pam.d/http
install -p -m 644 %{SOURCE1}    %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -p -m 644 %{SOURCE7}   %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -p -m 755 %{SOURCE10}   %{buildroot}%{_sysconfdir}/cron.daily/%{name}

install -p -D -m 644 %{SOURCE12}   %{buildroot}%{_unitdir}/cyrus-imapd.service
install -p -D -m 755 %{SOURCE13}   %{buildroot}%{_cyrexecdir}/cyr_systemd_helper

install -m 644 %{SOURCE100}   %{buildroot}%{_sysconfdir}/cyrus.conf
install -m 644 %{SOURCE101}   %{buildroot}%{_sysconfdir}/imapd.conf

# Cleanup of doc dir
find doc perl -name CVS -type d -prune -exec rm -rf {} \;
find doc perl -name .cvsignore -type f -exec rm -f {} \;
rm -f doc/Makefile.dist*
rm -f doc/text/htmlstrip.c
rm -f doc/text/Makefile
rm -rf doc/man

# fix permissions on perl .so files
find %{buildroot}%{_libdir}/perl5/ -type f -name "*.so" -exec chmod 755 {} \;

# fix conflicts with uw-imap
mv %{buildroot}%{_mandir}/man8/imapd.8 %{buildroot}%{_mandir}/man8/imapd.8cyrus
mv %{buildroot}%{_mandir}/man8/pop3d.8 %{buildroot}%{_mandir}/man8/pop3d.8cyrus

# Install templates
install -m 755 -d doc/conf
#install -m 644 master/conf/*.conf doc/conf/

# Generate db config file
( grep '^{' lib/imapoptions | grep _db | cut -d'"' -f 2,4 | \
  sed -e 's/^ *//' -e 's/-nosync//' -e 's/ *$//' -e 's/"/=/'
  echo sieve_version=2.2.3 ) | sort > %{buildroot}%{_datadir}/%{name}/rpm/db.cfg

# create the ghost pem file
touch %{buildroot}%{ssl_pem_file}

# Rename 'master' binary and manpage to avoid clash with postfix
mv -f %{buildroot}%{_cyrexecdir}/master         %{buildroot}%{_cyrexecdir}/cyrus-master
mv -f %{buildroot}%{_mandir}/man8/master.8      %{buildroot}%{_mandir}/man8/cyrus-master.8

# Rename 'fetchnews' binary and manpage to avoid clash with leafnode
mv -f %{buildroot}%{_sbindir}/fetchnews      %{buildroot}%{_sbindir}/cyrfetchnews
mv -f %{buildroot}%{_mandir}/man8/fetchnews.8   %{buildroot}%{_mandir}/man8/cyrfetchnews.8
%{__perl} -pi -e 's|fetchnews|cyrfetchnews|g;s|Fetchnews|Cyrfetchnews|g;s/FETCHNEWS/CYRFETCHNEWS/g' \
        %{buildroot}%{_mandir}/man8/cyrfetchnews.8

# Rename httpd man page
mv -f %{buildroot}%{_mandir}/man8/httpd.8   %{buildroot}%{_mandir}/man8/cyrhttpd.8

#remove executable bit from docs
for ddir in doc perl/imap/examples
do
  find $ddir -type f -exec chmod -x {} \;
done

# eGloo temporary hack:
# /usr/lib/cyrus-imapd/cvt_cyrusdb_all makes reference to /usr/lib/cyrus-imapd/cvt_cyrusdb
cp %{buildroot}%{_sbindir}/cvt_cyrusdb %{buildroot}%{_cyrexecdir}/cvt_cyrusdb

# Remove installed but not packaged files
rm -f %{buildroot}%{_cyrexecdir}/not-mkdep
rm -f %{buildroot}%{_cyrexecdir}/config2header*
rm -f %{buildroot}%{_cyrexecdir}/config2man
rm -f %{buildroot}%{_cyrexecdir}/pop3proxyd
find %{buildroot} -name "perllocal.pod" -exec rm -f {} \;
find %{buildroot} -name ".packlist" -exec rm -f {} \;
rm -f %{buildroot}%{_mandir}/man8/syncnews.8*
find %{buildroot}%{perl_vendorarch} -name "*.bs" -exec rm -f {} \;

%clean
rm -rf %{buildroot}

%pre
# Create 'cyrus' user on target host
getent group saslauth >/dev/null || /usr/sbin/groupadd -g %{gid} -r saslauth 
getent passwd cyrus >/dev/null || /usr/sbin/useradd -c "Cyrus IMAP Server" -d %{_var}/lib/imap -g %{_cyrusgroup} \
  -G saslauth -s /sbin/nologin -u %{uid} -r %{_cyrususer}

%post

# Force synchronous updates, usually only on ext2 filesystems
for i in %{_var}/lib/imap/{user,quota} %{_var}/spool/imap
do
  if [ "$(find $i -maxdepth 0 -printf %%F)" = "ext2" ]; then
    chattr -R +S $i 2>/dev/null ||:
  fi
done

# Create SSL certificates
exec > /dev/null 2> /dev/null

if [ ! -f %{ssl_pem_file} ]; then
pushd %{_sysconfdir}/pki/tls/certs
umask 077
cat << EOF | make %{name}.pem
--
SomeState
SomeCity
SomeOrganization
SomeOrganizationalUnit
localhost.localdomain
root@localhost.localdomain
EOF
chown root.%{_cyrusgroup} %{name}.pem
chmod 640 %{name}.pem
mv %{name}.pem %{ssl_pem_file}
popd
fi

%systemd_post cyrus-imapd.service

%preun
%systemd_preun cyrus-imapd.service

%postun
%systemd_postun_with_restart cyrus-imapd.service

%files
%defattr(-,root,root,-)
%doc COPYING README.md
%doc doc/examples
%config(noreplace) %{_sysconfdir}/cyrus.conf
%config(noreplace) %{_sysconfdir}/imapd.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/pam.d/pop
%config(noreplace) %{_sysconfdir}/pam.d/imap
%config(noreplace) %{_sysconfdir}/pam.d/sieve
%config(noreplace) %{_sysconfdir}/pam.d/lmtp
%config(noreplace) %{_sysconfdir}/pam.d/mupdate
%config(noreplace) %{_sysconfdir}/pam.d/csync
%config(noreplace) %{_sysconfdir}/pam.d/nntp
%config(noreplace) %{_sysconfdir}/pam.d/http
%{_sysconfdir}/cron.daily/%{name}
%{_unitdir}/cyrus-imapd.service
%{_libdir}/lib*.so*
%dir %{_cyrexecdir}
%{_cyrexecdir}/cyr_systemd_helper
%{_sbindir}/arbitron
%{_cyrexecdir}/arbitronsort.pl
%{_sbindir}/chk_cyrus
%{_sbindir}/cyr_df
%{_sbindir}/ctl_cyrusdb
%{_sbindir}/ctl_deliver
%{_sbindir}/ctl_mboxlist
%{_sbindir}/cvt_cyrusdb
%{_cyrexecdir}/cvt_cyrusdb
%{_sbindir}/cyr_dbtool
%{_sbindir}/cyr_expire
%{_sbindir}/cyr_sequence
%{_sbindir}/cyr_synclog
%{_sbindir}/cyr_userseen
%{_sbindir}/cyrdump
%{_cyrexecdir}/cyrus-master
%{_sbindir}/deliver
#%{_cyrexecdir}/dohash
%{_cyrexecdir}/fud
%{_cyrexecdir}/imapd
%{_sbindir}/ipurge
%{_cyrexecdir}/lmtpd
%{_cyrexecdir}/lmtpproxyd
%{_cyrexecdir}/masssievec
%{_sbindir}/mbexamine
%{_sbindir}/mbpath
#%{_cyrexecdir}/migrate-metadata
%{_cyrexecdir}/mkimap
%{_cyrexecdir}/mknewsgroups
%{_cyrexecdir}/notifyd
%{_cyrexecdir}/pop3d
%{_sbindir}/quota
%{_sbindir}/reconstruct
%{_cyrexecdir}/rehash
%{_sbindir}/sievec
%{_sbindir}/sieved
%{_cyrexecdir}/smmapd
%{_sbindir}/squatter
%{_cyrexecdir}/timsieved
%{_sbindir}/tls_prune
%{_cyrexecdir}/translatesieve
#%{_cyrexecdir}/undohash
%{_sbindir}/unexpunge
#%{_cyrexecdir}/upgradesieve
%{_cyrexecdir}/cvt_cyrusdb_all
%{_cyrexecdir}/idled
%{_cyrexecdir}/mupdate
#%{_cyrexecdir}/mupdate-loadgen.pl
%{_cyrexecdir}/proxyd
%{_sbindir}/sync_client
%{_sbindir}/sync_reset
%{_cyrexecdir}/sync_server
%{_sbindir}/cyrfetchnews
%{_cyrexecdir}/nntpd
%{_sbindir}/ptdump
%{_sbindir}/ptexpire
%{_cyrexecdir}/ptloader
# New 
%{_sbindir}/ctl_conversationsdb
%{_sbindir}/ctl_jmapauth
%{_sbindir}/ctl_zoneinfo
%{_sbindir}/cvt_xlist_specialuse
%{_sbindir}/cyr_buildinfo
%{_sbindir}/cyr_deny
%{_sbindir}/cyr_info
%{_sbindir}/cyr_virusscan
%{_sbindir}/dav_reconstruct
%{_sbindir}/mbtool
%{_cyrexecdir}/calalarmd
%{_cyrexecdir}/compile_st.pl
%{_cyrexecdir}/config2rst
%{_cyrexecdir}/config2sample
%{_cyrexecdir}/fixsearchpath.pl
%{_cyrexecdir}/git-version.sh
%{_cyrexecdir}/httpd
%{_cyrexecdir}/jenkins-build.sh
%attr(0750,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/backup
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/db
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/log
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/meta
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/md5
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/msg
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %{_var}/lib/imap/proc
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %{_var}/lib/imap/ptclient
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/quota
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/rpm
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/sieve
%attr(0750,%{_cyrususer},%{_cyrusgroup}) %{_var}/lib/imap/socket
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/sync
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/lib/imap/user
%attr(0700,%{_cyrususer},%{_cyrusgroup}) %dir %{_var}/spool/imap
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/rpm
%{_datadir}/%{name}/rpm/*
%{_mandir}/man5/*
%{_mandir}/man8/*
%dir %{_sysconfdir}/pki/%{name}
%attr(0640,root,%{_cyrusgroup}) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{ssl_pem_file}

%files devel
%defattr(0644,root,root,0755)
%doc COPYING
%{_includedir}/cyrus
%{_libdir}/pkgconfig/*.pc
%{_mandir}/man3/imclient.3*
%exclude %{_libdir}/*.la

%files utils
%defattr(-,root,root)
%{_bindir}/*
%dir %{perl_vendorarch}/Cyrus
%dir %{perl_vendorarch}/Cyrus/IMAP
%{perl_vendorarch}/Cyrus/IMAP/Admin.pm
%{perl_vendorarch}/Cyrus/IMAP/Shell.pm
%{perl_vendorarch}/Cyrus/IMAP/IMSP.pm
%{perl_vendorarch}/Cyrus/IMAP.pm
%dir %{perl_vendorarch}/Cyrus/SIEVE
%{perl_vendorarch}/Cyrus/SIEVE/managesieve.pm
%dir %{perl_vendorarch}/auto
%dir %{perl_vendorarch}/auto/Cyrus
%dir %{perl_vendorarch}/auto/Cyrus/IMAP
%{perl_vendorarch}/auto/Cyrus/IMAP/IMAP.so
%dir %{perl_vendorarch}/auto/Cyrus/SIEVE
%dir %{perl_vendorarch}/auto/Cyrus/SIEVE/managesieve
%{perl_vendorarch}/auto/Cyrus/SIEVE/managesieve/managesieve.so
%{_mandir}/man3/Cyrus::IMAP::Admin.3pm.gz
%{_mandir}/man3/Cyrus::IMAP::Shell.3pm.gz
%{_mandir}/man3/Cyrus::IMAP.3pm.gz
%{_mandir}/man3/Cyrus::IMAP::IMSP.3pm.gz
%{_mandir}/man3/Cyrus::SIEVE::managesieve.3pm.gz
%{_mandir}/man1/*
# FIXME
%{_mandir}/man3/Cyrus::Annotator::Daemon.3pm.gz
%{_mandir}/man3/Cyrus::Annotator::Message.3pm.gz
/usr/share/perl5/Cyrus/Annotator/

%changelog
* Fri Mar 02 2018 eGloo <developer@egloo.ca> - 3.0.5-1
- 3.0.5 release

* Fri Aug 18 2017 eGloo <developer@egloo.ca> - 3.0.3-1
- 3.0.3 release

* Fri May 12 2017 eGloo <developer@egloo.ca> - 3.0.1-1
- Build 3.0.1, based on RHEL 7 source spec file
