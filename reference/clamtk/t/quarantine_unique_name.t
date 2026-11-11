use strict;
use warnings;
use Test::More;
use FindBin;
use File::Temp 'tempdir';

require "$FindBin::Bin/../lib/Quarantine.pm";

my $directory = tempdir( CLEANUP => 1 );
my $hash_a = 'a' x 64;
my $hash_b = 'b' x 64;

my $first = ClamTk::Quarantine::unique_quarantine_path(
    $directory, 'sample.txt', $hash_a
);
is( $first, "$directory/sample.txt", 'uses original name when available' );
open( my $first_file, '>', $first ) or die "cannot create test file: $!";
print {$first_file} 'preserve this file';
close $first_file;

my $second = ClamTk::Quarantine::unique_quarantine_path(
    $directory, 'sample.txt', $hash_b
);
is(
    $second,
    "$directory/sample.txt.clamtk-" . substr( $hash_b, 0, 12 ),
    'uses a content-specific name when basename already exists'
);
ok( !-e $second, 'does not select an occupied path' );

open( my $prefix_collision, '>', $second ) or die "cannot create test file: $!";
close $prefix_collision;
my $longer = ClamTk::Quarantine::unique_quarantine_path(
    $directory, 'sample.txt', $hash_b
);
is(
    $longer,
    "$directory/sample.txt.clamtk-" . substr( $hash_b, 0, 16 ),
    'extends the hash prefix when the short candidate is occupied'
);

ok( -e $first, 'existing quarantined file remains untouched' );
ok( !defined ClamTk::Quarantine::unique_quarantine_path(
        $directory, 'sample.txt', 'not-a-hash'
    ),
    'rejects malformed content hashes'
);

done_testing();
