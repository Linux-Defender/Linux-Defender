use strict;
use warnings;
use Test::More;
use JSON 'decode_json';
use FindBin;

require "$FindBin::Bin/../lib/VirusTotal.pm";
$INC{'ClamTk/VirusTotal.pm'} = "$FindBin::Bin/../lib/VirusTotal.pm";
require "$FindBin::Bin/../lib/Urlscan.pm";

{
    package UrlscanTestResponse;
    sub new { bless { code => $_[1], body => $_[2] }, $_[0] }
    sub is_success { $_[0]->{code} >= 200 && $_[0]->{code} < 300 }
    sub status_line { "mock status $_[0]->{code}" }
    sub decoded_content { $_[0]->{body} }
}

{
    package UrlscanTestUA;
    sub new { bless { response => $_[1] }, $_[0] }
    sub post {
        my ( $self, $url, @args ) = @_;
        $self->{url} = $url;
        $self->{args} = \@args;
        return $self->{response};
    }
}

ok( ClamTk::Urlscan::validate_url('https://example.test/path'),
    'accepts an HTTP(S) URL' );
ok( !ClamTk::Urlscan::validate_url('file:///etc/passwd'),
    'rejects non-web schemes' );
ok( !ClamTk::Urlscan::validate_url('https://user:password@example.test/'),
    'rejects URLs containing embedded credentials' );
ok( !ClamTk::Urlscan::validate_url('not a URL'),
    'rejects malformed URLs' );

local $ENV{CLAMTK_URLSCAN_API_KEY} = 'urlscan-test-key';
my $ua = UrlscanTestUA->new(
    UrlscanTestResponse->new(
        200,
        '{"uuid":"scan-123","visibility":"private"}'
    )
);
my $result = ClamTk::Urlscan::submit_url(
    'https://example.test/a?token=private', 'private', $ua
);
is( $result->{status}, 'accepted', 'accepts a successful URL scan request' );
is( $result->{visibility}, 'private', 'preserves the requested private visibility' );
is( $result->{result_url}, 'https://urlscan.io/result/scan-123/',
    'returns a result link' );
is( $ua->{url}, 'https://urlscan.io/api/v1/scan',
    'uses the documented URLScan submission endpoint' );
my @args = @{ $ua->{args} };
is( $args[0], 'API-Key', 'uses urlscan API-Key header' );
is( $args[1], 'urlscan-test-key', 'sends the per-user key in the header' );
my $payload = decode_json( $args[5] );
is( $payload->{visibility}, 'private', 'submits private visibility explicitly' );
is( $payload->{url}, 'https://example.test/a?token=private',
    'submits the selected URL unchanged after confirmation' );

done_testing();
