use strict;
use warnings;
use Test::More;
use FindBin;
use File::Path 'make_path';
use File::Temp 'tempdir';

require "$FindBin::Bin/../lib/Quarantine.pm";
require "$FindBin::Bin/../lib/Results.pm";

my $root = tempdir( CLEANUP => 1 );
my $source_a = "$root/a";
my $source_b = "$root/b";
my $quarantine = "$root/quarantine";
my $restore = "$root/restore";
make_path( $source_a, $source_b, $quarantine );
$ClamTk::App::TEST_PATHS{ viruses } = $quarantine;
$ClamTk::App::TEST_PATHS{ restore } = $restore;

open( my $restore_file, '>', $restore ) or die "cannot create restore file: $!";
close $restore_file;
for my $case ( [ $source_a, 'first contents' ], [ $source_b, 'second contents' ] ) {
    my ( $directory, $contents ) = @$case;
    open( my $source, '>', "$directory/same-name.txt" )
        or die "cannot create source file: $!";
    print {$source} $contents;
    close $source;
}

ok(
    ClamTk::Results::quarantine( "$source_a/same-name.txt" ),
    'quarantines the first file'
);
ok(
    ClamTk::Results::quarantine( "$source_b/same-name.txt" ),
    'quarantines a second file with the same basename'
);
ok( !-e "$source_a/same-name.txt", 'first source was moved' );
ok( !-e "$source_b/same-name.txt", 'second source was moved' );

my @stored = glob "$quarantine/*";
is( scalar @stored, 2, 'both files remain in quarantine' );
ok( -e "$quarantine/same-name.txt", 'first file keeps the plain basename' );
my @collision_names = glob "$quarantine/same-name.txt.clamtk-*";
is( scalar @collision_names, 1, 'second file has a unique quarantine name' );

my @restore_entries;
open( my $index, '<', $restore ) or die "cannot read restore file: $!";
@restore_entries = <$index>;
close $index;
is( scalar @restore_entries, 2, 'both original restore paths are recorded' );

done_testing();

package ClamTk::App;

our %TEST_PATHS;

sub get_path {
    return $TEST_PATHS{ $_[1] };
}
