# ClamTk, copyright (C) 2004-2024 Dave M
package ClamTk::Urlscan;

use strict;
use warnings;

use JSON 'encode_json', 'decode_json';
use LWP::UserAgent;
use LWP::Protocol::https;
use URI;
use ClamTk::VirusTotal;

sub validate_url {
    my ($value) = @_;
    return 0 if !defined $value || $value !~ /\S/;
    my $uri = eval { URI->new($value) };
    return 0 if !$uri || !$uri->scheme || !$uri->host;
    return 0 if lc( $uri->scheme ) !~ /\Ahttps?\z/;
    return 0 if defined $uri->userinfo && length $uri->userinfo;
    return 1;
}

sub submit_url {
    my ( $url, $visibility, $ua ) = @_;
    return { status => 'invalid-url' } if !validate_url($url);
    return { status => 'invalid-visibility' }
        if !defined $visibility
        || $visibility !~ /\A(?:private|unlisted|public)\z/;
    my $key = ClamTk::VirusTotal::secret_key(
        'urlscan', 'CLAMTK_URLSCAN_API_KEY'
    );
    return { status => 'no-key' } if !$key;
    $ua ||= _user_agent();

    my $response = $ua->post(
        'https://urlscan.io/api/v1/scan',
        'API-Key'     => $key,
        Content_Type => 'application/json',
        Content      => encode_json(
            { url => $url, visibility => $visibility }
        ),
    );
    return { status => 'error', message => $response->status_line }
        if !$response->is_success;

    my $body;
    eval { $body = decode_json( $response->decoded_content ); };
    return { status => 'error', message => 'Invalid urlscan response' }
        if $@ || ref $body ne 'HASH' || !$body->{uuid};
    return {
        status     => 'accepted',
        uuid       => $body->{uuid},
        visibility => $body->{visibility} || $visibility,
        result_url => "https://urlscan.io/result/$body->{uuid}/",
    };
}

sub _user_agent {
    my $ua = LWP::UserAgent->new( ssl_opts => { verify_hostname => 1 } );
    $ua->timeout(30);
    $ua->protocols_allowed( [ 'https' ] );
    return $ua;
}

1;
