use strict;
use warnings;
use Test::More;
use File::Temp 'tempdir';
use File::Spec;
use FindBin;

require "$FindBin::Bin/../lib/Services.pm";

my $properties = ClamTk::Services::_parse_unit_properties(
    "LoadState=loaded\nActiveState=active\nUnitFileState=enabled\n"
);
is( $properties->{LoadState}, 'loaded', 'reads systemd load state' );
is( $properties->{ActiveState}, 'active', 'reads active timer state' );
is( $properties->{UnitFileState}, 'enabled', 'reads enabled timer state' );

my $not_found = ClamTk::Services::_parse_unit_properties("LoadState=not-found\n");
is( $not_found->{LoadState}, 'not-found', 'represents a missing timer unit' );

my $directory = tempdir( CLEANUP => 1 );
my $systemctl = File::Spec->catfile( $directory, 'systemctl' );
open( my $fh, '>', $systemctl ) or die "create mock systemctl: $!";
print {$fh} <<'MOCK';
#!/bin/sh
case "$*" in
  *clamav-freshclam-once.timer*)
    printf 'LoadState=loaded\nActiveState=active\nUnitFileState=enabled\n'
    ;;
  *clamav-freshclam-once.service*)
    printf 'LoadState=loaded\nActiveState=inactive\nUnitFileState=static\n'
    ;;
  *) exit 2 ;;
esac
MOCK
close $fh or die "close mock systemctl: $!";
chmod 0755, $systemctl or die "chmod mock systemctl: $!";

my $status = ClamTk::Services::freshclam_status($systemctl);
ok( $status->{available}, 'detects an installed system timer' );
ok( $status->{timer_active}, 'reports an active daily timer' );
ok( $status->{timer_enabled}, 'reports the timer is enabled' );
ok( !$status->{service_active}, 'reports no update is currently running' );

done_testing();
