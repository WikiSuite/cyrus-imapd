Name: cyrus-imapd
Version: 3.0.5
Release: 8%{?dist}

%define ssl_pem_file /etc/pki/%name/%name.pem

# UID/GID 76 have long been reserved for Cyrus
%define uid 76
%define gid 76

%define cyrususer cyrus
%define cyrusgroup mail
%define cyrexecdir %_libexecdir/%name

Summary: A high-performance email, contacts and calendar server
License: BSD
URL: http://www.cyrusimap.org/
Source0: http://www.cyrusimap.org/releases/%name-%version.tar.gz
Source10: cyrus-imapd.logrotate
Source11: cyrus-imapd.pam-config
Source12: cyrus-imapd.sysconfig
Source13: cyrus-imapd.cvt_cyrusdb_all
Source14: cyrus-imapd.magic
# XXX A systemd timer would probably be better
Source15: cyrus-imapd.cron-daily
Source17: cyrus-imapd.service
Source18: cyrus-imapd-init.service
Source19: cyrus-imapd.tmpfiles.conf


Source100: cyrus.conf
Source101: imapd.conf


BuildRequires: autoconf automake bison flex gcc gcc-c++ git groff libtool
BuildRequires: pkgconfig systemd transfig

BuildRequires: perl-devel perl-generators perl(ExtUtils::MakeMaker)
BuildRequires: perl(Pod::Html)

BuildRequires: cyrus-sasl-devel glib2-devel
#BuildRequires: jansson-devel krb5-devel libical-devel libnghttp2-devel
BuildRequires: jansson-devel krb5-devel libical-devel
BuildRequires: libxml2-devel mariadb-devel net-snmp-devel openldap-devel
BuildRequires: openssl-devel postgresql-devel shapelib-devel sqlite-devel
BuildRequires: xapian-core-devel

# Miscellaneous modules needed for 'make check' to function:
BuildRequires: cyrus-sasl-plain cyrus-sasl-md5

%if %{with cassandane}
# Additional packages required for cassandane to function
BuildRequires: imaptest net-tools words
BuildRequires: perl(AnyEvent) perl(BSD::Resource) perl(Clone)
BuildRequires: perl(experimental) perl(File::chdir) perl(File::Slurp)
BuildRequires: perl(IO::Socket::INET6) perl(Mail::IMAPTalk)
BuildRequires: perl(Config::IniFiles) perl(Mail::JMAPTalk) perl(Math::Int64)
BuildRequires: perl(Net::CalDAVTalk) perl(Net::CardDAVTalk)
BuildRequires: perl(Net::Server) perl(News::NNTPClient) perl(Path::Tiny)
BuildRequires: perl(String::CRC32) perl(Sys::Syslog)
BuildRequires: perl(Test::Unit::TestRunner) perl(Time::HiRes)
BuildRequires: perl(Unix::Syslog) perl(XML::DOM) perl(XML::Generator)

# These were only for JMAP-Tester
# perl(Moo), perl(Moose), perl(MooseX::Role::Parameterized) perl(Throwable), perl(Safe::Isa)
%endif

Requires(pre): shadow-utils
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
%{?systemd_requires}

Requires: %name-utils = %version-%release
Requires: file libdb-utils sscg
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%{?perl_default_filter}

%description
The Cyrus IMAP (Internet Message Access Protocol) server provides access to
personal mail, system-wide bulletin boards, news-feeds, calendar and contacts
through the IMAP, JMAP, NNTP, CalDAV and CardDAV protocols. The Cyrus IMAP
server is a scalable enterprise groupware system designed for use from small to
large enterprise environments using technologies based on well-established Open
Standards.

A full Cyrus IMAP implementation allows a seamless mail and bulletin board
environment to be set up across one or more nodes. It differs from other IMAP
server implementations in that it is run on sealed nodes, where users are not
normally permitted to log in. The mailbox database is stored in parts of the
filesystem that are private to the Cyrus IMAP system. All user access to mail
is through software using the IMAP, IMAPS, JMAP, POP3, POP3S, KPOP, CalDAV
and/or CardDAV protocols.

The private mailbox database design gives the Cyrus IMAP server large
advantages in efficiency, scalability, and administratability. Multiple
concurrent read/write connections to the same mailbox are permitted. The server
supports access control lists on mailboxes and storage quotas on mailbox
hierarchies.


%package devel
Summary: Cyrus IMAP server development files
Requires: %name%{?_isa} = %version-%release
Requires: pkgconfig

%description devel
The %name-devel package contains header files and libraries
necessary for developing applications which use the imclient library.


%package doc-extra
Summary: Extra documentation for the Cyrus IMAP server
#BuildArch: noarch

%description doc-extra
This package contains the HTML documentation for the Cyrus IMAP server, as well
as some legacy and internal documentation not useful for normal operation of
the server.


%package utils
Summary: Cyrus IMAP server administration utilities

%description utils
The cyrus-imapd-utils package contains administrative tools for the
Cyrus IMAP server. It can be installed on systems other than the
one running the server.


%package vzic
Summary: Utilities to convert timezone database files
License: GPLv2+
Requires: %name = %version-%release
# Contains a lightly forked version of vzic.  This seems to have been bundled
# into various other things and it's old, so I'm not sure where the upstream
# is.  Here are a couple of possible upstreams:
# https://github.com/libical/vzic
# https://sourceforge.net/projects/vzic/
# It is probably a good idea to split it out and package it separately, but the
# code here definitely differs from that at the second link above.
Provides: bundled(vzic) = 1.3

%description vzic
vzic is a program to convert the Olson timezone database files into VTIMEZONE
files compatible with the iCalendar specification (RFC2445).

This package contains a forked version of vzic for internal use by the Cyrus
IMAP server.

# Build dir is either $PWD, $(pwd) or %

%prep
%autosetup -p1 -S git
echo %version > VERSION

%build
# Needed because of Patch4.
autoreconf -vi

%configure \
    --disable-silent-rules \
    \
    --libexecdir=%cyrexecdir \
    --with-extraident="%release ClearOS" \
    --with-krbimpl=mit \
    --with-ldap=/usr \
    --with-pgsql \
    --with-libwrap=no \
    --with-perl=%__perl \
    --with-snmp \
    --with-syslogfacility=MAIL \
    \
    --enable-autocreate \
    --enable-backup \
    --enable-calalarmd \
    --enable-http \
    --enable-idled \
    --enable-jmap \
    --enable-murder \
    --enable-nntp \
    --enable-replication \
    --enable-unit-tests \
    --enable-xapian \
    --without-clamav
#

# The configure script will set up the Perl makefiles, but not in the way
# Fedora needs them.  So regenerate them manually.
for i in perl/annotator perl/imap perl/sieve/managesieve; do
    pushd $i
    rm -f Makefile
    perl Makefile.PL INSTALLDIRS=vendor # NO_PERLOCAL=1 NO_PACKLIST=1
    popd
done

%make_build

# This isn't built by default, but this package has always installed it.
make notifyd/notifytest

# Also not built by default, but the tools are needed for serving timezone info
make -C tools/vzic


%install
make install DESTDIR=%buildroot

# Create directories
install -d \
    %buildroot/etc/{rc.d/init.d,logrotate.d,pam.d,sysconfig,cron.daily} \
    %buildroot/%_libdir/sasl \
    %buildroot/var/spool/imap \
    %buildroot/var/lib/imap/{user,quota,proc,log,msg,socket,db,sieve,sync,md5,rpm,backup,meta} \
    %buildroot/var/lib/imap/ptclient \
    %buildroot/%_datadir/%name/rpm \
    %buildroot/%cyrexecdir \
    %buildroot/etc/pki/%name

install -d -m 0750 \
    %buildroot/run/cyrus \
    %buildroot/run/cyrus/socket

install -d -m 0700 \
    %buildroot/run/cyrus/db \
    %buildroot/run/cyrus/lock \
    %buildroot/run/cyrus/proc

# Some tools which aren't installed by the makefile which we have always installed
install -m 755 notifyd/notifytest  %buildroot%_bindir/
install -m 755 perl/imap/cyradm    %buildroot%_bindir/
for i in arbitronsort.pl masssievec mkimap mknewsgroups rehash translatesieve; do
    install -m 755 tools/$i %buildroot/%cyrexecdir/
done

for i in vzic vzic-test.pl vzic-merge.pl vzic-dump.pl; do
    install -m 755 tools/vzic/$i %buildroot/%cyrexecdir/
done

# Install additional files
install -p -m 644 %SOURCE10 %buildroot/etc/logrotate.d/%name
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/pop
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/imap
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/sieve
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/mupdate
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/lmtp
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/nntp
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/csync
install -p -m 644 %SOURCE11 %buildroot/etc/pam.d/http
install -p -m 644 %SOURCE12 %buildroot/etc/sysconfig/%name
install -p -m 755 %SOURCE13   %buildroot/%cyrexecdir/cvt_cyrusdb_all
install -p -m 644 %SOURCE14   %buildroot/%_datadir/%name/rpm/magic
install -p -m 755 %SOURCE15 %buildroot/etc/cron.daily/%name
install -p -m 644 %SOURCE100   %buildroot/etc/cyrus.conf
install -p -m 644 %SOURCE101   %buildroot/etc/imapd.conf
install -p -D -m 644 %SOURCE17 %buildroot/%_unitdir/cyrus-imapd.service
install -p -D -m 644 %SOURCE18 %buildroot/%_unitdir/cyrus-imapd-init.service
install -p -D -m 644 %SOURCE19 %buildroot/%_tmpfilesdir/cyrus-imapd.conf

# Cleanup of doc dir
find doc perl -name CVS -type d -prune -exec rm -rf {} \;
find doc perl -name .cvsignore -type f -exec rm -f {} \;
rm -f doc/Makefile.dist*
rm -f doc/text/htmlstrip.c
rm -f doc/text/Makefile
rm -rf doc/man

# fix permissions on perl .so files
#find %buildroot/%_libdir/perl5/ -type f -name "*.so" -exec chmod 755 {} \;

# Generate db config file
# XXX Is this still necessary?
( grep '^{' lib/imapoptions | grep _db | cut -d'"' -f 2,4 | \
  sed -e 's/^ *//' -e 's/-nosync//' -e 's/ *$//' -e 's/"/=/'
  echo sieve_version=2.2.3 ) | sort > %buildroot/%_datadir/%name/rpm/db.cfg

# create the ghost pem file
touch %buildroot/%ssl_pem_file

# Cyrus has various files with extremely conflicting names.  Some of these are
# not unexpected ("imapd" itself) but some like "httpd" are rather surprising.

# Where there are only conflicting manpages, they have been moved to a "8cyrus"
# section.  If the binary was renamed, then the manpages are renamed to match
# but a internal replacement has not been done.  This may lead to more
# confusion but involves modifying fewer upstream files.

# Actual binary conflicts
# Rename 'fetchnews' binary and manpage to avoid clash with leafnode
mv %buildroot/%_sbindir/fetchnews %buildroot/%_sbindir/cyr_fetchnews
mv %buildroot/%_mandir/man8/fetchnews.8 %buildroot/%_mandir/man8/cyr_fetchnews.8

# Fix conflict with dump
mv %buildroot/%_sbindir/restore %buildroot/%_sbindir/cyr_restore
mv %buildroot/%_mandir/man8/restore.8 %buildroot/%_mandir/man8/cyr_restore.8

# Fix conceptual conflict with quota
mv %buildroot/%_sbindir/quota %buildroot/%_sbindir/cyr_quota
mv %buildroot/%_mandir/man8/quota.8 %buildroot/%_mandir/man8/cyr_quota.8

# fix conflicts with uw-imap
mv %buildroot/%_mandir/man8/imapd.8 %buildroot/%_mandir/man8/imapd.8cyrus
mv %buildroot/%_mandir/man8/pop3d.8 %buildroot/%_mandir/man8/pop3d.8cyrus

# Rename 'master' manpage
mv %buildroot/%_mandir/man8/master.8 %buildroot/%_mandir/man8/master.8cyrus

# Rename 'httpd' manpage to avoid clash with Apache
mv %buildroot/%_mandir/man8/httpd.8 %buildroot/%_mandir/man8/httpd.8cyrus

# Old cyrus packages used to keep some executables in /usr/lib/cyrus-imapd
# RF hardcoded-library-path in %%buildroot/usr/lib/cyrus-imapd
mkdir %buildroot/usr/lib/cyrus-imapd
pushd %buildroot/usr/lib/cyrus-imapd
ln -s ../../sbin/deliver
popd

#remove executable bit from docs
for ddir in doc perl/imap/examples
do
  find $ddir -type f -exec chmod -x {} \;
done

# Remove pointless libtool archives
rm %buildroot/%_libdir/*.la

# Remove installed but not packaged files
rm %buildroot/%cyrexecdir/pop3proxyd
find %buildroot -name "perllocal.pod" -exec rm {} \;
find %buildroot -name ".packlist" -exec rm {} \;


%check
make %{?_smp_mflags} check || exit 1

%clean
rm -rf %{buildroot}


%pre
# Create 'cyrus' user on target host
getent group saslauth >/dev/null || /usr/sbin/groupadd -g %gid -r saslauth
getent passwd cyrus >/dev/null || /usr/sbin/useradd -c "Cyrus IMAP Server" -d /var/lib/imap -g %cyrusgroup \
  -G saslauth -s /sbin/nologin -u %uid -r %cyrususer

%post
/sbin/ldconfig
%systemd_post cyrus-imapd.service

%preun
%systemd_preun cyrus-imapd.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart cyrus-imapd.service


%files
%license COPYING
%doc README.md doc/README.* doc/examples doc/text

%_datadir/cyrus-imapd
%_libdir/libcyrus*.so.*
%_mandir/man5/*
%_mandir/man8/*

%dir /etc/pki/cyrus-imapd
%attr(0640,root,%cyrusgroup) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %ssl_pem_file


%config(noreplace) /etc/cyrus.conf
%config(noreplace) /etc/imapd.conf
%config(noreplace) /etc/logrotate.d/cyrus-imapd
%config(noreplace) /etc/sysconfig/cyrus-imapd
%config(noreplace) /etc/pam.d/*

/etc/cron.daily/cyrus-imapd
%_unitdir/cyrus-imapd.service
%_unitdir/cyrus-imapd-init.service
%_tmpfilesdir/cyrus-imapd.conf

%dir %cyrexecdir/
%cyrexecdir/[a-uw-z]*

# This creates some directories which in the default configuration cyrus will
# never use because they are placed under /run instead.  However, old
# configurations or setup advice from the 'net might reference them, and so
# it's simpler to just leave them in the package.
%attr(0750,%cyrususer,%cyrusgroup) %dir /var/lib/imap/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/backup/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/db/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/log/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/meta/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/md5/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/msg/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/proc/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/ptclient/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/quota/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/rpm/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/sieve/
%attr(0750,%cyrususer,%cyrusgroup) /var/lib/imap/socket
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/sync/
%attr(0700,%cyrususer,%cyrusgroup) /var/lib/imap/user/
%attr(0700,%cyrususer,%cyrusgroup) /var/spool/imap/

# The new locations
%attr(0750,%cyrususer,%cyrusgroup) %dir /run/cyrus/
%attr(0700,%cyrususer,%cyrusgroup) /run/cyrus/db/
%attr(0700,%cyrususer,%cyrusgroup) /run/cyrus/lock/
%attr(0700,%cyrususer,%cyrusgroup) /run/cyrus/proc/
%attr(0750,%cyrususer,%cyrusgroup) /run/cyrus/socket/


%files devel
%_includedir/cyrus/
%_libdir/libcyrus*.so
%_libdir/pkgconfig/*.pc
%_mandir/man3/imclient.3*


%files doc-extra
%doc doc/html doc/internal doc/legacy


%files utils
%license COPYING
%doc perl/imap/README
%doc perl/imap/Changes
%doc perl/imap/examples
%{_bindir}/*
%{_sbindir}/*
%{perl_vendorarch}/auto/Cyrus
%{perl_vendorarch}/Cyrus
%{perl_vendorlib}/Cyrus
%{_mandir}/man3/*.3pm*
%{_mandir}/man1/*
# RF hardcoded-library-path in /usr/lib/cyrus-imapd
/usr/lib/cyrus-imapd


%files vzic
%cyrexecdir/vzic*


%changelog
* Sat Mar 03 2018 eGloo <developer@egloo.ca> - 3.0.5-8
- Merged with upstream spec file

* Thu Mar 01 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-8
- Bump client_timeout value in test suite.

* Thu Mar 01 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-7
- Add patch to fix imtest (rhbz#1543481).
- Fix vzic makefile to use proper cflags (rhbz#1550543).

* Mon Feb 26 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-6
- Update cassandane checkout.
- Add two new build dependencies.
- Remove all JMAP-related tests from the exclusion lists, since cassandane no
  longer runs any JMAP tests on cyrus 3.0.
- Collapse unused test skip lists.
- Add ten additional skipped tests, after consultation with upstream.


* Mon Feb 26 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-5
- Add patch to fix segfaults in squatter.
- Exclude one test on all releases instead of just F28+.
- Remove --cleanup from cassandane invocation.

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 09 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-3
- Re-enable clamav and mariadb support as those are now built with openssl 1.1.
- But no clamav on ppc64 because of
  https://bugzilla.redhat.com/show_bug.cgi?id=1534071

* Thu Jan 04 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-2
- Reorganize some test exclusions so things build on all releases.

* Thu Jan 04 2018 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.5-1
- Update to 3.0.5.
- Add one new failing test.
- Remove one now-passing test on rawhide.

* Mon Dec 18 2017 Pavel Zhukov <pzhukov@redhat.com> - 3.0.4-6
- Rebuild with new net-snmp

* Thu Nov 30 2017 Pete Walter <pwalter@fedoraproject.org> - 3.0.4-5
- Rebuild for ICU 60.1

* Wed Nov 29 2017 Pavel Zhukov <pzhukov@redhat.com> - 3.0.4-4
- Do not require tcp_wrappers (#1518759)

* Tue Nov 14 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.4-3
- Rebuild for new libical.
- Add patch to fix compilation error with new libical.
- Disable two tests which fail due to the new libical.

* Tue Oct 24 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.4-2
- Fix typo in default config;
  https://bugzilla.redhat.com/show_bug.cgi?id=1506000

* Tue Sep 05 2017 Pavel Zhukov <landgraf@fedoraproject.org> - 3.0.4-1
- Update to 3.0.4
- Patched cassandane for new behaviour. It should be updated idealy.
- Disable ImapTest.urlauth2 test; it seems to fail randomly regardless of
  architecture.

* Fri Aug 11 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.3-1
- Update to 3.0.3, which contains an important security fix.  The fix is not
  embargoed but no CVE has been assigned yet.
- Drop patches merged upstream.
- An update of imaptest has resulted in three additional cassandane failures,
  reported upstream as https://github.com/cyrusimap/cyrus-imapd/issues/2087.
  In order to get the security fix out without delay, those three tests have been
  disabled.

* Fri Aug 11 2017 Igor Gnatenko <ignatenko@redhat.com> - 3.0.2-9
- Rebuilt after RPM update (№ 3)

* Thu Aug 10 2017 Igor Gnatenko <ignatenko@redhat.com> - 3.0.2-8
- Rebuilt for RPM soname bump

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jun 30 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.2-5
- Add two patches from upstream which fix JMAPCalendars issues on 32-bit and
  big-endian architectures.
- Clean up test invocation and exclusion list.  More tests pass now.

* Wed Jun 28 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.2-4
- Explicitly set specialusealways: 1 in the default config.

* Tue Jun 27 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.2-3
- Patch the provided imapd.conf and cyrus.conf to more closely match previous
  Fedora defaults and directories included in this package and to enable
  features which are supported by the Fedora build.
- Add tmpfiles.d configuration file for directories in /run.

* Tue Jun 27 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.2-2
- Exclude one more test from 32-bit arches.  Looks like this failure crept in
  with the Cassandane update.

* Thu Jun 22 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.2-1
- Update to 3.0.2.
- New Cassandane snapshot, with more tests (all of which are passing).

* Tue Jun 20 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.1-7
- Add old /usr/lib/cyrus-imapd directory to the utils package and add a symlink
  there to the deliver binary.  This should help a bit with migrations.
- Add upstream patch to fix reconstruct failures on 32-bit architectures.
  Re-enable those five Cassandane tests.

* Thu Jun 15 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.1-6
- Rename two commands: quota -> cyr_quota, restore -> cyr_restore.
- Fix Cassandane to handle those renames.
- Fix location of cyr_fetchnews.
- Fix Perl 5.26-related module linking issue which caused a test failure.
  Fixes https://bugzilla.redhat.com/show_bug.cgi?id=1461669

* Tue Jun 06 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.1-5
- Use proper path to ctl_mboxlist in cron file.
- Add patch to increase individual test timeout.  Sometimes armv7hl can't
  complete a single test in 20 seconds.
- Disable the Metronome tests; upstream says that they just won't reliably on
  shared hardware.
- Don't bother running Cassandane on s390x for now.  The machines are simply
  too slow.

* Tue Jun 06 2017 Jitka Plesnikova <jplesnik@redhat.com> - 3.0.1-4
- Perl 5.26 rebuild

* Fri Jun 02 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.1-3
- Remove clamav from build requirements.
- Add --cleanup to Cassandane call to hopefully reduce build disk usage.
- Disable maxforkrate test on s390x; our builders are too slow to run it.

* Fri Jun 02 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.1-2
- Add patch to fix up some endianness issues.
- Enable both test suites on all architectures.
- Add arch-specific excludes for a few Cassandane tests.

* Thu Apr 20 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 3.0.1-1
- Initial attempt at importing 3.0.  Many new dependencies.
- Use a stock sample imapd.conf file instead of a Fedora-provided one.

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.5.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Jan 09 2017 Jason L Tibbitts III <tibbs@math.uh.edu> - 2.5.10-2
- Rename httpd manpage to "cyrhttpd" to avoid conflict with the httpd package.

* Wed Nov 23 2016 Jason L Tibbitts III <tibbs@math.uh.edu> - 2.5.10-1
- Initial update to the 2.5 series.
- Significant spec cleanups.
- Add sscg dep and follow
  https://fedoraproject.org/wiki/Packaging:Initial_Service_Setup for initial
  cert generation.
- Change default conf to use the system crypto policy.

* Tue May 17 2016 Jitka Plesnikova <jplesnik@redhat.com> - 2.4.18-3
- Perl 5.24 rebuild

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.4.18-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Oct 01 2015 Jason L Tibbitts III <tibbs@math.uh.edu> - 2.4.18-1
- Update to 2.4.18, rhbz#1267871 and rhbz#1267878
- Backport ff4e6c71d932b3e6bbfa67d76f095e27ff21bad0 to fix issues from
  http://seclists.org/oss-sec/2015/q3/651

* Wed Sep 09 2015 Jason L Tibbitts III <tibbs@math.uh.edu> - 2.4.17-14
- Use %%license tag
- Have -devel require the base package
- Minor cleanups

* Sat Aug 08 2015 Jason L Tibbitts III <tibbs@math.uh.edu> - 2.4.17-13
- Remove invalid Patch0: URL.
- Use HTTP for upstream source.
- pod2html was split out of the main perl package, breaking cyrus.
  Add a build dep for it.

* Wed Jul 29 2015 Kevin Fenzi <kevin@scrye.com> 2.4.17-12
- Rebuild for new librpm

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.17-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Jun 05 2015 Jitka Plesnikova <jplesnik@redhat.com> - 2.4.17-10
- Perl 5.22 rebuild

* Wed Aug 27 2014 Jitka Plesnikova <jplesnik@redhat.com> - 2.4.17-9
- Perl 5.20 rebuild

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.17-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.17-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.17-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Jul 18 2013 Petr Pisar <ppisar@redhat.com> - 2.4.17-5
- Perl 5.18 rebuild

* Fri Jul 12 2013 Michal Hlavinka <mhlavink@redhat.com> - 2.4.17-4
- spec clean up

* Thu Apr 18 2013 Michal Hlavinka <mhlavink@redhat.com> - 2.4.17-3
- make sure binaries are hardened

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.17-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Dec  1 2012 Jeroen van Meeuwen <vanmeeuwen@kolabsys.com> - 2.4.17-1
- New upstream version, fixes upstream bugs:
- reconstruct doesn't retain internaldate correctly (#3733)
- Race condition in maibox rename (#3696)
- DBERROR db4: Transaction not specified for a transactional database (#3715)
- performance degradation on huge indexes in 2.4 branch (#3717)
- typo fix in imapd.conf man page (#3729)
- quota does not find all quotaroots if quotalegacy, fulldirhash and prefix are used and virtdomains is off (#3735)
- Mail delivered during XFER was lost (#3737)
- replication does not work on RENAME (#3742)
- Failed asserting during APPEND (#3754)

* Fri Nov 30 2012 Michal Hlavinka <mhlavink@redhat.com> - 2.4.16-5
- do not use strict aliasing

* Tue Aug 21 2012 Michal Hlavinka <mhlavink@redhat.com> - 2.4.16-4
- use new systemd rpm macros (#850079)

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.16-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jun 11 2012 Petr Pisar <ppisar@redhat.com> - 2.4.16-2
- Perl 5.16 rebuild

* Thu Apr 19 2012 Jeroen van Meeuwen <vanmeeuwen@kolabsys.com> - 2.4.16-1
- New upstream release

* Wed Apr 18 2012 Jeroen van Meeuwen <vanmeeuwen@kolabsys.com> - 2.4.15-1
- New upstream release

* Wed Apr 11 2012 Michal Hlavinka <mhlavink@redhat.com> - 2.4.14-2
- rebuilt because of new libdb

* Wed Mar 14 2012 Michal Hlavinka <mhlavink@redhat.com> - 2.4.14-1
- updated to 2.4.14

* Tue Feb 07 2012 Michal Hlavinka <mhlavink@redhat.com> - 2.4.13-3
- use PraveTmp in systemd unit file

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Jan 02 2012 Jeroen van Meeuwen <vanmeeuwen@kolabsys.com> - 2.4.13-1
- New upstream release

* Wed Dec 07 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.12-5
- do not use digest-md5 as part of default auth mechanisms,
  it does not coop with pam

* Tue Nov 22 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.12-4
- reduce noisy logging, add option to turn on LOG_DEBUG syslog
  messages again (thanks Philip Prindeville) (#754940)

* Mon Oct 24 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.12-3
- add login and digest-md5 as part of default auth mechanisms (#748278)

* Tue Oct 11 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.12-2
- do not hide errors if cyrus user can't be added

* Wed Oct 05 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.12-1
- cyrus-imapd updated to 2.4.12
- fixes incomplete authentication checks in nntpd (Secunia SA46093)

* Fri Sep  9 2011 Jeroen van Meeuwen <vanmeeuwen@kolabsys.com> - 2.4.11-1
- update to 2.4.11
- Fix CVE-2011-3208 (#734926, #736838)

* Tue Aug 16 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.10-4
- rebuild with db5

* Thu Jul 21 2011 Petr Sabata <contyk@redhat.com> - 2.4.10-3
- Perl mass rebuild

* Wed Jul 20 2011 Petr Sabata <contyk@redhat.com> - 2.4.10-2
- Perl mass rebuild

* Wed Jul  6 2011 Jeroen van Meeuwen <kanarip@kanarip.com> - 2.4.10-1
- New upstream release

* Wed Jun 22 2011 Iain Arnell <iarnell@gmail.com> 2.4.8-5
- Patch to work with Perl 5.14

* Mon Jun 20 2011 Marcela Mašláňová <mmaslano@redhat.com> - 2.4.8-4
- Perl mass rebuild

* Fri Jun 10 2011 Marcela Mašláňová <mmaslano@redhat.com> - 2.4.8-3
- Perl 5.14 mass rebuild

* Mon May 09 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.8-2
- fixed: systemd commands in %%post (thanks Bill Nottingham)

* Thu Apr 14 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.8-1
- cyrus-imapd updated to 2.4.8
- fixed: cannot set unlimited quota through proxy
- fixed: reconstruct tries to set timestamps again and again
- fixed: response for LIST "" user is wrong
- fixed: THREAD command doesn't support quoted charset
- fixed crashes in mupdatetest and cyr_expire when using -x

* Mon Apr 04 2011 Michal Hlaivnka <mhlavink@redhat.com> - 2.4.7-2
- now using systemd

* Thu Mar 31 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.7-1
- updated to 2.4.7

* Fri Feb 11 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.4.6-1
- updated to 2.4.6
- "autocreate" and "autosieve" features were removed

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.16-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jan 21 2011 Michal Hlavinka <mhlavink@redhat.com> - 2.3.16-7
- don't force sync io for all filesystems

* Fri Jul 09 2010 Michal Hlavinka <mhlavink@redhat.com> - 2.3.16-6
- follow licensing guideline update
- devel sub-package has to have virtual static provides (#609604)

* Mon Jun 07 2010 Michal Hlavinka <mhlavink@redhat.com> - 2.3.16-5
- spec cleanup
- simplified packaging (merge -perl in -utils)
- remove obsoleted and/or unmaintained additional sources/patches
- remove long time not used files from the cvs/srpm
- update additional sources/patches from their upstream

* Tue Jun 01 2010 Marcela Maslanova <mmaslano@redhat.com> - 2.3.16-4
- Mass rebuild with perl-5.12.0

* Tue Apr 20 2010 Michal Hlavinka <mhlavink@redhat.com> - 2.3.16-3
- add support for QoS marked traffic (#576652)

* Thu Jan 14 2010 Michal Hlavinka <mhlavink@redhat.com> - 2.3.16-2
- ignore user_denny.db if missing (#553011)
- fix location of certificates in default imapd.conf
