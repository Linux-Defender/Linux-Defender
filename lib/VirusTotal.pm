# ClamTk, copyright (C) 2004-2024 Dave M
package ClamTk::VirusTotal;

use strict;
use warnings;

use JSON 'decode_json';
use Digest::SHA;
use LWP::UserAgent;
use LWP::Protocol::https;
use File::Spec;

sub api_key {
    my ($secret_tool) = @_;
    return $ENV{ CLAMTK_VIRUSTOTAL_API_KEY }
        if defined $ENV{ CLAMTK_VIRUSTOTAL_API_KEY }
        && length $ENV{ CLAMTK_VIRUSTOTAL_API_KEY };

    $secret_tool ||= _find_executable('secret-tool');
    return if !$secret_tool;
    my $pid = open( my $pipe, '-|', $secret_tool, 'lookup',
        'application', 'clamtk', 'account', 'virustotal' );
    return if !defined $pid;
    local $/;
    my $key = <$pipe> // '';
    my $ok  = close $pipe;
    return if !$ok;
    $key =~ s/\s+\z//;
    return length $key ? $key : undef;
}

sub save_api_key {
    my ( $key, $secret_tool ) = @_;
    return 0 if !defined $key || $key !~ /\S/;
    $secret_tool ||= _find_executable('secret-tool');
    return 0 if !$secret_tool;

    my $pid = open( my $pipe, '|-', $secret_tool, 'store',
        '--label=ClamTk VirusTotal API key',
        'application', 'clamtk', 'account', 'virustotal' );
    return 0 if !defined $pid;
    print {$pipe} $key, "\n" or return 0;
    return close $pipe ? 1 : 0;
}

sub check_hash {
    my ( $hash, $ua ) = @_;
    return { status => 'invalid-hash' }
        if !defined $hash || $hash !~ /\A[0-9a-f]{64}\z/i;
    my $key = api_key();
    return { status => 'no-key' } if !$key;
    $ua ||= _user_agent();

    my $response = $ua->get(
        "https://www.virustotal.com/api/v3/files/$hash",
        'x-apikey' => $key
    );
    if ( $response->code == 404 ) {
        return { status => 'not-found' };
    }
    return { status => 'error', message => $response->status_line }
        if !$response->is_success;

    my $body;
    eval { $body = decode_json( $response->decoded_content ); };
    return { status => 'error', message => 'Invalid VirusTotal response' }
        if $@ || ref $body ne 'HASH';

    my $results = $body->{ data }{ attributes }{ last_analysis_results };
    return { status => 'not-found' } if ref $results ne 'HASH';
    my @rows = map {
        my $engine = $results->{ $_ };
        [ $_,
            ( $engine->{ result } || $engine->{ category } || '---' ),
            ( $engine->{ engine_update } || '---' ) ]
    } sort keys %$results;
    return { status => 'found', results => \@rows };
}

sub sha256_file {
    my ($path) = @_;
    open( my $file, '<', $path ) or return;
    binmode $file;
    my $digest = Digest::SHA->new(256);
    my $buffer;
    while (1) {
        my $bytes = read( $file, $buffer, 65536 );
        return if !defined $bytes;
        last if !$bytes;
        $digest->add($buffer);
    }
    close $file or return;
    return $digest->hexdigest;
}

sub submit_file {
    my ( $path, $ua ) = @_;
    return { status => 'invalid-file' } if !defined $path || !-f $path;
    my $key = api_key();
    return { status => 'no-key' } if !$key;
    $ua ||= _user_agent();

    my $response = $ua->post(
        'https://www.virustotal.com/api/v3/files',
        'x-apikey'    => $key,
        Content_Type => 'multipart/form-data',
        Content      => [ file => [$path] ],
    );
    return { status => 'error', message => $response->status_line }
        if !$response->is_success;

    my $body;
    eval { $body = decode_json( $response->decoded_content ); };
    return { status => 'error', message => 'Invalid VirusTotal response' }
        if $@ || ref $body ne 'HASH' || !ref $body->{ data };
    return { status => 'accepted', analysis_id => $body->{ data }{ id } };
}

sub _user_agent {
    my $ua = LWP::UserAgent->new( ssl_opts => { verify_hostname => 1 } );
    $ua->timeout(30);
    $ua->protocols_allowed( [ 'https' ] );
    return $ua;
}

sub _find_executable {
    my ($name) = @_;
    for my $directory ( File::Spec->path ) {
        next if !defined $directory || $directory eq '';
        my $path = File::Spec->catfile( $directory, $name );
        return $path if -f $path && -x $path;
    }
    return;
}

1;
