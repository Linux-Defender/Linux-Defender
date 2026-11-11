# ClamTk, copyright (C) 2004-2024 Dave M
package ClamTk::Services;

use strict;
use warnings;
use ClamTk::App;

sub freshclam_status {
    my ( $systemctl ) = @_;
    $systemctl ||= ClamTk::App::_find_executable('systemctl');
    return { available => 0, reason => 'systemctl-not-found' } if !$systemctl;

    my $timer = _unit_properties( $systemctl, 'clamav-freshclam-once.timer' );
    return { available => 0, reason => 'systemd-unavailable' } if !$timer;
    return { available => 0, reason => 'timer-not-installed' }
        if $timer->{ LoadState } eq 'not-found';

    my $service = _unit_properties( $systemctl, 'clamav-freshclam-once.service' );
    return { available => 0, reason => 'systemd-unavailable' } if !$service;

    return {
        available      => 1,
        timer_enabled  => $timer->{ UnitFileState } eq 'enabled' ? 1 : 0,
        timer_active   => $timer->{ ActiveState } eq 'active' ? 1 : 0,
        service_active => $service->{ ActiveState } eq 'active' ? 1 : 0,
        timer_unit     => 'clamav-freshclam-once.timer',
        service_unit   => 'clamav-freshclam-once.service',
    };
}

sub set_freshclam_timer {
    my ( $enabled, $pkexec, $systemctl ) = @_;
    $pkexec ||= ClamTk::App::_find_executable('pkexec');
    $systemctl ||= ClamTk::App::_find_executable('systemctl');
    return 0 if !$pkexec || !$systemctl;

    my @args = $enabled
        ? ( 'enable', '--now', '--no-block', 'clamav-freshclam-once.timer' )
        : ( 'disable', '--now', '--no-block', 'clamav-freshclam-once.timer' );
    return system( $pkexec, $systemctl, @args ) == 0 ? 1 : 0;
}

sub run_freshclam_once {
    my ( $pkexec, $systemctl ) = @_;
    $pkexec ||= ClamTk::App::_find_executable('pkexec');
    $systemctl ||= ClamTk::App::_find_executable('systemctl');
    return 0 if !$pkexec || !$systemctl;
    return system(
        $pkexec, $systemctl, 'start', '--no-block',
        'clamav-freshclam-once.service'
    ) == 0 ? 1 : 0;
}

sub _unit_properties {
    my ( $systemctl, $unit ) = @_;
    my $pid = open( my $pipe, '-|', $systemctl, 'show', '--property=LoadState',
        '--property=ActiveState', '--property=UnitFileState', $unit );
    return if !defined $pid;

    my %properties;
    while ( my $line = <$pipe> ) {
        chomp $line;
        my ( $key, $value ) = split( /=/, $line, 2 );
        $properties{$key} = $value if defined $value;
    }
    my $closed = close $pipe;
    return if !$closed || !exists $properties{ LoadState };
    return \%properties;
}

sub _parse_unit_properties {
    my ( $text ) = @_;
    my %properties = map {
        my ( $key, $value ) = split( /=/, $_, 2 );
        defined $value ? ( $key => $value ) : ()
    } split( /\n/, $text // '' );
    return \%properties;
}

1;
