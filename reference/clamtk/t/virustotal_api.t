use strict;
use warnings;
use Test::More;
use File::Temp 'tempfile', 'tempdir';
use File::Spec;
use Digest::SHA 'sha256_hex';
use FindBin;

require "$FindBin::Bin/../lib/VirusTotal.pm";

{
    package TestResponse;
    sub new { bless { code => $_[1], body => $_[2] }, $_[0] }
    sub code { $_[0]->{code} }
    sub status_line { "mock status $_[0]->{code}" }
    sub is_success { $_[0]->{code} >= 200 && $_[0]->{code} < 300 }
    sub decoded_content { $_[0]->{body} }
}

{
    package TestUserAgent;
    sub new { bless { response => $_[1] }, $_[0] }
    sub get {
        my ( $self, $url, @headers ) = @_;
        $self->{method} = 'GET';
        $self->{url} = $url;
        $self->{headers} = \@headers;
        return $self->{response};
    }
    sub post {
        my ( $self, $url, @args ) = @_;
        $self->{method} = 'POST';
        $self->{url} = $url;
        $self->{args} = \@args;
        return $self->{response};
    }
}

local $ENV{CLAMTK_VIRUSTOTAL_API_KEY} = 'test-key';
is( ClamTk::VirusTotal::api_key('/missing-secret-tool'), 'test-key',
    'uses an explicitly provided per-user key' );

my $key_dir = tempdir( CLEANUP => 1 );
my $key_tool = File::Spec->catfile( $key_dir, 'secret-tool' );
open( my $key_writer, '>', $key_tool ) or die "create fake keyring: $!";
print {$key_writer} "#!/usr/bin/perl\nprint qq(stored-test-key\\n);\n";
close $key_writer;
chmod 0755, $key_tool or die "chmod fake keyring: $!";
{
    local $ENV{CLAMTK_VIRUSTOTAL_API_KEY};
    is( ClamTk::VirusTotal::api_key($key_tool), 'stored-test-key',
        'reads a per-user key from the desktop keyring interface' );
}

my $capture_file = File::Spec->catfile( $key_dir, 'captured-key' );
open( $key_writer, '>', $key_tool ) or die "rewrite fake keyring: $!";
print {$key_writer} <<'MOCK';
#!/usr/bin/perl
open my $out, '>', $ENV{CAPTURE_KEY} or die $!;
while (<STDIN>) { print $out $_ }
close $out;
MOCK
close $key_writer;
chmod 0755, $key_tool or die "chmod fake keyring: $!";
{
    local $ENV{CAPTURE_KEY} = $capture_file;
    ok( ClamTk::VirusTotal::save_api_key( 'mock-secret', $key_tool ),
        'stores a key through the desktop keyring command' );
}
open( my $saved, '<', $capture_file ) or die "read captured key: $!";
is( scalar <$saved>, "mock-secret\n", 'sends the key to keyring stdin' );
close $saved;

my ( $hash_file, $hash_path ) = tempfile( UNLINK => 1 );
my $large_test_data = 'clamtk-streamed-hash-test' x 10000;
print {$hash_file} $large_test_data;
close $hash_file;
is( ClamTk::VirusTotal::sha256_file($hash_path), sha256_hex($large_test_data),
    'hashes files incrementally without slurping them into memory' );

my $hash = 'a' x 64;
my $json = '{"data":{"attributes":{"last_analysis_results":{"Engine A":{"category":"malicious","result":"Test.Bad","engine_update":"2026-11-10"}}}}}';
my $ua = TestUserAgent->new( TestResponse->new( 200, $json ) );
my $report = ClamTk::VirusTotal::check_hash( $hash, $ua );
is( $report->{status}, 'found', 'parses a VirusTotal v3 file report' );
is( $report->{results}[0][0], 'Engine A', 'returns the engine name' );
is( $report->{results}[0][1], 'Test.Bad', 'returns the engine verdict' );
is( $ua->{url}, "https://www.virustotal.com/api/v3/files/$hash",
    'queries by SHA-256 through the v3 API' );
is_deeply( $ua->{headers}, [ 'x-apikey', 'test-key' ],
    'sends the user key in the API header' );

$ua = TestUserAgent->new( TestResponse->new( 404, '' ) );
is( ClamTk::VirusTotal::check_hash( $hash, $ua )->{status}, 'not-found',
    'distinguishes a missing report from an API failure' );
is( ClamTk::VirusTotal::check_hash( 'not-a-hash', $ua )->{status}, 'invalid-hash',
    'rejects malformed hashes before network access' );

my ( $fh, $file ) = tempfile( UNLINK => 1 );
print {$fh} 'harmless test data';
close $fh;
$ua = TestUserAgent->new(
    TestResponse->new( 200, '{"data":{"id":"analysis-1"}}' )
);
is( ClamTk::VirusTotal::submit_file( $file, $ua )->{status}, 'accepted',
    'accepts a successful explicitly requested file submission' );
is( $ua->{url}, 'https://www.virustotal.com/api/v3/files',
    'uses the v3 file upload endpoint' );

done_testing();
