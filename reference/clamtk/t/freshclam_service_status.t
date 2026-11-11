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

my $pkexec = File::Spec->catfile( $directory, 'pkexec' );
my $args_file = File::Spec->catfile( $directory, 'pkexec-args' );
open( my $pfile, '>', $pkexec ) or die "create mock pkexec: $!";
print {$pfile} <<'MOCK';
#!/bin/sh
printf '%s\n' "$@" > "$CLAMTK_TEST_PKEXEC_ARGS"
MOCK
close $pfile or die "close mock pkexec: $!";
chmod 0755, $pkexec or die "chmod mock pkexec: $!";
local $ENV{CLAMTK_TEST_PKEXEC_ARGS} = $args_file;

ok( ClamTk::Services::set_freshclam_timer( 1, $pkexec, $systemctl ),
    'enables the daily timer through the authorized system service' );
open( my $args, '<', $args_file ) or die "read mock pkexec arguments: $!";
my @args = <$args>;
chomp @args;
close $args;
is_deeply( \@args,
    [ $systemctl, 'enable', '--now', '--no-block', 'clamav-freshclam-once.timer' ],
    'timer enable is limited to the known unit and does not block the UI' );

ok( ClamTk::Services::set_freshclam_timer( 0, $pkexec, $systemctl ),
    'disables the daily timer through the authorized system service' );
open( $args, '<', $args_file ) or die "read mock pkexec arguments: $!";
@args = <$args>;
chomp @args;
close $args;
is_deeply( \@args,
    [ $systemctl, 'disable', '--now', '--no-block', 'clamav-freshclam-once.timer' ],
    'timer disable targets only the known unit' );

ok( ClamTk::Services::run_freshclam_once( $pkexec, $systemctl ),
    'requests a one-time update through the authorized system service' );
open( $args, '<', $args_file ) or die "read mock pkexec arguments: $!";
@args = <$args>;
chomp @args;
close $args;
is_deeply( \@args,
    [ $systemctl, 'start', '--no-block', 'clamav-freshclam-once.service' ],
    'update is queued asynchronously for the known one-shot unit' );

done_testing();
